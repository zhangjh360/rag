# 查询接口优化指南

## 问题分析

### 当前 `/query` 接口存在的问题

#### 1. **性能问题**
- **全量查询**：每次查询都要获取所有文档的嵌入向量
- **内存占用**：所有文档向量加载到内存中计算相似度
- **扩展性差**：文档数量增加时性能急剧下降

#### 2. **上下文截断问题**
```python
# 当前代码的问题
def format_context(self, documents: list) -> str:
    context_parts = []
    for doc in documents:
        context_parts.append(f"文档: {doc['filename']}\n内容: {doc['content'][:500]}...")  # 只取前500字符
    return "\n\n".join(context_parts)
```

**问题**：如果相关信息在文档的第500字符之后，就会被截断丢失。

#### 3. **上下文长度限制**
- 没有考虑LLM的上下文长度限制
- 可能导致生成的回答不完整

## 解决方案

### 1. 文档分块检索

#### 原理
将长文档分割成多个小块，为每个块生成嵌入向量，检索时找到最相关的块。

#### 优势
- **精确匹配**：找到最相关的文档片段
- **避免截断**：不会丢失重要信息
- **提高准确性**：更精确的语义匹配

#### 实现
```python
def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """将文档分块，避免截断重要信息"""
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句号或换行处分割
        if end < len(content):
            for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                if content[i] in ['。', '\n', '！', '？']:
                    end = i + 1
                    break
        
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 下一块的开始位置，考虑重叠
        start = max(start + 1, end - overlap)
    
    return chunks
```

### 2. 智能上下文格式化

#### 原理
根据查询内容智能选择最相关的文档片段，而不是简单截取前500字符。

#### 实现
```python
def _extract_relevant_content(self, content: str, query_text: str) -> str:
    """从文档中提取与查询相关的内容"""
    # 将查询文本分词
    query_words = re.findall(r'\w+', query_text.lower())
    
    # 将文档分句
    sentences = re.split(r'[。！？\n]', content)
    
    # 计算每个句子的相关性得分
    sentence_scores = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        sentence_lower = sentence.lower()
        score = 0
        
        # 计算关键词匹配得分
        for word in query_words:
            if word in sentence_lower:
                score += 1
        
        # 计算位置权重（前面的内容权重更高）
        position_weight = 1.0 - (len(sentence_scores) / len(sentences)) * 0.3
        score *= position_weight
        
        sentence_scores.append((sentence, score))
    
    # 按得分排序，选择最相关的句子
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    
    relevant_sentences = []
    current_length = 0
    
    for sentence, score in sentence_scores:
        if current_length + len(sentence) > self.chunk_size:
            break
        relevant_sentences.append(sentence)
        current_length += len(sentence)
    
    return "。".join(relevant_sentences) + "。"
```

### 3. 上下文长度管理

#### 原理
动态管理上下文长度，确保不超过LLM的限制。

#### 实现
```python
def smart_format_context(self, documents: List[Dict], query_text: str) -> str:
    """智能格式化上下文，避免截断重要信息"""
    context_parts = []
    current_length = 0
    
    for doc in documents:
        # 计算当前文档需要的长度
        doc_header = f"文档: {doc['filename']}\n"
        doc_footer = "\n\n"
        
        # 获取文档内容
        content = doc['content']
        
        # 如果内容太长，尝试智能截取
        if len(content) > self.chunk_size:
            relevant_content = self._extract_relevant_content(content, query_text)
            if relevant_content:
                content = relevant_content
            else:
                content = content[:self.chunk_size] + "..."
        
        # 检查是否会超出长度限制
        doc_content = doc_header + content + doc_footer
        if current_length + len(doc_content) > self.max_context_length:
            remaining_length = self.max_context_length - current_length - len(doc_header) - len(doc_footer)
            if remaining_length > 100:
                content = content[:remaining_length] + "..."
                doc_content = doc_header + content + doc_footer
            else:
                break
        
        context_parts.append(doc_content)
        current_length += len(doc_content)
    
    return "".join(context_parts)
```

