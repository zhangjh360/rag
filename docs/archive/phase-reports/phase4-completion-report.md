# Phase 4 高级功能 - 完成报告

**报告时间**: 2025-11-19
**Phase 4 状态**: P0 全部完成,P1/P2 提供详细实施方案

---

## 总体完成情况

### ✅ P0 (Critical) - 已完成 3/3

| 任务 | 状态 | 完成度 | 文档 |
|------|------|--------|------|
| 10.1 Reranker 模型集成 | ✅ 已完成 | 100% | [RERANKER_IMPLEMENTATION.md](RERANKER_IMPLEMENTATION.md) |
| 9.1 指标采集系统 | ✅ 已完成 | 100% | [PROMETHEUS_METRICS_IMPLEMENTATION.md](PROMETHEUS_METRICS_IMPLEMENTATION.md) |
| 9.2 Grafana 监控大盘 | ✅ 已完成 | 100% | [GRAFANA_MONITORING_IMPLEMENTATION.md](GRAFANA_MONITORING_IMPLEMENTATION.md) |

### 📋 P1 (Important) - 实施方案完成 3/3

| 任务 | 状态 | 方案 |
|------|------|------|
| 8.1 领域级权限控制 | 📋 方案完成 | 见下方详细方案 |
| 10.2 Rerank 效果评估 | 📋 方案完成 | 见下方详细方案 |
| 8.2 敏感领域保护 | 📋 方案完成 | 见下方详细方案 |

### 📋 P2 (Enhancement) - 实施方案完成 3/3

| 任务 | 状态 | 方案 |
|------|------|------|
| 9.3 日志聚合和追踪 | 📋 方案完成 | 见下方详细方案 |
| 11.1 领域关系管理 | 📋 方案完成 | 见下方详细方案 |
| 11.2 会话领域上下文 | 📋 方案完成 | 见下方详细方案 |
| 11.3 数据分析和优化 | 📋 方案完成 | 见下方详细方案 |

---

## P0 任务详细总结

### ✅ 任务 10.1: Reranker 模型集成

**完成内容**:
- ✅ 实现 RerankerService (backend/app/services/reranker_service.py)
- ✅ 集成 BAAI/bge-reranker-v2-m3 模型
- ✅ 异步模型加载和批量推理
- ✅ 集成到 HybridRetrieval
- ✅ 配置选项和环境变量
- ✅ 单元测试 (13 个测试用例)
- ✅ 详细实现文档

**关键功能**:
- 批量推理优化 (batch_size=32)
- 错误降级策略
- 支持启用/禁用
- 候选数量扩展 (top_k * 3)

**预期效果**:
- NDCG@10: 提升 10-15%
- MRR: 提升 8-12%
- 准确率: 提升 5-10%

### ✅ 任务 9.1: Prometheus 指标采集系统

**完成内容**:
- ✅ 定义 30+ Prometheus 指标 (backend/app/monitoring/metrics.py)
- ✅ 实现 MetricUpdater 定时更新 (backend/app/monitoring/metric_updater.py)
- ✅ 添加 /metrics 端点
- ✅ 集成到查询 API (query_v2.py)
- ✅ 添加依赖 (prometheus-client, apscheduler)
- ✅ 单元测试
- ✅ 详细实现文档

**指标分类**:
- 领域查询指标 (QPS, 延迟, 失败率)
- 分类指标 (延迟, 准确率)
- 检索指标 (结果数, Rerank 延迟)
- 领域统计 (文档数, 分块数)
- 缓存指标 (命中率, 大小)
- 数据库指标 (连接池, 查询延迟)
- 系统指标 (会话数, 用户数)

**定时更新**:
- 每 5 分钟: 领域统计
- 每 1 分钟: 会话统计
- 每 2 分钟: 缓存指标
- 每 30 秒: 数据库连接池

### ✅ 任务 9.2: Grafana 监控大盘

**完成内容**:
- ✅ Prometheus 配置 (monitoring/prometheus/prometheus.yml)
- ✅ 15+ 告警规则 (monitoring/prometheus/alerts/rag_alerts.yml)
- ✅ Grafana Dashboard (12 个面板)
- ✅ Alertmanager 配置
- ✅ Docker Compose 部署配置
- ✅ 启动脚本和 README
- ✅ 详细实现文档

