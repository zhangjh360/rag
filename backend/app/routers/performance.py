"""
性能监控 API

提供查询性能统计、慢查询分析等功能
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.database import User
from app.middleware.auth import require_query_ask
from app.services.query_performance import get_query_performance_analyzer
from app.config.logging_config import get_app_logger

router = APIRouter()
logger = get_app_logger()


@router.get("/performance/stats")
async def get_performance_stats(
    hours: int = Query(default=24, description="统计时间范围(小时)"),
    namespace: Optional[str] = Query(default=None, description="筛选领域"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    获取查询性能统计
    """
    try:
        analyzer = get_query_performance_analyzer(db)
        stats = analyzer.get_performance_stats(hours=hours, namespace=namespace)

        return {
            "success": True,
            "data": stats,
            "query_params": {
                "hours": hours,
                "namespace": namespace
            }
        }

    except Exception as e:
        logger.error(f"获取性能统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取性能统计失败: {str(e)}"
        )


@router.get("/performance/slow-queries")
async def get_slow_queries(
    hours: int = Query(default=24, description="统计时间范围(小时)"),
    limit: int = Query(default=20, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    获取慢查询列表
    """
    try:
        analyzer = get_query_performance_analyzer(db)
        slow_queries = analyzer.get_slow_queries(hours=hours, limit=limit)

        return {
            "success": True,
            "data": {
                "slow_queries": slow_queries,
                "count": len(slow_queries)
            },
            "query_params": {
                "hours": hours,
                "limit": limit
            }
        }

    except Exception as e:
        logger.error(f"获取慢查询失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取慢查询失败: {str(e)}"
        )


@router.get("/performance/system-health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    获取系统健康状态
    """
    try:
        analyzer = get_query_performance_analyzer(db)

        # 获取最近1小时的统计
        recent_stats = analyzer.get_performance_stats(hours=1)
        recent_24h_stats = analyzer.get_performance_stats(hours=24)

        # 获取慢查询数量
        slow_queries_last_hour = analyzer.get_slow_queries(hours=1, limit=100)

        # 系统健康评分
        health_score = 100
        health_issues = []

        # 检查错误率
        error_rate = recent_stats.get('summary', {}).get('error_rate', 0)
        if error_rate > 5:
            health_score -= 20
            health_issues.append(f"错误率过高: {error_rate:.1f}%")

        # 检查平均响应时间
        avg_latency = recent_stats.get('summary', {}).get('avg_latency_ms', 0)
        if avg_latency > 2000:
            health_score -= 30
            health_issues.append(f"响应时间过长: {avg_latency:.0f}ms")
        elif avg_latency > 1000:
            health_score -= 15
            health_issues.append(f"响应时间较长: {avg_latency:.0f}ms")

        # 检查慢查询
        slow_query_count = len(slow_queries_last_hour)
        if slow_query_count > 10:
            health_score -= 20
            health_issues.append(f"慢查询过多: {slow_query_count} 个")

        # 检查查询量
        total_queries = recent_stats.get('summary', {}).get('total_queries', 0)
        if total_queries < 10:
            health_score -= 10
            health_issues.append("查询量较低")

        # 确定健康状态
        if health_score >= 90:
            health_status = "优秀"
        elif health_score >= 75:
            health_status = "良好"
        elif health_score >= 60:
            health_status = "一般"
        else:
            health_status = "需要关注"

        return {
            "success": True,
            "data": {
                "health_score": max(0, health_score),
                "health_status": health_status,
                "health_issues": health_issues,
                "recent_hour": {
                    "total_queries": recent_stats.get('summary', {}).get('total_queries', 0),
                    "avg_latency_ms": avg_latency,
                    "error_rate": error_rate,
                    "slow_queries_count": slow_query_count
                },
                "last_24h": {
                    "total_queries": recent_24h_stats.get('summary', {}).get('total_queries', 0),
                    "avg_latency_ms": recent_24h_stats.get('summary', {}).get('avg_latency_ms', 0),
                    "error_rate": recent_24h_stats.get('summary', {}).get('error_rate', 0),
                    "unique_sessions": recent_24h_stats.get('summary', {}).get('unique_sessions', 0)
                }
            }
        }

    except Exception as e:
        logger.error(f"获取系统健康状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取系统健康状态失败: {str(e)}"
        )


@router.post("/performance/cleanup-logs")
async def cleanup_logs(
    days: int = Query(default=30, description="保留天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    清理旧的性能日志
    """
    try:
        analyzer = get_query_performance_analyzer(db)
        deleted_count = analyzer.cleanup_old_logs(days=days)

        return {
            "success": True,
            "data": {
                "deleted_count": deleted_count,
                "retention_days": days
            }
        }

    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清理日志失败: {str(e)}"
        )


@router.get("/performance/retention")
async def get_log_retention(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    获取日志保留策略信息
    """
    try:
        # 获取不同时间段的日志数量
        retention_data = []

        time_ranges = [
            (1, "最近1小时"),
            (24, "最近24小时"),
            (168, "最近7天"),
            (720, "最近30天")
        ]

        for hours, label in time_ranges:
            analyzer = get_query_performance_analyzer(db)
            stats = analyzer.get_performance_stats(hours=hours)
            total_queries = stats.get('summary', {}).get('total_queries', 0)

            retention_data.append({
                "label": label,
                "hours": hours,
                "count": total_queries
            })

        return {
            "success": True,
            "data": {
                "retention_data": retention_data,
                "default_retention_days": 30,
                "storage_info": {
                    "auto_cleanup": True,
                    "compression_enabled": False
                }
            }
        }

    except Exception as e:
        logger.error(f"获取日志保留信息失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取日志保留信息失败: {str(e)}"
        )