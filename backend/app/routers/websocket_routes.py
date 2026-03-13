"""
WebSocket路由
用于实时推送任务进度
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.index_record import IndexTask as IndexTaskModel
from app.services.websocket_manager import manager
from app.models.database import User
from app.middleware.auth import get_current_user_websocket, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/task/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(..., description="JWT认证token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket端点: 订阅任务进度更新

    客户端连接示例:
    ```javascript
    const ws = new WebSocket('ws://localhost:8800/ws/task/YOUR_TASK_ID?token=YOUR_JWT_TOKEN');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress update:', data);

        switch(data.type) {
            case 'progress':
                // 更新进度条
                updateProgressBar(data.progress);
                break;
            case 'complete':
                // 任务完成
                onTaskComplete(data);
                break;
            case 'error':
                // 任务失败
                onTaskError(data);
                break;
        }
    };
    ```

    消息格式:
    - 进度更新: {"type": "progress", "task_id": "xxx", "progress": 50, "status": "processing", ...}
    - 任务完成: {"type": "complete", "task_id": "xxx", "success": true, "result": {...}}
    - 任务错误: {"type": "error", "task_id": "xxx", "error": "错误信息"}
    """
    user_id = None

    try:
        # 验证JWT token (WebSocket专用)
        try:
            current_user = await get_current_user_websocket(token, db)
            user_id = current_user.id
        except Exception as e:
            logger.error(f"WebSocket认证失败: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
            return

        # 验证任务是否存在且用户有权限访问
        task = db.query(IndexTaskModel).filter(
            IndexTaskModel.task_id == task_id
        ).first()

        if not task:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
            return

        # TODO: 可以在这里添加更细粒度的权限检查
        # 例如: 只有任务创建者或管理员可以订阅

        # 建立连接
        await manager.connect(websocket, task_id, user_id)

        # 发送初始状态
        initial_message = {
            'type': 'connected',
            'task_id': task_id,
            'message': f'已连接到任务 {task_id} 的进度推送',
            'current_status': task.status,
            'current_progress': task.progress or 0,
        }
        await manager.send_personal_message(initial_message, websocket)

        # 如果任务已经完成,发送完成消息
        if task.status in ['completed', 'failed']:
            completion_message = {
                'type': 'complete',
                'task_id': task_id,
                'success': task.status == 'completed',
                'message': f'任务已{task.status}',
                'progress': 100 if task.status == 'completed' else -1,
            }
            await manager.send_personal_message(completion_message, websocket)

        # 保持连接,等待断开
        while True:
            # 接收客户端消息(如果有的话)
            data = await websocket.receive_text()

            # 可以处理客户端发送的消息
            # 例如: ping/pong, 取消任务等
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket客户端主动断开: task_id={task_id}, user_id={user_id}")
        manager.disconnect(websocket, task_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}", exc_info=True)
        manager.disconnect(websocket, task_id, user_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except:
            pass


@router.get("/active-connections")
async def get_active_connections(current_user: User = Depends(get_current_user)):
    """
    获取所有活跃的WebSocket连接信息
    (仅管理员可访问)
    """
    # TODO: 添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理员权限")

    active_tasks = manager.get_all_active_tasks()
    connections_info = []

    for task_id in active_tasks:
        connections_info.append({
            'task_id': task_id,
            'subscribers_count': manager.get_task_subscribers_count(task_id)
        })

    return {
        'success': True,
        'data': {
            'total_active_tasks': len(active_tasks),
            'connections': connections_info
        }
    }
