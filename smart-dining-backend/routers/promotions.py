"""
促销管理 API
"""
from fastapi import APIRouter, HTTPException
from typing import List

from models.schemas import PromotionCreate, Promotion
from database.db import (
    get_all_promotions, get_active_promotions,
    create_promotion, update_promotion, delete_promotion
)

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_promotions():
    """获取所有促销活动"""
    return await get_all_promotions()


@router.get("/active", response_model=List[dict])
async def list_active_promotions():
    """获取当前有效的促销活动"""
    return await get_active_promotions()


@router.post("/", response_model=dict)
async def add_promotion(promo: PromotionCreate):
    """创建促销活动"""
    promo_data = promo.model_dump()
    
    # 转换 datetime 为 ISO 字符串
    if promo_data.get("start_time"):
        promo_data["start_time"] = promo_data["start_time"].isoformat()
    if promo_data.get("end_time"):
        promo_data["end_time"] = promo_data["end_time"].isoformat()
    
    return await create_promotion(promo_data)


@router.put("/{promo_id}", response_model=dict)
async def modify_promotion(promo_id: str, updates: dict):
    """更新促销活动"""
    result = await update_promotion(promo_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="促销活动不存在")
    return result


@router.delete("/{promo_id}")
async def remove_promotion(promo_id: str):
    """删除促销活动"""
    success = await delete_promotion(promo_id)
    if not success:
        raise HTTPException(status_code=404, detail="促销活动不存在")
    return {"success": True, "message": "促销活动已删除"}
