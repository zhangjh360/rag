"""
添加 document_write 权限到角色
用于索引管理功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.models.database import Role
from app.config import settings
import json

def add_document_write_permission():
    """添加 document_write 权限到所有角色"""
    # 创建数据库引擎
    engine = create_engine(settings.DB_URL)

    # 创建会话
    db = Session(engine)

    try:
        # 获取所有角色
        roles = db.query(Role).all()

        updated_count = 0
        for role in roles:
            # 解析现有权限
            try:
                permissions = json.loads(role.permissions) if role.permissions else []
            except:
                permissions = []

            # 检查是否已有 document_write 权限
            if 'document_write' not in permissions:
                # 根据角色类型添加权限
                if role.name == 'admin':
                    # 管理员: 添加 document_write
                    permissions.append('document_write')
                    role.permissions = json.dumps(permissions)
                    updated_count += 1
                    print(f"✅ 已为角色 '{role.description}' (admin) 添加 document_write 权限")

                elif role.name == 'user':
                    # 普通用户: 添加 document_write
                    permissions.append('document_write')
                    role.permissions = json.dumps(permissions)
                    updated_count += 1
                    print(f"✅ 已为角色 '{role.description}' (user) 添加 document_write 权限")

                elif role.name == 'readonly':
                    # 只读用户: 不添加 document_write 权限
                    print(f"⏭️  跳过角色 '{role.description}' (readonly) - 只读用户不需要写权限")

                else:
                    # 其他自定义角色: 根据是否有 document_upload 权限决定
                    if 'document_upload' in permissions or 'document_delete' in permissions:
                        permissions.append('document_write')
                        role.permissions = json.dumps(permissions)
                        updated_count += 1
                        print(f"✅ 已为角色 '{role.description}' ({role.name}) 添加 document_write 权限")
                    else:
                        print(f"⏭️  跳过角色 '{role.description}' ({role.name}) - 没有文档修改权限")
            else:
                print(f"ℹ️  角色 '{role.description}' ({role.name}) 已有 document_write 权限")

        # 提交更改
        if updated_count > 0:
            db.commit()
            print(f"\n✅ 成功更新 {updated_count} 个角色的权限")
        else:
            print("\nℹ️  无需更新,所有角色已配置正确")

        # 显示最终权限配置
        print("\n" + "="*60)
        print("当前角色权限配置:")
        print("="*60)

        roles = db.query(Role).all()
        for role in roles:
            permissions = json.loads(role.permissions) if role.permissions else []
            has_write = 'document_write' in permissions
            status = "✅" if has_write else "❌"

            print(f"\n{status} {role.description} ({role.name}):")
            print(f"   权限列表: {', '.join(permissions)}")
            print(f"   document_write: {'是' if has_write else '否'}")

        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("开始添加 document_write 权限...")
    print("="*60)
    add_document_write_permission()
    print("\n完成!")