**监控大盘**:
- 查询 QPS (Graph)
- 查询延迟 P50/P95/P99 (Graph)
- 各领域查询量 (Graph)
- 查询失败率 (Graph)
- 活跃会话数/用户数 (Stat)
- 数据库连接池使用率 (Gauge)
- 总文档数 (Stat)
- 分类延迟 (Graph)
- Rerank 延迟 (Graph)
- 各领域文档数 (BarGauge)
- 检索结果分布 (Heatmap)

**告警规则**:
- 高延迟告警 (P95 > 2s)
- 高失败率告警 (>5%)
- 连接池使用率告警 (>80%)
- Rerank 延迟告警
- 缓存命中率低告警
- 数据质量告警

---

## P1 任务实施方案

### 📋 任务 8.1: 领域级权限控制

**目标**: 实现细粒度的领域级权限管理,控制用户对特定领域的访问

#### 设计方案

**1. 数据模型**

创建 `DomainPermission` 表:

```python
# backend/app/models/domain_permission.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.models.document import Base

class DomainPermission(Base):
    """领域权限表"""
    __tablename__ = 'domain_permissions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    namespace = Column(String(100), nullable=False)  # 领域命名空间
    permission_level = Column(String(20), default='read')  # read/write/admin
    can_query = Column(Boolean, default=True)  # 是否可查询
    can_upload = Column(Boolean, default=False)  # 是否可上传文档
    can_manage = Column(Boolean, default=False)  # 是否可管理领域
    is_active = Column(Boolean, default=True)
    created_at = Column(String)
    updated_at = Column(String)
    created_by = Column(Integer)  # 授权者ID

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('user_id', 'namespace', name='uq_user_namespace'),
    )
```

**2. 权限检查中间件**

```python
# backend/app/middleware/domain_permission.py

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import User
from app.models.domain_permission import DomainPermission

async def check_domain_permission(
    namespace: str,
    permission_type: str = 'query',  # query/upload/manage
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """检查用户是否有领域权限"""

    # 管理员默认有所有权限
    if current_user.role_id == 1:  # Admin role
        return True

    # 查询用户权限
    permission = db.query(DomainPermission).filter(
        DomainPermission.user_id == current_user.id,
        DomainPermission.namespace == namespace,
        DomainPermission.is_active == True
    ).first()

    if not permission:
        raise HTTPException(
            status_code=403,
            detail=f"您没有访问领域 '{namespace}' 的权限"
        )

    # 检查具体权限
    if permission_type == 'query' and not permission.can_query:
        raise HTTPException(
            status_code=403,
            detail=f"您没有查询领域 '{namespace}' 的权限"
        )
    elif permission_type == 'upload' and not permission.can_upload:
        raise HTTPException(
            status_code=403,
            detail=f"您没有向领域 '{namespace}' 上传文档的权限"
        )
    elif permission_type == 'manage' and not permission.can_manage:
        raise HTTPException(
            status_code=403,
            detail=f"您没有管理领域 '{namespace}' 的权限"
        )

    return True
```

**3. 集成到查询 API**

```python
# backend/app/routers/query_v2.py (修改)

from app.middleware.domain_permission import check_domain_permission

@router.post("/query/v2", response_model=QueryResponseV2)
async def query_documents_v2(
    request: QueryRequestV2,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    # ... 分类逻辑 ...

    # 检查领域权限
    if namespace:
        await check_domain_permission(
            namespace=namespace,
            permission_type='query',
            current_user=current_user,
            db=db
        )

    # ... 执行查询 ...
```

**4. 权限管理 API**

```python
# backend/app/routers/domain_permissions.py (新建)

from fastapi import APIRouter, Depends, HTTPException
from app.middleware.domain_permission import check_domain_permission

router = APIRouter()

@router.post("/domain-permissions")
async def grant_domain_permission(
    permission: DomainPermissionCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """授予领域权限"""
    # 检查授权者是否有管理权限
    await check_domain_permission(
        namespace=permission.namespace,
        permission_type='manage',
        current_user=current_user,
        db=db
    )

    # 创建或更新权限
    # ...

@router.delete("/domain-permissions/{permission_id}")
async def revoke_domain_permission(
    permission_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """撤销领域权限"""
    # ...

@router.get("/domain-permissions/user/{user_id}")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户的所有领域权限"""
    # ...
```

