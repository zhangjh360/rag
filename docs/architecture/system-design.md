# RAG 系统设计稿

## 1. 系统概述

### 1.1 项目背景
本系统是一个基于Retrieval-Augmented Generation (RAG) 的智能问答或知识检索应用。RAG 通过检索相关文档来增强生成模型的输出，避免LLM的幻觉问题。系统分为前后端分离架构：
- **后端**：使用 Python 实现核心逻辑，包括数据摄入、向量嵌入、检索和生成。
- **前端**：使用 Vue 3 开发用户界面，提供交互式查询、结果展示和文件上传功能。
- **数据库**：使用 PostgreSQL 的向量扩展（pgvector），存储文档向量和元数据。
- **增强模型**：集成 OpenAI API，用于生成嵌入向量和响应生成。

系统目标：用户上传文档或查询知识库，系统检索相关内容并生成自然语言响应。适用于知识管理、客服聊天机器人等场景。

### 1.2 关键特性
- 支持文档上传、索引和检索。
- 实时查询：用户输入问题，系统检索相关文档片段，并用 OpenAI 生成增强响应。
- 向量搜索：使用余弦相似度等进行高效检索。
- 用户友好界面：支持查询历史、结果可视化。
- 安全性：API 认证、数据加密。

### 1.3 假设与约束
- 假设用户有 OpenAI API 密钥。
- 系统不涉及大规模分布式部署，初始为单机或小型服务器。
- 文档类型主要为文本（PDF、TXT 等），可扩展图像/多模态。
- 性能目标：查询响应时间 < 2 秒（视文档规模）。

## 2. 系统架构

### 2.1 高层架构图（文本描述）
```
[前端: Vue 3 App]
  - 用户交互：查询输入、文件上传、结果展示
  - API 调用：RESTful / WebSocket 到后端

↓ (HTTP/HTTPS)

[后端: Python (FastAPI/Flask)]
  - 路由：/upload, /query, /index
  - 逻辑层：文档处理、嵌入生成、检索
  - 集成：OpenAI Client, pgvector

↓ (数据库连接)

[数据库: PostgreSQL + pgvector]
  - 表：documents (id, content, embedding, metadata)
  - 索引：向量索引 (IVFFlat 或 HNSW)

↓ (外部 API)

[OpenAI API]
  - 嵌入：text-embedding-ada-002 或类似模型
  - 生成：gpt-4o 或类似模型
```

- **数据流**：
  1. 用户上传文档 → 后端解析 → 生成嵌入 → 存储到数据库。
  2. 用户查询 → 后端生成查询嵌入 → 向量检索 → 检索结果 + 查询 → OpenAI 生成响应 → 返回前端。

### 2.2 组件分解
- **前端**：单页应用 (SPA)，使用 Vue Router 管理路由，Vuex/Pinia 状态管理。
- **后端**：RESTful API，使用 FastAPI（推荐，异步支持好）或 Flask。
- **数据库**：PostgreSQL 实例，启用 pgvector 扩展。
- **外部依赖**：OpenAI SDK (openai-python)，向量处理库 (numpy, scikit-learn)。

## 3. 后端设计 (Python)

### 3.1 技术栈
- 框架：FastAPI (异步、自动文档生成)。
- 库：
  - openai：集成 OpenAI API。
  - psycopg2 或 SQLAlchemy：数据库连接，支持 pgvector。
  - langchain 或 llama-index：简化 RAG 管道（可选，简化嵌入和检索）。
  - PyPDF2 或 textract：文档解析。
  - numpy：向量操作。
- 环境：Python 3.10+，虚拟环境 (venv)。

