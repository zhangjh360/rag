-- ========================================
-- 多领域支持数据库迁移脚本 (Phase 1)
-- ========================================

-- 步骤 1: 扩展 documents 表
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS domain_confidence FLOAT DEFAULT 0.0;

-- 步骤 2: 扩展 document_chunks 表
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}';

-- 从父文档继承 namespace
UPDATE document_chunks dc
SET namespace = COALESCE(
    (SELECT d.namespace FROM documents d WHERE d.id = dc.document_id),
    'default'
)
WHERE EXISTS (SELECT 1 FROM documents d WHERE d.id = dc.document_id);

-- 步骤 3: 创建 knowledge_domains 表
CREATE TABLE IF NOT EXISTS knowledge_domains (
    id SERIAL PRIMARY KEY,
    namespace VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    keywords JSONB DEFAULT '[]',
    icon VARCHAR(50),
    color VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    priority INTEGER DEFAULT 0 NOT NULL,
    parent_namespace VARCHAR(100),
    permissions JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 步骤 4: 创建 domain_routing_rules 表
CREATE TABLE IF NOT EXISTS domain_routing_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    pattern TEXT NOT NULL,
    target_namespace VARCHAR(100) NOT NULL,
    confidence_threshold FLOAT DEFAULT 0.7,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 步骤 5: 创建 domain_relationships 表
CREATE TABLE IF NOT EXISTS domain_relationships (
    id SERIAL PRIMARY KEY,
    source_namespace VARCHAR(100) NOT NULL,
    related_namespace VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    weight FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_namespace, related_namespace, relationship_type)
);

-- 步骤 6: 创建索引
CREATE INDEX IF NOT EXISTS idx_documents_namespace ON documents(namespace, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_domain_tags ON documents USING GIN(domain_tags);
CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON document_chunks(namespace, document_id);
CREATE INDEX IF NOT EXISTS idx_domains_namespace ON knowledge_domains(namespace);
CREATE INDEX IF NOT EXISTS idx_domains_keywords ON knowledge_domains USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_domains_active ON knowledge_domains(is_active, priority DESC);
CREATE INDEX IF NOT EXISTS idx_rules_type ON domain_routing_rules(rule_type, is_active);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON domain_routing_rules(priority DESC);

-- 步骤 7: 插入默认领域数据
INSERT INTO knowledge_domains (namespace, display_name, description, keywords, icon, color, priority)
VALUES
    ('default', '默认知识库', '未分类的通用知识', '[]', 'folder', '#999999', 0),
    ('technical_docs', '技术文档', 'API、SDK、技术配置相关文档',
     '["API", "SDK", "接口", "配置", "部署", "集成", "代码", "开发"]',
     'code', '#4A90E2', 10),
    ('product_support', '产品支持', '退换货、保修、售后服务相关',
     '["退货", "换货", "保修", "发票", "售后", "维修", "质量", "投诉"]',
     'support', '#F5A623', 20)
ON CONFLICT (namespace) DO NOTHING;

-- 完成
SELECT '✅ 多领域支持迁移完成!' as status;
