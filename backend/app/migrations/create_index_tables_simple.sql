-- 简化版索引管理表
-- 使用PostgreSQL标准语法

-- 1. 索引记录表
CREATE TABLE IF NOT EXISTS document_index_records (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    content_hash VARCHAR(64) NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    vector_count INTEGER DEFAULT 0,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size BIGINT DEFAULT 0,
    file_modified_at TIMESTAMP,
    index_version INTEGER DEFAULT 1,
    namespace VARCHAR(100) DEFAULT 'default'
);

CREATE INDEX IF NOT EXISTS idx_dir_content_hash ON document_index_records(content_hash);
CREATE INDEX IF NOT EXISTS idx_dir_indexed_at ON document_index_records(indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_dir_namespace ON document_index_records(namespace);

-- 2. 任务队列表
CREATE TABLE IF NOT EXISTS index_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    doc_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    task_type VARCHAR(20) NOT NULL CHECK (task_type IN ('index', 'update', 'delete', 'rebuild', 'batch')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    progress INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_it_status_priority ON index_tasks(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_it_task_type ON index_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_it_doc_id ON index_tasks(doc_id);
CREATE INDEX IF NOT EXISTS idx_it_created_at ON index_tasks(created_at DESC);

-- 3. 变更历史表
CREATE TABLE IF NOT EXISTS index_change_history (
    id SERIAL PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('created', 'updated', 'deleted', 'rollback')),
    old_content_hash VARCHAR(64),
    new_content_hash VARCHAR(64),
    old_chunk_count INTEGER DEFAULT 0,
    new_chunk_count INTEGER DEFAULT 0,
    user_id INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_details JSONB DEFAULT '{}',
    snapshot_id VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_ich_doc_changed ON index_change_history(doc_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ich_type ON index_change_history(change_type);
CREATE INDEX IF NOT EXISTS idx_ich_changed_at ON index_change_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_ich_snapshot ON index_change_history(snapshot_id);

-- 4. 统计表
CREATE TABLE IF NOT EXISTS index_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    namespace VARCHAR(100) DEFAULT 'default',
    total_documents INTEGER DEFAULT 0,
    indexed_documents INTEGER DEFAULT 0,
    pending_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    avg_index_time_seconds FLOAT DEFAULT 0,
    total_vectors INTEGER DEFAULT 0,
    storage_size_mb FLOAT DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    api_cost_usd FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date, namespace)
);

CREATE INDEX IF NOT EXISTS idx_is_stat_date ON index_statistics(stat_date DESC);
CREATE INDEX IF NOT EXISTS idx_is_namespace ON index_statistics(namespace, stat_date DESC);

-- 5. 为documents表添加字段(如果不存在)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='file_modified_at') THEN
        ALTER TABLE documents ADD COLUMN file_modified_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='file_size') THEN
        ALTER TABLE documents ADD COLUMN file_size BIGINT DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='content_hash') THEN
        ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='last_indexed_at') THEN
        ALTER TABLE documents ADD COLUMN last_indexed_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='index_status') THEN
        ALTER TABLE documents ADD COLUMN index_status VARCHAR(20) DEFAULT 'pending';
    END IF;
END $$;

-- 6. 为documents表添加索引
CREATE INDEX IF NOT EXISTS idx_doc_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_doc_last_indexed ON documents(last_indexed_at DESC);
CREATE INDEX IF NOT EXISTS idx_doc_index_status ON documents(index_status);
CREATE INDEX IF NOT EXISTS idx_doc_file_modified ON documents(file_modified_at DESC);

-- 7. 创建自动更新时间触发器
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

-- 8. 创建视图
CREATE OR REPLACE VIEW v_index_status_summary AS
SELECT
    COALESCE(d.namespace, 'default') as namespace,
    COUNT(*) as total_docs,
    COUNT(CASE WHEN d.index_status = 'indexed' THEN 1 END) as indexed_docs,
    COUNT(CASE WHEN d.index_status = 'pending' THEN 1 END) as pending_docs,
    COUNT(CASE WHEN d.index_status = 'failed' THEN 1 END) as failed_docs,
    COUNT(CASE WHEN d.index_status = 'outdated' THEN 1 END) as outdated_docs,
    MAX(d.last_indexed_at) as last_index_time
FROM documents d
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
