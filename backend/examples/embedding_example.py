#!/usr/bin/env python3
"""
嵌入向量服务使用示例
展示如何使用 langchain_huggingface 实现的嵌入服务
"""

import asyncio
import os
from app.services.embedding import create_embedding_service

async def main():
    """主函数，演示嵌入服务的使用"""
    
    print("=== 嵌入向量服务使用示例 ===\n")
    
    # 1. 创建不同的嵌入服务实例
    
    # 使用 HuggingFace 本地模型
    print("1. 创建 HuggingFace 嵌入服务...")
    hf_service = create_embedding_service(
        backend="huggingface",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",  # 使用CPU，如果有GPU可以改为"cuda"
        cache_size=100
    )
    
    # 使用 OpenAI API（如果配置了API密钥）
    print("2. 创建 OpenAI 嵌入服务...")
    try:
        openai_service = create_embedding_service(
            backend="openai",
            model_name="text-embedding-ada-002"
        )
        print("   OpenAI 服务创建成功")
    except Exception as e:
        print(f"   OpenAI 服务创建失败: {e}")
        openai_service = None
    
    # 2. 测试单个文本嵌入
    print("\n3. 测试单个文本嵌入...")
    test_text = "这是一个测试文本，用于生成嵌入向量。"
    
    try:
        hf_embedding = await hf_service.create_embedding(test_text)
        print(f"   HuggingFace 嵌入向量维度: {len(hf_embedding)}")
        print(f"   前5个值: {hf_embedding[:5]}")
    except Exception as e:
        print(f"   HuggingFace 嵌入失败: {e}")
    
    if openai_service:
        try:
            openai_embedding = await openai_service.create_embedding(test_text)
            print(f"   OpenAI 嵌入向量维度: {len(openai_embedding)}")
            print(f"   前5个值: {openai_embedding[:5]}")
        except Exception as e:
            print(f"   OpenAI 嵌入失败: {e}")
    
    # 3. 测试批量嵌入
    print("\n4. 测试批量嵌入...")
    test_texts = [
        "第一个测试文本",
        "第二个测试文本",
        "第三个测试文本"
    ]
    
    try:
        batch_embeddings = await hf_service.create_batch_embeddings(test_texts)
        print(f"   批量嵌入成功，共 {len(batch_embeddings)} 个向量")
        for i, embedding in enumerate(batch_embeddings):
            print(f"   文本 {i+1} 向量维度: {len(embedding)}")
    except Exception as e:
        print(f"   批量嵌入失败: {e}")
    
    # 4. 测试相似度计算
    print("\n5. 测试相似度计算...")
    text1 = "人工智能是计算机科学的一个分支"
    text2 = "AI是计算机科学的重要领域"
    text3 = "今天天气很好，适合出门散步"
    
    try:
        embedding1 = await hf_service.create_embedding(text1)
        embedding2 = await hf_service.create_embedding(text2)
        embedding3 = await hf_service.create_embedding(text3)
        
        similarity_1_2 = hf_service.cosine_similarity(embedding1, embedding2)
        similarity_1_3 = hf_service.cosine_similarity(embedding1, embedding3)
        
        print(f"   文本1: {text1}")
        print(f"   文本2: {text2}")
        print(f"   相似度: {similarity_1_2:.4f}")
        print()
        print(f"   文本1: {text1}")
        print(f"   文本3: {text3}")
        print(f"   相似度: {similarity_1_3:.4f}")
    except Exception as e:
        print(f"   相似度计算失败: {e}")
    
    # 5. 测试最相似向量查找
    print("\n6. 测试最相似向量查找...")
    query_text = "机器学习算法"
    candidate_texts = [
        "深度学习是机器学习的一个子领域",
        "神经网络是深度学习的基础",
        "今天是个好日子",
        "人工智能技术发展迅速",
        "我喜欢吃苹果"
    ]
    
    try:
        query_embedding = await hf_service.create_embedding(query_text)
        candidate_embeddings = await hf_service.create_batch_embeddings(candidate_texts)
        
        similar_results = hf_service.find_most_similar(
            query_embedding, 
            candidate_embeddings, 
            top_k=3
        )
        
        print(f"   查询文本: {query_text}")
        print("   最相似的候选文本:")
        for i, (idx, score) in enumerate(similar_results):
            print(f"   {i+1}. {candidate_texts[idx]} (相似度: {score:.4f})")
    except Exception as e:
        print(f"   最相似向量查找失败: {e}")
    
    # 6. 测试缓存功能
    print("\n7. 测试缓存功能...")
    try:
        # 第一次调用
        start_time = asyncio.get_event_loop().time()
        embedding1 = await hf_service.create_embedding(test_text)
        first_time = asyncio.get_event_loop().time() - start_time
        
        # 第二次调用（应该从缓存获取）
        start_time = asyncio.get_event_loop().time()
        embedding2 = await hf_service.create_embedding(test_text)
        second_time = asyncio.get_event_loop().time() - start_time
        
        print(f"   第一次调用耗时: {first_time:.4f}秒")
        print(f"   第二次调用耗时: {second_time:.4f}秒")
        print(f"   缓存统计: {hf_service.get_cache_stats()}")
    except Exception as e:
        print(f"   缓存测试失败: {e}")
    
    print("\n=== 示例完成 ===")

if __name__ == "__main__":
    # 设置环境变量（如果需要）
    # os.environ["EMBEDDING_BACKEND"] = "huggingface"
    
    asyncio.run(main())
