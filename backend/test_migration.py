#!/usr/bin/env python3
"""测试数据库迁移 - 分步执行"""
import psycopg2
import sys

def execute_step(cur, step_name, sql):
    """执行单个步骤"""
    print(f"\n{step_name}")
    print(f"SQL: {sql[:100]}...")
    try:
        cur.execute(sql)
        print("✓ 成功")
        return True
    except Exception as e:
        print(f"✗ 失败: {e}")
        return False

def main():
    print("连接数据库...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="ragdb",
            user="postgres",
            password="admin!postgres123",
            connect_timeout=5
        )
        print("✓ 连接成功\n")
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return 1

    conn.autocommit = True
    cur = conn.cursor()

    # 步骤1: 扩展 documents 表
    execute_step(cur, "步骤1: 添加 namespace 到 documents",
                 "ALTER TABLE documents ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default';")

    execute_step(cur, "步骤2: 添加 domain_tags 到 documents",
                 "ALTER TABLE documents ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}';")

    execute_step(cur, "步骤3: 添加 domain_confidence 到 documents",
                 "ALTER TABLE documents ADD COLUMN IF NOT EXISTS domain_confidence FLOAT DEFAULT 0.0;")

    # 步骤4-5: 扩展 document_chunks 表
    execute_step(cur, "步骤4: 添加 namespace 到 document_chunks",
                 "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default';")

    execute_step(cur, "步骤5: 添加 domain_tags 到 document_chunks",
                 "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}';")

    # 步骤6: 创建 knowledge_domains 表
    sql = """
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
    """
    execute_step(cur, "步骤6: 创建 knowledge_domains 表", sql)

    # 步骤7: 创建索引
    execute_step(cur, "步骤7: 创建 documents namespace 索引",
                 "CREATE INDEX IF NOT EXISTS idx_documents_namespace ON documents(namespace);")

    execute_step(cur, "步骤8: 创建 document_chunks namespace 索引",
                 "CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON document_chunks(namespace);")

    execute_step(cur, "步骤9: 创建 knowledge_domains namespace 索引",
                 "CREATE INDEX IF NOT EXISTS idx_domains_namespace ON knowledge_domains(namespace);")

    # 步骤10: 插入默认数据
    sql = """
    INSERT INTO knowledge_domains (namespace, display_name, description, keywords, icon, color, priority)
    VALUES
        ('default', '默认知识库', '未分类的通用知识', '[]', 'folder', '#999999', 0),
        ('technical_docs', '技术文档', 'API、SDK、技术配置相关文档',
         '["API", "SDK", "接口", "配置", "部署"]', 'code', '#4A90E2', 10),
        ('product_support', '产品支持', '退换货、保修、售后服务相关',
         '["退货", "换货", "保修", "发票", "售后"]', 'support', '#F5A623', 20)
    ON CONFLICT (namespace) DO NOTHING;
    """
    execute_step(cur, "步骤10: 插入默认领域数据", sql)

    cur.close()
    conn.close()

    print("\n✅ 所有迁移步骤完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
