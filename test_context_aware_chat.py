"""
测试会话上下文感知RAG系统
验证:
1. 查询重写功能
2. 领域继承功能
3. 三层数据持久化
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_engine, get_db
from app.services.chat_rag_service import ChatRAGService
from app.services.query_rewriter import QueryRewriter
from app.services.llm_service import LLMService
from sqlalchemy.orm import Session


async def test_query_rewriter():
    """测试查询重写功能"""
    print("\n" + "="*60)
    print("测试1: 查询重写功能")
    print("="*60)

    # 创建数据库会话
    engine = get_engine()
    db = next(get_db())

    try:
        llm_service = LLMService(db=db)
        rewriter = QueryRewriter(llm_service=llm_service)

        # 场景1: 确认性回复 "是的"
        print("\n场景1: 确认性回复")
        print("-" * 40)
        chat_history = [
            {"role": "user", "content": "张建红的到岗时间是多久?"},
            {"role": "assistant", "content": "张建红的到岗时间为一周内,如果您正在寻找一位有丰富Go语言开发经验、熟悉高性能系统架构和可观测性平台的工程师,他应该是一个理想人选。您是否需要我提供更多关于他特定技能或项目的详细信息?"}
        ]
        current_query = "是的"

        rewritten, was_rewritten = await rewriter.rewrite_with_context(
            current_query=current_query,
            chat_history=chat_history
        )

        print(f"原查询: {current_query}")
        print(f"重写后: {rewritten}")
        print(f"是否重写: {was_rewritten}")

        # 场景2: 代词引用 "我还做过什么项目?"
        print("\n场景2: 代词引用")
        print("-" * 40)
        chat_history2 = [
            {"role": "user", "content": "我是Python后端工程师,有5年微服务开发经验"},
            {"role": "assistant", "content": "作为一名Python后端工程师,您在微服务领域有丰富的经验..."}
        ]
        current_query2 = "我还做过什么项目?"

        rewritten2, was_rewritten2 = await rewriter.rewrite_with_context(
            current_query=current_query2,
            chat_history=chat_history2
        )

        print(f"原查询: {current_query2}")
        print(f"重写后: {rewritten2}")
        print(f"是否重写: {was_rewritten2}")

        # 场景3: 完整查询,无需重写
        print("\n场景3: 完整查询")
        print("-" * 40)
        current_query3 = "FastAPI的依赖注入是如何工作的?"

        rewritten3, was_rewritten3 = await rewriter.rewrite_with_context(
            current_query=current_query3,
            chat_history=[]
        )

        print(f"原查询: {current_query3}")
        print(f"重写后: {rewritten3}")
        print(f"是否重写: {was_rewritten3}")

        print("\n✅ 查询重写功能测试完成")

    finally:
        db.close()


async def test_domain_inheritance():
    """测试领域继承功能"""
    print("\n" + "="*60)
    print("测试2: 领域继承功能")
    print("="*60)

    # 创建数据库会话
    engine = get_engine()
    db = next(get_db())

    try:
        chat_rag_service = ChatRAGService(db=db)

        # 场景1: 第一次查询(建立领域上下文)
        print("\n第一次查询: 建立领域上下文")
        print("-" * 40)
        query1 = "我是Python后端工程师,有5年微服务开发经验"

        sources1, metadata1 = await chat_rag_service.search_for_chat(
            query=query1,
            session_id="test_session_001",
            top_k=3,
            enable_query_rewrite=False  # 第一次查询不需要重写
        )

        classification1 = metadata1.get('classification', {})
        print(f"查询: {query1}")
        print(f"分类领域: {classification1.get('namespace')}")
        print(f"置信度: {classification1.get('confidence'):.2f}")
        print(f"检索结果数: {len(sources1)}")

        # 场景2: 第二次查询(应该继承job_doc领域)
        print("\n第二次查询: 测试领域继承")
        print("-" * 40)
        query2 = "我还做过什么项目?"
        chat_history = [
            {"role": "user", "content": query1},
            {"role": "assistant", "content": "您有丰富的Python微服务开发经验..."}
        ]

        sources2, metadata2 = await chat_rag_service.search_for_chat(
            query=query2,
            session_id="test_session_001",
            top_k=3,
            chat_history=chat_history,
            previous_domain=classification1.get('namespace'),  # 传递上一轮领域
            enable_query_rewrite=True  # 启用查询重写
        )

        classification2 = metadata2.get('classification', {})
        query_rewrite = metadata2.get('query_rewrite', {})
        session_ctx = metadata2.get('session_context', {})

        print(f"原查询: {query2}")
        print(f"重写后: {query_rewrite.get('rewritten_query', query2)}")
        print(f"分类领域: {classification2.get('namespace')}")
        print(f"置信度: {classification2.get('confidence'):.2f}")
        print(f"是否继承: {session_ctx.get('domain_inherited')}")
        print(f"检索结果数: {len(sources2)}")

        if session_ctx.get('domain_inherited'):
            print(f"\n✅ 领域继承成功! 从 {classification1.get('namespace')} 继承到当前查询")
        else:
            print(f"\n⚠️ 未触发领域继承 (当前分类置信度: {classification2.get('confidence'):.2f})")

        print("\n✅ 领域继承功能测试完成")

    finally:
        db.close()


async def test_full_scenario():
    """测试完整的多轮对话场景"""
    print("\n" + "="*60)
    print("测试3: 完整多轮对话场景")
    print("="*60)

    # 创建数据库会话
    engine = get_engine()
    db = next(get_db())

    try:
        chat_rag_service = ChatRAGService(db=db)

        # 模拟三轮对话
        conversations = [
            {
                "query": "张建红的到岗时间是多久?",
                "previous_domain": None,
                "chat_history": []
            },
            {
                "query": "他的技术栈是什么?",
                "previous_domain": "job_doc",  # 假设第一轮分类为job_doc
                "chat_history": [
                    {"role": "user", "content": "张建红的到岗时间是多久?"},
                    {"role": "assistant", "content": "张建红的到岗时间为一周内..."}
                ]
            },
            {
                "query": "是的",  # 最具挑战性的查询
                "previous_domain": "job_doc",
                "chat_history": [
                    {"role": "user", "content": "张建红的到岗时间是多久?"},
                    {"role": "assistant", "content": "张建红的到岗时间为一周内..."},
                    {"role": "user", "content": "他的技术栈是什么?"},
                    {"role": "assistant", "content": "张建红精通Go语言、Kubernetes、Prometheus等...您是否需要更详细的项目经验?"}
                ]
            }
        ]

        for i, conv in enumerate(conversations, 1):
            print(f"\n第{i}轮对话:")
            print("-" * 40)

            sources, metadata = await chat_rag_service.search_for_chat(
                query=conv["query"],
                session_id="test_session_full",
                top_k=3,
                chat_history=conv["chat_history"],
                previous_domain=conv["previous_domain"],
                enable_query_rewrite=True
            )

            classification = metadata.get('classification', {})
            query_rewrite = metadata.get('query_rewrite', {})
            session_ctx = metadata.get('session_context', {})

            print(f"用户查询: {conv['query']}")

            if query_rewrite.get('was_rewritten'):
                print(f"查询重写: {query_rewrite.get('rewritten_query')}")

            print(f"领域分类: {classification.get('namespace')} (置信度: {classification.get('confidence'):.2f})")

            if session_ctx.get('domain_inherited'):
                print(f"✓ 继承上一轮领域")

            print(f"检索结果: {len(sources)} 条")

            if sources:
                print(f"首条结果: {sources[0]['content'][:100]}...")

        print("\n✅ 完整场景测试完成")

    finally:
        db.close()


async def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " " * 10 + "会话上下文感知RAG系统测试" + " " * 20 + "║")
    print("╚" + "="*58 + "╝")

    try:
        # 测试1: 查询重写
        await test_query_rewriter()

        # 测试2: 领域继承
        await test_domain_inheritance()

        # 测试3: 完整场景
        await test_full_scenario()

        print("\n" + "="*60)
        print("🎉 所有测试完成!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
