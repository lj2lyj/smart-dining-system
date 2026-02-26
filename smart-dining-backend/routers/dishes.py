"""
菜品管理 API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models.schemas import Dish, DishCreate, DishUpdate, DishSource, DishCategory
from database.db import (
    get_all_dishes, get_dish_by_id, get_dishes_by_source,
    create_dish, update_dish, delete_dish
)

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_dishes(
    source: Optional[DishSource] = Query(None, description="筛选来源: yolo/manual"),
    category: Optional[DishCategory] = Query(None, description="筛选分类"),
    available_only: bool = Query(False, description="仅显示可用菜品")
):
    """
    获取菜品列表
    
    可按来源、分类筛选，支持只显示可用菜品
    """
    if source:
        dishes = await get_dishes_by_source(source.value)
    else:
        dishes = await get_all_dishes()
    
    # 按分类筛选
    if category:
        dishes = [d for d in dishes if d.get("category") == category.value]
    
    # 按可用性筛选
    if available_only:
        dishes = [d for d in dishes if d.get("is_available", True)]
    
    return dishes


@router.get("/yolo", response_model=List[dict])
async def list_yolo_dishes():
    """获取 YOLO 可识别的菜品列表"""
    return await get_dishes_by_source("yolo")


@router.get("/manual", response_model=List[dict])
async def list_manual_dishes():
    """获取手动添加的菜品列表（未识别库）"""
    return await get_dishes_by_source("manual")


@router.get("/{dish_id}", response_model=dict)
async def get_dish(dish_id: str):
    """获取单个菜品详情"""
    dish = await get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return dish


@router.post("/", response_model=dict)
async def add_dish(dish: DishCreate):
    """
    添加新菜品
    
    新添加的菜品默认进入"未识别库"（source=manual），
    除非指定了 yolo_class_id
    """
    dish_data = dish.model_dump()
    
    # 如果指定了 yolo_class_id，则标记为 yolo 来源
    if dish_data.get("yolo_class_id") is not None:
        dish_data["source"] = "yolo"
    else:
        dish_data["source"] = "manual"
    
    return await create_dish(dish_data)


@router.put("/{dish_id}", response_model=dict)
async def modify_dish(dish_id: str, updates: DishUpdate):
    """更新菜品信息"""
    update_data = updates.model_dump(exclude_unset=True)
    
    result = await update_dish(dish_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="菜品不存在")
    
    return result


@router.delete("/{dish_id}")
async def remove_dish(dish_id: str):
    """删除菜品"""
    success = await delete_dish(dish_id)
    if not success:
        raise HTTPException(status_code=404, detail="菜品不存在")
    
    return {"success": True, "message": "菜品已删除"}


@router.get("/categories/list")
async def list_categories():
    """获取所有菜品分类"""
    return [
        {"value": "staple", "label": "主食", "label_en": "Staple"},
        {"value": "meat", "label": "荤菜", "label_en": "Meat"},
        {"value": "vegetable", "label": "素菜", "label_en": "Vegetable"},
        {"value": "soup", "label": "汤类", "label_en": "Soup"},
        {"value": "drink", "label": "饮品", "label_en": "Drink"},
        {"value": "dessert", "label": "甜点", "label_en": "Dessert"},
        {"value": "other", "label": "其他", "label_en": "Other"}
    ]
