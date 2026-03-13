-- ================================================================
-- 增量更新支持表结构
-- 创建日期: 2025-01-22
-- 用途: 支持文档的增量索引和版本控制
-- ================================================================

-- 1. 索引记录表：追踪每个文档的索引状态
CREATE TABLE IF NOT EXISTS document_index_records (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL COMMENT '文档内容MD5哈希值',
    chunk_count INTEGER DEFAULT 0 COMMENT '文档分块数量',
    vector_count INTEGER DEFAULT 0 COMMENT '向量数量',
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '索引时间',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    file_modified_at TIMESTAMP COMMENT '文件修改时间',
    index_version INTEGER DEFAULT 1 COMMENT '索引版本号',
    namespace VARCHAR(100) DEFAULT 'default' COMMENT '领域命名空间',

    -- 索引优化
    CONSTRAINT unique_doc_index UNIQUE(doc_id),
    INDEX idx_content_hash (content_hash),
    INDEX idx_indexed_at (indexed_at DESC),
    INDEX idx_namespace (namespace)
);

-- 2. 索引任务队列表：管理异步索引任务
CREATE TABLE IF NOT EXISTS index_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'Celery任务ID',
    doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL COMMENT '文档ID',
    task_type VARCHAR(20) NOT NULL COMMENT '任务类型: index, update, delete, rebuild',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending, processing, completed, failed',
    priority INTEGER DEFAULT 5 COMMENT '优先级(1-10, 10最高)',
    retry_count INTEGER DEFAULT 0 COMMENT '重试次数',
    max_retries INTEGER DEFAULT 3 COMMENT '最大重试次数',
    error_message TEXT COMMENT '错误信息',
    progress INTEGER DEFAULT 0 COMMENT '进度(0-100)',
    metadata JSONB DEFAULT '{}' COMMENT '任务元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at TIMESTAMP COMMENT '开始时间',
    completed_at TIMESTAMP COMMENT '完成时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引优化
    INDEX idx_status_priority (status, priority DESC),
    INDEX idx_task_type (task_type),
    INDEX idx_doc_id (doc_id),
    INDEX idx_created_at (created_at DESC),

    -- 状态约束
    CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    CONSTRAINT chk_task_type CHECK (task_type IN ('index', 'update', 'delete', 'rebuild', 'batch')),
    CONSTRAINT chk_priority CHECK (priority BETWEEN 1 AND 10)
);

-- 3. 索引变更历史表：记录所有索引变更用于审计和回滚
CREATE TABLE IF NOT EXISTS index_change_history (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE COMMENT '文档ID',
    change_type VARCHAR(20) NOT NULL COMMENT '变更类型: created, updated, deleted',
    old_content_hash VARCHAR(64) COMMENT '旧内容哈希',
    new_content_hash VARCHAR(64) COMMENT '新内容哈希',
    old_chunk_count INTEGER DEFAULT 0 COMMENT '旧分块数',
    new_chunk_count INTEGER DEFAULT 0 COMMENT '新分块数',
    user_id INTEGER COMMENT '操作用户ID',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
    change_details JSONB DEFAULT '{}' COMMENT '变更详情',
    snapshot_id VARCHAR(100) COMMENT '快照ID(用于回滚)',

    -- 索引优化
    INDEX idx_doc_id_changed_at (doc_id, changed_at DESC),
    INDEX idx_change_type (change_type),
    INDEX idx_changed_at (changed_at DESC),
    INDEX idx_snapshot_id (snapshot_id),

    CONSTRAINT chk_change_type CHECK (change_type IN ('created', 'updated', 'deleted', 'rollback'))
);

-- 4. 索引统计表：用于监控和性能分析
CREATE TABLE IF NOT EXISTS index_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL COMMENT '统计日期',
    namespace VARCHAR(100) DEFAULT 'default' COMMENT '领域',
    total_documents INTEGER DEFAULT 0 COMMENT '总文档数',
    indexed_documents INTEGER DEFAULT 0 COMMENT '已索引文档数',
    pending_tasks INTEGER DEFAULT 0 COMMENT '待处理任务数',
    failed_tasks INTEGER DEFAULT 0 COMMENT '失败任务数',
    avg_index_time_seconds FLOAT DEFAULT 0 COMMENT '平均索引时间(秒)',
    total_vectors INTEGER DEFAULT 0 COMMENT '总向量数',
    storage_size_mb FLOAT DEFAULT 0 COMMENT '存储大小(MB)',
    api_calls INTEGER DEFAULT 0 COMMENT 'API调用次数',
    api_cost_usd FLOAT DEFAULT 0 COMMENT 'API成本(美元)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 唯一性约束
    CONSTRAINT unique_stat_date_namespace UNIQUE(stat_date, namespace),
    INDEX idx_stat_date (stat_date DESC),
    INDEX idx_namespace_stat (namespace, stat_date DESC)
);

