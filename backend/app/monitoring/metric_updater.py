"""
定时指标更新器

定期更新 Prometheus 指标
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import get_db
from app.models.knowledge_domain import KnowledgeDomain
from app.models.document import Document, DocumentChunk
from app.models.database import User
from app.models.chat import ChatSession

from app.monitoring.metrics import (
    domain_document_count,
    domain_chunk_count,
    domain_avg_confidence,
    active_sessions_count,
    active_users_count,
    cache_hit_rate,
    cache_size,
    db_connection_pool_usage,
    db_connection_pool_size,
)

logger = logging.getLogger(__name__)


class MetricUpdater:
    """定时更新 Prometheus 指标"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running = False

    def start(self):
        """启动定时任务"""
        if self._running:
            logger.warning("MetricUpdater 已在运行")
            return

        logger.info("启动 MetricUpdater...")

        # 每 5 分钟更新领域统计
        self.scheduler.add_job(
            self.update_domain_stats,
            trigger=IntervalTrigger(minutes=5),
            id='update_domain_stats',
            name='更新领域统计指标',
            replace_existing=True
        )

        # 每 1 分钟更新活跃会话和用户
        self.scheduler.add_job(
            self.update_session_stats,
            trigger=IntervalTrigger(minutes=1),
            id='update_session_stats',
            name='更新会话统计指标',
            replace_existing=True
        )

        # 每 2 分钟更新缓存指标
        self.scheduler.add_job(
            self.update_cache_stats,
            trigger=IntervalTrigger(minutes=2),
            id='update_cache_stats',
            name='更新缓存指标',
            replace_existing=True
        )

        # 每 30 秒更新数据库连接池指标
        self.scheduler.add_job(
            self.update_db_pool_stats,
            trigger=IntervalTrigger(seconds=30),
            id='update_db_pool_stats',
            name='更新数据库连接池指标',
            replace_existing=True
        )

        # 启动调度器
        self.scheduler.start()
        self._running = True

        logger.info("MetricUpdater 启动成功")

    def stop(self):
        """停止定时任务"""
        if not self._running:
            return

        logger.info("停止 MetricUpdater...")
        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("MetricUpdater 已停止")

    async def update_domain_stats(self):
        """更新领域统计指标"""
        try:
            logger.debug("开始更新领域统计指标...")

            # 获取数据库会话
            db_gen = get_db()
            db: Session = next(db_gen)

            try:
                # 获取所有活跃领域
                domains = db.query(KnowledgeDomain).filter(
                    KnowledgeDomain.is_active == True
                ).all()

                for domain in domains:
                    namespace = domain.namespace

                    # 文档数量
                    doc_count = db.query(Document).filter(
                        Document.namespace == namespace
                    ).count()
                    domain_document_count.labels(namespace=namespace).set(doc_count)

                    # 分块数量
                    chunk_count = db.query(DocumentChunk).filter(
                        DocumentChunk.namespace == namespace
                    ).count()
                    domain_chunk_count.labels(namespace=namespace).set(chunk_count)

                    # 平均置信度
                    avg_conf_result = db.query(
                        func.avg(Document.domain_confidence)
                    ).filter(
                        Document.namespace == namespace,
                        Document.domain_confidence > 0
                    ).scalar()

                    avg_conf = float(avg_conf_result) if avg_conf_result else 0.0
                    domain_avg_confidence.labels(namespace=namespace).set(avg_conf)

                logger.debug(f"更新了 {len(domains)} 个领域的统计指标")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"更新领域统计指标失败: {e}", exc_info=True)

    async def update_session_stats(self):
        """更新会话和用户统计指标"""
        try:
            logger.debug("开始更新会话统计指标...")

            db_gen = get_db()
            db: Session = next(db_gen)

            try:
                # 活跃会话数 (最近 30 分钟有活动)
                thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
                active_sessions = db.query(ChatSession).filter(
                    ChatSession.updated_at >= thirty_min_ago.isoformat()
                ).count()
                active_sessions_count.set(active_sessions)

                # 活跃用户数 (最近 24 小时有活动的会话数作为代理指标)
                # TODO: 当添加用户认证后,改为统计真实用户数
                one_day_ago = datetime.utcnow() - timedelta(days=1)
                active_sessions_24h = db.query(ChatSession).filter(
                    ChatSession.updated_at >= one_day_ago.isoformat()
                ).count()
                active_users_count.set(active_sessions_24h)

                logger.debug(
                    f"活跃会话: {active_sessions}, 活跃会话(24h): {active_sessions_24h}"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"更新会话统计指标失败: {e}", exc_info=True)

    async def update_cache_stats(self):
        """更新缓存指标"""
        try:
            logger.debug("开始更新缓存指标...")

            # 这里需要根据实际使用的缓存系统来实现
            # 示例:如果使用 Redis
            try:
                # TODO: 集成 Redis 缓存统计
                # import redis
                # redis_client = redis.Redis(...)
                # stats = redis_client.info('stats')
                # hits = stats.get('keyspace_hits', 0)
                # misses = stats.get('keyspace_misses', 0)
                #
                # if hits + misses > 0:
                #     hit_rate = hits / (hits + misses)
                #     cache_hit_rate.labels(cache_type='redis').set(hit_rate)
                #
                # memory_used = redis_client.info('memory')['used_memory']
                # cache_size.labels(cache_type='redis').set(memory_used)

                # 暂时设置默认值
                cache_hit_rate.labels(cache_type='memory').set(0.0)
                cache_size.labels(cache_type='memory').set(0)

                logger.debug("缓存指标更新完成")

            except Exception as cache_error:
                logger.warning(f"Redis 缓存统计失败 (可能未配置): {cache_error}")

        except Exception as e:
            logger.error(f"更新缓存指标失败: {e}", exc_info=True)

    async def update_db_pool_stats(self):
        """更新数据库连接池指标"""
        try:
            logger.debug("开始更新数据库连接池指标...")

            from app.database import get_engine
            engine = get_engine()

            # 获取连接池状态
            pool = engine.pool

            # 连接池大小
            pool_size = pool.size()
            db_connection_pool_size.set(pool_size)

            # 已检出连接数
            checked_out = pool.checkedout()

            # 连接池使用率
            if pool_size > 0:
                usage = checked_out / pool_size
                db_connection_pool_usage.set(usage)
            else:
                db_connection_pool_usage.set(0)

            logger.debug(
                f"连接池: size={pool_size}, checked_out={checked_out}, "
                f"usage={usage:.2%}" if pool_size > 0 else "连接池: size=0"
            )

        except Exception as e:
            logger.error(f"更新数据库连接池指标失败: {e}", exc_info=True)


# 全局实例
_metric_updater: Optional[MetricUpdater] = None


def get_metric_updater() -> MetricUpdater:
    """获取全局 MetricUpdater 实例"""
    global _metric_updater

    if _metric_updater is None:
        _metric_updater = MetricUpdater()
        logger.info("创建全局 MetricUpdater 实例")

    return _metric_updater


def start_metric_updater():
    """启动全局 MetricUpdater"""
    updater = get_metric_updater()
    updater.start()


def stop_metric_updater():
    """停止全局 MetricUpdater"""
    updater = get_metric_updater()
    updater.stop()
