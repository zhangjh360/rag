#!/usr/bin/env python3
"""
数据库迁移脚本：将embedding字段从TSVECTOR类型改为ARRAY(Float)类型
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config.settings import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_embedding_column():
    """迁移embedding字段类型"""
    try:
        # 创建数据库连接
        engine = create_engine(DB_URL)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 检查当前表结构
                logger.info("检查当前表结构...")
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'embedding'
                """))
                
                current_type = None
                for row in result:
                    current_type = row[1]
                    logger.info(f"当前embedding字段类型: {current_type}")
                
                if not current_type:
                    logger.error("未找到embedding字段，请检查表结构")
                    return False
                
                # 2. 如果已经是正确的类型，跳过迁移
                if current_type == 'ARRAY':
                    logger.info("embedding字段已经是ARRAY类型，无需迁移")
                    return True
                
                # 3. 备份现有数据（如果有的话）
                logger.info("检查现有数据...")
                count_result = conn.execute(text("SELECT COUNT(*) FROM documents"))
                doc_count = count_result.scalar()
                logger.info(f"现有文档数量: {doc_count}")
                
                if doc_count > 0:
                    logger.warning(f"发现 {doc_count} 个现有文档，将清空embedding字段")
                    # 清空embedding字段，因为TSVECTOR和ARRAY不兼容
                    conn.execute(text("UPDATE documents SET embedding = NULL"))
                
                # 4. 删除旧的embedding列
                logger.info("删除旧的embedding列...")
                conn.execute(text("ALTER TABLE documents DROP COLUMN IF EXISTS embedding"))
                
                # 5. 添加新的embedding列
                logger.info("添加新的embedding列...")
                conn.execute(text("""
                    ALTER TABLE documents 
                    ADD COLUMN embedding REAL[]
                """))
                
                # 6. 添加注释
                conn.execute(text("""
                    COMMENT ON COLUMN documents.embedding IS '文档嵌入向量'
                """))
                
                # 提交事务
                trans.commit()
                logger.info("数据库迁移完成！")
                
                # 7. 验证迁移结果
                logger.info("验证迁移结果...")
                result = conn.execute(text("""
                    SELECT column_name, data_type, udt_name
                    FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'embedding'
                """))
                
                for row in result:
                    logger.info(f"新embedding字段类型: {row[1]} ({row[2]})")
                
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"迁移失败，已回滚: {e}")
                raise
                
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

def create_documents_table_if_not_exists():
    """如果表不存在则创建表"""
    try:
        engine = create_engine(DB_URL)
        
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'documents'
                )
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("documents表不存在，创建新表...")
                conn.execute(text("""
                    CREATE TABLE documents (
                        id SERIAL PRIMARY KEY,
                        content TEXT,
                        embedding REAL[],
                        doc_metadata VARCHAR,
                        filename VARCHAR,
                        created_at VARCHAR
                    )
                """))
                
                # 添加注释
                conn.execute(text("""
                    COMMENT ON TABLE documents IS '文档存储表';
                    COMMENT ON COLUMN documents.id IS '文档ID';
                    COMMENT ON COLUMN documents.content IS '文档内容';
                    COMMENT ON COLUMN documents.embedding IS '文档嵌入向量';
                    COMMENT ON COLUMN documents.doc_metadata IS '文档元数据';
                    COMMENT ON COLUMN documents.filename IS '文件名';
                    COMMENT ON COLUMN documents.created_at IS '创建时间';
                """))
                
                conn.commit()
                logger.info("documents表创建完成！")
            else:
                logger.info("documents表已存在")
                
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始数据库迁移...")
    
    # 1. 确保表存在
    if not create_documents_table_if_not_exists():
        logger.error("创建表失败")
        sys.exit(1)
    
    # 2. 迁移embedding字段
    if not migrate_embedding_column():
        logger.error("迁移失败")
        sys.exit(1)
    
    logger.info("数据库迁移完成！")
    logger.info("现在可以正常使用嵌入向量功能了。")

if __name__ == "__main__":
    main()