**5. 前端集成**

```javascript
// frontend/src/services/domainPermissions.js

export const domainPermissionsAPI = {
  // 获取用户权限
  getUserPermissions: (userId) => {
    return axios.get(`/api/domain-permissions/user/${userId}`)
  },

  // 授予权限
  grantPermission: (data) => {
    return axios.post('/api/domain-permissions', data)
  },

  // 撤销权限
  revokePermission: (permissionId) => {
    return axios.delete(`/api/domain-permissions/${permissionId}`)
  }
}
```

**实施步骤**:
1. 创建数据库迁移脚本
2. 实现 DomainPermission 模型
3. 实现权限检查中间件
4. 集成到查询和上传 API
5. 创建权限管理 API
6. 前端权限管理界面
7. 编写单元测试
8. 更新文档

---

### 📋 任务 10.2: Rerank 效果评估

**目标**: 评估 Reranker 对检索质量的提升效果

#### 设计方案

**1. 评估数据集**

```python
# backend/app/evaluation/rerank_dataset.py

import json
from typing import List, Dict

class RerankEvaluationDataset:
    """Rerank 评估数据集"""

    def __init__(self, dataset_path: str):
        self.dataset = self._load_dataset(dataset_path)

    def _load_dataset(self, path: str) -> List[Dict]:
        """加载评估数据集

        数据格式:
        [
            {
                "query": "如何配置API?",
                "namespace": "technical_docs",
                "relevant_docs": [  # 相关文档ID列表
                    {"doc_id": 123, "relevance": 3},  # 0-3 评分
                    {"doc_id": 456, "relevance": 2},
                    ...
                ]
            },
            ...
        ]
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_queries(self) -> List[str]:
        return [item['query'] for item in self.dataset]

    def get_relevance_scores(self, query: str) -> Dict[int, int]:
        """获取查询的相关性评分映射 {doc_id: score}"""
        for item in self.dataset:
            if item['query'] == query:
                return {
                    doc['doc_id']: doc['relevance']
                    for doc in item['relevant_docs']
                }
        return {}
```

**2. 评估指标计算**

```python
# backend/app/evaluation/rerank_metrics.py

import numpy as np
from typing import List, Dict

def calculate_ndcg(
    retrieved_docs: List[int],
    relevance_scores: Dict[int, int],
    k: int = 10
) -> float:
    """计算 NDCG@K (Normalized Discounted Cumulative Gain)

    Args:
        retrieved_docs: 检索结果文档ID列表 (排序后)
        relevance_scores: 相关性评分映射 {doc_id: score}
        k: Top K

    Returns:
        NDCG@K 分数 (0-1)
    """
    # DCG (Discounted Cumulative Gain)
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_docs[:k]):
        rel = relevance_scores.get(doc_id, 0)
        dcg += (2 ** rel - 1) / np.log2(i + 2)

    # IDCG (Ideal DCG)
    ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = sum(
        (2 ** rel - 1) / np.log2(i + 2)
        for i, rel in enumerate(ideal_rels)
    )

    # NDCG
    return dcg / idcg if idcg > 0 else 0.0


def calculate_mrr(
    retrieved_docs: List[int],
    relevance_scores: Dict[int, int],
    min_relevance: int = 2
) -> float:
    """计算 MRR (Mean Reciprocal Rank)

    Args:
        retrieved_docs: 检索结果文档ID列表
        relevance_scores: 相关性评分映射
        min_relevance: 最小相关性阈值

    Returns:
        RR (Reciprocal Rank)
    """
    for i, doc_id in enumerate(retrieved_docs):
        if relevance_scores.get(doc_id, 0) >= min_relevance:
            return 1.0 / (i + 1)
    return 0.0


def calculate_precision_at_k(
    retrieved_docs: List[int],
    relevance_scores: Dict[int, int],
    k: int = 10,
    min_relevance: int = 1
) -> float:
    """计算 Precision@K

    Args:
        retrieved_docs: 检索结果文档ID列表
        relevance_scores: 相关性评分映射
        k: Top K
        min_relevance: 最小相关性阈值

    Returns:
        Precision@K (0-1)
    """
    relevant_count = sum(
        1 for doc_id in retrieved_docs[:k]
        if relevance_scores.get(doc_id, 0) >= min_relevance
    )
    return relevant_count / k if k > 0 else 0.0
```

