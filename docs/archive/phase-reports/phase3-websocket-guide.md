# Phase 3: WebSocket 实时进度推送集成指南

**版本**: Phase 3
**日期**: 2025-01-22
**状态**: ✅ 开发完成

---

## 📖 概述

Phase 3 在 Phase 2 的基础上,集成了 WebSocket 实时进度推送功能,实现真正的实时任务状态监控。主要特性包括:

- ✅ WebSocket 实时进度推送
- ✅ 任务状态实时更新
- ✅ 多客户端并发订阅
- ✅ 自动连接管理
- ✅ 心跳保活机制
- ✅ 完善的错误处理

---

## 🏗️ 架构设计

```
┌──────────────┐
│  前端客户端   │
│  (Browser)   │
└──────┬───────┘
       │
       │ WebSocket连接
       ▼
┌──────────────────────────────────┐
│  FastAPI WebSocket Endpoint      │
│  /ws/task/{task_id}             │
└──────────┬───────────────────────┘
           │
           │ 认证 & 订阅管理
           ▼
┌──────────────────────────────────┐
│  TaskProgressManager             │
│  (WebSocket连接管理器)           │
└──────────┬───────────────────────┘
           │
           │ 消息广播
           ▼
    ┌─────────────┐
    │ WebSocket 1 │
    │ WebSocket 2 │
    │ WebSocket 3 │
    └─────────────┘

┌──────────────┐      进度推送      ┌──────────────┐
│ Celery       │─────────────────>│ WebSocket    │
│ Worker       │   WebSocketNotifier │ Notifier     │
│ (后台进程)    │                    │              │
└──────────────┘                    └──────┬───────┘
       │                                   │
       │ 执行索引                           │ 事件循环
       ▼                                   ▼
┌──────────────┐                    ┌──────────────┐
│Incremental   │                    │TaskProgress  │
│Indexer       │                    │Manager       │
└──────────────┘                    └──────────────┘
```

---

## 📦 核心组件

### 1. WebSocket 端点

**位置**: `app/routers/websocket.py`

#### 端点: `/ws/task/{task_id}`

**功能**: 订阅指定任务的实时进度更新

**连接流程**:
1. 客户端建立 WebSocket 连接
2. 通过 JWT token 进行认证
3. 验证任务是否存在和权限
4. 注册到任务进度管理器
5. 发送初始状态
6. 保持连接,接收实时更新
7. 处理心跳和断开连接

### 2. 任务进度管理器

**类**: `TaskProgressManager`
**位置**: `app/routers/websocket.py`

**核心方法**:
- `connect()`: 建立 WebSocket 连接
- `disconnect()`: 断开连接
- `broadcast_to_task()`: 向任务的所有订阅者广播消息
- `send_progress_update()`: 发送进度更新
- `send_task_complete()`: 发送任务完成通知
- `send_task_error()`: 发送任务错误通知

### 3. WebSocket 通知器

**类**: `WebSocketNotifier`
**位置**: `app/services/websocket_notifier.py`

**功能**: 从同步的 Celery 任务中发送 WebSocket 消息

**核心方法**:
- `send_progress_update()`: 发送进度更新(同步调用)
- `send_task_complete()`: 发送完成通知
- `send_task_error()`: 发送错误通知

**实现原理**:
- 在 Celery worker 中创建新的事件循环
- 运行异步 WebSocket 推送任务
- 错误不影响主任务执行

---

## 🚀 客户端使用示例

### JavaScript/TypeScript

```javascript
// 建立 WebSocket 连接
const token = 'YOUR_JWT_TOKEN';
const taskId = 'task-uuid-here';
const ws = new WebSocket(`ws://localhost:8800/ws/task/${taskId}?token=${token}`);

// 连接成功
ws.onopen = () => {
    console.log('WebSocket connected');
};

// 接收消息
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);

    switch(data.type) {
        case 'connected':
            // 连接建立成功
            console.log(`Connected to task ${data.task_id}`);
            console.log(`Current status: ${data.current_status}`);
            console.log(`Current progress: ${data.current_progress}%`);
            break;

        case 'progress':
            // 进度更新
            updateProgressBar(data.progress);
            console.log(`Progress: ${data.current}/${data.total} (${data.progress}%)`);
            console.log(`Message: ${data.message}`);
            break;

        case 'complete':
            // 任务完成
            console.log('Task completed!');
            console.log('Result:', data.result);
            if (data.success) {
                showSuccess(data.message);
            }
            ws.close();
            break;

        case 'error':
            // 任务错误
            console.error('Task error:', data.error);
            showError(data.error);
            ws.close();
            break;

        case 'pong':
            // 心跳响应
            console.log('Heartbeat OK');
            break;
    }
};

