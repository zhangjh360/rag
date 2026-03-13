"""
文档模型类
存储文档内容和嵌入向量信息
"""
from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class Document(Base):
    """
    文档模型类
    存储文档内容和嵌入向量信息
    """
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    content = Column(Text, comment="文档内容")
    embedding = Column(Vector(384), comment="文档嵌入向量")  # 使用pgvector扩展的Vector类型
    doc_metadata = Column(String, comment="文档元数据")  # 重命名避免与SQLAlchemy的metadata冲突
    filename = Column(String, comment="文件名")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

    # 多领域支持字段
    namespace = Column(String(100), nullable=False, default='default', index=True, comment="领域命名空间")
    domain_tags = Column(JSONB, default=dict, nullable=False, comment="领域标签(JSON)")
    domain_confidence = Column(Float, default=0.0, nullable=False, comment="领域分类置信度")

class DocumentChunk(Base):
    """
    文档块模型类
    用于存储文档的分块内容
    """
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, comment="文档ID")
    content = Column(Text, comment="文档块内容")
    chunk_index = Column(Integer, comment="块索引")
    embedding = Column(Vector(384), comment="文档块嵌入向量")  # 使用pgvector扩展的Vector类型
    chunk_metadata = Column(String, comment="元数据信息")  # 重命名避免与SQLAlchemy保留字冲突
    filename = Column(String, comment="文件名")  # 添加filename字段
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

    # 多领域支持字段
    namespace = Column(String(100), nullable=False, default='default', index=True, comment="领域命名空间")
    domain_tags = Column(JSONB, default=dict, nullable=False, comment="领域标签(JSON)")