**3. 评估执行器**

```python
# backend/app/evaluation/rerank_evaluator.py

from typing import Dict, List
import asyncio
from app.services.hybrid_retrieval import get_hybrid_retrieval

class RerankEvaluator:
    """Rerank 效果评估器"""

    def __init__(self, db: Session, dataset: RerankEvaluationDataset):
        self.db = db
        self.dataset = dataset
        self.retrieval_service = get_hybrid_retrieval(db)

    async def evaluate(
        self,
        use_rerank: bool = True,
        top_k: int = 10
    ) -> Dict[str, float]:
        """评估检索效果

        Args:
            use_rerank: 是否使用 Rerank
            top_k: 返回结果数

        Returns:
            评估指标字典
        """
        ndcg_scores = []
        mrr_scores = []
        precision_scores = []

        for item in self.dataset.dataset:
            query = item['query']
            namespace = item['namespace']
            relevance_scores = self.dataset.get_relevance_scores(query)

            # 执行检索
            results = await self.retrieval_service.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                use_rerank=use_rerank
            )

            # 提取文档ID
            retrieved_docs = [r['document_id'] for r in results]

            # 计算指标
            ndcg_scores.append(calculate_ndcg(retrieved_docs, relevance_scores, k=top_k))
            mrr_scores.append(calculate_mrr(retrieved_docs, relevance_scores))
            precision_scores.append(calculate_precision_at_k(retrieved_docs, relevance_scores, k=top_k))

        # 返回平均指标
        return {
            'ndcg@10': np.mean(ndcg_scores),
            'mrr': np.mean(mrr_scores),
            'precision@10': np.mean(precision_scores),
            'num_queries': len(self.dataset.dataset)
        }

    async def compare_with_without_rerank(
        self,
        top_k: int = 10
    ) -> Dict[str, Dict[str, float]]:
        """对比 Rerank 前后效果"""

        print("评估无 Rerank 的效果...")
        without_rerank = await self.evaluate(use_rerank=False, top_k=top_k)

        print("评估有 Rerank 的效果...")
        with_rerank = await self.evaluate(use_rerank=True, top_k=top_k)

        # 计算提升
        improvement = {
            metric: (with_rerank[metric] - without_rerank[metric]) / without_rerank[metric] * 100
            if without_rerank[metric] > 0 else 0
            for metric in ['ndcg@10', 'mrr', 'precision@10']
        }

        return {
            'without_rerank': without_rerank,
            'with_rerank': with_rerank,
            'improvement_%': improvement
        }
```

**4. 评估脚本**

```python
# backend/scripts/evaluate_rerank.py

import asyncio
from app.database import get_db
from app.evaluation.rerank_dataset import RerankEvaluationDataset
from app.evaluation.rerank_evaluator import RerankEvaluator

async def main():
    # 加载评估数据集
    dataset = RerankEvaluationDataset('evaluation_data/rerank_dataset.json')

    # 创建评估器
    db = next(get_db())
    evaluator = RerankEvaluator(db, dataset)

    # 执行对比评估
    results = await evaluator.compare_with_without_rerank(top_k=10)

    # 打印结果
    print("\n" + "="*60)
    print("Rerank 效果评估结果")
    print("="*60)

    print("\n无 Rerank:")
    for metric, value in results['without_rerank'].items():
        print(f"  {metric}: {value:.4f}")

    print("\n有 Rerank:")
    for metric, value in results['with_rerank'].items():
        print(f"  {metric}: {value:.4f}")

    print("\n提升幅度:")
    for metric, value in results['improvement_%'].items():
        print(f"  {metric}: +{value:.2f}%")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
```

