"""
认证中间件
提供JWT令牌验证和权限检查功能
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..models.database import User, Role
from ..services.auth import auth_service
from ..database.connection import get_db

# HTTP Bearer认证
security = HTTPBearer()

class AuthMiddleware:
    """认证中间件类"""

    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """获取当前用户"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # 验证JWT令牌
            payload = auth_service.verify_token(credentials.credentials, "access")
            if payload is None:
                raise credentials_exception

            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception

        except Exception:
            raise credentials_exception

        # 从数据库获取用户信息
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception

        if user.is_active != 'Y':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        return user

    @staticmethod
    def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """获取当前激活用户"""
        if current_user.is_active != 'Y':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user

    @staticmethod
    def get_current_admin_user(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """获取当前管理员用户"""
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if not role or role.name != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return current_user

    @staticmethod
    def check_permission(permission: str):
        """检查权限装饰器工厂"""
        def permission_checker(
            current_user: User = Depends(AuthMiddleware.get_current_active_user),
            db: Session = Depends(get_db)
        ) -> User:
            if not auth_service.has_permission(db, current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            return current_user
        return permission_checker

    @staticmethod
    def check_permissions(permissions: List[str], require_all: bool = True):
        """检查多个权限装饰器工厂"""
        def permissions_checker(
            current_user: User = Depends(AuthMiddleware.get_current_active_user),
            db: Session = Depends(get_db)
        ) -> User:
            user_permissions = auth_service.get_user_permissions(db, current_user)

            if require_all:
                # 需要所有权限
                if not all(perm in user_permissions for perm in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"All permissions required: {', '.join(permissions)}"
                    )
            else:
                # 只需要其中一个权限
                if not any(perm in user_permissions for perm in permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"One of these permissions required: {', '.join(permissions)}"
                    )

            return current_user
        return permissions_checker

    @staticmethod
    def check_role(role_name: str):
        """检查角色装饰器工厂"""
        def role_checker(
            current_user: User = Depends(AuthMiddleware.get_current_active_user),
            db: Session = Depends(get_db)
        ) -> User:
            role = db.query(Role).filter(Role.id == current_user.role_id).first()
            if not role or role.name != role_name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role_name}' required"
                )
            return current_user
        return role_checker

# 权限检查装饰器
require_document_upload = AuthMiddleware.check_permission("document_upload")
require_document_delete = AuthMiddleware.check_permission("document_delete")
require_document_read = AuthMiddleware.check_permission("document_read")
require_query_ask = AuthMiddleware.check_permission("query_ask")
require_query_history = AuthMiddleware.check_permission("query_history")
require_system_settings = AuthMiddleware.check_permission("system_settings")
require_user_management = AuthMiddleware.check_permission("user_management")

# 导出常用的认证函数
get_current_user = AuthMiddleware.get_current_user
get_current_active_user = AuthMiddleware.get_current_active_user
get_current_admin_user = AuthMiddleware.get_current_admin_user
require_role_management = AuthMiddleware.check_permission("role_management")

# 角色检查装饰器
require_admin = AuthMiddleware.check_role("admin")
require_user = AuthMiddleware.check_role("user")
require_readonly = AuthMiddleware.check_role("readonly")

# 依赖注入函数
get_current_user = AuthMiddleware.get_current_user
get_current_active_user = AuthMiddleware.get_current_active_user
get_current_admin_user = AuthMiddleware.get_current_admin_user

# WebSocket认证支持
async def get_current_user_websocket(token: str, db: Session) -> User:
    """WebSocket认证 - 获取当前用户"""
    credentials_exception = Exception("Could not validate credentials")

    try:
        # 验证JWT令牌
        payload = auth_service.verify_token(token, "access")
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    # 从数据库获取用户信息
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if user.is_active != 'Y':
        raise Exception("User account is disabled")

    return user