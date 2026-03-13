"""
应用配置设置
从根目录的config.py移动而来，提供更好的模块化结构
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 获取当前文件所在目录
current_dir = Path(__file__).parent.parent.parent

# 加载.env文件
env_file = current_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    # 如果.env文件不存在，尝试从上级目录加载
    parent_env = current_dir.parent / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
    else:
        print(f"警告: 未找到.env文件，使用系统环境变量")

# 环境变量配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")

# 数据库URL - 使用 psycopg3 驱动
_DB_URL = os.getenv("DB_URL", "postgresql://postgres:admin!postgres123@localhost:5432/ragdb")
# 确保使用 psycopg 驱动而不是 psycopg2
if "+psycopg" not in _DB_URL:
    # 将 postgres:// 替换为 postgresql+psycopg://
    DB_URL = _DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DB_URL = _DB_URL

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
CHAT_MODEL = os.getenv("CHAT_MODEL", "glm-4")

# 日志配置
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
LOG_ENABLE_CONSOLE = os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
LOG_ENABLE_FILE = os.getenv("LOG_ENABLE_FILE", "true").lower() == "true"

# 检索配置
USE_CHUNK_RETRIEVAL = os.getenv("USE_CHUNK_RETRIEVAL", "false").lower() == "true"
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "openai")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "auto")

# Rerank 配置
ENABLE_RERANK = os.getenv("ENABLE_RERANK", "true").lower() == "true"
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANKER_MAX_LENGTH = int(os.getenv("RERANKER_MAX_LENGTH", "512"))
RERANKER_BATCH_SIZE = int(os.getenv("RERANKER_BATCH_SIZE", "32"))
RERANKER_DEVICE = os.getenv("RERANKER_DEVICE", "auto")  # auto, cpu, cuda

# Redis配置 (用于Celery)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "admin!redis123")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Celery配置
CELERY_ENABLED = os.getenv("CELERY_ENABLED", "true").lower() == "true"

# 文件上传配置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(current_dir, "uploads"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5MB

# 服务器配置（用于构建图片完整URL）
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")


#链路追踪配置
TRACING_ENABLED = os.getenv("TRACING_ENABLED", "false").lower() == "true"
TRACING_SERVICE_NAME = os.getenv("TRACING_SERVICE_NAME", "rag-backend")
TRACING_OTEL_ENDPOINT = os.getenv("TRACING_OTEL_ENDPOINT", "http://localhost:4317")
TRACING_API_KEY = os.getenv("TRACING_API_KEY", "")


# 验证必要的环境变量
def validate_config():
    """验证配置是否完整"""
    missing_vars = []
    
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    if not OPENAI_API_URL:
        missing_vars.append("OPENAI_API_URL")
    
    if missing_vars:
        print(f"警告: 缺少必要的环境变量: {', '.join(missing_vars)}")
        return False
    
    print("配置验证通过")
    return True

# 在导入时验证配置
if __name__ == "__main__":
    validate_config()
else:
    # 只在非测试环境下验证
    if not os.getenv("SKIP_CONFIG_VALIDATION"):
        validate_config()

def get_settings():
    """获取所有设置"""
    return {
        "openai_api_key": OPENAI_API_KEY,
        "openai_api_url": OPENAI_API_URL,
        "db_url": DB_URL,
        "embedding_model": EMBEDDING_MODEL,
        "chat_model": CHAT_MODEL,
        "log_dir": LOG_DIR,
        "log_level": LOG_LEVEL,
        "use_chunk_retrieval": USE_CHUNK_RETRIEVAL,
        "embedding_backend": EMBEDDING_BACKEND,
        "huggingface_model": HUGGINGFACE_MODEL,
        "embedding_device": EMBEDDING_DEVICE,
        "upload_dir": UPLOAD_DIR,
        "max_upload_size": MAX_UPLOAD_SIZE
    }