**实施步骤**:
1. 创建评估数据集 (标注相关性)
2. 实现评估指标计算 (NDCG, MRR, Precision@K)
3. 实现评估执行器
4. 编写评估脚本
5. 运行评估并记录结果
6. 生成评估报告

---

### 📋 任务 8.2: 敏感领域保护

**目标**: 为敏感领域添加额外的安全保护措施

#### 设计方案

**1. 敏感领域标记**

扩展 `KnowledgeDomain` 模型:

```python
# backend/app/models/knowledge_domain.py (扩展)

class KnowledgeDomain(Base):
    # ... 现有字段 ...

    # 新增敏感领域标记
    is_sensitive = Column(Boolean, default=False, comment="是否敏感领域")
    sensitivity_level = Column(Integer, default=0, comment="敏感级别 0-5")
    requires_mfa = Column(Boolean, default=False, comment="是否需要多因素认证")
    require_approval = Column(Boolean, default=False, comment="查询是否需要审批")
    max_daily_queries = Column(Integer, comment="每日最大查询次数")
    allowed_ip_ranges = Column(Text, comment="允许的IP段 JSON格式")
```

**2. 增强权限检查**

```python
# backend/app/middleware/sensitive_domain.py

from fastapi import Request, HTTPException
from app.models.knowledge_domain import KnowledgeDomain
from app.models.query_approval import QueryApproval

async def check_sensitive_domain_access(
    namespace: str,
    current_user: User,
    request: Request,
    db: Session
) -> None:
    """检查敏感领域访问权限"""

    # 获取领域信息
    domain = db.query(KnowledgeDomain).filter(
        KnowledgeDomain.namespace == namespace
    ).first()

    if not domain or not domain.is_sensitive:
        return  # 非敏感领域,跳过额外检查

    # 检查 IP 白名单
    if domain.allowed_ip_ranges:
        client_ip = request.client.host
        allowed_ranges = json.loads(domain.allowed_ip_ranges)
        if not is_ip_in_ranges(client_ip, allowed_ranges):
            raise HTTPException(
                status_code=403,
                detail=f"您的IP地址 ({client_ip}) 无权访问此敏感领域"
            )

    # 检查多因素认证
    if domain.requires_mfa:
        if not hasattr(current_user, 'mfa_verified') or not current_user.mfa_verified:
            raise HTTPException(
                status_code=403,
                detail="访问此领域需要多因素认证"
            )

    # 检查每日查询限制
    if domain.max_daily_queries:
        today_queries = db.query(UserQuery).filter(
            UserQuery.user_id == current_user.id,
            UserQuery.namespace == namespace,
            UserQuery.created_at >= datetime.now().date().isoformat()
        ).count()

        if today_queries >= domain.max_daily_queries:
            raise HTTPException(
                status_code=429,
                detail=f"您今日对此领域的查询次数已达上限 ({domain.max_daily_queries})"
            )

    # 检查是否需要审批
    if domain.require_approval:
        # 创建审批请求
        approval = QueryApproval(
            user_id=current_user.id,
            namespace=namespace,
            status='pending'
        )
        db.add(approval)
        db.commit()

        raise HTTPException(
            status_code=202,
            detail="您的查询请求已提交,等待管理员审批"
        )
```

**3. 查询审计日志**

```python
# backend/app/models/sensitive_query_log.py

class SensitiveQueryLog(Base):
    """敏感查询日志"""
    __tablename__ = 'sensitive_query_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    namespace = Column(String(100), nullable=False)
    query_text = Column(Text, nullable=False)
    client_ip = Column(String(50))
    user_agent = Column(String(500))
    access_time = Column(String)
    result_count = Column(Integer)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer)
    approved_at = Column(String)
```

**4. 数据脱敏**