-- 5. 为现有documents表添加索引追踪字段
-- 检查列是否存在再添加，避免重复运行报错
DO $$
BEGIN
    -- 添加文件修改时间字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='file_modified_at') THEN
        ALTER TABLE documents ADD COLUMN file_modified_at TIMESTAMP COMMENT '文件修改时间';
    END IF;

    -- 添加文件大小字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='file_size') THEN
        ALTER TABLE documents ADD COLUMN file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)';
    END IF;

    -- 添加内容哈希字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='content_hash') THEN
        ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64) COMMENT '内容MD5哈希';
    END IF;

    -- 添加最后索引时间字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='last_indexed_at') THEN
        ALTER TABLE documents ADD COLUMN last_indexed_at TIMESTAMP COMMENT '最后索引时间';
    END IF;

    -- 添加索引状态字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='documents' AND column_name='index_status') THEN
        ALTER TABLE documents ADD COLUMN index_status VARCHAR(20) DEFAULT 'pending'
            COMMENT '索引状态: pending, indexed, failed, outdated';
    END IF;
END $$;

-- 6. 创建索引
CREATE INDEX IF NOT EXISTS idx_doc_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_doc_last_indexed ON documents(last_indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_doc_index_status ON documents(index_status);
CREATE INDEX IF NOT EXISTS idx_doc_file_modified ON documents(file_modified_at DESC);

-- 7. 创建更新时间自动触发器
CREATE OR REPLACE FUNCTION update_index_task_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_index_task_time ON index_tasks;
CREATE TRIGGER trigger_update_index_task_time
    BEFORE UPDATE ON index_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_index_task_updated_at();

-- 8. 初始化统计数据
INSERT INTO index_statistics (stat_date, namespace)
SELECT CURRENT_DATE, COALESCE(namespace, 'default') as namespace
FROM documents
WHERE namespace IS NOT NULL
GROUP BY namespace
ON CONFLICT (stat_date, namespace) DO NOTHING;

-- 9. 创建有用的视图
CREATE OR REPLACE VIEW v_index_status_summary AS
SELECT
    d.namespace,
    COUNT(*) as total_docs,
    COUNT(CASE WHEN d.index_status = 'indexed' THEN 1 END) as indexed_docs,
    COUNT(CASE WHEN d.index_status = 'pending' THEN 1 END) as pending_docs,
    COUNT(CASE WHEN d.index_status = 'failed' THEN 1 END) as failed_docs,
    COUNT(CASE WHEN d.index_status = 'outdated' THEN 1 END) as outdated_docs,
    MAX(d.last_indexed_at) as last_index_time,
    COUNT(DISTINCT ir.id) as has_index_record
FROM documents d
LEFT JOIN document_index_records ir ON d.id = ir.doc_id
GROUP BY d.namespace;

CREATE OR REPLACE VIEW v_active_index_tasks AS
SELECT
    t.*,
    d.filename,
    d.namespace,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.created_at)) as age_seconds
FROM index_tasks t
LEFT JOIN documents d ON t.doc_id = d.id
WHERE t.status IN ('pending', 'processing')
ORDER BY t.priority DESC, t.created_at ASC;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '✓ 增量更新表结构创建完成！';
    RAISE NOTICE '  - document_index_records: 索引记录表';
    RAISE NOTICE '  - index_tasks: 任务队列表';
    RAISE NOTICE '  - index_change_history: 变更历史表';
    RAISE NOTICE '  - index_statistics: 统计表';
    RAISE NOTICE '  - v_index_status_summary: 状态摘要视图';
    RAISE NOTICE '  - v_active_index_tasks: 活跃任务视图';
END $$;
