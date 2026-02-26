"""
支付服务模块
支持支付宝和微信支付
"""
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime
from typing import Optional
import httpx

# ============================================================
# 支付配置（生产环境请使用环境变量）
# ============================================================

class PaymentConfig:
    """支付配置类"""
    
    # 支付宝配置
    ALIPAY_APP_ID = ""           # 应用ID
    ALIPAY_PRIVATE_KEY = ""      # 应用私钥
    ALIPAY_PUBLIC_KEY = ""       # 支付宝公钥
    ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"  # 正式环境
    # ALIPAY_GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"  # 沙箱环境
    ALIPAY_NOTIFY_URL = ""       # 异步通知回调地址
    
    # 微信支付配置
    WECHAT_APP_ID = ""           # 公众号/小程序 App ID
    WECHAT_MCH_ID = ""           # 商户号
    WECHAT_API_KEY = ""          # API 密钥 (V2)
    WECHAT_API_V3_KEY = ""       # API V3 密钥
    WECHAT_SERIAL_NO = ""        # 商户证书序列号
    WECHAT_PRIVATE_KEY = ""      # 商户私钥
    WECHAT_NOTIFY_URL = ""       # 异步通知回调地址
    
    # 通用配置
    PAYMENT_TIMEOUT = 900        # 支付超时时间（秒），默认15分钟
    
    @classmethod
    def is_alipay_configured(cls) -> bool:
        return bool(cls.ALIPAY_APP_ID and cls.ALIPAY_PRIVATE_KEY)
    
    @classmethod
    def is_wechat_configured(cls) -> bool:
        return bool(cls.WECHAT_APP_ID and cls.WECHAT_MCH_ID and cls.WECHAT_API_KEY)


# ============================================================
# 支付订单存储（生产环境请使用数据库）
# ============================================================

payment_orders = {}  # order_id -> payment_info


# ============================================================
# 支付宝支付服务
# ============================================================

class AlipayService:
    """支付宝支付服务"""
    
    @staticmethod
    def create_order(
        order_id: str,
        amount: float,
        subject: str,
        body: str = ""
    ) -> dict:
        """
        创建支付宝订单（当面付 - 扫码支付）
        
        返回:
            - qr_code: 二维码内容（用户扫码支付）
            - order_id: 订单号
        """
        if not PaymentConfig.is_alipay_configured():
            # 模拟模式
            return {
                "success": True,
                "order_id": order_id,
                "qr_code": f"https://qr.alipay.com/mock_{order_id}",
                "message": "模拟支付 - 请配置支付宝参数",
                "mock": True
            }
        
        # TODO: 实现真实支付宝接口调用
        # 需要安装: pip install alipay-sdk-python
        # from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
        # from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
        # from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
        
        return {
            "success": False,
            "message": "支付宝接口暂未实现，请安装 alipay-sdk-python"
        }
    
    @staticmethod
    def query_order(order_id: str) -> dict:
        """查询支付宝订单状态"""
        if not PaymentConfig.is_alipay_configured():
            # 模拟查询
            return {
                "trade_status": "TRADE_SUCCESS",  # 模拟已支付
                "order_id": order_id,
                "mock": True
            }
        
        # TODO: 实现真实查询接口
        return {"trade_status": "UNKNOWN"}
    
    @staticmethod
    def verify_notification(params: dict) -> bool:
        """验证支付宝异步通知签名"""
        if not PaymentConfig.is_alipay_configured():
            return True  # 模拟模式直接返回成功
        
        # TODO: 实现签名验证
        return False


# ============================================================
# 微信支付服务
# ============================================================

