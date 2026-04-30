# 支付功能配置指南（沙箱环境 - 本地开发）

本文档说明如何配置支付宝沙箱环境，实现本地支付功能。

> **无需公网地址**，通过主动轮询查询支付状态，完全在本地完成。

---

## 一、方案说明

| 环节 | 方案 | 需要公网？ |
|------|------|:---:|
| 创建预下单 | 后端调用支付宝沙箱 API → 拿到二维码 | ❌ |
| 用户扫码支付 | 沙箱支付宝 App 扫码 | ❌ |
| 确认支付状态 | 前端轮询 → 后端调用 `alipay.trade.query` 查询 | ❌ |

---

## 二、配置步骤

### 2.1 注册沙箱环境

1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 进入 **控制台** → **开发工具推荐** → **沙箱**
3. 记录 **APPID**

### 2.2 配置密钥

1. 下载 [支付宝开放平台开发助手](https://opendocs.alipay.com/common/02kipk)
2. 生成 **RSA2(SHA256) 2048位** 密钥对
3. 在沙箱控制台上传 **应用公钥**（纯内容，不带 BEGIN/END 头尾）
4. 获取并保存 **支付宝公钥**

### 2.3 下载沙箱支付宝 App

1. 在沙箱页面 → **沙箱工具** → 下载沙箱版支付宝（仅 Android）
2. 使用**沙箱买家账号**登录
3. 沙箱账号自带虚拟余额，不会真实扣款

### 2.4 放入密钥文件

在 `smart-dining-backend/keys/` 目录创建以下 3 个文件：

```
smart-dining-backend/
└── keys/
    ├── appid.txt              ← 沙箱 APPID（如 9021000123456789）
    ├── app_private_key.txt    ← 应用私钥（纯内容，不带 BEGIN/END）
    └── alipay_public_key.txt  ← 支付宝公钥（纯内容，不带 BEGIN/END）
```

> ⚠️ `keys/` 目录已添加到 `.gitignore`，不会被提交到 Git 仓库。

### 2.5 安装 SDK

```bash
pip install alipay-sdk-python
```

---

## 三、支付流程

```
用户点击 "立即结算"
    ↓
选择 "支付宝" 支付方式
    ↓
前端调用 POST /api/payment/create
    ↓
后端调用 alipay.trade.precreate（沙箱网关）
    ↓
支付宝返回 qr_code → 后端返回给前端
    ↓
前端生成二维码展示
    ↓
用户用沙箱支付宝 App 扫码支付
    ↓
前端每 2 秒轮询 GET /api/payment/query/{id}
    ↓
后端调用 alipay.trade.query 查询真实状态
    ↓
支付成功 → 前端显示成功页面 ✅
```

---

## 四、API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/payment/methods` | GET | 获取可用支付方式 |
| `/api/payment/create` | POST | 创建支付订单，返回二维码链接 |
| `/api/payment/query/{id}` | GET | 查询支付状态（主动轮询） |
| `/api/payment/config/status` | GET | 查看配置状态 |

---

## 五、验证配置

启动后端后，访问以下接口检查配置状态：

```bash
curl http://localhost:8000/api/payment/config/status
```

正确配置后应返回：
```json
{
  "alipay": {
    "configured": true,
    "app_id_set": true,
    "private_key_set": true,
    "public_key_set": true,
    "gateway": "https://openapi-sandbox.dl.alipaydev.com/gateway.do",
    "mode": "沙箱环境"
  }
}
```

---

## 六、常见问题

### Q: 二维码无法扫描
- 确认使用的是**沙箱版支付宝 App**，不是普通支付宝
- 使用**沙箱买家账号**登录，不是真实账号

### Q: 提示 "支付宝未配置"
- 检查 `keys/` 目录下 3 个文件是否都存在
- 检查文件内容是否为纯密钥内容（不带 BEGIN/END 头尾）

### Q: 签名验证失败
- 确认密钥是 RSA2(SHA256) 格式
- 确认使用沙箱网关而非正式网关
- 重新生成密钥对并重新配置

### Q: 沙箱配置公钥时提示 "内部异常"
- 粘贴时**去掉** `-----BEGIN PUBLIC KEY-----` 和 `-----END PUBLIC KEY-----`
- 确保公钥是完整的一行，中间没有换行
- 换用 Chrome 无痕模式重试
