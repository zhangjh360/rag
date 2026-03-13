"""
文档索引异步任务
使用Celery进行异步处理
"""
from celery import Task
from app.celery_app import celery_app
from app.database.connection import get_db
from app.services.incremental_indexer import create_incremental_indexer
from app.services.websocket_notifier import notifier as ws_notifier
from app.models.database import Document
from app.models.index_record import IndexTask as IndexTaskModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """
    自定义任务基类,提供数据库会话管理
    """
    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = next(get_db())
        return self._db

    def after_return(self, *args, **kwargs):
        """任务完成后关闭数据库连接"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    name='app.tasks.index_tasks.index_document_task',
    base=DatabaseTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def index_document_task(self, doc_id: int, user_id: int = None, force: bool = False):
    """
    异步索引单个文档

    Args:
        doc_id: 文档ID
        user_id: 用户ID
        force: 是否强制重新索引

    Returns:
        索引结果字典
    """
    task_record = None

    try:
        db = self.db

        # 更新任务状态为processing
        task_record = db.query(IndexTaskModel).filter(
            IndexTaskModel.task_id == self.request.id
        ).first()

        if task_record:
            task_record.status = 'processing'
            task_record.started_at = datetime.now()
            db.commit()

        # 获取文档
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise ValueError(f"文档不存在: doc_id={doc_id}")

        logger.info(f"开始索引文档: doc_id={doc_id}, filename={doc.filename}")

        # 更新进度: 10%
        if task_record:
            task_record.progress = 10
            db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': '准备索引'})
        ws_notifier.send_progress_update(
            task_id=self.request.id,
            progress=10,
            status='processing',
            message='准备索引'
        )

        # 创建索引器
        indexer = create_incremental_indexer(db)

        # 更新进度: 20%
        if task_record:
            task_record.progress = 20
            db.commit()
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': '开始处理'})
        ws_notifier.send_progress_update(
            task_id=self.request.id,
            progress=20,
            status='processing',
            message='开始处理'
        )

        # 执行索引
        result = indexer.index_document(doc, user_id=user_id, force=force)

        # 更新进度: 100%
        if task_record:
            task_record.status = 'completed'
            task_record.progress = 100
            task_record.completed_at = datetime.now()
            db.commit()

        # WebSocket 完成通知
        ws_notifier.send_task_complete(
            task_id=self.request.id,
            success=True,
            message='文档索引完成',
            result=result
        )

        logger.info(f"文档索引完成: doc_id={doc_id}, result={result}")
        return result

    except Exception as e:
        error_msg = f"索引失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

        # 更新任务状态为failed
        if task_record:
            task_record.status = 'failed'
            task_record.error_message = str(e)
            task_record.completed_at = datetime.now()
            self.db.commit()

        # WebSocket 错误通知
        ws_notifier.send_task_error(
            task_id=self.request.id,
            error=str(e),
            error_details={'traceback': traceback.format_exc()}
        )

        # 重试
        if self.request.retries < self.max_retries:
            logger.info(f"准备重试 (第{self.request.retries + 1}次): doc_id={doc_id}")
            raise self.retry(exc=e)
        else:
            logger.error(f"达到最大重试次数,任务失败: doc_id={doc_id}")
            return {'status': 'error', 'error': str(e)}


@celery_app.task(
    name='app.tasks.index_tasks.batch_index_task',
    base=DatabaseTask,
    bind=True
)
def batch_index_task(self, doc_ids: list, user_id: int = None):
    """
    异步批量索引文档

    Args:
        doc_ids: 文档ID列表
        user_id: 用户ID

    Returns:
        批量索引结果
    """
    task_record = None

    try:
        db = self.db

        # 更新任务状态
        task_record = db.query(IndexTaskModel).filter(
            IndexTaskModel.task_id == self.request.id
        ).first()

        if task_record:
            task_record.status = 'processing'
            task_record.started_at = datetime.now()
            db.commit()

        logger.info(f"开始批量索引: 共{len(doc_ids)}个文档")

        # 创建索引器
        indexer = create_incremental_indexer(db)

        # 批量索引with进度回调
        def progress_callback(current, total):
            progress = int((current / total) * 100)
            logger.info(f"批量索引进度: {current}/{total} ({progress}%)")

            if task_record:
                task_record.progress = progress
                db.commit()

            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'current': current,
                    'total': total,
                    'status': f'处理中 {current}/{total}'
                }
            )

            # WebSocket 进度推送
            ws_notifier.send_progress_update(
                task_id=self.request.id,
                progress=progress,
                status='processing',
                current=current,
                total=total,
                message=f'处理中 {current}/{total}'
            )

        result = indexer.batch_index_documents(
            doc_ids,
            user_id=user_id,
            progress_callback=progress_callback
        )

        # 更新任务状态为completed
        if task_record:
            task_record.status = 'completed'
            task_record.progress = 100
            task_record.completed_at = datetime.now()
            db.commit()

        # WebSocket 完成通知
        ws_notifier.send_task_complete(
            task_id=self.request.id,
            success=True,
            message='批量索引完成',
            result=result
        )

        logger.info(f"批量索引完成: {result}")
        return result

    except Exception as e:
        error_msg = f"批量索引失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

        if task_record:
            task_record.status = 'failed'
            task_record.error_message = str(e)
            task_record.completed_at = datetime.now()
            self.db.commit()

        # WebSocket 错误通知
        ws_notifier.send_task_error(
            task_id=self.request.id,
            error=str(e),
            error_details={'traceback': traceback.format_exc()}
        )

        return {'status': 'error', 'error': str(e)}


@celery_app.task(
    name='app.tasks.index_tasks.delete_index_task',
    base=DatabaseTask,
    bind=True
)
def delete_index_task(self, doc_id: int):
    """
    异步删除文档索引

    Args:
        doc_id: 文档ID

    Returns:
        删除结果
    """
    try:
        db = self.db
        logger.info(f"开始删除索引: doc_id={doc_id}")

        # 创建索引器
        indexer = create_incremental_indexer(db)

        # 执行删除
        result = indexer.delete_document_index(doc_id)

        logger.info(f"索引删除完成: doc_id={doc_id}, result={result}")
        return result

    except Exception as e:
        error_msg = f"删除索引失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {'status': 'error', 'error': str(e)}
