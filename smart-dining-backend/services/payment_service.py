"""
支付服务模块
支持支付宝当面付（沙箱环境）
通过主动轮询查询支付状态，无需公网地址
"""
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================
# 支付配置
# ============================================================

class PaymentConfig:
    """支付配置类 - 从 keys/ 目录自动加载密钥"""
    
    # 密钥文件目录（相对于 smart-dining-backend/）
    KEYS_DIR = Path(__file__).parent.parent / "keys"
    
    # 支付宝配置
    ALIPAY_APP_ID = ""
    ALIPAY_PRIVATE_KEY = ""
    ALIPAY_PUBLIC_KEY = ""
    ALIPAY_GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"  # 沙箱环境
    
    # 通用配置
    PAYMENT_TIMEOUT = 900  # 支付超时时间（秒），默认15分钟
    
    _initialized = False
    
    @classmethod
    def init(cls):
        """从密钥文件加载配置"""
        if cls._initialized:
            return
        
        keys_dir = cls.KEYS_DIR
        
        # 读取 APPID
        appid_file = keys_dir / "appid.txt"
        if appid_file.exists():
            cls.ALIPAY_APP_ID = appid_file.read_text(encoding="utf-8").strip()
            logger.info(f"[支付] 已加载 APPID: {cls.ALIPAY_APP_ID[:8]}...")
        
        # 读取应用私钥
        private_key_file = keys_dir / "app_private_key.txt"
        if private_key_file.exists():
            pk = private_key_file.read_text(encoding="utf-8").strip()
            
            try:
                # 强制转换成 PKCS#1 PEM 格式 (alipay-sdk-python的rsa库仅支持PKCS#1)
                from Crypto.PublicKey import RSA
                import base64
                
                if "BEGIN" not in pk:
                    key_data = base64.b64decode(pk)
                else:
                    key_data = pk.encode()
                    
                key_obj = RSA.import_key(key_data)
                pk = key_obj.export_key(format='PEM').decode()
            except Exception as e:
                logger.error(f"[支付] 解析应用私钥失败: {e}")
                
            cls.ALIPAY_PRIVATE_KEY = pk
            logger.info("[支付] 已加载应用私钥")
        
        # 读取支付宝公钥
        public_key_file = keys_dir / "alipay_public_key.txt"
        if public_key_file.exists():
            pub = public_key_file.read_text(encoding="utf-8").strip()
            
            try:
                from Crypto.PublicKey import RSA
                import base64
                if "BEGIN" not in pub:
                    key_data = base64.b64decode(pub)
                else:
                    key_data = pub.encode()
                    
                key_obj = RSA.import_key(key_data)
                pub = key_obj.export_key(format='PEM').decode()
            except Exception as e:
                logger.error(f"[支付] 解析支付宝公钥失败: {e}")
                
            cls.ALIPAY_PUBLIC_KEY = pub
            logger.info("[支付] 已加载支付宝公钥")
        
        cls._initialized = True
        
        if cls.is_alipay_configured():
            logger.info("[支付] ✅ 支付宝沙箱配置完成，已启用真实支付")
        else:
            logger.warning("[支付] ⚠️ 支付宝未配置，请在 keys/ 目录放入密钥文件")
    
    @classmethod
    def is_alipay_configured(cls) -> bool:
        cls.init()
        return bool(cls.ALIPAY_APP_ID and cls.ALIPAY_PRIVATE_KEY and cls.ALIPAY_PUBLIC_KEY)


# ============================================================
# 支付订单存储（内存存储，重启后丢失）
# ============================================================

payment_orders = {}  # payment_id -> payment_info


# ============================================================
# 支付宝支付服务
# ============================================================

