# 第四阶段:高级特性详细任务

## 阶段概览

**阶段名称**: 高级特性与优化
**预计工期**: 3-4 周
**目标**: 权限控制、监控告警、Rerank精排、高级功能
**前置条件**: 第三阶段完成,基础检索功能可用

---

## Week 1: 权限与安全

### 任务 8.1: 领域级权限控制

**优先级**: P0
**预计时间**: 2 天
**依赖**: 第三阶段完成

#### 子任务清单

1. **实现权限检查服务**

   文件: `backend/app/services/domain_permission_service.py` (新建)

   - [ ] **DomainPermissionService 类**
     ```python
     from typing import List, Optional
     from app.models.user import User
     from app.models.knowledge_domain import KnowledgeDomain

     class DomainPermissionService:
         """领域权限服务"""

         def __init__(self, db: Session):
             self.db = db

         async def check_permission(
             self,
             user: User,
             namespace: str,
             action: str  # 'read', 'write', 'admin'
         ) -> bool:
             """
             检查用户对领域的权限

             权限规则:
             1. super_admin 拥有所有权限
             2. 检查领域的 permissions 配置
             3. 检查用户角色是否在授权列表中
             """

             # 1. Super Admin 全权限
             if user.is_super_admin:
                 return True

             # 2. 查询领域配置
             domain = self.db.query(KnowledgeDomain).filter(
                 KnowledgeDomain.namespace == namespace
             ).first()

             if not domain:
                 # 领域不存在,拒绝访问
                 return False

             if not domain.is_active:
                 # 领域已禁用,拒绝访问
                 return False

             # 3. 检查权限配置
             permissions = domain.permissions or {}
             allowed_roles = permissions.get(action, [])

             if len(allowed_roles) == 0:
                 # 未配置权限,默认允许
                 return True

             # 4. 检查用户角色
             user_roles = [role.name for role in user.roles]

             for role_spec in allowed_roles:
                 # 支持格式: 'role:admin', 'user:123', 'group:developers'
                 if role_spec.startswith('role:'):
                     role_name = role_spec[5:]
                     if role_name in user_roles:
                         return True

                 elif role_spec.startswith('user:'):
                     user_id = int(role_spec[5:])
                     if user.id == user_id:
                         return True

                 elif role_spec.startswith('group:'):
                     # 预留:用户组功能
                     pass

             return False

         async def get_accessible_domains(
             self,
             user: User,
             action: str = 'read'
         ) -> List[KnowledgeDomain]:
             """获取用户可访问的领域列表"""

             # Super Admin 可访问所有领域
             if user.is_super_admin:
                 return self.db.query(KnowledgeDomain).filter(
                     KnowledgeDomain.is_active == True
                 ).all()

             # 查询所有活跃领域
             domains = self.db.query(KnowledgeDomain).filter(
                 KnowledgeDomain.is_active == True
             ).all()

             # 过滤有权限的领域
             accessible = []
             for domain in domains:
                 if await self.check_permission(user, domain.namespace, action):
                     accessible.append(domain)

             return accessible

         async def filter_results_by_permission(
             self,
             user: User,
             results: List[Tuple[DocumentChunk, str, float]]
         ) -> List[Tuple[DocumentChunk, str, float]]:
             """过滤检索结果,移除无权访问的领域"""

             filtered = []

             for chunk, namespace, score in results:
                 if await self.check_permission(user, namespace, 'read'):
                     filtered.append((chunk, namespace, score))

             return filtered
     ```

2. **集成到查询 API**

   文件: `backend/app/routers/query.py`

   - [ ] **添加权限检查**
     ```python
     @router.post("/query/v2")
     async def query_documents_v2(
         request: QueryRequest,
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         permission_service = DomainPermissionService(db)

         # 1. 检查指定领域的读权限
         if request.namespace:
             has_permission = await permission_service.check_permission(
                 current_user,
                 request.namespace,
                 'read'
             )

             if not has_permission:
                 raise HTTPException(
                     status_code=403,
                     detail=f"无权访问领域: {request.namespace}"
                 )

         # 2. 执行检索
         # ...

         # 3. 过滤结果(移除无权访问的领域)
         if retrieval_mode == 'cross':
             results_with_namespace = await permission_service.filter_results_by_permission(
                 current_user,
                 results_with_namespace
             )

         return response
     ```

