"""
Celery配置
用于异步任务队列
"""
import os

# 直接从环境变量读取配置,避免循环导入
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "admin!redis123")

# Celery Broker配置
if REDIS_PASSWORD:
    CELERY_BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Celery配置
CELERY_CONFIG = {
    'broker_url': CELERY_BROKER_URL,
    'result_backend': CELERY_RESULT_BACKEND,
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30分钟硬限制
    'task_soft_time_limit': 25 * 60,  # 25分钟软限制
    'worker_prefetch_multiplier': 1,  # 每次只取一个任务
    'worker_max_tasks_per_child': 1000,  # Worker重启前最多执行1000个任务
    'task_acks_late': True,  # 任务完成后才确认
    'task_reject_on_worker_lost': True,  # Worker丢失时拒绝任务
    'task_default_queue': 'indexing',  # 默认队列
    'task_default_exchange': 'indexing',
    'task_default_routing_key': 'index.default',
    'task_routes': {
        'app.tasks.index_tasks.index_document_task': {
            'queue': 'indexing',
            'routing_key': 'index.document',
        },
        'app.tasks.index_tasks.batch_index_task': {
            'queue': 'indexing',
            'routing_key': 'index.batch',
        },
        'app.tasks.index_tasks.delete_index_task': {
            'queue': 'indexing',
            'routing_key': 'index.delete',
        },
    },
}

# 队列定义
CELERY_QUEUES = {
    'indexing': {
        'exchange': 'indexing',
        'routing_key': 'index.#',
    },
}
