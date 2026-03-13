#!/usr/bin/env python3
"""
测试增量更新功能(不通过API)
直接调用服务类测试核心功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.connection import get_db
from app.services.change_detector import create_change_detector
from app.services.incremental_indexer import create_incremental_indexer
from app.models.database import Document
from sqlalchemy import text

def test_change_detection():
    """测试变更检测功能"""
    print("\n" + "="*60)
    print("测试1: 变更检测功能")
    print("="*60)

    db = next(get_db())

    try:
        detector = create_change_detector(db)

        # 获取所有documents数量
        total_docs = db.query(Document).count()
        print(f"数据库中总文档数: {total_docs}")

        if total_docs == 0:
            print("⚠ 数据库中没有文档,跳过变更检测测试")
            return

        # 测试基于哈希的精确检测
        print("\n测试: 基于哈希的精确变更检测")
        new_docs, modified_docs, unchanged_docs = detector.detect_changes_by_hash()

        print(f"  ✓ 新增文档: {len(new_docs)}")
        print(f"  ✓ 修改文档: {len(modified_docs)}")
        print(f"  ✓ 未变更文档: {len(unchanged_docs)}")

        if new_docs:
            print(f"\n新增文档示例 (前3个):")
            for doc in new_docs[:3]:
                print(f"    - ID={doc.id}, filename={doc.filename}")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_index_records():
    """测试索引记录查询"""
    print("\n" + "="*60)
    print("测试2: 索引记录表")
    print("="*60)

    db = next(get_db())

    try:
        # 查询索引记录统计
        result = db.execute(text("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT namespace) as namespace_count
            FROM document_index_records
        """))
        row = result.fetchone()

        print(f"  索引记录总数: {row[0]}")
        print(f"  命名空间数量: {row[1]}")

        # 查询最近的索引记录
        result = db.execute(text("""
            SELECT doc_id, content_hash, chunk_count, indexed_at
            FROM document_index_records
            ORDER BY indexed_at DESC
            LIMIT 5
        """))
        records = result.fetchall()

        if records:
            print(f"\n  最近的索引记录 (前5条):")
            for rec in records:
                print(f"    - doc_id={rec[0]}, chunks={rec[2]}, indexed_at={rec[3]}")
        else:
            print("  ⚠ 暂无索引记录")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_index_tasks():
    """测试任务队列表"""
    print("\n" + "="*60)
    print("测试3: 任务队列表")
    print("="*60)

    db = next(get_db())

    try:
        result = db.execute(text("""
            SELECT
                status,
                COUNT(*) as count
            FROM index_tasks
            GROUP BY status
            ORDER BY status
        """))
        status_counts = result.fetchall()

        if status_counts:
            print("  任务状态统计:")
            for status, count in status_counts:
                print(f"    - {status}: {count}")
        else:
            print("  ⚠ 暂无任务记录")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_change_history():
    """测试变更历史表"""
    print("\n" + "="*60)
    print("测试4: 变更历史表")
    print("="*60)

    db = next(get_db())

    try:
        result = db.execute(text("""
            SELECT
                change_type,
                COUNT(*) as count
            FROM index_change_history
            GROUP BY change_type
            ORDER BY change_type
        """))
        change_counts = result.fetchall()

        if change_counts:
            print("  变更类型统计:")
            for change_type, count in change_counts:
                print(f"    - {change_type}: {count}")
        else:
            print("  ⚠ 暂无变更历史")

        # 查询最近的变更
        result = db.execute(text("""
            SELECT doc_id, change_type, changed_at
            FROM index_change_history
            ORDER BY changed_at DESC
            LIMIT 5
        """))
        recent_changes = result.fetchall()

        if recent_changes:
            print(f"\n  最近的变更记录 (前5条):")
            for doc_id, change_type, changed_at in recent_changes:
                print(f"    - doc_id={doc_id}, type={change_type}, at={changed_at}")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("增量更新功能测试")
    print("="*60)

    test_change_detection()
    test_index_records()
    test_index_tasks()
    test_change_history()

    print("\n" + "="*60)
    print("✓ 所有测试完成!")
    print("="*60)
