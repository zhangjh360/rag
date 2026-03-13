"""
查询性能日志服务

记录查询性能数据，用于监控和优化
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import json

# 设置日志
logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceLog:
    """查询性能日志数据模型"""
    timestamp: datetime
    query: str
    query_length: int
    retrieval_mode: str
    retrieval_method: str
    namespace: Optional[str]
    top_k: int
    alpha: float
    similarity_threshold: float

    # 性能指标
    total_latency_ms: float
    classification_latency_ms: Optional[float]
    retrieval_latency_ms: float
    llm_latency_ms: Optional[float]

    # 结果统计
    total_candidates: int
    filtered_results: int
    vector_results: int
    bm25_results: int

    # 领域信息
    primary_domain: Optional[str]
    cross_domain_enabled: bool
    domains_searched: List[str]

    # 系统信息
    session_id: Optional[str]
    user_agent: Optional[str]
    error: Optional[str]


class QueryPerformanceLogger:
    """查询性能日志记录器"""

    def __init__(self, db: Session):
        self.db = db
        self._create_performance_table()

    def _create_performance_table(self):
        """创建性能日志表"""
        try:
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS query_performance_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    query TEXT NOT NULL,
                    query_length INTEGER NOT NULL,
                    retrieval_mode VARCHAR(50),
                    retrieval_method VARCHAR(50),
                    namespace VARCHAR(100),
                    top_k INTEGER,
                    alpha DECIMAL(3,2),
                    similarity_threshold DECIMAL(3,2),

                    -- 性能指标
                    total_latency_ms DECIMAL(8,2),
                    classification_latency_ms DECIMAL(8,2),
                    retrieval_latency_ms DECIMAL(8,2),
                    llm_latency_ms DECIMAL(8,2),

                    -- 结果统计
                    total_candidates INTEGER DEFAULT 0,
                    filtered_results INTEGER DEFAULT 0,
                    vector_results INTEGER DEFAULT 0,
                    bm25_results INTEGER DEFAULT 0,

                    -- 领域信息
                    primary_domain VARCHAR(100),
                    cross_domain_enabled BOOLEAN DEFAULT FALSE,
                    domains_searched TEXT, -- JSON array

                    -- 系统信息
                    session_id VARCHAR(100),
                    user_agent TEXT,
                    error TEXT,

                    -- 索引
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_query_perf_timestamp ON query_performance_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_query_perf_retrieval_mode ON query_performance_logs(retrieval_mode);
                CREATE INDEX IF NOT EXISTS idx_query_perf_namespace ON query_performance_logs(namespace);
                CREATE INDEX IF NOT EXISTS idx_query_perf_session_id ON query_performance_logs(session_id);
            """))
            self.db.commit()
            logger.info("✅ 查询性能日志表创建成功")
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 创建性能日志表失败: {e}")

    def log_query(
        self,
        query: str,
        retrieval_mode: str,
        retrieval_method: str,
        performance_data: Dict[str, Any],
        result_data: Dict[str, Any],
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        error: Optional[str] = None
    ):
        """记录查询性能日志"""
        try:
            log = QueryPerformanceLog(
                timestamp=datetime.utcnow(),
                query=query,
                query_length=len(query),
                retrieval_mode=retrieval_mode,
                retrieval_method=retrieval_method,
                namespace=performance_data.get('namespace'),
                top_k=performance_data.get('top_k', 10),
                alpha=performance_data.get('alpha', 0.5),
                similarity_threshold=performance_data.get('similarity_threshold', 0.0),

                total_latency_ms=performance_data.get('total_latency_ms', 0),
                classification_latency_ms=performance_data.get('classification_latency_ms'),
                retrieval_latency_ms=performance_data.get('retrieval_latency_ms', 0),
                llm_latency_ms=performance_data.get('llm_latency_ms'),

                total_candidates=result_data.get('total_candidates', 0),
                filtered_results=result_data.get('filtered_results', 0),
                vector_results=result_data.get('vector_results', 0),
                bm25_results=result_data.get('bm25_results', 0),

                primary_domain=result_data.get('primary_domain'),
                cross_domain_enabled=result_data.get('cross_domain_enabled', False),
                domains_searched=result_data.get('domains_searched', []),

                session_id=session_id,
                user_agent=user_agent,
                error=error
            )

            # 转换为字典并插入数据库
            log_dict = asdict(log)
            log_dict['domains_searched'] = json.dumps(log_dict['domains_searched'])

            self.db.execute(text("""
                INSERT INTO query_performance_logs (
                    timestamp, query, query_length, retrieval_mode, retrieval_method,
                    namespace, top_k, alpha, similarity_threshold,
                    total_latency_ms, classification_latency_ms, retrieval_latency_ms, llm_latency_ms,
                    total_candidates, filtered_results, vector_results, bm25_results,
                    primary_domain, cross_domain_enabled, domains_searched,
                    session_id, user_agent, error
                ) VALUES (
                    :timestamp, :query, :query_length, :retrieval_mode, :retrieval_method,
                    :namespace, :top_k, :alpha, :similarity_threshold,
                    :total_latency_ms, :classification_latency_ms, :retrieval_latency_ms, :llm_latency_ms,
                    :total_candidates, :filtered_results, :vector_results, :bm25_results,
                    :primary_domain, :cross_domain_enabled, :domains_searched,
                    :session_id, :user_agent, :error
                )
            """), log_dict)

            self.db.commit()
            logger.info(f"✅ 查询性能日志记录: {log.total_latency_ms:.2f}ms")

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 记录查询性能日志失败: {e}")


