"""
通用向量检索服务
提供统一的向量相似度检索接口，供其他服务使用
避免代码重复，确保性能优化的一致性
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding import embedding_service
from app.config.logging_config import get_app_logger

logger = get_app_logger()

class VectorRetrievalService:
    """
    通用向量检索服务
    提供高性能的向量相似度检索功能
    """

    def __init__(self):
        """初始化向量检索服务"""
        self.batch_size = 1000  # 批量处理大小，避免内存问题

    async def search_chunks(
        self,
        db: Session,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        document_ids: Optional[List[int]] = None,
        filename_filter: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        通用的文档块检索方法

        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的最大结果数
            similarity_threshold: 相似度阈值
            document_ids: 可选的文档ID过滤
            filename_filter: 可选的文件名过滤
            namespace: 可选的知识领域过滤

        Returns:
            List[Dict]: 相关文档块列表，包含相似度分数
        """
        try:
            # 1. 生成查询向量
            query_embedding = await embedding_service.create_embedding(query_text)
            logger.info(f"生成查询向量完成，维度: {len(query_embedding)}")

            # 2. 构建SQL查询条件
            conditions = ["embedding IS NOT NULL"]
            params = {}

            if document_ids:
                conditions.append("document_id = ANY(:document_ids)")
                params["document_ids"] = document_ids

            if filename_filter:
                conditions.append("filename ILIKE :filename_filter")
                params["filename_filter"] = f"%{filename_filter}%"

            if namespace:
                conditions.append("namespace = :namespace")
                params["namespace"] = namespace

            where_clause = " AND ".join(conditions)

            # 3. 从数据库获取文档块
            query_sql = f"""
                SELECT id, document_id, chunk_index, content, filename,
                       chunk_metadata, created_at, embedding, namespace
                FROM document_chunks
                WHERE {where_clause}
                ORDER BY document_id, chunk_index
            """

            result = db.execute(text(query_sql), params)
            chunks_with_embeddings = []

            for row in result:
                # 处理 embedding 字段 - 可能是字符串格式
                embedding = row.embedding
                if isinstance(embedding, str):
                    try:
                        import json
                        embedding = json.loads(embedding)
                    except:
                        try:
                            embedding = eval(embedding)
                        except:
                            logger.warning(f"无法解析文档块 {row.id} 的 embedding")
                            embedding = None

                chunks_with_embeddings.append({
                    "id": row.id,
                    "document_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "filename": row.filename,
                    "metadata": row.chunk_metadata,
                    "created_at": row.created_at,
                    "embedding": embedding,
                    "namespace": row.namespace if hasattr(row, 'namespace') else 'default'
                })

            if not chunks_with_embeddings:
                logger.info("没有找到任何文档块")
                return []

            logger.info(f"从数据库加载了 {len(chunks_with_embeddings)} 个文档块")

            # 4. 准备有效的向量数据（与 advanced_retrieval.py 逻辑一致）
            logger.info("开始批量计算相似度...")

            # 准备向量数据
            valid_chunks = []
            valid_embeddings = []

            for i, chunk_data in enumerate(chunks_with_embeddings):
                if chunk_data["embedding"] is not None:
                    valid_chunks.append((i, chunk_data))
                    valid_embeddings.append(chunk_data["embedding"])

            if not valid_chunks:
                logger.warning("没有有效的向量数据")
                return []

            # 批量计算所有相似度
            similarities = embedding_service.batch_cosine_similarity(query_embedding, valid_embeddings)

            # 创建(索引, 相似度)元组列表
            similarity_pairs = []
            for i, (chunk_idx, chunk_data) in enumerate(valid_chunks):
                similarity_pairs.append((chunk_idx, similarities[i]))

            if not similarity_pairs:
                logger.warning("没有有效的相似度计算结果")
                return []

            # 按相似度降序排序
            similarity_pairs.sort(key=lambda x: x[1], reverse=True)

            # 5. 应用相似度阈值并返回前top_k个最相似的文档块
            result_chunks = []
            for i, (chunk_idx, similarity) in enumerate(similarity_pairs[:top_k * 2]):  # 获取更多用于阈值过滤
                logger.info(f"文档块 {chunk_idx} 的相似度: {similarity}")
                if similarity >= similarity_threshold:
                    chunk = chunks_with_embeddings[chunk_idx].copy()
                    chunk['similarity'] = similarity
                    result_chunks.append(chunk)

            # 最终结果限制在top_k内
            final_results = result_chunks[:top_k]

            logger.info(f"检索完成，返回 {len(final_results)} 个最相关的文档块")
            return final_results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    
    async def search_documents(
        self,
        db: Session,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        检索整个文档（基于chunks，但按文档分组）

        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的最大文档数
            similarity_threshold: 相似度阈值

        Returns:
            List[Dict]: 相关文档列表
        """
        try:
            # 搜索相关chunks
            chunks = await self.search_chunks(
                db=db,
                query_text=query_text,
                top_k=top_k * 3,  # 获取更多chunks以便筛选
                similarity_threshold=similarity_threshold
            )

            if not chunks:
                return []

            # 按文档分组并取最高相似度
            document_scores = {}
            document_chunks = {}

            for chunk in chunks:
                doc_id = chunk['document_id']
                similarity = chunk['similarity']

                if doc_id not in document_scores or similarity > document_scores[doc_id]:
                    document_scores[doc_id] = similarity
                    document_chunks[doc_id] = chunk

            # 按相似度排序并返回前top_k个文档
            sorted_docs = sorted(
                document_chunks.items(),
                key=lambda x: x[1]['similarity'],
                reverse=True
            )

            result = []
            for doc_id, best_chunk in sorted_docs[:top_k]:
                # 获取文档的完整信息（这里可以根据需要扩展）
                document_query = text("""
                    SELECT id, filename, content, doc_metadata, created_at
                    FROM documents
                    WHERE id = :doc_id
                """)

                doc_result = db.execute(document_query, {"doc_id": doc_id}).first()

                if doc_result:
                    result.append({
                        "id": doc_result.id,
                        "filename": doc_result.filename,
                        "content": doc_result.content,
                        "metadata": doc_result.doc_metadata,
                        "created_at": doc_result.created_at,
                        "similarity": best_chunk['similarity'],
                        "best_chunk_id": best_chunk['id']
                    })

            return result

        except Exception as e:
            logger.error(f"文档检索失败: {e}")
            return []

    async def search_by_namespace(
        self,
        db: Session,
        query_text: str,
        namespace: str,
        top_k: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        在指定领域内进行向量检索

        Args:
            db: 数据库会话
            query_text: 查询文本
            namespace: 领域命名空间
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值

        Returns:
            List[Dict]: 排序后的文档块
        """
        logger.info(f"在领域 '{namespace}' 内检索: {query_text}")

        results = await self.search_chunks(
            db=db,
            query_text=query_text,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            namespace=namespace
        )

        logger.info(f"领域 '{namespace}' 检索完成,返回 {len(results)} 个结果")
        return results

    async def hybrid_search(
        self,
        db: Session,
        query_text: str,
        top_k: int = 5,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        混合检索：结合向量相似度和关键词匹配

        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的最大结果数
            keyword_weight: 关键词匹配权重
            vector_weight: 向量相似度权重

        Returns:
            List[Dict]: 混合检索结果
        """
        try:
            # 向量检索
            vector_results = await self.search_chunks(db, query_text, top_k * 2)

            # 简单的关键词匹配（可以进一步优化）
            keywords = query_text.lower().split()
            keyword_results = []

            for result in vector_results:
                content_lower = result['content'].lower()
                keyword_score = sum(1 for keyword in keywords if keyword in content_lower)
                keyword_score = keyword_score / len(keywords) if keywords else 0

                # 混合评分
                hybrid_score = (vector_weight * result['similarity'] +
                               keyword_weight * keyword_score)

                result['keyword_score'] = keyword_score
                result['hybrid_score'] = hybrid_score
                keyword_results.append(result)

            # 按混合评分排序
            keyword_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

            return keyword_results[:top_k]

        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []

# 创建全局实例
vector_retrieval_service = VectorRetrievalService()