3. **集成到上传 API**

   文件: `backend/app/routers/upload.py`

   - [ ] **添加写权限检查**
     ```python
     @router.post("/upload")
     async def upload_document(
         file: UploadFile,
         namespace: Optional[str] = Form('default'),
         ...
     ):
         permission_service = DomainPermissionService(db)

         # 检查写权限
         has_permission = await permission_service.check_permission(
             current_user,
             namespace,
             'write'
         )

         if not has_permission:
             raise HTTPException(
                 status_code=403,
                 detail=f"无权向领域上传文档: {namespace}"
             )

         # 继续上传流程
         # ...
     ```

4. **前端:领域列表过滤**

   文件: `frontend/src/components/domain/DomainSelector.vue`

   - [ ] **只显示有权访问的领域**
     ```javascript
     const loadDomains = async () => {
       try {
         // API 会自动过滤无权访问的领域
         const response = await getDomains({
           include_inactive: false,
           accessible_only: true  // 新参数
         })
         domains.value = response.data
       } catch (error) {
         console.error('加载领域失败', error)
       }
     }
     ```

**交付物**:
- ✅ DomainPermissionService 实现
- ✅ 查询和上传 API 权限集成
- ✅ 前端领域过滤

---

### 任务 8.2: 敏感领域保护

**优先级**: P1
**预计时间**: 1.5 天
**依赖**: 任务 8.1

#### 子任务清单

1. **添加敏感标记字段**

   - [ ] **数据库迁移**
     ```sql
     ALTER TABLE knowledge_domains
     ADD COLUMN is_sensitive BOOLEAN DEFAULT FALSE,
     ADD COLUMN require_mfa BOOLEAN DEFAULT FALSE,
     ADD COLUMN ip_whitelist JSONB DEFAULT '[]';
     ```

2. **敏感领域访问控制**

   文件: `backend/app/services/domain_permission_service.py`

   - [ ] **增强权限检查**
     ```python
     async def check_sensitive_domain_access(
         self,
         user: User,
         domain: KnowledgeDomain,
         request: Request
     ) -> Tuple[bool, Optional[str]]:
         """
         检查敏感领域访问

         Returns:
             (is_allowed, reason)
         """

         if not domain.is_sensitive:
             return True, None

         # 1. MFA 检查
         if domain.require_mfa:
             if not user.mfa_verified:
                 return False, "敏感领域需要多因素认证"

         # 2. IP 白名单检查
         if domain.ip_whitelist and len(domain.ip_whitelist) > 0:
             client_ip = request.client.host

             if client_ip not in domain.ip_whitelist:
                 logger.warning(
                     f"IP {client_ip} 尝试访问敏感领域 {domain.namespace}"
                 )
                 return False, f"IP {client_ip} 不在白名单中"

         # 3. 时间窗口检查(可选)
         # ...

         return True, None
     ```

3. **结果脱敏**

   文件: `backend/app/services/result_sanitizer.py` (新建)

   - [ ] **脱敏服务**
     ```python
     class ResultSanitizer:
         """结果脱敏服务"""

         @staticmethod
         def sanitize_sensitive_content(
             content: str,
             sensitivity_level: str = 'high'
         ) -> str:
             """脱敏敏感内容"""

             if sensitivity_level == 'high':
                 # 高敏感:替换敏感词
                 patterns = [
                     (r'\d{11}', '***********'),  # 手机号
                     (r'\d{17}[\dXx]', '******************'),  # 身份证
                     (r'\d{16,19}', '****************'),  # 银行卡
                     (r'[\w.-]+@[\w.-]+', '***@***'),  # 邮箱
                 ]

                 for pattern, replacement in patterns:
                     content = re.sub(pattern, replacement, content)

             elif sensitivity_level == 'medium':
                 # 中敏感:部分遮蔽
                 # ...
                 pass

             return content
     ```

