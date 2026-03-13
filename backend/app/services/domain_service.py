"""
知识领域服务 (Knowledge Domain Service)

提供知识领域的 CRUD 操作和统计功能
用于支持多领域知识库管理
"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.knowledge_domain import KnowledgeDomain
from app.models.document import Document, DocumentChunk
from app.schemas.knowledge_domain import (
    KnowledgeDomainCreate,
    KnowledgeDomainUpdate,
    KnowledgeDomainResponse,
    KnowledgeDomainStatsResponse
)


class DomainServiceError(Exception):
    """领域服务异常基类"""
    pass


class DomainNotFoundError(DomainServiceError):
    """领域不存在异常"""
    pass


class DomainAlreadyExistsError(DomainServiceError):
    """领域已存在异常"""
    pass


class DomainService:
    """知识领域服务类"""

    def get_all_domains(
        self,
        db: Session,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[KnowledgeDomain]:
        """
        获取所有知识领域

        Args:
            db: 数据库会话
            include_inactive: 是否包含未启用的领域
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            List[KnowledgeDomain]: 领域列表
        """
        query = db.query(KnowledgeDomain)

        if not include_inactive:
            query = query.filter(KnowledgeDomain.is_active == True)

        # 按优先级降序,创建时间升序排列
        query = query.order_by(
            KnowledgeDomain.priority.desc(),
            KnowledgeDomain.created_at.asc()
        )

        return query.offset(skip).limit(limit).all()

    def get_domain_by_namespace(
        self,
        db: Session,
        namespace: str
    ) -> Optional[KnowledgeDomain]:
        """
        根据命名空间获取领域

        Args:
            db: 数据库会话
            namespace: 领域命名空间

        Returns:
            KnowledgeDomain: 领域对象,如果不存在则返回None
        """
        return db.query(KnowledgeDomain).filter(
            KnowledgeDomain.namespace == namespace
        ).first()

    def get_domain_by_id(
        self,
        db: Session,
        domain_id: int
    ) -> Optional[KnowledgeDomain]:
        """
        根据ID获取领域

        Args:
            db: 数据库会话
            domain_id: 领域ID

        Returns:
            KnowledgeDomain: 领域对象,如果不存在则返回None
        """
        return db.query(KnowledgeDomain).filter(
            KnowledgeDomain.id == domain_id
        ).first()

    def create_domain(
        self,
        db: Session,
        domain_data: KnowledgeDomainCreate
    ) -> KnowledgeDomain:
        """
        创建新的知识领域

        Args:
            db: 数据库会话
            domain_data: 领域创建数据

        Returns:
            KnowledgeDomain: 创建的领域对象

        Raises:
            DomainAlreadyExistsError: 如果命名空间已存在
        """
        # 检查命名空间是否已存在
        existing_domain = self.get_domain_by_namespace(db, domain_data.namespace)
        if existing_domain:
            raise DomainAlreadyExistsError(
                f"领域命名空间 '{domain_data.namespace}' 已存在"
            )

        # 创建新领域
        db_domain = KnowledgeDomain(
            namespace=domain_data.namespace,
            display_name=domain_data.display_name,
            description=domain_data.description,
            keywords=domain_data.keywords,
            icon=domain_data.icon,
            color=domain_data.color,
            is_active=domain_data.is_active,
            priority=domain_data.priority,
            parent_namespace=domain_data.parent_namespace,
            permissions=domain_data.permissions,
            metadata_=domain_data.metadata
        )

        db.add(db_domain)
        db.commit()
        db.refresh(db_domain)

        return db_domain

    def update_domain(
        self,
        db: Session,
        namespace: str,
        domain_data: KnowledgeDomainUpdate
    ) -> KnowledgeDomain:
        """
        更新知识领域

        Args:
            db: 数据库会话
            namespace: 领域命名空间
            domain_data: 更新数据

        Returns:
            KnowledgeDomain: 更新后的领域对象

        Raises:
            DomainNotFoundError: 如果领域不存在
        """
        db_domain = self.get_domain_by_namespace(db, namespace)
        if not db_domain:
            raise DomainNotFoundError(f"领域 '{namespace}' 不存在")

        # 更新字段(只更新提供的非None字段)
        update_data = domain_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # 处理metadata字段的特殊映射
            if field == 'metadata':
                setattr(db_domain, 'metadata_', value)
            else:
                setattr(db_domain, field, value)

        # 更新时间戳
        db_domain.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(db_domain)

        return db_domain

    def delete_domain(
        self,
        db: Session,
        namespace: str,
        force: bool = False
    ) -> bool:
        """
        删除知识领域

        Args:
            db: 数据库会话
            namespace: 领域命名空间
            force: 是否强制删除(即使有关联文档)

        Returns:
            bool: 是否成功删除

        Raises:
            DomainNotFoundError: 如果领域不存在
            DomainServiceError: 如果领域有关联文档且未设置force=True
        """
        db_domain = self.get_domain_by_namespace(db, namespace)
        if not db_domain:
            raise DomainNotFoundError(f"领域 '{namespace}' 不存在")

        # 检查是否有关联文档
        if not force:
            doc_count = db.query(Document).filter(
                Document.namespace == namespace
            ).count()

            if doc_count > 0:
                raise DomainServiceError(
                    f"领域 '{namespace}' 有 {doc_count} 个关联文档,无法删除。"
                    "请使用 force=True 强制删除,或先删除关联文档。"
                )

        # 执行删除
        db.delete(db_domain)
        db.commit()

        return True

    def get_domain_stats(
        self,
        db: Session,
        namespace: str
    ) -> KnowledgeDomainStatsResponse:
        """
        获取领域统计信息

        Args:
            db: 数据库会话
            namespace: 领域命名空间

        Returns:
            KnowledgeDomainStatsResponse: 统计信息

        Raises:
            DomainNotFoundError: 如果领域不存在
        """
        # 验证领域存在
        domain = self.get_domain_by_namespace(db, namespace)
        if not domain:
            raise DomainNotFoundError(f"领域 '{namespace}' 不存在")

        # 文档数量
        document_count = db.query(Document).filter(
            Document.namespace == namespace
        ).count()

        # 分块数量
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.namespace == namespace
        ).count()

        # 平均置信度
        avg_confidence_result = db.query(
            func.avg(Document.domain_confidence)
        ).filter(
            Document.namespace == namespace,
            Document.domain_confidence > 0  # 只统计有置信度的文档
        ).scalar()

        avg_confidence = float(avg_confidence_result) if avg_confidence_result else 0.0

        # 最近7天上传数
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        # 注意: Document.created_at 是字符串类型,需要转换为字符串进行比较
        seven_days_ago_str = seven_days_ago.isoformat()
        recent_uploads = db.query(Document).filter(
            and_(
                Document.namespace == namespace,
                Document.created_at >= seven_days_ago_str
            )
        ).count()

        return KnowledgeDomainStatsResponse(
            namespace=namespace,
            document_count=document_count,
            chunk_count=chunk_count,
            avg_confidence=round(avg_confidence, 3),
            recent_uploads=recent_uploads
        )

    def get_all_domains_with_stats(
        self,
        db: Session,
        include_inactive: bool = False
    ) -> List[KnowledgeDomainResponse]:
        """
        获取所有领域及其统计信息

        Args:
            db: 数据库会话
            include_inactive: 是否包含未启用的领域

        Returns:
            List[KnowledgeDomainResponse]: 包含统计信息的领域列表
        """
        domains = self.get_all_domains(db, include_inactive=include_inactive)

        results = []
        for domain in domains:
            # 获取文档和分块数量
            document_count = db.query(Document).filter(
                Document.namespace == domain.namespace
            ).count()

            chunk_count = db.query(DocumentChunk).filter(
                DocumentChunk.namespace == domain.namespace
            ).count()

            # 转换为响应模型
            domain_dict = {
                "id": domain.id,
                "namespace": domain.namespace,
                "display_name": domain.display_name,
                "description": domain.description,
                "keywords": domain.keywords,
                "icon": domain.icon,
                "color": domain.color,
                "is_active": domain.is_active,
                "priority": domain.priority,
                "parent_namespace": domain.parent_namespace,
                "permissions": domain.permissions,
                "metadata": domain.metadata_,
                "created_at": domain.created_at,
                "updated_at": domain.updated_at,
                "document_count": document_count,
                "chunk_count": chunk_count
            }

            results.append(KnowledgeDomainResponse(**domain_dict))

        return results

    def search_domains_by_keyword(
        self,
        db: Session,
        keyword: str,
        include_inactive: bool = False
    ) -> List[KnowledgeDomain]:
        """
        根据关键词搜索领域

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            include_inactive: 是否包含未启用的领域

        Returns:
            List[KnowledgeDomain]: 匹配的领域列表
        """
        query = db.query(KnowledgeDomain)

        if not include_inactive:
            query = query.filter(KnowledgeDomain.is_active == True)

        # 搜索条件: 命名空间、显示名称、描述或关键词
        search_filter = or_(
            KnowledgeDomain.namespace.ilike(f"%{keyword}%"),
            KnowledgeDomain.display_name.ilike(f"%{keyword}%"),
            KnowledgeDomain.description.ilike(f"%{keyword}%"),
            # JSONB数组关键词搜索 (PostgreSQL特定)
            func.jsonb_array_length(KnowledgeDomain.keywords) > 0
        )

        query = query.filter(search_filter)
        query = query.order_by(KnowledgeDomain.priority.desc())

        return query.all()


# 创建全局服务实例
domain_service = DomainService()
