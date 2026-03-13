"""
Celery应用实例
用于异步任务处理
"""
from celery import Celery
from app.config.celery_config import CELERY_CONFIG
import logging

logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery('rag_indexing')

# 加载配置
celery_app.config_from_object(CELERY_CONFIG)

# 自动发现任务
celery_app.autodiscover_tasks(['app.tasks'])

logger.info("Celery应用已初始化")


# 任务示例(用于测试)
@celery_app.task(name='app.tasks.test_task')
def test_task(x, y):
    """测试任务"""
    return x + y


if __name__ == '__main__':
    celery_app.start()
