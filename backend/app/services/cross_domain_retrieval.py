"""
跨领域检索服务

支持在多个知识领域中并行检索,并智能融合结果
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.knowledge_domain import KnowledgeDomain
from app.services.hybrid_retrieval import get_hybrid_retrieval
from app.services.domain_classifier import DomainClassificationResult
from app.config.logging_config import get_app_logger

logger = get_app_logger()


class CrossDomainRetrieval:
    """跨领域检索服务"""

    def __init__(self, db: Session):
        self.db = db
        self.hybrid_retrieval = get_hybrid_retrieval(db)

    async def search_across_domains(
        self,
        query: str,
        namespaces: Optional[List[str]] = None,
        top_k: int = 10,
        domain_weights: Optional[Dict[str, float]] = None,
        alpha: float = 0.5
    ) -> List[Tuple[Dict[str, Any], str, float]]:
        """
        跨领域检索

        Args:
            query: 查询文本
            namespaces: 指定领域列表(None = 所有活跃领域)
            top_k: 总返回结果数
            domain_weights: 领域权重字典
            alpha: 混合检索权重

        Returns:
            List[Tuple[chunk, namespace, score]]: 文档块、领域、得分的元组列表
        """
        try:
            # 1. 确定检索领域
            if namespaces is None:
                domains = self.db.query(KnowledgeDomain).filter(
                    KnowledgeDomain.is_active == True
                ).all()
                namespaces = [d.namespace for d in domains]
                logger.info(f"跨领域检索: 使用所有活跃领域 {namespaces}")
            else:
                logger.info(f"跨领域检索: 指定领域 {namespaces}")

            if len(namespaces) == 0:
                logger.warning("没有可用的领域")
                return []

            # 2. 并行检索所有领域
            tasks = []
            for namespace in namespaces:
                task = self._search_single_domain(
                    query=query,
                    namespace=namespace,
                    top_k=top_k * 2,  # 每个领域获取更多结果用于融合
                    alpha=alpha
                )
                tasks.append(task)

            domain_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 3. 处理异常和空结果
            valid_results = []
            for namespace, result in zip(namespaces, domain_results):
                if isinstance(result, Exception):
                    logger.error(f"领域 {namespace} 检索失败: {result}")
                    continue
                if result:
                    valid_results.append((namespace, result))

            if not valid_results:
                logger.warning("所有领域检索都失败或无结果")
                return []

            logger.info(f"成功检索 {len(valid_results)}/{len(namespaces)} 个领域")

            # 4. 计算领域权重
            if domain_weights is None:
                domain_weights = {ns: 1.0 for ns in namespaces}

            # 5. 合并并重排序
            all_results = []

            for namespace, chunks in valid_results:
                weight = domain_weights.get(namespace, 1.0)

                for rank, chunk in enumerate(chunks, 1):
                    # 计算综合得分(结合排名和领域权重)
                    # 使用 1/rank 作为基础分数,权重调整
                    score = (1 / rank) * weight

                    # 如果chunk有原始得分,也考虑进去
                    if 'fusion_score' in chunk:
                        score = (score + chunk['fusion_score']) / 2
                    elif 'similarity' in chunk:
                        score = (score + chunk['similarity']) / 2

                    all_results.append((chunk, namespace, score))

            # 6. 全局排序
            all_results.sort(key=lambda x: x[2], reverse=True)

            # 7. 去重(同一文档块只保留得分最高的)
            seen_chunks = set()
            unique_results = []

            for chunk, namespace, score in all_results:
                chunk_id = chunk['id']
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    unique_results.append((chunk, namespace, score))

                if len(unique_results) >= top_k:
                    break

            logger.info(f"跨领域检索完成: 返回 {len(unique_results)} 个结果")
            return unique_results

        except Exception as e:
            logger.error(f"跨领域检索失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def _search_single_domain(
        self,
        query: str,
        namespace: str,
        top_k: int,
        alpha: float
    ) -> List[Dict[str, Any]]:
        """
        单领域检索(内部方法)

        Args:
            query: 查询文本
            namespace: 领域命名空间
            top_k: 返回结果数
            alpha: 混合检索权重

        Returns:
            文档块列表
        """
        try:
            return await self.hybrid_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                alpha=alpha
            )
        except Exception as e:
            logger.error(f"领域 {namespace} 检索失败: {e}")
            return []

    def calculate_domain_weights(
        self,
        classification_result: DomainClassificationResult,
        boost_primary: float = 2.0,
        boost_alternatives: float = 0.5
    ) -> Dict[str, float]:
        """
        基于分类结果计算领域权重

        Args:
            classification_result: 领域分类结果
            boost_primary: 主领域权重倍数
            boost_alternatives: 备选领域基础权重

        Returns:
            领域权重字典
        """
        weights = {
            classification_result.namespace: boost_primary
        }

        # 备选领域降权
        for alt in classification_result.alternatives:
            namespace = alt.get('namespace')
            confidence = alt.get('confidence', 0)
            if namespace:
                weights[namespace] = boost_alternatives + confidence

        return weights

    def group_results_by_domain(
        self,
        results: List[Tuple[Dict[str, Any], str, float]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按领域分组结果

        Args:
            results: 检索结果列表

        Returns:
            按领域分组的字典
        """
        grouped = {}

        for chunk, namespace, score in results:
            if namespace not in grouped:
                grouped[namespace] = []

            chunk_with_score = chunk.copy()
            chunk_with_score['cross_domain_score'] = score

            grouped[namespace].append(chunk_with_score)

        return grouped

    async def search_with_classification(
        self,
        query: str,
        classification_result: DomainClassificationResult,
        top_k: int = 10,
        alpha: float = 0.5,
        include_all_domains: bool = False
    ) -> Tuple[List[Tuple[Dict, str, float]], Dict[str, float]]:
        """
        基于分类结果进行跨领域检索

        Args:
            query: 查询文本
            classification_result: 分类结果
            top_k: 返回结果数
            alpha: 混合检索权重
            include_all_domains: 是否包含所有活跃领域

        Returns:
            (检索结果, 使用的权重)
        """
        # 计算权重
        weights = self.calculate_domain_weights(classification_result)

        # 确定检索领域
        if include_all_domains:
            namespaces = None  # 所有活跃领域
        else:
            # 只检索主领域和备选领域
            namespaces = [classification_result.namespace]
            namespaces.extend([
                alt['namespace']
                for alt in classification_result.alternatives
                if alt.get('namespace')
            ])

        # 执行检索
        results = await self.search_across_domains(
            query=query,
            namespaces=namespaces,
            top_k=top_k,
            domain_weights=weights,
            alpha=alpha
        )

        return results, weights


def get_cross_domain_retrieval(db: Session) -> CrossDomainRetrieval:
    """获取跨领域检索服务实例"""
    return CrossDomainRetrieval(db)