4. **审计日志**

   文件: `backend/app/services/audit_logger.py` (新建)

   - [ ] **审计日志服务**
     ```python
     class AuditLogger:
         """审计日志"""

         @staticmethod
         async def log_sensitive_access(
             user: User,
             domain: KnowledgeDomain,
             action: str,
             query: Optional[str],
             ip: str,
             success: bool
         ):
             """记录敏感领域访问日志"""

             log_entry = AuditLog(
                 user_id=user.id,
                 username=user.username,
                 domain_namespace=domain.namespace,
                 action=action,
                 query_content=query,
                 ip_address=ip,
                 success=success,
                 timestamp=datetime.utcnow()
             )

             db.add(log_entry)
             db.commit()

             # 同时记录到文件
             logger.info(
                 f"[AUDIT] User={user.username} Domain={domain.namespace} "
                 f"Action={action} IP={ip} Success={success}"
             )
     ```

**交付物**:
- ✅ 敏感领域标记字段
- ✅ 敏感访问控制
- ✅ 结果脱敏服务
- ✅ 审计日志

---

## Week 2: 监控与可观测性

### 任务 9.1: 指标采集系统

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 8.2

#### 子任务清单

1. **Prometheus 指标导出**

   文件: `backend/app/monitoring/metrics.py` (新建)

   - [ ] **定义指标**
     ```python
     from prometheus_client import Counter, Histogram, Gauge

     # 领域查询指标
     domain_query_total = Counter(
         'domain_query_total',
         'Total number of queries per domain',
         ['namespace', 'retrieval_mode']
     )

     domain_query_latency = Histogram(
         'domain_query_latency_seconds',
         'Query latency per domain',
         ['namespace'],
         buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
     )

     domain_classification_accuracy = Gauge(
         'domain_classification_accuracy',
         'Classification accuracy per method',
         ['method']
     )

     domain_document_count = Gauge(
         'domain_document_count',
         'Number of documents per domain',
         ['namespace']
     )

     # 缓存指标
     cache_hit_rate = Gauge(
         'cache_hit_rate',
         'Cache hit rate',
         ['cache_type']
     )

     # 数据库指标
     db_connection_pool_usage = Gauge(
         'db_connection_pool_usage',
         'Database connection pool usage percentage'
     )
     ```

   - [ ] **集成到 API**
     ```python
     # 在查询 API 中
     @router.post("/query/v2")
     async def query_documents_v2(...):
         start_time = time.time()

         try:
             # 执行查询 
             result = ...

             # 记录指标
             domain_query_total.labels(
                 namespace=namespace,
                 retrieval_mode=retrieval_mode
             ).inc()

             latency = time.time() - start_time
             domain_query_latency.labels(namespace=namespace).observe(latency)

             return result

         except Exception as e:
             # 记录错误
             logger.error(f"查询失败: {e}")
             raise
     ```

2. **Prometheus 端点**

   文件: `backend/app/main.py`

   - [ ] **添加 /metrics 端点**
     ```python
     from prometheus_client import make_asgi_app

     # 创建 Prometheus ASGI app
     metrics_app = make_asgi_app()
     app.mount("/metrics", metrics_app)
     ```

3. **定时更新指标**

   文件: `backend/app/monitoring/metric_updater.py` (新建)

   - [ ] **后台任务**
     ```python
     import asyncio
     from apscheduler.schedulers.asyncio import AsyncIOScheduler

     class MetricUpdater:
         """定时更新指标"""

         def __init__(self, db: Session):
             self.db = db
             self.scheduler = AsyncIOScheduler()

         def start(self):
             """启动定时任务"""

             # 每5分钟更新一次领域文档数
             self.scheduler.add_job(
                 self.update_domain_document_counts,
                 'interval',
                 minutes=5
             )

             # 每分钟更新缓存命中率
             self.scheduler.add_job(
                 self.update_cache_metrics,
                 'interval',
                 minutes=1
             )

             self.scheduler.start()

         async def update_domain_document_counts(self):
             """更新领域文档数"""
             domains = self.db.query(KnowledgeDomain).all()

             for domain in domains:
                 count = self.db.query(Document).filter(
                     Document.namespace == domain.namespace
                 ).count()

                 domain_document_count.labels(
                     namespace=domain.namespace
                 ).set(count)

         async def update_cache_metrics(self):
             """更新缓存指标"""
             # Redis 缓存统计
             redis_stats = redis_client.info('stats')
             hits = redis_stats.get('keyspace_hits', 0)
             misses = redis_stats.get('keyspace_misses', 0)

             if hits + misses > 0:
                 hit_rate = hits / (hits + misses)
                 cache_hit_rate.labels(cache_type='redis').set(hit_rate)
     ```