class QueryPerformanceAnalyzer:
    """查询性能分析器"""

    def __init__(self, db: Session):
        self.db = db

    def get_performance_stats(
        self,
        hours: int = 24,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            # 构建WHERE条件
            where_conditions = [
                f"timestamp >= NOW() - INTERVAL '{hours} hours'"
            ]
            if namespace:
                where_conditions.append(f"namespace = '{namespace}'")

            where_clause = " AND ".join(where_conditions)

            # 基础统计
            stats = self.db.execute(text(f"""
                SELECT
                    COUNT(*) as total_queries,
                    AVG(total_latency_ms) as avg_latency,
                    MIN(total_latency_ms) as min_latency,
                    MAX(total_latency_ms) as max_latency,
                    AVG(total_candidates) as avg_candidates,
                    AVG(filtered_results) as avg_filtered,
                    COUNT(*) FILTER (WHERE error IS NOT NULL) as error_count,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM query_performance_logs
                WHERE {where_clause}
            """)).fetchone()

            # 按检索模式统计
            mode_stats = self.db.execute(text(f"""
                SELECT
                    retrieval_mode,
                    COUNT(*) as count,
                    AVG(total_latency_ms) as avg_latency
                FROM query_performance_logs
                WHERE {where_clause}
                GROUP BY retrieval_mode
                ORDER BY count DESC
            """)).fetchall()

            # 按领域统计
            namespace_stats = self.db.execute(text(f"""
                SELECT
                    namespace,
                    COUNT(*) as count,
                    AVG(total_latency_ms) as avg_latency
                FROM query_performance_logs
                WHERE {where_clause}
                AND namespace IS NOT NULL
                GROUP BY namespace
                ORDER BY count DESC
                LIMIT 10
            """)).fetchall()

            # 每小时查询量趋势
            hourly_stats = self.db.execute(text(f"""
                SELECT
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(*) as count,
                    AVG(total_latency_ms) as avg_latency
                FROM query_performance_logs
                WHERE {where_clause}
                GROUP BY DATE_TRUNC('hour', timestamp)
                ORDER BY hour DESC
                LIMIT 24
            """)).fetchall()

            return {
                'summary': {
                    'total_queries': stats.total_queries,
                    'avg_latency_ms': float(stats.avg_latency or 0),
                    'min_latency_ms': float(stats.min_latency or 0),
                    'max_latency_ms': float(stats.max_latency or 0),
                    'avg_candidates': float(stats.avg_candidates or 0),
                    'avg_filtered': float(stats.avg_filtered or 0),
                    'error_count': stats.error_count,
                    'error_rate': (stats.error_count / stats.total_queries * 100) if stats.total_queries > 0 else 0,
                    'unique_sessions': stats.unique_sessions
                },
                'by_retrieval_mode': [
                    {
                        'mode': row.retrieval_mode,
                        'count': row.count,
                        'avg_latency_ms': float(row.avg_latency or 0)
                    }
                    for row in mode_stats
                ],
                'by_namespace': [
                    {
                        'namespace': row.namespace,
                        'count': row.count,
                        'avg_latency_ms': float(row.avg_latency or 0)
                    }
                    for row in namespace_stats
                ],
                'hourly_trend': [
                    {
                        'hour': row.hour.isoformat(),
                        'count': row.count,
                        'avg_latency_ms': float(row.avg_latency or 0)
                    }
                    for row in hourly_stats
                ]
            }

        except Exception as e:
            logger.error(f"❌ 获取性能统计失败: {e}")
            return {}

    def get_slow_queries(
        self,
        hours: int = 24,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        try:
            rows = self.db.execute(text(f"""
                SELECT
                    query,
                    retrieval_mode,
                    retrieval_method,
                    total_latency_ms,
                    namespace,
                    top_k,
                    timestamp
                FROM query_performance_logs
                WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                AND total_latency_ms > 1000
                ORDER BY total_latency_ms DESC
                LIMIT {limit}
            """)).fetchall()

            return [
                {
                    'query': row.query[:100] + ('...' if len(row.query) > 100 else ''),
                    'full_query': row.query,
                    'retrieval_mode': row.retrieval_mode,
                    'retrieval_method': row.retrieval_method,
                    'latency_ms': float(row.total_latency_ms),
                    'namespace': row.namespace,
                    'top_k': row.top_k,
                    'timestamp': row.timestamp.isoformat()
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"❌ 获取慢查询失败: {e}")
            return []

    def cleanup_old_logs(self, days: int = 30) -> int:
        """清理旧日志"""
        try:
            result = self.db.execute(text(f"""
                DELETE FROM query_performance_logs
                WHERE timestamp < NOW() - INTERVAL '{days} days'
            """))

            deleted_count = result.rowcount
            self.db.commit()
            logger.info(f"✅ 清理了 {deleted_count} 条旧日志")
            return deleted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ 清理旧日志失败: {e}")
            return 0


# 依赖注入
def get_query_performance_logger(db: Session) -> QueryPerformanceLogger:
    """获取查询性能日志记录器"""
    return QueryPerformanceLogger(db)


def get_query_performance_analyzer(db: Session) -> QueryPerformanceAnalyzer:
    """获取查询性能分析器"""
    return QueryPerformanceAnalyzer(db)