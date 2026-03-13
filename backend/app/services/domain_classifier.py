"""
领域分类器 (Domain Classifier)

提供多种策略的智能领域分类功能:
- 关键词分类器: 基于规则的快速分类
- LLM分类器: 基于大模型的智能分类
- 混合分类器: 结合关键词和LLM的最佳实践
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import name
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import time
import re
from sqlalchemy.orm import Session
from app.models.knowledge_domain import KnowledgeDomain, DomainRoutingRule

# type: ignore  # SQLAlchemy 模型属性访问在 Pylance 中会产生类型警告


@dataclass
class DomainClassificationResult:
    """领域分类结果"""
    namespace: str
    display_name: str
    confidence: float  # 0.0-1.0
    method: str  # 'keyword', 'llm', 'hybrid'
    reasoning: str  # 推理过程
    alternatives: List[Dict[str, Any]] = field(default_factory=list)  # 备选领域
    fallback_to_cross_domain: bool = False  # 是否建议跨领域检索
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'namespace': self.namespace,
            'display_name': self.display_name,
            'confidence': self.confidence,
            'method': self.method,
            'reasoning': self.reasoning,
            'alternatives': self.alternatives,
            'fallback_to_cross_domain': self.fallback_to_cross_domain,
            'metadata': self.metadata
        }


class DomainClassifier(ABC):
    """领域分类器抽象基类"""

    def __init__(self, db: Session):
        self.db = db
        self._domains_cache = None
        self._cache_timestamp = None
        self.cache_ttl = 300  # 5分钟缓存

    def get_active_domains(self) -> List[KnowledgeDomain]:
        """获取活跃领域(带缓存)"""
        now = time.time()
        if (self._domains_cache is None or
            self._cache_timestamp is None or
            now - self._cache_timestamp > self.cache_ttl):
            self._domains_cache = self.db.query(KnowledgeDomain).filter(
                KnowledgeDomain.is_active == True
            ).order_by(KnowledgeDomain.priority.desc()).all()
            self._cache_timestamp = now
        return self._domains_cache

    @abstractmethod
    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainClassificationResult:
        """
        分类查询到领域

        Args:
            query: 用户查询
            context: 上下文信息(如用户ID、会话ID、历史领域等)

        Returns:
            DomainClassificationResult
        """
        pass

    def extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词(简单实现,支持中英文)

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 转小写
        text = text.lower()

        # 移除标点符号,但保留中文字符
        text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)

        # 提取英文单词和中文词组
        keywords = []

        # 提取英文单词(空格分隔)
        english_words = re.findall(r'[a-z]+', text)
        keywords.extend(english_words)

        # 提取中文2-4字词组(简单滑动窗口)
        chinese_text = re.sub(r'[a-z\s]+', '', text)
        if chinese_text:
            # 2字词
            for i in range(len(chinese_text) - 1):
                keywords.append(chinese_text[i:i+2])
            # 3字词
            for i in range(len(chinese_text) - 2):
                keywords.append(chinese_text[i:i+3])
            # 4字词
            for i in range(len(chinese_text) - 3):
                keywords.append(chinese_text[i:i+4])

        # 过滤停用词(简化版)
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '如何', '怎么',
            '什么', '哪里', '为什么', '吗', '吧', '呢', '啊', '呀'
        }

        keywords = [w for w in keywords if w not in stop_words and len(w) >= 2]

        return keywords


class KeywordClassifier(DomainClassifier):
    """关键词分类器 - 基于规则的快速分类"""

    def __init__(self, db: Session):
        super().__init__(db)
        self._routing_rules_cache = None
        self._rules_cache_timestamp = None

    def get_routing_rules(self) -> List[DomainRoutingRule]:
        """获取路由规则(带缓存)"""
        now = time.time()
        if (self._routing_rules_cache is None or
            self._rules_cache_timestamp is None or
            now - self._rules_cache_timestamp > self.cache_ttl):
            self._routing_rules_cache = self.db.query(DomainRoutingRule).filter(
                DomainRoutingRule.is_active == True
            ).order_by(DomainRoutingRule.priority.desc()).all()
            self._rules_cache_timestamp = now
        return self._routing_rules_cache

    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainClassificationResult:
        """
        基于关键词匹配的分类

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            DomainClassificationResult
        """
        domains = self.get_active_domains()
        rules = self.get_routing_rules()

        # 提取查询关键词
        query_keywords = set(self.extract_keywords(query))

        # 计算每个领域的匹配分数
        scores = {}
        matched_keywords = {}

        for domain in domains:
            # 提取领域关键词
            domain_keywords = set()
            if domain.keywords:
                for kw in domain.keywords:
                    domain_keywords.add(kw.lower())

            # 计算关键词匹配
            matches = query_keywords.intersection(domain_keywords)
            if matches:
                matched_keywords[domain.namespace] = list(matches)
                # 匹配度 = 匹配的关键词数 / 查询关键词总数
                score = len(matches) / max(len(query_keywords), 1)
                scores[domain.namespace] = score

        # 应用路由规则
        for rule in rules:
            if rule.rule_type == 'keyword':
                # 简单关键词匹配
                pattern_keywords = set(rule.pattern.lower().split())
                matches = query_keywords.intersection(pattern_keywords)
                if matches:
                    # 规则优先级更高
                    current_score = scores.get(rule.target_namespace, 0)
                    rule_score = len(matches) / max(len(pattern_keywords), 1)
                    scores[rule.target_namespace] = max(current_score, rule_score)

            elif rule.rule_type == 'regex':
                # 正则表达式匹配
                if re.search(rule.pattern, query, re.IGNORECASE):
                    scores[rule.target_namespace] = max(
                        scores.get(rule.target_namespace, 0),
                        0.9  # 正则匹配给高分
                    )

        # 如果没有任何匹配,返回默认领域
        if not scores:
            default_domain = next((d for d in domains if d.namespace == 'default'), domains[0] if domains else None)
            if default_domain:
                return DomainClassificationResult(
                    namespace=default_domain.namespace,
                    display_name=default_domain.display_name,
                    confidence=0.3,
                    method='keyword',
                    reasoning='未匹配到关键词,返回默认领域',
                    alternatives=[],
                    fallback_to_cross_domain=True,
                    metadata={'query_keywords': list(query_keywords)}
                )

        # 找到最高分领域
        best_namespace = max(scores, key=scores.get)
        best_score = scores[best_namespace]
        best_domain = next(d for d in domains if d.namespace == best_namespace)

        # 生成备选项(分数前3的其他领域)
        alternatives = []
        for namespace, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:4]:
            domain = next((d for d in domains if d.namespace == namespace), None)
            if domain:
                alternatives.append({
                    'namespace': namespace,
                    'display_name': domain.display_name,
                    'confidence': score
                })

        # 生成推理说明
        matches = matched_keywords.get(best_namespace, [])
        reasoning = f"匹配到关键词: {', '.join(matches[:5])}" if matches else "基于路由规则匹配"

        return DomainClassificationResult(
            namespace=best_namespace,
            display_name=best_domain.display_name,
            confidence=best_score,
            method='keyword',
            reasoning=reasoning,
            alternatives=alternatives,
            fallback_to_cross_domain=(best_score < 0.5),  # 低置信度建议跨领域
            metadata={
                'matched_keywords': matches,
                'query_keywords': list(query_keywords),
                'all_scores': scores
            }
        )


class LLMClassifier(DomainClassifier):
    """LLM分类器 - 基于大模型的智能分类"""

    def __init__(self, db: Session, llm_service = None):
        super().__init__(db)
        if llm_service is None:
            # 懒加载 LLMService
            from app.services.llm_service import LLMService
            self.llm_service = LLMService(db=db)
        else:
            self.llm_service = llm_service

    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainClassificationResult:
        """
        基于LLM的智能分类

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            DomainClassificationResult
        """
        domains: List[KnowledgeDomain] = self.get_active_domains()

        # 构建领域描述
        domain_descriptions = []
        for domain in domains:
            desc = f"- {domain.display_name} ({domain.namespace}): {domain.description or '未提供描述'}"
            if domain.keywords:
                desc += f" 关键词: {', '.join(domain.keywords[:5])}"
            domain_descriptions.append(desc)

        # 获取上一轮领域信息(如果有)
        previous_domain = context.get('previous_domain') if context else None
        previous_domain_hint = ""
        if previous_domain:
            # 查找previous_domain的display_name
            prev_domain_obj = next((d for d in domains if d.namespace == previous_domain), None)
            if prev_domain_obj:
                previous_domain_hint = f"""