**交付物**:
- ✅ Prometheus 指标定义
- ✅ /metrics 端点
- ✅ 定时指标更新

---

### 任务 9.2: Grafana 监控大盘

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 9.1

#### 子任务清单

1. **创建 Grafana Dashboard**

   文件: `monitoring/grafana/domain-dashboard.json` (新建)

   - [ ] **领域使用情况面板**
     - 每个领域的查询量(时间序列)
     - 领域查询量分布(饼图)
     - 领域文档数量(条形图)

   - [ ] **性能指标面板**
     - 查询延迟 P50/P95/P99(时间序列)
     - 分类延迟(按方法分组)
     - 数据库连接池使用率

   - [ ] **准确性指标面板**
     - 分类准确率(按方法)
     - 跨领域检索使用率
     - 无结果查询占比

   - [ ] **缓存效率面板**
     - 缓存命中率
     - 缓存大小
     - 缓存清理频率

2. **告警规则**

   文件: `monitoring/grafana/alerts.yaml` (新建)

   - [ ] **性能告警**
     ```yaml
     - alert: HighQueryLatency
       expr: domain_query_latency_seconds{quantile="0.95"} > 2
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "查询延迟过高"
         description: "领域 {{ $labels.namespace }} 的 P95 延迟超过 2 秒"

     - alert: LowClassificationAccuracy
       expr: domain_classification_accuracy < 0.7
       for: 10m
       labels:
         severity: warning
       annotations:
         summary: "分类准确率下降"
         description: "{{ $labels.method }} 分类准确率低于 70%"
     ```

   - [ ] **可用性告警**
     ```yaml
     - alert: HighQueryFailureRate
       expr: rate(domain_query_failures_total[5m]) > 0.05
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "查询失败率过高"
         description: "领域 {{ $labels.namespace }} 查询失败率 > 5%"

     - alert: DatabaseConnectionPoolExhausted
       expr: db_connection_pool_usage > 0.9
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "数据库连接池耗尽"
     ```

3. **导出配置**

   - [ ] 导出 Dashboard JSON
   - [ ] 创建部署脚本
   - [ ] 编写配置文档

**交付物**:
- ✅ Grafana Dashboard JSON
- ✅ 告警规则配置
- ✅ 部署文档

---

### 任务 9.3: 日志聚合与追踪

**优先级**: P1
**预计时间**: 2 天
**依赖**: 任务 9.2

#### 子任务清单

1. **结构化日志**

   文件: `backend/app/utils/structured_logger.py` (新建)

   - [ ] **日志格式**
     ```python
     import structlog

     def configure_logging():
         structlog.configure(
             processors=[
                 structlog.stdlib.add_log_level,
                 structlog.stdlib.add_logger_name,
                 structlog.processors.TimeStamper(fmt="iso"),
                 structlog.processors.JSONRenderer()
             ],
             context_class=dict,
             logger_factory=structlog.stdlib.LoggerFactory(),
             cache_logger_on_first_use=True,
         )

     logger = structlog.get_logger()

     # 使用示例
     logger.info(
         "domain_classification",
         query="API 认证失败",
         namespace="technical_docs",
         confidence=0.88,
         method="hybrid",
         latency_ms=45
     )
     ```

