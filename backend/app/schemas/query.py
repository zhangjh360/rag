"""
查询请求和响应的Schema定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class QueryRequestV2(BaseModel):
    """查询请求 v2 (支持多领域检索)"""
    query: str = Field(..., description="查询内容", min_length=1, max_length=1000)
    namespace: Optional[str] = Field(None, description="指定领域命名空间(可选)")
    retrieval_mode: Optional[str] = Field(
        'auto',
        description="检索模式: 'auto'(自动识别), 'single'(单领域), 'cross'(跨领域)"
    )
    retrieval_method: Optional[str] = Field(
        'hybrid',
        description="检索方法: 'vector'(向量), 'bm25'(关键词), 'hybrid'(混合)"
    )
    namespaces: Optional[List[str]] = Field(
        None,
        description="跨领域检索时指定的领域列表(None=所有活跃领域)"
    )
    top_k: int = Field(10, description="返回结果数量", ge=1, le=50)
    similarity_threshold: float = Field(
        0.0,
        description="相似度阈值(仅向量检索)",
        ge=0.0,
        le=1.0
    )
    alpha: float = Field(
        0.5,
        description="混合检索权重(0.0=纯BM25, 1.0=纯向量, 0.5=均衡)",
        ge=0.0,
        le=1.0
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="额外过滤条件"
    )
    session_id: Optional[str] = Field(None, description="会话ID")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "如何配置API密钥?",
                "retrieval_mode": "auto",
                "retrieval_method": "hybrid",
                "top_k": 10,
                "alpha": 0.5
            }
        }


class ChunkResult(BaseModel):
    """文档块检索结果"""
    chunk_id: int = Field(description="文档块ID")
    content: str = Field(description="文档块内容")
    score: float = Field(description="相似度/相关度分数")
    namespace: str = Field(description="所属领域")
    domain_display_name: str = Field(description="领域显示名称")
    domain_color: Optional[str] = Field(None, description="领域颜色")
    domain_icon: Optional[str] = Field(None, description="领域图标")
    document_id: int = Field(description="文档ID")
    document_title: str = Field(description="文档标题")
    chunk_index: Optional[int] = Field(None, description="块索引")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": 123,
                "content": "API密钥配置方法...",
                "score": 0.85,
                "namespace": "technical_docs",
                "domain_display_name": "技术文档",
                "domain_color": "#4A90E2",
                "domain_icon": "code",
                "document_id": 456,
                "document_title": "API使用指南.pdf",
                "chunk_index": 2,
                "metadata": {}
            }
        }


class DomainGroup(BaseModel):
    """跨领域检索的领域分组结果"""
    namespace: str = Field(description="领域命名空间")
    display_name: str = Field(description="领域显示名称")
    count: int = Field(description="该领域的结果数")
    results: List[ChunkResult] = Field(description="该领域的检索结果")


class RetrievalStats(BaseModel):
    """检索统计信息"""
    total_candidates: int = Field(description="候选结果总数")
    method: str = Field(description="检索方法")
    latency_ms: float = Field(description="检索延迟(毫秒)")
    vector_count: Optional[int] = Field(None, description="向量检索结果数")
    bm25_count: Optional[int] = Field(None, description="BM25检索结果数")


class QueryResponseV2(BaseModel):
    """查询响应 v2"""
    query_id: str = Field(description="查询ID")
    query: str = Field(description="查询内容")
    domain_classification: Optional[Dict[str, Any]] = Field(
        None,
        description="领域分类结果"
    )
    retrieval_mode: str = Field(description="实际使用的检索模式")
    retrieval_method: str = Field(description="实际使用的检索方法")
    results: List[ChunkResult] = Field(description="检索结果列表")
    cross_domain_results: Optional[List[DomainGroup]] = Field(
        None,
        description="跨领域检索的分组结果"
    )
    retrieval_stats: RetrievalStats = Field(description="检索统计信息")
    created_at: datetime = Field(default_factory=lambda: datetime.now(), description="创建时间")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "uuid-123",
                "query": "如何配置API密钥?",
                "domain_classification": {
                    "namespace": "technical_docs",
                    "display_name": "技术文档",
                    "confidence": 0.85,
                    "method": "hybrid"
                },
                "retrieval_mode": "single",
                "retrieval_method": "hybrid",
                "results": [],
                "retrieval_stats": {
                    "total_candidates": 10,
                    "method": "hybrid",
                    "latency_ms": 125.5
                }
            }
        }
