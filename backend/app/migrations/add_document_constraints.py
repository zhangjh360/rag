"""
数据库迁移脚本: 添加文档唯一约束和外键
Phase 3: 数据库优化

执行步骤:
1. 添加 UNIQUE(filename, namespace) 约束到 documents 表
2. 添加外键约束 document_chunks.document_id -> documents.id (CASCADE DELETE)
3. 创建性能索引
4. 验证约束

注意事项:
- 执行前请确保已清理重复数据
- 外键约束将自动级联删除相关的 document_chunks
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent.parent  # backend/
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.config.settings import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_duplicates(conn):
    """检查是否存在重复的文档"""
    logger.info("检查重复文档...")

    result = conn.execute(text("""
        SELECT filename, namespace, COUNT(*) as count
        FROM documents
        GROUP BY filename, namespace
        HAVING COUNT(*) > 1
    """))

    duplicates = result.fetchall()

    if duplicates:
        logger.warning(f"⚠️  发现 {len(duplicates)} 组重复文档:")
        for row in duplicates[:10]:  # 只显示前10个
            logger.warning(f"   - filename='{row.filename}', namespace='{row.namespace}', count={row.count}")
        if len(duplicates) > 10:
            logger.warning(f"   ... 还有 {len(duplicates) - 10} 组重复")
        return False
    else:
        logger.info("✓ 没有发现重复文档")
        return True


def check_orphaned_chunks(conn):
    """检查是否存在孤立的文档块(没有对应的父文档)"""
    logger.info("检查孤立文档块...")

    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM document_chunks dc
        LEFT JOIN documents d ON dc.document_id = d.id
        WHERE d.id IS NULL
    """))

    orphan_count = result.scalar()

    if orphan_count > 0:
        logger.warning(f"⚠️  发现 {orphan_count} 个孤立文档块(没有对应的父文档)")
        return False
    else:
        logger.info("✓ 没有发现孤立文档块")
        return True