2. **分布式追踪(OpenTelemetry)**

   文件: `backend/app/tracing/tracer.py` (新建)

   - [ ] **配置 OpenTelemetry**
     ```python
     from opentelemetry import trace
     from opentelemetry.exporter.jaeger.thrift import JaegerExporter
     from opentelemetry.sdk.trace import TracerProvider
     from opentelemetry.sdk.trace.export import BatchSpanProcessor

     def configure_tracing(service_name: str = "rag-backend"):
         trace.set_tracer_provider(TracerProvider())

         jaeger_exporter = JaegerExporter(
             agent_host_name="localhost",
             agent_port=6831,
         )

         trace.get_tracer_provider().add_span_processor(
             BatchSpanProcessor(jaeger_exporter)
         )

     tracer = trace.get_tracer(__name__)

     # 使用示例
     with tracer.start_as_current_span("query_documents") as span:
         span.set_attribute("namespace", namespace)
         span.set_attribute("retrieval_mode", retrieval_mode)

         with tracer.start_as_current_span("domain_classification"):
             result = await classifier.classify(query)

         with tracer.start_as_current_span("retrieval"):
             chunks = await retrieval.search(query, namespace)

         with tracer.start_as_current_span("rerank"):
             ranked = await reranker.rerank(chunks)
     ```

3. **日志查询接口**

   文件: `backend/app/routers/monitoring.py` (新建)

   - [ ] **日志查询 API**
     ```python
     @router.get("/monitoring/logs")
     async def get_logs(
         level: Optional[str] = None,
         start_time: Optional[datetime] = None,
         end_time: Optional[datetime] = None,
         limit: int = 100,
         current_user: User = Depends(require_admin)
     ):
         """查询日志(需要管理员权限)"""
         # 从日志文件或 Elasticsearch 查询
         # ...
     ```

**交付物**:
- ✅ 结构化日志配置
- ✅ OpenTelemetry 追踪
- ✅ 日志查询 API

---

## Week 3: Rerank 精排

### 任务 10.1: Reranker 模型集成

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 9.3

#### 子任务清单

1. **Reranker 服务**

   文件: `backend/app/services/reranker_service.py` (新建)

   - [ ] **实现 Reranker**
     ```python
     from sentence_transformers import CrossEncoder

     class RerankerService:
         """Rerank 精排服务"""

         def __init__(self):
             self.model_name = "BAAI/bge-reranker-v2-m3"
             self.model = None

         async def initialize(self):
             """加载模型"""
             self.model = CrossEncoder(self.model_name, max_length=512)
             logger.info(f"Reranker 模型已加载: {self.model_name}")

         async def rerank(
             self,
             query: str,
             chunks: List[DocumentChunk],
             top_k: Optional[int] = None
         ) -> List[Tuple[DocumentChunk, float]]:
             """
             Rerank 文档块

             Args:
                 query: 查询文本
                 chunks: 候选文档块
                 top_k: 返回前 K 个(None = 全部)

             Returns:
                 List[Tuple[chunk, score]]
             """

             if len(chunks) == 0:
                 return []

             # 1. 构建 query-chunk 对
             pairs = [[query, chunk.content] for chunk in chunks]

             # 2. 批量推理
             scores = self.model.predict(pairs)

             # 3. 排序
             chunk_scores = list(zip(chunks, scores))
             chunk_scores.sort(key=lambda x: x[1], reverse=True)

             # 4. 返回 Top-K
             if top_k is not None:
                 chunk_scores = chunk_scores[:top_k]

             return chunk_scores

         async def rerank_batch(
             self,
             queries: List[str],
             chunks_list: List[List[DocumentChunk]],
             top_k: int = 5
         ) -> List[List[Tuple[DocumentChunk, float]]]:
             """批量 Rerank(并发优化)"""

             tasks = [
                 self.rerank(query, chunks, top_k)
                 for query, chunks in zip(queries, chunks_list)
             ]

             results = await asyncio.gather(*tasks)
             return results
     ```

