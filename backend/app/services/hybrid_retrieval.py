"""
混合检索服务

结合向量检索和BM25检索,使用RRF(Reciprocal Rank Fusion)融合算法
支持 Rerank 精排优化
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from app.services.vector_retrieval import vector_retrieval_service
from app.services.bm25_retrieval import get_bm25_service
from app.services.reranker_service import get_reranker
from app.models.document import DocumentChunk
from app.config.logging_config import get_app_logger

logger = get_app_logger()


class HybridRetrieval:
    """混合检索(向量 + BM25 + Rerank)"""

    def __init__(self, db: Session, enable_rerank: bool = False):
        self.db = db
        self.vector_retrieval = vector_retrieval_service
        self.bm25_retrieval = get_bm25_service(db)
        self.rrf_k = 60  # RRF算法参数
        self.enable_rerank = enable_rerank
        self.reranker = get_reranker() if enable_rerank else None

    async def search_by_namespace(
        self,
        query: str,
        namespace: str,
        top_k: int = 10,
        alpha: float = 0.5,  # 向量检索权重
        use_rrf: bool = True,
        use_rerank: Optional[bool] = None  # None=使用默认设置
    ) -> List[Dict[str, Any]]:
        """
        在指定领域内进行混合检索

        Args:
            query: 查询文本
            namespace: 领域命名空间
            top_k: 返回结果数量
            alpha: 向量检索权重(0.0-1.0)
                   0.0 = 纯BM25, 1.0 = 纯向量, 0.5 = 均衡
            use_rrf: 是否使用RRF融合算法(否则使用加权平均)
            use_rerank: 是否使用 Rerank 精排 (None=使用默认设置)

        Returns:
            List[Dict]: 混合检索结果
        """
        try:
            # 确定是否使用 Rerank
            should_rerank = use_rerank if use_rerank is not None else self.enable_rerank

            # 如果使用 Rerank,需要获取更多候选结果
            candidate_k = top_k * 3 if should_rerank else top_k * 2

            logger.info(
                f"混合检索: {namespace}, alpha={alpha}, use_rrf={use_rrf}, "
                f"use_rerank={should_rerank}, candidate_k={candidate_k}"
            )

            # 1. 并行执行两种检索
            vector_task = self.vector_retrieval.search_by_namespace(
                db=self.db,
                query_text=query,
                namespace=namespace,
                top_k=candidate_k  # 获取更多结果用于融合和重排
            )

            bm25_task = self.bm25_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=candidate_k
            )

            vector_results, bm25_results = await asyncio.gather(
                vector_task,
                bm25_task,
                return_exceptions=True
            )

            # 处理异常
            if isinstance(vector_results, Exception):
                logger.error(f"向量检索失败: {vector_results}")
                vector_results = []

            if isinstance(bm25_results, Exception):
                logger.error(f"BM25检索失败: {bm25_results}")
                bm25_results = []

            logger.info(f"向量检索: {len(vector_results)} 结果, BM25检索: {len(bm25_results)} 结果")

            # 2. 如果两种方法都没结果,直接返回
            if not vector_results and not bm25_results:
                return []

            # 3. 如果只有一种方法有结果,返回该方法结果
            if not vector_results:
                logger.info("仅使用BM25结果")
                initial_results = [chunk for chunk, score in bm25_results[:candidate_k]]
            elif not bm25_results:
                logger.info("仅使用向量检索结果")
                initial_results = vector_results[:candidate_k]
            else:
                # 4. 融合两种检索结果
                if use_rrf:
                    initial_results = self._rrf_fusion(
                        vector_results, bm25_results, alpha, candidate_k
                    )
                else:
                    initial_results = self._weighted_fusion(
                        vector_results, bm25_results, alpha, candidate_k
                    )

            # 5. Rerank 精排
            if should_rerank and self.reranker and len(initial_results) > 1:
                try:
                    logger.info(f"开始 Rerank,候选数: {len(initial_results)}")

                    # 将 Dict 转换为 DocumentChunk 对象
                    chunks = self._convert_to_chunks(initial_results)

                    # Rerank
                    reranked_chunks = await self.reranker.rerank(
                        query=query,
                        chunks=chunks,
                        top_k=top_k,
                        return_scores=False
                    )

                    # 转换回 Dict 格式
                    final_results = self._convert_from_chunks(reranked_chunks)

                    logger.info(f"Rerank 完成,返回 {len(final_results)} 个结果")
                    return final_results

                except Exception as e:
                    logger.error(f"Rerank 失败,降级为融合结果: {e}")
                    return initial_results[:top_k]
            else:
                # 不使用 Rerank,直接返回融合结果
                logger.info(f"混合检索完成(无Rerank),返回 {len(initial_results[:top_k])} 个结果")
                return initial_results[:top_k]

        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []

    def _rrf_fusion(
        self,
        vector_results: List[Dict],
        bm25_results: List[Tuple[Dict, float]],
        alpha: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        使用RRF(Reciprocal Rank Fusion)算法融合结果

        RRF Score = sum(weight / (k + rank))

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果(带分数)
            alpha: 向量检索权重
            top_k: 返回结果数

        Returns:
            融合后的结果列表
        """
        scores = {}

        # 向量检索得分
        for rank, chunk in enumerate(vector_results, 1):
            chunk_id = chunk['id']
            rrf_score = alpha * (1 / (self.rrf_k + rank))
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score

        # BM25 得分
        beta = 1 - alpha  # BM25权重
        for rank, (chunk, _) in enumerate(bm25_results, 1):
            chunk_id = chunk['id']
            rrf_score = beta * (1 / (self.rrf_k + rank))
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score

        # 排序
        sorted_chunk_ids = sorted(
            scores.keys(),
            key=lambda x: scores[x],
            reverse=True
        )

        # 构建结果(从向量检索结果中获取完整数据)
        chunk_dict = {c['id']: c for c in vector_results}
        # 添加BM25独有的结果
        for chunk, _ in bm25_results:
            if chunk['id'] not in chunk_dict:
                chunk_dict[chunk['id']] = chunk

        result = []
        for chunk_id in sorted_chunk_ids[:top_k]:
            if chunk_id in chunk_dict:
                chunk = chunk_dict[chunk_id].copy()
                chunk['fusion_score'] = scores[chunk_id]
                result.append(chunk)

        return result

    def _weighted_fusion(
        self,
        vector_results: List[Dict],
        bm25_results: List[Tuple[Dict, float]],
        alpha: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        使用加权平均融合结果

        Weighted Score = alpha * vector_score + (1-alpha) * bm25_score

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25检索结果(带分数)
            alpha: 向量检索权重
            top_k: 返回结果数

        Returns:
            融合后的结果列表
        """
        scores = {}

        # 归一化向量检索分数
        if vector_results and 'similarity' in vector_results[0]:
            vector_scores = [c.get('similarity', 0) for c in vector_results]
            max_vector = max(vector_scores) if vector_scores else 1
            min_vector = min(vector_scores) if vector_scores else 0
            range_vector = max_vector - min_vector if max_vector != min_vector else 1

            for chunk in vector_results:
                chunk_id = chunk['id']
                normalized = (chunk.get('similarity', 0) - min_vector) / range_vector
                scores[chunk_id] = alpha * normalized

        # 归一化BM25分数
        if bm25_results:
            bm25_scores = [score for _, score in bm25_results]
            max_bm25 = max(bm25_scores) if bm25_scores else 1
            min_bm25 = min(bm25_scores) if bm25_scores else 0
            range_bm25 = max_bm25 - min_bm25 if max_bm25 != min_bm25 else 1

            for chunk, score in bm25_results:
                chunk_id = chunk['id']
                normalized = (score - min_bm25) / range_bm25
                current_score = scores.get(chunk_id, 0)
                scores[chunk_id] = current_score + (1 - alpha) * normalized

        # 排序
        sorted_chunk_ids = sorted(
            scores.keys(),
            key=lambda x: scores[x],
            reverse=True
        )

        # 构建结果
        chunk_dict = {c['id']: c for c in vector_results}
        for chunk, _ in bm25_results:
            if chunk['id'] not in chunk_dict:
                chunk_dict[chunk['id']] = chunk

        result = []
        for chunk_id in sorted_chunk_ids[:top_k]:
            if chunk_id in chunk_dict:
                chunk = chunk_dict[chunk_id].copy()
                chunk['fusion_score'] = scores[chunk_id]
                result.append(chunk)

        return result

    def _convert_to_chunks(self, results: List[Dict[str, Any]]) -> List[DocumentChunk]:
        """将 Dict 结果转换为 DocumentChunk 对象

        Args:
            results: Dict 格式的检索结果

        Returns:
            DocumentChunk 对象列表
        """
        chunks = []
        for result in results:
            # 从数据库查询完整的 DocumentChunk 对象
            chunk = self.db.query(DocumentChunk).filter(
                DocumentChunk.id == result['id']
            ).first()

            if chunk:
                chunks.append(chunk)
            else:
                logger.warning(f"未找到 chunk: {result['id']}")

        return chunks

    def _convert_from_chunks(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """将 DocumentChunk 对象转换回 Dict 格式

        Args:
            chunks: DocumentChunk 对象列表

        Returns:
            Dict 格式的结果列表
        """
        results = []
        for chunk in chunks:
            result = {
                'id': chunk.id,
                'document_id': chunk.document_id,
                'chunk_index': chunk.chunk_index,
                'content': chunk.content,
                'metadata': chunk.metadata,
                'namespace': chunk.namespace,
                'domain_tags': chunk.domain_tags
            }
            results.append(result)

        return results


def get_hybrid_retrieval(db: Session, enable_rerank: bool = False) -> HybridRetrieval:
    """获取混合检索服务实例

    Args:
        db: 数据库会话
        enable_rerank: 是否启用 Rerank 精排

    Returns:
        HybridRetrieval 实例
    """
    return HybridRetrieval(db, enable_rerank=enable_rerank)
