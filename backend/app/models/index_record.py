"""
索引记录相关模型
用于增量更新和版本控制
"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, Float, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional
# 使用 document.py 中的 Base,确保模型在同一个元数据中
from app.models.document import Base


class DocumentIndexRecord(Base):
    """
    文档索引记录表
    追踪每个文档的索引状态和元信息
    """
    __tablename__ = 'document_index_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'),
                   unique=True, nullable=False, comment='文档ID')
    content_hash = Column(String(64), nullable=False, index=True, comment='文档内容MD5哈希值')
    chunk_count = Column(Integer, default=0, comment='文档分块数量')
    vector_count = Column(Integer, default=0, comment='向量数量')
    indexed_at = Column(DateTime, default=datetime.now, index=True, comment='索引时间')
    file_size = Column(BigInteger, default=0, comment='文件大小(字节)')
    file_modified_at = Column(DateTime, comment='文件修改时间')
    index_version = Column(Integer, default=1, comment='索引版本号')
    namespace = Column(String(100), default='default', index=True, comment='领域命名空间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'content_hash': self.content_hash,
            'chunk_count': self.chunk_count,
            'vector_count': self.vector_count,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None,
            'file_size': self.file_size,
            'file_modified_at': self.file_modified_at.isoformat() if self.file_modified_at else None,
            'index_version': self.index_version,
            'namespace': self.namespace
        }


class IndexTask(Base):
    """
    索引任务队列表
    管理异步索引任务
    """
    __tablename__ = 'index_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), unique=True, nullable=False, comment='Celery任务ID')
    doc_id = Column(Integer, ForeignKey('documents.id', ondelete='SET NULL'),
                   index=True, comment='文档ID')
    task_type = Column(String(20), nullable=False, index=True,
                      comment='任务类型: index, update, delete, rebuild, batch')
    status = Column(String(20), nullable=False, default='pending', index=True,
                   comment='状态: pending, processing, completed, failed, cancelled')
    priority = Column(Integer, default=5, comment='优先级(1-10, 10最高)')
    retry_count = Column(Integer, default=0, comment='重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    error_message = Column(Text, comment='错误信息')
    progress = Column(Integer, default=0, comment='进度(0-100)')
    task_metadata = Column('metadata', JSONB, default=dict, comment='任务元数据')
    created_at = Column(DateTime, default=datetime.now, index=True, comment='创建时间')
    started_at = Column(DateTime, comment='开始时间')
    completed_at = Column(DateTime, comment='完成时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'doc_id': self.doc_id,
            'task_type': self.task_type,
            'status': self.status,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'progress': self.progress,
            'metadata': self.task_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'duration_seconds': self._calculate_duration()
        }

    def _calculate_duration(self) -> Optional[float]:
        """计算任务耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None


class IndexChangeHistory(Base):
    """
    索引变更历史表
    记录所有索引变更用于审计和回滚
    """
    __tablename__ = 'index_change_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'),
                   nullable=False, index=True, comment='文档ID')
    change_type = Column(String(20), nullable=False, index=True,
                        comment='变更类型: created, updated, deleted, rollback')
    old_content_hash = Column(String(64), comment='旧内容哈希')
    new_content_hash = Column(String(64), comment='新内容哈希')
    old_chunk_count = Column(Integer, default=0, comment='旧分块数')
    new_chunk_count = Column(Integer, default=0, comment='新分块数')
    user_id = Column(Integer, comment='操作用户ID')
    changed_at = Column(DateTime, default=datetime.now, index=True, comment='变更时间')
    change_details = Column(JSONB, default=dict, comment='变更详情')
    snapshot_id = Column(String(100), index=True, comment='快照ID(用于回滚)')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'doc_id': self.doc_id,
            'change_type': self.change_type,
            'old_content_hash': self.old_content_hash,
            'new_content_hash': self.new_content_hash,
            'old_chunk_count': self.old_chunk_count,
            'new_chunk_count': self.new_chunk_count,
            'user_id': self.user_id,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'change_details': self.change_details,
            'snapshot_id': self.snapshot_id
        }


class IndexStatistics(Base):
    """
    索引统计表
    用于监控和性能分析
    """
    __tablename__ = 'index_statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, nullable=False, index=True, comment='统计日期')
    namespace = Column(String(100), default='default', index=True, comment='领域')
    total_documents = Column(Integer, default=0, comment='总文档数')
    indexed_documents = Column(Integer, default=0, comment='已索引文档数')
    pending_tasks = Column(Integer, default=0, comment='待处理任务数')
    failed_tasks = Column(Integer, default=0, comment='失败任务数')
    avg_index_time_seconds = Column(Float, default=0, comment='平均索引时间(秒)')
    total_vectors = Column(Integer, default=0, comment='总向量数')
    storage_size_mb = Column(Float, default=0, comment='存储大小(MB)')
    api_calls = Column(Integer, default=0, comment='API调用次数')
    api_cost_usd = Column(Float, default=0, comment='API成本(美元)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'namespace': self.namespace,
            'total_documents': self.total_documents,
            'indexed_documents': self.indexed_documents,
            'pending_tasks': self.pending_tasks,
            'failed_tasks': self.failed_tasks,
            'avg_index_time_seconds': self.avg_index_time_seconds,
            'total_vectors': self.total_vectors,
            'storage_size_mb': self.storage_size_mb,
            'api_calls': self.api_calls,
            'api_cost_usd': self.api_cost_usd,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'indexing_rate': self._calculate_indexing_rate()
        }

    def _calculate_indexing_rate(self) -> Optional[float]:
        """计算索引完成率"""
        if self.total_documents > 0:
            return (self.indexed_documents / self.total_documents) * 100
        return None
