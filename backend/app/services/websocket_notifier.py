"""
WebSocket通知服务
用于从Celery任务中发送WebSocket消息
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebSocketNotifier:
    """
    WebSocket通知器

    在Celery worker中调用,通过事件循环发送WebSocket消息
    """

    @staticmethod
    def send_progress_update(
        task_id: str,
        progress: int,
        status: str,
        current: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """
        发送任务进度更新

        这个方法可以从同步的Celery任务中调用
        """
        try:
            from app.routers.websocket import task_progress_manager

            # 创建新的事件循环(因为Celery worker可能没有运行的事件循环)
            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 运行异步任务
            loop.run_until_complete(
                task_progress_manager.send_progress_update(
                    task_id=task_id,
                    progress=progress,
                    status=status,
                    current=current,
                    total=total,
                    message=message,
                    details=details
                )
            )

            logger.debug(f"WebSocket进度推送成功: task_id={task_id}, progress={progress}%")

        except Exception as e:
            # WebSocket推送失败不应影响任务执行
            logger.warning(f"WebSocket进度推送失败 (不影响任务执行): {e}")

    @staticmethod
    def send_task_complete(
        task_id: str,
        success: bool,
        message: str,
        result: Optional[dict] = None
    ):
        """发送任务完成通知"""
        try:
            from app.routers.websocket import task_progress_manager

            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(
                task_progress_manager.send_task_complete(
                    task_id=task_id,
                    success=success,
                    message=message,
                    result=result
                )
            )

            logger.info(f"WebSocket完成通知发送成功: task_id={task_id}, success={success}")

        except Exception as e:
            logger.warning(f"WebSocket完成通知发送失败: {e}")

    @staticmethod
    def send_task_error(
        task_id: str,
        error: str,
        error_details: Optional[dict] = None
    ):
        """发送任务错误通知"""
        try:
            from app.routers.websocket import task_progress_manager

            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(
                task_progress_manager.send_task_error(
                    task_id=task_id,
                    error=error,
                    error_details=error_details
                )
            )

            logger.info(f"WebSocket错误通知发送成功: task_id={task_id}")

        except Exception as e:
            logger.warning(f"WebSocket错误通知发送失败: {e}")


# 全局实例
notifier = WebSocketNotifier()
