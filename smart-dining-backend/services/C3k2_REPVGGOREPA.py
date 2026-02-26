"""
C3k2_REPVGGOREPA 自定义模块
用于加载使用 RepVGG + OREPA 重参数化训练的 YOLO 模型

该模块结合了:
- C3k2: Ultralytics 的 CSP Bottleneck 块
- RepVGG: 结构重参数化卷积
- OREPA: Online Convolutional Re-parameterization (CVPR 2022)

实际模型结构:
  RepVGGBlock
    ├── reparam (OREPA_3x3_RepConv)
    │     ├── weight_3x3 (Parameter)
    │     ├── scale_3x3  (Parameter) 
    │     ├── weight_1x1 (Parameter)
    │     ├── scale_1x1  (Parameter)
    │     ├── scale_identity (Parameter)
    │     └── bn (BatchNorm2d)
    ├── se (Identity)
    └── act (SiLU)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


def autopad(k, p=None, d=1):
    """Pad to 'same' shape outputs."""
    if d > 1:
        k = d * (k - 1) + 1 if isinstance(k, int) else [d * (x - 1) + 1 for x in k]
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]
    return p


class Conv(nn.Module):
    """Standard convolution with batch normalization and activation."""
    default_act = nn.SiLU()

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p, d), groups=g, dilation=d, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        return self.act(self.conv(x))


class OREPA_3x3_RepConv(nn.Module):
    """OREPA 3x3 Online Re-parameterizable Convolution.
    
    Uses learnable weight parameters + scaling factors for each branch,
    merged through a single BN at the end.
    """

    def __init__(self, c1, c2, k=3, s=1, p=1, g=1, act=True, deploy=False):
        super().__init__()
        self.deploy = deploy
        self.groups = g
        self.stride = s
        self.padding = p

        if deploy:
            self.fused_conv = nn.Conv2d(c1, c2, k, s, p, groups=g, bias=True)
        else:
            # 3x3 branch
            self.weight_3x3 = nn.Parameter(torch.empty(c2, c1 // g, k, k))
            nn.init.kaiming_uniform_(self.weight_3x3, a=5**0.5)
            self.scale_3x3 = nn.Parameter(torch.ones(c2, 1, 1, 1))
            
            # 1x1 branch
            self.weight_1x1 = nn.Parameter(torch.empty(c2, c1 // g, 1, 1))
            nn.init.kaiming_uniform_(self.weight_1x1, a=5**0.5)
            self.scale_1x1 = nn.Parameter(torch.ones(c2, 1, 1, 1))
            
            # Identity scaling
            self.scale_identity = nn.Parameter(torch.ones(c2, 1, 1, 1))
            
            # Final batch normalization
            self.bn = nn.BatchNorm2d(c2)

    def forward(self, x):
        if hasattr(self, 'fused_conv'):
            return self.fused_conv(x)
        
        # Get dimensions from tensor shapes (safe for unpickled models)
        c_out, c_in_per_g, kh, kw = self.weight_3x3.shape
        g = x.shape[1] // c_in_per_g if c_in_per_g > 0 else 1
        s = getattr(self, 'stride', 1)
        p = getattr(self, 'padding', kh // 2)
        
        # 3x3 branch
        w3 = self.weight_3x3 * self.scale_3x3
        
        # 1x1 branch padded to 3x3
        w1 = self.weight_1x1 * self.scale_1x1
        pad_size = kh // 2
        w1_padded = F.pad(w1, [pad_size, pad_size, pad_size, pad_size])
        
        # Identity branch as 3x3 kernel
        id_kernel = torch.zeros_like(self.weight_3x3)
        n_copy = min(c_out, c_in_per_g)
        for i in range(n_copy):
            id_kernel[i, i, kh // 2, kw // 2] = 1.0
        w_id = id_kernel * self.scale_identity
        
        # Merge and compute
        weight = w3 + w1_padded + w_id
        out = F.conv2d(x, weight, stride=s, padding=p, groups=g)
        return self.bn(out)


class RepVGGBlock(nn.Module):
    """RepVGG style block with OREPA re-parameterization.
    
    Structure:
    - reparam: OREPA_3x3_RepConv (the actual convolution)
    - se: squeeze-excite module (Identity when not used)
    - act: activation function (SiLU)
    """

    def __init__(self, c1, c2, k=3, s=1, p=1, g=1, act=True, deploy=False):
        super().__init__()
        self.reparam = OREPA_3x3_RepConv(c1, c2, k, s, p, g, act=False, deploy=deploy)
        self.se = nn.Identity()
        self.act = nn.SiLU() if act is True else (act if isinstance(act, nn.Module) else nn.Identity())

    def forward(self, x):
        return self.act(self.se(self.reparam(x)))


# Alias expected by trained model checkpoint
RepVGGOREPA_Block = RepVGGBlock


class RepVGGOREPA_Bottleneck(nn.Module):
    """Bottleneck with RepVGG-OREPA re-parameterization."""

    def __init__(self, c1, c2, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = RepVGGBlock(c1, c_, k=3, s=1, p=1)
        self.cv2 = RepVGGBlock(c_, c2, k=3, s=1, p=1)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x))


class C3k2_REPVGGOREPA(nn.Module):
    """C3k2 block with RepVGG-OREPA re-parameterized bottlenecks.

    Faster Implementation of CSP Bottleneck with 2 convolutions,
    using RepVGG + OREPA for efficient multi-branch training and
    single-branch inference.
    """

    def __init__(self, c1, c2, n=1, shortcut=False, g=1, e=0.5):
        super().__init__()
        self.c = int(c2 * e)
        self.cv1 = Conv(c1, 2 * self.c, 1, 1)
        self.cv2 = Conv((2 + n) * self.c, c2, 1)
        self.m = nn.ModuleList(
            RepVGGOREPA_Bottleneck(self.c, self.c, shortcut, g, e=1.0)
            for _ in range(n)
        )

    def forward(self, x):
        y = list(self.cv1(x).chunk(2, 1))
        y.extend(m(y[-1]) for m in self.m)
        return self.cv2(torch.cat(y, 1))

    def forward_split(self, x):
        y = self.cv1(x).split((self.c, self.c), 1)
        y = [y[0], y[1]]
        y.extend(m(y[-1]) for m in self.m)
        return self.cv2(torch.cat(y, 1))
