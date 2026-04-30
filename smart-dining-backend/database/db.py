"""
数据库模块 - MySQL 实现 (通过 PHPStudy MySQL)
使用 aiomysql 连接池进行异步数据库操作
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import uuid

import aiomysql
from database.db_config import DB_CONFIG

# 全局连接池
_pool: Optional[aiomysql.Pool] = None

# 默认系统设置
DEFAULT_SETTINGS = {
    "confidence_threshold": 0.15,
    "auto_recognize_interval": 3000,
    "model_path": None,
    "enable_logging": True
}


def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


async def _get_pool() -> aiomysql.Pool:
    """获取连接池（懒初始化）"""
    global _pool
    if _pool is None or _pool.closed:
        _pool = await aiomysql.create_pool(**DB_CONFIG)
    return _pool


async def _execute(sql: str, args=None, fetchone=False, fetchall=False):
    """执行 SQL 并返回结果"""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            if fetchone:
                return await cur.fetchone()
            if fetchall:
                return await cur.fetchall()
            return cur.lastrowid


def _parse_json_fields(row: dict, fields: list) -> dict:
    """解析行中的 JSON 字段"""
    if row is None:
        return None
    result = dict(row)
    for f in fields:
        val = result.get(f)
        if val is None:
            continue
        if isinstance(val, str):
            try:
                result[f] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
        # 如果已经是 dict/list 就不用转换

    # 转换 tinyint -> bool (is_available, is_active 等)
    for bf in ("is_available", "is_active"):
        if bf in result:
            result[bf] = bool(result[bf])

    # 遍历所有值，类型转换
    for k, v in list(result.items()):
        if hasattr(v, 'as_tuple'):  # Decimal -> float
            result[k] = float(v)
        elif isinstance(v, datetime):  # datetime -> ISO string
            result[k] = v.isoformat()

    return result


def _parse_dish(row: dict) -> Optional[dict]:
    """解析菜品行"""
    return _parse_json_fields(row, ["allergens", "nutrition"])


def _parse_order(row: dict) -> Optional[dict]:
    """解析订单行"""
    return _parse_json_fields(row, ["items"])


def _parse_promo(row: dict) -> Optional[dict]:
    """解析促销行"""
    return _parse_json_fields(row, ["applicable_dishes"])


# ============================================
# 初始化
# ============================================

async def init_db():
    """初始化数据库 - 自动建表并插入初始数据"""
    # 先用不指定 db 的连接创建数据库
    try:
        conn = await aiomysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            charset="utf8mb4",
            autocommit=True
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "CREATE DATABASE IF NOT EXISTS `{}` "
                "DEFAULT CHARACTER SET utf8mb4 "
                "DEFAULT COLLATE utf8mb4_unicode_ci".format(DB_CONFIG["db"])
            )
        conn.close()
    except Exception as e:
        print(f"[ERROR] 无法连接 MySQL: {e}")
        print(f"[ERROR] 请确认 PHPStudy 中 MySQL 已启动，连接信息: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        raise

    # 执行建表 SQL
    schema_path = Path(__file__).parent / "schema.sql"
    if schema_path.exists():
        sql_content = schema_path.read_text(encoding="utf-8")
        pool = await _get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for statement in sql_content.split(";"):
                    # 去掉注释行，只保留有效 SQL
                    lines = [l for l in statement.split("\n") 
                             if l.strip() and not l.strip().startswith("--")]
                    stmt = "\n".join(lines).strip()
                    if not stmt:
                        continue
                    # 跳过 CREATE DATABASE / USE（已在上面手动执行）
                    stmt_upper = stmt.upper().lstrip()
                    if stmt_upper.startswith("CREATE DATABASE") or stmt_upper.startswith("USE "):
                        continue
                    try:
                        await cur.execute(stmt)
                    except Exception as e:
                        err_str = str(e).lower()
                        if "already exists" not in err_str and "duplicate" not in err_str:
                            print(f"[WARN] SQL: {e}")

    # 统计菜品数
    result = await _execute("SELECT COUNT(*) as cnt FROM dishes", fetchone=True)
    count = result["cnt"] if result else 0
    print(f"[INFO] MySQL 数据库就绪，已有 {count} 个菜品")


# ============ 菜品操作 ============

async def get_all_dishes() -> List[Dict]:
    """获取所有菜品"""
    rows = await _execute("SELECT * FROM dishes ORDER BY id", fetchall=True)
    return [_parse_dish(r) for r in (rows or [])]


async def get_dish_by_id(dish_id: str) -> Optional[Dict]:
    """根据ID获取菜品"""
    row = await _execute("SELECT * FROM dishes WHERE id=%s", (dish_id,), fetchone=True)
    return _parse_dish(row)


async def get_dishes_by_source(source: str) -> List[Dict]:
    """根据来源获取菜品"""
    rows = await _execute("SELECT * FROM dishes WHERE source=%s", (source,), fetchall=True)
    return [_parse_dish(r) for r in (rows or [])]


async def get_yolo_dish_by_class_id(class_id: int) -> Optional[Dict]:
    """根据YOLO类别ID获取菜品"""
    row = await _execute(
        "SELECT * FROM dishes WHERE yolo_class_id=%s LIMIT 1",
        (class_id,), fetchone=True
    )
    return _parse_dish(row)


async def create_dish(dish_data: Dict) -> Dict:
    """创建菜品"""
    dish_id = generate_id("dish_")
    allergens = json.dumps(dish_data.get("allergens", []), ensure_ascii=False)
    nutrition = json.dumps(dish_data.get("nutrition", {}), ensure_ascii=False)

    await _execute(
        """INSERT INTO dishes (id, name, name_en, price, category, source,
           yolo_class_id, description, allergens, nutrition, stock, is_available)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (dish_id, dish_data.get("name", ""), dish_data.get("name_en", ""),
         dish_data.get("price", 0), dish_data.get("category", "other"),
         dish_data.get("source", "manual"), dish_data.get("yolo_class_id"),
         dish_data.get("description", ""), allergens, nutrition,
         dish_data.get("stock", 100), 1)
    )
    return await get_dish_by_id(dish_id)