## 新的API接口

### 1. 高级查询接口

```http
POST /api/advanced-query
```

**请求体**：
```json
{
    "query": "什么是人工智能？",
    "use_chunks": true,
    "max_context_length": 4000,
    "top_k": 10,
    "include_similarity": true
}
```

**响应**：
```json
{
    "response": "人工智能是...",
    "sources": [...],
    "context_length": 3500,
    "retrieval_method": "chunk_based",
    "processing_time": 1.234
}
```

### 2. 文档块查询接口

```http
POST /api/query-with-chunks
```

**请求体**：
```json
{
    "query": "什么是机器学习？"
}
```

### 3. 查询性能统计

```http
GET /api/query/performance
```

### 4. 上下文优化

```http
POST /api/query/optimize?max_length=4000
```

## 性能优化建议

### 1. 数据库优化

#### 添加向量索引
```sql
-- 使用 pgvector 扩展（如果使用 PostgreSQL）
CREATE EXTENSION IF NOT EXISTS vector;

-- 修改表结构
ALTER TABLE documents ALTER COLUMN embedding TYPE vector(384);

-- 创建向量索引
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

#### 分页查询
```python
def retrieve_documents_paginated(self, db: Session, query_text: str, page: int = 0, page_size: int = 100):
    """分页检索文档"""
    offset = page * page_size
    query = text("""
        SELECT id, content, filename, doc_metadata, created_at, embedding
        FROM documents
        WHERE embedding IS NOT NULL
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(query, {"limit": page_size, "offset": offset})
    return result.fetchall()
```

### 2. 缓存优化

#### 嵌入向量缓存
```python
class CachedEmbeddingService:
    def __init__(self, base_service, cache_size=1000):
        self.base_service = base_service
        self.cache = {}
        self.cache_size = cache_size
    
    async def create_embedding(self, text: str) -> List[float]:
        cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        embedding = await self.base_service.create_embedding(text)
        self._manage_cache(cache_key, embedding)
        return embedding
```

#### 查询结果缓存
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_retrieve_documents(query_hash: str, top_k: int):
    """缓存查询结果"""
    # 实现缓存逻辑
    pass
```

### 3. 异步优化

#### 并行处理
```python
async def parallel_embedding_creation(self, texts: List[str]) -> List[List[float]]:
    """并行创建嵌入向量"""
    tasks = [self.create_embedding(text) for text in texts]
    embeddings = await asyncio.gather(*tasks)
    return embeddings
```

#### 批量处理
```python
async def batch_retrieve_documents(self, queries: List[str]) -> List[List[Dict]]:
    """批量检索文档"""
    tasks = [self.retrieve_documents(db, query) for query in queries]
    results = await asyncio.gather(*tasks)
    return results
```

## 使用建议

### 1. 选择合适的检索方法

- **文档块检索**：适合长文档，需要精确匹配
- **文档检索**：适合短文档，需要整体理解

### 2. 调整参数

- **chunk_size**：根据文档类型调整（技术文档：1000，新闻：500）
- **overlap_size**：确保上下文连续性（chunk_size的20%）
- **max_context_length**：根据LLM限制调整（GPT-3.5：4000，GPT-4：8800）

### 3. 监控性能

- 使用 `/api/query/performance` 监控查询性能
- 定期检查日志中的慢查询
- 监控内存使用情况

## 总结

通过以上优化，新的查询系统具有以下优势：

1. **解决截断问题**：使用文档分块和智能提取
2. **提高性能**：支持向量索引和缓存
3. **增强准确性**：更精确的语义匹配
4. **灵活配置**：支持多种检索策略
5. **性能监控**：提供详细的性能统计

现在您的查询系统可以更好地处理长文档，避免信息截断，并提供更准确的检索结果！
