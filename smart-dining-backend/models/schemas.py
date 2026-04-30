"""
数据模型 - Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============ 枚举类型 ============

class DishCategory(str, Enum):
    """菜品分类"""
    STAPLE = "staple"       # 主食
    MEAT = "meat"           # 荤菜
    VEGETABLE = "vegetable" # 素菜
    SOUP = "soup"           # 汤类
    DRINK = "drink"         # 饮品
    DESSERT = "dessert"     # 甜点
    OTHER = "other"         # 其他

class DishSource(str, Enum):
    """菜品来源"""
    YOLO = "yolo"           # YOLO模型可识别
    MANUAL = "manual"       # 手动添加（未识别库）

# ============ 营养信息 ============

class NutritionInfo(BaseModel):
    """营养信息"""
    calories: float = Field(0, description="卡路里 (kcal)")
    protein: float = Field(0, description="蛋白质 (g)")
    carbohydrates: float = Field(0, description="碳水化合物 (g)")
    fat: float = Field(0, description="脂肪 (g)")
    fiber: float = Field(0, description="膳食纤维 (g)")
    sodium: float = Field(0, description="钠 (mg)")

# ============ 菜品模型 ============

class DishBase(BaseModel):
    """菜品基础信息"""
    name: str = Field(..., description="菜品名称")
    name_en: Optional[str] = Field(None, description="英文名称")
    price: float = Field(..., ge=0, description="价格")
    category: DishCategory = Field(DishCategory.OTHER, description="分类")
    description: Optional[str] = Field(None, description="描述")
    image_url: Optional[str] = Field(None, description="图片URL")
    allergens: List[str] = Field(default_factory=list, description="过敏原")
    nutrition: Optional[NutritionInfo] = Field(None, description="营养信息")

class DishCreate(DishBase):
    """创建菜品"""
    source: DishSource = Field(DishSource.MANUAL, description="菜品来源")
    yolo_class_id: Optional[int] = Field(None, description="YOLO类别ID")

class Dish(DishBase):
    """菜品完整信息"""
    id: str
    source: DishSource
    yolo_class_id: Optional[int] = None
    stock: int = Field(100, description="库存数量")
    is_available: bool = Field(True, description="是否可用")
    created_at: datetime
    updated_at: datetime

class DishUpdate(BaseModel):
    """更新菜品"""
    name: Optional[str] = None
    name_en: Optional[str] = None
    price: Optional[float] = None
    category: Optional[DishCategory] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    allergens: Optional[List[str]] = None
    nutrition: Optional[NutritionInfo] = None
    stock: Optional[int] = None
    is_available: Optional[bool] = None

# ============ 识别结果 ============

class RecognitionResult(BaseModel):
    """单个识别结果"""
    dish_id: str = Field(..., description="菜品ID")
    name: str = Field(..., description="菜品名称")
    name_en: Optional[str] = Field(None, description="英文名称")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    price: float = Field(..., description="价格")
    bbox: List[float] = Field(default_factory=list, description="边界框 [x1,y1,x2,y2]")
    category: DishCategory = Field(DishCategory.OTHER, description="分类")
    nutrition: Optional[NutritionInfo] = Field(None, description="营养信息")

class RecognitionResponse(BaseModel):
    """识别响应"""
    success: bool
    dishes: List[RecognitionResult] = Field(default_factory=list)
    unrecognized_count: int = Field(0, description="未识别菜品数量")
    processing_time_ms: float = Field(0, description="处理时间(毫秒)")
    log_id: Optional[str] = Field(None, description="识别日志ID")
    message: Optional[str] = None

# ============ 订单模型 ============

class OrderItem(BaseModel):
    """订单项"""
    dish_id: str
    name: str
    price: float
    quantity: int = Field(1, ge=1)
    is_manual: bool = Field(False, description="是否手动添加")

class OrderCreate(BaseModel):
    """创建订单"""
    items: List[OrderItem]
    total_amount: float
    recognition_log_id: Optional[str] = None

class Order(BaseModel):
    """订单"""
    id: str
    items: List[OrderItem]
    total_amount: float
    created_at: datetime
    recognition_log_id: Optional[str] = None

# ============ 促销模型 ============

class PromotionType(str, Enum):
    """促销类型"""
    DISCOUNT = "discount"   # 折扣
    FIXED = "fixed"         # 固定减价
    BUNDLE = "bundle"       # 套餐

class PromotionCreate(BaseModel):
    """创建促销"""
    name: str
    type: PromotionType
    discount_value: float = Field(0, description="折扣值或减价金额")
    min_amount: float = Field(0, description="最低消费金额")
    applicable_dishes: List[str] = Field(default_factory=list, description="适用菜品")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: bool = True

class Promotion(PromotionCreate):
    """促销"""
    id: str
    created_at: datetime

# ============ 用户设置 ============

class UserPreferences(BaseModel):
    """用户偏好设置"""
    allergens: List[str] = Field(default_factory=list, description="过敏原")
    dietary_restrictions: List[str] = Field(default_factory=list, description="饮食限制")
    language: str = Field("zh", description="语言偏好")
    voice_enabled: bool = Field(True, description="语音播报")

# ============ 系统设置 ============

class SystemSettings(BaseModel):
    """系统设置"""
    confidence_threshold: float = Field(0.7, ge=0, le=1, description="识别置信度阈值")
    auto_recognize_interval: int = Field(3000, description="自动识别间隔(毫秒)")
    model_path: Optional[str] = Field(None, description="YOLO模型路径")
    enable_logging: bool = Field(True, description="启用识别日志")

# ============ 统计模型 ============

class SalesStats(BaseModel):
    """销售统计"""
    date: str
    total_orders: int
    total_revenue: float
    top_dishes: List[dict]

class DashboardStats(BaseModel):
    """仪表盘统计"""
    today_orders: int
    today_revenue: float
    total_dishes: int
    low_stock_count: int
