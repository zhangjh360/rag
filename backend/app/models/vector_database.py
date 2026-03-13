from sqlalchemy import Column, Integer, String, Text, create_engine, ARRAY, Float
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class Document(Base):
    """
    文档模型类
    存储文档内容和嵌入向量信息
    支持向量搜索和全文搜索
    """
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, comment="文档内容")
    embedding = Column(ARRAY(Float), comment="文档嵌入向量")  # 使用ARRAY存储数值向量
    doc_metadata = Column(String, comment="文档元数据")  # 重命名避免与SQLAlchemy的metadata冲突
    filename = Column(String, comment="文件名")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

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

class VectorDocument(Base):
    """
    向量文档模型类
    专门用于向量搜索的文档存储
    """
    __tablename__ = 'vector_documents'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, comment="文档内容")
    embedding = Column(String, comment="嵌入向量JSON字符串")  # 存储向量作为JSON字符串
    doc_metadata = Column(String, comment="文档元数据")
    filename = Column(String, comment="文件名")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")
