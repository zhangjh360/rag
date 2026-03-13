# 项目依赖说明

本文档描述了项目的 Python 依赖包及其用途。

## 依赖概览

总计约 **90+ 个包**,分为以下几个主要类别:

### 📦 核心分类

1. **Web 框架** (4 个包)
2. **数据库** (3 个包)
3. **数据验证** (4 个包)
4. **安全认证** (5 个包)
5. **AI & LLM** (2 个包)
6. **LangChain 生态** (7 个包)
7. **向量搜索** (6 个包)
8. **科学计算** (4 个包)
9. **监控可观测性** (19 个包)
10. **HTTP 网络** (4 个包)
11. **NLP 文本处理** (3 个包)
12. **系统工具** (30+ 个包)

---

## 详细说明

### 🌐 Core Web Framework (核心 Web 框架)

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.104.1 | 高性能异步 Web 框架 |
| `uvicorn[standard]` | 0.24.0 | ASGI 服务器 |
| `starlette` | 0.27.0 | FastAPI 的底层框架 |
| `python-multipart` | 0.0.6 | 文件上传支持 |

### 💾 Database & ORM (数据库)

| 包名 | 版本 | 用途 |
|------|------|------|
| `sqlalchemy` | 2.0.23 | Python SQL 工具包和 ORM |
| `psycopg2-binary` | 2.9.9 | PostgreSQL 适配器 |
| `pgvector` | 0.4.1 | PostgreSQL 向量扩展支持 |

### ✅ Data Validation (数据验证)

| 包名 | 版本 | 用途 |
|------|------|------|
| `pydantic` | 2.11.7 | 数据验证和设置管理 |
| `pydantic-core` | 2.33.2 | Pydantic 核心库 |
| `pydantic-settings` | 2.10.1 | 配置管理 |
| `email-validator` | 2.3.0 | 邮箱验证 |

### 🔐 Authentication & Security (安全认证)

| 包名 | 版本 | 用途 |
|------|------|------|
| `PyJWT` | 2.8.0 | JWT token 生成和验证 |
| `passlib[bcrypt]` | 1.7.4 | 密码哈希 |
| `python-jose[cryptography]` | 3.3.0 | JOSE 实现 (JWT/JWS/JWE) |
| `bcrypt` | 5.0.0 | Bcrypt 哈希算法 |
| `cryptography` | 46.0.3 | 加密库 |

### 🤖 AI & LLM (人工智能)

| 包名 | 版本 | 用途 |
|------|------|------|
| `openai` | 1.107.0 | OpenAI API 客户端 |
| `anthropic` | 0.67.0 | Anthropic Claude API 客户端 |

### ⛓️ LangChain Ecosystem (LangChain 生态)

| 包名 | 版本 | 用途 |
|------|------|------|
| `langchain` | 0.3.27 | LLM 应用开发框架 |
| `langchain-core` | 0.3.75 | LangChain 核心组件 |
| `langchain-openai` | 0.3.32 | OpenAI 集成 |
| `langchain-huggingface` | 0.3.1 | HuggingFace 集成 |
| `langchain-community` | 0.3.29 | 社区集成 |
| `langchain-text-splitters` | 0.3.11 | 文本分割工具 |
| `langsmith` | 0.4.21 | LangChain 监控平台 |

### 🔍 Embeddings & Vector Search (向量搜索)

| 包名 | 版本 | 用途 |
|------|------|------|
| `sentence-transformers` | 5.1.0 | 句子嵌入模型 |
| `transformers` | 4.56.0 | HuggingFace Transformers |
| `huggingface-hub` | 0.34.4 | HuggingFace Hub 客户端 |
| `tokenizers` | 0.22.0 | 快速分词器 |
| `torch` | 2.8.0 | PyTorch 深度学习框架 |
| `faiss-cpu` | 1.12.0 | Facebook 向量相似度搜索 |

### 🔬 Scientific Computing (科学计算)

| 包名 | 版本 | 用途 |
|------|------|------|
| `numpy` | 2.3.2 | 数值计算基础库 |
| `scipy` | 1.16.1 | 科学计算库 |
| `scikit-learn` | 1.7.1 | 机器学习库 |
| `pandas` | 2.3.2 | 数据分析库 |

### 📊 Monitoring & Observability (监控可观测性)

#### Prometheus & 调度

| 包名 | 版本 | 用途 |
|------|------|------|
| `prometheus-client` | 0.23.1 | Prometheus 指标收集 |
| `APScheduler` | 3.11.0 | 定时任务调度 |
| `traceloop-sdk` | 0.47.0 | Traceloop 追踪 SDK |

#### OpenTelemetry Core

