#!/usr/bin/env python3
"""
简化的数据库修复脚本
直接执行SQL命令修复embedding字段类型
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.config.settings import DB_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """修复数据库embedding字段类型"""
    try:
        # 创建数据库连接
        engine = create_engine(DB_URL)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                logger.info("开始修复数据库...")
                
                # 1. 清空embedding字段（因为类型不兼容）
                logger.info("清空现有embedding数据...")
                conn.execute(text("UPDATE documents SET embedding = NULL"))
                
                # 2. 删除旧的embedding列
                logger.info("删除旧的embedding列...")
                conn.execute(text("ALTER TABLE documents DROP COLUMN IF EXISTS embedding"))
                
                # 3. 添加新的embedding列
                logger.info("添加新的embedding列...")
                conn.execute(text("""
                    ALTER TABLE documents 
                    ADD COLUMN embedding REAL[]
                """))
                
                # 提交事务
                trans.commit()
                logger.info("数据库修复完成！")
                
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"修复失败，已回滚: {e}")
                raise
                
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始修复数据库embedding字段类型...")
    
    if not fix_database():
        logger.error("修复失败")
        sys.exit(1)
    
    logger.info("数据库修复完成！")
    logger.info("现在可以正常使用嵌入向量功能了。")

if __name__ == "__main__":
    main()
