# 多领域知识库架构方案(方案A:命名空间架构)

## 文档信息
- **方案名称**: 基于命名空间的多领域知识库架构
- **版本**: v1.0
- **创建日期**: 2025-11-17
- **目标场景**: 智能客服系统,支持多领域知识库检索

---

## 1. 架构概述

### 1.1 核心设计理念
- **逻辑隔离,物理集中**: 使用 `namespace` 字段实现领域隔离,数据存储在同一数据库中
- **向后兼容**: 现有单领域数据自动归属 `default` 命名空间
- **灵活路由**: 支持单领域检索、跨领域检索、智能领域识别三种模式
- **可扩展性**: 支持领域动态增删,无需修改数据库架构

### 1.2 适用场景
- 智能客服(产品咨询、技术支持、售后服务等多领域)
- 企业知识管理(人事、财务、技术、运营等部门知识隔离)
- 垂直行业RAG(医疗、法律、金融等多专业领域)

### 1.3 技术优势
- **低成本**: 无需部署多个向量数据库实例
- **高性能**: PostgreSQL 原生支持多租户查询,索引优化明确
- **易维护**: 统一的数据管理和备份策略
- **安全性**: 基于命名空间的权限控制

---

## 2. 数据库架构设计

### 2.1 核心字段扩展

#### 2.1.1 documents 表扩展
```
新增字段:
- namespace: VARCHAR(100) NOT NULL DEFAULT 'default'
  - 领域命名空间(如: 'product_support', 'technical_docs', 'sales')
- domain_tags: JSONB
  - 多标签支持(如: {"primary": "technical", "secondary": ["api", "backend"]})
- domain_confidence: FLOAT
  - 领域分类置信度(0.0-1.0)

索引策略:
- idx_documents_namespace: (namespace, created_at DESC)
- idx_documents_domain_tags: GIN(domain_tags)
- idx_documents_namespace_embedding: (namespace, id) INCLUDE (embedding)
```

#### 2.1.2 document_chunks 表扩展
```
新增字段:
- namespace: VARCHAR(100) NOT NULL DEFAULT 'default'
  - 继承自父文档的命名空间
- domain_tags: JSONB
  - 继承或独立的领域标签

索引策略:
- idx_chunks_namespace: (namespace, document_id)
- idx_chunks_namespace_vector: (namespace) 用于向量检索优化
```

### 2.2 领域配置表

#### 2.2.1 knowledge_domains 表(新建)
```
表结构:
- id: SERIAL PRIMARY KEY
- namespace: VARCHAR(100) UNIQUE NOT NULL
  - 命名空间唯一标识
- display_name: VARCHAR(200) NOT NULL
  - 显示名称(如: "产品支持知识库")
- description: TEXT
  - 领域描述
- keywords: JSONB
  - 关键词列表,用于快速分类
  - 格式: ["退货", "换货", "保修", "发票"]
- icon: VARCHAR(50)
  - 前端图标标识
- color: VARCHAR(20)
  - UI 主题色
- is_active: BOOLEAN DEFAULT TRUE
  - 是否启用
- priority: INTEGER DEFAULT 0
  - 排序优先级
- parent_namespace: VARCHAR(100)
  - 父领域(支持层级结构)
- permissions: JSONB
  - 权限配置
  - 格式: {"read": ["role:user"], "write": ["role:admin"]}
- metadata: JSONB
  - 扩展元数据
  - 格式: {"embedding_model": "bge-large-zh", "retrieval_config": {...}}
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

索引:
- idx_domains_namespace: (namespace)
- idx_domains_keywords: GIN(keywords)
- idx_domains_active: (is_active, priority DESC)
```

#### 2.2.2 domain_routing_rules 表(新建)
```
表结构:
- id: SERIAL PRIMARY KEY
- rule_name: VARCHAR(200) NOT NULL
  - 规则名称
- rule_type: VARCHAR(50) NOT NULL
  - 规则类型: 'keyword', 'regex', 'llm', 'hybrid'
- pattern: TEXT
  - 匹配模式
- target_namespace: VARCHAR(100)
  - 目标命名空间
- confidence_threshold: FLOAT
  - 置信度阈值
- priority: INTEGER
  - 规则优先级
- is_active: BOOLEAN DEFAULT TRUE
- metadata: JSONB
  - 规则扩展配置
- created_at: TIMESTAMP
```

### 2.3 领域关系表

