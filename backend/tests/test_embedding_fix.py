#!/usr/bin/env python3
"""
测试嵌入向量修复是否有效
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config.settings import DB_URL
from app.models.database import Document, Base
from app.services.embedding import create_embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_embedding_service():
    """测试嵌入向量服务"""
    try:
        logger.info("测试嵌入向量服务...")
        
        # 创建嵌入服务（使用HuggingFace本地模型）
        service = create_embedding_service(
            backend="huggingface",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"
        )
        
        # 测试文本
        test_text = "这是一个测试文档，用于验证嵌入向量功能是否正常工作。"
        
        # 创建嵌入向量
        embedding = await service.create_embedding(test_text)
        logger.info(f"嵌入向量创建成功，维度: {len(embedding)}")
        logger.info(f"前5个值: {embedding[:5]}")
        
        return embedding
        
    except Exception as e:
        logger.error(f"嵌入向量服务测试失败: {e}")
        return None

def test_database_connection():
    """测试数据库连接和表结构"""
    try:
        logger.info("测试数据库连接...")
        
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 检查表结构
            result = conn.execute(text("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'embedding'
            """))
            
            for row in result:
                logger.info(f"embedding字段类型: {row[1]} ({row[2]})")
                return True
            
            logger.warning("未找到embedding字段")
            return False
            
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

async def test_document_insertion(embedding):
    """测试文档插入"""
    try:
        logger.info("测试文档插入...")
        
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # 创建测试文档
            document = Document(
                content="这是一个测试文档",
                embedding=embedding,
                doc_metadata='{"test": true}',
                filename="test.txt",
                created_at="2024-01-01 00:00:00"
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"文档插入成功，ID: {document.id}")
            
            # 验证插入的数据
            result = db.execute(text("""
                SELECT id, content, array_length(embedding, 1) as embedding_dim
                FROM documents 
                WHERE id = :doc_id
            """), {"doc_id": document.id})
            
            for row in result:
                logger.info(f"验证结果 - ID: {row.id}, 内容: {row.content[:20]}..., 嵌入维度: {row.embedding_dim}")
            
            return True
            
    except Exception as e:
        logger.error(f"文档插入测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始测试嵌入向量修复...")
    
    # 1. 测试数据库连接
    if not test_database_connection():
        logger.error("数据库连接测试失败")
        sys.exit(1)
    
    # 2. 测试嵌入向量服务
    embedding = await test_embedding_service()
    if embedding is None:
        logger.error("嵌入向量服务测试失败")
        sys.exit(1)
    
    # 3. 测试文档插入
    if not await test_document_insertion(embedding):
        logger.error("文档插入测试失败")
        sys.exit(1)
    
    logger.info("所有测试通过！嵌入向量功能已修复。")

if __name__ == "__main__":
    asyncio.run(main())
