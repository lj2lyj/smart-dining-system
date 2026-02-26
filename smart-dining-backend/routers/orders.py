"""
订单管理 API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime

from models.schemas import OrderCreate, Order, OrderItem
from database.db import create_order, get_orders, get_order_by_id, update_stock

router = APIRouter()


@router.post("/", response_model=dict)
async def create_new_order(order: OrderCreate):
    """
    创建订单
    
    同时更新库存（减少相应数量）
    """
    # 验证订单项
    if not order.items:
        raise HTTPException(status_code=400, detail="订单不能为空")
    
    # 计算总金额
    calculated_total = sum(item.price * item.quantity for item in order.items)
    
    # 验证总金额（允许小数误差）
    if abs(calculated_total - order.total_amount) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"金额不匹配: 计算值 {calculated_total}, 提交值 {order.total_amount}"
        )
    
    # 更新库存
    for item in order.items:
        await update_stock(item.dish_id, -item.quantity)
    
    # 创建订单
    order_data = {
        "items": [item.model_dump() for item in order.items],
        "total_amount": order.total_amount,
        "recognition_log_id": order.recognition_log_id
    }
    
    result = await create_order(order_data)
    return result


@router.get("/", response_model=List[dict])
async def list_orders(
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    date: str = Query(None, description="筛选日期 (YYYY-MM-DD)")
):
    """获取订单列表"""
    orders = await get_orders(limit)
    
    # 按日期筛选
    if date:
        orders = [o for o in orders if o.get("created_at", "").startswith(date)]
    
    return orders


@router.get("/today", response_model=List[dict])
async def get_today_orders():
    """获取今日订单"""
    today = datetime.now().date().isoformat()
    orders = await get_orders(200)
    return [o for o in orders if o.get("created_at", "").startswith(today)]


@router.get("/{order_id}", response_model=dict)
async def get_order_detail(order_id: str):
    """获取订单详情"""
    order = await get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order
