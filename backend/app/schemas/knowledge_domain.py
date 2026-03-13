"""
知识领域相关的 Pydantic Schema
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class KnowledgeDomainBase(BaseModel):
    """知识领域基础 Schema"""
    namespace: str = Field(..., min_length=1, max_length=100, description="领域命名空间")
    display_name: str = Field(..., min_length=1, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, description="领域描述")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    icon: Optional[str] = Field(None, max_length=50, description="图标标识")
    color: Optional[str] = Field(None, max_length=20, description="主题色")
    is_active: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级")
    parent_namespace: Optional[str] = Field(None, max_length=100, description="父领域")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="权限配置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")

    @validator('namespace')
    def validate_namespace(cls, v):
        """验证命名空间格式"""
        import re
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('命名空间只能包含小写字母、数字、下划线和连字符')
        return v

    @validator('color')
    def validate_color(cls, v):
        """验证颜色格式"""
        if v and not v.startswith('#'):
            raise ValueError('颜色必须以#开头的十六进制格式')
        return v


class KnowledgeDomainCreate(KnowledgeDomainBase):
    """创建知识领域的 Schema"""
    pass


class KnowledgeDomainUpdate(BaseModel):
    """更新知识领域的 Schema(所有字段可选)"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    parent_namespace: Optional[str] = Field(None, max_length=100)
    permissions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeDomainResponse(KnowledgeDomainBase):
    """知识领域响应 Schema"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 统计信息(可选,通过 Service 层添加)
    document_count: Optional[int] = Field(None, description="文档数量")
    chunk_count: Optional[int] = Field(None, description="分块数量")

    class Config:
        from_attributes = True  # Pydantic v2
        # orm_mode = True  # Pydantic v1


class KnowledgeDomainListResponse(BaseModel):
    """知识领域列表响应"""
    domains: List[KnowledgeDomainResponse]
    total: int = Field(..., description="总数")


class KnowledgeDomainStatsResponse(BaseModel):
    """知识领域统计信息"""
    namespace: str
    document_count: int = Field(0, description="文档数量")
    chunk_count: int = Field(0, description="分块数量")
    avg_confidence: float = Field(0.0, description="平均分类置信度")
    recent_uploads: int = Field(0, description="最近7天上传数")


# ==================== 领域路由规则 Schemas ====================

class DomainRoutingRuleBase(BaseModel):
    """领域路由规则基础 Schema"""
    rule_name: str = Field(..., min_length=1, max_length=200, description="规则名称")
    rule_type: str = Field(..., description="规则类型: keyword/regex/llm/hybrid")
    pattern: str = Field(..., description="匹配模式")
    target_namespace: str = Field(..., max_length=100, description="目标领域")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="置信度阈值")
    priority: int = Field(0, description="优先级")
    is_active: bool = Field(True, description="是否启用")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展配置")


class DomainRoutingRuleCreate(DomainRoutingRuleBase):
    """创建路由规则的 Schema"""
    pass


class DomainRoutingRuleUpdate(BaseModel):
    """更新路由规则的 Schema"""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=200)
    rule_type: Optional[str] = None
    pattern: Optional[str] = None
    target_namespace: Optional[str] = Field(None, max_length=100)
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    """路由规则响应 Schema"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 领域关系 Schemas ====================

class DomainRelationshipBase(BaseModel):
    """领域关系基础 Schema"""
    source_namespace: str = Field(..., max_length=100, description="源领域")
    related_namespace: str = Field(..., max_length=100, description="关联领域")
    relationship_type: str = Field(..., max_length=50, description="关系类型")
    weight: float = Field(0.5, ge=0.0, le=1.0, description="关系权重")
    is_active: bool = Field(True, description="是否启用")


class DomainRelationshipCreate(DomainRelationshipBase):
    """创建领域关系的 Schema"""
    pass


class DomainRelationshipResponse(DomainRelationshipBase):
    """领域关系响应 Schema"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 领域分类结果 Schemas ====================

class DomainClassificationResult(BaseModel):
    """领域分类结果"""
    namespace: str = Field(..., description="分类的领域")
    display_name: str = Field(..., description="领域显示名称")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    method: str = Field(..., description="分类方法: keyword/llm/hybrid")
    reasoning: str = Field("", description="分类推理过程")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="备选领域")
    fallback_to_cross_domain: bool = Field(False, description="是否建议跨领域检索")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
