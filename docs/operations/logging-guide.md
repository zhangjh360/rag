# 日志系统配置指南

## 概述

新的日志系统提供了完整的日志管理功能，包括分类存储、自动轮转、搜索查询、清理归档等功能。

## 日志目录结构

```
logs/
├── app/           # 应用日志
│   ├── app.log
│   ├── app.log.1
│   └── ...
├── error/         # 错误日志
│   ├── error.log
│   └── ...
├── access/        # 访问日志
│   ├── access.log
│   └── ...
├── debug/         # 调试日志
│   ├── debug.log
│   └── ...
└── archive/       # 归档日志
    ├── app/
    ├── error/
    └── ...
```

## 环境变量配置

### 基本配置

```bash
# 日志目录
LOG_DIR=logs

# 日志级别
LOG_LEVEL=INFO

# 文件大小限制（字节）
LOG_MAX_SIZE=10485760  # 10MB

# 备份文件数量
LOG_BACKUP_COUNT=5

# 是否启用控制台输出
LOG_ENABLE_CONSOLE=true

# 是否启用文件输出
LOG_ENABLE_FILE=true
```

### 日志级别说明

| 级别 | 数值 | 说明 |
|------|------|------|
| DEBUG | 10 | 调试信息，最详细 |
| INFO | 20 | 一般信息 |
| WARNING | 30 | 警告信息 |
| ERROR | 40 | 错误信息 |
| CRITICAL | 50 | 严重错误 |

## 使用方法

### 1. 基本日志记录

```python
from app.config.logging_config import get_app_logger, get_error_logger

# 获取日志器
logger = get_app_logger()
error_logger = get_error_logger()

# 记录日志
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
error_logger.error("这是一条错误日志")
```

### 2. 在服务中使用

```python
# 在服务类中
from app.config.logging_config import get_app_logger

class MyService:
    def __init__(self):
        self.logger = get_app_logger()
    
    async def do_something(self):
        try:
            # 业务逻辑
            self.logger.info("开始执行业务逻辑")
            # ...
            self.logger.info("业务逻辑执行完成")
        except Exception as e:
            self.logger.error(f"业务逻辑执行失败: {e}")
            raise
```

### 3. 中间件日志

系统自动记录HTTP请求日志：

```
2024-01-01 12:00:00 - access - INFO - [abc12345] 请求开始 - POST /api/upload 来自 192.168.1.100
2024-01-01 12:00:01 - access - INFO - [abc12345] 请求完成 - POST /api/upload 状态码: 200 处理时间: 1.234s
```

## API接口

### 1. 获取日志文件列表

```http
GET /api/logs/files?log_type=app
```

### 2. 读取日志文件

```http
GET /api/logs/read/logs/app/app.log?lines=100
```

### 3. 搜索日志

```http
GET /api/logs/search?query=error&log_type=error&hours=24
```

### 4. 获取日志统计

```http
GET /api/logs/statistics
```

### 5. 清理旧日志

```http
POST /api/logs/clean?days=30
```

### 6. 归档日志

```http
POST /api/logs/archive?days=7
```

### 7. 导出日志

```http
POST /api/logs/export?output_file=export.log&log_type=app&hours=24
```

## 日志管理工具

### 1. 命令行工具

```python
from app.utils.log_manager import log_manager

# 获取日志统计
stats = log_manager.get_log_statistics()
print(f"总文件数: {stats['total_files']}")
print(f"总大小: {stats['total_size_mb']} MB")

# 搜索日志
results = log_manager.search_logs("error", "error", 24)
for result in results:
    print(f"{result['file']}:{result['line']} - {result['content']}")

# 清理旧日志
clean_result = log_manager.clean_old_logs(30)
print(f"清理了 {clean_result['cleaned_files']} 个文件")
```

### 2. 定期清理脚本

```python
#!/usr/bin/env python3
"""
定期日志清理脚本
"""

import schedule
import time
from app.utils.log_manager import log_manager

def clean_logs():
    """清理30天前的日志"""
    result = log_manager.clean_old_logs(30)
    print(f"清理完成: {result['cleaned_files']} 个文件, 释放 {result['freed_space_mb']} MB")

def archive_logs():
    """归档7天前的日志"""
    result = log_manager.archive_logs(7)
    print(f"归档完成: {result['archived_files']} 个文件")

# 每天凌晨2点清理日志
schedule.every().day.at("02:00").do(clean_logs)

# 每周一凌晨3点归档日志
schedule.every().monday.at("03:00").do(archive_logs)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## 性能优化

### 1. 日志级别优化

生产环境建议设置：
```bash
LOG_LEVEL=WARNING  # 只记录警告和错误
```

开发环境建议设置：
```bash
LOG_LEVEL=DEBUG    # 记录所有信息
```

### 2. 文件轮转配置

```bash
# 单个文件最大10MB
LOG_MAX_SIZE=10485760

# 保留5个备份文件
LOG_BACKUP_COUNT=5
```

### 3. 第三方库日志控制

系统自动设置第三方库的日志级别：
- uvicorn: INFO
- fastapi: INFO  
- sqlalchemy: WARNING
- openai: WARNING
- transformers: WARNING

## 监控和告警

### 1. 日志监控

```python
# 监控错误日志
def monitor_errors():
    results = log_manager.search_logs("ERROR", "error", 1)
    if len(results) > 10:  # 1小时内超过10个错误
        # 发送告警
        send_alert(f"错误日志过多: {len(results)} 个错误")
```

### 2. 性能监控

```python
# 监控慢请求
def monitor_slow_requests():
    results = log_manager.search_logs("慢请求检测", "access", 1)
    if len(results) > 5:  # 1小时内超过5个慢请求
        # 发送告警
        send_alert(f"慢请求过多: {len(results)} 个慢请求")
```

## 故障排除

### 1. 日志文件过大

```bash
# 检查日志文件大小
ls -lh logs/*/

# 手动清理
python -c "from app.utils.log_manager import log_manager; print(log_manager.clean_old_logs(7))"
```

### 2. 日志目录权限问题

```bash
# 确保日志目录可写
chmod 755 logs/
chmod 755 logs/*/
```

### 3. 磁盘空间不足

```bash
# 检查磁盘使用情况
df -h

# 清理旧日志
python -c "from app.utils.log_manager import log_manager; print(log_manager.clean_old_logs(1))"
```

## 最佳实践

1. **分级记录**：根据重要性选择合适的日志级别
2. **结构化日志**：使用统一的日志格式
3. **定期清理**：设置自动清理和归档任务
4. **监控告警**：监控错误和性能指标
5. **安全考虑**：避免在日志中记录敏感信息
6. **性能优化**：生产环境使用合适的日志级别

## 总结

新的日志系统提供了：
- ✅ 分类存储（app、error、access、debug）
- ✅ 自动轮转（按大小和时间）
- ✅ 搜索查询（关键词搜索）
- ✅ 清理归档（自动管理）
- ✅ API接口（Web管理）
- ✅ 性能监控（慢请求检测）
- ✅ 错误追踪（详细错误信息）

现在您的日志系统已经完全独立管理，可以更好地监控和调试应用程序！
