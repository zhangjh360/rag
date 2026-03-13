#!/usr/bin/env python3
"""简化的迁移脚本 - 直接执行SQL"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import psycopg2

DB_URL = "postgresql://postgres:admin!postgres123@localhost:5432/ragdb"

def main():
    print("开始数据库迁移...")

    try:
        # 使用 psycopg2 直接连接
        conn = psycopg2.connect(
            host="localhost",
            database="ragdb",
            user="postgres",
            password="admin!postgres123"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. 扩展 documents 表
        print("1. 扩展 documents 表...")
        cur.execute("""
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
            ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS domain_confidence FLOAT DEFAULT 0.0;
        """)
        print("   ✓ 完成")

        # 2. 扩展 document_chunks 表
        print("2. 扩展 document_chunks 表...")
        cur.execute("""
            ALTER TABLE document_chunks
            ADD COLUMN IF NOT EXISTS namespace VARCHAR(100) NOT NULL DEFAULT 'default',
            ADD COLUMN IF NOT EXISTS domain_tags JSONB DEFAULT '{}';
        """)
        print("   ✓ 完成")

        # 3. 创建 knowledge_domains 表
        print("3. 创建 knowledge_domains 表...")
        cur.execute("""
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
        """)
        print("   ✓ 完成")

        # 4. 创建索引
        print("4. 创建索引...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_namespace ON documents(namespace);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON document_chunks(namespace);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_domains_namespace ON knowledge_domains(namespace);")
        print("   ✓ 完成")

        # 5. 插入默认数据
        print("5. 插入默认领域数据...")
        cur.execute("""
            INSERT INTO knowledge_domains (namespace, display_name, description, keywords, icon, color, priority)
            VALUES
                ('default', '默认知识库', '未分类的通用知识', '[]', 'folder', '#999999', 0),
                ('technical_docs', '技术文档', 'API、SDK、技术配置相关文档',
                 '["API", "SDK", "接口", "配置", "部署"]', 'code', '#4A90E2', 10),
                ('product_support', '产品支持', '退换货、保修、售后服务相关',
                 '["退货", "换货", "保修", "发票", "售后"]', 'support', '#F5A623', 20)
            ON CONFLICT (namespace) DO NOTHING;
        """)
        print("   ✓ 完成")

        cur.close()
        conn.close()

        print("\n✅ 数据库迁移完成!")
        return 0

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
