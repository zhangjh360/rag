from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 从 document.py 导入 Base, Document 和 DocumentChunk (统一使用更完善的定义)
from app.models.document import Base, Document, DocumentChunk

# 导出所有模型供其他模块使用
__all__ = ['Base', 'Document', 'DocumentChunk', 'Query', 'User', 'Role', 'UserDocument', 'UserQuery']

class Query(Base):
    """
    查询模型类
    存储用户查询和响应信息
    """
    __tablename__ = 'queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(String, comment="查询文本")
    response = Column(Text, comment="响应内容")
    sources = Column(String, comment="来源信息")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

class User(Base):
    """
    用户模型类
    存储用户基本信息和认证数据
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    role_id = Column(Integer, nullable=False, default=2, comment="角色ID")
    is_active = Column(String(1), default='Y', comment="是否激活 Y/N")
    last_login = Column(String, comment="最后登录时间")
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(String, comment="锁定到期时间")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")
    updated_at = Column(String, default=lambda: str(datetime.now()), comment="更新时间")

class Role(Base):
    """
    角色模型类
    定义用户角色和权限
    """
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, comment="角色名称")
    description = Column(String(200), comment="角色描述")
    permissions = Column(Text, comment="权限列表 JSON格式")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")
    updated_at = Column(String, default=lambda: str(datetime.now()), comment="更新时间")

class UserDocument(Base):
    """
    用户文档关联表
    实现用户与文档的关联关系，支持数据隔离
    """
    __tablename__ = 'user_documents'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, comment="用户ID")
    document_id = Column(Integer, nullable=False, comment="文档ID")
    permission_level = Column(String(20), default='read', comment="权限级别 read/write/delete")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

class UserQuery(Base):
    """
    用户查询历史表
    存储用户的查询历史记录
    """
    __tablename__ = 'user_queries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, comment="用户ID")
    query_text = Column(String, comment="查询文本")
    response = Column(Text, comment="响应内容")
    sources = Column(String, comment="来源信息")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")
