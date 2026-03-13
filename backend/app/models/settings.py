from sqlalchemy import Column, String, Text, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Settings(Base):
    """
    系统设置模型
    存储LLM配置、RAG配置和系统配置
    """
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_type = Column(String(50), nullable=False, comment="设置类型: llm, rag, system")
    setting_key = Column(String(100), nullable=False, comment="设置键名")
    setting_value = Column(Text, comment="设置值(JSON格式)")
    description = Column(String(255), comment="设置描述")
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<Settings(type={self.setting_type}, key={self.setting_key})>"

    @classmethod
    def get_setting_key(cls, setting_type: str, setting_key: str) -> str:
        """生成设置的唯一键名"""
        return f"{setting_type}.{setting_key}"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.setting_type,
            'key': self.setting_key,
            'value': self.setting_value,
            'description': self.description
        }