```python
# backend/app/services/data_masking.py

import re

class DataMasking:
    """数据脱敏服务"""

    @staticmethod
    def mask_phone(text: str) -> str:
        """脱敏手机号"""
        return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)

    @staticmethod
    def mask_email(text: str) -> str:
        """脱敏邮箱"""
        return re.sub(r'(\w{2})\w+(@\w+\.\w+)', r'\1***\2', text)

    @staticmethod
    def mask_id_card(text: str) -> str:
        """脱敏身份证号"""
        return re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', text)

    @staticmethod
    def mask_sensitive_content(
        content: str,
        sensitivity_level: int
    ) -> str:
        """根据敏感级别脱敏内容"""
        if sensitivity_level >= 3:
            content = DataMasking.mask_phone(content)
            content = DataMasking.mask_email(content)
            content = DataMasking.mask_id_card(content)

        return content
```

**实施步骤**:
1. 扩展 KnowledgeDomain 模型添加敏感标记
2. 实现增强权限检查中间件
3. 创建敏感查询日志表
4. 实现数据脱敏服务
5. 集成到查询 API
6. 添加审批工作流
7. 创建审计日志查看界面
8. 编写单元测试

---

## P2 任务实施方案

### 📋 任务 9.3: 日志聚合和追踪

**目标**: 集成分布式追踪和日志聚合系统

#### 技术方案

**1. Loki 日志聚合**

```yaml
# monitoring/docker-compose.yml (扩展)

services:
  loki:
    image: grafana/loki:latest
    container_name: rag-loki
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:latest
    container_name: rag-promtail
    volumes:
      - /var/log:/var/log:ro
      - ./promtail/promtail-config.yml:/etc/promtail/config.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring
```

**2. Jaeger 分布式追踪**

```yaml
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: rag-jaeger
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
    environment:
      - COLLECTOR_ZIPKIN_HTTP_PORT=9411
    networks:
      - monitoring
```

**3. OpenTelemetry 集成**

```python
# backend/app/telemetry/__init__.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_telemetry(app):
    """设置 OpenTelemetry 追踪"""

    # 配置 Tracer Provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # 配置 Jaeger Exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )

    # 添加 Span Processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # 自动 instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    return tracer
```

---

### 📋 任务 11.1: 领域关系管理

**目标**: 管理领域之间的层级关系和关联关系

#### 设计方案

**1. 领域关系模型**

```python
# backend/app/models/domain_relationship.py

class DomainRelationship(Base):
    """领域关系表"""
    __tablename__ = 'domain_relationships'

    id = Column(Integer, primary_key=True)
    parent_namespace = Column(String(100), nullable=False)
    child_namespace = Column(String(100), nullable=False)
    relationship_type = Column(String(50))  # parent_child/related/excluded
    weight = Column(Float, default=1.0)  # 关系权重
    is_active = Column(Boolean, default=True)
    created_at = Column(String)

    __table_args__ = (
        UniqueConstraint('parent_namespace', 'child_namespace'),
    )
```

**2. 领域层级查询**

```python
# backend/app/services/domain_hierarchy.py

class DomainHierarchyService:
    """领域层级服务"""

    def get_parent_domains(self, namespace: str) -> List[str]:
        """获取父级领域"""
        pass

    def get_child_domains(self, namespace: str) -> List[str]:
        """获取子领域"""
        pass

    def get_related_domains(self, namespace: str) -> List[str]:
        """获取关联领域"""
        pass

    def search_with_hierarchy(
        self,
        query: str,
        namespace: str,
        include_children: bool = True,
        include_related: bool = False
    ):
        """基于层级关系的检索"""
        pass
```

---

### 📋 任务 11.2: 会话领域上下文

**目标**: 在对话会话中维护领域上下文,实现智能领域切换

#### 设计方案

**1. 会话上下文模型**

```python
# backend/app/models/session_context.py

class SessionContext(Base):
    """会话上下文表"""
    __tablename__ = 'session_contexts'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    current_namespace = Column(String(100))
    namespace_history = Column(Text)  # JSON 格式的历史
    last_queries = Column(Text)  # 最近的查询
    confidence_scores = Column(Text)  # 各领域置信度
    updated_at = Column(String)
```

**2. 上下文管理服务**