class WechatPayService:
    """微信支付服务"""
    
    @staticmethod
    def create_order(
        order_id: str,
        amount: float,
        description: str,
        trade_type: str = "NATIVE"  # NATIVE=扫码, JSAPI=公众号, H5=H5支付
    ) -> dict:
        """
        创建微信支付订单
        
        trade_type:
            - NATIVE: 扫码支付（生成二维码）
            - JSAPI: 公众号/小程序支付
            - H5: H5网页支付
        
        返回:
            - code_url: 二维码链接（NATIVE模式）
            - prepay_id: 预支付ID（JSAPI模式）
        """
        if not PaymentConfig.is_wechat_configured():
            # 模拟模式
            return {
                "success": True,
                "order_id": order_id,
                "code_url": f"weixin://wxpay/bizpayurl?mock={order_id}",
                "message": "模拟支付 - 请配置微信支付参数",
                "mock": True
            }
        
        # TODO: 实现真实微信支付接口
        # 需要使用微信支付 API V3
        # 文档: https://pay.weixin.qq.com/wiki/doc/apiv3/apis/chapter3_4_1.shtml
        
        return {
            "success": False,
            "message": "微信支付接口暂未实现"
        }
    
    @staticmethod
    def query_order(order_id: str) -> dict:
        """查询微信支付订单状态"""
        if not PaymentConfig.is_wechat_configured():
            return {
                "trade_state": "SUCCESS",  # 模拟已支付
                "order_id": order_id,
                "mock": True
            }
        
        # TODO: 实现真实查询接口
        return {"trade_state": "UNKNOWN"}
    
    @staticmethod
    def verify_notification(headers: dict, body: str) -> bool:
        """验证微信支付异步通知"""
        if not PaymentConfig.is_wechat_configured():
            return True
        
        # TODO: 实现 API V3 签名验证
        return False
    
    @staticmethod
    def generate_sign(params: dict) -> str:
        """生成微信支付签名（V2）"""
        sorted_params = sorted(params.items())
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if v])
        sign_str += f"&key={PaymentConfig.WECHAT_API_KEY}"
        return hashlib.md5(sign_str.encode()).hexdigest().upper()


# ============================================================
# 统一支付服务
# ============================================================

class PaymentService:
    """统一支付服务"""
    
    @staticmethod
    def create_payment(
        order_id: str,
        amount: float,
        subject: str,
        payment_method: str = "alipay",  # alipay, wechat
        **kwargs
    ) -> dict:
        """
        创建支付订单
        
        Args:
            order_id: 业务订单ID
            amount: 支付金额（元）
            subject: 商品描述
            payment_method: 支付方式 (alipay/wechat)
        
        Returns:
            支付信息，包含二维码或支付链接
        """
        # 生成支付订单号
        payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        
        # 创建支付
        if payment_method == "alipay":
            result = AlipayService.create_order(payment_id, amount, subject)
        elif payment_method == "wechat":
            result = WechatPayService.create_order(payment_id, amount, subject)
        else:
            return {"success": False, "message": f"不支持的支付方式: {payment_method}"}
        
        if result.get("success"):
            # 保存支付订单
            payment_orders[payment_id] = {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "subject": subject,
                "payment_method": payment_method,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "qr_code": result.get("qr_code") or result.get("code_url"),
                "mock": result.get("mock", False)
            }
            result["payment_id"] = payment_id
        
        return result
    
    @staticmethod
    def query_payment(payment_id: str) -> dict:
        """查询支付状态"""
        payment = payment_orders.get(payment_id)
        if not payment:
            return {"success": False, "message": "支付订单不存在"}
        
        # 如果是模拟模式，直接返回成功
        if payment.get("mock"):
            payment["status"] = "paid"
            return {
                "success": True,
                "status": "paid",
                "payment": payment,
                "mock": True
            }
        
        # 查询真实支付状态
        if payment["payment_method"] == "alipay":
            result = AlipayService.query_order(payment_id)
            if result.get("trade_status") == "TRADE_SUCCESS":
                payment["status"] = "paid"
        elif payment["payment_method"] == "wechat":
            result = WechatPayService.query_order(payment_id)
            if result.get("trade_state") == "SUCCESS":
                payment["status"] = "paid"
        
        return {
            "success": True,
            "status": payment["status"],
            "payment": payment
        }
    
    @staticmethod
    def handle_notification(payment_method: str, data: dict) -> dict:
        """处理支付回调通知"""
        # TODO: 根据回调更新订单状态
        return {"success": True}
    
    @staticmethod
    def get_available_methods() -> list:
        """获取可用的支付方式"""
        methods = []
        
        # 支付宝
        methods.append({
            "id": "alipay",
            "name": "支付宝",
            "name_en": "Alipay",
            "icon": "alipay",
            "configured": PaymentConfig.is_alipay_configured(),
            "mock": not PaymentConfig.is_alipay_configured()
        })
        
        # 微信支付
        methods.append({
            "id": "wechat",
            "name": "微信支付",
            "name_en": "WeChat Pay",
            "icon": "wechat",
            "configured": PaymentConfig.is_wechat_configured(),
            "mock": not PaymentConfig.is_wechat_configured()
        })
        
        return methods
