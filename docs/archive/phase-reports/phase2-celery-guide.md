# Phase 2: Celery异步任务队列集成指南

**版本**: Phase 2
**日期**: 2025-01-22
**状态**: ✅ 开发完成,待配置Redis

---

## 📖 概述

Phase 2 在 Phase 1 的基础上,集成了 Celery 异步任务队列,实现真正的后台异步索引功能。主要特性包括:

- ✅ Celery异步任务队列
- ✅ Redis作为消息代理
- ✅ 任务状态追踪和更新
- ✅ 进度实时监控
- ✅ 失败重试机制
- ✅ Worker进程管理

---

## 🏗️ 架构设计

```
┌──────────────┐
│  FastAPI     │
│  Web Server  │
└──────┬───────┘
       │
       │ API调用
       ▼
┌──────────────┐      任务消息      ┌──────────────┐
│ API Router   │─────────────────>│  Redis       │
│ (document_   │                   │  (Message    │
│  index.py)   │                   │   Broker)    │
└──────────────┘                   └──────┬───────┘
                                          │
                                          │ 任务拉取
                                          ▼
                                   ┌──────────────┐
                                   │ Celery       │
                                   │ Worker       │
                                   │ (后台进程)    │
                                   └──────┬───────┘
                                          │
                                          │ 执行索引
                                          ▼
                                   ┌──────────────┐
                                   │Incremental   │
                                   │Indexer       │
                                   │(索引引擎)     │
                                   └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │Vector Store  │
                                   │ + Database   │
                                   └──────────────┘
```

---

## 📦 安装依赖

### 1. Python包

```bash
cd /home/zhangjh/code/python/rag
source venv/bin/activate
pip install celery redis flower
```

**已安装版本**:
- celery==5.5.3
- redis==7.1.0
- flower (可选,用于监控)

### 2. Redis服务

确保Redis服务正在运行:

```bash
# 检查Redis状态
redis-cli ping

# 如果需要密码认证
redis-cli -a YOUR_PASSWORD ping
```

---

## ⚙️ 配置

### 1. 环境变量 (.env)

在项目根目录的`.env`文件中添加:

```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password  # 如果Redis设置了密码
REDIS_DB=0

# Celery配置
CELERY_ENABLED=true  # 启用Celery异步任务
```

### 2. Celery配置文件

配置文件位置: `app/config/celery_config.py`

主要配置项:
- **broker_url**: Redis消息代理地址
- **result_backend**: 结果存储后端
- **task_routes**: 任务路由规则
- **worker_prefetch_multiplier**: Worker预取任务数
- **task_time_limit**: 任务最大执行时间(30分钟)

---

## 🚀 启动服务

### 方法1: 手动启动 (推荐,用于开发)

**步骤1**: 启动FastAPI服务

```bash
cd /home/zhangjh/code/python/rag/backend
source ../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8800 --reload
```

**步骤2**: 启动Celery Worker (新终端)

```bash
cd /home/zhangjh/code/python/rag/backend
./start_celery_worker.sh
```

**步骤3**: (可选) 启动Flower监控 (新终端)

```bash
cd /home/zhangjh/code/python/rag/backend
./start_flower.sh
```

访问监控界面: http://localhost:5555

### 方法2: 使用脚本启动

```bash
# Worker启动脚本
./start_celery_worker.sh

# 包含以下参数:
# - concurrency=4 (4个worker进程)
# - max-tasks-per-child=1000 (每个worker最多执行1000个任务后重启)
# - time-limit=1800 (任务硬超时30分钟)
# - soft-time-limit=1500 (软超时25分钟)
```

---

## 📝 API接口变更

### 1. 索引文档 (/api/index/index-documents)

**请求**:
```json
{
  "doc_ids": [1, 2, 3, 4, 5],
  "force": false,
  "priority": 5
}
```

**响应 (Celery模式 - 5个或以上文档)**:
```json
{
  "success": true,
  "message": "已提交 5 个文档到Celery队列",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "doc_ids": [1, 2, 3, 4, 5],
    "status": "queued",
    "mode": "celery"
  }
}
```

**响应 (同步模式 - 少于5个文档)**:
```json
{
  "success": true,
  "message": "索引完成: 成功=3, 失败=0",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "details": [...],
    "mode": "sync"
  }
}
```

### 2. 查询任务状态 (/api/index/task/{task_id})

**新增API**: 查询Celery任务的执行状态

**请求**:
```bash
GET /api/index/task/550e8400-e29b-41d4-a716-446655440000
```

**响应**:
```json
{
  "success": true,
  "message": "任务状态获取成功",
  "data": {
    "id": 123,
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "task_type": "batch",
    "status": "processing",
    "priority": 5,
    "progress": 60,
    "created_at": "2025-01-22T10:00:00",
    "started_at": "2025-01-22T10:00:05",
    "updated_at": "2025-01-22T10:02:30",
    "celery_state": "PROGRESS",
    "celery_result": {
      "progress": 60,
      "current": 3,
      "total": 5,
      "status": "处理中 3/5"
    }
  }
}
```

---

## 🔧 Celery任务定义

### 1. index_document_task - 单文档索引

**位置**: `app/tasks/index_tasks.py`