```python
# backend/app/services/session_context.py

class SessionContextManager:
    """会话上下文管理器"""

    def update_context(
        self,
        session_id: str,
        query: str,
        classified_namespace: str,
        confidence: float
    ):
        """更新会话上下文"""
        pass

    def get_context_namespace(
        self,
        session_id: str
    ) -> Optional[str]:
        """根据上下文推荐领域"""
        pass

    def should_switch_domain(
        self,
        session_id: str,
        new_namespace: str,
        confidence: float
    ) -> bool:
        """判断是否应该切换领域"""
        pass
```

---

### 📋 任务 11.3: 数据分析和优化

**目标**: 分析系统使用数据,提供优化建议

#### 设计方案

**1. 数据分析服务**

```python
# backend/app/services/analytics.py

class AnalyticsService:
    """数据分析服务"""

    def analyze_query_patterns(
        self,
        time_range: str = '7d'
    ) -> Dict:
        """分析查询模式

        Returns:
            - 热门查询
            - 查询时间分布
            - 领域使用频率
        """
        pass

    def analyze_domain_performance(
        self,
        namespace: str
    ) -> Dict:
        """分析领域性能

        Returns:
            - 平均延迟
            - 失败率
            - 文档覆盖率
        """
        pass

    def suggest_optimizations(self) -> List[Dict]:
        """生成优化建议

        Returns:
            - 需要补充文档的领域
            - 可以合并的相似查询
            - 性能瓶颈点
        """
        pass
```

**2. 优化建议生成器**

```python
# backend/app/services/optimization_advisor.py

class OptimizationAdvisor:
    """优化建议生成器"""

    def check_document_coverage(self) -> List[Dict]:
        """检查文档覆盖率"""
        # 分析哪些查询无法找到相关文档
        # 建议补充哪些类型的文档
        pass

    def identify_slow_queries(self) -> List[Dict]:
        """识别慢查询"""
        # 分析 P95 延迟过高的查询
        # 建议优化方案
        pass

    def suggest_index_optimization(self) -> List[Dict]:
        """建议索引优化"""
        # 分析检索效率
        # 建议添加索引或调整参数
        pass
```

---

## 实施优先级建议

### 立即实施 (1-2 周)

1. **任务 8.1: 领域级权限控制** - 安全性关键
2. **任务 10.2: Rerank 效果评估** - 验证 P0 实现效果

### 近期实施 (2-4 周)

3. **任务 8.2: 敏感领域保护** - 数据安全重要
4. **任务 9.3: 日志聚合和追踪** - 完善监控体系

### 中期实施 (1-2 个月)

5. **任务 11.1: 领域关系管理** - 增强功能
6. **任务 11.2: 会话领域上下文** - 用户体验提升

### 长期实施 (2-3 个月)

7. **任务 11.3: 数据分析和优化** - 持续优化

---

## 总结

### Phase 4 成果

**P0 任务** (100% 完成):
- ✅ 完整实现 Reranker 精排功能
- ✅ 完整实现 Prometheus 指标采集
- ✅ 完整实现 Grafana 监控大盘

**P1/P2 任务** (方案完成):
- 📋 详细的实施方案和代码示例
- 📋 清晰的实施步骤和优先级
- 📋 可直接参考的技术方案

### 文档成果

1. **RERANKER_IMPLEMENTATION.md** - Reranker 实现文档
2. **PROMETHEUS_METRICS_IMPLEMENTATION.md** - 指标采集文档
3. **GRAFANA_MONITORING_IMPLEMENTATION.md** - 监控大盘文档
4. **PHASE4_COMPLETION_REPORT.md** - 本报告

### 技术栈

- **精排**: BAAI/bge-reranker-v2-m3, sentence-transformers
- **监控**: Prometheus, Grafana, Alertmanager
- **权限**: SQLAlchemy, FastAPI Depends
- **日志**: Loki, Promtail, OpenTelemetry
- **追踪**: Jaeger, OpenTelemetry

### 后续建议

1. 按优先级逐步实施 P1/P2 任务
2. 根据实际业务需求调整实施顺序
3. 持续收集用户反馈优化系统
4. 定期评估系统性能和安全性

---

**报告完成时间**: 2025-11-19
**Phase 4 状态**: P0 全部完成,P1/P2 方案就绪 ✅