| 包名 | 版本 | 用途 |
|------|------|------|
| `opentelemetry-api` | 1.36.0 | OTEL API |
| `opentelemetry-sdk` | 1.36.0 | OTEL SDK |
| `opentelemetry-proto` | 1.36.0 | OTEL 协议 |
| `opentelemetry-semantic-conventions` | 0.57b0 | 语义约定 |
| `opentelemetry-semantic-conventions-ai` | 0.4.13 | AI 语义约定 |

#### OpenTelemetry Exporters

| 包名 | 版本 | 用途 |
|------|------|------|
| `opentelemetry-exporter-otlp` | 1.36.0 | OTLP 导出器 |
| `opentelemetry-exporter-otlp-proto-grpc` | 1.36.0 | gRPC 导出器 |
| `opentelemetry-exporter-otlp-proto-http` | 1.36.0 | HTTP 导出器 |
| `opentelemetry-exporter-otlp-proto-common` | 1.36.0 | 通用导出器 |

#### OpenTelemetry Instrumentation

| 包名 | 版本 | 用途 |
|------|------|------|
| `opentelemetry-instrumentation` | 0.57b0 | 基础插桩 |
| `opentelemetry-instrumentation-langchain` | 0.47.0 | LangChain 插桩 |
| `opentelemetry-instrumentation-openai` | 0.47.0 | OpenAI 插桩 |
| `opentelemetry-instrumentation-sqlalchemy` | 0.57b0 | SQLAlchemy 插桩 |
| `opentelemetry-instrumentation-requests` | 0.57b0 | Requests 插桩 |
| `opentelemetry-instrumentation-logging` | 0.57b0 | 日志插桩 |

### 🌐 HTTP & Network (网络)

| 包名 | 版本 | 用途 |
|------|------|------|
| `httpx` | 0.28.1 | 现代 HTTP 客户端 |
| `httpcore` | 1.0.9 | HTTP 核心库 |
| `requests` | 2.32.5 | HTTP 库 |
| `aiohttp` | 3.12.15 | 异步 HTTP 客户端 |

### 📝 NLP & Text Processing (文本处理)

| 包名 | 版本 | 用途 |
|------|------|------|
| `jieba` | 0.42.1 | 中文分词 |
| `rank-bm25` | 0.2.2 | BM25 排序算法 |
| `regex` | 2025.9.1 | 正则表达式增强 |

### 🛠️ Data Structures & Utilities (工具库)

| 包名 | 版本 | 用途 |
|------|------|------|
| `orjson` | 3.11.3 | 快速 JSON 库 |
| `PyYAML` | 6.0.2 | YAML 解析 |
| `tiktoken` | 0.11.0 | OpenAI tokenizer |
| `tenacity` | 9.1.2 | 重试库 |
| `jsonpatch` | 1.33 | JSON Patch |
| `jsonpointer` | 3.0.0 | JSON Pointer |

---

## 📌 重要说明

### 版本固定原则

- **严格固定版本**: 所有生产依赖使用 `==` 固定版本
- **兼容性保证**: 版本已在当前环境验证通过
- **安全性**: 使用已知安全的版本

### 懒加载依赖

以下包支持懒加载,不会在启动时加载:

- `torch` - 仅在使用本地 Embedding 模型时加载
- `sentence-transformers` - 仅在使用 HuggingFace 模型时加载
- `transformers` - 仅在需要时动态加载

### CUDA 依赖 (可选)

如果需要 GPU 加速,PyTorch 会自动安装以下 CUDA 相关包:

- `nvidia-cuda-runtime-cu12`
- `nvidia-cudnn-cu12`
- `nvidia-cublas-cu12`
- 等等...

这些包由 `torch==2.8.0` 自动管理,无需手动指定。

### 安装方式

```bash
# 基础安装
pip install -r requirements.txt

# 验证依赖
pip check

# 查看依赖树
pip list
```

### 更新策略

1. **定期更新**: 每季度检查一次安全更新
2. **测试验证**: 更新前必须在测试环境验证
3. **版本锁定**: 生产环境使用固定版本
4. **文档更新**: 更新后同步更新此文档

---

## 🔧 故障排查

### JWT 包冲突

**问题**: 安装了错误的 `jwt` 包而不是 `PyJWT`

**解决方案**:
```bash
pip uninstall -y jwt
pip install PyJWT==2.8.0
```

详见: `JWT_FIX_README.md`

### Torch CUDA 问题

**问题**: CUDA 版本不匹配

**解决方案**:
```bash
# CPU 版本
pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu

# CUDA 12.8
pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```

---

## 📅 更新日志

### 2025-01-20
- 重新整理 requirements.txt
- 添加详细分类和说明
- 验证所有版本与当前环境一致
- 添加 OpenTelemetry 完整依赖
- 添加 Anthropic Claude 支持

### 之前版本
- 初始版本依赖列表

---

**维护者**: RAG 项目团队
**最后更新**: 2025-01-20
