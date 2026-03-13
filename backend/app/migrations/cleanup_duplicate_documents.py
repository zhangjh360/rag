"""
数据清理脚本: 清理重复文档
Phase 3: 数据库优化 - 准备工作

功能:
1. 识别重复文档 (相同 filename + namespace)
2. 保留最新版本(根据 created_at 或 id)
3. 删除旧版本及其关联的 document_chunks
4. 生成清理报告

执行方式:
1. 预览模式 (默认): 只显示将要删除的数据,不实际删除
   python cleanup_duplicate_documents.py

2. 执行模式: 实际删除重复数据
   python cleanup_duplicate_documents.py --execute

3. 强制模式: 跳过确认直接删除
   python cleanup_duplicate_documents.py --execute --force
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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_duplicates(conn):
    """查找所有重复的文档组"""
    logger.info("正在扫描重复文档...")

    # 查找重复的 (filename, namespace) 组合
    result = conn.execute(text("""
        SELECT
            filename,
            namespace,
            COUNT(*) as duplicate_count,
            array_agg(id ORDER BY created_at DESC, id DESC) as doc_ids,
            array_agg(created_at ORDER BY created_at DESC, id DESC) as created_times
        FROM documents
        GROUP BY filename, namespace
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC, filename
    """))

    duplicates = result.fetchall()
    return duplicates


def get_document_stats(conn, doc_id):
    """获取文档的详细统计信息"""
    # 获取文档块数量
    chunks_result = conn.execute(text("""
        SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id
    """), {"doc_id": doc_id})
    chunks_count = chunks_result.scalar()

    # 获取文档元数据
    doc_result = conn.execute(text("""
        SELECT
            id,
            filename,
            namespace,
            created_at,
            LENGTH(content) as content_length,
            doc_metadata
        FROM documents
        WHERE id = :doc_id
    """), {"doc_id": doc_id})
    doc = doc_result.fetchone()

    return {
        "id": doc.id if doc else None,
        "filename": doc.filename if doc else None,
        "namespace": doc.namespace if doc else None,
        "created_at": doc.created_at if doc else None,
        "content_length": doc.content_length if doc else 0,
        "chunks_count": chunks_count,
        "metadata": doc.doc_metadata if doc else None
    }


def preview_cleanup(duplicates, conn):
    """预览将要删除的数据"""
    logger.info("\n" + "="*80)
    logger.info("预览模式: 以下是将要删除的重复文档")
    logger.info("="*80 + "\n")

    total_docs_to_delete = 0
    total_chunks_to_delete = 0

    for idx, dup in enumerate(duplicates, 1):
        filename = dup.filename
        namespace = dup.namespace
        doc_ids = dup.doc_ids
        duplicate_count = dup.duplicate_count

        logger.info(f"\n【重复组 {idx}/{len(duplicates)}】")
        logger.info(f"  文件名: {filename}")
        logger.info(f"  命名空间: {namespace}")
        logger.info(f"  重复数量: {duplicate_count}")
        logger.info(f"  保留: 最新版本 (ID: {doc_ids[0]})")
        logger.info(f"  删除: {duplicate_count - 1} 个旧版本")
        logger.info("")

        # 显示每个版本的详细信息
        for i, doc_id in enumerate(doc_ids):
            stats = get_document_stats(conn, doc_id)
            status = "✓ 保留" if i == 0 else "✗ 删除"

            logger.info(f"    {status} ID={doc_id}")
            logger.info(f"         创建时间: {stats['created_at']}")
            logger.info(f"         内容大小: {stats['content_length']} 字符")
            logger.info(f"         文档块数: {stats['chunks_count']}")

            if i > 0:  # 统计将要删除的
                total_docs_to_delete += 1
                total_chunks_to_delete += stats['chunks_count']

        logger.info("")

    logger.info("="*80)
    logger.info("清理统计预览:")
    logger.info(f"  将删除文档: {total_docs_to_delete} 个")
    logger.info(f"  将删除文档块: {total_chunks_to_delete} 个")
    logger.info(f"  释放空间: 预估 {(total_chunks_to_delete * 1000) // 1024} KB")
    logger.info("="*80 + "\n")

    return total_docs_to_delete, total_chunks_to_delete


def execute_cleanup(duplicates, conn, force=False):
    """执行清理操作"""
    total_docs_deleted = 0
    total_chunks_deleted = 0
    errors = []

    logger.info("\n" + "="*80)
    logger.info("开始执行清理...")
    logger.info("="*80 + "\n")

    for idx, dup in enumerate(duplicates, 1):
        filename = dup.filename
        namespace = dup.namespace
        doc_ids = dup.doc_ids  # 已按创建时间倒序排列

        # 保留第一个(最新的),删除其余的
        keep_id = doc_ids[0]
        delete_ids = doc_ids[1:]

        logger.info(f"处理重复组 {idx}/{len(duplicates)}: {filename} ({namespace})")
        logger.info(f"  保留 ID={keep_id}, 删除 {len(delete_ids)} 个旧版本...")

        for doc_id in delete_ids:
            try:
                # 获取统计信息
                stats = get_document_stats(conn, doc_id)

                # 删除文档块
                chunks_result = conn.execute(text("""
                    DELETE FROM document_chunks
                    WHERE document_id = :doc_id
                """), {"doc_id": doc_id})
                chunks_deleted = chunks_result.rowcount

                # 删除用户关联
                conn.execute(text("""
                    DELETE FROM user_documents
                    WHERE document_id = :doc_id
                """), {"doc_id": doc_id})

                # 删除索引记录
                conn.execute(text("""
                    DELETE FROM document_index_records
                    WHERE doc_id = :doc_id
                """), {"doc_id": doc_id})

                # 删除文档
                doc_result = conn.execute(text("""
                    DELETE FROM documents
                    WHERE id = :doc_id
                """), {"doc_id": doc_id})
                docs_deleted = doc_result.rowcount

                total_docs_deleted += docs_deleted
                total_chunks_deleted += chunks_deleted

                logger.info(f"    ✓ 已删除 ID={doc_id}: {chunks_deleted} 个文档块")

            except Exception as e:
                error_msg = f"删除文档 {doc_id} 失败: {e}"
                logger.error(f"    ✗ {error_msg}")
                errors.append(error_msg)

        logger.info("")

    logger.info("="*80)
    logger.info("清理完成!")
    logger.info(f"  成功删除文档: {total_docs_deleted} 个")
    logger.info(f"  成功删除文档块: {total_chunks_deleted} 个")

    if errors:
        logger.warning(f"  错误数量: {len(errors)}")
        logger.warning("  错误详情:")
        for error in errors[:10]:  # 只显示前10个错误
            logger.warning(f"    - {error}")
        if len(errors) > 10:
            logger.warning(f"    ... 还有 {len(errors) - 10} 个错误")

    logger.info("="*80 + "\n")

    return total_docs_deleted, total_chunks_deleted, errors


def run_cleanup(execute=False, force=False):
    """运行清理流程"""
    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        try:
            # 查找重复文档
            duplicates = find_duplicates(conn)

            if not duplicates:
                logger.info("\n✅ 没有发现重复文档,数据库状态良好!\n")
                return True

            logger.info(f"\n发现 {len(duplicates)} 组重复文档\n")

            if not execute:
                # 预览模式
                preview_cleanup(duplicates, conn)
                logger.info("💡 提示:")
                logger.info("   这是预览模式,没有实际删除数据")
                logger.info("   如需执行清理,请使用: python cleanup_duplicate_documents.py --execute")
                logger.info("")
                return True

            # 执行模式
            # 先预览
            total_docs, total_chunks = preview_cleanup(duplicates, conn)

            # 确认
            if not force:
                logger.warning("⚠️  警告: 即将删除上述数据,此操作不可撤销!")
                confirm = input("\n是否继续? (输入 'YES' 确认): ")
                if confirm != "YES":
                    logger.info("已取消操作")
                    return False

            # 执行清理
            docs_deleted, chunks_deleted, errors = execute_cleanup(duplicates, conn)

            if errors:
                logger.warning(f"\n⚠️  清理完成,但有 {len(errors)} 个错误")
                return False
            else:
                logger.info("\n✅ 清理成功完成!")
                logger.info("\n下一步:")
                logger.info("   运行数据库迁移添加唯一约束:")
                logger.info("   python backend/app/migrations/add_document_constraints.py")
                logger.info("")
                return True

        except Exception as e:
            logger.error(f"\n❌ 清理失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="清理重复文档")
    parser.add_argument("--execute", action="store_true",
                       help="执行清理(默认为预览模式)")
    parser.add_argument("--force", action="store_true",
                       help="强制执行,跳过确认提示")

    args = parser.parse_args()

    success = run_cleanup(execute=args.execute, force=args.force)
    sys.exit(0 if success else 1)