#### 2.3.1 domain_relationships 表(新建,可选)
```
表结构:
- id: SERIAL PRIMARY KEY
- source_namespace: VARCHAR(100)
- related_namespace: VARCHAR(100)
- relationship_type: VARCHAR(50)
  - 关系类型: 'parent', 'sibling', 'related', 'fallback'
- weight: FLOAT DEFAULT 0.5
  - 关系权重,用于跨领域检索排序
- is_active: BOOLEAN DEFAULT TRUE

用途:
- 跨领域检索时的智能推荐
- 领域层级关系管理
- Fallback 领域配置
```

---

## 3. 领域分类系统

### 3.1 三层分类架构

#### 3.1.1 第一层:快速关键词分类器
```
工作原理:
1. 提取用户查询中的关键词
2. 匹配 knowledge_domains.keywords
3. 计算匹配得分(TF-IDF 或简单计数)
4. 如果最高得分 > 阈值(如 0.8),直接返回领域

优势:
- 延迟极低(< 10ms)
- 适用于明确领域特征的查询
- 无需 LLM 调用

缺点:
- 对模糊查询效果差
- 需要维护关键词库
```

#### 3.1.2 第二层:LLM 智能分类器
```
工作原理:
1. 构建包含所有领域描述的 Prompt
2. 调用 LLM 分类(如 Qwen-2.5, GLM-4)
3. 使用 JSON Mode 返回结构化结果
4. 返回: {namespace, confidence, reasoning}

Prompt 模板示例:
"""
你是一个领域分类专家。根据用户问题,判断属于哪个知识库领域。

可用领域:
1. product_support - 产品支持(退货、换货、保修)
2. technical_docs - 技术文档(API、SDK、配置)
3. sales - 销售咨询(价格、促销、购买)

用户问题: {query}

返回 JSON 格式:
{
  "namespace": "领域标识",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由"
}
"""

优势:
- 准确率高(> 90%)
- 理解复杂语义
- 支持多意图识别

缺点:
- 延迟较高(200-500ms)
- 需要 API 成本
```

#### 3.1.3 第三层:混合分类器(推荐)
```
工作流程:
1. 首先尝试关键词分类
2. 如果 confidence < 0.6,调用 LLM 分类
3. 如果 LLM confidence < 0.5,标记为 'uncertain'
4. uncertain 查询使用跨领域检索

fallback 策略:
- 使用 'default' 命名空间作为兜底
- 或使用最近访问的领域(基于用户会话)

性能优化:
- LLM 分类结果缓存(相似查询直接命中)
- 异步预分类(用户输入时后台预判)
```

### 3.2 分类服务设计

#### 3.2.1 DomainClassifier 类职责
```
核心方法:
- classify(query: str, context: dict) -> DomainResult
  - 统一分类接口
- classify_keyword(query: str) -> DomainResult
  - 关键词分类
- classify_llm(query: str, domains: List[Domain]) -> DomainResult
  - LLM 分类
- classify_hybrid(query: str) -> DomainResult
  - 混合分类(推荐)

辅助方法:
- extract_keywords(query: str) -> List[str]
  - 提取关键词
- calculate_keyword_score(keywords: List[str], domain: Domain) -> float
  - 计算匹配得分
- get_user_preferred_domain(user_id: int) -> str
  - 获取用户偏好领域
```

#### 3.2.2 DomainResult 数据结构
```
返回结构:
{
  "namespace": str,           # 领域标识
  "display_name": str,        # 显示名称
  "confidence": float,        # 置信度 0.0-1.0
  "method": str,              # 分类方法: 'keyword', 'llm', 'hybrid'
  "reasoning": str,           # 推理过程(可选)
  "alternatives": [           # 备选领域
    {"namespace": str, "confidence": float}
  ],
  "fallback_to_cross_domain": bool  # 是否需要跨领域检索
}
```

---

## 4. 检索流程设计

### 4.1 单领域检索流程

```
步骤 1: 查询分析
├─ 用户查询: "API 认证失败怎么办?"
├─ 领域分类: namespace='technical_docs', confidence=0.92
└─ 提取关键词: ["API", "认证", "失败"]

步骤 2: 向量检索
├─ 生成 query embedding
├─ 数据库查询:
│   SELECT * FROM document_chunks
│   WHERE namespace = 'technical_docs'
│   ORDER BY embedding <=> query_embedding
│   LIMIT 20
└─ 返回候选结果 Top-20

步骤 3: 混合检索(可选)
├─ BM25 关键词检索(namespace 过滤)
├─ 向量检索结果
└─ RRF 融合 Top-10

步骤 4: Rerank 精排
├─ 使用 bge-reranker-v2-m3
├─ 计算 query-chunk 相似度
└─ 返回 Top-5

步骤 5: 结果增强
├─ 添加来源领域标签
├─ 添加领域图标和颜色
└─ 返回给 LLM 生成答案
```

