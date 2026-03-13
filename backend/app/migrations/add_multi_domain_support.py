"""
数据库迁移脚本: 添加多领域支持
Phase 1: 基础架构

执行步骤:
1. 为 documents 表添加 namespace, domain_tags, domain_confidence 字段
2. 为 document_chunks 表添加 namespace, domain_tags 字段
3. 创建 knowledge_domains 表
4. 创建 domain_routing_rules 表
5. 创建 domain_relationships 表
6. 创建必要的索引
7. 插入默认领域数据
"""

from sqlalchemy import create_engine, text
from app.config.settings import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """执行数据库迁移"""
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        try:
            logger.info("开始执行多领域支持迁移...")

            # ========== 步骤 1: 扩展 documents 表 ==========
            logger.info("1. 扩展 documents 表...")

            # 检查字段是否已存在
            check_column_sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'namespace';
            """
            result = conn.execute(text(check_column_sql))
            column_exists = result.fetchone() is not None

            if not column_exists:
                conn.execute(text("""
                    ALTER TABLE documents
                    ADD COLUMN namespace VARCHAR(100) NOT NULL DEFAULT 'default',
                    ADD COLUMN domain_tags JSONB DEFAULT '{}',
                    ADD COLUMN domain_confidence FLOAT DEFAULT 0.0;
                """))
                logger.info("   ✓ documents 表字段添加成功")
            else:
                logger.info("   - documents 表字段已存在,跳过")

            # ========== 步骤 2: 扩展 document_chunks 表 ==========
            logger.info("2. 扩展 document_chunks 表...")

            check_column_sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'document_chunks' AND column_name = 'namespace';
            """
            result = conn.execute(text(check_column_sql))
            column_exists = result.fetchone() is not None

            if not column_exists:
                conn.execute(text("""
                    ALTER TABLE document_chunks
                    ADD COLUMN namespace VARCHAR(100) NOT NULL DEFAULT 'default',
                    ADD COLUMN domain_tags JSONB DEFAULT '{}';
                """))
                logger.info("   ✓ document_chunks 表字段添加成功")
            else:
                logger.info("   - document_chunks 表字段已存在,跳过")

            # 从父文档继承 namespace
            logger.info("   - 同步 namespace 到文档块...")
            conn.execute(text("""
                UPDATE document_chunks dc
                SET namespace = COALESCE(
                    (SELECT d.namespace FROM documents d WHERE d.id = dc.document_id),
                    'default'
                )
                WHERE dc.namespace = 'default';
            """))
            logger.info("   ✓ 文档块 namespace 同步完成")

            # ========== 步骤 3: 创建 knowledge_domains 表 ==========
            logger.info("3. 创建 knowledge_domains 表...")

            conn.execute(text("""
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
            """))
            logger.info("   ✓ knowledge_domains 表创建成功")

            # ========== 步骤 4: 创建 domain_routing_rules 表 ==========
            logger.info("4. 创建 domain_routing_rules 表...")

            conn.execute(text("""
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
            """))
            logger.info("   ✓ domain_routing_rules 表创建成功")

            # ========== 步骤 5: 创建 domain_relationships 表 ==========
            logger.info("5. 创建 domain_relationships 表...")

            conn.execute(text("""
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
            """))
            logger.info("   ✓ domain_relationships 表创建成功")

            # ========== 步骤 6: 创建索引 ==========
            logger.info("6. 创建索引...")

            # documents 表索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_namespace
                ON documents(namespace, created_at DESC);
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_domain_tags
                ON documents USING GIN(domain_tags);
            """))

            # document_chunks 表索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_namespace
                ON document_chunks(namespace, document_id);
            """))

            # knowledge_domains 表索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_domains_namespace
                ON knowledge_domains(namespace);
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_domains_keywords
                ON knowledge_domains USING GIN(keywords);
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_domains_active
                ON knowledge_domains(is_active, priority DESC);
            """))

            # domain_routing_rules 表索引
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rules_type
                ON domain_routing_rules(rule_type, is_active);
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rules_priority
                ON domain_routing_rules(priority DESC);
            """))

            logger.info("   ✓ 所有索引创建成功")

            # ========== 步骤 7: 插入默认领域数据 ==========
            logger.info("7. 插入默认领域数据...")

            # 检查是否已有数据
            result = conn.execute(text("SELECT COUNT(*) FROM knowledge_domains"))
            count = result.scalar()

            if count == 0:
                conn.execute(text("""
                    INSERT INTO knowledge_domains
                    (namespace, display_name, description, keywords, icon, color, priority)
                    VALUES
                    ('default', '默认知识库', '未分类的通用知识', '[]', 'folder', '#999999', 0),
                    ('technical_docs', '技术文档', 'API、SDK、技术配置相关文档',
                     '["API", "SDK", "接口", "配置", "部署", "集成", "代码", "开发"]',
                     'code', '#4A90E2', 10),
                    ('product_support', '产品支持', '退换货、保修、售后服务相关',
                     '["退货", "换货", "保修", "发票", "售后", "维修", "质量", "投诉"]',
                     'support', '#F5A623', 20);
                """))
                logger.info("   ✓ 默认领域数据插入成功")
            else:
                logger.info(f"   - 已存在 {count} 个领域,跳过默认数据插入")

            logger.info("✅ 多领域支持迁移完成!")

        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            raise


def rollback_migration():
    """回滚迁移(可选)"""
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        logger.info("开始回滚多领域支持迁移...")

        try:
            # 删除索引
            logger.info("删除索引...")
            conn.execute(text("DROP INDEX IF EXISTS idx_documents_namespace"))
            conn.execute(text("DROP INDEX IF EXISTS idx_documents_domain_tags"))
            conn.execute(text("DROP INDEX IF EXISTS idx_chunks_namespace"))
            conn.execute(text("DROP INDEX IF EXISTS idx_domains_namespace"))
            conn.execute(text("DROP INDEX IF EXISTS idx_domains_keywords"))
            conn.execute(text("DROP INDEX IF EXISTS idx_domains_active"))
            conn.execute(text("DROP INDEX IF EXISTS idx_rules_type"))
            conn.execute(text("DROP INDEX IF EXISTS idx_rules_priority"))

            # 删除表
            logger.info("删除表...")
            conn.execute(text("DROP TABLE IF EXISTS domain_relationships"))
            conn.execute(text("DROP TABLE IF EXISTS domain_routing_rules"))
            conn.execute(text("DROP TABLE IF EXISTS knowledge_domains"))

            # 删除字段
            logger.info("删除字段...")
            conn.execute(text("""
                ALTER TABLE documents
                DROP COLUMN IF EXISTS namespace,
                DROP COLUMN IF EXISTS domain_tags,
                DROP COLUMN IF EXISTS domain_confidence;
            """))

            conn.execute(text("""
                ALTER TABLE document_chunks
                DROP COLUMN IF EXISTS namespace,
                DROP COLUMN IF EXISTS domain_tags;
            """))

            logger.info("✅ 回滚完成!")

        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()
