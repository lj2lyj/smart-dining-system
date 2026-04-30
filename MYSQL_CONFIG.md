# MySQL 配置指南（PHPStudy + Navicat）

## 一、启动 PHPStudy 中的 MySQL

1. 打开 **小皮面板（PHPStudy）**
2. 在首页找到 **MySQL**，点击 **启动**
3. 确认状态变为 ✅ **已启动**（默认端口 `3306`）

> 如果端口被占用，可以在 PHPStudy 中修改 MySQL 端口，同时修改项目中 `smart-dining-backend/database/db_config.py` 的 `port` 值。

---

## 二、查看 MySQL 密码

PHPStudy 默认 MySQL 账号：
- **用户名**：`root`
- **密码**：`root`

> 如果你修改过密码，请同步更新 `smart-dining-backend/database/db_config.py` 中的 `password` 字段。

---

## 三、Navicat 连接 MySQL

1. 打开 **Navicat**
2. 点击左上角 **连接** → **MySQL**
3. 填写：

| 字段 | 值 |
|------|----|
| 连接名 | `智慧餐饮系统` (随意) |
| 主机 | `127.0.0.1` |
| 端口 | `3306` |
| 用户名 | `root` |
| 密码 | `root` |

4. 点击 **测试连接** → 显示 "连接成功" → 点击 **确定**

---

## 四、创建数据库并初始化表

### 方式一：自动创建（推荐）

直接启动后端，程序会**自动创建数据库和所有表**：

```bash
cd C:\Users\ASUS\Desktop\1111\smart-dining-backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后会看到：
```
[INFO] MySQL 数据库就绪，已有 39 个菜品
[OK] 数据库初始化完成
```

然后在 Navicat 中**右键连接 → 刷新**，即可看到 `smart_dining` 数据库和所有表。

### 方式二：Navicat 手动执行 SQL

1. 在 Navicat 中双击打开连接
2. 点击菜单栏 **查询** → **新建查询**
3. 打开文件 `smart-dining-backend/database/schema.sql`，全选复制粘贴
4. 点击 **运行**（▶ 按钮）
5. 刷新左侧，数据库 `smart_dining` 和所有表即出现

---

## 五、数据表说明

| 表名 | 说明 | 字段数 |
|------|------|--------|
| `dishes` | 菜品表（含36种YOLO菜品 + 3种手动菜品） | 14 |
| `orders` | 订单表 | 8 |
| `promotions` | 促销表 | 10 |
| `recognition_logs` | 识别日志表 | 8 |
| `settings` | 系统设置表 | 3 |

### dishes 菜品表（核心表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VARCHAR(50) PK | 菜品ID |
| `name` | VARCHAR(100) | 中文名 |
| `name_en` | VARCHAR(100) | 英文名 |
| `price` | DECIMAL(10,2) | 价格 |
| `category` | VARCHAR(50) | 分类：meat/vegetable/staple/drink/other |
| `source` | VARCHAR(20) | 来源：yolo（模型识别）/manual（手动添加） |
| `yolo_class_id` | INT | YOLO 模型类别ID（0-35） |
| `description` | TEXT | 描述 |
| `allergens` | JSON | 过敏原列表，如 `["鸡蛋","小麦"]` |
| `nutrition` | JSON | 营养信息，如 `{"calories":90,...}` |
| `stock` | INT | 库存 |
| `is_available` | TINYINT(1) | 是否可用 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |

---

## 六、配置文件说明

数据库连接信息在 `smart-dining-backend/database/db_config.py`：

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "db": "smart_dining",
    "charset": "utf8mb4",
}
```

如需修改，直接编辑此文件，或设置环境变量：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `MYSQL_HOST` | MySQL 地址 | `127.0.0.1` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | 用户名 | `root` |
| `MYSQL_PASSWORD` | 密码 | `root` |
| `MYSQL_DATABASE` | 数据库名 | `smart_dining` |

---

## 七、常见问题

### Q1：启动报错 "无法连接 MySQL"
- 确认 PHPStudy 中 MySQL 已启动（状态为绿色）
- 确认端口未被占用：打开 CMD 运行 `netstat -ano | findstr 3306`
- 确认密码正确

### Q2：Navicat 中看不到数据库
- 右键连接名 → **刷新**
- 确认后端至少启动过一次（自动建库建表）

### Q3：数据会丢失吗？
- 不会。迁移到 MySQL 后数据持久化存储，重启后端不会丢失数据
- 只有在 Navicat 中手动删除数据或数据库才会丢失

### Q4：如何重置数据？
- 在 Navicat 中右键 `smart_dining` → **删除数据库**
- 重新启动后端即可自动重建