// 连接关闭
ws.onclose = () => {
    console.log('WebSocket closed');
};

// 连接错误
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

// 发送心跳(每30秒)
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);

// UI更新函数
function updateProgressBar(progress) {
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;
}

function showSuccess(message) {
    alert(`Success: ${message}`);
}

function showError(message) {
    alert(`Error: ${message}`);
}
```

### Python 客户端示例

```python
import asyncio
import websockets
import json

async def subscribe_task_progress(task_id: str, token: str):
    """订阅任务进度"""
    uri = f"ws://localhost:8800/ws/task/{task_id}?token={token}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to task {task_id}")

        # 接收消息
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

            msg_type = data.get('type')

            if msg_type == 'connected':
                print(f"Initial status: {data['current_status']}")
                print(f"Initial progress: {data['current_progress']}%")

            elif msg_type == 'progress':
                progress = data['progress']
                current = data.get('current')
                total = data.get('total')
                message = data.get('message', '')

                print(f"Progress: {progress}%")
                if current and total:
                    print(f"  {current}/{total}")
                if message:
                    print(f"  {message}")

            elif msg_type == 'complete':
                print("Task completed!")
                print(f"Success: {data['success']}")
                print(f"Message: {data['message']}")
                if 'result' in data:
                    print(f"Result: {data['result']}")
                break

            elif msg_type == 'error':
                print(f"Task error: {data['error']}")
                break

# 使用示例
token = "your_jwt_token_here"
task_id = "task-uuid-here"

asyncio.run(subscribe_task_progress(task_id, token))
```

---

## 📊 消息格式

### 1. 连接成功消息

```json
{
  "type": "connected",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "已连接到任务 xxx 的进度推送",
  "current_status": "processing",
  "current_progress": 30,
  "timestamp": "2025-01-22T10:00:00.123456"
}
```

### 2. 进度更新消息

```json
{
  "type": "progress",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": 60,
  "status": "processing",
  "current": 3,
  "total": 5,
  "message": "处理中 3/5",
  "timestamp": "2025-01-22T10:01:30.123456"
}
```

### 3. 任务完成消息

```json
{
  "type": "complete",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "message": "批量索引完成",
  "progress": 100,
  "result": {
    "total": 5,
    "success": 5,
    "failed": 0,
    "details": [...]
  },
  "timestamp": "2025-01-22T10:02:00.123456"
}
```

### 4. 任务错误消息

```json
{
  "type": "error",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "error": "索引失败: 数据库连接错误",
  "progress": -1,
  "details": {
    "traceback": "..."
  },
  "timestamp": "2025-01-22T10:01:45.123456"
}
```

### 5. 心跳响应消息

```json
{
  "type": "pong",
  "timestamp": "2025-01-22T10:02:00.123456"
}
```

---

## 🔧 技术实现细节

### 1. 事件循环管理

Celery worker 是同步进程,需要创建事件循环来发送 WebSocket 消息:

```python
def send_progress_update(...):
    try:
        from app.routers.websocket import task_progress_manager

        # 创建事件循环
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
            task_progress_manager.send_progress_update(...)
        )

    except Exception as e:
        # WebSocket推送失败不影响任务执行
        logger.warning(f"WebSocket推送失败: {e}")
```

### 2. 连接管理

使用字典管理 WebSocket 连接:

```python
class TaskProgressManager:
    def __init__(self):
        # 任务ID -> WebSocket列表
        self.task_connections: Dict[str, List[WebSocket]] = {}
        # 用户ID -> 订阅的任务ID集合
        self.user_subscriptions: Dict[int, set] = {}
```

### 3. 死连接清理

广播时自动清理失效的连接:

```python
async def broadcast_to_task(self, task_id: str, message: dict):
    dead_connections = []

    for connection in self.task_connections[task_id]:
        try:
            await connection.send_json(message)
        except Exception as e:
            dead_connections.append(connection)

    # 清理死连接
    for dead_conn in dead_connections:
        self.task_connections[task_id].remove(dead_conn)
