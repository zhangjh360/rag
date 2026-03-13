# 查询接口改进说明

## 概述

为了保持与现有前端的兼容性，我们直接改进了原有的 `/query` 接口，而不是创建新的接口。这样您的前端代码无需任何修改。

## 主要改进

### 1. 解决截断问题 ✅

**之前的问题**：
```python
def format_context(self, documents: list) -> str:
    context_parts = []
    for doc in documents:
        context_parts.append(f"文档: {doc['filename']}\n内容: {doc['content'][:500]}...")  # 只取前500字符
    return "\n\n".join(context_parts)
```

**现在的解决方案**：
```python
def format_context(self, documents: list, query_text: str = "") -> str:
    """智能格式化上下文，避免截断重要信息"""
    # 1. 智能提取相关内容
    relevant_content = self._extract_relevant_content(content, query_text)
    
    # 2. 动态管理上下文长度
    if current_length + len(doc_content) > max_context_length:
        # 智能截断，保留最相关的内容
    
    # 3. 按相关性排序，优先保留重要信息
```

### 2. 智能内容提取

现在系统会：
- 分析查询关键词
- 从文档中找到最相关的句子
- 按相关性得分排序
- 优先保留包含关键词的内容

### 3. 上下文长度管理

- 最大上下文长度：4000字符
- 动态调整，避免超出LLM限制
- 智能截断，保留最相关信息

### 4. 可选的文档分块功能

通过环境变量控制是否启用文档分块检索：

```bash
# 启用文档分块检索（推荐用于长文档）
USE_CHUNK_RETRIEVAL=true

# 使用传统文档检索（默认）
USE_CHUNK_RETRIEVAL=false
```

## 使用方法

### 1. 保持现有前端代码不变

您的前端代码无需任何修改，继续使用：

```javascript
// 前端代码保持不变
const response = await fetch('/api/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: "您的问题"
    })
});

const result = await response.json();
// result.response - 回答
// result.sources - 源文档信息
```

### 2. 环境变量配置

在 `.env` 文件中添加：

```bash
# 是否启用文档分块检索
USE_CHUNK_RETRIEVAL=false

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 3. 响应格式保持不变

```json
{
    "response": "生成的回答",
    "sources": [
        {
            "id": 1,
            "filename": "文档.pdf",
            "similarity": 0.85,
            "content_preview": "文档内容预览...",
            "is_chunk": false
        }
    ]
}
```

## 性能改进

### 1. 智能内容提取

- 不再简单截取前500字符
- 根据查询内容智能选择相关片段
- 提高检索准确性

### 2. 上下文优化

- 动态管理上下文长度
- 避免超出LLM限制
- 提高生成质量

### 3. 日志记录

- 记录处理时间
- 记录上下文长度
- 记录检索方法

## 配置选项

### 1. 传统模式（默认）

```bash
USE_CHUNK_RETRIEVAL=false
```

- 使用传统文档检索
- 适合短文档
- 性能较好

### 2. 分块模式（推荐）

```bash
USE_CHUNK_RETRIEVAL=true
```

- 使用文档分块检索
- 适合长文档
- 更精确的匹配

## 日志示例

```
2024-01-01 12:00:00 - app - INFO - 使用传统文档检索
2024-01-01 12:00:01 - app - INFO - 格式化上下文完成，长度: 3500 字符
2024-01-01 12:00:02 - app - INFO - 查询处理完成，处理时间: 1.234s，上下文长度: 3500，检索方法: document
```

## 向后兼容性

✅ **完全向后兼容**
- API接口路径不变：`/api/query`
- 请求格式不变：`{"query": "问题"}`
- 响应格式不变：`{"response": "回答", "sources": [...]}`
- 前端代码无需修改

## 测试建议

### 1. 测试截断问题解决

上传一个长文档，查询文档后面的内容，验证是否能正确找到相关信息。

### 2. 测试性能

比较启用和禁用分块检索的性能差异：

```bash
# 测试传统模式
USE_CHUNK_RETRIEVAL=false

# 测试分块模式
USE_CHUNK_RETRIEVAL=true
```

### 3. 监控日志

查看日志中的处理时间和上下文长度信息。

## 总结

通过这次改进，您的查询系统现在可以：

1. **✅ 解决截断问题**：智能提取相关内容，不再简单截取前500字符
2. **✅ 提高准确性**：根据查询内容找到最相关的文档片段
3. **✅ 保持兼容性**：前端代码无需任何修改
4. **✅ 灵活配置**：可选择传统模式或分块模式
5. **✅ 性能监控**：详细的日志记录

现在您可以测试改进后的查询功能，应该能明显感受到检索准确性的提升！
