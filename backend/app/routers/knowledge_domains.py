"""
知识领域管理 API 路由

提供知识领域的 CRUD 接口和统计功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.connection import get_db
from app.models.database import User
from app.middleware.auth import get_current_active_user, require_admin
from app.services.domain_service import (
    domain_service,
    DomainNotFoundError,
    DomainAlreadyExistsError,
    DomainServiceError
)
from app.schemas.knowledge_domain import (
    KnowledgeDomainCreate,
    KnowledgeDomainUpdate,
    KnowledgeDomainResponse,
    KnowledgeDomainListResponse,
    KnowledgeDomainStatsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/knowledge-domains", response_model=KnowledgeDomainListResponse)
async def get_all_domains(
    include_inactive: bool = QueryParam(False, description="是否包含未启用的领域"),
    skip: int = QueryParam(0, ge=0, description="跳过的记录数"),
    limit: int = QueryParam(100, ge=1, le=500, description="返回的最大记录数"),
    with_stats: bool = QueryParam(False, description="是否包含统计信息"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有知识领域列表

    Args:
        include_inactive: 是否包含未启用的领域
        skip: 分页跳过数
        limit: 分页限制数
        with_stats: 是否包含文档和分块统计信息

    Returns:
        KnowledgeDomainListResponse: 领域列表及总数
    """
    try:
        if with_stats:
            # 获取包含统计信息的领域列表
            domains = domain_service.get_all_domains_with_stats(
                db=db,
                include_inactive=include_inactive
            )
            # 手动分页
            total = len(domains)
            domains = domains[skip:skip + limit]
        else:
            # 获取简单的领域列表
            all_domains = domain_service.get_all_domains(
                db=db,
                include_inactive=include_inactive,
                skip=skip,
                limit=limit
            )

            # 计算总数
            total = domain_service.get_all_domains(
                db=db,
                include_inactive=include_inactive,
                skip=0,
                limit=999999
            )
            total = len(total)

            # 转换为响应模型
            domains = [
                KnowledgeDomainResponse(
                    id=d.id,
                    namespace=d.namespace,
                    display_name=d.display_name,
                    description=d.description,
                    keywords=d.keywords,
                    icon=d.icon,
                    color=d.color,
                    is_active=d.is_active,
                    priority=d.priority,
                    parent_namespace=d.parent_namespace,
                    permissions=d.permissions,
                    metadata=d.metadata_,
                    created_at=d.created_at,
                    updated_at=d.updated_at
                )
                for d in all_domains
            ]

        return KnowledgeDomainListResponse(
            domains=domains,
            total=total
        )

    except Exception as e:
        logger.error(f"获取领域列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取领域列表失败: {str(e)}")


