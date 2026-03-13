"""
直接通过psycopg2执行SQL迁移
避免SQL分割问题
"""
import os
import sys
import psycopg2
from app.config.settings import DB_URL
from sqlalchemy.engine.url import make_url
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration_direct():
    """直接执行SQL文件"""
    # 读取SQL文件
    sql_file = os.path.join(os.path.dirname(__file__), 'create_index_tables_simple.sql')
    logger.info(f"读取SQL文件: {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 解析数据库URL
    url = make_url(DB_URL)
    logger.info(f"连接数据库: {url.database}")

    # 连接数据库
    conn = psycopg2.connect(
        host=url.host,
        port=url.port or 5432,
        database=url.database,
        user=url.username,
        password=url.password
    )

    # 执行SQL（作为单个事务）
    try:
        cursor = conn.cursor()

        # 整个SQL文件作为一个完整脚本执行
        logger.info("执行SQL脚本...")
        cursor.execute(sql_content)

        conn.commit()
        logger.info("✓ 数据库迁移成功完成！")

        # 验证表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN (
                'document_index_records',
                'index_tasks',
                'index_change_history',
                'index_statistics'
            )
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        logger.info("\n创建的表:")
        for table in tables:
            logger.info(f"  ✓ {table[0]}")

        cursor.close()

    except Exception as e:
        conn.rollback()
        logger.error(f"✗ 数据库迁移失败: {e}", exc_info=True)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始执行增量更新表结构迁移")
    logger.info("=" * 60)

    run_migration_direct()

    logger.info("=" * 60)
    logger.info("迁移完成！")
    logger.info("=" * 60)
