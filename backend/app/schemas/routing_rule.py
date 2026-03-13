"""
领域路由规则 Schemas
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DomainRoutingRuleBase(BaseModel):
    """路由规则基础Schema"""
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型: keyword/regex/pattern")
    pattern: str = Field(..., description="匹配模式")
    target_namespace: str = Field(..., description="目标领域命名空间")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="置信度阈值")
    priority: int = Field(0, description="优先级,数值越大优先级越高")
    is_active: bool = Field(True, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class DomainRoutingRuleCreate(DomainRoutingRuleBase):
    """创建路由规则Schema"""
    pass


class DomainRoutingRuleUpdate(BaseModel):
    """更新路由规则Schema"""
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    pattern: Optional[str] = None
    target_namespace: Optional[str] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    """路由规则响应Schema"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def model_validate(cls, obj):
        """自定义验证,处理 metadata_ 到 metadata 的映射"""
        if hasattr(obj, 'metadata_'):
            # 创建一个字典来存储属性
            data = {}
            for field_name in cls.model_fields.keys():
                if field_name == 'metadata':
                    # 特殊处理 metadata 字段
                    data[field_name] = obj.metadata_ if hasattr(obj, 'metadata_') else {}
                else:
                    # 其他字段直接获取
                    if hasattr(obj, field_name):
                        data[field_name] = getattr(obj, field_name)
            return cls(**data)
        return super().model_validate(obj)


class DomainRoutingRuleListResponse(BaseModel):
    """路由规则列表响应"""
    rules: list[DomainRoutingRuleResponse]
    total: int


class RoutingRuleMatchRequest(BaseModel):
    """路由规则匹配请求"""
    query: str = Field(..., description="查询文本")
    min_confidence: float = Field(0.0, ge=0.0, le=1.0, description="最小置信度")


class RoutingRuleMatchResponse(BaseModel):
    """路由规则匹配响应"""
    matched: bool
    target_namespace: Optional[str] = None
    confidence: Optional[float] = None
    rule_name: Optional[str] = None
    message: str