### 4.2 跨领域检索流程

```
触发条件:
- 用户显式选择"全领域检索"
- 分类器 confidence < 0.5
- 单领域检索结果 < 3 条

步骤 1: 多命名空间并行检索
├─ 领域 A: technical_docs → 5 chunks
├─ 领域 B: product_support → 3 chunks
└─ 领域 C: sales → 2 chunks

步骤 2: 领域权重调整
├─ 根据 domain_relationships.weight 调整得分
├─ 根据分类器 confidence 调整得分
└─ 公式: final_score = similarity * domain_weight * confidence

步骤 3: 全局 Rerank
├─ 对所有候选 chunks 统一 rerank
├─ 考虑领域多样性(避免单领域占据全部结果)
└─ Top-5 结果可能来自 2-3 个领域

步骤 4: 结果分组展示
├─ 按领域分组
├─ 每个领域显示 1-2 个最佳结果
└─ 前端展示领域标签
```

### 4.3 智能路由检索流程

```
场景:多轮对话中的领域切换

步骤 1: 会话上下文分析
├─ 读取 chat_sessions.metadata.current_namespace
├─ 判断本轮查询是否切换领域
└─ 示例:
    上一轮: "API 认证问题"(technical_docs)
    本轮: "退货流程"(product_support) ← 领域切换

步骤 2: 领域切换检测
├─ 对比当前分类结果与会话 namespace
├─ 如果不同 && confidence > 0.7 → 确认切换
└─ 更新 session.metadata.current_namespace

步骤 3: 动态检索策略
├─ 领域切换: 使用新领域检索
├─ 领域延续: 使用原领域 + 会话历史增强
└─ 不确定: 使用"原领域 + 新领域"双领域检索
```

---

## 5. API 接口设计

### 5.1 领域管理 API

#### 5.1.1 获取领域列表
```
GET /api/knowledge-domains

响应示例:
{
  "domains": [
    {
      "namespace": "technical_docs",
      "display_name": "技术文档",
      "description": "API、SDK、配置相关技术文档",
      "icon": "code",
      "color": "#4A90E2",
      "document_count": 245,
      "chunk_count": 1823,
      "is_active": true
    },
    {
      "namespace": "product_support",
      "display_name": "产品支持",
      "description": "退换货、保修、售后服务",
      "icon": "support",
      "color": "#F5A623",
      "document_count": 132,
      "chunk_count": 956,
      "is_active": true
    }
  ]
}
```

#### 5.1.2 创建/更新领域
```
POST /api/knowledge-domains
PUT /api/knowledge-domains/{namespace}

请求体:
{
  "namespace": "new_domain",
  "display_name": "新领域",
  "description": "描述",
  "keywords": ["关键词1", "关键词2"],
  "icon": "icon_name",
  "color": "#hex_color",
  "permissions": {
    "read": ["role:user"],
    "write": ["role:admin"]
  }
}
```

#### 5.1.3 删除领域
```
DELETE /api/knowledge-domains/{namespace}?force=false

参数:
- force: 是否强制删除(有数据时)
- migrate_to: 迁移目标领域(可选)
```

### 5.2 文档上传 API(扩展)

```
POST /api/upload

请求体(multipart/form-data):
- file: 文件
- namespace: 领域标识(新增)
- auto_classify: 是否自动分类(新增,默认 false)
- domain_tags: JSON 数组,多标签(新增)

响应:
{
  "document_id": 123,
  "namespace": "technical_docs",
  "domain_confidence": 0.88,
  "suggested_tags": ["api", "authentication"],
  "chunk_count": 15
}
```

### 5.3 查询 API(扩展)

#### 5.3.1 智能检索
```
POST /api/query

请求体:
{
  "query": "用户问题",
  "namespace": "technical_docs",  # 可选,指定领域
  "retrieval_mode": "single",     # single/cross/auto
  "session_id": "xxx",            # 会话 ID(用于上下文)
  "top_k": 5
}

响应:
{
  "results": [
    {
      "chunk_id": 456,
      "content": "...",
      "score": 0.92,
      "namespace": "technical_docs",
      "domain_display_name": "技术文档",
      "domain_color": "#4A90E2",
      "document_title": "API 认证指南",
      "metadata": {...}
    }
  ],
  "domain_classification": {
    "namespace": "technical_docs",
    "confidence": 0.88,
    "method": "hybrid"
  },
  "cross_domain_results": [...]  # 如果启用跨领域
}
```