### 3.2 目录结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # 入口文件
│   ├── routers/         # API 路由
│   │   ├── upload.py    # 文档上传
│   │   └── query.py     # 查询接口
│   ├── services/        # 业务逻辑
│   │   ├── embedding.py # 嵌入生成
│   │   ├── retrieval.py # 向量检索
│   │   └── generation.py# 响应生成
│   └── models/          # 数据模型 (Pydantic)
├── config.py            # 配置 (DB URL, OpenAI Key)
├── requirements.txt     # 依赖
└── Dockerfile           # 容器化（可选）
```

### 3.3 关键模块设计
- **配置**：config.py 中存储环境变量，如 `OPENAI_API_KEY`、`DB_URL = "postgresql://user:pass@localhost:5432/ragdb"`。
- **数据库初始化**：
  - 使用 SQLAlchemy 创建表：
    ```python
    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.dialects.postgresql import VECTOR
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()
    engine = create_engine(DB_URL)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)
        content = Column(String)
        embedding = Column(VECTOR(1536))  # OpenAI 嵌入维度示例
        metadata = Column(String)  # JSON 字符串

    Base.metadata.create_all(engine)
    ```
  - 添加向量索引：`CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);` (在迁移脚本中执行)。

- **上传接口** (/upload, POST)：
  - 接收文件，解析文本。
  - 生成嵌入：`openai.Embedding.create(input=text, model="text-embedding-ada-002")`。
  - 插入数据库。

- **查询接口** (/query, POST)：
  - 接收查询字符串。
  - 生成查询嵌入。
  - 检索：`SELECT * FROM documents ORDER BY embedding <=> query_embedding LIMIT 5;` (使用 pgvector 的 <=> 操作符)。
  - 组合上下文 + 查询，调用 OpenAI ChatCompletion 生成响应。

- **错误处理**：使用 FastAPI 的异常处理，日志记录 (logging)。

### 3.4 性能优化
- 批量嵌入：处理大文档时分块。
- 缓存：使用 Redis 缓存热门查询（可选扩展）。
- 异步：FastAPI 支持 async def。

## 4. 前端设计 (Vue 3)

### 4.1 技术栈
- 框架：Vue 3 (Composition API)。
- UI 库：Element Plus 或 Ant Design Vue。
- 状态管理：Pinia。
- HTTP：Axios。
- 构建工具：Vite。
- 路由：Vue Router。

### 4.2 目录结构
```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # 组件
│   │   ├── UploadForm.vue
│   │   └── QueryResult.vue
│   ├── views/           # 页面
│   │   ├── Home.vue     # 主页（查询 + 上传）
│   │   └── History.vue  # 查询历史
│   ├── store/           # Pinia 状态
│   ├── router.js        # 路由配置
│   └── App.vue          # 根组件
├── public/              # 公共文件
├── vite.config.js       # 配置
└── package.json         # 依赖
```

### 4.3 关键页面与组件
- **主页 (Home.vue)**：
  - 上传组件：`<el-upload>` 支持拖拽，调用后端 /upload。
  - 查询输入：文本框 + 按钮，调用 /query，展示结果（问题、检索文档片段、生成响应）。
  - 使用 Pinia 存储查询历史。

- **结果展示**：QueryResult.vue 使用卡片或列表显示检索片段和高亮响应。

- **API 调用**：
  ```javascript
  import axios from 'axios';

  const api = axios.create({ baseURL: 'http://localhost:8800' });

  // 上传
  async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData);
  }

  // 查询
  async function query(text) {
    return api.post('/query', { query: text });
  }
  ```

- **响应式设计**：使用 Vue 的 ref/reactive 管理状态。

## 5. 数据库设计 (PostgreSQL + pgvector)

### 5.1 安装与配置
- 安装 PostgreSQL 15+。
- 启用 pgvector：`CREATE EXTENSION vector;`。
- 表结构：如后端设计所述。
- 数据类型：VECTOR(1536) 为 OpenAI 嵌入维度（可根据模型调整）。

### 5.2 索引与查询
- 索引类型：HNSW (高性能近似搜索) 或 IVFFlat。
- 查询示例：使用余弦距离 `<=>` 操作符。
- 备份：定期 pg_dump。

## 6. 数据流与交互

### 6.1 上传流程
1. 前端上传文件 → 后端解析文本 → 分块（可选） → OpenAI 嵌入 → 存储到 pgvector。

### 6.2 查询流程
1. 前端发送查询 → 后端生成嵌入 → pgvector 检索 Top-K 文档 → 构建提示（"基于以下上下文回答: [docs] Question: [query]"） → OpenAI 生成 → 返回 JSON {response, sources} → 前端渲染。

## 7. 安全与部署

### 7.1 安全考虑
- API 认证：使用 JWT 或 API Key。
- 输入验证：防止 SQL 注入、XSS。
- OpenAI Key：环境变量存储，不暴露。
- 数据隐私：加密敏感文档。

### 7.2 部署
- 后端：Docker 容器，部署到 Heroku/AWS。
- 前端：Vite 构建，部署到 Vercel/Netlify。
- 数据库：托管于 Supabase (内置 pgvector) 或 AWS RDS。
- CI/CD：GitHub Actions。

## 8. 开发计划与扩展

### 8.1 开发阶段
1. 设置环境与数据库 (1 天)。
2. 后端核心 (上传/查询, 3 天)。
3. 前端界面 (2 天)。
4. 集成测试 (1 天)。
5. 优化与部署 (2 天)。

### 8.2 扩展点
- 多模态：添加图像嵌入 (OpenAI CLIP)。
- 实时索引：使用 WebSocket 更新。
- 监控：集成 Prometheus/Grafana。
- 成本优化：监控 OpenAI API 调用。

## 9. 实现状态

### 9.1 已完成功能 ✅

#### 后端实现
- [x] **FastAPI 框架搭建**: 完整的后端架构，包含路由、服务和数据模型
- [x] **数据库模型**: 使用 SQLAlchemy + pgvector 实现文档和查询表
- [x] **嵌入服务**: 集成 OpenAI API 生成文本嵌入
- [x] **文档上传**: 支持 PDF/TXT 文件上传、解析和向量化存储
- [x] **检索服务**: 基于余弦相似度的向量检索
- [x] **生成服务**: 使用 OpenAI ChatCompletion 生成回答
- [x] **API 接口**: 完整的 RESTful API，包含上传、查询和历史记录
- [x] **错误处理**: 完善的异常处理和日志记录
- [x] **CORS 支持**: 配置跨域访问支持

#### 前端实现
- [x] **Vue 3 应用**: 完整的单页应用，使用 Composition API
- [x] **Element Plus UI**: 现代化的用户界面组件
- [x] **文档上传**: 拖拽上传功能，支持文件类型验证
- [x] **查询界面**: 文本输入和结果显示
- [x] **状态管理**: 使用 Pinia 管理应用状态
- [x] **路由管理**: Vue Router 实现页面导航
- [x] **历史记录**: 查询历史的展示和管理
- [x] **响应式设计**: 适配不同屏幕尺寸

#### 部署和文档
- [x] **使用文档**: 完整的 README 和使用指南
- [x] **快速启动**: 自动化启动脚本
- [x] **Docker 支持**: 完整的容器化部署方案
- [x] **环境配置**: 环境变量模板和配置文件

### 9.2 核心特性

#### 文档处理
- 支持 PDF 和 TXT 文件格式
- 自动文本提取和内容验证
- 文档元数据管理
- 批量上传支持

#### 智能检索
- 向量嵌入生成 (OpenAI text-embedding-ada-002)
- 余弦相似度计算
- Top-K 相关文档检索
- 相似度评分和排序

#### 问答生成
- 上下文感知的回答生成
- 基于 GPT-3.5-turbo 的自然语言处理
- 相关文档引用和来源展示
- 回答质量优化

#### 用户体验
- 直观的文件上传界面
- 实时查询处理
- 查询结果高亮显示
- 历史记录时间线展示

### 9.3 技术实现亮点

#### 后端架构
```
backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── routers/             # API 路由
│   │   ├── upload.py        # 文档上传接口
│   │   └── query.py         # 查询接口
│   ├── services/            # 业务逻辑
│   │   ├── embedding.py     # 嵌入生成服务
│   │   ├── retrieval.py     # 检索服务
│   │   └── generation.py    # 生成服务
│   └── models/              # 数据模型
│       ├── database.py      # SQLAlchemy 模型
│       └── schemas.py       # Pydantic 模型
├── config.py                # 配置管理
├── database.py              # 数据库初始化
└── requirements.txt         # 依赖管理
```

#### 前端架构
```
frontend/
├── src/
│   ├── main.js              # 应用入口
│   ├── App.vue             # 根组件
│   ├── router.js           # 路由配置
│   ├── store/              # 状态管理
│   │   └── ragStore.js     # RAG 状态存储
│   └── views/              # 页面组件
│       ├── Home.vue        # 主页
│       └── History.vue     # 历史记录
├── package.json            # 依赖配置
└── vite.config.js          # 构建配置
```

#### 数据库设计
- **documents 表**: 存储文档内容、嵌入向量和元数据
- **queries 表**: 存储查询历史和回答记录
- **向量索引**: HNSW 索引优化检索性能
- **扩展性**: 支持多模态数据和元数据过滤

### 9.4 部署选项

#### 开发环境
- 快速启动脚本 (`start.sh`)
- 热重载开发服务器
- 自动依赖安装

#### 生产环境
- Docker 容器化部署
- Docker Compose 编排
- 环境变量配置
- 健康检查和监控

### 9.5 API 接口

#### 文档管理
- `POST /api/upload` - 上传文档
- `GET /api/documents` - 获取文档列表

#### 查询功能
- `POST /api/query` - 执行查询
- `GET /api/history` - 获取查询历史

#### 系统状态
- `GET /` - 系统信息
- `GET /health` - 健康检查
- `GET /docs` - API 文档

### 9.6 扩展建议

#### 性能优化
- [ ] Redis 缓存层
- [ ] 文档分块处理
- [ ] 异步任务队列
- [ ] 查询结果缓存

#### 功能增强
- [ ] 多模态支持 (图片、音频)
- [ ] 用户认证和权限管理
- [ ] 文档版本控制
- [ ] 高级搜索过滤

#### 监控和运维
- [ ] 性能监控
- [ ] 错误追踪
- [ ] 使用分析
- [ ] 自动化备份

### 9.7 总结

本 RAG 系统已完整实现设计稿中的核心功能，包括：
- 完整的前后端分离架构
- 文档上传和向量化存储
- 智能检索和问答生成
- 用户友好的 Web 界面
- 完善的部署和文档

系统具备生产环境部署的基础条件，可根据具体需求进一步扩展和优化。