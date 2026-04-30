"""
YOLOv13 服务模块
使用训练好的 best.pt 模型进行菜品识别
"""
import time
import base64
import io
import sys
import traceback
from typing import Dict
from pathlib import Path

# 确保自定义模块可被导入
_services_dir = str(Path(__file__).parent)
if _services_dir not in sys.path:
    sys.path.insert(0, _services_dir)

# 应用补丁（必须在 import ultralytics 之前）
from model_patches import apply_patches
apply_patches()

import numpy as np
from PIL import Image
from ultralytics import YOLO
from database.db import get_yolo_dish_by_class_id

# ============================================
# 模型配置
# ============================================

# 模型文件路径（使用项目根目录下的 best.pt）
MODEL_PATH = r"C:\Users\ASUS\Desktop\1111\best.pt"

# 模型是否已加载
MODEL_LOADED = False

# ============================================


class YOLOService:
    """YOLOv13 菜品识别服务"""
    
    def __init__(self):
        self.model = None
        self.class_names = {}
        self.confidence_threshold = 0.15  # 降低默认阈值，提高召回率
        self.iou_threshold = 0.5          # NMS IoU 阈值
        self.imgsz = 640                  # 推理输入尺寸
        self._load_default_model()
        
    def _load_default_model(self):
        """启动时自动加载默认模型"""
        if Path(MODEL_PATH).exists():
            self.load_model(MODEL_PATH)
        else:
            print(f"[ERROR] 模型文件不存在: {MODEL_PATH}")
            print(f"[ERROR] 请确认 best.pt 文件在正确位置")
        
    def load_model(self, model_path: str) -> bool:
        """
        加载 YOLO 模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            是否加载成功
        """
        global MODEL_LOADED
        
        try:
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            MODEL_LOADED = True
            print(f"[OK] YOLO 模型加载成功: {model_path}")
            print(f"[OK] 可识别 {len(self.class_names)} 种菜品")
            return True
        except Exception as e:
            print(f"[ERROR] 模型加载失败: {e}")
            traceback.print_exc()
            MODEL_LOADED = False
            return False
    
    def set_confidence_threshold(self, threshold: float):
        """设置置信度阈值"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        图像预处理：自动旋转、格式转换、合理缩放
        
        Args:
            image: PIL 图像
            
        Returns:
            预处理后的图像
        """
        # 1. 处理 EXIF 旋转信息（手机拍照常见问题）
        try:
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass
        
        # 2. 确保图像为 RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 3. 如果图像太小，适当放大以提高识别率
        w, h = image.size
        min_dim = min(w, h)
        if min_dim < 320:
            scale = 320 / min_dim
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        
        # 4. 如果图像过大（>4K），缩小以加速推理且避免内存问题
        max_dim = max(w, h)
        if max_dim > 3840:
            scale = 3840 / max_dim
            image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        
        return image
    
    def _deduplicate_detections(self, detections: list) -> list:
        """
        对同类别的重叠检测框去重，保留置信度最高的
        
        Args:
            detections: 检测结果列表
            
        Returns:
            去重后的检测结果
        """
        if len(detections) <= 1:
            return detections
        
        # 按置信度降序排列
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        
        kept = []
        for det in detections:
            is_duplicate = False
            for existing in kept:
                # 同一类菜品才检查重叠
                if det.get("dish_id") == existing.get("dish_id") or det.get("name") == existing.get("name"):
                    # 计算 IoU
                    iou = self._compute_iou(det["bbox"], existing["bbox"])
                    if iou > 0.4:  # 重叠超过 40% 视为重复
                        is_duplicate = True
                        break
            if not is_duplicate:
                kept.append(det)
        
        return kept
    
    @staticmethod
    def _compute_iou(box1: list, box2: list) -> float:
        """计算两个框的 IoU"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        
        return inter / union if union > 0 else 0
    
    async def predict(self, image_base64: str) -> Dict:
        """
        识别图像中的菜品
        
        Args:
            image_base64: Base64 编码的图像
            
        Returns:
            识别结果字典
        """
        start_time = time.time()
        
        if not MODEL_LOADED or self.model is None:
            return {
                "success": False,
                "dishes": [],
                "unrecognized_count": 0,
                "processing_time_ms": 0,
                "message": "模型未加载，无法识别"
            }
        
        try:
            # 解码 Base64 图像
            image_data_str = image_base64.split(',')[1] if ',' in image_base64 else image_base64
            image_data = base64.b64decode(image_data_str)
            image = Image.open(io.BytesIO(image_data))
            
            # 图像预处理
            image = self._preprocess_image(image)
            
            # 运行 YOLO 推理（增加 imgsz 和 iou 参数）
            results = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                verbose=False,
                augment=False,        # 关闭TTA，提升速度
                max_det=50            # 最多检测50个目标
            )
            
            # 解析结果
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                    
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = self.class_names.get(class_id, f"unknown_{class_id}")
                    
                    # 从数据库匹配菜品
                    dish = await get_yolo_dish_by_class_id(class_id)
                    
                    if dish:
                        detections.append({
                            "dish_id": dish["id"],
                            "name": dish["name"],
                            "name_en": dish.get("name_en", class_name),
                            "confidence": round(confidence, 3),
                            "price": dish["price"],
                            "bbox": box.xyxy[0].tolist(),
                            "category": dish.get("category", "other"),
                            "nutrition": dish.get("nutrition")
                        })
                    else:
                        # 数据库中没有对应菜品时使用模型类名
                        detections.append({
                            "dish_id": f"yolo_{class_id}",
                            "name": class_name,
                            "name_en": class_name,
                            "confidence": round(confidence, 3),
                            "price": 0.0,
                            "bbox": box.xyxy[0].tolist(),
                            "category": "other",
                            "nutrition": None
                        })
            
            # 去重：移除同类菜品的重叠检测
            detections = self._deduplicate_detections(detections)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "dishes": detections,
                "unrecognized_count": 0,
                "processing_time_ms": round(processing_time, 2),
                "message": f"识别完成，检测到 {len(detections)} 个菜品"
            }
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            print(f"[ERROR] 识别失败: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "dishes": [],
                "unrecognized_count": 0,
                "processing_time_ms": round(processing_time, 2),
                "message": f"识别失败: {str(e)}"
            }


# 全局服务实例
yolo_service = YOLOService()


def get_model_status() -> Dict:
    """获取模型状态"""
    return {
        "loaded": MODEL_LOADED,
        "model_path": MODEL_PATH,
        "mode": "production" if MODEL_LOADED else "error",
        "class_count": len(yolo_service.class_names) if MODEL_LOADED else 0,
        "class_names": yolo_service.class_names if MODEL_LOADED else {},
        "message": "模型已就绪" if MODEL_LOADED else "模型加载失败"
    }
