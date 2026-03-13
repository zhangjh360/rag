"""
创建Chat相关的数据库表
"""
import os
from sqlalchemy import create_engine
from app.models.chat import Base
from app.config.settings import get_settings

settings = get_settings()

def create_chat_tables():
    """创建Chat相关表"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings["db_url"])

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        print("✅ Chat tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating chat tables: {e}")
        return False

if __name__ == "__main__":
    create_chat_tables()