"""
数据库模块 - 使用内存存储（可替换为实际数据库）
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"

# 内存数据库
_db: Dict[str, Dict] = {
    "dishes": {},
    "orders": {},
    "promotions": {},
    "recognition_logs": {},
    "settings": {}
}

# 默认系统设置
DEFAULT_SETTINGS = {
    "confidence_threshold": 0.3,
    "auto_recognize_interval": 3000,
    "model_path": None,
    "enable_logging": True
}

# YOLO 模型可识别的 36 种菜品
# class_id 与训练好的 best.pt 模型对应
SAMPLE_DISHES = [
    # 0: AW cola
    {"id": "dish_001", "name": "AW可乐", "name_en": "AW Cola", "price": 5.0, "category": "drink",
     "source": "yolo", "yolo_class_id": 0, "description": "AW根汁汽水",
     "allergens": [], "nutrition": {"calories": 170, "protein": 0, "carbohydrates": 46, "fat": 0, "fiber": 0, "sodium": 65},
     "stock": 100, "is_available": True},
    # 1: Beijing Beef
    {"id": "dish_002", "name": "北京牛肉", "name_en": "Beijing Beef", "price": 22.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 1, "description": "甜辣酱汁牛肉配青红椒",
     "allergens": ["大豆"], "nutrition": {"calories": 470, "protein": 26, "carbohydrates": 36, "fat": 24, "fiber": 2, "sodium": 890},
     "stock": 50, "is_available": True},
    # 2: Chow Mein
    {"id": "dish_003", "name": "炒面", "name_en": "Chow Mein", "price": 12.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 2, "description": "经典中式炒面",
     "allergens": ["小麦"], "nutrition": {"calories": 510, "protein": 13, "carbohydrates": 80, "fat": 16, "fiber": 4, "sodium": 980},
     "stock": 80, "is_available": True},
    # 3: Fried Rice
    {"id": "dish_004", "name": "炒饭", "name_en": "Fried Rice", "price": 14.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 3, "description": "蛋炒饭",
     "allergens": ["鸡蛋", "大豆"], "nutrition": {"calories": 520, "protein": 12, "carbohydrates": 85, "fat": 16, "fiber": 1, "sodium": 850},
     "stock": 80, "is_available": True},
    # 4: Hashbrown
    {"id": "dish_005", "name": "薯饼", "name_en": "Hashbrown", "price": 6.0, "category": "other",
     "source": "yolo", "yolo_class_id": 4, "description": "香脆薯饼",
     "allergens": [], "nutrition": {"calories": 150, "protein": 1, "carbohydrates": 15, "fat": 9, "fiber": 1, "sodium": 310},
     "stock": 100, "is_available": True},
    # 5: Honey Walnut Shrimp
    {"id": "dish_006", "name": "核桃虾", "name_en": "Honey Walnut Shrimp", "price": 28.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 5, "description": "蜂蜜核桃虾仁",
     "allergens": ["虾", "核桃", "鸡蛋"], "nutrition": {"calories": 360, "protein": 13, "carbohydrates": 35, "fat": 19, "fiber": 1, "sodium": 440},
     "stock": 40, "is_available": True},
    # 6: Kung Pao Chicken
    {"id": "dish_007", "name": "宫保鸡丁", "name_en": "Kung Pao Chicken", "price": 20.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 6, "description": "花生与鸡肉的经典搭配",
     "allergens": ["花生"], "nutrition": {"calories": 290, "protein": 16, "carbohydrates": 14, "fat": 19, "fiber": 1, "sodium": 780},
     "stock": 60, "is_available": True},
    # 7: String Bean Chicken Breast
    {"id": "dish_008", "name": "四季豆鸡胸", "name_en": "String Bean Chicken Breast", "price": 18.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 7, "description": "四季豆配嫩滑鸡胸肉",
     "allergens": [], "nutrition": {"calories": 190, "protein": 14, "carbohydrates": 13, "fat": 9, "fiber": 2, "sodium": 560},
     "stock": 60, "is_available": True},
    # 8: Super Greens
    {"id": "dish_009", "name": "时蔬拼盘", "name_en": "Super Greens", "price": 10.0, "category": "vegetable",
     "source": "yolo", "yolo_class_id": 8, "description": "混合新鲜蔬菜",
     "allergens": [], "nutrition": {"calories": 90, "protein": 6, "carbohydrates": 10, "fat": 3, "fiber": 5, "sodium": 420},
     "stock": 80, "is_available": True},
    # 9: The Original Orange Chicken
    {"id": "dish_010", "name": "橙汁鸡", "name_en": "The Original Orange Chicken", "price": 22.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 9, "description": "经典橙汁鸡块",
     "allergens": ["小麦", "鸡蛋"], "nutrition": {"calories": 490, "protein": 25, "carbohydrates": 51, "fat": 21, "fiber": 0, "sodium": 820},
     "stock": 50, "is_available": True},
    # 10: White Steamed Rice
    {"id": "dish_011", "name": "白米饭", "name_en": "White Steamed Rice", "price": 3.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 10, "description": "香软白米饭",
     "allergens": [], "nutrition": {"calories": 380, "protein": 7, "carbohydrates": 87, "fat": 0, "fiber": 0, "sodium": 0},
     "stock": 200, "is_available": True},
    # 11: black pepper rice bowl
    {"id": "dish_012", "name": "黑椒饭", "name_en": "Black Pepper Rice Bowl", "price": 16.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 11, "description": "黑椒酱配米饭",
     "allergens": ["大豆"], "nutrition": {"calories": 450, "protein": 15, "carbohydrates": 70, "fat": 12, "fiber": 2, "sodium": 730},
     "stock": 60, "is_available": True},
    # 12: burger
    {"id": "dish_013", "name": "汉堡", "name_en": "Burger", "price": 18.0, "category": "other",
     "source": "yolo", "yolo_class_id": 12, "description": "经典汉堡",
     "allergens": ["小麦", "鸡蛋"], "nutrition": {"calories": 540, "protein": 25, "carbohydrates": 40, "fat": 30, "fiber": 2, "sodium": 950},
     "stock": 50, "is_available": True},
    # 13: carrot_eggs
    {"id": "dish_014", "name": "胡萝卜炒蛋", "name_en": "Carrot Eggs", "price": 10.0, "category": "vegetable",
     "source": "yolo", "yolo_class_id": 13, "description": "胡萝卜炒鸡蛋",
     "allergens": ["鸡蛋"], "nutrition": {"calories": 160, "protein": 10, "carbohydrates": 8, "fat": 10, "fiber": 2, "sodium": 350},
     "stock": 70, "is_available": True},
    # 14: cheese burger
    {"id": "dish_015", "name": "芝士汉堡", "name_en": "Cheese Burger", "price": 22.0, "category": "other",
     "source": "yolo", "yolo_class_id": 14, "description": "芝士牛肉汉堡",
     "allergens": ["小麦", "牛奶", "鸡蛋"], "nutrition": {"calories": 630, "protein": 30, "carbohydrates": 42, "fat": 38, "fiber": 2, "sodium": 1100},
     "stock": 40, "is_available": True},
    # 15: chicken waffle
    {"id": "dish_016", "name": "鸡肉华夫饼", "name_en": "Chicken Waffle", "price": 20.0, "category": "other",
     "source": "yolo", "yolo_class_id": 15, "description": "炸鸡配华夫饼",
     "allergens": ["小麦", "鸡蛋", "牛奶"], "nutrition": {"calories": 580, "protein": 28, "carbohydrates": 48, "fat": 30, "fiber": 1, "sodium": 870},
     "stock": 40, "is_available": True},
    # 16: chicken_nuggets
    {"id": "dish_017", "name": "鸡块", "name_en": "Chicken Nuggets", "price": 12.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 16, "description": "香酥鸡块",
     "allergens": ["小麦"], "nutrition": {"calories": 270, "protein": 14, "carbohydrates": 16, "fat": 17, "fiber": 0, "sodium": 540},
     "stock": 80, "is_available": True},
    # 17: chinese_cabbage
    {"id": "dish_018", "name": "大白菜", "name_en": "Chinese Cabbage", "price": 8.0, "category": "vegetable",
     "source": "yolo", "yolo_class_id": 17, "description": "清炒大白菜",
     "allergens": [], "nutrition": {"calories": 60, "protein": 2, "carbohydrates": 8, "fat": 2, "fiber": 3, "sodium": 280},
     "stock": 90, "is_available": True},
    # 18: chinese_sausage
    {"id": "dish_019", "name": "中式香肠", "name_en": "Chinese Sausage", "price": 12.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 18, "description": "广式腊肠",
     "allergens": [], "nutrition": {"calories": 320, "protein": 16, "carbohydrates": 6, "fat": 26, "fiber": 0, "sodium": 700},
     "stock": 60, "is_available": True},
    # 19: crispy corn
    {"id": "dish_020", "name": "脆玉米", "name_en": "Crispy Corn", "price": 8.0, "category": "other",
     "source": "yolo", "yolo_class_id": 19, "description": "酥脆玉米粒",
     "allergens": [], "nutrition": {"calories": 200, "protein": 3, "carbohydrates": 28, "fat": 10, "fiber": 2, "sodium": 400},
     "stock": 70, "is_available": True},
    # 20: curry
    {"id": "dish_021", "name": "咖喱", "name_en": "Curry", "price": 16.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 20, "description": "日式咖喱",
     "allergens": ["小麦"], "nutrition": {"calories": 350, "protein": 14, "carbohydrates": 30, "fat": 18, "fiber": 3, "sodium": 650},
     "stock": 50, "is_available": True},
    # 21: french fries
    {"id": "dish_022", "name": "薯条", "name_en": "French Fries", "price": 8.0, "category": "other",
     "source": "yolo", "yolo_class_id": 21, "description": "金黄薯条",
     "allergens": [], "nutrition": {"calories": 340, "protein": 4, "carbohydrates": 44, "fat": 16, "fiber": 4, "sodium": 230},
     "stock": 100, "is_available": True},
    # 22: fried chicken (western style)
    {"id": "dish_023", "name": "炸鸡", "name_en": "Fried Chicken", "price": 18.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 22, "description": "美式炸鸡",
     "allergens": ["小麦"], "nutrition": {"calories": 400, "protein": 28, "carbohydrates": 15, "fat": 26, "fiber": 0, "sodium": 680},
     "stock": 50, "is_available": True},
    # 23: fried_chicken (chinese style)
    {"id": "dish_024", "name": "中式炸鸡", "name_en": "Chinese Fried Chicken", "price": 16.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 23, "description": "中式香炸鸡块",
     "allergens": ["小麦"], "nutrition": {"calories": 380, "protein": 26, "carbohydrates": 14, "fat": 24, "fiber": 0, "sodium": 620},
     "stock": 50, "is_available": True},
    # 24: fried_dumplings
    {"id": "dish_025", "name": "煎饺", "name_en": "Fried Dumplings", "price": 12.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 24, "description": "香脆煎饺",
     "allergens": ["小麦"], "nutrition": {"calories": 280, "protein": 12, "carbohydrates": 30, "fat": 12, "fiber": 1, "sodium": 600},
     "stock": 60, "is_available": True},
    # 25: fried_eggs
    {"id": "dish_026", "name": "煎蛋", "name_en": "Fried Eggs", "price": 5.0, "category": "other",
     "source": "yolo", "yolo_class_id": 25, "description": "香煎荷包蛋",
     "allergens": ["鸡蛋"], "nutrition": {"calories": 90, "protein": 6, "carbohydrates": 0, "fat": 7, "fiber": 0, "sodium": 150},
     "stock": 100, "is_available": True},
    # 26: mango chicken pocket
    {"id": "dish_027", "name": "芒果鸡肉口袋饼", "name_en": "Mango Chicken Pocket", "price": 20.0, "category": "other",
     "source": "yolo", "yolo_class_id": 26, "description": "芒果鸡肉口袋饼",
     "allergens": ["小麦"], "nutrition": {"calories": 420, "protein": 22, "carbohydrates": 45, "fat": 16, "fiber": 2, "sodium": 580},
     "stock": 40, "is_available": True},
    # 27: mozza burger
    {"id": "dish_028", "name": "马苏里拉汉堡", "name_en": "Mozza Burger", "price": 24.0, "category": "other",
     "source": "yolo", "yolo_class_id": 27, "description": "马苏里拉芝士汉堡",
     "allergens": ["小麦", "牛奶"], "nutrition": {"calories": 650, "protein": 32, "carbohydrates": 44, "fat": 40, "fiber": 2, "sodium": 1050},
     "stock": 40, "is_available": True},
    # 28: mung_bean_sprouts
    {"id": "dish_029", "name": "绿豆芽", "name_en": "Mung Bean Sprouts", "price": 8.0, "category": "vegetable",
     "source": "yolo", "yolo_class_id": 28, "description": "清炒绿豆芽",
     "allergens": [], "nutrition": {"calories": 50, "protein": 3, "carbohydrates": 6, "fat": 1, "fiber": 2, "sodium": 200},
     "stock": 90, "is_available": True},
    # 29: nugget
    {"id": "dish_030", "name": "鸡米花", "name_en": "Nugget", "price": 10.0, "category": "meat",
     "source": "yolo", "yolo_class_id": 29, "description": "一口鸡米花",
     "allergens": ["小麦"], "nutrition": {"calories": 250, "protein": 12, "carbohydrates": 15, "fat": 15, "fiber": 0, "sodium": 500},
     "stock": 80, "is_available": True},
    # 30: perkedel
    {"id": "dish_031", "name": "印尼土豆饼", "name_en": "Perkedel", "price": 8.0, "category": "other",
     "source": "yolo", "yolo_class_id": 30, "description": "印尼风味土豆饼",
     "allergens": ["鸡蛋"], "nutrition": {"calories": 180, "protein": 5, "carbohydrates": 20, "fat": 9, "fiber": 2, "sodium": 350},
     "stock": 60, "is_available": True},
    # 31: rice
    {"id": "dish_032", "name": "米饭", "name_en": "Rice", "price": 3.0, "category": "staple",
     "source": "yolo", "yolo_class_id": 31, "description": "普通米饭",
     "allergens": [], "nutrition": {"calories": 130, "protein": 2.5, "carbohydrates": 28, "fat": 0.3, "fiber": 0.4, "sodium": 1},
     "stock": 200, "is_available": True},
    # 32: sprite
    {"id": "dish_033", "name": "雪碧", "name_en": "Sprite", "price": 5.0, "category": "drink",
     "source": "yolo", "yolo_class_id": 32, "description": "冰镇雪碧",
     "allergens": [], "nutrition": {"calories": 140, "protein": 0, "carbohydrates": 38, "fat": 0, "fiber": 0, "sodium": 65},
     "stock": 100, "is_available": True},
    # 33: tostitos cheese dip sauce
    {"id": "dish_034", "name": "芝士蘸酱", "name_en": "Tostitos Cheese Dip Sauce", "price": 6.0, "category": "other",
     "source": "yolo", "yolo_class_id": 33, "description": "多力多滋芝士蘸酱",
     "allergens": ["牛奶"], "nutrition": {"calories": 40, "protein": 1, "carbohydrates": 3, "fat": 3, "fiber": 0, "sodium": 280},
     "stock": 80, "is_available": True},
    # 34: triangle_hash_brown
    {"id": "dish_035", "name": "三角薯饼", "name_en": "Triangle Hash Brown", "price": 6.0, "category": "other",
     "source": "yolo", "yolo_class_id": 34, "description": "三角形香脆薯饼",
     "allergens": [], "nutrition": {"calories": 140, "protein": 1, "carbohydrates": 14, "fat": 8, "fiber": 1, "sodium": 290},
     "stock": 100, "is_available": True},
    # 35: water_spinach
    {"id": "dish_036", "name": "空心菜", "name_en": "Water Spinach", "price": 10.0, "category": "vegetable",
     "source": "yolo", "yolo_class_id": 35, "description": "清炒空心菜",
     "allergens": [], "nutrition": {"calories": 70, "protein": 3, "carbohydrates": 8, "fat": 2, "fiber": 3, "sodium": 250},
     "stock": 80, "is_available": True},
]


# 示例未识别库菜品（手动添加）
MANUAL_DISHES = [
    {
        "id": "manual_001",
        "name": "鱼香肉丝",
        "name_en": "Yu-Shiang Pork",
        "price": 16.0,
        "category": "meat",
        "source": "manual",
        "yolo_class_id": None,
        "description": "经典川菜",
        "allergens": [],
        "nutrition": {"calories": 280, "protein": 18, "carbohydrates": 15, "fat": 16, "fiber": 2, "sodium": 750},
        "stock": 40,
        "is_available": True
    },
    {
        "id": "manual_002",
        "name": "麻婆豆腐",
        "name_en": "Mapo Tofu",
        "price": 14.0,
        "category": "vegetable",
        "source": "manual",
        "yolo_class_id": None,
        "description": "麻辣鲜香",
        "allergens": ["大豆"],
        "nutrition": {"calories": 200, "protein": 14, "carbohydrates": 8, "fat": 12, "fiber": 2, "sodium": 900},
        "stock": 45,
        "is_available": True
    },
    {
        "id": "manual_003",
        "name": "宫保鸡丁",
        "name_en": "Kung Pao Chicken",
        "price": 18.0,
        "category": "meat",
        "source": "manual",
        "yolo_class_id": None,
        "description": "花生与鸡肉的完美搭配",
        "allergens": ["花生"],
        "nutrition": {"calories": 320, "protein": 22, "carbohydrates": 12, "fat": 20, "fiber": 1, "sodium": 680},
        "stock": 35,
        "is_available": True
    }
]

async def init_db():
    """初始化数据库"""
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载或初始化菜品数据
    now = datetime.now().isoformat()
    
    for dish in SAMPLE_DISHES + MANUAL_DISHES:
        dish["created_at"] = now
        dish["updated_at"] = now
        _db["dishes"][dish["id"]] = dish
    
    # 初始化系统设置
    _db["settings"] = DEFAULT_SETTINGS.copy()
    
    print(f"[INFO] 已加载 {len(_db['dishes'])} 个菜品")

def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"

# ============ 菜品操作 ============

async def get_all_dishes() -> List[Dict]:
    """获取所有菜品"""
    return list(_db["dishes"].values())

async def get_dish_by_id(dish_id: str) -> Optional[Dict]:
    """根据ID获取菜品"""
    return _db["dishes"].get(dish_id)

async def get_dishes_by_source(source: str) -> List[Dict]:
    """根据来源获取菜品"""
    return [d for d in _db["dishes"].values() if d.get("source") == source]

async def get_yolo_dish_by_class_id(class_id: int) -> Optional[Dict]:
    """根据YOLO类别ID获取菜品"""
    for dish in _db["dishes"].values():
        if dish.get("yolo_class_id") == class_id:
            return dish
    return None

async def create_dish(dish_data: Dict) -> Dict:
    """创建菜品"""
    dish_id = generate_id("dish_")
    now = datetime.now().isoformat()
    
    dish = {
        **dish_data,
        "id": dish_id,
        "created_at": now,
        "updated_at": now,
        "stock": dish_data.get("stock", 100),
        "is_available": True
    }
    
    _db["dishes"][dish_id] = dish
    return dish

async def update_dish(dish_id: str, update_data: Dict) -> Optional[Dict]:
    """更新菜品"""
    if dish_id not in _db["dishes"]:
        return None
    
    dish = _db["dishes"][dish_id]
    for key, value in update_data.items():
        if value is not None:
            dish[key] = value
    
    dish["updated_at"] = datetime.now().isoformat()
    return dish

async def delete_dish(dish_id: str) -> bool:
    """删除菜品"""
    if dish_id in _db["dishes"]:
        del _db["dishes"][dish_id]
        return True
    return False

# ============ 订单操作 ============

async def create_order(order_data: Dict) -> Dict:
    """创建订单"""
    order_id = generate_id("order_")
    now = datetime.now().isoformat()
    
    order = {
        **order_data,
        "id": order_id,
        "created_at": now
    }
    
    _db["orders"][order_id] = order
    return order

async def get_orders(limit: int = 50) -> List[Dict]:
    """获取订单列表"""
    orders = sorted(
        _db["orders"].values(),
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )
    return orders[:limit]

async def get_order_by_id(order_id: str) -> Optional[Dict]:
    """根据ID获取订单"""
    return _db["orders"].get(order_id)

# ============ 促销操作 ============

async def get_all_promotions() -> List[Dict]:
    """获取所有促销"""
    return list(_db["promotions"].values())

async def get_active_promotions() -> List[Dict]:
    """获取有效促销"""
    now = datetime.now()
    active = []
    
    for promo in _db["promotions"].values():
        if not promo.get("is_active"):
            continue
        
        start = promo.get("start_time")
        end = promo.get("end_time")
        
        if start and datetime.fromisoformat(start) > now:
            continue
        if end and datetime.fromisoformat(end) < now:
            continue
        
        active.append(promo)
    
    return active

async def create_promotion(promo_data: Dict) -> Dict:
    """创建促销"""
    promo_id = generate_id("promo_")
    now = datetime.now().isoformat()
    
    promo = {
        **promo_data,
        "id": promo_id,
        "created_at": now
    }
    
    _db["promotions"][promo_id] = promo
    return promo

async def update_promotion(promo_id: str, update_data: Dict) -> Optional[Dict]:
    """更新促销"""
    if promo_id not in _db["promotions"]:
        return None
    
    promo = _db["promotions"][promo_id]
    for key, value in update_data.items():
        if value is not None:
            promo[key] = value
    
    return promo

async def delete_promotion(promo_id: str) -> bool:
    """删除促销"""
    if promo_id in _db["promotions"]:
        del _db["promotions"][promo_id]
        return True
    return False

# ============ 识别日志操作 ============

async def create_recognition_log(log_data: Dict) -> Dict:
    """创建识别日志"""
    log_id = generate_id("log_")
    now = datetime.now().isoformat()
    
    log = {
        **log_data,
        "id": log_id,
        "created_at": now
    }
    
    _db["recognition_logs"][log_id] = log
    return log

async def get_recognition_logs(limit: int = 100) -> List[Dict]:
    """获取识别日志"""
    logs = sorted(
        _db["recognition_logs"].values(),
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )
    return logs[:limit]

# ============ 系统设置操作 ============

async def get_settings() -> Dict:
    """获取系统设置"""
    return _db["settings"].copy()

async def update_settings(update_data: Dict) -> Dict:
    """更新系统设置"""
    for key, value in update_data.items():
        if value is not None and key in DEFAULT_SETTINGS:
            _db["settings"][key] = value
    return _db["settings"].copy()

# ============ 统计操作 ============

async def get_sales_stats(days: int = 7) -> List[Dict]:
    """获取销售统计"""
    from datetime import timedelta
    from collections import defaultdict
    
    stats = []
    today = datetime.now().date()
    
    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.isoformat()
        
        # 统计当天订单
        day_orders = [
            o for o in _db["orders"].values()
            if o.get("created_at", "").startswith(date_str)
        ]
        
        # 统计菜品销量
        dish_sales = defaultdict(int)
        for order in day_orders:
            for item in order.get("items", []):
                dish_sales[item["name"]] += item.get("quantity", 1)
        
        # 热门菜品
        top_dishes = sorted(
            [{"name": k, "count": v} for k, v in dish_sales.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        stats.append({
            "date": date_str,
            "total_orders": len(day_orders),
            "total_revenue": sum(o.get("total_amount", 0) for o in day_orders),
            "top_dishes": top_dishes
        })
    
    return stats

async def get_dashboard_stats() -> Dict:
    """获取仪表盘统计"""
    today = datetime.now().date().isoformat()
    
    today_orders = [
        o for o in _db["orders"].values()
        if o.get("created_at", "").startswith(today)
    ]
    
    low_stock = [
        d for d in _db["dishes"].values()
        if d.get("stock", 0) < 20
    ]
    
    return {
        "today_orders": len(today_orders),
        "today_revenue": sum(o.get("total_amount", 0) for o in today_orders),
        "total_dishes": len(_db["dishes"]),
        "low_stock_count": len(low_stock)
    }

# ============ 库存操作 ============

async def update_stock(dish_id: str, quantity: int) -> Optional[Dict]:
    """更新库存"""
    if dish_id not in _db["dishes"]:
        return None
    
    dish = _db["dishes"][dish_id]
    dish["stock"] = max(0, dish.get("stock", 0) + quantity)
    dish["updated_at"] = datetime.now().isoformat()
    
    return dish

async def get_low_stock_dishes(threshold: int = 20) -> List[Dict]:
    """获取低库存菜品"""
    return [
        d for d in _db["dishes"].values()
        if d.get("stock", 0) < threshold
    ]