class AlipayService:
    """支付宝当面付服务（沙箱环境）"""
    
    _client = None
    
    @classmethod
    def _get_client(cls):
        """获取或创建支付宝客户端（懒加载）"""
        if cls._client is not None:
            return cls._client
        
        try:
            from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
            from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
        except ImportError:
            raise RuntimeError(
                "未安装支付宝 SDK，请执行: pip install alipay-sdk-python"
            )
        
        PaymentConfig.init()
        
        config = AlipayClientConfig()
        config.server_url = PaymentConfig.ALIPAY_GATEWAY
        config.app_id = PaymentConfig.ALIPAY_APP_ID
        config.app_private_key = PaymentConfig.ALIPAY_PRIVATE_KEY
        config.alipay_public_key = PaymentConfig.ALIPAY_PUBLIC_KEY
        # 设置签名类型为 RSA2
        config.sign_type = "RSA2"
        
        cls._client = DefaultAlipayClient(alipay_client_config=config)
        logger.info("[支付宝] 客户端初始化成功")
        return cls._client
    
    @staticmethod
    def create_order(
        order_id: str,
        amount: float,
        subject: str,
        body: str = ""
    ) -> dict:
        """
        创建支付宝预下单（当面付 - 扫码支付）
        
        调用 alipay.trade.precreate 接口，返回二维码链接
        不设置 notify_url，通过主动查询获取支付状态
        """
        if not PaymentConfig.is_alipay_configured():
            return {
                "success": False,
                "message": "支付宝未配置，请在 keys/ 目录放入密钥文件（appid.txt, app_private_key.txt, alipay_public_key.txt）"
            }
        
        try:
            from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
            from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
            
            client = AlipayService._get_client()
            
            # 构造业务模型
            model = AlipayTradePrecreateModel()
            model.out_trade_no = order_id
            model.total_amount = f"{amount:.2f}"
            model.subject = subject
            model.timeout_express = "15m"  # 设置15分钟有效，防止沙箱默认过期
            if body:
                model.body = body
            
            # 构造请求（不设置 notify_url，无需公网）
            request = AlipayTradePrecreateRequest(biz_model=model)
            
            # 执行请求
            logger.info(f"[支付宝] 创建预下单: order_id={order_id}, amount={amount}")
            response_str = client.execute(request)
            
            # 解析响应
            logger.info(f"[支付宝] 预下单响应: {response_str}")
            response = json.loads(response_str) if isinstance(response_str, str) else response_str
            
            # 检查响应结构 - SDK 返回的可能是直接的响应体
            qr_code = None
            
            # 尝试从不同的响应结构中提取 qr_code
            if isinstance(response, dict):
                # 直接在响应体中
                if "qr_code" in response:
                    qr_code = response["qr_code"]
                # 在 alipay_trade_precreate_response 中
                elif "alipay_trade_precreate_response" in response:
                    sub_resp = response["alipay_trade_precreate_response"]
                    if sub_resp.get("code") == "10000":
                        qr_code = sub_resp.get("qr_code")
                    else:
                        error_msg = sub_resp.get("sub_msg") or sub_resp.get("msg") or "未知错误"
                        logger.error(f"[支付宝] 预下单失败: {error_msg}")
                        return {"success": False, "message": f"支付宝返回错误: {error_msg}"}
            
            if qr_code:
                logger.info(f"[支付宝] ✅ 预下单成功，获得二维码")
                return {
                    "success": True,
                    "order_id": order_id,
                    "qr_code": qr_code,
                    "message": "预下单成功，请扫码支付"
                }
            else:
                # 可能响应格式不同，打印完整响应便于调试
                logger.warning(f"[支付宝] 响应中未找到 qr_code，完整响应: {response}")
                return {
                    "success": False,
                    "message": f"预下单响应异常，请查看后端日志。响应: {str(response)[:200]}"
                }
            
        except ImportError:
            return {
                "success": False,
                "message": "未安装支付宝 SDK，请执行: pip install alipay-sdk-python"
            }
        except Exception as e:
            logger.error(f"[支付宝] 创建预下单异常: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"支付宝接口调用失败: {str(e)}"
            }
    
    @staticmethod
    def query_order(order_id: str) -> dict:
        """
        主动查询支付宝订单状态
        
        调用 alipay.trade.query 接口
        返回 trade_status: WAIT_BUYER_PAY / TRADE_SUCCESS / TRADE_CLOSED 等
        """
        if not PaymentConfig.is_alipay_configured():
            return {"trade_status": "UNKNOWN", "message": "支付宝未配置"}
        
        try:
            from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
            from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
            
            client = AlipayService._get_client()
            
            model = AlipayTradeQueryModel()
            model.out_trade_no = order_id
            
            request = AlipayTradeQueryRequest(biz_model=model)
            response_str = client.execute(request)
            
            logger.debug(f"[支付宝] 查询响应: {response_str}")
            response = json.loads(response_str) if isinstance(response_str, str) else response_str
            
            # 提取交易状态
            trade_status = "UNKNOWN"
            
            if isinstance(response, dict):
                if "trade_status" in response:
                    trade_status = response["trade_status"]
                elif "alipay_trade_query_response" in response:
                    sub_resp = response["alipay_trade_query_response"]
                    if sub_resp.get("code") == "10000":
                        trade_status = sub_resp.get("trade_status", "UNKNOWN")
                    else:
                        # 交易不存在等情况
                        trade_status = "WAIT_BUYER_PAY"
            
            return {
                "trade_status": trade_status,
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"[支付宝] 查询订单异常: {e}", exc_info=True)
            return {"trade_status": "UNKNOWN", "message": str(e)}
    
    @staticmethod
    def verify_notification(params: dict) -> bool:
        """验证支付宝异步通知签名（本地模式下不使用）"""
        return False


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
        payment_method: str = "alipay",
        **kwargs
    ) -> dict:
        """
        创建支付订单
        
        Args:
            order_id: 业务订单ID
            amount: 支付金额（元）
            subject: 商品描述
            payment_method: 支付方式 (alipay)
        
        Returns:
            支付信息，包含二维码链接
        """
        # 生成支付订单号
        payment_id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        
        # 创建支付
        if payment_method == "alipay":
            result = AlipayService.create_order(payment_id, amount, subject)
        else:
            return {"success": False, "message": f"暂不支持的支付方式: {payment_method}，目前仅支持支付宝"}
        
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
                "qr_code": result.get("qr_code"),
            }
            result["payment_id"] = payment_id
        
        return result
    
    @staticmethod
    def query_payment(payment_id: str) -> dict:
        """查询支付状态（通过主动调用支付宝查询接口）"""
        payment = payment_orders.get(payment_id)
        if not payment:
            return {"success": False, "message": "支付订单不存在"}
        
        # 如果已经确认支付成功，直接返回
        if payment["status"] == "paid":
            return {
                "success": True,
                "status": "paid",
                "payment": payment
            }
        
        # 主动查询支付宝订单状态
        if payment["payment_method"] == "alipay":
            result = AlipayService.query_order(payment_id)
            trade_status = result.get("trade_status", "UNKNOWN")
            
            if trade_status == "TRADE_SUCCESS":
                payment["status"] = "paid"
                payment["paid_at"] = datetime.now().isoformat()
                logger.info(f"[支付] ✅ 支付成功: {payment_id}")
            elif trade_status == "TRADE_CLOSED":
                payment["status"] = "closed"
                logger.info(f"[支付] ❌ 交易关闭: {payment_id}")
        
        return {
            "success": True,
            "status": payment["status"],
            "payment": payment
        }
    
    @staticmethod
    def handle_notification(payment_method: str, data: dict) -> dict:
        """处理支付回调通知（本地模式下不使用）"""
        return {"success": True}
    
    @staticmethod
    def get_available_methods() -> list:
        """获取可用的支付方式"""
        PaymentConfig.init()
        
        methods = []
        
        # 支付宝
        configured = PaymentConfig.is_alipay_configured()
        methods.append({
            "id": "alipay",
            "name": "支付宝",
            "name_en": "Alipay",
            "icon": "alipay",
            "configured": configured,
            "mock": not configured
        })
        
        return methods
