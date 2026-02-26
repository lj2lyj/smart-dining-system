# 支付功能配置指南

本文档说明如何配置支付宝和微信支付功能。

---

## 一、当前状态

系统默认运行在 **模拟模式**：
- 可以正常创建支付订单
- 返回模拟的二维码链接
- 查询状态自动返回"已支付"
- **不会产生真实扣款**

适合开发测试使用。生产环境需按以下步骤配置真实参数。

---

## 二、支付宝配置

### 2.1 申请流程

1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 创建应用，获取 **App ID**
3. 在应用设置中配置：
   - 接口加签方式：**RSA2**
   - 生成应用私钥和公钥
   - 上传公钥获取支付宝公钥
4. 申请开通 **当面付** 产品

### 2.2 配置参数

编辑文件：`smart-dining-backend/services/payment_service.py`

```python
class PaymentConfig:
    # 支付宝配置
    ALIPAY_APP_ID = "你的App ID"
    ALIPAY_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
你的应用私钥
-----END RSA PRIVATE KEY-----"""
    ALIPAY_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
支付宝公钥
-----END PUBLIC KEY-----"""
    ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"  # 正式环境
    ALIPAY_NOTIFY_URL = "https://你的域名/api/payment/notify/alipay"
```

### 2.3 安装 SDK

```bash
pip install alipay-sdk-python
```

### 2.4 启用真实接口

取消 `payment_service.py` 中 `AlipayService.create_order()` 方法里的注释代码。

---

## 三、微信支付配置

### 3.1 申请流程

1. 登录 [微信支付商户平台](https://pay.weixin.qq.com/)
2. 完成商户入驻
3. 获取以下信息：
   - **商户号** (mch_id)
   - **API 密钥** (V2 版本)
   - **API V3 密钥**
   - **商户证书** (包含序列号和私钥)
4. 关联公众号或小程序获取 **App ID**

### 3.2 配置参数

编辑文件：`smart-dining-backend/services/payment_service.py`

```python
class PaymentConfig:
    # 微信支付配置
    WECHAT_APP_ID = "公众号/小程序 App ID"
    WECHAT_MCH_ID = "商户号"
    WECHAT_API_KEY = "API 密钥（V2）"
    WECHAT_API_V3_KEY = "API V3 密钥"
    WECHAT_SERIAL_NO = "商户证书序列号"
    WECHAT_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
商户私钥
-----END PRIVATE KEY-----"""
    WECHAT_NOTIFY_URL = "https://你的域名/api/payment/notify/wechat"
```

### 3.3 安装依赖

```bash
pip install wechatpayv3
```

### 3.4 启用真实接口

取消 `payment_service.py` 中 `WechatPayService.create_order()` 方法里的注释代码。

---

## 四、回调通知配置

### 4.1 HTTPS 要求

支付宝和微信都要求回调地址必须是 **HTTPS**。确保：
- 服务器配置了有效的 SSL 证书
- 回调 URL 可以被外网访问

### 4.2 Nginx 配置示例

确保以下路径可被外网访问：

```nginx
location /api/payment/notify/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 4.3 回调 URL

| 支付方式 | 回调地址 |
|----------|----------|
| 支付宝 | `https://你的域名/api/payment/notify/alipay` |
| 微信 | `https://你的域名/api/payment/notify/wechat` |

---

## 五、环境变量配置（推荐）

生产环境中，敏感信息应使用环境变量：

### 5.1 创建 .env 文件

```bash
# smart-dining-backend/.env

# 支付宝
ALIPAY_APP_ID=你的AppID
ALIPAY_PRIVATE_KEY_PATH=/path/to/alipay_private_key.pem
ALIPAY_PUBLIC_KEY_PATH=/path/to/alipay_public_key.pem
ALIPAY_NOTIFY_URL=https://你的域名/api/payment/notify/alipay

# 微信支付
WECHAT_APP_ID=你的AppID
WECHAT_MCH_ID=你的商户号
WECHAT_API_KEY=API密钥
WECHAT_API_V3_KEY=API_V3密钥
WECHAT_CERT_SERIAL_NO=证书序列号
WECHAT_PRIVATE_KEY_PATH=/path/to/wechat_private_key.pem
WECHAT_NOTIFY_URL=https://你的域名/api/payment/notify/wechat
```

### 5.2 加载环境变量

安装 python-dotenv：

```bash
pip install python-dotenv
```

在 `payment_service.py` 开头添加：

```python
import os
from dotenv import load_dotenv

load_dotenv()

class PaymentConfig:
    ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "")
    # ... 其他配置
```

---

## 六、前端支付流程

### 6.1 支付流程图

```
用户点击结算
    ↓
选择支付方式 (支付宝/微信)
    ↓
前端调用 POST /api/payment/create
    ↓
后端返回 qr_code / code_url
    ↓
前端生成二维码展示
    ↓
用户扫码支付
    ↓
前端轮询 GET /api/payment/query/{payment_id}
    ↓
检测到支付成功 → 显示成功页面
```

### 6.2 二维码生成

前端需要安装二维码库：

```bash
npm install qrcode
```

使用示例：

```javascript
import QRCode from 'qrcode'

// 生成二维码
const qrCodeUrl = await QRCode.toDataURL(paymentResult.qr_code)
```

---

## 七、测试支付

### 7.1 支付宝沙箱

1. 在开放平台启用沙箱环境
2. 下载沙箱版支付宝 App
3. 使用沙箱测试账号支付
4. 修改网关地址：
```python
ALIPAY_GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
```

### 7.2 微信支付

微信支付没有沙箱环境，建议：
- 使用小金额（0.01元）测试
- 测试后在商户平台退款

---

## 八、常见问题

### Q: 二维码无法扫描
- 检查金额是否大于0
- 检查商户状态是否正常
- 确认产品权限是否开通

### Q: 回调未收到
- 检查服务器防火墙
- 确认 HTTPS 证书有效
- 查看后端日志

### Q: 签名验证失败
- 检查密钥是否正确
- 确认使用正确的加签方式（RSA2）
- 注意公钥私钥不要混淆

---

## 九、API 接口速览

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/payment/methods` | GET | 获取可用支付方式 |
| `/api/payment/create` | POST | 创建支付订单 |
| `/api/payment/query/{id}` | GET | 查询支付状态 |
| `/api/payment/notify/alipay` | POST | 支付宝回调 |
| `/api/payment/notify/wechat` | POST | 微信回调 |
| `/api/payment/config/status` | GET | 查看配置状态 |