#### 5.3.2 领域分类预测(独立接口)
```
POST /api/classify-domain

请求体:
{
  "query": "用户问题",
  "method": "hybrid"  # keyword/llm/hybrid
}

响应:
{
  "namespace": "technical_docs",
  "display_name": "技术文档",
  "confidence": 0.88,
  "method": "hybrid",
  "reasoning": "查询包含'API'、'认证'等技术关键词",
  "alternatives": [
    {"namespace": "product_support", "confidence": 0.12}
  ]
}
```

### 5.4 会话 API(扩展)

```
POST /api/chat/sessions

新增字段:
{
  "title": "会话标题",
  "metadata": {
    "current_namespace": "technical_docs",  # 当前领域
    "namespace_history": [                   # 领域切换历史
      {"namespace": "sales", "timestamp": "2025-01-15T10:00:00Z"},
      {"namespace": "technical_docs", "timestamp": "2025-01-15T10:05:00Z"}
    ]
  }
}
```

---

## 6. 前端集成设计

### 6.1 领域选择器组件

#### 6.1.1 DomainSelector.vue
```
功能:
- 显示所有可用领域(带图标和颜色)
- 支持单选/多选模式
- 显示每个领域的文档数量
- 实时预测用户输入的可能领域

位置:
- 查询输入框上方
- 文档上传页面
- 管理后台
```

#### 6.1.2 DomainBadge.vue
```
功能:
- 显示领域标签(带颜色和图标)
- 显示置信度(可选)
- 支持点击切换到该领域

位置:
- 检索结果项
- 文档列表
- 聊天消息
```

### 6.2 管理后台页面

#### 6.2.1 领域管理页面
```
功能模块:
1. 领域列表
   - 表格展示所有领域
   - 显示文档数、分块数、状态
   - 快速启用/禁用

2. 创建/编辑领域
   - 表单填写基本信息
   - 关键词编辑器(Tag 输入)
   - 图标和颜色选择器
   - 权限配置

3. 领域数据统计
   - 每个领域的文档数趋势图
   - 检索命中率统计
   - 领域切换流向图(Sankey)

4. 分类规则管理
   - 添加/编辑分类规则
   - 测试分类效果
   - 规则优先级调整
```

#### 6.2.2 文档领域管理
```
功能:
- 批量修改文档的 namespace
- 自动分类已上传文档
- 领域迁移工具
- 领域数据导出/导入
```

### 6.3 用户端交互

#### 6.3.1 智能推荐
```
场景 1: 输入提示
- 用户输入时,后台异步预测领域
- 输入框下方显示:"建议在 [技术文档] 中搜索"

场景 2: 无结果提示
- 单领域检索无结果
- 提示:"在 [技术文档] 中未找到结果,是否尝试 [全领域检索]?"

场景 3: 领域切换提示
- 检测到领域切换
- 提示:"已切换到 [产品支持] 领域"
```

#### 6.3.2 结果展示
```
多领域结果分组:
┌─────────────────────────────────────┐
│ 🔧 技术文档 (3 条结果)              │
├─────────────────────────────────────┤
│ [结果 1] API 认证指南 - 相似度 0.92 │
│ [结果 2] SDK 集成文档 - 相似度 0.86 │
│ [结果 3] ...                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🛒 产品支持 (2 条结果)              │
├─────────────────────────────────────┤
│ [结果 1] 退货流程说明 - 相似度 0.78 │
│ [结果 2] ...                        │
└─────────────────────────────────────┘
```

---

## 7. 权限与安全设计

### 7.1 领域级权限控制

```
权限模型:
- 角色 → 领域权限映射
- 支持 read/write/admin 三级权限
- 支持用户组和角色继承

配置示例:
knowledge_domains.permissions = {
  "read": ["role:user", "role:guest"],
  "write": ["role:admin", "role:editor"],
  "admin": ["role:super_admin"]
}

检查逻辑:
1. 用户请求检索 namespace='sensitive_docs'
2. 查询 knowledge_domains 的 permissions
3. 验证 current_user.roles 是否包含授权角色
4. 如果无权限,返回 403 或过滤该领域
```

### 7.2 数据隔离保证

```
SQL 注入防护:
- 使用参数化查询
- namespace 字段严格验证(只允许 [a-z0-9_-])

跨领域访问控制:
- 所有检索查询强制添加 namespace 过滤
- ORM 层级别的 namespace 过滤器

审计日志:
- 记录领域访问日志
- 记录领域切换行为
- 记录敏感领域的查询内容
```