2. **集成到检索流程**

   文件: `backend/app/services/hybrid_retrieval.py`

   - [ ] **添加 Rerank 步骤**
     ```python
     class HybridRetrieval:
         def __init__(self, db: Session, enable_rerank: bool = True):
             self.db = db
             self.vector_retrieval = VectorRetrieval(db)
             self.bm25_retrieval = BM25Retrieval(db)
             self.reranker = RerankerService() if enable_rerank else None

         async def search_by_namespace(
             self,
             query: str,
             namespace: str,
             top_k: int = 10,
             alpha: float = 0.5
         ) -> List[DocumentChunk]:
             # 1. 混合检索(获取 Top-K * 3 候选)
             candidates = await self._hybrid_search(
                 query,
                 namespace,
                 top_k * 3,
                 alpha
             )

             # 2. Rerank 精排
             if self.reranker:
                 ranked = await self.reranker.rerank(query, candidates, top_k)
                 return [chunk for chunk, score in ranked]
             else:
                 return candidates[:top_k]
     ```

3. **性能优化**

   - [ ] **批量推理**
     ```python
     # Rerank 模型支持批量推理,减少推理次数
     batch_size = 32
     all_scores = []

     for i in range(0, len(pairs), batch_size):
         batch = pairs[i:i + batch_size]
         scores = self.model.predict(batch)
         all_scores.extend(scores)
     ```

   - [ ] **GPU 加速(可选)**
   - [ ] **模型量化(可选)**

4. **单元测试**

   文件: `backend/tests/services/test_reranker.py`

   - [ ] 测试 Rerank 效果
   - [ ] 测试批量推理
   - [ ] 测试性能(延迟、吞吐量)

**交付物**:
- ✅ RerankerService 实现
- ✅ 集成到检索流程
- ✅ 性能优化
- ✅ 单元测试

---

### 任务 10.2: Rerank 效果评估

**优先级**: P1
**预计时间**: 1.5 天
**依赖**: 任务 10.1

#### 子任务清单

1. **创建评估数据集**

   文件: `backend/tests/data/rerank_test_set.json` (新建)

   - [ ] **标注数据集**
     ```json
     [
       {
         "query": "API 认证失败怎么办",
         "candidates": [
           {"chunk_id": 123, "relevance": 2},  // 2=高度相关
           {"chunk_id": 456, "relevance": 1},  // 1=部分相关
           {"chunk_id": 789, "relevance": 0}   // 0=不相关
         ]
       }
     ]
     ```

2. **评估脚本**

   文件: `backend/scripts/evaluate_rerank.py` (新建)

   - [ ] **评估指标**
     ```python
     def evaluate_rerank(test_set, reranker):
         """评估 Rerank 效果"""

         # 指标
         ndcg_scores = []
         mrr_scores = []

         for case in test_set:
             query = case['query']
             chunks = load_chunks(case['candidates'])

             # Rerank
             ranked = reranker.rerank(query, chunks)

             # 计算 NDCG@5
             ndcg = calculate_ndcg(ranked, case['candidates'], k=5)
             ndcg_scores.append(ndcg)

             # 计算 MRR
             mrr = calculate_mrr(ranked, case['candidates'])
             mrr_scores.append(mrr)

         return {
             'ndcg@5': np.mean(ndcg_scores),
             'mrr': np.mean(mrr_scores)
         }
     ```

3. **对比测试**

   - [ ] 无 Rerank vs 有 Rerank
   - [ ] 不同 Rerank 模型对比
   - [ ] 生成评估报告

**交付物**:
- ✅ Rerank 评估数据集
- ✅ 评估脚本
- ✅ 评估报告

---

## Week 4: 高级功能

### 任务 11.1: 领域关系管理

**优先级**: P2
**预计时间**: 2 天
**依赖**: 任务 10.2

#### 子任务清单

1. **创建领域关系表**

   - [ ] **数据库迁移**
     ```sql
     CREATE TABLE domain_relationships (
         id SERIAL PRIMARY KEY,
         source_namespace VARCHAR(100) NOT NULL,
         related_namespace VARCHAR(100) NOT NULL,
         relationship_type VARCHAR(50) NOT NULL,
         weight FLOAT DEFAULT 0.5,
         is_active BOOLEAN DEFAULT TRUE,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (source_namespace) REFERENCES knowledge_domains(namespace),
         FOREIGN KEY (related_namespace) REFERENCES knowledge_domains(namespace),
         UNIQUE (source_namespace, related_namespace, relationship_type)
     );
     ```

