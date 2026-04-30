"""
支付 API 路由
支付宝当面付（沙箱环境）
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from services.payment_service import PaymentService, PaymentConfig

router = APIRouter(prefix="/api/payment", tags=["支付"])


# ============================================================
# 请求/响应模型
# ============================================================

class CreatePaymentRequest(BaseModel):
    order_id: str                    # 业务订单ID
    amount: float                    # 支付金额
    subject: str = "智慧餐饮订单"     # 商品描述
    payment_method: str = "alipay"   # 支付方式: alipay


class PaymentResponse(BaseModel):
    success: bool
    payment_id: Optional[str] = None
    qr_code: Optional[str] = None
    message: Optional[str] = None


# ============================================================
# API 端点
# ============================================================

@router.get("/methods")
async def get_payment_methods():
    """获取可用的支付方式"""
    return {
        "methods": PaymentService.get_available_methods()
    }


@router.post("/create", response_model=PaymentResponse)
async def create_payment(request: CreatePaymentRequest):
    """
    创建支付订单
    
    调用支付宝当面付接口，返回二维码链接供前端展示
    用户使用沙箱支付宝 App 扫码支付
    """
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="支付金额必须大于0")
    
    result = PaymentService.create_payment(
        order_id=request.order_id,
        amount=request.amount,
        subject=request.subject,
        payment_method=request.payment_method
    )
    
    return result


@router.get("/query/{payment_id}")
async def query_payment(payment_id: str):
    """
    查询支付状态
    
    前端轮询此接口，后端主动调用支付宝查询接口检查支付是否完成
    """
    result = PaymentService.query_payment(payment_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    
    return result


@router.post("/notify/alipay")
async def alipay_notify(request: Request):
    """
    支付宝异步通知回调（本地模式下不使用）
    
    保留此接口以备将来部署到公网时使用
    """
    form_data = await request.form()
    params = dict(form_data)
    
    result = PaymentService.handle_notification("alipay", params)
    
    return "success" if result.get("success") else "fail"


@router.get("/config/status")
async def get_config_status():
    """
    获取支付配置状态（管理员用）
    
    检查支付宝沙箱是否已正确配置
    """
    PaymentConfig.init()
    
    return {
        "alipay": {
            "configured": PaymentConfig.is_alipay_configured(),
            "app_id_set": bool(PaymentConfig.ALIPAY_APP_ID),
            "private_key_set": bool(PaymentConfig.ALIPAY_PRIVATE_KEY),
            "public_key_set": bool(PaymentConfig.ALIPAY_PUBLIC_KEY),
            "gateway": PaymentConfig.ALIPAY_GATEWAY,
            "mode": "沙箱环境"
        }
    }
