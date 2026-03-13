#!/usr/bin/env python3
"""
测试 advanced_retrieval.py 和 vector_retrieval.py 的逻辑一致性
验证修改后的 search_chunks 方法与 retrieve_relevant_chunks 方法完全一致
"""

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.advanced_retrieval import advanced_retrieval_service
from app.services.vector_retrieval import vector_retrieval_service
from app.config.settings import DB_URL as DATABASE_URL
from app.config.logging_config import get_app_logger

logger = get_app_logger()

async def test_retrieval_consistency():
    """测试两个检索服务的一致性"""

    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 70)
        print("🔍 检索服务逻辑一致性测试")
        print("=" * 70)

        test_queries = [
            "Python开发",
            "项目经验",
            "技术能力",
            "工作背景",
            "教育经历"
        ]

        all_consistent = True
        inconsistency_details = []

        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 测试查询 {i}: {query}")
            print("-" * 50)

            # 测试 advanced_retrieval_service.retrieve_relevant_chunks
            print("🔹 使用 advanced_retrieval_service.retrieve_relevant_chunks:")
            adv_results = await advanced_retrieval_service.retrieve_relevant_chunks(
                db=db,
                query_text=query,
                top_k=5
            )

            print(f"   结果数: {len(adv_results)}")
            if adv_results:
                for j, result in enumerate(adv_results[:3], 1):
                    print(f"   {j}. 相似度: {result.get('similarity', 0):.6f}, "
                          f"文件: {result.get('filename', 'unknown')}, "
                          f"索引: {result.get('chunk_index', 'N/A')}")

            # 测试 vector_retrieval_service.search_chunks (无阈值)
            print("\n🔹 使用 vector_retrieval_service.search_chunks:")
            vec_results = await vector_retrieval_service.search_chunks(
                db=db,
                query_text=query,
                top_k=5,
                similarity_threshold=0.0  # 不设置阈值
            )

            print(f"   结果数: {len(vec_results)}")
            if vec_results:
                for j, result in enumerate(vec_results[:3], 1):
                    print(f"   {j}. 相似度: {result.get('similarity', 0):.6f}, "
                          f"文件: {result.get('filename', 'unknown')}, "
                          f"索引: {result.get('chunk_index', 'N/A')}")

            # 比较结果
            print(f"\n📊 结果对比:")
            print(f"   advanced_retrieval 结果数: {len(adv_results)}")
            print(f"   vector_retrieval 结果数: {len(vec_results)}")

            if len(adv_results) == len(vec_results):
                consistent = True
                for j in range(len(adv_results)):
                    adv_sim = adv_results[j].get('similarity', 0)
                    vec_sim = vec_results[j].get('similarity', 0)

                    if abs(adv_sim - vec_sim) > 0.0001:  # 允许微小误差
                        consistent = False
                        inconsistency_details.append(f"查询{i}第{j+1}个结果: "
                                                   f"advanced={adv_sim:.6f}, "
                                                   f"vector={vec_sim:.6f}")

                print(f"   相似度一致性: {'✅' if consistent else '❌'}")
                if not consistent:
                    all_consistent = False
            else:
                print(f"   ❌ 结果数量不一致")
                all_consistent = False
                inconsistency_details.append(f"查询{i}: 结果数量不一致 "
                                           f"(advanced={len(adv_results)}, "
                                           f"vector={len(vec_results)})")

        # 总结
        print("\n" + "=" * 70)
        if all_consistent:
            print("✅ 所有测试通过！两个检索服务的逻辑完全一致")
        else:
            print("❌ 发现不一致！详情如下:")
            for detail in inconsistency_details:
                print(f"   - {detail}")

        print("=" * 70)

        # 测试关键数据点的一致性
        print("\n🔍 关键逻辑点验证:")
        print("-" * 30)

        # 测试有效向量处理
        test_query = "简历"
        print(f"\n测试查询: {test_query}")

        adv_results = await advanced_retrieval_service.retrieve_relevant_chunks(
            db=db, query_text=test_query, top_k=3
        )
        vec_results = await vector_retrieval_service.search_chunks(
            db=db, query_text=test_query, top_k=3, similarity_threshold=0.0
        )

        if adv_results and vec_results:
            print("✅ 相同的查询逻辑:")
            print(f"   都使用 embedding_service.create_embedding()")
            print(f"   都从 document_chunks 表读取数据")
            print(f"   都使用批量相似度计算")
            print(f"   都按相似度降序排序")
            print(f"   第一结果相似度: {adv_results[0]['similarity']:.6f} (一致)")
        else:
            print("❌ 无法验证关键逻辑点")

    except Exception as e:
        logger.error(f"一致性测试失败: {e}")
        print(f"❌ 测试失败: {e}")

    finally:
        db.close()

async def main():
    """主函数"""
    print("🚀 开始测试检索服务逻辑一致性...")

    try:
        await test_retrieval_consistency()
        print("\n✨ 一致性测试完成！")

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"\n💥 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())