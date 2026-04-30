"""
系统设置 API
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from database.db import get_settings, update_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    """设置更新请求"""
    confidence_threshold: Optional[float] = Field(None, ge=0, le=1, description="识别置信度阈值")
    auto_recognize_interval: Optional[int] = Field(None, ge=1000, le=10000, description="自动识别间隔(毫秒)")
    model_path: Optional[str] = Field(None, description="YOLO模型路径")
    enable_logging: Optional[bool] = Field(None, description="启用识别日志")


@router.get("/")
async def get_system_settings():
    """获取系统设置"""
    return await get_settings()


@router.put("/")
async def update_system_settings(updates: SettingsUpdate):
    """更新系统设置"""
    update_data = updates.model_dump(exclude_unset=True)
    result = await update_settings(update_data)
    return {
        "success": True,
        "settings": result
    }


@router.get("/confidence-threshold")
async def get_confidence_threshold():
    """获取置信度阈值"""
    settings = await get_settings()
    return {
        "confidence_threshold": settings.get("confidence_threshold", 0.15)
    }


@router.put("/confidence-threshold")
async def set_confidence_threshold(threshold: float):
    """设置置信度阈值"""
    if not 0 <= threshold <= 1:
        return {"success": False, "message": "阈值必须在 0-1 之间"}
    
    await update_settings({"confidence_threshold": threshold})
    return {
        "success": True,
        "confidence_threshold": threshold
    }
