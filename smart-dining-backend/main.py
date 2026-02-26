"""
智慧餐饮结算系统 - FastAPI 后端服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.db import init_db
from routers import recognition, dishes, auth, orders, stats, inventory, promotions, settings, payment

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("[OK] 数据库初始化完成")
    print("[OK] 智慧餐饮结算系统后端启动成功")
    yield
    # 关闭时清理资源
    print("[OK] 系统关闭")

app = FastAPI(
    title="智慧餐饮结算系统 API",
    description="基于 YOLOv13 的智能菜品识别与结算系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(recognition.router, prefix="/api/recognition", tags=["图像识别"])
app.include_router(dishes.router, prefix="/api/dishes", tags=["菜品管理"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(stats.router, prefix="/api/stats", tags=["销售统计"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["库存管理"])
app.include_router(promotions.router, prefix="/api/promotions", tags=["促销管理"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])
app.include_router(payment.router)  # 支付路由（已包含 /api/payment 前缀）

@app.get("/", tags=["健康检查"])
async def root():
    """API 健康检查"""
    return {
        "status": "running",
        "message": "智慧餐饮结算系统 API 运行中",
        "version": "1.0.0"
    }

@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    from services.yolo_service import MODEL_LOADED
    return {
        "status": "healthy",
        "model_loaded": MODEL_LOADED,
        "database": "connected"
    }
