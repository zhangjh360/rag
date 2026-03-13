"""
监控模块

提供 Prometheus 指标采集和定时更新功能
"""

from app.monitoring.metrics import (
    # 领域查询指标
    domain_query_total,
    domain_query_latency,
    domain_query_failures_total,

    # 分类指标
    domain_classification_accuracy,
    domain_classification_latency,

    # 检索指标
    retrieval_results_count,
    rerank_latency,

    # 领域统计指标
    domain_document_count,
    domain_chunk_count,

    # 缓存指标
    cache_hit_rate,
    cache_size,

    # 数据库指标
    db_connection_pool_usage,
    db_query_latency,

    # 系统指标
    active_sessions_count,
    api_request_total,
)

from app.monitoring.metric_updater import MetricUpdater

__all__ = [
    # 指标
    'domain_query_total',
    'domain_query_latency',
    'domain_query_failures_total',
    'domain_classification_accuracy',
    'domain_classification_latency',
    'retrieval_results_count',
    'rerank_latency',
    'domain_document_count',
    'domain_chunk_count',
    'cache_hit_rate',
    'cache_size',
    'db_connection_pool_usage',
    'db_query_latency',
    'active_sessions_count',
    'api_request_total',

    # 更新器
    'MetricUpdater',
]