```

---

## 🔒 安全考虑

### 1. JWT 认证

所有 WebSocket 连接需要提供有效的 JWT token:

```python
current_user = await get_current_user_websocket(token, db)
```

### 2. 任务权限验证

检查用户是否有权访问指定任务:

```python
task = db.query(IndexTaskModel).filter(
    IndexTaskModel.task_id == task_id
).first()

if not task:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Task not found")
    return
```

### 3. 错误隔离

WebSocket 推送失败不影响任务执行:

```python
try:
    ws_notifier.send_progress_update(...)
except Exception as e:
    logger.warning(f"WebSocket推送失败(不影响任务): {e}")
```

---

## 📈 性能优化

### 1. 批量推送

进度更新在批量索引时按合理频率推送,避免过于频繁:

```python
# 批量索引回调,每处理一个文档推送一次
def progress_callback(current, total):
    progress = int((current / total) * 100)
    ws_notifier.send_progress_update(
        task_id=self.request.id,
        progress=progress,
        current=current,
        total=total,
        message=f'处理中 {current}/{total}'
    )
```

### 2. 连接复用

多个客户端可以订阅同一个任务:

```python
if task_id not in self.task_connections:
    self.task_connections[task_id] = []
self.task_connections[task_id].append(websocket)
```

### 3. 自动清理

任务完成后,订阅者自动断开:

```python
if task.status in ['completed', 'failed']:
    # 发送完成消息
    await task_progress_manager.send_to_websocket(websocket, completion_message)
    # 客户端可选择关闭连接
```

---

## ⚠️ 故障排查

### 问题1: WebSocket 连接失败

**错误**: `Authentication failed`

**解决方案**:
1. 检查 JWT token 是否有效
2. 确认 token 格式: `?token=YOUR_JWT_TOKEN`
3. 检查 token 是否过期

### 问题2: 收不到进度更新

**原因**: Worker 未运行或未集成 WebSocket 推送

**解决方案**:
1. 启动 Celery worker: `./start_celery_worker.sh`
2. 确认 `websocket_notifier` 已导入到任务文件
3. 检查日志中是否有 WebSocket 推送失败的警告

### 问题3: 连接频繁断开

**原因**: 网络不稳定或缺少心跳

**解决方案**:
```javascript
// 添加心跳机制
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);

// 添加重连机制
ws.onclose = () => {
    console.log('Connection closed, reconnecting...');
    setTimeout(() => {
        reconnect();
    }, 3000);
};
```

---

## 🎯 最佳实践

### 1. 错误处理

```javascript
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // 显示用户友好的错误消息
    showNotification('连接失败,请刷新页面重试', 'error');
};
```

### 2. 超时处理

```javascript
// 设置连接超时
const connectionTimeout = setTimeout(() => {
    if (ws.readyState !== WebSocket.OPEN) {
        ws.close();
        showNotification('连接超时', 'error');
    }
}, 10000);

ws.onopen = () => {
    clearTimeout(connectionTimeout);
};
```

### 3. 状态管理

```javascript
// 使用状态机管理连接状态
const CONNECTION_STATES = {
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    DISCONNECTED: 'disconnected',
    ERROR: 'error'
};

let connectionState = CONNECTION_STATES.CONNECTING;

ws.onopen = () => {
    connectionState = CONNECTION_STATES.CONNECTED;
    updateUI();
};

ws.onclose = () => {
    connectionState = CONNECTION_STATES.DISCONNECTED;
    updateUI();
};
```

---

## 📞 API 参考

### WebSocket 端点

**URL**: `/ws/task/{task_id}`
**协议**: WebSocket
**认证**: JWT token (通过查询参数)

**参数**:
- `task_id` (path): 任务 UUID
- `token` (query): JWT 认证 token

**连接示例**:
```
ws://localhost:8800/ws/task/550e8400-e29b-41d4-a716-446655440000?token=eyJhbG...
```

---

## 📝 下一步 (Phase 4 规划)

- [ ] 前端监控 Dashboard
- [ ] 任务历史记录查看
- [ ] 批量任务管理
- [ ] 任务取消功能
- [ ] 定时任务调度
- [ ] 任务依赖链

---

**版本**: Phase 3
**作者**: Claude Code
**日期**: 2025-01-22
**状态**: ✅ 开发完成,可投入生产使用
