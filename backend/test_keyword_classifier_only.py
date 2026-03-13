"""
仅测试关键词分类器
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_session_local
from app.services.domain_classifier import KeywordClassifier


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("测试关键词分类器")
    print("="*60)

    db = get_session_local()()
    try:
        # 首先查看数据库中的领域配置
        from app.models.knowledge_domain import KnowledgeDomain
        domains = db.query(KnowledgeDomain).filter(
            KnowledgeDomain.is_active == True
        ).all()

        print(f"\n找到 {len(domains)} 个活跃领域:")
        for domain in domains:
            print(f"\n领域: {domain.display_name} ({domain.namespace})")
            print(f"  关键词: {domain.keywords}")
            print(f"  描述: {domain.description}")

        # 创建分类器
        classifier = KeywordClassifier(db)

        # 测试查询
        test_queries = [
            "API配置",
            "api接口",
            "SDK文档",
            "退货流程",
            "保修政策",
            "如何使用产品"
        ]

        print("\n" + "="*60)
        print("分类测试:")
        print("="*60)

        for query in test_queries:
            print(f"\n查询: {query}")
            result = await classifier.classify(query)
            print(f"  领域: {result.display_name} ({result.namespace})")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  推理: {result.reasoning}")
            if result.metadata.get('matched_keywords'):
                print(f"  匹配关键词: {result.metadata['matched_keywords']}")
            if result.metadata.get('query_keywords'):
                print(f"  查询关键词: {result.metadata['query_keywords']}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
