"""
运行增量更新表结构迁移脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database.connection import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """执行SQL迁移"""
    # 读取SQL文件
    sql_file = os.path.join(os.path.dirname(__file__), 'add_incremental_update_tables.sql')

    logger.info(f"读取SQL文件: {sql_file}")

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 获取数据库引擎
    engine = get_engine()

    # 执行SQL
    try:
        with engine.begin() as connection:
            # 分割SQL语句并逐个执行
            statements = sql_content.split(';')

            for i, statement in enumerate(statements, 1):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        connection.execute(text(statement))
                        logger.debug(f"执行语句 {i}/{len(statements)}")
                    except Exception as e:
                        # 某些语句可能因为已存在而失败，继续执行
                        if 'already exists' not in str(e).lower():
                            logger.warning(f"语句 {i} 执行警告: {e}")

        logger.info("✓ 数据库迁移成功完成！")

        # 验证表是否创建
        verify_tables(connection)

    except Exception as e:
        logger.error(f"✗ 数据库迁移失败: {e}", exc_info=True)
        raise


def verify_tables(connection):
    """验证表是否创建成功"""
    tables_to_check = [
        'document_index_records',
        'index_tasks',
        'index_change_history',
        'index_statistics'
    ]

    logger.info("\n验证表结构...")

    for table in tables_to_check:
        result = connection.execute(text(f"""
            SELECT COUNT(*) as cnt
            FROM information_schema.tables
            WHERE table_name = '{table}'
        """))
        count = result.fetchone()[0]

        if count > 0:
            logger.info(f"  ✓ 表 {table} 已存在")
        else:
            logger.error(f"  ✗ 表 {table} 不存在")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始执行增量更新表结构迁移")
    logger.info("=" * 60)

    run_migration()

    logger.info("=" * 60)
    logger.info("迁移完成！")
    logger.info("=" * 60)
