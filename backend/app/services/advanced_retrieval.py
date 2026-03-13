"""
高级检索服务
解决当前检索系统的性能和上下文截断问题
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.embedding import embedding_service
from app.models.database import Document
from app.config.logging_config import get_app_logger
import numpy as np
import re
from typing import List, Dict, Tuple
import asyncio

logger = get_app_logger()

class AdvancedRetrievalService:
    """高级检索服务类"""
    
    def __init__(self):
        self.top_k = 10
        self.max_context_length = 4000  # 最大上下文长度
        self.chunk_size = 1000  # 文档分块大小
        self.overlap_size = 200  # 分块重叠大小
    
    async def retrieve_documents(self, db: Session, query_text: str, top_k: int = None) -> List[Dict]:
        """
        使用向量相似度检索相关文档
        
        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的文档数量
            
        Returns:
            List[Dict]: 相关文档列表，按相似度排序
        """
        try:
            top_k = top_k or self.top_k
            
            # 1. 为查询文本生成嵌入向量
            query_embedding = await embedding_service.create_embedding(query_text)
            
            # 2. 获取所有文档的嵌入向量
            query = text("""
                SELECT id, content, filename, doc_metadata, created_at, embedding
                FROM documents
                WHERE embedding IS NOT NULL
            """)
            
            result = db.execute(query)
            documents = []
            document_embeddings = []
            
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
                            logger.warning(f"无法解析文档 {row.id} 的 embedding")
                            embedding = None

                documents.append({
                    "id": row.id,
                    "content": row.content,
                    "filename": row.filename,
                    "metadata": row.doc_metadata,
                    "created_at": row.created_at,
                    "embedding": embedding
                })
                if embedding is not None:
                    document_embeddings.append(embedding)
            
            if not documents:
                logger.info("没有找到任何文档")
                return []
            
            # 3. 计算相似度并排序
            similarities = []
            for i, doc_embedding in enumerate(document_embeddings):
                if doc_embedding is not None:
                    similarity = embedding_service.cosine_similarity(query_embedding, doc_embedding)
                    similarities.append((i, similarity))
            
            # 按相似度降序排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 4. 返回前top_k个最相似的文档
            result_documents = []
            for i, (doc_idx, similarity) in enumerate(similarities[:top_k]):
                doc = documents[doc_idx].copy()
                doc['similarity'] = similarity
                result_documents.append(doc)
            
            logger.info(f"检索到 {len(result_documents)} 个相关文档")
            return result_documents
            
        except Exception as e:
            logger.error(f"检索文档失败: {e}")
            return []
    
    def chunk_document(self, content: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        将文档分块，避免截断重要信息
        
        Args:
            content: 文档内容
            chunk_size: 分块大小
            overlap: 重叠大小
            
        Returns:
            List[str]: 文档块列表
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap_size
        
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # 如果不是最后一块，尝试在句号或换行处分割
            if end < len(content):
                # 寻找最近的句号或换行
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if content[i] in ['。', '\n', '！', '？']:
                        end = i + 1
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 下一块的开始位置，考虑重叠
            start = max(start + 1, end - overlap)
        
        return chunks
    
    async def retrieve_relevant_chunks(self, db: Session, query_text: str, top_k: int = None) -> List[Dict]:
        """
        检索相关文档块，直接使用预计算好的向量数据

        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的文档块数量

        Returns:
            List[Dict]: 相关文档块列表
        """
        try:
            top_k = top_k or self.top_k * 2  # 获取更多块以提供更好的上下文

            # 1. 为查询文本生成嵌入向量
            query_embedding = await embedding_service.create_embedding(query_text)
            logger.info(f"生成查询向量完成，维度: {len(query_embedding)}")

            # 2. 直接从数据库获取所有已计算的文档块向量
            query = text("""
                SELECT id, document_id, chunk_index, content, filename, chunk_metadata, created_at, embedding
                FROM document_chunks
                WHERE embedding IS NOT NULL
                ORDER BY document_id, chunk_index
            """)

            result = db.execute(query)
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
                            continue  # 跳过无法解析的块

                chunks_with_embeddings.append({
                    "id": row.id,
                    "doc_id": row.document_id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "filename": row.filename,
                    "metadata": row.chunk_metadata,
                    "created_at": row.created_at,
                    "embedding": embedding  # 使用转换后的向量
                })

            if not chunks_with_embeddings:
                logger.info("没有找到任何已嵌入的文档块")
                return []

            logger.info(f"从数据库加载了 {len(chunks_with_embeddings)} 个文档块")

            # 3. 使用批量计算相似度（大幅提升性能）
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

            # 4. 返回前top_k个最相似的文档块
            result_chunks = []
            for i, (chunk_idx, similarity) in enumerate(similarity_pairs[:top_k]):
                chunk = chunks_with_embeddings[chunk_idx].copy()
                chunk['similarity'] = similarity
                result_chunks.append(chunk)

            logger.info(f"检索完成，返回 {len(result_chunks)} 个最相关的文档块")
            return result_chunks

        except Exception as e:
            logger.error(f"检索文档块失败: {e}")
            return []
    
    def smart_format_context(self, documents: List[Dict], query_text: str) -> str:
        """
        智能格式化上下文，避免截断重要信息
        
        Args:
            documents: 检索到的文档列表
            query_text: 查询文本
            
        Returns:
            str: 格式化的上下文
        """
        try:
            context_parts = []
            current_length = 0
            
            for doc in documents:
                # 计算当前文档需要的长度
                doc_header = f"文档: {doc['filename']}\n"
                doc_footer = "\n\n"
                
                # 获取文档内容
                content = doc['content']
                
                # 如果内容太长，尝试智能截取
                if len(content) > self.chunk_size:
                    # 寻找包含查询关键词的部分
                    relevant_content = self._extract_relevant_content(content, query_text)
                    if relevant_content:
                        content = relevant_content
                    else:
                        # 如果没有找到相关部分，取前部分
                        content = content[:self.chunk_size] + "..."
                
                # 检查是否会超出长度限制
                doc_content = doc_header + content + doc_footer
                if current_length + len(doc_content) > self.max_context_length:
                    # 如果超出限制，截断内容
                    remaining_length = self.max_context_length - current_length - len(doc_header) - len(doc_footer)
                    if remaining_length > 100:  # 至少保留100字符
                        content = content[:remaining_length] + "..."
                        doc_content = doc_header + content + doc_footer
                    else:
                        break  # 无法再添加更多内容
                
                context_parts.append(doc_content)
                current_length += len(doc_content)
            
            context = "".join(context_parts)
            logger.info(f"格式化上下文完成，长度: {len(context)} 字符")
            return context
            
        except Exception as e:
            logger.error(f"格式化上下文失败: {e}")
            return self._fallback_format_context(documents)
    
    def _extract_relevant_content(self, content: str, query_text: str) -> str:
        """
        从文档中提取与查询相关的内容
        
        Args:
            content: 文档内容
            query_text: 查询文本
            
        Returns:
            str: 相关内容
        """
        try:
            # 将查询文本分词
            query_words = re.findall(r'\w+', query_text.lower())
            
            # 将文档分句
            sentences = re.split(r'[。！？\n]', content)
            
            # 计算每个句子的相关性得分
            sentence_scores = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                
                sentence_lower = sentence.lower()
                score = 0
                
                # 计算关键词匹配得分
                for word in query_words:
                    if word in sentence_lower:
                        score += 1
                
                # 计算位置权重（前面的内容权重更高）
                position_weight = 1.0 - (len(sentence_scores) / len(sentences)) * 0.3
                score *= position_weight
                
                sentence_scores.append((sentence, score))
            
            # 按得分排序
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 选择得分最高的句子
            relevant_sentences = []
            current_length = 0
            
            for sentence, score in sentence_scores:
                if current_length + len(sentence) > self.chunk_size:
                    break
                relevant_sentences.append(sentence)
                current_length += len(sentence)
            
            if relevant_sentences:
                return "。".join(relevant_sentences) + "。"
            
            return ""
            
        except Exception as e:
            logger.error(f"提取相关内容失败: {e}")
            return ""
    
    def _fallback_format_context(self, documents: List[Dict]) -> str:
        """
        备用格式化方法
        
        Args:
            documents: 文档列表
            
        Returns:
            str: 格式化的上下文
        """
        context_parts = []
        for doc in documents:
            content = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
            context_parts.append(f"文档: {doc['filename']}\n内容: {content}")
        return "\n\n".join(context_parts)
    
    def format_context_with_chunks(self, chunks: List[Dict], query_text: str) -> str:
        """
        使用文档块格式化上下文
        
        Args:
            chunks: 文档块列表
            query_text: 查询文本
            
        Returns:
            str: 格式化的上下文
        """
        try:
            context_parts = []
            current_length = 0
            used_docs = set()  # 避免重复文档
            
            for chunk in chunks:
                doc_id = chunk['doc_id']
                filename = chunk['filename']
                
                # 检查是否已经使用了这个文档
                if doc_id in used_docs:
                    continue
                
                # 计算当前块需要的长度
                doc_header = f"文档: {filename}\n"
                doc_footer = "\n\n"
                
                content = chunk['content']
                
                # 检查是否会超出长度限制
                doc_content = doc_header + content + doc_footer
                if current_length + len(doc_content) > self.max_context_length:
                    remaining_length = self.max_context_length - current_length - len(doc_header) - len(doc_footer)
                    if remaining_length > 100:
                        content = content[:remaining_length] + "..."
                        doc_content = doc_header + content + doc_footer
                    else:
                        break
                
                context_parts.append(doc_content)
                current_length += len(doc_content)
                used_docs.add(doc_id)
            
            context = "".join(context_parts)
            logger.info(f"使用文档块格式化上下文完成，长度: {len(context)} 字符")
            return context
            
        except Exception as e:
            logger.error(f"使用文档块格式化上下文失败: {e}")
            return self._fallback_format_context(chunks)

# 创建高级检索服务的全局实例
advanced_retrieval_service = AdvancedRetrievalService()
