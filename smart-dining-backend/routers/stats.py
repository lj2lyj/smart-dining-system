"""
销售统计 API
"""
from fastapi import APIRouter, Query
from typing import List

from database.db import get_sales_stats, get_dashboard_stats, get_recognition_logs

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard():
    """
    获取仪表盘数据
    
    返回今日订单数、今日收入、菜品总数、低库存数量
    """
    return await get_dashboard_stats()


@router.get("/sales")
async def get_sales(days: int = Query(7, ge=1, le=30, description="统计天数")):
    """
    获取销售统计
    
    返回每日订单数、收入和热门菜品
    """
    return await get_sales_stats(days)


@router.get("/recognition-logs", response_model=List[dict])
async def get_logs(limit: int = Query(100, ge=1, le=500)):
    """
    获取识别日志
    
    用于问题追溯和系统优化
    """
    return await get_recognition_logs(limit)
