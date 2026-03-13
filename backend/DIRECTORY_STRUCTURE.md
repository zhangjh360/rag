# 目录结构说明

## 整理后的目录结构

```
backend/
├── app/                          # 应用核心代码
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── config/                   # 配置模块
│   │   ├── __init__.py
│   │   ├── settings.py           # 应用配置（从config.py移动）
│   │   └── logging_config.py     # 日志配置
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── schemas.py
│   │   └── vector_database.py
│   ├── services/                 # 业务服务
│   │   ├── __init__.py
│   │   ├── embedding.py
│   │   ├── generation.py
│   │   ├── generation_async.py
│   │   ├── retrieval.py
│   │   └── advanced_retrieval.py
│   ├── routers/                  # API路由
│   │   ├── __init__.py
│   │   ├── query.py
│   │   ├── upload.py
│   │   ├── logs.py
│   │   └── advanced_query.py
│   ├── middleware/               # 中间件
│   │   ├── __init__.py
│   │   └── logging_middleware.py
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   └── log_manager.py
│   └── database/                 # 数据库相关
│       ├── __init__.py
│       ├── connection.py         # 数据库连接（从database.py移动）
│       └── init.py              # 数据库初始化
├── scripts/                      # 脚本文件
│   ├── __init__.py
│   ├── start_dev.py             # 开发启动脚本
│   ├── load_env.py              # 环境变量加载
│   ├── fix_database.py          # 数据库修复
│   └── migrate_embedding_column.py # 数据库迁移
├── tests/                        # 测试文件
│   ├── __init__.py
│   ├── test_embedding_fix.py
│   ├── test_generation_fix.py
│   └── test_logging_system.py
├── examples/                     # 示例文件
│   ├── __init__.py
│   └── embedding_example.py
├── docs/                         # 文档
│   ├── EMBEDDING_CONFIG.md
│   ├── EMBEDDING_FIX_GUIDE.md
│   ├── GENERATION_FIX_SUMMARY.md
│   ├── LOGGING_GUIDE.md
│   ├── QUERY_IMPROVEMENTS.md
│   └── QUERY_OPTIMIZATION_GUIDE.md
├── requirements.txt
├── Dockerfile
├── start.py                      # 新的启动脚本
└── .env.example
```

## 整理原因和好处

### 1. **模块化结构**
- **之前**：配置文件、数据库文件、脚本文件都混在根目录
- **现在**：按功能分类，每个模块职责清晰

### 2. **配置管理**
- **之前**：`config.py` 在根目录，配置分散
- **现在**：`app/config/settings.py` 统一管理所有配置

### 3. **数据库管理**
- **之前**：`database.py` 在根目录，功能混杂
- **现在**：`app/database/` 模块专门管理数据库相关功能

### 4. **脚本组织**
- **之前**：各种脚本文件散落在根目录
- **现在**：`scripts/` 目录统一管理所有脚本

### 5. **测试组织**
- **之前**：测试文件在根目录
- **现在**：`tests/` 目录专门管理测试文件

### 6. **示例代码**
- **之前**：示例文件在根目录
- **现在**：`examples/` 目录专门管理示例代码

## 文件移动说明

### 移动的文件

1. **配置文件**
   - `config.py` → `app/config/settings.py`
   - 增加了更多配置选项（日志、检索等）

2. **数据库文件**
   - `database.py` → `app/database/connection.py` + `app/database/init.py`
   - 分离了连接管理和初始化功能

3. **脚本文件**
   - `start_dev.py` → `scripts/start_dev.py`
   - `load_env.py` → `scripts/load_env.py`
   - `fix_database.py` → `scripts/fix_database.py`
   - `migrate_embedding_column.py` → `scripts/migrate_embedding_column.py`

4. **测试文件**
   - `test_*.py` → `tests/test_*.py`

5. **示例文件**
   - `embedding_example.py` → `examples/embedding_example.py`

### 更新的导入路径

所有文件中的导入路径都已更新：

```python
# 之前
from config import DB_URL
from database import get_db

# 现在
from app.config.settings import DB_URL
from app.database.connection import get_db
```

## 使用方法

### 1. 启动服务

```bash
# 使用新的启动脚本
python start.py

# 或者使用原来的脚本
python scripts/start_dev.py
```

### 2. 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_embedding_fix.py
```

### 3. 运行示例

```bash
# 运行嵌入向量示例
python examples/embedding_example.py
```

### 4. 数据库操作

```bash
# 修复数据库
python scripts/fix_database.py

# 迁移数据库
python scripts/migrate_embedding_column.py
```

## 优势

1. **清晰的模块结构**：每个目录职责明确
2. **更好的可维护性**：相关文件集中管理
3. **便于扩展**：新功能可以按模块添加
4. **符合Python最佳实践**：标准的包结构
5. **便于测试**：测试文件独立管理
6. **便于部署**：脚本文件统一管理

## 注意事项

1. **导入路径**：所有导入路径已更新，确保使用新的路径
2. **环境变量**：配置加载逻辑保持不变
3. **向后兼容**：API接口保持不变
4. **启动方式**：可以使用新的 `start.py` 或原来的脚本

现在您的项目结构更加清晰和专业，符合Python项目的最佳实践！
