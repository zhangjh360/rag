"""
用户管理API路由
管理员用于管理系统用户
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database.connection import get_db
from app.models.database import User, Role
from app.middleware.auth import require_user_management, get_current_admin_user
from app.services.auth import auth_service

router = APIRouter(prefix="/api/users", tags=["用户管理"])


# Pydantic 模型
class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str
    email: EmailStr
    password: str
    role_id: int = 2


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    username: str | None = None
    email: EmailStr | None = None
    role_id: int | None = None
    is_active: str | None = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    role_id: int
    role_name: str | None = None
    is_active: str
    last_login: str | None = None
    created_at: str | None = None
    failed_login_attempts: int = 0


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    total: int
    users: List[UserResponse]


@router.get("", response_model=UserListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role_id: int | None = None,
    is_active: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """
    获取用户列表
    - 支持分页
    - 支持按角色筛选
    - 支持按状态筛选
    - 支持搜索用户名或邮箱
    """
    query = db.query(User)

    # 角色筛选
    if role_id is not None:
        query = query.filter(User.role_id == role_id)

    # 状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # 搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )

    # 获取总数
    total = query.count()

    # 分页
    users = query.offset(skip).limit(limit).all()

    # 获取角色信息
    user_responses = []
    for user in users:
        role = db.query(Role).filter(Role.id == user.role_id).first()
        user_responses.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role_id=user.role_id,
            role_name=role.name if role else None,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            failed_login_attempts=user.failed_login_attempts
        ))

    return UserListResponse(total=total, users=user_responses)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """获取单个用户详情"""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    role = db.query(Role).filter(Role.id == user.role_id).first()

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role_id=user.role_id,
        role_name=role.name if role else None,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        failed_login_attempts=user.failed_login_attempts
    )


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """
    创建新用户
    - 需要管理员权限
    - 检查用户名和邮箱唯一性
    - 验证角色是否存在
    """
    # 检查角色是否存在
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色不存在"
        )

    # 检查用户名和邮箱是否已存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    # 创建用户
    new_user = auth_service.create_user(
        db,
        user_data.username,
        user_data.email,
        user_data.password,
        user_data.role_id
    )

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role_id=new_user.role_id,
        role_name=role.name,
        is_active=new_user.is_active,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        failed_login_attempts=new_user.failed_login_attempts
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """
    更新用户信息
    - 需要管理员权限
    - 不能修改自己的角色
    - 检查新用户名和邮箱的唯一性
    """
    # 获取要更新的用户
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 防止管理员修改自己的角色
    if user_id == current_user.id and user_data.role_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )

    # 更新用户名
    if user_data.username is not None:
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        user.username = user_data.username

    # 更新邮箱
    if user_data.email is not None:
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        user.email = user_data.email

    # 更新角色
    if user_data.role_id is not None:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色不存在"
            )
        user.role_id = user_data.role_id

    # 更新状态
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)

    role = db.query(Role).filter(Role.id == user.role_id).first()

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role_id=user.role_id,
        role_name=role.name if role else None,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        failed_login_attempts=user.failed_login_attempts
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """
    删除用户
    - 需要管理员权限
    - 不能删除自己
    - 不能删除最后一个管理员
    """
    # 获取要删除的用户
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    # 检查是否是最后一个管理员
    if user.role_id == 1:  # 管理员角色
        admin_count = db.query(User).filter(User.role_id == 1).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个管理员"
            )

    db.delete(user)
    db.commit()

    return {"message": "用户删除成功", "user_id": user_id}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user_management)
):
    """
    重置用户密码
    - 需要管理员权限
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新密码
    user.password_hash = auth_service.get_password_hash(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    db.commit()

    return {"message": "密码重置成功"}