@router.get("/knowledge-domains/{namespace}", response_model=KnowledgeDomainResponse)
async def get_domain_by_namespace(
    namespace: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据命名空间获取单个领域信息

    Args:
        namespace: 领域命名空间

    Returns:
        KnowledgeDomainResponse: 领域详细信息
    """
    try:
        domain = domain_service.get_domain_by_namespace(db=db, namespace=namespace)

        if not domain:
            raise HTTPException(
                status_code=404,
                detail=f"领域 '{namespace}' 不存在"
            )

        return KnowledgeDomainResponse(
            id=domain.id,
            namespace=domain.namespace,
            display_name=domain.display_name,
            description=domain.description,
            keywords=domain.keywords,
            icon=domain.icon,
            color=domain.color,
            is_active=domain.is_active,
            priority=domain.priority,
            parent_namespace=domain.parent_namespace,
            permissions=domain.permissions,
            metadata=domain.metadata_,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取领域失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取领域失败: {str(e)}")


@router.post("/knowledge-domains", response_model=KnowledgeDomainResponse, status_code=201)
async def create_domain(
    domain_data: KnowledgeDomainCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # 只有管理员可以创建领域
):
    """
    创建新的知识领域 (需要管理员权限)

    Args:
        domain_data: 领域创建数据

    Returns:
        KnowledgeDomainResponse: 创建的领域信息
    """
    try:
        domain = domain_service.create_domain(db=db, domain_data=domain_data)

        logger.info(f"用户 {current_user.username} 创建了领域: {domain.namespace}")

        return KnowledgeDomainResponse(
            id=domain.id,
            namespace=domain.namespace,
            display_name=domain.display_name,
            description=domain.description,
            keywords=domain.keywords,
            icon=domain.icon,
            color=domain.color,
            is_active=domain.is_active,
            priority=domain.priority,
            parent_namespace=domain.parent_namespace,
            permissions=domain.permissions,
            metadata=domain.metadata_,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    except DomainAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"创建领域失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建领域失败: {str(e)}")


@router.put("/knowledge-domains/{namespace}", response_model=KnowledgeDomainResponse)
async def update_domain(
    namespace: str,
    domain_data: KnowledgeDomainUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # 只有管理员可以更新领域
):
    """
    更新知识领域 (需要管理员权限)

    Args:
        namespace: 领域命名空间
        domain_data: 更新数据

    Returns:
        KnowledgeDomainResponse: 更新后的领域信息
    """
    try:
        domain = domain_service.update_domain(
            db=db,
            namespace=namespace,
            domain_data=domain_data
        )

        logger.info(f"用户 {current_user.username} 更新了领域: {namespace}")

        return KnowledgeDomainResponse(
            id=domain.id,
            namespace=domain.namespace,
            display_name=domain.display_name,
            description=domain.description,
            keywords=domain.keywords,
            icon=domain.icon,
            color=domain.color,
            is_active=domain.is_active,
            priority=domain.priority,
            parent_namespace=domain.parent_namespace,
            permissions=domain.permissions,
            metadata=domain.metadata_,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    except DomainNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新领域失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新领域失败: {str(e)}")


@router.delete("/knowledge-domains/{namespace}", status_code=204)
async def delete_domain(
    namespace: str,
    force: bool = QueryParam(False, description="是否强制删除(即使有关联文档)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)  # 只有管理员可以删除领域
):
    """
    删除知识领域 (需要管理员权限)

    Args:
        namespace: 领域命名空间
        force: 是否强制删除

    Returns:
        None (204 No Content)
    """
    try:
        # 防止删除默认领域
        if namespace == "default":
            raise HTTPException(
                status_code=403,
                detail="不能删除默认领域"
            )

        domain_service.delete_domain(db=db, namespace=namespace, force=force)

        logger.info(f"用户 {current_user.username} 删除了领域: {namespace} (force={force})")

        return None

    except DomainNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除领域失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除领域失败: {str(e)}")


@router.get("/knowledge-domains/{namespace}/stats", response_model=KnowledgeDomainStatsResponse)
async def get_domain_stats(
    namespace: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取知识领域统计信息

    Args:
        namespace: 领域命名空间

    Returns:
        KnowledgeDomainStatsResponse: 统计信息
    """
    try:
        stats = domain_service.get_domain_stats(db=db, namespace=namespace)
        return stats

    except DomainNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取领域统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取领域统计失败: {str(e)}")


@router.get("/knowledge-domains/search/{keyword}")
async def search_domains(
    keyword: str,
    include_inactive: bool = QueryParam(False, description="是否包含未启用的领域"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    搜索知识领域

    Args:
        keyword: 搜索关键词
        include_inactive: 是否包含未启用的领域

    Returns:
        List[KnowledgeDomainResponse]: 匹配的领域列表
    """
    try:
        domains = domain_service.search_domains_by_keyword(
            db=db,
            keyword=keyword,
            include_inactive=include_inactive
        )

        results = [
            KnowledgeDomainResponse(
                id=d.id,
                namespace=d.namespace,
                display_name=d.display_name,
                description=d.description,
                keywords=d.keywords,
                icon=d.icon,
                color=d.color,
                is_active=d.is_active,
                priority=d.priority,
                parent_namespace=d.parent_namespace,
                permissions=d.permissions,
                metadata=d.metadata_,
                created_at=d.created_at,
                updated_at=d.updated_at
            )
            for d in domains
        ]

        return results

    except Exception as e:
        logger.error(f"搜索领域失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索领域失败: {str(e)}")
