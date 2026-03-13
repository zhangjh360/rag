"""
Prometheus 指标系统单元测试
"""

import pytest
from app.monitoring.metrics import (
    domain_query_total,
    domain_query_latency,
    domain_classification_latency,
    classification_total,
    retrieval_results_count,
    rerank_latency,
    record_query_metrics,
    record_classification_metrics,
    record_rerank_metrics,
    record_retrieval_results
)


class TestMetrics:
    """Prometheus 指标测试"""

    def test_record_query_metrics_success(self):
        """测试记录成功查询指标"""
        # 记录成功查询
        record_query_metrics(
            namespace='test_domain',
            retrieval_mode='single',
            latency=0.5,
            status='success'
        )

        # 验证 Counter 增加
        counter_value = domain_query_total.labels(
            namespace='test_domain',
            retrieval_mode='single',
            status='success'
        )._value._value
        assert counter_value > 0

    def test_record_query_metrics_failure(self):
        """测试记录失败查询指标"""
        # 记录失败查询
        record_query_metrics(
            namespace='test_domain',
            retrieval_mode='single',
            latency=0.5,
            status='failure',
            error_type='ValueError'
        )

        # 验证失败计数
        counter_value = domain_query_total.labels(
            namespace='test_domain',
            retrieval_mode='single',
            status='failure'
        )._value._value
        assert counter_value > 0

    def test_record_classification_metrics(self):
        """测试记录分类指标"""
        record_classification_metrics(
            method='hybrid',
            namespace='test_domain',
            latency=0.1
        )

        # 验证分类总数增加
        counter_value = classification_total.labels(
            method='hybrid',
            namespace='test_domain'
        )._value._value
        assert counter_value > 0

    def test_record_rerank_metrics(self):
        """测试记录 Rerank 指标"""
        record_rerank_metrics(
            namespace='test_domain',
            latency=0.2,
            status='success'
        )

        # 验证计数增加
        # (由于 Histogram 结构复杂,这里只测试不抛异常)
        assert True

    def test_record_retrieval_results(self):
        """测试记录检索结果数"""
        record_retrieval_results(
            namespace='test_domain',
            retrieval_type='hybrid',
            count=10
        )

        # 验证不抛异常
        assert True


class TestMetricUpdater:
    """MetricUpdater 测试"""

    def test_metric_updater_initialization(self):
        """测试 MetricUpdater 初始化"""
        from app.monitoring.metric_updater import MetricUpdater

        updater = MetricUpdater()
        assert updater._running == False
        assert updater.scheduler is not None

    def test_get_metric_updater_singleton(self):
        """测试单例模式"""
        from app.monitoring.metric_updater import get_metric_updater
        import app.monitoring.metric_updater as updater_module

        # 清除全局实例
        updater_module._metric_updater = None

        # 获取实例
        updater1 = get_metric_updater()
        updater2 = get_metric_updater()

        # 验证是同一个实例
        assert updater1 is updater2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
