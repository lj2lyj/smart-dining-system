"""
图像识别 API
"""
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from services.yolo_service import yolo_service, get_model_status
from database.db import create_recognition_log, get_settings

router = APIRouter()


class RecognizeRequest(BaseModel):
    """识别请求"""
    image: str  # Base64 编码的图像
    auto_log: bool = True  # 是否自动记录日志


class RecognizeResponse(BaseModel):
    """识别响应"""
    success: bool
    dishes: list
    unrecognized_count: int
    processing_time_ms: float
    log_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/recognize", response_model=RecognizeResponse)
async def recognize_dishes(request: RecognizeRequest):
    """
    识别菜品
    
    接收 Base64 编码的图像，返回识别到的菜品列表
    """
    try:
        settings = await get_settings()
        yolo_service.set_confidence_threshold(settings.get("confidence_threshold", 0.3))
        
        result = await yolo_service.predict(request.image)
        
        log_id = None
        if request.auto_log and settings.get("enable_logging", True):
            log = await create_recognition_log({
                "image_size": len(request.image),
                "dishes_count": len(result.get("dishes", [])),
                "unrecognized_count": result.get("unrecognized_count", 0),
                "processing_time_ms": result.get("processing_time_ms", 0)
            })
            log_id = log["id"]
        
        return RecognizeResponse(
            success=result.get("success", True),
            dishes=result.get("dishes", []),
            unrecognized_count=result.get("unrecognized_count", 0),
            processing_time_ms=result.get("processing_time_ms", 0),
            log_id=log_id,
            message=result.get("message")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/upload", response_model=RecognizeResponse)
async def recognize_uploaded_image(file: UploadFile = File(...)):
    """
    上传图片识别菜品
    
    接收上传的图片文件，返回识别到的菜品列表
    支持 jpg、png、webp 等常见图片格式
    """
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif"]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {file.content_type}，请上传 jpg/png/webp 格式")
    
    try:
        # 读取文件内容并转为 base64
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="上传的文件为空")
        if len(contents) > 20 * 1024 * 1024:  # 20MB 限制
            raise HTTPException(status_code=400, detail="图片文件过大，请上传小于 20MB 的图片")
        
        image_base64 = base64.b64encode(contents).decode("utf-8")
        
        # 获取系统设置
        settings = await get_settings()
        yolo_service.set_confidence_threshold(settings.get("confidence_threshold", 0.3))
        
        # 执行识别
        result = await yolo_service.predict(image_base64)
        
        # 记录识别日志
        log_id = None
        if settings.get("enable_logging", True):
            log = await create_recognition_log({
                "image_size": len(contents),
                "dishes_count": len(result.get("dishes", [])),
                "unrecognized_count": result.get("unrecognized_count", 0),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "source": "upload",
                "filename": file.filename
            })
            log_id = log["id"]
        
        return RecognizeResponse(
            success=result.get("success", True),
            dishes=result.get("dishes", []),
            unrecognized_count=result.get("unrecognized_count", 0),
            processing_time_ms=result.get("processing_time_ms", 0),
            log_id=log_id,
            message=result.get("message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片识别失败: {str(e)}")


@router.get("/status")
async def get_recognition_status():
    """
    获取识别服务状态
    
    返回模型加载状态和配置信息
    """
    settings = await get_settings()
    model_status = get_model_status()
    
    return {
        "model": model_status,
        "settings": {
            "confidence_threshold": settings.get("confidence_threshold", 0.3),
            "enable_logging": settings.get("enable_logging", True)
        }
    }