### 7.3 敏感领域保护

```
特殊领域标记:
- is_sensitive: BOOLEAN 字段
- require_mfa: BOOLEAN(是否需要多因素认证)

敏感领域策略:
1. 结果脱敏:敏感字段用 *** 替换
2. 水印添加:结果中注入用户标识水印
3. 访问限制:IP 白名单、时间窗口限制
4. 审计增强:记录完整查询和结果
```

---

## 8. 性能优化策略

### 8.1 数据库优化

#### 8.1.1 索引策略
```
单领域检索优化:
- CREATE INDEX idx_chunks_namespace_vector
  ON document_chunks (namespace)
  WHERE embedding IS NOT NULL;

跨领域检索优化:
- 分区表(按 namespace 分区,适用于海量数据)
- CREATE TABLE document_chunks_technical PARTITION OF document_chunks
  FOR VALUES IN ('technical_docs');

向量检索优化:
- 使用 IVFFlat 索引(如果使用 pgvector)
- CREATE INDEX idx_embedding_ivfflat
  ON document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

#### 8.1.2 查询优化
```
减少全表扫描:
- WHERE namespace IN ('domain1', 'domain2') 使用索引
- EXPLAIN ANALYZE 验证执行计划

结果缓存:
- 缓存热门查询的检索结果(Redis)
- Key: hash(query + namespace + top_k)
- TTL: 5 分钟

连接池:
- 增加数据库连接池大小
- 针对检索查询使用只读副本
```

### 8.2 分类器优化

#### 8.2.1 关键词分类加速
```
预构建索引:
- 启动时加载所有领域的关键词到内存
- 使用 Trie 树或 Aho-Corasick 算法快速匹配

缓存策略:
- 缓存最近 1000 条查询的分类结果
- LRU 淘汰策略
```

#### 8.2.2 LLM 分类优化
```
批量分类:
- 收集 10 个查询,批量调用 LLM
- 适用于后台任务(如文档自动分类)

模型优化:
- 使用轻量级分类模型(如 1.8B 参数)
- 本地部署避免网络延迟

Prompt 缓存:
- LLM 的领域描述部分使用 Prompt Cache(Anthropic)
- 减少 Token 消耗和延迟
```

### 8.3 检索性能优化

#### 8.3.1 并行检索
```
跨领域并行:
- 使用 asyncio.gather 并行查询多个领域
- 每个领域独立数据库连接

代码示例(伪代码):
async def cross_domain_search(query, namespaces):
    tasks = [
        search_single_domain(query, ns)
        for ns in namespaces
    ]
    results = await asyncio.gather(*tasks)
    return merge_and_rerank(results)
```

#### 8.3.2 Rerank 优化
```
分阶段 Rerank:
1. 粗排:向量检索 Top-50
2. 细排:Rerank Top-10(减少计算量)

批量推理:
- Rerank 模型批量处理(batch_size=32)
- GPU 加速

Early Stop:
- 如果 Top-1 得分 > 0.95,直接返回
```

### 8.4 缓存策略

```
多层缓存:
1. L1: 内存缓存(LRU, 1000 条)
   - 分类结果
   - 热门查询结果

2. L2: Redis 缓存(1 小时)
   - 检索结果
   - 领域配置

3. L3: CDN 缓存(1 天)
   - 领域列表
   - 静态资源

缓存失效:
- 文档更新时,清除相关领域的缓存
- 领域配置更新时,清除 L2/L3 缓存
```

---

## 9. 监控与可观测性

### 9.1 关键指标

#### 9.1.1 业务指标
```
领域使用统计:
- 每个领域的查询量(QPS)
- 每个领域的命中率
- 领域切换频率

分类准确性:
- 关键词分类准确率(人工标注样本)
- LLM 分类准确率
- 混合分类器的 Fallback 率

用户体验:
- 平均响应时间(P50, P95, P99)
- 跨领域检索的使用率
- 无结果查询的比例
```

#### 9.1.2 技术指标
```
数据库性能:
- 向量检索延迟(按 namespace 统计)
- 数据库连接池使用率
- 慢查询日志(> 1s)

LLM 性能:
- 分类 API 调用延迟
- Token 消耗统计
- 分类失败率

缓存效率:
- 缓存命中率
- 缓存内存使用
```

### 9.2 监控大盘

#### 9.2.1 领域健康度大盘
```
展示内容:
- 每个领域的文档数趋势
- 每个领域的查询量热力图
- 领域分类准确率雷达图
- 跨领域检索流向图(Sankey)

