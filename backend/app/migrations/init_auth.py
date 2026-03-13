"""
认证系统初始化脚本
创建角色和初始管理员用户
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.models.database import Base, Role, User
from app.services.auth import auth_service
from app.config import settings

def init_auth_system():
    """初始化认证系统"""
    # 创建数据库引擎
    engine = create_engine(settings.DB_URL)

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    db = Session(engine)

    try:
        # 检查是否已有角色数据
        existing_roles = db.query(Role).count()
        if existing_roles == 0:
            # 创建默认角色
            roles_data = [
                {
                    "id": 1,
                    "name": "admin",
                    "description": "管理员",
                    "permissions": '["document_upload", "document_delete", "document_read", "query_ask", "query_history", "system_settings", "user_management", "role_management"]'
                },
                {
                    "id": 2,
                    "name": "user",
                    "description": "普通用户",
                    "permissions": '["document_upload", "document_delete", "document_read", "query_ask", "query_history"]'
                },
                {
                    "id": 3,
                    "name": "readonly",
                    "description": "只读用户",
                    "permissions": '["document_read", "query_ask", "query_history"]'
                }
            ]

            for role_data in roles_data:
                role = Role(
                    id=role_data["id"],
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=role_data["permissions"]
                )
                db.add(role)

            print("✅ 默认角色创建成功")

        # 检查是否已有管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 创建默认管理员用户
            admin_password = "admin123"  # 默认密码
            admin_hash = auth_service.get_password_hash(admin_password)

            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=admin_hash,
                role_id=1,  # 管理员角色
                is_active="Y"
            )
            db.add(admin_user)

            print("✅ 默认管理员用户创建成功")
            print(f"   用户名: admin")
            print(f"   密码: {admin_password}")
            print("   请登录后立即修改默认密码！")

        # 提交更改
        db.commit()
        print("✅ 认证系统初始化完成")

    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_auth_system()