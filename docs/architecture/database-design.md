# 数据库架构设计说明

## 修复时间
**2025-11-09 00:10**

## 问题背景
用户在查看 `upload.py` 中的 `upload_document` 方法时，发现了一个重要的架构问题：
- Document 表什么时候写入？
- Document 和 DocumentChunk 的关联关系是什么？
- Document 是主表，DocumentChunk 是分片表吗？

## 原始问题分析

### ❌ 错误的原始实现

**问题1：Document 表从未被写入**
```python
# 原始代码中只有这段
document_chunk = DocumentChunk(...)
db.add(document_chunk)
db.commit()
# Document 表从未创建！
```

**问题2：DocumentChunk 没有关联到 Document**
```python
document_chunk = DocumentChunk(
    # document_id 从未设置，始终为 NULL
    content=chunk,
    ...
)
```

**问题3：没有主外键关系**
- 所有数据都存储在 DocumentChunk 中
- Document 表完全没用
- 无法建立文档和分块的关联关系

## ✅ 正确的架构设计

### 数据表结构

#### 1. Document (主表)
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,              -- 完整文档内容
    embedding FLOAT[],         -- 完整文档的嵌入向量（可选）
    doc_metadata TEXT,         -- 文档元数据 JSON
    filename VARCHAR,          -- 文件名
    created_at TIMESTAMP       -- 创建时间
);
```

**作用**：
- 存储整个文档的元信息
- 作为 DocumentChunk 的主表
- 便于文档管理和查询

#### 2. DocumentChunk (分片表)
```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),  -- 外键关联
    content TEXT,              -- 分块内容
    chunk_index INTEGER,       -- 块索引 (0, 1, 2, ...)
    embedding FLOAT[],         -- 该分块的嵌入向量
    chunk_metadata TEXT,       -- 分块元数据 JSON
    filename VARCHAR,          -- 文件名 (冗余，便于查询)
    created_at TIMESTAMP       -- 创建时间
);
```

**作用**：
- 存储文档的分块内容
- 每个分块都有嵌入向量
- 通过 document_id 关联到主文档

### 关联关系

```
Document (主表) 1: N DocumentChunk (分片表)

Document
├── id: 1
├── filename: "requirements.txt"
├── content: "完整文档内容..."
└── chunks:
    ├── DocumentChunk (chunk_index: 0)
    ├── DocumentChunk (chunk_index: 1)
    └── DocumentChunk (chunk_index: 2)
```

## 🔧 修复后的实现

### 正确的写入流程

**第一步：创建主文档**
```python
# 1. 创建 Document 记录
main_document = Document(
    content=text_content,  # 完整文档内容
    doc_metadata=json.dumps({
        "filename": file.filename,
        "size": len(file_content),
        "type": file.filename.split('.')[-1],
        "total_chunks": len(text_chunks),
        "total_size": len(text_content)
    }),
    filename=file.filename,
    created_at=str(datetime.now())
)

db.add(main_document)
db.commit()
db.refresh(main_document)  # 获取生成的 ID
```

**第二步：创建分块记录**
```python
# 2. 为每个分块创建 DocumentChunk 记录
for i, chunk in enumerate(text_chunks):
    embedding = await embedding_service.create_embedding(chunk)

    document_chunk = DocumentChunk(
        document_id=main_document.id,  # ✅ 关键：建立关联关系
        content=chunk,
        chunk_index=i,
        embedding=embedding,
        chunk_metadata=json.dumps({
            "chunk_index": i,
            "total_chunks": len(text_chunks),
            "chunk_size": len(chunk)
        }),
        filename=f"{file.filename}_chunk_{i+1}",
        created_at=str(datetime.now())
    )

    db.add(document_chunk)
    db.commit()
```

**第三步：返回结果**
```python
return {
    "message": "Document uploaded successfully",
    "document_id": main_document.id,        # 主文档 ID
    "document_chunk_ids": document_chunk_ids,  # 所有分块 ID
    "filename": file.filename,
    "chunks_created": len(document_chunk_ids),
    "total_chunks": len(text_chunks)
}
```

## 📊 RAG 检索流程

### 修改后的 RAG 查询逻辑

```python
# 1. 从 DocumentChunk 表检索相关分块
chunks = self.db.query(DocumentChunk).all()

# 2. 计算相似度
for chunk in chunks:
    if chunk.embedding:
        similarity = self._cosine_similarity(query_embedding, chunk.embedding)
        results.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,  # 可获取主文档 ID
            "content": chunk.content,
            "similarity": float(similarity),
            "metadata": chunk.chunk_metadata
        })

# 3. 可选：使用 document_id 聚合查询
# 获取同一文档的所有分块
chunks_by_doc = db.query(DocumentChunk)\
    .filter(DocumentChunk.document_id == some_doc_id)\
    .all()
```

## 🎯 架构优势

### 1. 数据规范化
- **Document 表**：存储文档的元信息和整体内容
- **DocumentChunk 表**：存储可检索的分块
- 避免数据冗余

### 2. 高效查询
- RAG 检索：查询 DocumentChunk 表（分块级）
- 文档管理：查询 Document 表（文档级）
- 统计信息：可分别统计

### 3. 灵活扩展
- 可以为 Document 添加更多元字段
- 可以为 DocumentChunk 添加更多检索维度
- 支持多级分块（块 → 段 → 节）

### 4. 关联查询
```python
# 关联查询：获取某文档的所有分块
chunks = db.query(DocumentChunk)\
    .filter(DocumentChunk.document_id == doc_id)\
    .order_by(DocumentChunk.chunk_index)\
    .all()

# 关联查询：获取分块所属的文档信息
chunk_with_doc = db.query(DocumentChunk, Document)\
    .join(Document, DocumentChunk.document_id == Document.id)\
    .filter(DocumentChunk.id == chunk_id)\
    .first()
```

## 📋 对比总结

| 方面 | 修复前 ❌ | 修复后 ✅ |
|------|----------|----------|
| **Document 表** | 从未写入 | ✅ 正常写入 |
| **关联关系** | 无关联 (document_id=NULL) | ✅ 正确关联 |
| **数据组织** | 所有数据在 DocumentChunk | ✅ 规范化设计 |
| **查询性能** | 混乱，效率低 | ✅ 高效，职责清晰 |
| **扩展性** | 差 | ✅ 好 |

## 🔮 进一步优化建议

1. **添加索引**
   ```sql
   CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
   CREATE INDEX idx_document_chunks_chunk_index ON document_chunks(document_id, chunk_index);
   ```

2. **全文检索**
   ```sql
   -- 为 DocumentChunk 添加全文检索
   ALTER TABLE document_chunks ADD COLUMN content_tsv tsvector;
   CREATE INDEX idx_document_chunks_tsv ON document_chunks USING gin(content_tsv);
   ```

3. **向量相似度索引**
   ```sql
   -- 使用 pgvector 扩展进行向量检索
   CREATE EXTENSION IF NOT EXISTS vector;
   ALTER TABLE document_chunks ADD COLUMN embedding vector(1536);
   CREATE INDEX idx_document_chunks_vector ON document_chunks USING ivfflat(embedding vector_cosine_ops);
   ```

## 总结

通过这次修复，我们建立了正确的 **主表-分片表** 架构：
- **Document** (主表) - 管理文档元信息
- **DocumentChunk** (分片表) - 存储可检索的分块
- 通过 **document_id** 建立正确的关联关系

这种设计符合数据库设计范式，便于维护和扩展。

---

**状态**: ✅ 已完成并验证
**影响范围**: 整个文档上传和检索系统
**风险等级**: 中 (需要重新设计数据流)
