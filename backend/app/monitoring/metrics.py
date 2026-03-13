"""
Prometheus 指标定义

定义系统的所有监控指标
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ==================== 领域查询指标 ====================

domain_query_total = Counter(
    'domain_query_total',
    'Total number of queries per domain',
    ['namespace', 'retrieval_mode', 'status']
)

domain_query_latency = Histogram(
    'domain_query_latency_seconds',
    'Query latency per domain in seconds',
    ['namespace', 'retrieval_mode'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

domain_query_failures_total = Counter(
    'domain_query_failures_total',
    'Total number of failed queries per domain',
    ['namespace', 'error_type']
)

# ==================== 分类指标 ====================

domain_classification_accuracy = Gauge(
    'domain_classification_accuracy',
    'Classification accuracy per method',
    ['method']
)

domain_classification_latency = Histogram(
    'domain_classification_latency_seconds',
    'Classification latency per method in seconds',
    ['method'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

classification_total = Counter(
    'domain_classification_total',
    'Total number of classifications',
    ['method', 'namespace']
)

# ==================== 检索指标 ====================

retrieval_results_count = Histogram(
    'retrieval_results_count',
    'Number of results returned by retrieval',
    ['namespace', 'retrieval_type'],
    buckets=[0, 1, 5, 10, 20, 50, 100]
)

rerank_latency = Histogram(
    'rerank_latency_seconds',
    'Rerank processing latency in seconds',
    ['namespace'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

rerank_total = Counter(
    'rerank_total',
    'Total number of rerank operations',
    ['namespace', 'status']
)

# ==================== 领域统计指标 ====================

domain_document_count = Gauge(
    'domain_document_count',
    'Number of documents per domain',
    ['namespace']
)

domain_chunk_count = Gauge(
    'domain_chunk_count',
    'Number of chunks per domain',
    ['namespace']
)

domain_avg_confidence = Gauge(
    'domain_avg_confidence',
    'Average domain confidence score',
    ['namespace']
)

# ==================== 缓存指标 ====================

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    ['cache_type']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['cache_type', 'operation']
)

# ==================== 数据库指标 ====================

db_connection_pool_usage = Gauge(
    'db_connection_pool_usage',
    'Database connection pool usage (0-1)'
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_query_latency = Histogram(
    'db_query_latency_seconds',
    'Database query latency in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

db_query_total = Counter(
    'db_query_total',
    'Total number of database queries',
    ['operation', 'status']
)

# ==================== 系统指标 ====================

active_sessions_count = Gauge(
    'active_sessions_count',
    'Number of active chat sessions'
)

active_users_count = Gauge(
    'active_users_count',
    'Number of active users'
)

api_request_total = Counter(
    'api_request_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_latency = Histogram(
    'api_request_latency_seconds',
    'API request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ==================== 应用信息 ====================

app_info = Info(
    'rag_app',
    'RAG application information'
)

# 设置应用信息
app_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'features': 'multi_domain,rerank,hybrid_retrieval'
})

# ==================== 辅助函数 ====================

def record_query_metrics(
    namespace: str,
    retrieval_mode: str,
    latency: float,
    status: str = 'success',
    error_type: str = None
):
    """记录查询指标

    Args:
        namespace: 领域命名空间
        retrieval_mode: 检索模式 (single/cross/hybrid)
        latency: 延迟时间(秒)
        status: 状态 (success/failure)
        error_type: 错误类型(如果失败)
    """
    # 记录查询总数
    domain_query_total.labels(
        namespace=namespace,
        retrieval_mode=retrieval_mode,
        status=status
    ).inc()

    # 记录延迟
    domain_query_latency.labels(
        namespace=namespace,
        retrieval_mode=retrieval_mode
    ).observe(latency)

    # 如果失败,记录失败指标
    if status == 'failure' and error_type:
        domain_query_failures_total.labels(
            namespace=namespace,
            error_type=error_type
        ).inc()


def record_classification_metrics(
    method: str,
    namespace: str,
    latency: float
):
    """记录分类指标

    Args:
        method: 分类方法 (keyword/llm/hybrid)
        namespace: 分类结果的领域
        latency: 延迟时间(秒)
    """
    # 记录分类总数
    classification_total.labels(
        method=method,
        namespace=namespace
    ).inc()

    # 记录延迟
    domain_classification_latency.labels(
        method=method
    ).observe(latency)


def record_rerank_metrics(
    namespace: str,
    latency: float,
    status: str = 'success'
):
    """记录 Rerank 指标

    Args:
        namespace: 领域命名空间
        latency: 延迟时间(秒)
        status: 状态 (success/failure)
    """
    # 记录 Rerank 总数
    rerank_total.labels(
        namespace=namespace,
        status=status
    ).inc()

    # 记录延迟
    if status == 'success':
        rerank_latency.labels(
            namespace=namespace
        ).observe(latency)


def record_retrieval_results(
    namespace: str,
    retrieval_type: str,
    count: int
):
    """记录检索结果数量

    Args:
        namespace: 领域命名空间
        retrieval_type: 检索类型 (vector/bm25/hybrid)
        count: 结果数量
    """
    retrieval_results_count.labels(
        namespace=namespace,
        retrieval_type=retrieval_type
    ).observe(count)


def record_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    latency: float
):
    """记录 API 请求指标

    Args:
        method: HTTP 方法
        endpoint: API 端点
        status_code: 状态码
        latency: 延迟时间(秒)
    """
    # 记录请求总数
    api_request_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()

    # 记录延迟
    api_request_latency.labels(
        method=method,
        endpoint=endpoint
    ).observe(latency)
