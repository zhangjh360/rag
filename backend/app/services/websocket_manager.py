"""
WebSocket 连接管理器
用于实时推送任务进度更新
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 存储所有活跃连接: {task_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # 存储用户的所有订阅: {user_id: Set[task_id]}
        self.user_subscriptions: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, task_id: str, user_id: int = None):
        """
        接受WebSocket连接并订阅指定任务

        Args:
            websocket: WebSocket连接对象
            task_id: 要订阅的任务ID
            user_id: 用户ID(可选,用于权限控制)
        """
        await websocket.accept()

        # 添加到任务订阅者列表
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)

        # 记录用户订阅
        if user_id:
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(task_id)

        logger.info(f"WebSocket连接已建立: task_id={task_id}, user_id={user_id}, "
                   f"当前订阅数={len(self.active_connections[task_id])}")

    def disconnect(self, websocket: WebSocket, task_id: str, user_id: int = None):
        """
        断开WebSocket连接

        Args:
            websocket: WebSocket连接对象
            task_id: 任务ID
            user_id: 用户ID
        """
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)

            # 如果没有订阅者了,删除任务记录
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        # 清理用户订阅记录
        if user_id and user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(task_id)
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]

        logger.info(f"WebSocket连接已断开: task_id={task_id}, user_id={user_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        向单个WebSocket连接发送消息

        Args:
            message: 要发送的消息字典
            websocket: WebSocket连接对象
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        """
        向订阅指定任务的所有连接广播消息

        Args:
            task_id: 任务ID
            message: 要广播的消息字典
        """
        if task_id not in self.active_connections:
            logger.debug(f"任务 {task_id} 没有活跃的WebSocket订阅者")
            return

        # 添加时间戳
        message['timestamp'] = datetime.now().isoformat()

        # 记录要移除的死连接
        dead_connections = set()

        # 向所有订阅者发送消息
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                dead_connections.add(connection)

        # 清理死连接
        for dead_conn in dead_connections:
            self.active_connections[task_id].discard(dead_conn)

        if dead_connections:
            logger.info(f"清理了 {len(dead_connections)} 个死连接")

    async def send_progress_update(
        self,
        task_id: str,
        progress: int,
        status: str,
        current: int = None,
        total: int = None,
        message: str = None,
        details: dict = None
    ):
        """
        发送任务进度更新

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            status: 任务状态
            current: 当前处理数量
            total: 总数量
            message: 进度消息
            details: 额外详情
        """
        update_message = {
            'type': 'progress',
            'task_id': task_id,
            'progress': progress,
            'status': status,
        }

        if current is not None:
            update_message['current'] = current
        if total is not None:
            update_message['total'] = total
        if message:
            update_message['message'] = message
        if details:
            update_message['details'] = details

        await self.broadcast_to_task(task_id, update_message)

    async def send_task_complete(
        self,
        task_id: str,
        success: bool,
        message: str,
        result: dict = None
    ):
        """
        发送任务完成通知

        Args:
            task_id: 任务ID
            success: 是否成功
            message: 完成消息
            result: 任务结果
        """
        complete_message = {
            'type': 'complete',
            'task_id': task_id,
            'success': success,
            'message': message,
            'progress': 100 if success else -1,
        }

        if result:
            complete_message['result'] = result

        await self.broadcast_to_task(task_id, complete_message)

    async def send_task_error(
        self,
        task_id: str,
        error: str,
        error_details: dict = None
    ):
        """
        发送任务错误通知

        Args:
            task_id: 任务ID
            error: 错误消息
            error_details: 错误详情
        """
        error_message = {
            'type': 'error',
            'task_id': task_id,
            'error': error,
            'progress': -1,
        }

        if error_details:
            error_message['details'] = error_details

        await self.broadcast_to_task(task_id, error_message)

    def get_task_subscribers_count(self, task_id: str) -> int:
        """获取任务的订阅者数量"""
        return len(self.active_connections.get(task_id, set()))

    def get_user_subscriptions(self, user_id: int) -> Set[str]:
        """获取用户的所有订阅"""
        return self.user_subscriptions.get(user_id, set())

    def get_all_active_tasks(self) -> list:
        """获取所有有活跃订阅的任务ID"""
        return list(self.active_connections.keys())


# 全局单例
manager = ConnectionManager()
