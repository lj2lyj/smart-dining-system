"""
认证 API
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional

router = APIRouter()

# 安全配置
SECRET_KEY = "smart-dining-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 密码处理
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# 模拟用户数据（生产环境应使用数据库）
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin123"),  # 默认密码
        "role": "admin",
        "name": "管理员"
    }
}


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class TokenData(BaseModel):
    """Token 数据"""
    username: str
    role: str
    exp: datetime


def create_access_token(data: dict) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """获取当前用户"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username and username in USERS:
            return USERS[username]
    except JWTError:
        pass
    
    return None


async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """要求管理员权限"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        role = payload.get("role")
        
        if username in USERS and role == "admin":
            return USERS[username]
        
        raise HTTPException(status_code=403, detail="需要管理员权限")
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"令牌无效: {str(e)}")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    管理员登录
    
    默认账号: admin / admin123
    """
    user = USERS.get(request.username)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        return LoginResponse(
            success=False,
            message="用户名或密码错误"
        )
    
    token = create_access_token({
        "username": user["username"],
        "role": user["role"]
    })
    
    return LoginResponse(
        success=True,
        token=token,
        user={
            "username": user["username"],
            "name": user["name"],
            "role": user["role"]
        }
    )


@router.get("/me")
async def get_me(user: dict = Depends(require_admin)):
    """获取当前登录用户信息"""
    return {
        "username": user["username"],
        "name": user["name"],
        "role": user["role"]
    }


@router.post("/logout")
async def logout():
    """
    登出
    
    客户端应删除本地存储的 token
    """
    return {"success": True, "message": "已登出"}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    user: dict = Depends(require_admin)
):
    """修改密码"""
    if not verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 更新密码
    USERS[user["username"]]["password_hash"] = pwd_context.hash(new_password)
    
    return {"success": True, "message": "密码已修改"}
