from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.embedding import embedding_service
from app.models.database import Document
from app.config.logging_config import get_app_logger
import numpy as np
import re

logger = get_app_logger()

class RetrievalService:
    def __init__(self):
        self.top_k = 10
    
    async def retrieve_documents(self, db: Session, query_text: str, top_k: int = None) -> list:
        """
        使用向量相似度检索相关文档
        
        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回的文档数量
            
        Returns:
            list: 相关文档列表，按相似度排序
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
                # 解析JSON格式的embedding
                embedding = None
                if row.embedding:
                    try:
                        import json
                        embedding = json.loads(row.embedding)
                    except (json.JSONDecodeError, TypeError):
                        logger.error(f"Failed to parse embedding for document {row.id}")
                        continue

                documents.append({
                    "id": row.id,
                    "content": row.content,
                    "filename": row.filename,
                    "metadata": row.doc_metadata,
                    "created_at": row.created_at,
                    "embedding": embedding
                })
                if embedding:
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
    
    def format_context(self, documents: list, query_text: str = "") -> str:
        """
        智能格式化上下文，避免截断重要信息
        
        Args:
            documents: 文档列表
            query_text: 查询文本，用于智能提取相关内容
            
        Returns:
            str: 格式化的上下文
        """
        context_parts = []
        max_context_length = 4000  # 最大上下文长度
        current_length = 0
        
        for doc in documents:
            # 计算当前文档需要的长度
            doc_header = f"文档: {doc['filename']}\n"
            doc_footer = "\n\n"
            
            # 获取文档内容
            content = doc['content']
            
            # 如果内容太长，尝试智能截取
            if len(content) > 1000:
                # 寻找包含查询关键词的部分
                relevant_content = self._extract_relevant_content(content, query_text)
                if relevant_content:
                    content = relevant_content
                else:
                    # 如果没有找到相关部分，取前部分
                    content = content[:1000] + "..."
            
            # 检查是否会超出长度限制
            doc_content = doc_header + content + doc_footer
            if current_length + len(doc_content) > max_context_length:
                # 如果超出限制，截断内容
                remaining_length = max_context_length - current_length - len(doc_header) - len(doc_footer)
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
            if not query_text.strip():
                return ""
            
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
            max_length = 1000
            
            for sentence, score in sentence_scores:
                if current_length + len(sentence) > max_length:
                    break
                relevant_sentences.append(sentence)
                current_length += len(sentence)
            
            if relevant_sentences:
                return "。".join(relevant_sentences) + "。"
            
            return ""
            
        except Exception as e:
            logger.error(f"提取相关内容失败: {e}")
            return ""

retrieval_service = RetrievalService()