告警规则:
- 某领域查询失败率 > 5%
- 分类器 confidence < 0.3 的查询占比 > 10%
- 数据库连接池耗尽
```

#### 9.2.2 用户行为分析
```
分析维度:
- 用户最常访问的领域
- 领域切换路径分析
- 查询意图分布(按领域)

可视化:
- 用户领域访问热力图
- 领域切换桑基图
- 时间序列趋势图
```

### 9.3 日志与追踪

```
结构化日志:
{
  "event": "domain_classification",
  "query": "API 认证失败",
  "result": {
    "namespace": "technical_docs",
    "confidence": 0.88,
    "method": "hybrid"
  },
  "latency_ms": 45,
  "user_id": 123,
  "session_id": "xxx"
}

分布式追踪:
- 使用 OpenTelemetry
- Trace: 查询 → 分类 → 检索 → Rerank → 生成
- 每个 Span 记录 namespace 信息
```

---

## 10. 实施路线图

### 10.1 第一阶段:基础架构(2-3 周)

#### 10.1.1 Week 1: 数据库改造
```
任务:
✅ 扩展 documents 和 document_chunks 表
✅ 创建 knowledge_domains 表
✅ 创建必要索引
✅ 数据迁移脚本(将现有数据标记为 'default')
✅ 编写数据库单元测试

交付物:
- 数据库迁移脚本(Alembic)
- 数据库架构文档
- 单元测试覆盖率 > 80%
```

#### 10.1.2 Week 2-3: 领域管理功能
```
任务:
✅ 实现领域 CRUD API
✅ 开发 DomainService 服务层
✅ 前端领域管理页面
✅ 领域选择器组件
✅ 文档上传支持 namespace 参数

交付物:
- 领域管理 API 文档
- 前端管理界面
- Postman 测试集合
```

### 10.2 第二阶段:智能分类(2-3 周)

#### 10.2.1 Week 1: 关键词分类器
```
任务:
✅ 实现 DomainClassifier 基础类
✅ 实现 classify_keyword 方法
✅ 领域关键词配置界面
✅ 分类效果测试工具

交付物:
- DomainClassifier 服务
- 关键词配置管理页面
- 分类准确率测试报告
```

#### 10.2.2 Week 2: LLM 分类器
```
任务:
✅ 实现 classify_llm 方法
✅ Prompt 工程和优化
✅ 集成 LLM API(支持多提供商)
✅ 分类结果缓存(Redis)

交付物:
- LLM 分类器实现
- Prompt 模板库
- 性能测试报告(延迟、准确率)
```

#### 10.2.3 Week 3: 混合分类器
```
任务:
✅ 实现 classify_hybrid 方法
✅ Fallback 策略优化
✅ 分类结果日志和分析
✅ A/B 测试框架

交付物:
- 混合分类器实现
- 分类策略配置文档
- A/B 测试报告
```

### 10.3 第三阶段:检索集成(2 周)

#### 10.3.1 Week 1: 单领域检索
```
任务:
✅ 修改检索 API 支持 namespace 参数
✅ 更新 VectorRetrieval 服务
✅ 添加领域过滤逻辑
✅ 前端查询界面集成领域选择器

交付物:
- 领域检索 API(v2)
- 前端检索界面更新
- 检索性能对比报告
```

#### 10.3.2 Week 2: 跨领域检索
```
任务:
✅ 实现跨领域并行检索
✅ RRF 融合算法优化
✅ 结果分组和展示
✅ 领域权重配置

交付物:
- 跨领域检索实现
- 结果展示组件
- 用户体验测试报告
```

### 10.4 第四阶段:高级特性(3-4 周)

#### 10.4.1 权限与安全
```
任务:
✅ 领域级权限控制
✅ 敏感领域保护
✅ 审计日志系统
✅ 安全测试(渗透测试)

交付物:
- 权限管理文档
- 安全审计报告
- 合规性检查清单
```

#### 10.4.2 监控与优化
```
任务:
✅ 监控指标采集
✅ Grafana 大盘配置
✅ 告警规则配置
✅ 性能调优(索引、缓存)

交付物:
- 监控大盘
- 告警手册
- 性能优化报告
```

#### 10.4.3 高级功能
```
任务:
✅ 领域关系管理(domain_relationships)
✅ 智能领域推荐
✅ 会话领域上下文
✅ 领域数据分析报表

交付物:
- 高级功能文档
- 数据分析报表
- 用户使用手册
```

---

## 11. 风险与挑战

### 11.1 技术风险

#### 11.1.1 性能风险
```
风险描述:
- 跨领域检索可能导致延迟增加(N 倍领域数量)
- PostgreSQL ARRAY 向量检索性能不如专用向量库

