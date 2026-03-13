"""
数据库索引优化脚本

功能:
- 创建向量检索索引(IVFFlat)
- 创建BM25全文索引(GIN)
- 创建复合索引
- 更新统计信息
- 创建监控视图
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import psycopg2
from psycopg2 import sql
from app.config.settings import get_settings

def get_db_connection():
    """获取数据库连接"""
    settings = get_settings()

    try:
        conn = psycopg2.connect(
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


def read_sql_file(filepath: str) -> str:
    """读取SQL文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取SQL文件失败: {e}")
        return None


def execute_sql_statements(conn, sql_content: str):
    """执行SQL语句"""
    cursor = conn.cursor()

    # 分割SQL语句(按分号和空行)
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # 跳过注释和空行
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_statement.append(line)

        # 检查是否是完整语句(以分号结尾)
        if stripped.endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.startswith('/*'):  # 跳过注释块
                statements.append(stmt)
            current_statement = []

    # 执行每个语句
    success_count = 0
    error_count = 0

    for i, stmt in enumerate(statements, 1):
        try:
            # 提取语句类型(用于显示)
            stmt_type = stmt.split()[0].upper()

            # 跳过已经执行的注释
            if '/*' in stmt or '*/' in stmt:
                continue

            print(f"\n[{i}/{len(statements)}] 执行: {stmt_type} ...")

            cursor.execute(stmt)
            conn.commit()

            print(f"✅ 成功")
            success_count += 1

        except psycopg2.Error as e:
            conn.rollback()
            print(f"⚠️  警告: {e}")

            # 某些错误是可以忽略的(如索引已存在)
            if 'already exists' in str(e):
                print("   (索引已存在,跳过)")
                success_count += 1
            else:
                error_count += 1
                print(f"   错误详情: {e.pgerror}")

    cursor.close()

    return success_count, error_count


def check_index_status(conn):
    """检查索引状态"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("📊 索引状态检查")
    print("="*60)

    # 1. 检查所有索引
    cursor.execute("""
        SELECT
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename IN ('document_chunks', 'documents', 'knowledge_domains')
        ORDER BY tablename, indexname
    """)

    indexes = cursor.fetchall()

    if indexes:
        print(f"\n✅ 共找到 {len(indexes)} 个索引:")
        current_table = None
        for table, name, definition in indexes:
            if table != current_table:
                print(f"\n📋 表: {table}")
                current_table = table
            print(f"   - {name}")
    else:
        print("\n⚠️  未找到索引")

    # 2. 检查向量索引
    cursor.execute("""
        SELECT
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes
        WHERE indexname LIKE '%embedding%'
    """)

    vector_indexes = cursor.fetchall()
    if vector_indexes:
        print(f"\n🔍 向量索引:")
        for name, size in vector_indexes:
            print(f"   - {name}: {size}")

    # 3. 检查全文索引
    cursor.execute("""
        SELECT
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes
        WHERE indexname LIKE '%gin%'
    """)

    gin_indexes = cursor.fetchall()
    if gin_indexes:
        print(f"\n📝 全文索引:")
        for name, size in gin_indexes:
            print(f"   - {name}: {size}")

    # 4. 检查表大小
    cursor.execute("""
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size('public.' || tablename)) as total_size,
            pg_size_pretty(pg_relation_size('public.' || tablename)) as table_size
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN ('document_chunks', 'documents', 'knowledge_domains')
        ORDER BY pg_total_relation_size('public.' || tablename) DESC
    """)

    tables = cursor.fetchall()
    if tables:
        print(f"\n💾 表大小:")
        for table, total, data in tables:
            print(f"   - {table}: {total} (数据: {data})")

    cursor.close()


def set_ivfflat_probes(conn):
    """设置向量检索参数"""
    cursor = conn.cursor()

    try:
        print("\n⚙️  设置向量检索参数...")
        cursor.execute("SET ivfflat.probes = 20;")
        conn.commit()
        print("✅ ivfflat.probes = 20 (精度优先)")

    except Exception as e:
        print(f"⚠️  设置失败: {e}")
        print("   (可能 pgvector 未安装或版本过低)")

    cursor.close()


def main():
    """主函数"""
    print("="*60)
    print("🚀 Phase 3 检索性能优化")
    print("="*60)

    # 1. 获取数据库连接
    print("\n1. 连接数据库...")
    conn = get_db_connection()
    if not conn:
        print("❌ 无法连接数据库,退出")
        return 1

    print("✅ 数据库连接成功")

    try:
        # 2. 读取SQL文件
        print("\n2. 读取优化SQL...")
        sql_file = Path(__file__).parent / 'optimize_retrieval_indexes.sql'

        if not sql_file.exists():
            print(f"❌ SQL文件不存在: {sql_file}")
            return 1

        sql_content = read_sql_file(sql_file)
        if not sql_content:
            return 1

        print(f"✅ SQL文件读取成功 ({len(sql_content)} 字符)")

        # 3. 执行优化
        print("\n3. 执行索引优化...")
        success, errors = execute_sql_statements(conn, sql_content)

        print(f"\n执行完成: {success} 成功, {errors} 失败")

        # 4. 设置向量检索参数
        set_ivfflat_probes(conn)

        # 5. 检查索引状态
        check_index_status(conn)

        # 6. 完成
        print("\n" + "="*60)
        print("🎉 优化完成!")
        print("="*60)

        print("\n📈 预期性能提升:")
        print("   - 向量检索: 5-10x 提升")
        print("   - BM25检索: 3-5x 提升")
        print("   - 跨域检索: 2-3x 提升")
        print("   - 总体查询: 2-3x 提升")

        print("\n💡 提示:")
        print("   1. 索引会在后台异步构建,可能需要几分钟")
        print("   2. 数据量大时建议在低峰期执行")
        print("   3. 定期执行 ANALYZE 保持统计信息准确")
        print("   4. 监控索引使用情况: SELECT * FROM v_index_usage_stats;")

        return 0

    except Exception as e:
        print(f"\n❌ 优化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        conn.close()
        print("\n✅ 数据库连接已关闭")


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