2. **关系管理 API**

   文件: `backend/app/routers/domain_relationships.py` (新建)

   - [ ] CRUD 端点
   - [ ] 关系推荐算法

3. **智能跨领域检索**

   - [ ] 基于关系权重调整检索结果
   - [ ] Fallback 领域配置

**交付物**:
- ✅ 领域关系表
- ✅ 关系管理 API
- ✅ 智能跨领域检索

---

### 任务 11.2: 会话领域上下文

**优先级**: P2
**预计时间**: 1.5 天
**依赖**: 任务 11.1

#### 子任务清单

1. **会话领域追踪**

   - [ ] 在 chat_sessions.metadata 中记录 current_namespace
   - [ ] 记录领域切换历史

2. **智能领域延续**

   - [ ] 多轮对话中延续当前领域
   - [ ] 检测领域切换意图

**交付物**:
- ✅ 会话领域追踪
- ✅ 智能领域延续

---

### 任务 11.3: 数据分析与优化建议

**优先级**: P2
**预计时间**: 2 天
**依赖**: 任务 11.2

#### 子任务清单

1. **领域使用分析报表**

   文件: `backend/app/routers/analytics.py` (新建)

   - [ ] **GET /api/analytics/domain-usage** - 领域使用统计
   - [ ] **GET /api/analytics/classification-accuracy** - 分类准确率分析
   - [ ] **GET /api/analytics/query-patterns** - 查询模式分析

2. **优化建议引擎**

   - [ ] 识别低文档数领域,建议补充
   - [ ] 识别分类混淆,建议优化关键词
   - [ ] 识别热点查询,建议缓存

3. **前端分析页面**

   文件: `frontend/src/views/admin/Analytics.vue` (新建)

   - [ ] 领域使用趋势图表
   - [ ] 分类准确率雷达图
   - [ ] 优化建议列表

**交付物**:
- ✅ 数据分析 API
- ✅ 优化建议引擎
- ✅ 前端分析页面

---

## 阶段验收标准

### 功能验收

- [ ] ✅ 领域级权限控制正常工作
- [ ] ✅ 敏感领域访问受限,审计日志完整
- [ ] ✅ Prometheus + Grafana 监控大盘可用
- [ ] ✅ Rerank 精排效果提升 > 10% (NDCG@5)
- [ ] ✅ 告警规则触发并通知
- [ ] ✅ 领域关系管理功能可用
- [ ] ✅ 分析报表数据准确

### 质量验收

- [ ] ✅ 安全审计通过
- [ ] ✅ 性能测试达标
- [ ] ✅ 监控覆盖率 > 90%
- [ ] ✅ 文档齐全

### 性能验收

- [ ] ✅ 权限检查延迟 < 10ms
- [ ] ✅ Rerank 延迟 < 200ms (10个候选)
- [ ] ✅ 监控指标采集间隔 < 1s
- [ ] ✅ 告警延迟 < 5min

---

## 项目总结

完成四个阶段后,多领域知识库系统将具备:

### 核心功能
✅ 命名空间领域隔离
✅ 智能领域分类(关键词/LLM/混合)
✅ 单领域和跨领域检索
✅ 混合检索(向量+BM25+RRF)
✅ Rerank 精排
✅ 领域级权限控制

### 高级特性
✅ 敏感领域保护
✅ 完整监控告警体系
✅ 领域关系管理
✅ 会话领域上下文
✅ 数据分析与优化建议

### 性能指标
- 分类准确率 > 88%
- 单领域检索延迟 P95 < 500ms
- 跨领域检索延迟 P95 < 1.5s
- Rerank 效果提升 > 10%
- 系统可用性 > 99.5%

恭喜完成多领域知识库架构的完整实施! 🎉
