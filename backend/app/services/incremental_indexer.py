"""
增量索引服务
负责文档的增量更新、删除和重建
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import Document
from app.models.document import DocumentChunk
from app.models.index_record import DocumentIndexRecord, IndexChangeHistory
from app.services.change_detector import ChangeDetector
from app.services.embedding import embedding_service

logger = logging.getLogger(__name__)


class IncrementalIndexer:
    """增量索引器"""

    def __init__(self, db: Session):
        self.db = db
        self.change_detector = ChangeDetector(db)
        self.embedding_service = embedding_service

    async def index_document(
        self,
        doc: Document,
        user_id: Optional[int] = None,
        force: bool = False
    ) -> Dict:
        """
        索引单个文档（增量模式）

        Args:
            doc: 文档对象
            user_id: 操作用户ID
            force: 是否强制重新索引

        Returns:
            索引结果字典
        """
        start_time = datetime.now()
        result = {
            'doc_id': doc.id,
            'filename': doc.filename,
            'status': 'success',
            'action': None,  # 'created', 'updated', 'skipped'
            'chunks_added': 0,
            'chunks_removed': 0,
            'error': None
        }

        try:
            # 检查是否可以跳过
            if not force and self.change_detector.should_skip_document(doc):
                result['action'] = 'skipped'
                result['message'] = '内容未变更，跳过索引'
                logger.info(f"跳过文档 {doc.id}: {doc.filename}")
                return result

            # 计算内容哈希
            content_hash = self.change_detector.compute_content_hash(doc.content or "")

            # 查找现有索引记录
            index_record = self.db.query(DocumentIndexRecord).filter(
                DocumentIndexRecord.doc_id == doc.id
            ).first()

            old_hash = index_record.content_hash if index_record else None
            old_chunk_count = index_record.chunk_count if index_record else 0

            # 删除旧的文档块
            if index_record:
                deleted_count = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).delete()
                result['chunks_removed'] = deleted_count
                logger.debug(f"删除文档 {doc.id} 的 {deleted_count} 个旧块")

            # 重新分块和嵌入
            # 注意：这里复用现有的分块逻辑，需要从documents router中提取
            chunks = self._chunk_document(doc)
            result['chunks_added'] = len(chunks)

            # 批量生成嵌入向量 - 使用 await
            embeddings = await self._generate_embeddings_batch([chunk['content'] for chunk in chunks])

            # 保存文档块
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    content=chunk['content'],
                    chunk_index=i,
                    embedding=embedding,
                    chunk_metadata=chunk.get('metadata', ''),
                    filename=doc.filename,
                    namespace=doc.namespace,
                    domain_tags=doc.domain_tags
                )
                self.db.add(doc_chunk)

            # 更新或创建索引记录
            if index_record:
                # 更新现有记录
                index_record.content_hash = content_hash
                index_record.chunk_count = len(chunks)
                index_record.vector_count = len(embeddings)
                index_record.indexed_at = datetime.now()
                index_record.index_version += 1
                result['action'] = 'updated'
            else:
                # 创建新记录
                # 尝试获取文件修改时间，如果Document模型没有该字段则使用None
                file_modified_at = getattr(doc, 'file_modified_at', None)

                index_record = DocumentIndexRecord(
                    doc_id=doc.id,
                    content_hash=content_hash,
                    chunk_count=len(chunks),
                    vector_count=len(embeddings),
                    indexed_at=datetime.now(),
                    file_size=len(doc.content or ""),
                    file_modified_at=file_modified_at,
                    namespace=doc.namespace
                )
                self.db.add(index_record)
                result['action'] = 'created'

            # 记录变更历史
            self._record_change_history(
                doc_id=doc.id,
                change_type=result['action'],
                old_hash=old_hash,
                new_hash=content_hash,
                old_chunk_count=old_chunk_count,
                new_chunk_count=len(chunks),
                user_id=user_id
            )

            # 提交事务
            self.db.commit()

            duration = (datetime.now() - start_time).total_seconds()
            result['duration_seconds'] = duration

            logger.info(f"文档 {doc.id} 索引完成: {result['action']}, "
                       f"块数={len(chunks)}, 耗时={duration:.2f}s")

        except Exception as e:
            self.db.rollback()
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"文档 {doc.id} 索引失败: {e}", exc_info=True)

        return result

    def delete_document_index(self, doc_id: int, user_id: Optional[int] = None) -> Dict:
        """
        删除文档的索引数据

        Args:
            doc_id: 文档ID
            user_id: 操作用户ID

        Returns:
            删除结果字典
        """
        result = {
            'doc_id': doc_id,
            'status': 'success',
            'chunks_deleted': 0,
            'error': None
        }

        try:
            # 获取索引记录
            index_record = self.db.query(DocumentIndexRecord).filter(
                DocumentIndexRecord.doc_id == doc_id
            ).first()

            if not index_record:
                result['status'] = 'not_found'
                result['message'] = '未找到索引记录'
                return result

            old_hash = index_record.content_hash
            old_chunk_count = index_record.chunk_count

            # 删除文档块
            deleted_count = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc_id
            ).delete()
            result['chunks_deleted'] = deleted_count

            # 删除索引记录
            self.db.delete(index_record)

            # 记录变更历史
            self._record_change_history(
                doc_id=doc_id,
                change_type='deleted',
                old_hash=old_hash,
                new_hash=None,
                old_chunk_count=old_chunk_count,
                new_chunk_count=0,
                user_id=user_id
            )

            self.db.commit()
            logger.info(f"文档 {doc_id} 索引已删除，删除 {deleted_count} 个块")

        except Exception as e:
            self.db.rollback()
            result['status'] = 'failed'
            result['error'] = str(e)
            logger.error(f"删除文档 {doc_id} 索引失败: {e}", exc_info=True)

        return result

    async def batch_index_documents(
        self,
        doc_ids: List[int],
        user_id: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        批量索引文档

        Args:
            doc_ids: 文档ID列表
            user_id: 操作用户ID
            progress_callback: 进度回调函数 callback(current, total, doc_id, result)

        Returns:
            批量处理结果统计
        """
        total = len(doc_ids)
        results = {
            'total': total,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        for i, doc_id in enumerate(doc_ids, 1):
            # 获取文档
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                results['failed'] += 1
                results['details'].append({
                    'doc_id': doc_id,
                    'status': 'not_found',
                    'error': '文档不存在'
                })
                continue

            # 索引文档 - 使用 await
            result = await self.index_document(doc, user_id=user_id)
            results['details'].append(result)

            # 统计
            if result['status'] == 'success':
                if result['action'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['success'] += 1
            else:
                results['failed'] += 1

            # 进度回调
            if progress_callback:
                progress_callback(i, total, doc_id, result)

            # 定期提交（每10个文档）
            if i % 10 == 0:
                self.db.commit()
                logger.debug(f"批量索引进度: {i}/{total}")

        # 最终提交
        self.db.commit()

        logger.info(f"批量索引完成: 总数={total}, 成功={results['success']}, "
                   f"跳过={results['skipped']}, 失败={results['failed']}")

        return results

    def _chunk_document(self, doc: Document) -> List[Dict]:
        """
        分块文档内容

        Args:
            doc: 文档对象

        Returns:
            块列表，每个块为字典 {'content': str, 'metadata': str}
        """
        # TODO: 从现有的分块逻辑中提取
        # 这里简化实现，实际应复用documents router中的逻辑
        content = doc.content or ""
        max_chunk_size = 1500
        overlap = 300

        chunks = []
        start = 0
        while start < len(content):
            end = min(start + max_chunk_size, len(content))
            chunk_content = content[start:end]

            chunks.append({
                'content': chunk_content,
                'metadata': f'{{"start": {start}, "end": {end}}}'
            })

            start = end - overlap if end < len(content) else end

        return chunks

    async def _generate_embeddings_batch(self, texts: List[str]) -> List:
        """
        批量生成嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        try:
            # 使用embedding service的批量方法
            embeddings = await self.embedding_service.create_batch_embeddings(texts)
            return embeddings
        except Exception as e:
            logger.error(f"批量生成嵌入失败: {e}")
            raise

    def _record_change_history(
        self,
        doc_id: int,
        change_type: str,
        old_hash: Optional[str],
        new_hash: Optional[str],
        old_chunk_count: int,
        new_chunk_count: int,
        user_id: Optional[int] = None
    ):
        """记录变更历史"""
        history = IndexChangeHistory(
            doc_id=doc_id,
            change_type=change_type,
            old_content_hash=old_hash,
            new_content_hash=new_hash,
            old_chunk_count=old_chunk_count,
            new_chunk_count=new_chunk_count,
            user_id=user_id,
            changed_at=datetime.now(),
            change_details={
                'hash_changed': old_hash != new_hash if old_hash and new_hash else True,
                'chunk_count_delta': new_chunk_count - old_chunk_count
            }
        )
        self.db.add(history)


def create_incremental_indexer(db: Session) -> IncrementalIndexer:
    """工厂函数：创建增量索引器实例"""
    return IncrementalIndexer(db)
