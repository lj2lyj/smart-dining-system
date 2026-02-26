"""
支付 API 路由
"""
from fastapi import APIRouter, HTTPException, Request, Body
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
    payment_method: str = "alipay"   # 支付方式: alipay, wechat


class PaymentResponse(BaseModel):
    success: bool
    payment_id: Optional[str] = None
    qr_code: Optional[str] = None
    code_url: Optional[str] = None
    message: Optional[str] = None
    mock: bool = False


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
    
    返回二维码链接，前端生成二维码供用户扫码支付
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
    
    前端可轮询此接口检查支付是否完成
    """
    result = PaymentService.query_payment(payment_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    
    return result


@router.post("/notify/alipay")
async def alipay_notify(request: Request):
    """
    支付宝异步通知回调
    
    支付宝服务器会在用户支付成功后调用此接口
    """
    form_data = await request.form()
    params = dict(form_data)
    
    # 验证签名
    # if not AlipayService.verify_notification(params):
    #     return "fail"
    
    # 处理通知
    result = PaymentService.handle_notification("alipay", params)
    
    return "success" if result.get("success") else "fail"


@router.post("/notify/wechat")
async def wechat_notify(request: Request):
    """
    微信支付异步通知回调
    
    微信支付服务器会在用户支付成功后调用此接口
    """
    body = await request.body()
    headers = dict(request.headers)
    
    # 验证签名
    # if not WechatPayService.verify_notification(headers, body.decode()):
    #     return {"code": "FAIL", "message": "签名验证失败"}
    
    # 处理通知
    data = await request.json()
    result = PaymentService.handle_notification("wechat", data)
    
    if result.get("success"):
        return {"code": "SUCCESS", "message": "成功"}
    else:
        return {"code": "FAIL", "message": "处理失败"}


@router.get("/config/status")
async def get_config_status():
    """
    获取支付配置状态（管理员用）
    
    检查支付宝和微信支付是否已正确配置
    """
    return {
        "alipay": {
            "configured": PaymentConfig.is_alipay_configured(),
            "app_id_set": bool(PaymentConfig.ALIPAY_APP_ID),
            "private_key_set": bool(PaymentConfig.ALIPAY_PRIVATE_KEY),
            "notify_url": PaymentConfig.ALIPAY_NOTIFY_URL or "未设置"
        },
        "wechat": {
            "configured": PaymentConfig.is_wechat_configured(),
            "app_id_set": bool(PaymentConfig.WECHAT_APP_ID),
            "mch_id_set": bool(PaymentConfig.WECHAT_MCH_ID),
            "api_key_set": bool(PaymentConfig.WECHAT_API_KEY),
            "notify_url": PaymentConfig.WECHAT_NOTIFY_URL or "未设置"
        }
    }
