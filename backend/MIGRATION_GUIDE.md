# 数据库迁移执行指南

## 方式1: 使用Docker直接执行 (推荐)

```bash
# 进入backend目录
cd /home/zhangjh/code/python/rag/backend

# 方法A: 复制SQL文件到容器并执行
sudo docker cp migrations_phase1.sql postgresql:/tmp/migrations_phase1.sql
sudo docker exec postgresql psql -U postgres -d ragdb -f /tmp/migrations_phase1.sql
sudo docker exec postgresql rm /tmp/migrations_phase1.sql

# 方法B: 通过管道直接执行
cat migrations_phase1.sql | sudo docker exec -i postgresql psql -U postgres -d ragdb
```

## 方式2: 使用Python脚本

```bash
cd /home/zhangjh/code/python/rag/backend

# 运行分步迁移脚本
python3 test_migration.py
```

## 方式3: 手动逐步执行

如果上述方式都有问题,可以手动连接数据库执行以下SQL:

### 步骤1: 连接数据库
```bash
sudo docker exec -it postgresql psql -U postgres -d ragdb
```

### 步骤2: 在psql中执行以下SQL

```sql
-- 1. 扩展 documents 表
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS domain_confidence FLOAT DEFAULT 0.0;

-- 2. 扩展 document_chunks 表
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}';

-- 3. 创建 knowledge_domains 表
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

-- 4. 创建 domain_routing_rules 表
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

-- 5. 创建 domain_relationships 表
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

-- 6. 创建索引
CREATE INDEX IF NOT EXISTS idx_documents_namespace ON documents(namespace, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_domain_tags ON documents USING GIN(domain_tags);
CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON document_chunks(namespace, document_id);
CREATE INDEX IF NOT EXISTS idx_domains_namespace ON knowledge_domains(namespace);
CREATE INDEX IF NOT EXISTS idx_domains_keywords ON knowledge_domains USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_domains_active ON knowledge_domains(is_active, priority DESC);
CREATE INDEX IF NOT EXISTS idx_rules_type ON domain_routing_rules(rule_type, is_active);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON domain_routing_rules(priority DESC);

-- 7. 插入默认领域数据
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

-- 8. 验证迁移
SELECT '✅ 多领域支持迁移完成!' as status;
```

## 验证迁移是否成功

```bash
# 检查新表是否创建
sudo docker exec postgresql psql -U postgres -d ragdb -c "\dt knowledge_domains"

# 检查默认数据是否插入
sudo docker exec postgresql psql -U postgres -d ragdb -c "SELECT namespace, display_name FROM knowledge_domains;"

# 检查 documents 表新字段
sudo docker exec postgresql psql -U postgres -d ragdb -c "\d documents"
```

## 预期结果

迁移成功后,您应该看到:
- 3个新表: `knowledge_domains`, `domain_routing_rules`, `domain_relationships`
- `documents` 表增加3个字段: `namespace`, `domain_tags`, `domain_confidence`
- `document_chunks` 表增加2个字段: `namespace`, `domain_tags`
- 3条默认领域数据: default, technical_docs, product_support

## 如果遇到问题

1. **权限错误**: 确保使用 `sudo` 执行Docker命令
2. **连接超时**: 检查PostgreSQL容器是否正常运行 `docker ps | grep postgresql`
3. **字段已存在**: 忽略此错误,说明字段已经添加
4. **表已存在**: 忽略此错误,说明表已经创建

## 联系支持

如果上述所有方式都失败,请检查:
- PostgreSQL容器状态: `docker ps`
- 容器日志: `docker logs postgresql`
- 数据库连接参数是否正确
