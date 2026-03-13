"""
数据库初始化
从根目录的database.py移动而来，提供更好的模块化结构
"""

from sqlalchemy import create_engine, text
from app.config.settings import DB_URL
from app.models.database import Base, Document, Query
import logging

logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库"""
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Vector extension created successfully")
        except Exception as e:
            logger.error(f"Error creating vector extension: {e}")
        
        try:
            # 为TSVECTOR创建GIN索引，用于全文搜索
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents USING gin (embedding);
            """))
            conn.commit()
            logger.info("TSVECTOR GIN index created successfully")
        except Exception as e:
            logger.error(f"Error creating TSVECTOR index: {e}")

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
