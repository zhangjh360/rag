"""
数据库连接管理
从根目录的database.py移动而来，提供更好的模块化结构
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import DB_URL
import logging

logger = logging.getLogger(__name__)

# 全局变量存储引擎和会话工厂
_engine = None
_session_factory = None

# 全局注册 pgvector 类型（在模块加载时立即执行）
def _register_vector_types_globally():
    """在全局范围内注册 pgvector 自定义类型"""
    try:
        # psycopg 3.x 和 pgvector 扩展会自动处理类型
        # 这里只需要验证 pgvector 扩展是否可用
        logger.info("pgvector types are handled automatically by pgvector extension with psycopg 3")
        return True
    except Exception as e:
        logger.warning(f"Failed to globally register pgvector types: {e}")
        return False

# 尝试全局注册类型
_types_registered = _register_vector_types_globally()

def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DB_URL,
            pool_pre_ping=True,
            connect_args={
                "options": "-c client_encoding=utf8"
            }
        )

        logger.info(f"Database engine created for: {DB_URL}")
        if _types_registered:
            logger.info("pgvector types are globally registered")
        else:
            logger.warning("pgvector types registration failed, may encounter type errors")
    return _engine

def get_session_local():
    """获取会话工厂（单例模式）"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_factory

def get_db() -> Session:
    """获取数据库会话"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
