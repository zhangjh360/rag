"""
WebSocket 路由
提供实时数据推送功能
"""
import json
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.middleware.auth import get_current_user_websocket
from app.models.database import User
from app.models.index_record import IndexTask as IndexTaskModel

router = APIRouter()
logger = logging.getLogger(__name__)

# 存储活跃的WebSocket连接
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[WebSocket, str] = {}  # WebSocket -> user_id

    async def connect(self, websocket: WebSocket, user_id: str, endpoint: str):
        await websocket.accept()

        if endpoint not in self.active_connections:
            self.active_connections[endpoint] = []

        self.active_connections[endpoint].append(websocket)
        self.user_connections[websocket] = user_id

        logger.info(f"用户 {user_id} 连接到 WebSocket 端点: {endpoint}")
        logger.info(f"当前活跃连接数: {len(self.active_connections.get(endpoint, []))}")

    def disconnect(self, websocket: WebSocket, endpoint: str):
        if endpoint in self.active_connections:
            self.active_connections[endpoint].remove(websocket)

        user_id = self.user_connections.pop(websocket, None)

        logger.info(f"用户 {user_id} 断开 WebSocket 连接: {endpoint}")
        logger.info(f"当前活跃连接数: {len(self.active_connections.get(endpoint, []))}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")

    async def broadcast(self, message: dict, endpoint: str):
        if endpoint not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[endpoint]:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection, endpoint)

    async def broadcast_to_user(self, message: dict, user_id: str, endpoint: str):
        if endpoint not in self.active_connections:
            return

        for connection in self.active_connections[endpoint]:
            if self.user_connections.get(connection) == user_id:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"向用户 {user_id} 发送消息失败: {e}")
                    self.disconnect(connection, endpoint)

manager = ConnectionManager()

# 任务进度推送专用管理器
class TaskProgressManager:
    """任务进度 WebSocket 管理器"""

    def __init__(self):
        # 存储所有活跃连接: {task_id: Set[WebSocket]}
        self.task_connections: Dict[str, List[WebSocket]] = {}
        # 存储用户订阅: {user_id: Set[task_id]}
        self.user_subscriptions: Dict[int, set] = {}

    async def connect(self, websocket: WebSocket, task_id: str, user_id: int = None):
        """连接到任务进度推送"""
        await websocket.accept()

        if task_id not in self.task_connections:
            self.task_connections[task_id] = []
        self.task_connections[task_id].append(websocket)

        if user_id:
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(task_id)

        logger.info(f"任务进度 WebSocket 连接: task_id={task_id}, user_id={user_id}, "
                   f"订阅数={len(self.task_connections[task_id])}")

    def disconnect(self, websocket: WebSocket, task_id: str, user_id: int = None):
        """断开连接"""
        if task_id in self.task_connections:
            if websocket in self.task_connections[task_id]:
                self.task_connections[task_id].remove(websocket)

            if not self.task_connections[task_id]:
                del self.task_connections[task_id]

        if user_id and user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(task_id)
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]

        logger.info(f"任务进度 WebSocket 断开: task_id={task_id}, user_id={user_id}")

    async def send_to_websocket(self, websocket: WebSocket, message: dict):
        """发送消息到单个 WebSocket"""
        try:
            message['timestamp'] = datetime.now().isoformat()
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送 WebSocket 消息失败: {e}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        """广播到订阅指定任务的所有连接"""
        if task_id not in self.task_connections:
            logger.debug(f"任务 {task_id} 没有活跃订阅")
            return

        message['timestamp'] = datetime.now().isoformat()
        dead_connections = []

        for connection in self.task_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                dead_connections.append(connection)

        # 清理死连接
        for dead_conn in dead_connections:
            if dead_conn in self.task_connections[task_id]:
                self.task_connections[task_id].remove(dead_conn)

        if dead_connections:
            logger.info(f"清理了 {len(dead_connections)} 个死连接")

    async def send_progress_update(self, task_id: str, progress: int, status: str,
                                   current: int = None, total: int = None,
                                   message: str = None, details: dict = None):
        """发送任务进度更新"""
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

    async def send_task_complete(self, task_id: str, success: bool, message: str, result: dict = None):
        """发送任务完成通知"""
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

    async def send_task_error(self, task_id: str, error: str, error_details: dict = None):
        """发送任务错误通知"""
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
        """获取任务订阅者数量"""
        return len(self.task_connections.get(task_id, []))

    def get_all_active_tasks(self) -> List[str]:
        """获取所有有活跃订阅的任务ID"""
        return list(self.task_connections.keys())

# 全局任务进度管理器
task_progress_manager = TaskProgressManager()