**功能**:
- 异步索引单个文档
- 自动重试(最多3次)
- 实时进度更新
- 错误处理和日志记录

**使用示例**:
```python
from app.tasks.index_tasks import index_document_task

# 提交任务
result = index_document_task.delay(doc_id=101, user_id=1, force=False)

# 查询状态
print(f"任务ID: {result.id}")
print(f"任务状态: {result.state}")
```

### 2. batch_index_task - 批量索引

**功能**:
- 批量索引多个文档
- 进度回调机制
- 详细的统计信息

**使用示例**:
```python
from app.tasks.index_tasks import batch_index_task

# 提交批量任务
result = batch_index_task.delay(doc_ids=[1,2,3,4,5], user_id=1)
```

### 3. delete_index_task - 删除索引

**功能**:
- 异步删除文档索引
- 清理向量和数据库记录

---

## 📊 任务状态生命周期

```
pending → processing → completed
   ↓                      ↑
   └──→ failed ──(retry)──┘
           ↓
       cancelled
```

**状态说明**:
- `pending`: 任务已创建,等待执行
- `processing`: 任务正在执行中
- `completed`: 任务成功完成
- `failed`: 任务执行失败
- `cancelled`: 任务被取消

---

## 🔍 监控与诊断

### 1. Flower监控界面

访问 http://localhost:5555 查看:
- 实时任务列表
- Worker状态
- 任务成功/失败统计
- 任务执行时间分布

### 2. 数据库查询

```sql
-- 查看活跃任务
SELECT * FROM v_active_index_tasks;

-- 查看任务统计
SELECT
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM index_tasks
WHERE completed_at IS NOT NULL
GROUP BY status;

-- 查看最近的任务
SELECT task_id, task_type, status, progress, created_at, updated_at
FROM index_tasks
ORDER BY created_at DESC
LIMIT 20;
```

### 3. 日志查看

```bash
# FastAPI日志
tail -f backend/logs/app.log

# Celery Worker日志
# (输出在启动worker的终端)
```

---

## ⚠️ 故障排查

### 问题1: Worker无法连接Redis

**错误**: `redis.exceptions.ConnectionError`

**解决方案**:
1. 检查Redis是否运行: `redis-cli ping`
2. 检查Redis密码配置: `.env`文件中的`REDIS_PASSWORD`
3. 检查防火墙设置

### 问题2: 任务一直处于pending状态

**原因**: Worker未启动或未连接到正确的队列

**解决方案**:
```bash
# 检查Worker是否运行
ps aux | grep celery

# 启动Worker
./start_celery_worker.sh
```

### 问题3: Redis认证失败

**错误**: `NOAUTH Authentication required`

**解决方案**:
1. 在`.env`中设置正确的`REDIS_PASSWORD`
2. 或者修改Redis配置,禁用认证(仅开发环境)

```bash
# Redis配置文件 (通常是 /etc/redis/redis.conf)
# 注释掉以下行来禁用认证:
# requirepass your_password
```

### 问题4: 任务执行超时

**配置调整**:

编辑 `app/config/celery_config.py`:

```python
'task_time_limit': 30 * 60,      # 硬限制(秒)
'task_soft_time_limit': 25 * 60, # 软限制(秒)
```

---

## 🎯 性能优化建议

### 1. Worker并发配置

根据服务器资源调整:

```bash
# CPU密集型任务
celery -A app.celery_app worker --concurrency=4

# IO密集型任务
celery -A app.celery_app worker --concurrency=8
```

### 2. 任务优先级

高优先级任务优先执行:

```python
# 高优先级
batch_index_task.apply_async(args=[doc_ids], priority=9)

# 普通优先级
batch_index_task.apply_async(args=[doc_ids], priority=5)

# 低优先级
batch_index_task.apply_async(args=[doc_ids], priority=1)
```

### 3. 结果过期时间

配置任务结果的保存时间:

```python
'result_expires': 3600,  # 结果保存1小时
```

---

## 📈 Phase 2 vs Phase 1 对比

| 特性 | Phase 1 | Phase 2 |
|------|---------|---------|
| 异步处理 | BackgroundTasks (伪异步) | Celery (真异步) |
| 进程管理 | 单进程 | 多进程Worker |
| 任务队列 | 内存 | Redis持久化 |
| 失败重试 | 不支持 | ✅ 自动重试 |
| 进度监控 | 基础回调 | ✅ 实时状态更新 |
| 分布式 | 不支持 | ✅ 支持 |
| 任务优先级 | 不支持 | ✅ 支持 |
| 监控界面 | 无 | ✅ Flower |

---

## 🚧 下一步 (Phase 3)

Phase 3 计划功能:
1. WebSocket实时进度推送
2. 版本控制与回滚
3. 前端监控Dashboard
4. 自动化定时任务
5. 任务链和工作流

---

## 📞 技术支持

### 测试脚本

```bash
# 测试Celery配置
python test_celery.py
```

### 相关文档
- [Celery官方文档](https://docs.celeryq.dev/)
- [Redis官方文档](https://redis.io/docs/)
- [Phase 1使用指南](./INCREMENTAL_UPDATE_GUIDE.md)

---

**版本**: Phase 2
**作者**: Claude Code
**日期**: 2025-01-22
**状态**: ✅ 开发完成,待Redis配置后测试
