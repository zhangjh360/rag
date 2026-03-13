from pydantic import BaseModel
from typing import List, Optional
import json

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    sources: List[dict]

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content: str
    metadata: dict
    created_at: str
    namespace: Optional[str] = 'default'  # 添加领域字段
    domain_tags: Optional[dict] = {}  # 添加领域标签字段
    domain_confidence: Optional[float] = 0.0  # 添加领域置信度