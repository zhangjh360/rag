"""
配置模块
提供统一配置访问接口
"""

from app.config.settings import (
    OPENAI_API_KEY,
    OPENAI_API_URL,
    DB_URL,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    LOG_DIR,
    LOG_LEVEL,
    LOG_MAX_SIZE,
    LOG_BACKUP_COUNT,
    LOG_ENABLE_CONSOLE,
    LOG_ENABLE_FILE,
    USE_CHUNK_RETRIEVAL,
    EMBEDDING_BACKEND,
    HUGGINGFACE_MODEL,
    EMBEDDING_DEVICE,
    ENABLE_RERANK,
    RERANKER_MODEL,
    RERANKER_MAX_LENGTH,
    RERANKER_BATCH_SIZE,
    RERANKER_DEVICE,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    REDIS_DB,
    CELERY_ENABLED,
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    validate_config,
    get_settings
)


class Settings:
    """Settings类，提供配置属性访问"""

    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.openai_api_url = OPENAI_API_URL
        self.db_url = DB_URL
        self.embedding_model = EMBEDDING_MODEL
        self.chat_model = CHAT_MODEL
        self.log_dir = LOG_DIR
        self.log_level = LOG_LEVEL
        self.log_max_size = LOG_MAX_SIZE
        self.log_backup_count = LOG_BACKUP_COUNT
        self.log_enable_console = LOG_ENABLE_CONSOLE
        self.log_enable_file = LOG_ENABLE_FILE
        self.use_chunk_retrieval = USE_CHUNK_RETRIEVAL
        self.embedding_backend = EMBEDDING_BACKEND
        self.huggingface_model = HUGGINGFACE_MODEL
        self.embedding_device = EMBEDDING_DEVICE
        self.enable_rerank = ENABLE_RERANK
        self.reranker_model = RERANKER_MODEL
        self.reranker_max_length = RERANKER_MAX_LENGTH
        self.reranker_batch_size = RERANKER_BATCH_SIZE
        self.reranker_device = RERANKER_DEVICE
        self.redis_host = REDIS_HOST
        self.redis_port = REDIS_PORT
        self.redis_password = REDIS_PASSWORD
        self.redis_db = REDIS_DB
        self.celery_enabled = CELERY_ENABLED
        self.upload_dir = UPLOAD_DIR
        self.max_upload_size = MAX_UPLOAD_SIZE


# 创建全局配置实例
settings = Settings()