#!/usr/bin/env python3
"""
测试优化后的检索性能
验证 retrieve_relevant_chunks 方法的改进
"""

import time
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.advanced_retrieval import advanced_retrieval_service
from app.config.settings import DB_URL as DATABASE_URL
from app.config.logging_config import get_app_logger

logger = get_app_logger()

async def test_retrieval_performance():
    """测试检索性能"""

    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 测试查询
        test_queries = [
            "什么是机器学习？",
            "深度学习的原理是什么？",
            "如何优化神经网络？",
            "自然语言处理的应用",
            "推荐系统的算法"
        ]

        print("=" * 60)
        print("🔍 优化后的检索性能测试")
        print("=" * 60)

        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 测试查询 {i}: {query}")
            print("-" * 40)

            # 记录开始时间
            start_time = time.time()

            # 执行检索
            results = await advanced_retrieval_service.retrieve_relevant_chunks(
                db=db,
                query_text=query,
                top_k=5
            )

            # 记录结束时间
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # 转换为毫秒

            print(f"⏱️  检索时间: {duration:.2f}ms")
            print(f"📊 返回结果数: {len(results)}")

            # 显示前3个结果
            for j, result in enumerate(results[:3], 1):
                similarity = result.get('similarity', 0)
                filename = result.get('filename', 'unknown')
                content_preview = result.get('content', '')[:100] + '...'

                print(f"  {j}. [{similarity:.4f}] {filename}")
                print(f"     {content_preview}")

            if not results:
                print("   ❌ 未找到相关文档")

        print("\n" + "=" * 60)
        print("✅ 性能测试完成")
        print("=" * 60)

        # 测试数据库中是否有chunks数据
        print("\n📊 数据库统计信息:")
        print("-" * 30)

        chunk_count_query = text("SELECT COUNT(*) FROM document_chunks")
        embedding_count_query = text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")

        total_chunks = db.execute(chunk_count_query).scalar()
        embedded_chunks = db.execute(embedding_count_query).scalar()

        print(f"总文档块数: {total_chunks}")
        print(f"已嵌入块数: {embedded_chunks}")
        print(f"嵌入率: {(embedded_chunks/total_chunks*100):.1f}%" if total_chunks > 0 else "嵌入率: 0%")

    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")

    finally:
        db.close()

async def test_accuracy():
    """测试检索准确性"""
    print("\n🎯 检索准确性测试")
    print("-" * 30)

    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 检查相似度分数是否合理
        query = "机器学习"
        results = await advanced_retrieval_service.retrieve_relevant_chunks(
            db=db,
            query_text=query,
            top_k=10
        )

        if results:
            print(f"查询: {query}")
            print("前10个结果的相似度分数:")

            for i, result in enumerate(results, 1):
                similarity = result.get('similarity', 0)
                print(f"  {i}. {similarity:.6f}")

            # 检查相似度分布
            similarities = [r.get('similarity', 0) for r in results]
            avg_similarity = sum(similarities) / len(similarities)
            max_similarity = max(similarities)
            min_similarity = min(similarities)

            print(f"\n相似度统计:")
            print(f"  平均值: {avg_similarity:.4f}")
            print(f"  最大值: {max_similarity:.4f}")
            print(f"  最小值: {min_similarity:.4f}")

            # 检查结果是否按相似度降序排列
            is_descending = all(similarities[i] >= similarities[i+1] for i in range(len(similarities)-1))
            print(f"  降序排列: {'✅' if is_descending else '❌'}")

    except Exception as e:
        logger.error(f"准确性测试失败: {e}")
        print(f"❌ 准确性测试失败: {e}")

    finally:
        db.close()

async def main():
    """主函数"""
    print("🚀 开始测试优化后的检索服务...")

    try:
        await test_retrieval_performance()
        await test_accuracy()

        print("\n✨ 所有测试完成！")

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"\n💥 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())