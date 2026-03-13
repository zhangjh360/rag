"""
文档变更检测服务
用于识别需要增量更新的文档
"""
import hashlib
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.models.database import Document
from app.models.index_record import DocumentIndexRecord

logger = logging.getLogger(__name__)


class ChangeDetector:
    """文档变更检测器"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        计算内容的MD5哈希值

        Args:
            content: 文档内容

        Returns:
            MD5哈希值（十六进制字符串）
        """
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        计算文件的MD5哈希值

        Args:
            file_path: 文件路径

        Returns:
            MD5哈希值（十六进制字符串）
        """
        if not os.path.exists(file_path):
            return ""

        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def detect_changes_by_timestamp(
        self,
        since: Optional[datetime] = None,
        namespace: Optional[str] = None
    ) -> List[Document]:
        """
        基于时间戳检测变更的文档（快速筛选）

        Args:
            since: 起始时间，默认为最后一次索引时间
            namespace: 领域命名空间筛选

        Returns:
            可能变更的文档列表
        """
        # 查询所有文档,并LEFT JOIN索引记录表
        from sqlalchemy.orm import aliased

        query = self.db.query(Document).outerjoin(
            DocumentIndexRecord,
            Document.id == DocumentIndexRecord.doc_id
        )

        # 领域筛选
        if namespace:
            query = query.filter(Document.namespace == namespace)

        # 时间筛选
        if since:
            # 查找以下文档:
            # 1. 文件修改时间在since之后的(使用DocumentIndexRecord.file_modified_at)
            # 2. 从未被索引的(DocumentIndexRecord为NULL)
            # 3. 索引时间早于since的
            query = query.filter(
                or_(
                    and_(
                        DocumentIndexRecord.file_modified_at.isnot(None),
                        DocumentIndexRecord.file_modified_at > since
                    ),
                    DocumentIndexRecord.indexed_at.is_(None),
                    and_(
                        DocumentIndexRecord.indexed_at.isnot(None),
                        DocumentIndexRecord.indexed_at < since
                    )
                )
            )
        else:
            # 默认查找未索引的文档(没有索引记录)
            query = query.filter(DocumentIndexRecord.doc_id.is_(None))

        documents = query.all()
        logger.info(f"基于时间戳检测到 {len(documents)} 个可能变更的文档")
        return documents

    def detect_changes_by_hash(
        self,
        documents: Optional[List[Document]] = None,
        namespace: Optional[str] = None
    ) -> Tuple[List[Document], List[Document], List[Document]]:
        """
        基于内容哈希精确检测变更（精确检测）

        Args:
            documents: 待检测的文档列表，如果为None则检测所有文档
            namespace: 领域命名空间筛选

        Returns:
            (新增文档列表, 修改文档列表, 未变更文档列表)
        """
        if documents is None:
            query = self.db.query(Document)
            if namespace:
                query = query.filter(Document.namespace == namespace)
            documents = query.all()

        new_docs = []
        modified_docs = []
        unchanged_docs = []

        for doc in documents:
            # 计算当前内容哈希
            current_hash = self.compute_content_hash(doc.content or "")

            # 查询索引记录
            index_record = self.db.query(DocumentIndexRecord).filter(
                DocumentIndexRecord.doc_id == doc.id
            ).first()

            if not index_record:
                # 没有索引记录，视为新文档
                new_docs.append(doc)
                logger.debug(f"新文档: {doc.filename} (ID:{doc.id})")
            elif index_record.content_hash != current_hash:
                # 哈希值不匹配，内容已变更
                modified_docs.append(doc)
                logger.debug(f"修改文档: {doc.filename} (ID:{doc.id}) "
                           f"旧哈希:{index_record.content_hash[:8]}... "
                           f"新哈希:{current_hash[:8]}...")
            else:
                # 哈希值匹配，内容未变更
                unchanged_docs.append(doc)

        logger.info(f"哈希检测结果: 新增={len(new_docs)}, "
                   f"修改={len(modified_docs)}, 未变更={len(unchanged_docs)}")

        return new_docs, modified_docs, unchanged_docs

    def detect_deleted_documents(self, namespace: Optional[str] = None) -> List[int]:
        """
        检测已删除的文档（有索引记录但文档不存在）

        Args:
            namespace: 领域命名空间筛选

        Returns:
            已删除文档的ID列表
        """
        # 查询所有索引记录
        query = self.db.query(DocumentIndexRecord.doc_id)
        if namespace:
            query = query.filter(DocumentIndexRecord.namespace == namespace)

        indexed_doc_ids = {record.doc_id for record in query.all()}

        # 查询实际存在的文档
        doc_query = self.db.query(Document.id)
        if namespace:
            doc_query = doc_query.filter(Document.namespace == namespace)

        existing_doc_ids = {doc.id for doc in doc_query.all()}

        # 找出差异
        deleted_doc_ids = list(indexed_doc_ids - existing_doc_ids)

        if deleted_doc_ids:
            logger.info(f"检测到 {len(deleted_doc_ids)} 个已删除的文档")

        return deleted_doc_ids

    def get_outdated_documents(
        self,
        max_age_hours: int = 24,
        namespace: Optional[str] = None
    ) -> List[Document]:
        """
        获取过时的文档（索引时间超过指定小时数）

        Args:
            max_age_hours: 最大索引年龄(小时)
            namespace: 领域命名空间筛选

        Returns:
            过时文档列表
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # 通过LEFT JOIN索引记录表来查询过时文档
        query = self.db.query(Document).outerjoin(
            DocumentIndexRecord,
            Document.id == DocumentIndexRecord.doc_id
        ).filter(
            or_(
                # 索引时间早于cutoff_time
                and_(
                    DocumentIndexRecord.indexed_at.isnot(None),
                    DocumentIndexRecord.indexed_at < cutoff_time
                ),
                # 或者从未被索引
                DocumentIndexRecord.indexed_at.is_(None)
            )
        )

        if namespace:
            query = query.filter(Document.namespace == namespace)

        outdated_docs = query.all()
        logger.info(f"发现 {len(outdated_docs)} 个超过 {max_age_hours} 小时未更新的文档")

        return outdated_docs

    def get_change_summary(self, namespace: Optional[str] = None) -> Dict:
        """
        获取变更摘要统计

        Args:
            namespace: 领域命名空间筛选

        Returns:
            变更摘要字典，包含完整的文档信息供前端使用
        """
        # 先基于时间戳快速筛选
        candidates = self.detect_changes_by_timestamp(namespace=namespace)

        # 再基于哈希精确检测
        new_docs, modified_docs, unchanged_docs = self.detect_changes_by_hash(
            documents=candidates,
            namespace=namespace
        )

        # 检测已删除的文档
        deleted_doc_ids = self.detect_deleted_documents(namespace=namespace)

        # 将文档对象转换为字典（包含前端需要的字段）
        def doc_to_dict(doc: Document) -> dict:
            return {
                'id': doc.id,
                'filename': doc.filename,
                'namespace': doc.namespace,
                'created_at': doc.created_at,
                'content_preview': doc.content[:100] if doc.content else ''
            }

        summary = {
            'total_candidates': len(candidates),
            'new_documents': [doc_to_dict(doc) for doc in new_docs],  # 完整文档对象
            'modified_documents': [doc_to_dict(doc) for doc in modified_docs],  # 完整文档对象
            'unchanged_count': len(unchanged_docs),  # 改为count后缀
            'deleted_documents': len(deleted_doc_ids),
            'needs_update': len(new_docs) + len(modified_docs),
            'needs_delete': len(deleted_doc_ids),
            'new_doc_ids': [doc.id for doc in new_docs],  # 保留ID列表供兼容
            'modified_doc_ids': [doc.id for doc in modified_docs],  # 保留ID列表供兼容
            'deleted_doc_ids': deleted_doc_ids,
            'namespace': namespace or 'all',
            'detected_at': datetime.now().isoformat()
        }

        logger.info(f"变更摘要: {summary['needs_update']} 个文档需要更新, "
                   f"{summary['needs_delete']} 个需要删除")

        return summary

    def should_skip_document(
        self,
        doc: Document,
        similarity_threshold: float = 0.95
    ) -> bool:
        """
        判断文档是否可以跳过索引（基于向量相似度）

        这是一个可选的优化，用于避免对内容微小变化的文档重新索引

        Args:
            doc: 文档对象
            similarity_threshold: 相似度阈值(0-1)

        Returns:
            True表示可以跳过
        """
        # 获取索引记录
        index_record = self.db.query(DocumentIndexRecord).filter(
            DocumentIndexRecord.doc_id == doc.id
        ).first()

        if not index_record:
            return False  # 新文档不能跳过

        # 计算当前哈希
        current_hash = self.compute_content_hash(doc.content or "")

        if index_record.content_hash == current_hash:
            # 内容完全相同，可以跳过
            logger.debug(f"文档 {doc.id} 内容未变更，跳过索引")
            return True

        # TODO: 这里可以添加更复杂的逻辑
        # 例如计算新旧版本embedding的余弦相似度
        # 如果相似度 > threshold，则跳过

        return False


def create_change_detector(db: Session) -> ChangeDetector:
    """工厂函数：创建变更检测器实例"""
    return ChangeDetector(db)
