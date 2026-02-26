"""
model_patches.py - 模型加载补丁模块

基于官方 YOLOv13 源代码 (iMoonLab/yolov13) 精确实现所有自定义模块。
在加载模型之前调用 apply_patches() 即可。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


def autopad(k, p=None, d=1):
    if d > 1:
        k = d * (k - 1) + 1 if isinstance(k, int) else [d * (x - 1) + 1 for x in k]
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]
    return p


try:
    from ultralytics.nn.modules.conv import Conv
    from ultralytics.nn.modules.block import C3
    from ultralytics.nn.modules.block import C2f
except ImportError:
    class Conv(nn.Module):
        default_act = nn.SiLU()
        def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
            super().__init__()
            self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p, d), groups=g, dilation=d, bias=False)
            self.bn = nn.BatchNorm2d(c2)
            self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()
        def forward(self, x):
            return self.act(self.bn(self.conv(x)))
    C3 = None
    C2f = None


# ============================================================
# DSConv
# ============================================================
class DSConv(nn.Module):
    """Depthwise Separable Convolution."""
    def __init__(self, c1, c2, k=3, s=1, p=None, d=1, act=True):
        super().__init__()
        if p is None:
            p = autopad(k, d=d)
        self.dw = nn.Conv2d(c1, c1, k, s, p, dilation=d, groups=c1, bias=False)
        self.pw = nn.Conv2d(c1, c2, 1, 1, 0, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = nn.SiLU() if act is True else (act if isinstance(act, nn.Module) else nn.Identity())

    def forward(self, x):
        return self.act(self.bn(self.pw(self.dw(x))))


# ============================================================
# DSBottleneck
# ============================================================
class DSBottleneck(nn.Module):
    def __init__(self, c1, c2, shortcut=True, e=0.5, k1=3, k2=5, d2=1):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = DSConv(c1, c_, k1, s=1, p=None, d=1)
        self.cv2 = DSConv(c_, c2, k2, s=1, p=None, d=d2)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        y = self.cv2(self.cv1(x))
        return x + y if self.add else y


# ============================================================
# DSC3k (extends C3)
# ============================================================
class DSC3k(nn.Module):
    """CSP Bottleneck with DSConv (reimplementation not requiring C3 parent)."""
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, k1=3, k2=5, d2=1):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.cv3 = Conv(2 * c_, c2, 1)
        self.m = nn.Sequential(
            *(DSBottleneck(c_, c_, shortcut=shortcut, e=1.0, k1=k1, k2=k2, d2=d2) for _ in range(n))
        )

    def forward(self, x):
        return self.cv3(torch.cat((self.m(self.cv1(x)), self.cv2(x)), 1))


# ============================================================
# AdaHyperedgeGen (Official YOLOv13)
# ============================================================
class AdaHyperedgeGen(nn.Module):
    """Adaptive Hyperedge Generator with multi-head attention."""
    def __init__(self, node_dim, num_hyperedges, num_heads=4, dropout=0.1, context="both"):
        super().__init__()
        self.num_heads = num_heads
        self.num_hyperedges = num_hyperedges
        self.head_dim = node_dim // num_heads
        self.context = context

        self.prototype_base = nn.Parameter(torch.Tensor(num_hyperedges, node_dim))
        nn.init.xavier_uniform_(self.prototype_base)
        
        if context in ("mean", "max"):
            self.context_net = nn.Linear(node_dim, num_hyperedges * node_dim)
        elif context == "both":
            self.context_net = nn.Linear(2 * node_dim, num_hyperedges * node_dim)
        
        self.pre_head_proj = nn.Linear(node_dim, node_dim)
        self.dropout = nn.Dropout(dropout)
        self.scaling = math.sqrt(self.head_dim)

    def forward(self, X):
        B, N, D = X.shape
        
        # Global context
        if self.context == "mean":
            context_cat = X.mean(dim=1)
        elif self.context == "max":
            context_cat, _ = X.max(dim=1)
        else:  # "both"
            avg_context = X.mean(dim=1)
            max_context, _ = X.max(dim=1)
            context_cat = torch.cat([avg_context, max_context], dim=-1)
        
        # Generate prototype offsets from context
        prototype_offsets = self.context_net(context_cat).view(B, self.num_hyperedges, D)
        prototypes = self.prototype_base.unsqueeze(0) + prototype_offsets
        
        # Multi-head attention between X and prototypes
        X_proj = self.pre_head_proj(X)
        X_heads = X_proj.view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        proto_heads = prototypes.view(B, self.num_hyperedges, self.num_heads, self.head_dim).permute(0, 2, 1, 3)
        
        X_heads_flat = X_heads.reshape(B * self.num_heads, N, self.head_dim)
        proto_heads_flat = proto_heads.reshape(B * self.num_heads, self.num_hyperedges, self.head_dim).transpose(1, 2)
        
        logits = torch.bmm(X_heads_flat, proto_heads_flat) / self.scaling
        logits = logits.view(B, self.num_heads, N, self.num_hyperedges).mean(dim=1)
        logits = self.dropout(logits)
        
        return F.softmax(logits, dim=1)


# ============================================================
# AdaHGConv (Official YOLOv13)
# ============================================================
class AdaHGConv(nn.Module):
    """Adaptive Hypergraph Convolution."""
    def __init__(self, embed_dim, num_hyperedges=16, num_heads=4, dropout=0.1, context="both"):
        super().__init__()
        self.edge_generator = AdaHyperedgeGen(embed_dim, num_hyperedges, num_heads, dropout, context)
        self.edge_proj = nn.Sequential(nn.Linear(embed_dim, embed_dim), nn.GELU())
        self.node_proj = nn.Sequential(nn.Linear(embed_dim, embed_dim), nn.GELU())

    def forward(self, X):
        A = self.edge_generator(X)          # (B, N, num_edges)
        He = torch.bmm(A.transpose(1, 2), X)  # vertex-to-edge: (B, num_edges, D)
        He = self.edge_proj(He)
        X_new = torch.bmm(A, He)            # edge-to-vertex: (B, N, D)
        X_new = self.node_proj(X_new)
        return X_new + X


# ============================================================
# AdaHGComputation (Official YOLOv13)
# ============================================================
class AdaHGComputation(nn.Module):
    """Wrapper for applying AdaHGConv to 4D feature maps."""
    def __init__(self, embed_dim, num_hyperedges=16, num_heads=8, dropout=0.1, context="both"):
        super().__init__()
        self.embed_dim = embed_dim
        self.hgnn = AdaHGConv(embed_dim, num_hyperedges, num_heads, dropout, context)

    def forward(self, x):
        B, C, H, W = x.shape
        tokens = x.flatten(2).transpose(1, 2)  # (B, H*W, C)
        tokens = self.hgnn(tokens)
        return tokens.transpose(1, 2).view(B, C, H, W)


# ============================================================
# C3AH (Official YOLOv13)
# ============================================================
class C3AH(nn.Module):
    """CSP block with Adaptive Hypergraph."""
    def __init__(self, c1, c2, e=1.0, num_hyperedges=8, context="both"):
        super().__init__()
        c_ = int(c2 * e)
        num_heads = max(c_ // 16, 1)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.m = AdaHGComputation(embed_dim=c_, num_hyperedges=num_hyperedges, 
                                   num_heads=num_heads, dropout=0.1, context=context)
        self.cv3 = Conv(2 * c_, c2, 1)

    def forward(self, x):
        return self.cv3(torch.cat((self.m(self.cv1(x)), self.cv2(x)), 1))


# ============================================================
# FuseModule (Official YOLOv13)
# ============================================================
class FuseModule(nn.Module):
    """Multi-scale feature fusion: downsample x[0], keep x[1], upsample x[2], concat → conv."""
    def __init__(self, c_in, channel_adjust=True):
        super().__init__()
        self.downsample = nn.AvgPool2d(kernel_size=2)
        self.upsample = nn.Upsample(scale_factor=2, mode='nearest')
        if channel_adjust:
            self.conv_out = Conv(4 * c_in, c_in, 1)
        else:
            self.conv_out = Conv(3 * c_in, c_in, 1)

    def forward(self, x):
        x1_ds = self.downsample(x[0])
        x3_up = self.upsample(x[2])
        x_cat = torch.cat([x1_ds, x[1], x3_up], dim=1)
        return self.conv_out(x_cat)


# ============================================================
# FullPAD_Tunnel (Official YOLOv13)
# ============================================================
class FullPAD_Tunnel(nn.Module):
    """Gated residual: output = x[0] + gate * x[1]."""
    def __init__(self):
        super().__init__()
        self.gate = nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        return x[0] + self.gate * x[1]


# ============================================================
# HyperACE (Official YOLOv13)
# ============================================================
class HyperACE(nn.Module):
    """Hypergraph-based Adaptive Correlation Enhancement."""
    def __init__(self, c1, c2, n=1, num_hyperedges=8, dsc3k=True, shortcut=False,
                 e1=0.5, e2=1, context="both", channel_adjust=True):
        super().__init__()
        self.c = int(c2 * e1)
        self.cv1 = Conv(c1, 3 * self.c, 1, 1)
        self.cv2 = Conv((4 + n) * self.c, c2, 1)
        self.m = nn.ModuleList(
            DSC3k(self.c, self.c, 2, shortcut, k1=3, k2=7) if dsc3k 
            else DSBottleneck(self.c, self.c, shortcut=shortcut) 
            for _ in range(n)
        )
        self.fuse = FuseModule(c1, channel_adjust)
        self.branch1 = C3AH(self.c, self.c, e2, num_hyperedges, context)
        self.branch2 = C3AH(self.c, self.c, e2, num_hyperedges, context)

    def forward(self, X):
        x = self.fuse(X)
        y = list(self.cv1(x).chunk(3, 1))
        out1 = self.branch1(y[1])
        out2 = self.branch2(y[1])
        y.extend(m(y[-1]) for m in self.m)
        y[1] = out1
        y.append(out2)
        return self.cv2(torch.cat(y, 1))


# ============================================================
# DownsampleConv (Official YOLOv13)
# ============================================================
class DownsampleConv(nn.Module):
    """Downsample with AvgPool + optional channel doubling."""
    def __init__(self, in_channels, channel_adjust=True):
        super().__init__()
        self.downsample = nn.AvgPool2d(kernel_size=2)
        if channel_adjust:
            self.channel_adjust = Conv(in_channels, in_channels * 2, 1)
        else:
            self.channel_adjust = nn.Identity()

    def forward(self, x):
        return self.channel_adjust(self.downsample(x))


# ============================================================
# Patch Application
# ============================================================

CONV_PATCHES = {
    'DSConv': DSConv,
}

BLOCK_PATCHES = {
    'DownsampleConv': DownsampleConv,
    'DSBottleneck': DSBottleneck,
    'DSC3k': DSC3k,
    'FuseModule': FuseModule,
    'FullPAD_Tunnel': FullPAD_Tunnel,
    'AdaHyperedgeGen': AdaHyperedgeGen,
    'AdaHGConv': AdaHGConv,
    'AdaHGComputation': AdaHGComputation,
    'C3AH': C3AH,
    'HyperACE': HyperACE,
}


def apply_patches():
    """Must be called before loading the YOLO model."""
    import importlib
    import sys

    try:
        conv_module = importlib.import_module('ultralytics.nn.modules.conv')
        for name, cls in CONV_PATCHES.items():
            if not hasattr(conv_module, name):
                setattr(conv_module, name, cls)
                print(f"[PATCH] Added {name} to ultralytics.nn.modules.conv")
    except ImportError:
        pass

    try:
        block_module = importlib.import_module('ultralytics.nn.modules.block')
        for name, cls in BLOCK_PATCHES.items():
            if not hasattr(block_module, name):
                setattr(block_module, name, cls)
                print(f"[PATCH] Added {name} to ultralytics.nn.modules.block")

        # Patch AAttn to use separate qk + v (model trained with older ultralytics)
        if hasattr(block_module, 'AAttn'):
            AAttn = block_module.AAttn
            ConvCls = conv_module.Conv

            def _new_init(self, dim, num_heads=8, area=1):
                nn.Module.__init__(self)
                self.area = area
                self.num_heads = num_heads
                self.head_dim = dim // num_heads
                all_head_dim = self.head_dim * num_heads
                self.qk = ConvCls(dim, all_head_dim * 2, 1, act=False)
                self.v = ConvCls(dim, all_head_dim, 1, act=False)
                self.proj = ConvCls(all_head_dim, dim, 1, act=False)
                self.pe = ConvCls(all_head_dim, dim, 7, 1, 3, g=dim, act=False)

            def _new_forward(self, x):
                B, C, H, W = x.shape
                N = H * W
                qk = self.qk(x).flatten(2).transpose(1, 2)
                v_out = self.v(x).flatten(2).transpose(1, 2)
                if self.area > 1:
                    qk = qk.reshape(B * self.area, N // self.area, C * 2)
                    v_out = v_out.reshape(B * self.area, N // self.area, C)
                    B_a, N_a = qk.shape[0], qk.shape[1]
                else:
                    B_a, N_a = B, N
                qk = qk.view(B_a, N_a, self.num_heads, self.head_dim * 2).permute(0, 2, 3, 1)
                q, k = qk.split([self.head_dim, self.head_dim], dim=2)
                v = v_out.view(B_a, N_a, self.num_heads, self.head_dim).permute(0, 2, 3, 1)
                attn = (q.transpose(-2, -1) @ k) * (self.head_dim ** -0.5)
                attn = attn.softmax(dim=-1)
                x = v @ attn.transpose(-2, -1)
                x = x.permute(0, 3, 1, 2)
                v = v.permute(0, 3, 1, 2)
                if self.area > 1:
                    x = x.reshape(B, N, C)
                    v = v.reshape(B, N, C)
                x = x.reshape(B, H, W, C).permute(0, 3, 1, 2).contiguous()
                v = v.reshape(B, H, W, C).permute(0, 3, 1, 2).contiguous()
                x = x + self.pe(v)
                return self.proj(x)

            AAttn.__init__ = _new_init
            AAttn.forward = _new_forward
            print("[PATCH] Fixed AAttn to use separate qk/v layout")
    except ImportError:
        pass

    for parent in ['ultralytics.nn.modules', 'ultralytics.nn.tasks']:
        try:
            mod = importlib.import_module(parent)
            for name, cls in {**CONV_PATCHES, **BLOCK_PATCHES}.items():
                if not hasattr(mod, name):
                    setattr(mod, name, cls)
        except ImportError:
            pass

    services_dir = str(__import__('pathlib').Path(__file__).parent)
    if services_dir not in sys.path:
        sys.path.insert(0, services_dir)

    print("[OK] All model patches applied successfully")