缓解措施:
- 使用并行查询 + 超时控制(单领域 500ms,总超时 2s)
- 后续可迁移到 Milvus/Qdrant(namespace 作为 partition)
- 智能分类器尽量避免不必要的跨领域检索
```

#### 11.1.2 分类准确性风险
```
风险描述:
- 关键词分类对模糊查询效果差
- LLM 分类可能出现幻觉或误判

缓解措施:
- 提供用户手动校正分类的界面
- 记录分类错误,持续优化关键词库和 Prompt
- 低 confidence 查询自动使用跨领域检索
```

### 11.2 业务风险

#### 11.2.1 用户体验风险
```
风险描述:
- 领域选择增加用户操作成本
- 跨领域结果混杂可能降低精准度

缓解措施:
- 默认使用智能分类,用户无需手动选择
- 跨领域结果明确分组展示,避免混淆
- 提供"快速切换"功能(一键切换到建议领域)
```

#### 11.2.2 数据质量风险
```
风险描述:
- 历史文档未标注 namespace,需要批量分类
- 自动分类可能产生错误标注

缓解措施:
- 提供批量自动分类 + 人工审核工具
- 分阶段迁移:先标注明确文档,再处理模糊文档
- 支持文档多标签(domain_tags),减少分类压力
```

### 11.3 运维风险

#### 11.3.1 迁移风险
```
风险描述:
- 数据库迁移可能失败或数据丢失
- 迁移期间服务中断

缓解措施:
- 迁移前完整备份
- 使用 Blue-Green 部署(新旧版本并行)
- 提供回滚脚本和回滚预案
- 分阶段迁移:先灰度 10% 用户,逐步放量
```

#### 11.3.2 兼容性风险
```
风险描述:
- 旧版 API 客户端无法识别 namespace 参数
- 前端未更新导致功能不可用

缓解措施:
- 保留 v1 API(自动使用 'default' namespace)
- 新增 v2 API,逐步迁移客户端
- 前端增加版本检测和降级逻辑
```

---

## 12. 成功指标

### 12.1 技术指标

```
性能指标:
✅ 单领域检索延迟 P95 < 500ms
✅ 跨领域检索延迟 P95 < 1.5s
✅ 分类器延迟 P95 < 100ms(关键词) / 300ms(LLM)
✅ 数据库查询 QPS > 500

准确性指标:
✅ 分类准确率 > 85%(人工标注测试集)
✅ 检索召回率 > 90%(单领域)
✅ 跨领域检索精准度 > 80%
```

### 12.2 业务指标

```
用户体验:
✅ 用户主动使用领域选择功能的比例 > 30%
✅ 跨领域检索的使用率 < 20%(说明分类准确)
✅ 查询无结果率下降 > 30%

效率提升:
✅ 领域内检索精准度提升 > 25%(对比全局检索)
✅ 用户平均解决问题时间缩短 > 20%
✅ 客服工单量下降 > 15%
```

### 12.3 数据指标

```
领域覆盖:
✅ 所有领域文档数量均衡(最大/最小比 < 5:1)
✅ 长尾领域查询量 > 总量的 10%(避免冷数据)

系统健康:
✅ 领域查询失败率 < 1%
✅ 分类器 fallback 率 < 15%
✅ 数据库慢查询(>1s)占比 < 0.1%
```

---

## 13. 未来扩展方向

### 13.1 智能推荐

```
功能描述:
- 根据用户历史查询,智能推荐相关领域
- 跨领域知识关联挖掘(如:"API 认证"关联"账号管理")

实现思路:
- 使用协同过滤算法分析用户行为
- 构建领域知识图谱(Domain Knowledge Graph)
- LLM 生成跨领域关联建议
```

### 13.2 多模态领域

```
功能描述:
- 支持图片、视频等多模态文档分类
- 视觉领域(如:"产品外观"、"UI 设计")

实现思路:
- 使用 CLIP 等多模态模型提取特征
- 扩展 namespace 支持 multimodal_type 字段
- 前端支持多模态检索结果展示
```

### 13.3 联邦学习

```
功能描述:
- 多租户场景下,共享通用领域,隔离私有领域
- 跨组织协作(如:多个子公司共享基础知识,保留专有知识)

实现思路:
- namespace 支持层级结构(如: 'global.technical', 'company_a.technical')
- 联邦检索:先查私有领域,再查共享领域
- 权限细粒度控制(组织级、项目级)
```

### 13.4 自动化运维

```
功能描述:
- 自动检测领域数据不平衡,建议补充文档
- 自动优化关键词库(基于分类错误日志)
- 自动调整领域权重(基于查询效果反馈)

