# 嵌入向量字段类型修复指南

## 问题描述

上传文档时出现以下错误：
```
(psycopg2.errors.DatatypeMismatch) column "embedding" is of type tsvector but expression is of type numeric[]
```

这是因为数据库中的 `embedding` 字段被定义为 `TSVECTOR` 类型（用于全文搜索），但我们的嵌入向量是数值数组类型。

## 解决方案

### 1. 自动修复（推荐）

运行修复脚本：
```bash
cd /home/zhangjh/code/python/rag/backend
python fix_database.py
```

### 2. 手动修复

如果自动修复失败，可以手动执行以下SQL命令：

```sql
-- 1. 清空现有embedding数据
UPDATE documents SET embedding = NULL;

-- 2. 删除旧的embedding列
ALTER TABLE documents DROP COLUMN IF EXISTS embedding;

-- 3. 添加新的embedding列
ALTER TABLE documents ADD COLUMN embedding REAL[];

-- 4. 添加注释
COMMENT ON COLUMN documents.embedding IS '文档嵌入向量';
```

### 3. 验证修复

运行测试脚本验证修复是否成功：
```bash
cd /home/zhangjh/code/python/rag/backend
python test_embedding_fix.py
```

## 修复内容

### 1. 数据库模型更新

**修改前：**
```python
embedding = Column(TSVECTOR(), comment="文档嵌入向量")
```

**修改后：**
```python
embedding = Column(ARRAY(Float), comment="文档嵌入向量")
```

### 2. 检索服务更新

**修改前：** 使用全文搜索
```python
query = text("""
    SELECT id, content, filename, doc_metadata, created_at,
           ts_rank(embedding, plainto_tsquery('chinese', :query_text)) as similarity
    FROM documents
    WHERE embedding @@ plainto_tsquery('chinese', :query_text)
    ORDER BY similarity DESC
    LIMIT :limit
""")
```

**修改后：** 使用向量相似度搜索
```python
# 1. 为查询文本生成嵌入向量
query_embedding = await embedding_service.create_embedding(query_text)

# 2. 获取所有文档并计算相似度
similarities = []
for i, doc_embedding in enumerate(document_embeddings):
    similarity = embedding_service.cosine_similarity(query_embedding, doc_embedding)
    similarities.append((i, similarity))
```

## 技术细节

### 数据类型对比

| 类型 | 用途 | 存储方式 | 搜索方式 |
|------|------|----------|----------|
| TSVECTOR | 全文搜索 | 词向量 | 文本匹配 |
| REAL[] | 数值向量 | 浮点数组 | 向量相似度 |

### 性能考虑

1. **向量相似度计算**：在应用层计算，适合小到中等规模数据
2. **索引优化**：可以考虑使用 pgvector 扩展进行优化
3. **缓存策略**：嵌入向量服务已内置缓存机制

## 后续优化建议

### 1. 使用 pgvector 扩展

对于大规模数据，建议使用 pgvector 扩展：

```sql
-- 安装扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 修改表结构
ALTER TABLE documents ALTER COLUMN embedding TYPE vector(384);

-- 创建索引
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

### 2. 混合搜索

结合全文搜索和向量搜索：

```python
# 全文搜索 + 向量搜索
fulltext_results = fulltext_search(query)
vector_results = vector_search(query)
combined_results = merge_results(fulltext_results, vector_results)
```

## 故障排除

### 常见问题

1. **权限不足**
   ```bash
   # 确保数据库用户有ALTER TABLE权限
   GRANT ALTER ON TABLE documents TO your_user;
   ```

2. **数据丢失**
   ```bash
   # 修复前会清空embedding字段，这是正常的
   # 重新上传文档即可重新生成嵌入向量
   ```

3. **依赖问题**
   ```bash
   # 确保安装了必要的依赖
   pip install -r requirements.txt
   ```

### 回滚方案

如果需要回滚到原来的全文搜索：

```sql
-- 删除数值向量列
ALTER TABLE documents DROP COLUMN embedding;

-- 重新添加TSVECTOR列
ALTER TABLE documents ADD COLUMN embedding TSVECTOR;

-- 重新创建全文搜索索引
CREATE INDEX ON documents USING gin(embedding);
```

## 测试验证

修复完成后，可以通过以下方式验证：

1. **上传测试**：尝试上传一个PDF或TXT文件
2. **查询测试**：使用查询接口测试检索功能
3. **性能测试**：检查响应时间和准确性

## 联系支持

如果遇到问题，请检查：
1. 数据库连接是否正常
2. 依赖包是否正确安装
3. 环境变量是否正确配置

修复完成后，嵌入向量功能将正常工作，支持更准确的语义搜索。
