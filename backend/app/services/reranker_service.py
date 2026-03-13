"""
Reranker 精排服务

使用 BAAI/bge-reranker-v2-m3 模型对检索结果进行重排序,提升检索质量
"""

import asyncio
import logging
from typing import List, Optional, Tuple
from sentence_transformers import CrossEncoder
import numpy as np

from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class RerankerService:
    """Rerank 精排服务

    使用 Cross-Encoder 模型对检索结果进行重排序
    支持批量推理和异步处理
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        max_length: int = 512,
        batch_size: int = 32,
        device: Optional[str] = None
    ):
        """
        初始化 Reranker 服务

        Args:
            model_name: Reranker 模型名称
            max_length: 最大序列长度
            batch_size: 批量推理大小
            device: 设备 (None=自动选择, 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device
        self.model: Optional[CrossEncoder] = None
        self._initialized = False

    async def initialize(self):
        """加载 Reranker 模型"""
        if self._initialized:
            logger.info(f"Reranker 模型已加载,跳过初始化")
            return

        try:
            logger.info(f"开始加载 Reranker 模型: {self.model_name}")

            # 在线程池中加载模型(避免阻塞事件循环)
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: CrossEncoder(
                    self.model_name,
                    max_length=self.max_length,
                    device=self.device
                )
            )

            self._initialized = True
            logger.info(
                f"Reranker 模型加载成功: {self.model_name}, "
                f"device={self.model.device}, max_length={self.max_length}"
            )
        except Exception as e:
            logger.error(f"加载 Reranker 模型失败: {e}", exc_info=True)
            raise

    def _ensure_initialized(self):
        """确保模型已初始化"""
        if not self._initialized or self.model is None:
            raise RuntimeError(
                "Reranker 模型未初始化,请先调用 initialize() 方法"
            )

    async def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: Optional[int] = None,
        return_scores: bool = False
    ) -> List[DocumentChunk] | List[Tuple[DocumentChunk, float]]:
        """
        对文档块进行重排序

        Args:
            query: 查询文本
            chunks: 候选文档块列表
            top_k: 返回前 K 个结果 (None=全部)
            return_scores: 是否返回分数

        Returns:
            重排序后的文档块列表,或 [(chunk, score), ...] 如果 return_scores=True
        """
        self._ensure_initialized()

        if len(chunks) == 0:
            return []

        if len(chunks) == 1:
            # 只有一个结果,直接返回
            if return_scores:
                return [(chunks[0], 1.0)]
            return chunks

        try:
            # 1. 构建 query-chunk 对
            pairs = [[query, chunk.content] for chunk in chunks]

            # 2. 批量推理
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self._predict_batch,
                pairs
            )

            # 3. 排序
            chunk_scores = list(zip(chunks, scores))
            chunk_scores.sort(key=lambda x: x[1], reverse=True)

            # 4. 返回 Top-K
            if top_k is not None:
                chunk_scores = chunk_scores[:top_k]

            # 5. 返回格式
            if return_scores:
                return chunk_scores
            else:
                return [chunk for chunk, _ in chunk_scores]

        except Exception as e:
            logger.error(f"Rerank 失败: {e}", exc_info=True)
            # 降级:返回原始结果
            logger.warning("Rerank 失败,返回原始检索结果")
            if return_scores:
                return [(chunk, 0.0) for chunk in chunks[:top_k]] if top_k else [(chunk, 0.0) for chunk in chunks]
            return chunks[:top_k] if top_k else chunks

    def _predict_batch(self, pairs: List[List[str]]) -> np.ndarray:
        """批量推理(在线程池中执行)

        Args:
            pairs: [[query, chunk_content], ...] 列表

        Returns:
            scores: numpy array of scores
        """
        # 批量推理,避免多次模型调用
        all_scores = []

        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i:i + self.batch_size]
            scores = self.model.predict(batch)
            all_scores.extend(scores)

        return np.array(all_scores)

    async def rerank_batch(
        self,
        queries: List[str],
        chunks_list: List[List[DocumentChunk]],
        top_k: int = 5,
        return_scores: bool = False
    ) -> List[List[DocumentChunk]] | List[List[Tuple[DocumentChunk, float]]]:
        """
        批量 Rerank(并发优化)

        Args:
            queries: 查询列表
            chunks_list: 文档块列表的列表
            top_k: 每个查询返回前 K 个
            return_scores: 是否返回分数

        Returns:
            重排序后的文档块列表的列表
        """
        self._ensure_initialized()

        if len(queries) != len(chunks_list):
            raise ValueError("queries 和 chunks_list 长度必须相同")

        # 并发执行多个 rerank 任务
        tasks = [
            self.rerank(query, chunks, top_k, return_scores)
            for query, chunks in zip(queries, chunks_list)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量 Rerank 第 {i} 个查询失败: {result}")
                # 降级:返回原始结果
                chunks = chunks_list[i][:top_k]
                if return_scores:
                    final_results.append([(chunk, 0.0) for chunk in chunks])
                else:
                    final_results.append(chunks)
            else:
                final_results.append(result)

        return final_results

    async def score_pairs(
        self,
        query_chunk_pairs: List[Tuple[str, str]]
    ) -> List[float]:
        """
        计算 query-chunk 对的相关性分数

        Args:
            query_chunk_pairs: [(query, chunk_content), ...] 列表

        Returns:
            scores: 相关性分数列表
        """
        self._ensure_initialized()

        if len(query_chunk_pairs) == 0:
            return []

        try:
            # 转换为模型输入格式
            pairs = [[query, chunk] for query, chunk in query_chunk_pairs]

            # 批量推理
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self._predict_batch,
                pairs
            )

            return scores.tolist()

        except Exception as e:
            logger.error(f"计算相关性分数失败: {e}", exc_info=True)
            # 降级:返回默认分数
            return [0.0] * len(query_chunk_pairs)

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "device": str(self.model.device) if self.model else None,
            "initialized": self._initialized
        }


# 全局单例
_reranker_instance: Optional[RerankerService] = None


def get_reranker(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    max_length: int = 512,
    batch_size: int = 32
) -> RerankerService:
    """
    获取全局 Reranker 实例(单例模式)

    Args:
        model_name: 模型名称
        max_length: 最大序列长度
        batch_size: 批量大小

    Returns:
        RerankerService 实例
    """
    global _reranker_instance

    if _reranker_instance is None:
        _reranker_instance = RerankerService(
            model_name=model_name,
            max_length=max_length,
            batch_size=batch_size
        )
        logger.info("创建全局 Reranker 实例")

    return _reranker_instance


async def initialize_reranker():
    """初始化全局 Reranker 实例"""
    reranker = get_reranker()
    await reranker.initialize()