async def update_dish(dish_id: str, update_data: Dict) -> Optional[Dict]:
    """更新菜品"""
    existing = await get_dish_by_id(dish_id)
    if not existing:
        return None

    sets = []
    vals = []
    for key, value in update_data.items():
        if value is not None and key not in ("id", "created_at"):
            if key in ("allergens", "nutrition"):
                value = json.dumps(value, ensure_ascii=False)
            sets.append(f"`{key}`=%s")
            vals.append(value)

    if sets:
        vals.append(dish_id)
        await _execute(f"UPDATE dishes SET {','.join(sets)} WHERE id=%s", tuple(vals))

    return await get_dish_by_id(dish_id)


async def delete_dish(dish_id: str) -> bool:
    """删除菜品"""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM dishes WHERE id=%s", (dish_id,))
            return cur.rowcount > 0


# ============ 订单操作 ============

async def create_order(order_data: Dict) -> Dict:
    """创建订单"""
    order_id = generate_id("order_")
    items_json = json.dumps(order_data.get("items", []), ensure_ascii=False)

    await _execute(
        """INSERT INTO orders (id, total_amount, original_amount, discount_amount,
           payment_method, status, items) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (order_id,
         order_data.get("total_amount", 0),
         order_data.get("original_amount", 0),
         order_data.get("discount_amount", 0),
         order_data.get("payment_method"),
         order_data.get("status", "completed"),
         items_json)
    )
    return await get_order_by_id(order_id)


async def get_orders(limit: int = 50) -> List[Dict]:
    """获取订单列表"""
    rows = await _execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT %s",
        (limit,), fetchall=True
    )
    return [_parse_order(r) for r in (rows or [])]


async def get_order_by_id(order_id: str) -> Optional[Dict]:
    """根据ID获取订单"""
    row = await _execute("SELECT * FROM orders WHERE id=%s", (order_id,), fetchone=True)
    return _parse_order(row)


# ============ 促销操作 ============

async def get_all_promotions() -> List[Dict]:
    """获取所有促销"""
    rows = await _execute("SELECT * FROM promotions ORDER BY created_at DESC", fetchall=True)
    return [_parse_promo(r) for r in (rows or [])]


async def get_active_promotions() -> List[Dict]:
    """获取有效促销"""
    rows = await _execute(
        """SELECT * FROM promotions
           WHERE is_active=1
           AND (start_time IS NULL OR start_time <= NOW())
           AND (end_time IS NULL OR end_time >= NOW())""",
        fetchall=True
    )
    return [_parse_promo(r) for r in (rows or [])]


async def create_promotion(promo_data: Dict) -> Dict:
    """创建促销"""
    promo_id = generate_id("promo_")
    applicable = json.dumps(promo_data.get("applicable_dishes", []), ensure_ascii=False)

    await _execute(
        """INSERT INTO promotions (id, name, type, discount_value, min_amount,
           applicable_dishes, start_time, end_time, is_active)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (promo_id, promo_data.get("name", ""),
         promo_data.get("type"), promo_data.get("discount_value", 0),
         promo_data.get("min_amount", 0), applicable,
         promo_data.get("start_time"), promo_data.get("end_time"),
         promo_data.get("is_active", True))
    )

    row = await _execute("SELECT * FROM promotions WHERE id=%s", (promo_id,), fetchone=True)
    return _parse_promo(row)


async def update_promotion(promo_id: str, update_data: Dict) -> Optional[Dict]:
    """更新促销"""
    existing = await _execute("SELECT id FROM promotions WHERE id=%s", (promo_id,), fetchone=True)
    if not existing:
        return None

    sets = []
    vals = []
    for key, value in update_data.items():
        if value is not None and key not in ("id", "created_at"):
            if key == "applicable_dishes":
                value = json.dumps(value, ensure_ascii=False)
            sets.append(f"`{key}`=%s")
            vals.append(value)

    if sets:
        vals.append(promo_id)
        await _execute(f"UPDATE promotions SET {','.join(sets)} WHERE id=%s", tuple(vals))

    row = await _execute("SELECT * FROM promotions WHERE id=%s", (promo_id,), fetchone=True)
    return _parse_promo(row)