上一轮对话的领域: {prev_domain_obj.display_name} ({previous_domain})
提示: 如果当前查询是对上一轮的延续或追问,应该倾向于使用相同的领域。
"""

        # 构建提示词
        prompt = f"""你是一个智能分类助手。请根据用户的查询,判断它最可能属于哪个知识领域。

可用的知识领域:
{chr(10).join(domain_descriptions)}
{previous_domain_hint}
用户查询: "{query}"

请分析查询的主题和意图,选择最合适的领域。返回JSON格式:
{{
  "namespace": "最匹配的领域的namespace(括号内的值,例如job_doc、technical_docs等)",
  "confidence": 0.0-1.0的置信度分数,
  "reasoning": "选择该领域的理由(1-2句话)",
  "alternatives": [
    {{"namespace": "备选领域的namespace(例如job_doc)", "confidence": 置信度}},
    {{"namespace": "备选领域的namespace", "confidence": 置信度}}
  ]
}}

示例1:
用户查询: "我是一名Python后端工程师,有5年微服务开发经验"
正确返回:
{{
  "namespace": "job_doc",
  "confidence": 0.95,
  "reasoning": "查询明确提到工程师职位和工作经验,属于简历类文档",
  "alternatives": [
    {{"namespace": "technical_docs", "confidence": 0.3}},
    {{"namespace": "default", "confidence": 0.1}}
  ]
}}

