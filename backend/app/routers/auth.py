"""
认证路由
提供用户登录、注册、密码管理等功能
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from ..models.database import User, Role
from ..services.auth import auth_service
from ..middleware.auth import get_current_user, get_current_active_user
from ..database.connection import get_db

router = APIRouter(prefix="/auth", tags=["认证"])

# Pydantic模型
class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str  # 可以是用户名或邮箱
    password: str
    remember_me: Optional[bool] = False

class UserRegister(BaseModel):
    """用户注册请求模型"""
    username: str
    email: EmailStr
    password: str
    confirm_password: str

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    email: str
    role: str
    permissions: list[str]
    is_active: bool
    last_login: Optional[str]

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str
    confirm_password: str

@router.post("/login", response_model=Dict[str, Any])
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 验证用户凭据
    user = auth_service.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户角色和权限
    role = db.query(Role).filter(Role.id == user.role_id).first()
    permissions = auth_service.get_user_permissions(db, user)

    # 创建访问令牌
    access_token_expires = timedelta(minutes=30)
    if user_credentials.remember_me:
        access_token_expires = timedelta(days=7)

    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    refresh_token = auth_service.create_refresh_token(data={"sub": user.username})

    # 更新最后登录时间
    user.last_login = datetime.now().isoformat()
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds(),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role.name if role else "user",
            "permissions": permissions,
            "is_active": user.is_active == 'Y'
        }
    }

@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 验证密码确认
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码确认不匹配"
        )

    # 验证密码强度
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位"
        )

    # 创建新用户
    user = auth_service.create_user(
        db,
        user_data.username,
        user_data.email,
        user_data.password,
        role_id=2  # 默认为普通用户角色
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )

    # 获取用户角色和权限
    role = db.query(Role).filter(Role.id == user.role_id).first()
    permissions = auth_service.get_user_permissions(db, user)

    # 自动登录
    access_token = auth_service.create_access_token(data={"sub": user.username})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.username})

    return {
        "message": "注册成功",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role.name if role else "user",
            "permissions": permissions,
            "is_active": user.is_active == 'Y'
        }
    }

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    payload = auth_service.verify_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()

    if not user or bool(user.is_active != 'Y'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )

    # 创建新的访问令牌
    access_token = auth_service.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800  # 30分钟
    }

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": "user",  # 需要从数据库获取
        "permissions": [],  # 需要从数据库获取
        "is_active": current_user.is_active == 'Y',
        "last_login": current_user.last_login
    }

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证新密码确认
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码确认不匹配"
        )

    # 修改密码
    success = auth_service.change_password(
        db, current_user, password_data.old_password, password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    return {"message": "密码修改成功"}

@router.post("/logout")
async def logout():
    """用户登出"""
    # 在实际应用中，可以将令牌加入黑名单
    return {"message": "登出成功"}

@router.get("/check-permission/{permission}")
async def check_permission(
    permission: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检查用户权限"""
    has_perm = auth_service.has_permission(db, current_user, permission)
    return {"has_permission": has_perm, "permission": permission}