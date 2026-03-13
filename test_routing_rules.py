"""测试领域路由规则功能"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import get_db
from app.services.routing_rule_service import get_routing_rule_service
from app.services.domain_classifier import KeywordClassifier


async def test_routing_rule_matching():
    """测试路由规则匹配"""
    print("\n" + "=" * 60)
    print("测试路由规则匹配功能")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        service = get_routing_rule_service(db)
        
        # 测试用例
        test_queries = [
            "如何使用 Python 的 API 接口?",
            "我想退货,怎么办?",
            "我的简历有哪些项目经验?",
            "leetcode 算法题怎么做?",
            "今天天气怎么样?",  # 应该不匹配任何规则
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = service.match_query(query, min_confidence=0.0)
            
            if result:
                namespace, confidence, rule_name = result
                print(f"  ✅ 匹配成功")
                print(f"     规则: {rule_name}")
                print(f"     领域: {namespace}")
                print(f"     置信度: {confidence:.2f}")
            else:
                print(f"  ❌ 未匹配到规则")
    
    finally:
        db.close()


async def test_keyword_classifier_with_rules():
    """测试关键词分类器集成路由规则"""
    print("\n" + "=" * 60)
    print("测试关键词分类器 (含路由规则)")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        classifier = KeywordClassifier(db)
        
        test_queries = [
            "Python API 开发文档在哪里?",
            "我要退货退款",
            "张建红的工作经验如何?",
            "ACM 竞赛题目有哪些?",
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = await classifier.classify(query)
            
            print(f"  领域: {result.namespace}")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  方法: {result.method}")
            if hasattr(result, 'details') and result.details:
                print(f"  详情: {result.details}")
    
    finally:
        db.close()


async def test_rule_crud():
    """测试路由规则 CRUD 操作"""
    print("\n" + "=" * 60)
    print("测试路由规则 CRUD")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        service = get_routing_rule_service(db)
        
        # 列出所有规则
        print("\n当前所有规则:")
        rules = service.get_all_rules(include_inactive=True)
        for rule in rules:
            status = "✅" if rule.is_active else "❌"
            print(f"  {status} [{rule.id}] {rule.rule_name} -> {rule.target_namespace}")
        
        print(f"\n总计: {len(rules)} 条规则")
    
    finally:
        db.close()


async def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "领域路由规则测试" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # 测试1: 路由规则匹配
        await test_routing_rule_matching()
        
        # 测试2: 关键词分类器集成
        await test_keyword_classifier_with_rules()
        
        # 测试3: CRUD操作
        await test_rule_crud()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试完成!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