示例2:
用户查询: "FastAPI的依赖注入是如何工作的?"
正确返回:
{{
  "namespace": "technical_docs",
  "confidence": 0.90,
  "reasoning": "查询涉及具体的技术框架使用问题,属于技术文档范畴",
  "alternatives": [
    {{"namespace": "default", "confidence": 0.2}}
  ]
}}

重要提示:
- namespace必须是括号内的英文标识符(如job_doc、technical_docs),不是中文名称
- 例如: 对于"简历 (job_doc)",应返回"job_doc"而不是"简历"
- 如果查询涉及多个领域,选择最主要的
- 如果不确定,confidence应低于0.6
- 提供2-3个备选领域
"""

        try:
            # 调用LLM
            response = await self.llm_service.get_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的文档分类助手，负责将用户查询分类到合适的知识领域。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 较低温度以获得更确定的分类
                max_tokens=300
            )

            # 解析JSON响应
            import json

            # 清理可能的markdown格式标记
            content = response['content'].strip()
            if content.startswith('```json'):
                content = content[7:]  # 移除 ```json
            if content.endswith('```'):
                content = content[:-3]  # 移除 ```
            content = content.strip()

            result_data = json.loads(content)

            # 验证命名空间是否有效
            namespace = result_data.get('namespace', 'default')
            domain = next((d for d in domains if d.namespace == namespace), None)

            if not domain:
                # 如果LLM返回的领域不存在,fallback到默认领域
                default_candidates = [d for d in domains if d.namespace == 'default']
                domain = default_candidates[0] if default_candidates else domains[0]
                namespace = domain.namespace
            if domain:
                namespace = domain.namespace

            return DomainClassificationResult(
                namespace=namespace,
                display_name=domain.display_name,
                confidence=result_data.get('confidence', 0.5),
                method='llm',
                reasoning=result_data.get('reasoning', 'LLM分类'),
                alternatives=result_data.get('alternatives', []),
                fallback_to_cross_domain=(result_data.get('confidence', 0.5) < 0.6),
                metadata={
                    'llm_response': response,
                    'model': self.llm_service.default_model
                }
            )

        except Exception as e:
            # LLM调用失败,fallback到默认领域
            default_candidates = [d for d in domains if d.namespace == 'default'] if domains else []
            default_domain = default_candidates[0] if default_candidates else (domains[0] if domains else None)
            if default_domain:
                return DomainClassificationResult(
                    namespace=default_domain.namespace,
                    display_name=default_domain.display_name,
                    confidence=0.3,
                    method='llm',
                    reasoning=f'LLM分类失败: {str(e)},返回默认领域',
                    alternatives=[],
                    fallback_to_cross_domain=True,
                    metadata={'error': str(e)}
                )


class HybridClassifier(DomainClassifier):
    """混合分类器 - 结合关键词和LLM的最佳实践"""

    def __init__(self, db: Session, llm_service = None):
        super().__init__(db)
        self.keyword_classifier = KeywordClassifier(db)
        self.llm_classifier = LLMClassifier(db, llm_service)

    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DomainClassificationResult:
        """
        混合分类策略

        1. 先使用关键词分类(快速)
        2. 如果置信度高(>0.7),直接返回
        3. 如果置信度低(<0.7),调用LLM二次确认
        4. 综合两种方法的结果

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            DomainClassificationResult
        """
        # 第一步:关键词分类
        keyword_result = await self.keyword_classifier.classify(query, context)

        # 如果关键词分类置信度高,直接返回
        if keyword_result.confidence >= 0.5:
            keyword_result.method = 'hybrid'
            keyword_result.metadata['strategy'] = 'keyword_only'
            keyword_result.metadata['keyword_confidence'] = keyword_result.confidence
            return keyword_result

        # 第二步:LLM分类
        try:
            llm_result = await self.llm_classifier.classify(query, context)

            # 综合两种结果
            # 如果两者一致,提升置信度
            if keyword_result.namespace == llm_result.namespace:
                final_confidence = min(
                    (keyword_result.confidence + llm_result.confidence) / 2 + 0.2,
                    1.0
                )
                reasoning = f"关键词和LLM一致: {llm_result.reasoning}"
                strategy = 'both_agree'
            else:
                # 如果不一致,选择置信度更高的
                if llm_result.confidence > keyword_result.confidence:
                    final_result = llm_result
                    final_result.metadata['keyword_result'] = keyword_result.to_dict()
                    strategy = 'llm_chosen'
                else:
                    final_result = keyword_result
                    final_result.metadata['llm_result'] = llm_result.to_dict()
                    strategy = 'keyword_chosen'

                final_result.method = 'hybrid'
                final_result.metadata['strategy'] = strategy
                return final_result

            return DomainClassificationResult(
                namespace=keyword_result.namespace,
                display_name=keyword_result.display_name,
                confidence=final_confidence,
                method='hybrid',
                reasoning=reasoning,
                alternatives=llm_result.alternatives or keyword_result.alternatives,
                fallback_to_cross_domain=(final_confidence < 0.6),
                metadata={
                    'strategy': strategy,
                    'keyword_confidence': keyword_result.confidence,
                    'llm_confidence': llm_result.confidence,
                    'keyword_result': keyword_result.to_dict(),
                    'llm_result': llm_result.to_dict()
                }
            )

        except Exception as e:
            # LLM失败,降级到关键词结果
            keyword_result.method = 'hybrid'
            keyword_result.metadata['strategy'] = 'keyword_fallback'
            keyword_result.metadata['llm_error'] = str(e)
            return keyword_result


# 全局分类器实例(可在应用启动时初始化)
_classifier_instance = None


def get_classifier(
    db: Session,
    classifier_type: str = 'hybrid',
    llm_service = None
) -> DomainClassifier:
    """
    获取分类器实例

    Args:
        db: 数据库会话
        classifier_type: 分类器类型 ('keyword', 'llm', 'hybrid')
        llm_service: LLM服务实例

    Returns:
        DomainClassifier实例
    """
    if classifier_type == 'keyword':
        return KeywordClassifier(db)
    elif classifier_type == 'llm':
        return LLMClassifier(db, llm_service)
    else:  # hybrid
        return HybridClassifier(db, llm_service)
