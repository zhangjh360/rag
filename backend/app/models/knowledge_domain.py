"""
知识领域模型类
用于管理多领域知识库的配置
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class KnowledgeDomain(Base):
    """
    知识领域配置表
    用于定义和管理不同的知识库领域
    """
    __tablename__ = 'knowledge_domains'

    id = Column(Integer, primary_key=True, autoincrement=True)
    namespace = Column(String(100), unique=True, nullable=False, index=True, comment="领域命名空间唯一标识")
    display_name = Column(String(200), nullable=False, comment="领域显示名称")
    description = Column(Text, comment="领域描述")
    keywords = Column(JSONB, default=list, comment="关键词列表(JSON数组)")
    icon = Column(String(50), comment="前端图标标识")
    color = Column(String(20), comment="UI主题色")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    priority = Column(Integer, default=0, nullable=False, comment="排序优先级")
    parent_namespace = Column(String(100), comment="父领域命名空间")
    permissions = Column(JSONB, default=dict, comment="权限配置(JSON对象)")
    metadata_ = Column('metadata', JSONB, default=dict, comment="扩展元数据")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'namespace': self.namespace,
            'display_name': self.display_name,
            'description': self.description,
            'keywords': self.keywords,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'priority': self.priority,
            'parent_namespace': self.parent_namespace,
            'permissions': self.permissions,
            'metadata': self.metadata_,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None,
        }


class DomainRoutingRule(Base):
    """
    领域路由规则表
    用于自动分类查询到对应的领域
    """
    __tablename__ = 'domain_routing_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    rule_type = Column(String(50), nullable=False, comment="规则类型: keyword/regex/llm/hybrid")
    pattern = Column(Text, nullable=False, comment="匹配模式")
    target_namespace = Column(String(100), nullable=False, comment="目标领域命名空间")
    confidence_threshold = Column(Float, default=0.7, comment="置信度阈值")
    priority = Column(Integer, default=0, comment="规则优先级")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    metadata_ = Column('metadata', JSONB, default=dict, comment="规则扩展配置")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment="创建时间")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'pattern': self.pattern,
            'target_namespace': self.target_namespace,
            'confidence_threshold': self.confidence_threshold,
            'priority': self.priority,
            'is_active': self.is_active,
            'metadata': self.metadata_,
            'created_at': str(self.created_at) if self.created_at else None,
        }


class DomainRelationship(Base):
    """
    领域关系表(可选)
    用于管理领域之间的关系
    """
    __tablename__ = 'domain_relationships'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_namespace = Column(String(100), nullable=False, comment="源领域")
    related_namespace = Column(String(100), nullable=False, comment="关联领域")
    relationship_type = Column(String(50), nullable=False, comment="关系类型: parent/sibling/related/fallback")
    weight = Column(Float, default=0.5, comment="关系权重")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, comment="创建时间")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'source_namespace': self.source_namespace,
            'related_namespace': self.related_namespace,
            'relationship_type': self.relationship_type,
            'weight': self.weight,
            'is_active': self.is_active,
            'created_at': str(self.created_at) if self.created_at else None,
        }
