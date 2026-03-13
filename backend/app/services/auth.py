"""
用户认证服务
提供用户登录、注册、权限验证等功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import jwt
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import secrets
import json

from ..models.database import User, Role
from ..config.settings import DB_URL

class AuthService:
    """用户认证服务类"""

    def __init__(self):
        self.secret_key = "your-secret-key-change-in-production"  # 生产环境需要修改
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        # Bcrypt 限制密码最多 72 字节
        password_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        # Bcrypt 限制密码最多 72 字节
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """创建JWT刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except Exception:
            return None

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = db.query(User).filter(
            or_(User.username == username, User.email == username)
        ).first()

        if not user:
            return None

        # 检查账户是否被锁定
        if user.locked_until:
            lock_time = datetime.fromisoformat(user.locked_until)
            if datetime.now() < lock_time:
                return None  # 账户被锁定
            else:
                # 解锁账户
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()

        # 检查账户是否激活
        if user.is_active != 'Y':
            return None

        # 验证密码
        if not self.verify_password(password, user.password_hash):
            # 增加失败次数
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # 锁定账户30分钟
                user.locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
            db.commit()
            return None

        # 重置失败次数
        user.failed_login_attempts = 0
        user.last_login = datetime.now().isoformat()
        db.commit()

        return user

    def get_user_permissions(self, db: Session, user: User) -> List[str]:
        """获取用户权限列表"""
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if not role:
            return []

        try:
            permissions = json.loads(role.permissions) if role.permissions else []
            return permissions
        except json.JSONDecodeError:
            return []

    def has_permission(self, db: Session, user: User, permission: str) -> bool:
        """检查用户是否有指定权限"""
        permissions = self.get_user_permissions(db, user)
        return permission in permissions

    def create_user(self, db: Session, username: str, email: str, password: str, role_id: int = 2) -> Optional[User]:
        """创建新用户"""
        # 检查用户名和邮箱是否已存在
        existing_user = db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()

        if existing_user:
            return None

        # 创建新用户
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role_id=role_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def change_password(self, db: Session, user: User, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not self.verify_password(old_password, user.password_hash):
            return False

        user.password_hash = self.get_password_hash(new_password)
        user.updated_at = datetime.now().isoformat()
        db.commit()

        return True

    def reset_password(self, db: Session, user: User, new_password: str) -> bool:
        """重置密码（管理员功能）"""
        user.password_hash = self.get_password_hash(new_password)
        user.updated_at = datetime.now().isoformat()
        user.failed_login_attempts = 0  # 重置失败次数
        user.locked_until = None  # 解锁账户
        db.commit()

        return True

# 全局认证服务实例
auth_service = AuthService()