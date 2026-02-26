"""
库存管理 API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List

from database.db import (
    get_all_dishes, get_dish_by_id, 
    update_stock, get_low_stock_dishes
)

router = APIRouter()


class StockUpdateRequest(BaseModel):
    """库存更新请求"""
    quantity: int  # 正数增加，负数减少


@router.get("/", response_model=List[dict])
async def get_inventory():
    """获取所有菜品库存"""
    dishes = await get_all_dishes()
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "stock": d.get("stock", 0),
            "is_available": d.get("is_available", True),
            "category": d.get("category")
        }
        for d in dishes
    ]


@router.get("/low-stock", response_model=List[dict])
async def get_low_stock(threshold: int = Query(20, ge=1, description="低库存阈值")):
    """获取低库存菜品"""
    return await get_low_stock_dishes(threshold)


@router.put("/{dish_id}")
async def update_dish_stock(dish_id: str, request: StockUpdateRequest):
    """
    更新菜品库存
    
    quantity 为正数时增加库存，负数时减少库存
    """
    dish = await get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    
    result = await update_stock(dish_id, request.quantity)
    
    return {
        "success": True,
        "dish_id": dish_id,
        "new_stock": result.get("stock", 0),
        "message": f"库存已更新: {'+' if request.quantity > 0 else ''}{request.quantity}"
    }


@router.post("/{dish_id}/restock")
async def restock_dish(dish_id: str, quantity: int = Query(..., ge=1, description="补货数量")):
    """快捷补货"""
    dish = await get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    
    result = await update_stock(dish_id, quantity)
    
    return {
        "success": True,
        "dish_id": dish_id,
        "new_stock": result.get("stock", 0),
        "message": f"已补货 {quantity} 份"
    }