async def delete_promotion(promo_id: str) -> bool:
    """删除促销"""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM promotions WHERE id=%s", (promo_id,))
            return cur.rowcount > 0


# ============ 识别日志操作 ============

async def create_recognition_log(log_data: Dict) -> Dict:
    """创建识别日志"""
    log_id = generate_id("log_")

    await _execute(
        """INSERT INTO recognition_logs (id, image_size, dishes_count,
           unrecognized_count, processing_time_ms, source, filename)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (log_id,
         log_data.get("image_size", 0),
         log_data.get("dishes_count", 0),
         log_data.get("unrecognized_count", 0),
         log_data.get("processing_time_ms", 0),
         log_data.get("source"),
         log_data.get("filename"))
    )

    row = await _execute("SELECT * FROM recognition_logs WHERE id=%s", (log_id,), fetchone=True)
    return _parse_json_fields(row, [])


async def get_recognition_logs(limit: int = 100) -> List[Dict]:
    """获取识别日志"""
    rows = await _execute(
        "SELECT * FROM recognition_logs ORDER BY created_at DESC LIMIT %s",
        (limit,), fetchall=True
    )
    return [_parse_json_fields(r, []) for r in (rows or [])]


# ============ 系统设置操作 ============

async def get_settings() -> Dict:
    """获取系统设置"""
    rows = await _execute("SELECT * FROM settings", fetchall=True)
    result = {}
    for row in (rows or []):
        key = row["setting_key"]
        val_str = row["setting_value"]
        # 解析值类型
        try:
            val = json.loads(val_str)
        except (json.JSONDecodeError, TypeError):
            val = val_str
        result[key] = val

    # 合并默认值
    for k, v in DEFAULT_SETTINGS.items():
        if k not in result:
            result[k] = v

    return result


async def update_settings(update_data: Dict) -> Dict:
    """更新系统设置"""
    for key, value in update_data.items():
        if value is not None and key in DEFAULT_SETTINGS:
            val_str = json.dumps(value)
            await _execute(
                """INSERT INTO settings (setting_key, setting_value)
                   VALUES (%s, %s)
                   ON DUPLICATE KEY UPDATE setting_value=%s""",
                (key, val_str, val_str)
            )
    return await get_settings()


# ============ 统计操作 ============

async def get_sales_stats(days: int = 7) -> List[Dict]:
    """获取销售统计"""
    stats = []
    today = datetime.now().date()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.isoformat()

        rows = await _execute(
            "SELECT * FROM orders WHERE DATE(created_at)=%s",
            (date_str,), fetchall=True
        )
        day_orders = [_parse_order(r) for r in (rows or [])]

        # 统计菜品销量
        from collections import defaultdict
        dish_sales = defaultdict(int)
        for order in day_orders:
            for item in (order.get("items") or []):
                dish_sales[item.get("name", "未知")] += item.get("quantity", 1)

        top_dishes = sorted(
            [{"name": k, "count": v} for k, v in dish_sales.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        total_revenue = sum(float(o.get("total_amount", 0) or 0) for o in day_orders)

        stats.append({
            "date": date_str,
            "total_orders": len(day_orders),
            "total_revenue": total_revenue,
            "top_dishes": top_dishes
        })

    return stats


async def get_dashboard_stats() -> Dict:
    """获取仪表盘统计"""
    today = datetime.now().date().isoformat()

    # 今日订单
    rows = await _execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as revenue FROM orders WHERE DATE(created_at)=%s",
        (today,), fetchone=True
    )

    # 菜品总数
    dish_count = await _execute("SELECT COUNT(*) as cnt FROM dishes", fetchone=True)

    # 低库存
    low_stock = await _execute(
        "SELECT COUNT(*) as cnt FROM dishes WHERE stock < 20",
        fetchone=True
    )

    return {
        "today_orders": rows["cnt"] if rows else 0,
        "today_revenue": float(rows["revenue"]) if rows else 0,
        "total_dishes": dish_count["cnt"] if dish_count else 0,
        "low_stock_count": low_stock["cnt"] if low_stock else 0
    }


# ============ 库存操作 ============

async def update_stock(dish_id: str, quantity: int) -> Optional[Dict]:
    """更新库存"""
    existing = await get_dish_by_id(dish_id)
    if not existing:
        return None

    new_stock = max(0, existing.get("stock", 0) + quantity)
    await _execute("UPDATE dishes SET stock=%s WHERE id=%s", (new_stock, dish_id))
    return await get_dish_by_id(dish_id)


async def get_low_stock_dishes(threshold: int = 20) -> List[Dict]:
    """获取低库存菜品"""
    rows = await _execute(
        "SELECT * FROM dishes WHERE stock < %s",
        (threshold,), fetchall=True
    )
    return [_parse_dish(r) for r in (rows or [])]