实现思路:
- 定时任务分析领域健康度
- LLM 生成优化建议报告
- 管理员审核后一键执行优化
```

---

## 14. 参考资料

### 14.1 技术文档
- PostgreSQL Multi-tenancy Best Practices
- OpenAI Embeddings API
- BGE Embedding Models (BAAI)
- BM25 + Vector Hybrid Search (Reciprocal Rank Fusion)

### 14.2 相关论文
- "REALM: Retrieval-Augmented Language Model Pre-Training"
- "Dense Passage Retrieval for Open-Domain Question Answering"
- "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT"

### 14.3 开源项目
- LangChain (Multi-index Retrieval)
- LlamaIndex (Namespace Support)
- Haystack (Multi-domain Pipelines)

---

## 15. 附录

### 15.1 术语表

| 术语 | 解释 |
|------|------|
| Namespace | 命名空间,用于逻辑隔离不同领域的数据 |
| Domain | 领域,业务上的知识分类(如:技术文档、产品支持) |
| Cross-domain Retrieval | 跨领域检索,在多个领域中同时搜索 |
| RRF | Reciprocal Rank Fusion,倒数排名融合算法 |
| Rerank | 重排序,使用更精细的模型对粗排结果进行精排 |
| Hybrid Search | 混合检索,结合 BM25 关键词和向量语义检索 |

### 15.2 配置示例

#### 15.2.1 领域配置(YAML)
```yaml
domains:
  - namespace: technical_docs
    display_name: 技术文档
    keywords:
      - API
      - SDK
      - 接口
      - 配置
      - 部署
    classifier:
      keyword_threshold: 0.7
      llm_model: qwen-plus
      llm_temperature: 0.1
    retrieval:
      top_k: 10
      rerank: true
      hybrid_alpha: 0.3  # BM25 权重

  - namespace: product_support
    display_name: 产品支持
    keywords:
      - 退货
      - 换货
      - 保修
      - 发票
    classifier:
      keyword_threshold: 0.8
    retrieval:
      top_k: 5
      rerank: true
```

### 15.3 API 完整示例

#### 15.3.1 智能检索完整请求/响应
```json
// 请求
POST /api/query/v2
{
  "query": "如何集成支付 API?",
  "retrieval_mode": "auto",
  "session_id": "session_123",
  "user_id": 456,
  "top_k": 5,
  "include_cross_domain": true,
  "filters": {
    "date_range": {"start": "2025-01-01", "end": "2025-12-31"}
  }
}

// 响应
{
  "query_id": "query_789",
  "domain_classification": {
    "namespace": "technical_docs",
    "display_name": "技术文档",
    "confidence": 0.92,
    "method": "hybrid",
    "reasoning": "查询包含'集成'、'API'等技术关键词",
    "latency_ms": 45,
    "alternatives": [
      {"namespace": "product_support", "confidence": 0.08}
    ]
  },
  "results": [
    {
      "chunk_id": 1234,
      "content": "支付 API 集成步骤:\n1. 申请商户号\n2. 配置回调地址...",
      "score": 0.95,
      "namespace": "technical_docs",
      "domain_display_name": "技术文档",
      "domain_color": "#4A90E2",
      "domain_icon": "code",
      "document_id": 567,
      "document_title": "支付 API 集成指南",
      "source_file": "payment_api_guide.pdf",
      "page_number": 5,
      "metadata": {
        "author": "技术团队",
        "version": "v2.1",
        "last_updated": "2025-01-10"
      },
      "highlights": [
        "支付 <em>API</em> 集成步骤"
      ]
    },
    // ... 更多结果
  ],
  "cross_domain_results": [
    {
      "namespace": "product_support",
      "display_name": "产品支持",
      "count": 2,
      "top_result": {
        "chunk_id": 5678,
        "content": "支付常见问题...",
        "score": 0.72
      }
    }
  ],
  "retrieval_stats": {
    "total_candidates": 50,
    "reranked": true,
    "latency_ms": 320,
    "breakdown": {
      "embedding": 15,
      "vector_search": 120,
      "rerank": 180,
      "formatting": 5
    }
  },
  "suggestions": [
    "您可能还想了解: 支付回调处理",
    "相关文档: 退款 API 说明"
  ]
}
```

---

## 文档版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-17 | 初始版本,完整架构大纲 | Claude |

---

**备注**: 本文档为架构设计大纲,不包含具体代码实现。实施时请结合项目实际情况调整。