def run_migration():
    """执行数据库迁移"""
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        try:
            logger.info("========== 开始执行文档约束迁移 ==========\n")

            # ========== 步骤 0: 数据验证 ==========
            logger.info("步骤 0: 数据完整性验证")

            has_duplicates = not check_duplicates(conn)
            has_orphans = not check_orphaned_chunks(conn)

            if has_duplicates:
                logger.error("""
❌ 迁移中止: 检测到重复文档

解决方案:
1. 运行数据清理脚本清理重复数据
2. 或手动删除重复文档,保留最新版本
3. 然后重新执行此迁移
                """)
                return False

            if has_orphans:
                logger.warning("""
⚠️  检测到孤立文档块,将自动清理

这些文档块没有对应的父文档,可能是数据不一致导致的。
                """)
                # 清理孤立块
                result = conn.execute(text("""
                    DELETE FROM document_chunks dc
                    WHERE NOT EXISTS (
                        SELECT 1 FROM documents d WHERE d.id = dc.document_id
                    )
                """))
                deleted_count = result.rowcount
                logger.info(f"   ✓ 已清理 {deleted_count} 个孤立文档块")

            logger.info("")

            # ========== 步骤 1: 添加唯一约束 ==========
            logger.info("步骤 1: 添加 UNIQUE(filename, namespace) 约束...")

            # 检查约束是否已存在
            check_constraint_sql = """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'documents'
                AND constraint_name = 'uq_documents_filename_namespace'
            """
            result = conn.execute(text(check_constraint_sql))
            constraint_exists = result.fetchone() is not None

            if not constraint_exists:
                conn.execute(text("""
                    ALTER TABLE documents
                    ADD CONSTRAINT uq_documents_filename_namespace
                    UNIQUE (filename, namespace)
                """))
                logger.info("   ✓ 唯一约束添加成功")
            else:
                logger.info("   - 唯一约束已存在,跳过")

            # ========== 步骤 2: 添加外键约束 ==========
            logger.info("\n步骤 2: 添加外键约束 document_chunks -> documents...")

            # 检查外键是否已存在
            check_fk_sql = """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'document_chunks'
                AND constraint_name = 'fk_document_chunks_document_id'
            """
            result = conn.execute(text(check_fk_sql))
            fk_exists = result.fetchone() is not None

            if not fk_exists:
                conn.execute(text("""
                    ALTER TABLE document_chunks
                    ADD CONSTRAINT fk_document_chunks_document_id
                    FOREIGN KEY (document_id)
                    REFERENCES documents(id)
                    ON DELETE CASCADE
                """))
                logger.info("   ✓ 外键约束添加成功 (CASCADE DELETE 已启用)")
            else:
                logger.info("   - 外键约束已存在,跳过")

            # ========== 步骤 3: 创建性能索引 ==========
            logger.info("\n步骤 3: 创建性能索引...")

            # documents 表的组合索引 (filename, namespace)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_filename_namespace
                ON documents(filename, namespace)
            """))
            logger.info("   ✓ 创建索引: idx_documents_filename_namespace")

            # documents 表的 filename 单独索引 (用于前缀搜索)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_documents_filename
                ON documents(filename)
            """))
            logger.info("   ✓ 创建索引: idx_documents_filename")

            # document_chunks 表的 document_id 索引 (外键查询优化)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                ON document_chunks(document_id)
            """))
            logger.info("   ✓ 创建索引: idx_chunks_document_id")

            # ========== 步骤 4: 验证约束 ==========
            logger.info("\n步骤 4: 验证约束...")

            # 验证唯一约束 - 查询系统表确认约束存在
            check_unique_constraint = conn.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'documents'
                AND constraint_name = 'uq_documents_filename_namespace'
                AND constraint_type = 'UNIQUE'
            """)).fetchone()

            if check_unique_constraint:
                logger.info("   ✓ 唯一约束验证通过 (已存在)")
            else:
                logger.error("   ❌ 唯一约束验证失败 (未找到)")
                return False

            # 验证外键约束 - 查询系统表确认外键存在
            check_fk_constraint = conn.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'document_chunks'
                AND constraint_name = 'fk_document_chunks_document_id'
                AND constraint_type = 'FOREIGN KEY'
            """)).fetchone()

            if check_fk_constraint:
                logger.info("   ✓ 外键约束验证通过 (已存在)")
            else:
                logger.error("   ❌ 外键约束验证失败 (未找到)")
                return False

            logger.info("\n========== ✅ 文档约束迁移完成! ==========\n")
            logger.info("新增约束:")
            logger.info("  1. UNIQUE(filename, namespace) - 防止重复文档")
            logger.info("  2. FOREIGN KEY(document_id) ON DELETE CASCADE - 自动清理孤立块")
            logger.info("\n新增索引:")
            logger.info("  1. idx_documents_filename_namespace - 组合查询优化")
            logger.info("  2. idx_documents_filename - 文件名搜索优化")
            logger.info("  3. idx_chunks_document_id - 外键查询优化")
            logger.info("")

            return True

        except Exception as e:
            logger.error(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            raise


def rollback_migration():
    """回滚迁移"""
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        logger.info("开始回滚文档约束迁移...")

        try:
            # 删除外键约束
            logger.info("1. 删除外键约束...")
            conn.execute(text("""
                ALTER TABLE document_chunks
                DROP CONSTRAINT IF EXISTS fk_document_chunks_document_id
            """))
            logger.info("   ✓ 外键约束已删除")

            # 删除唯一约束
            logger.info("2. 删除唯一约束...")
            conn.execute(text("""
                ALTER TABLE documents
                DROP CONSTRAINT IF EXISTS uq_documents_filename_namespace
            """))
            logger.info("   ✓ 唯一约束已删除")

            # 删除索引
            logger.info("3. 删除索引...")
            conn.execute(text("DROP INDEX IF EXISTS idx_documents_filename_namespace"))
            conn.execute(text("DROP INDEX IF EXISTS idx_documents_filename"))
            conn.execute(text("DROP INDEX IF EXISTS idx_chunks_document_id"))
            logger.info("   ✓ 索引已删除")

            logger.info("\n✅ 回滚完成!")

        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        success = run_migration()
        sys.exit(0 if success else 1)
