"""
Celery任务模块
"""
from app.tasks.index_tasks import (
    index_document_task,
    batch_index_task,
    delete_index_task
)

__all__ = [
    'index_document_task',
    'batch_index_task',
    'delete_index_task'
]
