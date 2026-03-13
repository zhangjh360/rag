"""
Chat专用的RAG服务
整合领域分类、混合检索、跨域检索，提供简化的chat接口
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.services.domain_classifier import HybridClassifier
from app.services.hybrid_retrieval import HybridRetrieval
from app.services.cross_domain_retrieval import CrossDomainRetrieval
from app.services.bm25_retrieval import BM25Retrieval
from app.services.llm_service import LLMService
from app.services.query_performance import QueryPerformanceLogger
from app.services.query_rewriter import QueryRewriter

logger = logging.getLogger(__name__)


class ChatRAGService:
    """
    Chat专用的RAG检索服务

    特点:
    - 自动领域分类
    - 自动选择检索模式(单领域/跨领域)
    - 多层降级策略
    - 性能监控集成
    - 返回兼容旧格式的结果
    """

    def __init__(self, db: Session):
        """
        初始化Chat RAG服务

        Args:
            db: 数据库会话
        """
        self.db = db

        # 初始化各个服务组件
        self.llm_service = LLMService(db=db)
        self.classifier = HybridClassifier(db=db, llm_service=self.llm_service)
        self.hybrid_retrieval = HybridRetrieval(db=db)
        self.cross_domain_retrieval = CrossDomainRetrieval(db=db)
        self.bm25_retrieval = BM25Retrieval(db=db)
        self.perf_logger = QueryPerformanceLogger(db=db)
        self.query_rewriter = QueryRewriter(llm_service=self.llm_service)

        # 配置参数
        self.classification_confidence_threshold = 0.6  # 分类置信度阈值
        self.default_top_k = 5
        self.default_alpha = 0.5  # 混合检索权重
        self.default_similarity_threshold = 0.2

    async def search_for_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        alpha: Optional[float] = None,  # 新增:混合检索权重
        namespace: Optional[str] = None,  # 可选的知识领域参数
        chat_history: Optional[List[Dict[str, str]]] = None,  # 新增:聊天历史
        previous_domain: Optional[str] = None,  # 新增:上一轮领域
        enable_query_rewrite: bool = True  # 新增:是否启用查询重写
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        为Chat优化的检索接口(会话上下文感知版本)

        流程:
        0. 查询重写(如果启用且有历史上下文)
        1. 领域分类(如果未提供namespace,考虑previous_domain)
        2. 根据置信度决定检索模式(单领域/跨领域)
        3. 执行混合检索(向量+BM25)
        4. 多层降级策略
        5. 记录性能日志

        Args:
            query: 用户查询
            session_id: 会话ID(用于性能追踪)
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            namespace: 可选的知识领域过滤,如果提供则跳过自动分类,直接使用指定领域
            chat_history: 聊天历史,格式: [{"role": "user/assistant", "content": "..."}]
            previous_domain: 上一轮对话的领域namespace
            enable_query_rewrite: 是否启用查询重写(基于历史补全代词和省略)

        Returns:
            (sources, metadata)
            - sources: 兼容旧格式的检索结果列表
              格式: [{"chunk_id": int, "content": str, "similarity": float, "filename": str}]
            - metadata: 扩展信息(领域分类、性能统计、查询重写等)
        """
        start_time = time.time()
        top_k = top_k or self.default_top_k
        similarity_threshold = similarity_threshold or self.default_similarity_threshold
        alpha = alpha if alpha is not None else self.default_alpha  # 使用传入的alpha或默认值

        # 用于性能追踪的数据
        performance_data = {
            'top_k': top_k,
            'similarity_threshold': similarity_threshold,
            'alpha': alpha,
            'has_previous_domain': previous_domain is not None,
            'has_chat_history': chat_history is not None and len(chat_history) > 0
        }

        classification_result = None
        retrieval_mode = 'unknown'
        target_namespace = namespace or 'default'  # 使用提供的namespace或默认值
        confidence = 1.0  # 默认置信度

        # 查询重写相关变量
        rewritten_query = query
        query_was_rewritten = False
        rewrite_latency = 0.0

        try:
            # Step 0: 查询重写(如果启用且有历史上下文)
            if enable_query_rewrite and chat_history and len(chat_history) > 0:
                rewrite_start = time.time()
                try:
                    rewritten_query, query_was_rewritten = await self.query_rewriter.rewrite_with_context(
                        current_query=query,
                        chat_history=chat_history,
                        max_history=5  # 最多使用5轮历史
                    )
                    rewrite_latency = (time.time() - rewrite_start) * 1000
                    performance_data['rewrite_latency_ms'] = rewrite_latency
                    performance_data['query_rewritten'] = query_was_rewritten

                    if query_was_rewritten:
                        logger.info(
                            f"查询重写: '{query}' → '{rewritten_query}' "
                            f"(耗时: {rewrite_latency:.0f}ms)"
                        )
                except Exception as e:
                    logger.warning(f"查询重写失败,使用原查询: {e}")
                    rewritten_query = query
                    query_was_rewritten = False

            # Step 1: 领域分类(如果未提供namespace)
            classification_latency = 0.0

            if namespace:
                # 用户显式指定了领域,跳过自动分类
                logger.info(f"使用用户指定的领域: namespace={namespace}")
                classification_result = {
                    'namespace': namespace,
                    'confidence': 1.0,  # 用户指定的领域,置信度为1.0
                    'method': 'user_specified'
                }
                retrieval_mode = 'single'  # 直接使用单领域检索
            else:
                # 执行自动领域分类(使用重写后的查询)
                classification_start = time.time()
                classification_result = await self._classify_query(
                    query=rewritten_query,  # 使用重写后的查询
                    previous_domain=previous_domain  # 传递上一轮领域
                )
                classification_latency = (time.time() - classification_start) * 1000
                performance_data['classification_latency_ms'] = classification_latency

                target_namespace = classification_result.get('namespace', 'default')
                confidence = classification_result.get('confidence', 0.0)
                inherited_from_previous = classification_result.get('inherited_from_previous', False)

                logger.info(
                    f"领域分类结果: namespace={target_namespace}, "
                    f"confidence={confidence:.2f}, "
                    f"inherited={inherited_from_previous}, "
                    f"latency={classification_latency:.0f}ms"
                )

                # 根据置信度和领域继承情况决定检索模式
                if inherited_from_previous:
                    # 如果是继承的领域,使用单领域检索
                    retrieval_mode = 'single'
                    logger.info(f"继承上一轮领域: {target_namespace}")
                elif confidence >= self.classification_confidence_threshold:
                    retrieval_mode = 'single'
                else:
                    retrieval_mode = 'cross'
                    logger.info(f"置信度较低({confidence:.2f}), 启用跨领域检索")

            # Step 2: 执行检索(使用重写后的查询)
            retrieval_start = time.time()

            if retrieval_mode == 'single':
                # 单领域检索
                results, error = await self._single_domain_search(
                    query=rewritten_query,  # 使用重写后的查询
                    namespace=target_namespace,
                    top_k=top_k,
                    alpha=alpha  # 传递alpha参数
                )
            else:
                # 跨领域检索
                results, error = await self._cross_domain_search(
                    query=rewritten_query,  # 使用重写后的查询
                    top_k=top_k,
                    alpha=alpha  # 传递alpha参数
                )

            retrieval_latency = (time.time() - retrieval_start) * 1000
            performance_data['retrieval_latency_ms'] = retrieval_latency
            performance_data['namespace'] = target_namespace

            # Step 3: 转换为兼容格式
            sources = self._convert_to_legacy_format(results)

            # Step 4: 构建元数据
            total_latency = (time.time() - start_time) * 1000
            metadata = {
                'classification': classification_result,
                'retrieval_mode': retrieval_mode,
                'retrieval_method': 'hybrid',
                'total_latency_ms': total_latency,
                'classification_latency_ms': classification_latency,
                'retrieval_latency_ms': retrieval_latency,
                'rewrite_latency_ms': rewrite_latency,
                'total_results': len(sources),
                'error': error,
                # 新增:查询重写信息
                'query_rewrite': {
                    'enabled': enable_query_rewrite,
                    'was_rewritten': query_was_rewritten,
                    'original_query': query if query_was_rewritten else None,
                    'rewritten_query': rewritten_query if query_was_rewritten else None
                },
                # 新增:会话上下文信息
                'session_context': {
                    'previous_domain': previous_domain,
                    'domain_inherited': classification_result.get('inherited_from_previous', False) if classification_result else False,
                    'has_chat_history': chat_history is not None and len(chat_history) > 0
                }
            }

            # Step 5: 记录性能日志
            self._log_performance(
                query=query,
                retrieval_mode=retrieval_mode,
                performance_data=performance_data,
                result_data={
                    'total_candidates': len(results),
                    'total_results': len(sources),
                    'namespace': target_namespace
                },
                session_id=session_id,
                error=error
            )

            logger.info(
                f"检索完成: mode={retrieval_mode}, "
                f"results={len(sources)}, "
                f"total_latency={total_latency:.0f}ms"
            )

            return sources, metadata

        except Exception as e:
            logger.error(f"Chat RAG检索失败: {e}", exc_info=True)

            # 记录错误
            total_latency = (time.time() - start_time) * 1000
            self._log_performance(
                query=query,
                retrieval_mode=retrieval_mode,
                performance_data=performance_data,
                result_data={'total_results': 0},
                session_id=session_id,
                error=str(e)
            )

            # 返回空结果，但不中断对话
            return [], {
                'error': str(e),
                'total_latency_ms': total_latency,
                'retrieval_mode': retrieval_mode
            }

    async def _classify_query(
        self,
        query: str,
        previous_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        领域分类(带降级和领域继承)

        Args:
            query: 用户查询
            previous_domain: 上一轮对话的领域namespace

        Returns:
            分类结果字典,包含:
            - namespace: 领域
            - confidence: 置信度
            - method: 分类方法
            - inherited_from_previous: 是否继承自上一轮
        """
        try:
            # 调用混合分类器,传递previous_domain作为context
            context = {'previous_domain': previous_domain} if previous_domain else None
            result = await self.classifier.classify(query, context=context)

            result_dict = result.to_dict() if hasattr(result, 'to_dict') else {
                'namespace': getattr(result, 'namespace', 'default'),
                'confidence': getattr(result, 'confidence', 0.5),
                'method': getattr(result, 'method', 'hybrid'),
                'reasoning': getattr(result, 'reasoning', ''),
                'fallback_to_cross_domain': getattr(result, 'fallback_to_cross_domain', False)
            }

            # 领域继承逻辑:如果当前分类置信度低且存在previous_domain,则继承上一轮领域
            current_confidence = result_dict.get('confidence', 0.0)

            if previous_domain and current_confidence < self.classification_confidence_threshold:
                logger.info(
                    f"当前分类置信度较低({current_confidence:.2f}), "
                    f"继承上一轮领域: {previous_domain}"
                )
                result_dict['namespace'] = previous_domain
                result_dict['confidence'] = 0.7  # 继承的置信度设为0.7
                result_dict['method'] = f"{result_dict.get('method', 'hybrid')}_inherited"
                result_dict['inherited_from_previous'] = True
                result_dict['original_classification'] = {
                    'namespace': getattr(result, 'namespace', 'default'),
                    'confidence': current_confidence
                }
            else:
                result_dict['inherited_from_previous'] = False

            return result_dict

        except Exception as e:
            logger.warning(f"领域分类失败: {e}")

            # 降级: 如果有previous_domain,使用它;否则使用默认领域
            if previous_domain:
                logger.info(f"领域分类失败,使用上一轮领域: {previous_domain}")
                return {
                    'namespace': previous_domain,
                    'confidence': 0.6,
                    'method': 'fallback_inherited',
                    'reasoning': f'分类失败,继承上一轮领域: {str(e)}',
                    'inherited_from_previous': True,
                    'fallback_to_cross_domain': False
                }
            else:
                logger.info("领域分类失败,使用默认领域")
                return {
                    'namespace': 'default',
                    'confidence': 0.3,
                    'method': 'fallback',
                    'reasoning': f'分类失败: {str(e)}',
                    'inherited_from_previous': False,
                    'fallback_to_cross_domain': True
                }

    async def _single_domain_search(
        self,
        query: str,
        namespace: str,
        top_k: int,
        alpha: float = 0.5
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        单领域混合检索(带多层降级)

        降级链: 混合检索 → 向量检索 → BM25检索 → 空结果

        Args:
            query: 用户查询
            namespace: 领域命名空间
            top_k: 返回结果数量
            alpha: 混合检索权重(0.0=纯BM25, 1.0=纯向量)

        Returns:
            (results, error_message)
        """
        # Level 1: 混合检索 (最佳效果)
        try:
            results = await self.hybrid_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                alpha=alpha,  # 使用传入的alpha
                use_rrf=True
            )

            if results:
                logger.debug(f"混合检索成功: {len(results)} 条结果")
                return results, None
            else:
                logger.info("混合检索无结果，尝试降级")

        except Exception as e:
            logger.warning(f"混合检索失败: {e}")

        # Level 2: 向量检索 (降级)
        try:
            # 使用hybrid_retrieval的向量检索能力
            results = await self.hybrid_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                alpha=1.0,  # alpha=1.0 表示纯向量检索
                use_rrf=False
            )

            if results:
                logger.info(f"向量检索成功(降级): {len(results)} 条结果")
                return results, "降级到向量检索"
            else:
                logger.info("向量检索无结果，继续降级")

        except Exception as e:
            logger.warning(f"向量检索失败: {e}")

        # Level 3: BM25检索 (再次降级)
        try:
            results = await self.bm25_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k
            )

            if results:
                logger.info(f"BM25检索成功(降级): {len(results)} 条结果")
                return results, "降级到BM25检索"
            else:
                logger.info("BM25检索无结果")

        except Exception as e:
            logger.warning(f"BM25检索失败: {e}")

        # Level 4: 返回空结果
        logger.warning(f"所有检索方法失败，领域: {namespace}")
        return [], "所有检索方法均失败"

    async def _cross_domain_search(
        self,
        query: str,
        top_k: int,
        alpha: float = 0.5
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        跨领域检索(带降级)

        Args:
            query: 用户查询
            top_k: 返回结果数量
            alpha: 混合检索权重

        Returns:
            (results, error_message)
        """
        try:
            # 获取所有启用的领域
            from app.models.knowledge_domain import KnowledgeDomain
            domains = self.db.query(KnowledgeDomain).filter(
                KnowledgeDomain.is_active == True
            ).all()

            namespaces = [d.namespace for d in domains]

            if not namespaces:
                logger.warning("没有启用的领域，降级到单领域检索")
                return await self._single_domain_search(
                    query=query,
                    namespace='default',
                    top_k=top_k,
                    alpha=alpha
                )

            # 调用跨领域检索服务
            results = await self.cross_domain_retrieval.search_across_domains(
                query=query,
                namespaces=namespaces,
                top_k=top_k,
                alpha=alpha  # 使用传入的alpha
            )

            if results:
                logger.info(f"跨领域检索成功: {len(results)} 条结果")
                return results, None
            else:
                logger.info("跨领域检索无结果")
                return [], "跨领域检索无结果"

        except Exception as e:
            logger.error(f"跨领域检索失败: {e}")
            # 降级到默认领域的单领域检索
            logger.info("跨领域检索失败，降级到默认领域")
            return await self._single_domain_search(
                query=query,
                namespace='default',
                top_k=top_k
            )

    def _convert_to_legacy_format(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        将检索结果转换为旧格式，保持向后兼容

        新格式:
        - Dict 格式: {chunk_id, content, score, ...}
        - Tuple 格式: (chunk_dict, score)

        旧格式: {chunk_id, content, similarity, filename}

        Args:
            results: 检索结果列表 (可能是Dict或Tuple)

        Returns:
            兼容旧格式的结果列表
        """
        legacy_sources = []

        for item in results:
            # 处理不同的返回格式
            if isinstance(item, tuple):
                # 检查元组长度
                if len(item) == 3:
                    # 跨领域检索返回 (chunk_dict, namespace, score) 格式
                    result, namespace, score = item
                    result = dict(result)  # 确保是字典
                    if 'score' not in result and 'similarity' not in result:
                        result['similarity'] = score
                    # 保留namespace信息
                    if 'namespace' not in result:
                        result['namespace'] = namespace
                elif len(item) == 2:
                    # BM25 返回 (chunk_dict, score) 格式
                    result, score = item
                    result = dict(result)  # 确保是字典
                    if 'score' not in result and 'similarity' not in result:
                        result['similarity'] = score
                else:
                    logger.warning(f"未知的元组长度: {len(item)}, 跳过")
                    continue
            elif isinstance(item, dict):
                # 向量检索返回 dict 格式
                result = item
            else:
                logger.warning(f"未知的结果格式: {type(item)}, 跳过")
                continue

            # 提取必要字段
            legacy_source = {
                'chunk_id': result.get('chunk_id') or result.get('id'),
                'content': result.get('content', ''),
                'similarity': result.get('score') or result.get('similarity') or result.get('fusion_score', 0.0),
                'filename': result.get('document_title') or result.get('filename', '未知文档')
            }

            # 可选: 保留一些额外信息(不影响兼容性)
            if 'namespace' in result:
                legacy_source['namespace'] = result['namespace']
            if 'domain_display_name' in result:
                legacy_source['domain_display_name'] = result['domain_display_name']

            legacy_sources.append(legacy_source)

        return legacy_sources

    def _log_performance(
        self,
        query: str,
        retrieval_mode: str,
        performance_data: Dict[str, Any],
        result_data: Dict[str, Any],
        session_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        记录性能日志

        Args:
            query: 查询内容
            retrieval_mode: 检索模式
            performance_data: 性能数据
            result_data: 结果数据
            session_id: 会话ID
            error: 错误信息
        """
        try:
            self.perf_logger.log_query(
                query=query,
                retrieval_mode=retrieval_mode,
                retrieval_method='hybrid',
                performance_data=performance_data,
                result_data=result_data,
                session_id=session_id,
                error=error
            )
        except Exception as e:
            # 性能日志失败不应影响主流程
            logger.warning(f"性能日志记录失败: {e}")


def get_chat_rag_service(db: Session) -> ChatRAGService:
    """
    获取ChatRAGService实例(工厂函数)

    Args:
        db: 数据库会话

    Returns:
        ChatRAGService实例
    """
    return ChatRAGService(db=db)
