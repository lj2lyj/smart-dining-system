# 智慧餐饮结算系统 - 后端服务

基于 FastAPI + YOLOv13 的智能菜品识别与结算系统后端。

## 📋 系统要求

- Python 3.9+
- pip 包管理器

## 🚀 本地运行指南

### 步骤 1：进入项目目录

```powershell
cd C:\Users\ASUS\Desktop\1111\smart-dining-backend
```

### 步骤 2：创建虚拟环境（推荐）

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# 如果提示脚本执行被禁止，先运行：
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 步骤 3：安装依赖

```powershell
pip install -r requirements.txt
```

### 步骤 4：启动后端服务

```powershell
# Windows PowerShell 需要先设置执行策略
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 启动开发服务器
uvicorn main:app --reload --port 8000
```

### 步骤 5：验证服务

浏览器访问：
- **API 首页**: http://localhost:8000
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc

---

## 🖥️ 前端运行指南

```powershell
# 进入前端目录
cd C:\Users\ASUS\Desktop\1111\smart-dining-frontend

# 安装依赖
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
npm install

# 启动开发服务器
npm run dev
```

浏览器访问：http://localhost:5173

---

## ⚡ 一键启动脚本

### 方法 1：使用批处理文件

在项目根目录（`C:\Users\ASUS\Desktop\1111`）创建 `start.bat`：

```bat
@echo off
echo 正在启动智慧餐饮结算系统...

:: 启动后端
start "Backend" cmd /k "cd smart-dining-backend && uvicorn main:app --reload --port 8000"

:: 等待2秒
timeout /t 2

:: 启动前端
start "Frontend" cmd /k "cd smart-dining-frontend && npm run dev"

echo 系统启动中...
echo 后端: http://localhost:8000
echo 前端: http://localhost:5173
```

### 方法 2：PowerShell 命令

```powershell
# 后端（新终端窗口）
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\ASUS\Desktop\1111\smart-dining-backend; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; uvicorn main:app --reload --port 8000"

# 前端（新终端窗口）
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\ASUS\Desktop\1111\smart-dining-frontend; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; npm run dev"
```

---

## 📁 项目结构

```
smart-dining-backend/
├── main.py              # FastAPI 应用入口
├── requirements.txt     # Python 依赖
├── database/
│   └── db.py           # 内存数据库
├── models/
│   └── schemas.py      # Pydantic 数据模型
├── routers/
│   ├── auth.py         # 认证接口
│   ├── dishes.py       # 菜品管理
│   ├── orders.py       # 订单管理
│   ├── recognition.py  # 图像识别
│   ├── stats.py        # 销售统计
│   ├── inventory.py    # 库存管理
│   ├── promotions.py   # 促销管理
│   ├── settings.py     # 系统设置
│   └── payment.py      # 支付接口
└── services/
    ├── yolo_service.py    # YOLO 识别服务
    └── payment_service.py # 支付服务
```

---

## 🔧 常见问题

### 1. PowerShell 脚本执行被禁止

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. 端口被占用

```powershell
# 查看占用端口的进程
netstat -ano | findstr :8000

# 结束进程 (替换 PID)
taskkill /PID <PID> /F
```

### 3. 模块未找到 (ModuleNotFoundError)

```powershell
pip install <模块名>
# 或重新安装所有依赖
pip install -r requirements.txt
```

---

## 🌐 API 接口概览

| 模块 | 路径前缀 | 描述 |
|------|----------|------|
| 认证 | `/api/auth` | 登录、注册、退出 |
| 菜品 | `/api/dishes` | 菜品 CRUD |
| 订单 | `/api/orders` | 订单管理 |
| 识别 | `/api/recognition` | 图像识别 |
| 统计 | `/api/stats` | 销售数据 |
| 库存 | `/api/inventory` | 库存管理 |
| 促销 | `/api/promotions` | 活动管理 |
| 设置 | `/api/settings` | 系统配置 |
| 支付 | `/api/payment` | 支付接口 |

---

## 📞 技术支持

如有问题，请检查：
1. Python 版本是否 >= 3.9
2. 依赖是否全部安装
3. 端口 8000 是否被占用
