#!/usr/bin/env python3
"""
测试动态模型选择功能
"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, '/home/zhangjh/code/python/rag/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.llm_models import LLMModel
from app.services.llm_service import LLMService

# 创建数据库连接
engine = create_engine('sqlite:///./test.db', echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_dynamic_model_selection():
    """测试动态模型选择功能"""
    print("\n=== 测试动态模型选择功能 ===\n")

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 创建 LLMService 实例，传入数据库会话
        llm_service = LLMService(db=db)

        # 测试获取不同提供商的客户端
        test_models = [
            ("gpt-3.5-turbo", "openai"),
            ("gpt-4o", "openai"),
            ("glm-4", "zhipuai")
        ]

        for model_name, expected_provider in test_models:
            print(f"\n测试模型: {model_name} (预期提供商: {expected_provider})")
            try:
                client, actual_model, provider = llm_service._get_client_for_model(model_name)
                print(f"  ✓ 成功获取客户端")
                print(f"  - 提供商: {provider}")
                print(f"  - 实际模型名: {actual_model}")
                print(f"  - 客户端类型: {type(client).__name__}")

                # 验证提供商是否正确
                if provider == expected_provider:
                    print(f"  ✓ 提供商匹配成功")
                else:
                    print(f"  ✗ 提供商不匹配! 预期: {expected_provider}, 实际: {provider}")

            except Exception as e:
                print(f"  ✗ 获取客户端失败: {e}")

        print("\n=== 测试完成 ===\n")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_dynamic_model_selection()
