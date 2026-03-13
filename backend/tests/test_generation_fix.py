#!/usr/bin/env python3
"""
测试生成服务修复是否有效
"""

import asyncio
import sys
import os
from app.services.generation import generation_service
from app.services.generation_async import async_generation_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_generation_service():
    """测试生成服务"""
    try:
        logger.info("测试生成服务...")
        
        # 测试数据
        query = "什么是人工智能？"
        context = """
        人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
        """
        
        # 测试同步版本（使用线程池）
        logger.info("测试同步版本生成服务...")
        response1 = await generation_service.generate_response(query, context)
        logger.info(f"同步版本响应: {response1[:100]}...")
        
        # 测试异步版本
        logger.info("测试异步版本生成服务...")
        response2 = await async_generation_service.generate_response(query, context)
        logger.info(f"异步版本响应: {response2[:100]}...")
        
        # 测试流式响应
        logger.info("测试流式响应...")
        stream_response = ""
        async for chunk in async_generation_service.generate_response_with_streaming(query, context):
            stream_response += chunk
            logger.info(f"流式片段: {chunk}")
            if len(stream_response) > 200:  # 限制测试长度
                break
        
        logger.info(f"流式响应: {stream_response[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"生成服务测试失败: {e}")
        return False

async def test_full_rag_pipeline():
    """测试完整的RAG流程"""
    try:
        logger.info("测试完整RAG流程...")
        
        from app.services.embedding import create_embedding_service
        from app.services.retrieval import retrieval_service
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.config.settings import DB_URL
        
        # 创建嵌入服务
        embedding_service = create_embedding_service(
            backend="huggingface",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        # 创建数据库连接
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # 测试查询
            test_query = "什么是机器学习？"
            
            # 检索相关文档
            retrieved_docs = await retrieval_service.retrieve_documents(db, test_query)
            logger.info(f"检索到 {len(retrieved_docs)} 个相关文档")
            
            if retrieved_docs:
                # 格式化上下文
                context = retrieval_service.format_context(retrieved_docs)
                logger.info(f"上下文长度: {len(context)} 字符")
                
                # 生成回答
                response = await generation_service.generate_response(test_query, context)
                logger.info(f"生成的回答: {response[:200]}...")
                
                return True
            else:
                logger.warning("没有检索到相关文档，请先上传一些文档")
                return False
                
    except Exception as e:
        logger.error(f"完整RAG流程测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始测试生成服务修复...")
    
    # 1. 测试生成服务
    if not await test_generation_service():
        logger.error("生成服务测试失败")
        sys.exit(1)
    
    # 2. 测试完整RAG流程
    if not await test_full_rag_pipeline():
        logger.warning("完整RAG流程测试失败，可能是数据库问题")
    
    logger.info("所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
