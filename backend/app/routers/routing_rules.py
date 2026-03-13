"""
领域路由规则管理 API

提供路由规则的 CRUD 和匹配功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.connection import get_db
from app.models.database import User
from app.middleware.auth import get_current_active_user, require_admin
from app.services.routing_rule_service import get_routing_rule_service, RoutingRuleService
from app.schemas.routing_rule import (
    DomainRoutingRuleCreate,
    DomainRoutingRuleUpdate,
    DomainRoutingRuleResponse,
    DomainRoutingRuleListResponse,
    RoutingRuleMatchRequest,
    RoutingRuleMatchResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/routing-rules", response_model=DomainRoutingRuleListResponse)
async def get_all_routing_rules(
    include_inactive: bool = QueryParam(False, description="是否包含未激活的规则"),
    skip: int = QueryParam(0, ge=0, description="跳过数量"),
    limit: int = QueryParam(100, ge=1, le=500, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取所有路由规则列表
    
    Args:
        include_inactive: 是否包含未激活的规则
        skip: 分页跳过数
        limit: 分页限制数
    
    Returns:
        路由规则列表及总数
    """
    try:
        service = get_routing_rule_service(db)
        rules = service.get_all_rules(
            include_inactive=include_inactive,
            skip=skip,
            limit=limit
        )
        
        # 计算总数
        total_rules = service.get_all_rules(
            include_inactive=include_inactive,
            skip=0,
            limit=999999
        )
        
        return DomainRoutingRuleListResponse(
            rules=[DomainRoutingRuleResponse.model_validate(rule) for rule in rules],
            total=len(total_rules)
        )
    
    except Exception as e:
        logger.error(f"获取路由规则列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取路由规则列表失败: {str(e)}")


@router.get("/routing-rules/{rule_id}", response_model=DomainRoutingRuleResponse)
async def get_routing_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据ID获取单个路由规则
    
    Args:
        rule_id: 规则ID
    
    Returns:
        路由规则详情
    """
    try:
        service = get_routing_rule_service(db)
        rule = service.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"规则不存在: {rule_id}")
        
        return DomainRoutingRuleResponse.model_validate(rule)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取路由规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取路由规则失败: {str(e)}")


@router.post("/routing-rules", response_model=DomainRoutingRuleResponse, status_code=201)
async def create_routing_rule(
    rule_data: DomainRoutingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    创建新的路由规则 (需要管理员权限)
    
    Args:
        rule_data: 规则创建数据
    
    Returns:
        创建的规则信息
    """
    try:
        service = get_routing_rule_service(db)
        rule = service.create_rule(
            rule_name=rule_data.rule_name,
            rule_type=rule_data.rule_type,
            pattern=rule_data.pattern,
            target_namespace=rule_data.target_namespace,
            confidence_threshold=rule_data.confidence_threshold,
            priority=rule_data.priority,
            is_active=rule_data.is_active,
            metadata=rule_data.metadata
        )
        
        logger.info(f"用户 {current_user.username} 创建了路由规则: {rule.rule_name}")
        
        return DomainRoutingRuleResponse.model_validate(rule)
    
    except Exception as e:
        logger.error(f"创建路由规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建路由规则失败: {str(e)}")


@router.put("/routing-rules/{rule_id}", response_model=DomainRoutingRuleResponse)
async def update_routing_rule(
    rule_id: int,
    rule_data: DomainRoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新路由规则 (需要管理员权限)
    
    Args:
        rule_id: 规则ID
        rule_data: 更新数据
    
    Returns:
        更新后的规则信息
    """
    try:
        service = get_routing_rule_service(db)
        
        # 只更新提供的字段
        update_data = rule_data.model_dump(exclude_unset=True)
        rule = service.update_rule(rule_id, **update_data)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"规则不存在: {rule_id}")
        
        logger.info(f"用户 {current_user.username} 更新了路由规则: {rule_id}")
        
        return DomainRoutingRuleResponse.model_validate(rule)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新路由规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新路由规则失败: {str(e)}")


@router.delete("/routing-rules/{rule_id}", status_code=204)
async def delete_routing_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    删除路由规则 (需要管理员权限)
    
    Args:
        rule_id: 规则ID
    
    Returns:
        None (204 No Content)
    """
    try:
        service = get_routing_rule_service(db)
        success = service.delete_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"规则不存在: {rule_id}")
        
        logger.info(f"用户 {current_user.username} 删除了路由规则: {rule_id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除路由规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除路由规则失败: {str(e)}")


@router.post("/routing-rules/match", response_model=RoutingRuleMatchResponse)
async def match_routing_rule(
    request: RoutingRuleMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    测试查询与路由规则的匹配
    
    Args:
        request: 匹配请求 (包含查询文本和最小置信度)
    
    Returns:
        匹配结果
    """
    try:
        service = get_routing_rule_service(db)
        result = service.match_query(
            query=request.query,
            min_confidence=request.min_confidence
        )
        
        if result:
            target_namespace, confidence, rule_name = result
            return RoutingRuleMatchResponse(
                matched=True,
                target_namespace=target_namespace,
                confidence=confidence,
                rule_name=rule_name,
                message=f"匹配成功: {rule_name} -> {target_namespace}"
            )
        else:
            return RoutingRuleMatchResponse(
                matched=False,
                message="未匹配到路由规则"
            )
    
    except Exception as e:
        logger.error(f"路由规则匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"路由规则匹配失败: {str(e)}")