@router.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    Dashboard 实时数据推送 WebSocket
    """
    # 认证用户
    try:
        # 从查询参数或头部获取token
        token = None
        if "authorization" in websocket.headers:
            token = websocket.headers["authorization"].replace("Bearer ", "")
        elif "token" in websocket.query_params:
            token = websocket.query_params["token"]

        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return

        # 验证token并获取用户
        current_user = await get_current_user_websocket(token, db)
        user_id = str(current_user.id)

    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect(websocket, user_id, "dashboard")

    try:
        # 发送初始连接成功消息
        await manager.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        }, websocket)

        # 保持连接并处理消息
        while True:
            try:
                # 接收客户端消息（如果有）
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理客户端发送的消息
                await handle_client_message(message, websocket, user_id, db)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"处理WebSocket消息时出错: {e}")
                # 发送错误消息但不关闭连接
                await manager.send_personal_message({
                    "type": "error",
                    "message": "处理消息时出错",
                    "timestamp": datetime.now().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "dashboard")

async def handle_client_message(message: dict, websocket: WebSocket, user_id: str, db: Session):
    """
    处理客户端发送的WebSocket消息
    """
    message_type = message.get("type")

    if message_type == "ping":
        # 心跳检测
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif message_type == "subscribe_stats":
        # 订阅统计数据更新
        await manager.send_personal_message({
            "type": "subscription_confirmed",
            "subscription": "stats_update",
            "timestamp": datetime.now().isoformat()
        }, websocket)

    elif message_type == "get_stats":
        # 获取当前统计数据
        from app.routers.dashboard import get_dashboard_stats
        try:
            # 这里需要手动创建用户依赖
            from app.models.database import User
            current_user = db.query(User).filter(User.id == int(user_id)).first()
            if not current_user:
                raise HTTPException(status_code=404, detail="用户不存在")

            stats = await get_dashboard_stats(db, current_user)

            await manager.send_personal_message({
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            }, websocket)

        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            await manager.send_personal_message({
                "type": "error",
                "message": "获取统计数据失败",
                "timestamp": datetime.now().isoformat()
            }, websocket)

# 以下函数可以被其他地方调用来推送实时数据
async def broadcast_stats_update(stats_data: dict):
    """
    广播统计数据更新到所有连接的dashboard客户端
    """
    await manager.broadcast({
        "type": "stats_update",
        "data": stats_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_document_uploaded(document_data: dict):
    """
    广播文档上传通知
    """
    await manager.broadcast({
        "type": "document_uploaded",
        "data": document_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_new_query(query_data: dict):
    """
    广播新查询通知
    """
    await manager.broadcast({
        "type": "new_query",
        "data": query_data,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

async def broadcast_system_notification(notification: dict):
    """
    广播系统通知
    """
    await manager.broadcast({
        "type": "system_notification",
        "data": notification,
        "timestamp": datetime.now().isoformat()
    }, "dashboard")

@router.websocket("/ws/task/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(..., description="JWT认证token"),
    db: Session = Depends(get_db)
):
    """
    任务进度实时推送 WebSocket

    客户端连接示例:
    ```javascript
    const ws = new WebSocket('ws://localhost:8800/ws/task/YOUR_TASK_ID?token=YOUR_JWT_TOKEN');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress update:', data);

        switch(data.type) {
            case 'connected':
                console.log('WebSocket connected');
                break;
            case 'progress':
                // 更新进度条
                updateProgressBar(data.progress);
                console.log(`Progress: ${data.progress}%`);
                break;
            case 'complete':
                // 任务完成
                console.log('Task completed:', data);
                break;
            case 'error':
                // 任务失败
                console.error('Task error:', data);
                break;
        }
    };

    ws.onclose = () => console.log('WebSocket closed');
    ws.onerror = (error) => console.error('WebSocket error:', error);

    // 发送心跳
    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
        }
    }, 30000);
    ```

    消息格式:
    - 连接成功: {"type": "connected", "task_id": "xxx", "current_status": "processing", ...}
    - 进度更新: {"type": "progress", "task_id": "xxx", "progress": 50, "status": "processing", ...}
    - 任务完成: {"type": "complete", "task_id": "xxx", "success": true, "result": {...}}
    - 任务错误: {"type": "error", "task_id": "xxx", "error": "错误信息"}
    """
    user_id = None

    try:
        # 验证JWT token
        try:
            current_user = await get_current_user_websocket(token, db)
            user_id = current_user.id
        except Exception as e:
            logger.error(f"WebSocket认证失败: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return

        # 验证任务是否存在
        task = db.query(IndexTaskModel).filter(
            IndexTaskModel.task_id == task_id
        ).first()

        if not task:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
            return

        # 建立连接
        await task_progress_manager.connect(websocket, task_id, user_id)

        # 发送初始状态
        initial_message = {
            'type': 'connected',
            'task_id': task_id,
            'message': f'已连接到任务 {task_id} 的进度推送',
            'current_status': task.status,
            'current_progress': task.progress or 0,
        }
        await task_progress_manager.send_to_websocket(websocket, initial_message)

        # 如果任务已完成,发送完成消息
        if task.status in ['completed', 'failed']:
            completion_message = {
                'type': 'complete',
                'task_id': task_id,
                'success': task.status == 'completed',
                'message': f'任务已{task.status}',
                'progress': 100 if task.status == 'completed' else -1,
            }
            await task_progress_manager.send_to_websocket(websocket, completion_message)

        # 保持连接
        while True:
            try:
                data = await websocket.receive_text()

                # 处理心跳
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket接收消息错误: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端主动断开: task_id={task_id}, user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}", exc_info=True)
    finally:
        task_progress_manager.disconnect(websocket, task_id, user_id)


# 导出manager供其他模块使用
__all__ = [
    "manager",
    "task_progress_manager",
    "broadcast_stats_update",
    "broadcast_document_uploaded",
    "broadcast_new_query",
    "broadcast_system_notification"
]