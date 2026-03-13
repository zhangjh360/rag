from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class LLMGroup(Base):
    """
    LLM模型分组
    用于管理模型的分类
    """
    __tablename__ = 'llm_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="分组标识")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="分组描述")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    # 关系
    models = relationship("LLMModel", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LLMGroup(name={self.name})>"

class LLMModel(Base):
    """
    LLM模型配置
    存储每个模型的具体配置信息
    """
    __tablename__ = 'llm_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="模型标识")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    provider = Column(String(50), nullable=False, comment="API提供商")
    model_name = Column(String(100), nullable=False, comment="实际模型名称")
    api_key = Column(Text, comment="API密钥（加密存储）")
    base_url = Column(String(255), comment="自定义API地址")
    group_id = Column(Integer, ForeignKey('llm_groups.id'), comment="所属分组")
    is_default = Column(Boolean, default=False, comment="是否默认模型")
    is_active = Column(Boolean, default=True, comment="是否启用")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大tokens")
    top_p = Column(Float, default=1.0, comment="Top P参数")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    # 关系
    group = relationship("LLMGroup", back_populates="models")
    scenarios = relationship("LLMScenario", back_populates="default_model")

    def __repr__(self):
        return f"<LLMModel(name={self.name})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'provider': self.provider,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'group_id': self.group_id,
            'group_name': self.group.display_name if self.group else None,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class LLMScenario(Base):
    """
    场景配置
    为不同使用场景配置不同的默认模型
    """
    __tablename__ = 'llm_scenarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="场景标识")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="场景描述")
    default_model_id = Column(Integer, ForeignKey('llm_models.id'), comment="默认模型")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    # 关系
    default_model = relationship("LLMModel", back_populates="scenarios")

    def __repr__(self):
        return f"<LLMScenario(name={self.name})>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'default_model_id': self.default_model_id,
            'default_model_name': self.default_model.display_name if self.default_model else None,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
