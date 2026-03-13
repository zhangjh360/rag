-- ========================================
-- Phase 3 检索性能优化 - 数据库索引
-- ========================================
-- 创建时间: 2025-11-17
-- 用途: 优化向量检索、BM25和跨领域查询性能
-- ========================================

-- 1. 向量检索优化索引
-- ========================================

-- 为 document_chunks 表的 embedding 字段创建 IVFFlat 索引
-- IVFFlat 是 pgvector 的近似最近邻索引,可以大幅提升向量检索速度
-- lists=100 表示聚类中心数量,适合中等规模数据(10w-100w条)
DROP INDEX IF EXISTS idx_chunks_embedding_ivfflat;
CREATE INDEX idx_chunks_embedding_ivfflat
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 为 namespace 字段创建 B-tree 索引,加速单领域过滤
DROP INDEX IF EXISTS idx_chunks_namespace;
CREATE INDEX idx_chunks_namespace
ON document_chunks(namespace);

-- 为 namespace + document_id 创建复合索引,加速文档内检索
DROP INDEX IF EXISTS idx_chunks_namespace_document;
CREATE INDEX idx_chunks_namespace_document
ON document_chunks(namespace, document_id);

-- 为 document_id 创建索引,加速文档关联查询
DROP INDEX IF EXISTS idx_chunks_document_id;
CREATE INDEX idx_chunks_document_id
ON document_chunks(document_id);


-- 2. 文档表优化索引
-- ========================================

-- 为 documents 表的 namespace 字段创建索引
DROP INDEX IF EXISTS idx_documents_namespace;
CREATE INDEX idx_documents_namespace
ON documents(namespace);

-- 为 namespace + upload_time 创建复合索引,加速按时间筛选
DROP INDEX IF EXISTS idx_documents_namespace_time;
CREATE INDEX idx_documents_namespace_time
ON documents(namespace, upload_time DESC);

-- 为 user_id 创建索引,加速用户文档查询
DROP INDEX IF EXISTS idx_documents_user_id;
CREATE INDEX idx_documents_user_id
ON documents(user_id);


-- 3. 知识领域表优化索引
-- ========================================

-- 为 is_active 字段创建部分索引(只索引活跃领域)
DROP INDEX IF EXISTS idx_domains_active;
CREATE INDEX idx_domains_active
ON knowledge_domains(namespace)
WHERE is_active = true;

-- 为 namespace 创建唯一索引(如果还没有)
DROP INDEX IF EXISTS idx_domains_namespace_unique;
CREATE UNIQUE INDEX idx_domains_namespace_unique
ON knowledge_domains(namespace);


-- 4. 全文搜索优化(BM25支持)
-- ========================================

-- 为 document_chunks 的 content 字段创建 GIN 全文索引
-- 用于加速关键词搜索(BM25的基础)
DROP INDEX IF EXISTS idx_chunks_content_gin;
CREATE INDEX idx_chunks_content_gin
ON document_chunks
USING gin(to_tsvector('simple', content));

-- 为 documents 的 filename 创建 GIN 索引,支持文件名搜索
DROP INDEX IF EXISTS idx_documents_filename_gin;
CREATE INDEX idx_documents_filename_gin
ON documents
USING gin(to_tsvector('simple', filename));


-- 5. 统计信息更新
-- ========================================

-- 更新表统计信息,帮助查询优化器选择更好的执行计划
ANALYZE document_chunks;
ANALYZE documents;
ANALYZE knowledge_domains;


-- 6. 查询性能监控视图
-- ========================================

-- 创建索引使用统计视图
CREATE OR REPLACE VIEW v_index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 创建表大小统计视图
CREATE OR REPLACE VIEW v_table_size_stats AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;


-- 7. 向量检索性能配置
-- ========================================

-- 设置 probes 参数,控制向量检索的精度/速度权衡
-- probes 越大越精确但越慢,建议值为 lists/10 到 lists/2
-- 这里设置为 20 (lists=100 时的推荐值)
SET ivfflat.probes = 20;

-- 在应用代码中也需要设置(每个连接都要设置)
COMMENT ON INDEX idx_chunks_embedding_ivfflat IS
'向量检索索引。在查询前执行: SET ivfflat.probes = 20;';


-- ========================================
-- 性能优化说明
-- ========================================

/*
1. 向量索引优化:
   - IVFFlat 索引可以将检索速度提升 10-100x
   - 适合中大规模数据(>10000条)
   - 精度略有损失(~95-99%)但速度大幅提升

2. namespace 索引:
   - 单领域查询必备
   - 支持快速过滤
   - 建议将常用领域数据预加载到缓存

3. 全文索引:
   - GIN 索引支持快速关键词搜索
   - 配合 ts_rank 使用可实现 BM25 类似效果
   - 支持多语言(中文需要额外配置)

4. 复合索引:
   - namespace + document_id 支持文档内检索
   - namespace + upload_time 支持按时间筛选
   - 减少回表查询

5. 统计信息:
   - 定期执行 ANALYZE 保持统计信息准确
   - 帮助查询优化器选择最佳执行计划

6. 监控视图:
   - v_index_usage_stats: 查看索引使用情况
   - v_table_size_stats: 查看表和索引大小
   - 定期检查未使用的索引并删除

使用方法:
---------
在 PostgreSQL 中执行:
    psql -U your_user -d your_database -f optimize_retrieval_indexes.sql

或在应用代码中执行:
    python backend/app/migrations/run_index_optimization.py

预期效果:
---------
- 向量检索: 100ms → 10-20ms (5-10x 提升)
- BM25检索: 50ms → 10-15ms (3-5x 提升)
- 跨域检索: 250ms → 80-120ms (2-3x 提升)
- 总体查询: 300ms → 100-150ms (2-3x 提升)

注意事项:
---------
1. 索引会占用额外存储空间(约为数据的 20-50%)
2. 索引会略微影响插入/更新性能
3. IVFFlat 索引需要定期 REINDEX(数据变化 >30% 时)
4. 根据实际数据量调整 lists 和 probes 参数
*/

-- ========================================
-- 索引维护命令
-- ========================================

-- 重建所有索引(数据变化较大时)
-- REINDEX TABLE document_chunks;
-- REINDEX TABLE documents;
-- REINDEX TABLE knowledge_domains;

-- 查看索引使用情况
-- SELECT * FROM v_index_usage_stats;

-- 查看表大小
-- SELECT * FROM v_table_size_stats;

-- 查看慢查询
-- SELECT query, calls, mean_exec_time, max_exec_time
-- FROM pg_stat_statements
-- ORDER BY mean_exec_time DESC
-- LIMIT 20;
