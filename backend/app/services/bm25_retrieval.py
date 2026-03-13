"""
BM25 关键词检索服务

提供基于 BM25 算法的文本检索功能
使用 jieba 进行中文分词
"""
import time
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config.logging_config import get_app_logger

logger = get_app_logger()


class BM25Retrieval:
    """BM25 关键词检索"""

    def __init__(self, db: Session):
        self.db = db
        # 缓存索引,避免重复构建
        self._corpus = {}
        self._bm25 = {}
        self._last_update = {}
        self.cache_ttl = 300  # 5分钟缓存

    def _tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词

        Args:
            text: 输入文本

        Returns:
            分词后的token列表
        """
        try:
            import jieba
            # 使用jieba分词
            tokens = list(jieba.cut(text))
            # 过滤空白和单字符token
            tokens = [t.strip() for t in tokens if len(t.strip()) > 1]
            return tokens
        except ImportError:
            logger.warning("jieba未安装,使用简单分词")
            # fallback到简单空格分词
            return text.lower().split()

    async def initialize_for_namespace(self, namespace: str):
        """
        为指定领域初始化 BM25 索引

        Args:
            namespace: 领域命名空间
        """
        try:
            # 检查缓存是否有效
            now = time.time()
            if (namespace in self._bm25 and
                namespace in self._last_update and
                now - self._last_update[namespace] < self.cache_ttl):
                logger.info(f"使用缓存的BM25索引: {namespace}")
                return

            logger.info(f"为领域 '{namespace}' 构建BM25索引...")

            # 1. 加载领域内所有文档块
            query_sql = """
                SELECT id, content
                FROM document_chunks
                WHERE namespace = :namespace AND content IS NOT NULL
                ORDER BY document_id, chunk_index
            """

            result = self.db.execute(text(query_sql), {"namespace": namespace})
            chunks = list(result)

            if len(chunks) == 0:
                logger.warning(f"领域 '{namespace}' 没有文档块")
                self._corpus[namespace] = []
                self._bm25[namespace] = None
                return

            logger.info(f"加载了 {len(chunks)} 个文档块")

            # 2. 分词构建语料库
            corpus = []
            chunk_ids = []

            for row in chunks:
                tokens = self._tokenize(row.content)
                corpus.append(tokens)
                chunk_ids.append(row.id)

            # 3. 构建 BM25 索引
            try:
                from rank_bm25 import BM25Okapi

                self._corpus[namespace] = chunk_ids
                self._bm25[namespace] = BM25Okapi(corpus)
                self._last_update[namespace] = now

                logger.info(f"BM25索引构建完成: {namespace}, 文档数: {len(chunk_ids)}")

            except ImportError:
                logger.error("rank_bm25 未安装,无法使用BM25检索")
                logger.info("请运行: pip install rank-bm25")
                self._bm25[namespace] = None

        except Exception as e:
            logger.error(f"初始化BM25索引失败: {e}")
            self._bm25[namespace] = None

    async def search_by_namespace(
        self,
        query: str,
        namespace: str,
        top_k: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        在指定领域内进行BM25检索

        Args:
            query: 查询文本
            namespace: 领域命名空间
            top_k: 返回结果数量

        Returns:
            List[Tuple[chunk_dict, score]]: 文档块和分数的元组列表
        """
        try:
            # 1. 确保索引已初始化
            if namespace not in self._bm25:
                await self.initialize_for_namespace(namespace)

            if namespace not in self._bm25 or self._bm25[namespace] is None:
                logger.warning(f"BM25索引不可用: {namespace}")
                return []

            if len(self._corpus[namespace]) == 0:
                return []

            # 2. 分词查询
            query_tokens = self._tokenize(query)
            logger.info(f"查询分词: {query_tokens}")

            # 3. BM25 评分
            scores = self._bm25[namespace].get_scores(query_tokens)

            # 4. 排序并获取 Top-K
            chunk_ids = self._corpus[namespace]
            scored_chunks = list(zip(chunk_ids, scores))
            scored_chunks.sort(key=lambda x: x[1], reverse=True)

            top_chunk_ids = [chunk_id for chunk_id, score in scored_chunks[:top_k]]

            if not top_chunk_ids:
                return []

            # 5. 查询数据库获取完整信息
            query_sql = """
                SELECT id, document_id, chunk_index, content, filename,
                       chunk_metadata, created_at, namespace
                FROM document_chunks
                WHERE id = ANY(:chunk_ids)
            """

            result = self.db.execute(
                text(query_sql),
                {"chunk_ids": top_chunk_ids}
            )

            chunks = {}
            for row in result:
                chunks[row.id] = {
                    "id": row.id,
                    "document_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "filename": row.filename,
                    "metadata": row.chunk_metadata,
                    "created_at": row.created_at,
                    "namespace": row.namespace
                }

            # 6. 恢复排序并关联分数
            result_list = []
            for chunk_id, score in scored_chunks[:top_k]:
                if chunk_id in chunks:
                    result_list.append((chunks[chunk_id], float(score)))

            logger.info(f"BM25检索完成: {namespace}, 返回 {len(result_list)} 个结果")
            return result_list

        except Exception as e:
            logger.error(f"BM25检索失败: {e}")
            return []

    async def clear_cache(self, namespace: Optional[str] = None):
        """
        清除BM25索引缓存

        Args:
            namespace: 指定领域(None=清除所有)
        """
        if namespace:
            self._corpus.pop(namespace, None)
            self._bm25.pop(namespace, None)
            self._last_update.pop(namespace, None)
            logger.info(f"已清除领域 '{namespace}' 的BM25缓存")
        else:
            self._corpus.clear()
            self._bm25.clear()
            self._last_update.clear()
            logger.info("已清除所有BM25缓存")


# 全局实例
bm25_retrieval_service = None


def get_bm25_service(db: Session) -> BM25Retrieval:
    """获取BM25检索服务实例"""
    return BM25Retrieval(db)
