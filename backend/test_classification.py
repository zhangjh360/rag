"""
测试领域分类功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_session_local
from app.services.domain_classifier import get_classifier


async def test_keyword_classifier():
    """测试关键词分类器"""
    print("\n" + "="*60)
    print("测试关键词分类器 (KeywordClassifier)")
    print("="*60)

    db = get_session_local()()
    try:
        classifier = get_classifier(db, classifier_type='keyword')

        test_queries = [
            "如何配置API密钥?",
            "产品保修期多长?",
            "我想退货",
            "SDK文档在哪里?",
            "发票怎么开?",
            "这是什么产品?"
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            result = await classifier.classify(query)
            print(f"领域: {result.display_name} ({result.namespace})")
            print(f"置信度: {result.confidence:.2f}")
            print(f"推理: {result.reasoning}")
            print(f"建议跨域: {result.fallback_to_cross_domain}")
            if result.alternatives:
                print(f"备选领域: {[a['display_name'] for a in result.alternatives[:2]]}")

    finally:
        db.close()


async def test_llm_classifier():
    """测试LLM分类器"""
    print("\n" + "="*60)
    print("测试LLM分类器 (LLMClassifier)")
    print("="*60)

    db = get_session_local()()
    try:
        classifier = get_classifier(db, classifier_type='llm')

        test_queries = [
            "我想了解一下你们的API文档在哪里查看?",
            "购买的产品出现质量问题,可以退货吗?"
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            try:
                result = await classifier.classify(query)
                print(f"领域: {result.display_name} ({result.namespace})")
                print(f"置信度: {result.confidence:.2f}")
                print(f"推理: {result.reasoning}")
                print(f"方法: {result.method}")
            except Exception as e:
                print(f"LLM分类失败: {str(e)}")

    finally:
        db.close()


async def test_hybrid_classifier():
    """测试混合分类器"""
    print("\n" + "="*60)
    print("测试混合分类器 (HybridClassifier)")
    print("="*60)

    db = get_session_local()()
    try:
        classifier = get_classifier(db, classifier_type='hybrid')

        test_queries = [
            "API密钥配置",  # 高置信度,应该只用关键词
            "我想问一下关于产品保修方面的问题",  # 低置信度,应该调用LLM
            "这个怎么用?"  # 模糊查询
        ]

        for query in test_queries:
            print(f"\n查询: {query}")
            result = await classifier.classify(query)
            print(f"领域: {result.display_name} ({result.namespace})")
            print(f"置信度: {result.confidence:.2f}")
            print(f"方法: {result.method}")
            print(f"推理: {result.reasoning}")
            if 'strategy' in result.metadata:
                print(f"策略: {result.metadata['strategy']}")

    finally:
        db.close()


async def test_classifier_performance():
    """测试分类器性能"""
    print("\n" + "="*60)
    print("测试分类器性能对比")
    print("="*60)

    db = get_session_local()()
    try:
        import time

        query = "API文档在哪里?"

        # 测试关键词分类器
        classifier = get_classifier(db, classifier_type='keyword')
        start = time.time()
        result = await classifier.classify(query)
        keyword_time = time.time() - start
        print(f"\n关键词分类器: {keyword_time*1000:.2f}ms")
        print(f"  结果: {result.display_name} (置信度: {result.confidence:.2f})")

        # 测试混合分类器
        classifier = get_classifier(db, classifier_type='hybrid')
        start = time.time()
        result = await classifier.classify(query)
        hybrid_time = time.time() - start
        print(f"\n混合分类器: {hybrid_time*1000:.2f}ms")
        print(f"  结果: {result.display_name} (置信度: {result.confidence:.2f})")
        print(f"  策略: {result.metadata.get('strategy', 'N/A')}")

    finally:
        db.close()


async def main():
    """主测试函数"""
    print("\n" + "#"*60)
    print("# 领域分类系统测试")
    print("#"*60)

    try:
        # 测试关键词分类器
        await test_keyword_classifier()

        # 测试混合分类器
        await test_hybrid_classifier()

        # 测试性能
        await test_classifier_performance()

        # LLM测试(可选,需要配置LLM)
        # await test_llm_classifier()

        print("\n" + "="*60)
        print("测试完成!")
        print("="*60)

    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
