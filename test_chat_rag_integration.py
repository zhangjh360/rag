"""
测试Chat RAG集成
验证多领域检索是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.database import get_session_local
from app.services.chat_rag_service import ChatRAGService


async def test_single_query():
    """测试单个查询"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # 创建ChatRAGService
        chat_rag_service = ChatRAGService(db=db)

        # 测试查询列表
        test_queries = [
            "如何使用API认证？",
            "产品退货流程是什么？",
            "这个系统支持哪些功能？",
        ]

        print("=" * 80)
        print("Chat RAG 集成测试")
        print("=" * 80)

        for i, query in enumerate(test_queries, 1):
            print(f"\n测试 {i}: {query}")
            print("-" * 80)

            try:
                # 执行检索
                sources, metadata = await chat_rag_service.search_for_chat(
                    query=query,
                    session_id=f"test_session_{i}",
                    top_k=5,
                    similarity_threshold=0.2
                )

                # 显示结果
                print(f"✓ 检索成功!")

                if metadata:
                    classification = metadata.get('classification', {})
                    print(f"\n领域分类:")
                    print(f"  - Namespace: {classification.get('namespace', 'N/A')}")
                    print(f"  - Confidence: {classification.get('confidence', 0.0):.2f}")
                    print(f"  - Method: {classification.get('method', 'N/A')}")

                    print(f"\n检索统计:")
                    print(f"  - Mode: {metadata.get('retrieval_mode', 'N/A')}")
                    print(f"  - Method: {metadata.get('retrieval_method', 'N/A')}")
                    print(f"  - Total Latency: {metadata.get('total_latency_ms', 0):.0f}ms")
                    print(f"  - Classification Latency: {metadata.get('classification_latency_ms', 0):.0f}ms")
                    print(f"  - Retrieval Latency: {metadata.get('retrieval_latency_ms', 0):.0f}ms")

                    if metadata.get('error'):
                        print(f"  ⚠ 警告: {metadata['error']}")

                print(f"\n检索结果: {len(sources)} 条")
                if sources:
                    for j, source in enumerate(sources[:3], 1):
                        print(f"\n  结果 {j}:")
                        print(f"    - ID: {source.get('chunk_id')}")
                        print(f"    - 相似度: {source.get('similarity', 0.0):.3f}")
                        print(f"    - 文档: {source.get('filename', 'N/A')}")
                        print(f"    - 内容: {source.get('content', '')[:100]}...")
                        if 'domain_display_name' in source:
                            print(f"    - 领域: {source.get('domain_display_name')}")
                else:
                    print("  (无检索结果)")

            except Exception as e:
                print(f"✗ 检索失败: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 80)
        print("测试完成!")
        print("=" * 80)

    finally:
        db.close()


async def test_degradation():
    """测试降级策略"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        chat_rag_service = ChatRAGService(db=db)

        print("\n" + "=" * 80)
        print("降级策略测试")
        print("=" * 80)

        # 测试不存在的领域(应该触发降级)
        query = "完全不相关的随机查询xyz123"

        print(f"\n查询: {query}")
        print("-" * 80)

        sources, metadata = await chat_rag_service.search_for_chat(
            query=query,
            session_id="degradation_test",
            top_k=5
        )

        print(f"✓ 降级测试完成")
        print(f"  - 结果数: {len(sources)}")
        print(f"  - 模式: {metadata.get('retrieval_mode')}")

        if metadata.get('error'):
            print(f"  - 降级信息: {metadata['error']}")

    finally:
        db.close()


if __name__ == "__main__":
    print("\n开始测试...")

    # 运行测试
    asyncio.run(test_single_query())
    asyncio.run(test_degradation())

    print("\n所有测试完成! ✓")
