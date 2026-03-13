# 嵌入向量服务配置说明

## 概述

新的嵌入向量服务使用 `langchain_huggingface` 实现，支持多种后端和配置选项。

## 支持的后端

### 1. OpenAI 后端
使用 OpenAI 的嵌入 API 服务。

**配置要求：**
```bash
# 环境变量
OPENAI_API_KEY=your_api_key
OPENAI_API_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_BACKEND=openai
```

**优点：**
- 嵌入质量高
- 支持多种模型
- 无需本地计算资源

**缺点：**
- 需要网络连接
- 有API调用费用
- 数据需要发送到外部服务

### 2. HuggingFace 后端
使用本地 HuggingFace 模型。

**配置要求：**
```bash
# 环境变量
EMBEDDING_BACKEND=huggingface
HUGGINGFACE_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=auto  # 或 cpu, cuda
```

**推荐模型：**

| 模型名称 | 特点 | 适用场景 |
|---------|------|----------|
| `sentence-transformers/all-MiniLM-L6-v2` | 轻量级，速度快 | 快速原型开发 |
| `sentence-transformers/all-mpnet-base-v2` | 高质量，速度较慢 | 生产环境 |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 多语言支持 | 多语言应用 |
| `BAAI/bge-large-zh-v1.5` | 中文优化 | 中文应用 |

**优点：**
- 免费使用
- 数据隐私性好
- 可离线运行
- 支持自定义模型

**缺点：**
- 需要本地计算资源
- 首次下载模型需要时间
- 嵌入质量可能不如商业API

## 使用方法

### 基本使用

```python
from app.services.embedding import create_embedding_service

# 创建服务实例
service = create_embedding_service(
    backend="huggingface",
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"
)

# 创建单个嵌入向量
embedding = await service.create_embedding("这是一个测试文本")

# 批量创建嵌入向量
embeddings = await service.create_batch_embeddings([
    "文本1", "文本2", "文本3"
])

# 计算相似度
similarity = service.cosine_similarity(embedding1, embedding2)
```

### 高级功能

```python
# 查找最相似的向量
similar_results = service.find_most_similar(
    query_embedding, 
    candidate_embeddings, 
    top_k=5
)

# 缓存管理
service.clear_cache()
stats = service.get_cache_stats()
```

## 性能优化建议

### 1. 缓存配置
- 默认缓存大小为 1000
- 可根据内存情况调整
- 缓存使用 LRU 策略

### 2. 批量处理
- 优先使用 `create_batch_embeddings`
- 批量处理比单个处理更高效
- 自动处理缓存命中

### 3. 设备选择
- GPU: 速度快，但需要显存
- CPU: 兼容性好，速度较慢
- auto: 自动检测最佳设备

### 4. 模型选择
- 轻量级模型：适合快速开发
- 高质量模型：适合生产环境
- 多语言模型：适合国际化应用

## 故障排除

### 常见问题

1. **模型下载失败**
   - 检查网络连接
   - 使用镜像源
   - 手动下载模型

2. **内存不足**
   - 使用更小的模型
   - 减少缓存大小
   - 使用CPU而非GPU

3. **API调用失败**
   - 检查API密钥
   - 验证网络连接
   - 查看API配额

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
service = create_embedding_service(backend="huggingface")
```

## 迁移指南

### 从旧版本迁移

1. 更新依赖：
```bash
pip install -r requirements.txt
```

2. 更新环境变量：
```bash
# 添加新的配置项
EMBEDDING_BACKEND=huggingface
HUGGINGFACE_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

3. 代码无需修改，API保持兼容

### 性能对比

| 后端 | 速度 | 质量 | 成本 | 隐私 |
|------|------|------|------|------|
| OpenAI | 快 | 高 | 付费 | 低 |
| HuggingFace | 中等 | 中等 | 免费 | 高 |

## 最佳实践

1. **开发阶段**：使用 HuggingFace 后端进行快速迭代
2. **生产环境**：根据需求选择合适后端
3. **混合使用**：开发用本地模型，生产用API
4. **监控性能**：定期检查缓存命中率和响应时间
