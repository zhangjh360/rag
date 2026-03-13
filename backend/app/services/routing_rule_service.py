"""
领域路由规则服务

功能:
- 基于规则匹配查询到目标领域
- 支持关键词规则、正则规则等
- 规则优先级管理
"""

import re
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.knowledge_domain import DomainRoutingRule

logger = logging.getLogger(__name__)


class RoutingRuleService:
    """路由规则服务"""
    
    def __init__(self, db: Session):
        """
        初始化路由规则服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def get_active_rules(self, rule_type: Optional[str] = None) -> List[DomainRoutingRule]:
        """
        获取所有激活的规则
        
        Args:
            rule_type: 规则类型过滤 (keyword/regex/pattern)
        
        Returns:
            规则列表 (按优先级降序)
        """
        query = self.db.query(DomainRoutingRule).filter(
            DomainRoutingRule.is_active == True
        )
        
        if rule_type:
            query = query.filter(DomainRoutingRule.rule_type == rule_type)
        
        return query.order_by(DomainRoutingRule.priority.desc()).all()
    
    def match_query(
        self, 
        query: str,
        min_confidence: float = 0.0
    ) -> Optional[Tuple[str, float, str]]:
        """
        匹配查询到最佳领域
        
        Args:
            query: 用户查询
            min_confidence: 最小置信度阈值
        
        Returns:
            (target_namespace, confidence, rule_name) 或 None
        """
        # 获取所有激活的规则
        rules = self.get_active_rules()
        
        if not rules:
            logger.debug("没有激活的路由规则")
            return None
        
        # 按优先级匹配
        for rule in rules:
            matched, confidence = self._match_rule(query, rule)

            if matched and confidence >= rule.confidence_threshold and confidence >= min_confidence:
                logger.info(
                    f"路由规则匹配成功: '{rule.rule_name}' -> {rule.target_namespace} "
                    f"(confidence: {confidence:.2f})"
                )
                return (str(rule.target_namespace), confidence, str(rule.rule_name))
        
        logger.debug(f"未匹配到路由规则: {query}")
        return None
    
    def _match_rule(self, query: str, rule: DomainRoutingRule) -> Tuple[bool, float]:
        """
        匹配单条规则
        
        Args:
            query: 用户查询
            rule: 规则对象
        
        Returns:
            (是否匹配, 置信度)
        """
        try:
            if rule.rule_type == 'keyword':
                return self._match_keyword(query, str(rule.pattern))
            elif rule.rule_type == 'regex':
                return self._match_regex(query, str(rule.pattern))
            elif rule.rule_type == 'pattern':
                return self._match_pattern(query, str(rule.pattern))
            else:
                logger.warning(f"未知规则类型: {rule.rule_type}")
                return False, 0.0
        except Exception as e:
            logger.error(f"规则匹配失败: {rule.rule_name}, error: {e}")
            return False, 0.0
    
    def _match_keyword(self, query: str, pattern: str) -> Tuple[bool, float]:
        """
        关键词匹配
        
        Args:
            query: 查询文本
            pattern: 关键词模式 (用 | 分隔)
        
        Returns:
            (是否匹配, 置信度)
        """
        # 分割关键词
        keywords = [kw.strip() for kw in pattern.split('|') if kw.strip()]
        
        if not keywords:
            return False, 0.0
        
        # 统计匹配的关键词数量
        query_lower = query.lower()
        matched_count = sum(1 for kw in keywords if kw.lower() in query_lower)
        
        if matched_count == 0:
            return False, 0.0
        
        # 置信度 = 匹配关键词数 / 总关键词数
        confidence = min(matched_count / len(keywords) * 1.5, 1.0)  # 乘以1.5增加权重,上限1.0
        
        return True, confidence
    
    def _match_regex(self, query: str, pattern: str) -> Tuple[bool, float]:
        """
        正则表达式匹配
        
        Args:
            query: 查询文本
            pattern: 正则表达式
        
        Returns:
            (是否匹配, 置信度)
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(query)
            
            if match:
                # 根据匹配长度计算置信度
                match_length = len(match.group(0))
                query_length = len(query)
                confidence = min(match_length / query_length * 2, 1.0)
                return True, confidence
            else:
                return False, 0.0
        except re.error as e:
            logger.error(f"正则表达式错误: {pattern}, error: {e}")
            return False, 0.0
    
    def _match_pattern(self, query: str, pattern: str) -> Tuple[bool, float]:
        """
        通配符模式匹配
        
        Args:
            query: 查询文本
            pattern: 模式 (支持 * 和 ?)
        
        Returns:
            (是否匹配, 置信度)
        """
        # 将通配符模式转换为正则
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return self._match_regex(query, f'^{regex_pattern}$')
    
    def get_all_rules(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[DomainRoutingRule]:
        """
        获取所有规则
        
        Args:
            include_inactive: 是否包含未激活的规则
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            规则列表
        """
        query = self.db.query(DomainRoutingRule)
        
        if not include_inactive:
            query = query.filter(DomainRoutingRule.is_active == True)
        
        return query.order_by(
            DomainRoutingRule.priority.desc(),
            DomainRoutingRule.id.asc()
        ).offset(skip).limit(limit).all()
    
    def get_rule_by_id(self, rule_id: int) -> Optional[DomainRoutingRule]:
        """
        根据ID获取规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            规则对象或None
        """
        return self.db.query(DomainRoutingRule).filter(
            DomainRoutingRule.id == rule_id
        ).first()
    
    def create_rule(
        self,
        rule_name: str,
        rule_type: str,
        pattern: str,
        target_namespace: str,
        confidence_threshold: float = 0.7,
        priority: int = 0,
        is_active: bool = True,
        metadata: dict = None
    ) -> DomainRoutingRule:
        """
        创建新规则
        
        Args:
            rule_name: 规则名称
            rule_type: 规则类型 (keyword/regex/pattern)
            pattern: 匹配模式
            target_namespace: 目标领域
            confidence_threshold: 置信度阈值
            priority: 优先级
            is_active: 是否激活
            metadata: 元数据
        
        Returns:
            创建的规则对象
        """
        rule = DomainRoutingRule(
            rule_name=rule_name,
            rule_type=rule_type,
            pattern=pattern,
            target_namespace=target_namespace,
            confidence_threshold=confidence_threshold,
            priority=priority,
            is_active=is_active,
            metadata_=metadata or {}
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"创建路由规则: {rule_name} -> {target_namespace}")
        
        return rule
    
    def update_rule(
        self,
        rule_id: int,
        **kwargs
    ) -> Optional[DomainRoutingRule]:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            **kwargs: 更新字段
        
        Returns:
            更新后的规则对象或None
        """
        rule = self.get_rule_by_id(rule_id)
        
        if not rule:
            logger.warning(f"规则不存在: {rule_id}")
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)
        
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"更新路由规则: {rule_id}")
        
        return rule
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            是否删除成功
        """
        rule = self.get_rule_by_id(rule_id)
        
        if not rule:
            logger.warning(f"规则不存在: {rule_id}")
            return False
        
        self.db.delete(rule)
        self.db.commit()
        
        logger.info(f"删除路由规则: {rule_id}")
        
        return True


# 工厂函数
def get_routing_rule_service(db: Session) -> RoutingRuleService:
    """
    获取路由规则服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        RoutingRuleService实例
    """
    return RoutingRuleService(db=db)
