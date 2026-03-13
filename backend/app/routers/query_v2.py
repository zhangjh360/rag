"""
查询API v2 - 支持多领域智能检索

提供完整的查询流程:
1. 自动领域分类
2. 单领域/跨领域检索
3. 多种检索方法(向量/BM25/混合)
"""
import time
import uuid
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.query import QueryRequestV2, QueryResponseV2, ChunkResult, RetrievalStats
from app.models.database import User
from app.models.knowledge_domain import KnowledgeDomain
from app.middleware.auth import require_query_ask
from app.services.domain_classifier import get_classifier
from app.services.vector_retrieval import vector_retrieval_service
from app.services.bm25_retrieval import get_bm25_service
from app.services.hybrid_retrieval import get_hybrid_retrieval
from app.services.cross_domain_retrieval import get_cross_domain_retrieval
from app.services.query_performance import get_query_performance_logger
from app.config.logging_config import get_app_logger
from app.monitoring.metrics import (
    record_query_metrics,
    record_classification_metrics,
    record_rerank_metrics,
    record_retrieval_results
)

router = APIRouter()
logger = get_app_logger()


@router.post("/query/v2", response_model=QueryResponseV2)
async def query_documents_v2(
    request: QueryRequestV2,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    查询文档 v2 (支持自动分类和多领域检索)

    检索模式:
    - auto: 自动识别领域并决定检索策略
    - single: 单领域精确检索
    - cross: 跨领域检索

    检索方法:
    - vector: 纯向量检索(语义相似度)
    - bm25: 纯关键词检索(BM25算法)
    - hybrid: 混合检索(推荐,准确度最高)
    """
    start_time = time.time()
    classification_start_time = None
    retrieval_start_time = None

    # 性能数据收集
    performance_data = {
        'namespace': request.namespace,
        'top_k': request.top_k,
        'alpha': request.alpha,
        'similarity_threshold': request.similarity_threshold
    }

    # 获取性能日志记录器
    perf_logger = get_query_performance_logger(db)

    try:
        logger.info(f"查询v2: {request.query}, mode={request.retrieval_mode}, method={request.retrieval_method}")

        # === 步骤 1: 领域分类 ===
        namespace = request.namespace
        retrieval_mode = request.retrieval_mode or 'auto'
        classification_result = None

        if not namespace or retrieval_mode == 'auto':
            # 自动分类 - 开始计时
            classification_start_time = time.time()

            classifier = get_classifier(
                db=db,
                classifier_type='hybrid'  # 使用混合分类器
            )

            classification_result = await classifier.classify(
                query=request.query,
                context={
                    'user_id': current_user.id,
                    'session_id': request.session_id
                }
            )

            # 记录分类耗时
            classification_latency_ms = (time.time() - classification_start_time) * 1000
            performance_data['classification_latency_ms'] = classification_latency_ms
            logger.info(f"分类耗时: {classification_latency_ms:.2f}ms")

            # 记录分类指标
            record_classification_metrics(
                method='hybrid',
                namespace=classification_result.namespace,
                latency=classification_latency_ms / 1000  # 转换为秒
            )

            namespace = classification_result.namespace

            # 判断是否需要跨领域检索
            if classification_result.fallback_to_cross_domain:
                retrieval_mode = 'cross'
                logger.info(f"低置信度({classification_result.confidence:.2f}),切换到跨领域检索")
            else:
                retrieval_mode = 'single'

        # === 步骤 2: 执行检索 ===
        retrieval_start_time = time.time()

        if retrieval_mode == 'single':
            # 单领域检索
            results = await _single_domain_retrieval(
                query=request.query,
                namespace=namespace,
                top_k=request.top_k,
                method=request.retrieval_method,
                alpha=request.alpha,
                similarity_threshold=request.similarity_threshold,
                db=db
            )

            # 转换为ChunkResult格式
            chunk_results = [
                await _chunk_to_result(chunk, namespace, db)
                for chunk in results
            ]

        elif retrieval_mode == 'cross':
            # 跨领域检索
            logger.info(f"执行跨领域检索: namespaces={request.namespaces}")

            results_with_namespace = await _cross_domain_retrieval(
                query=request.query,
                classification_result=classification_result,
                namespaces=request.namespaces,
                top_k=request.top_k,
                alpha=request.alpha,
                db=db
            )

            # 转换为ChunkResult并获取分组结果
            chunk_results = []
            for chunk, ns, score in results_with_namespace:
                result = await _chunk_to_result(chunk, ns, db)
                # 使用跨领域得分
                result.score = score
                chunk_results.append(result)

            # 按领域分组用于前端展示
            cross_domain_service = get_cross_domain_retrieval(db)
            grouped = cross_domain_service.group_results_by_domain(results_with_namespace)

            # 构建分组响应
            from app.schemas.query import DomainGroup
            domain_groups = []

            for ns, chunks in grouped.items():
                domain = db.query(KnowledgeDomain).filter(
                    KnowledgeDomain.namespace == ns
                ).first()

                # 为该领域的结果创建ChunkResult列表
                group_results = []
                for chunk in chunks[:3]:  # 每个领域显示前3个
                    result = await _chunk_to_result(chunk, ns, db)
                    result.score = chunk.get('cross_domain_score', 0.0)
                    group_results.append(result)

                domain_groups.append(DomainGroup(
                    namespace=ns,
                    display_name=domain.display_name if domain else ns,
                    count=len(chunks),
                    results=group_results
                ))

            # 按结果数量排序
            domain_groups.sort(key=lambda x: x.count, reverse=True)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"未知的检索模式: {retrieval_mode}"
            )

        # === 步骤 3: 构建响应 ===
        latency_ms = (time.time() - start_time) * 1000
        retrieval_latency_ms = (time.time() - retrieval_start_time) * 1000 if retrieval_start_time else 0
        performance_data['total_latency_ms'] = latency_ms
        performance_data['retrieval_latency_ms'] = retrieval_latency_ms

        # 记录查询指标
        record_query_metrics(
            namespace=namespace,
            retrieval_mode=retrieval_mode,
            latency=latency_ms / 1000,  # 转换为秒
            status='success'
        )

        # 记录检索结果数量
        record_retrieval_results(
            namespace=namespace,
            retrieval_type=request.retrieval_method or 'hybrid',
            count=len(chunk_results)
        )

        # 构建结果统计
        domains_searched = [namespace]
        if retrieval_mode == 'cross' and domain_groups:
            domains_searched = [group.namespace for group in domain_groups]

        result_data = {
            'total_candidates': len(chunk_results),
            'filtered_results': len(chunk_results),
            'vector_results': len(chunk_results) if request.retrieval_method in ['vector', 'hybrid'] else 0,
            'bm25_results': len(chunk_results) if request.retrieval_method in ['bm25', 'hybrid'] else 0,
            'primary_domain': namespace,
            'cross_domain_enabled': retrieval_mode == 'cross',
            'domains_searched': domains_searched
        }

        # 记录性能日志
        try:
            perf_logger.log_query(
                query=request.query,
                retrieval_mode=retrieval_mode,
                retrieval_method=request.retrieval_method or 'hybrid',
                performance_data=performance_data,
                result_data=result_data,
                session_id=request.session_id,
                error=None
            )
        except Exception as e:
            logger.warning(f"记录性能日志失败: {e}")

        response = QueryResponseV2(
            query_id=str(uuid.uuid4()),
            query=request.query,
            domain_classification=classification_result.to_dict() if classification_result else None,
            retrieval_mode=retrieval_mode,
            retrieval_method=request.retrieval_method or 'hybrid',
            results=chunk_results,
            cross_domain_results=domain_groups if retrieval_mode == 'cross' else None,
            retrieval_stats=RetrievalStats(
                total_candidates=len(chunk_results),
                method=request.retrieval_method or 'hybrid',
                latency_ms=latency_ms,
                bm25_count=len(chunk_results) if request.retrieval_method in ['bm25', 'hybrid'] else 0,
                vector_count=len(chunk_results) if request.retrieval_method in ['vector', 'hybrid'] else 0
            )
        )

        logger.info(f"查询完成: {len(chunk_results)} 结果, 耗时 {latency_ms:.2f}ms")
        return response

    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # 记录错误指标
        try:
            error_latency_ms = (time.time() - start_time) * 1000
            record_query_metrics(
                namespace=namespace if namespace else 'unknown',
                retrieval_mode=retrieval_mode if 'retrieval_mode' in locals() else 'auto',
                latency=error_latency_ms / 1000,
                status='failure',
                error_type=type(e).__name__
            )
        except Exception as metric_error:
            logger.warning(f"记录错误指标失败: {metric_error}")

        # 记录错误性能日志
        try:
            error_performance_data = {**performance_data, 'total_latency_ms': error_latency_ms}

            perf_logger.log_query(
                query=request.query,
                retrieval_mode=request.retrieval_mode or 'auto',
                retrieval_method=request.retrieval_method or 'hybrid',
                performance_data=error_performance_data,
                result_data={},
                session_id=request.session_id,
                error=str(e)
            )
        except Exception as log_error:
            logger.warning(f"记录错误性能日志失败: {log_error}")

        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


async def _cross_domain_retrieval(
    query: str,
    classification_result: Optional[Any],
    namespaces: Optional[List[str]],
    top_k: int,
    alpha: float,
    db: Session
) -> List[Tuple[Dict[str, Any], str, float]]:
    """
    跨领域检索

    Args:
        query: 查询文本
        classification_result: 分类结果(用于权重计算)
        namespaces: 指定领域列表
        top_k: 返回结果数
        alpha: 混合检索权重
        db: 数据库会话

    Returns:
        (chunk, namespace, score) 元组列表
    """
    cross_domain_service = get_cross_domain_retrieval(db)

    if classification_result:
        # 基于分类结果进行智能跨领域检索
        results, weights = await cross_domain_service.search_with_classification(
            query=query,
            classification_result=classification_result,
            top_k=top_k,
            alpha=alpha,
            include_all_domains=(namespaces is None)
        )
        logger.info(f"使用分类权重: {weights}")
    else:
        # 普通跨领域检索(无权重)
        results = await cross_domain_service.search_across_domains(
            query=query,
            namespaces=namespaces,
            top_k=top_k,
            alpha=alpha
        )

    return results


async def _single_domain_retrieval(
    query: str,
    namespace: str,
    top_k: int,
    method: str,
    alpha: float,
    similarity_threshold: float,
    db: Session
) -> List[Dict[str, Any]]:
    """
    单领域检索

    Args:
        query: 查询文本
        namespace: 领域命名空间
        top_k: 返回结果数
        method: 检索方法(vector/bm25/hybrid)
        alpha: 混合检索权重
        similarity_threshold: 相似度阈值
        db: 数据库会话

    Returns:
        检索结果列表
    """
    if method == 'vector':
        # 纯向量检索
        return await vector_retrieval_service.search_by_namespace(
            db=db,
            query_text=query,
            namespace=namespace,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

    elif method == 'bm25':
        # 纯BM25检索
        bm25_service = get_bm25_service(db)
        results = await bm25_service.search_by_namespace(
            query=query,
            namespace=namespace,
            top_k=top_k
        )
        # 转换格式(去掉score元组)
        return [chunk for chunk, score in results]

    elif method == 'hybrid':
        # 混合检索
        hybrid_service = get_hybrid_retrieval(db)
        return await hybrid_service.search_by_namespace(
            query=query,
            namespace=namespace,
            top_k=top_k,
            alpha=alpha
        )

    else:
        raise ValueError(f"未知的检索方法: {method}")


async def _chunk_to_result(
    chunk: Dict[str, Any],
    namespace: str,
    db: Session
) -> ChunkResult:
    """
    将文档块转换为ChunkResult格式

    Args:
        chunk: 文档块字典
        namespace: 领域命名空间
        db: 数据库会话

    Returns:
        ChunkResult对象
    """
    # 获取领域信息
    domain = db.query(KnowledgeDomain).filter(
        KnowledgeDomain.namespace == namespace
    ).first()

    return ChunkResult(
        chunk_id=chunk['id'],
        content=chunk['content'],
        score=chunk.get('similarity', chunk.get('fusion_score', 0.0)),
        namespace=namespace,
        domain_display_name=domain.display_name if domain else namespace,
        domain_color=domain.color if domain else '#999999',
        domain_icon=domain.icon if domain else 'folder',
        document_id=chunk['document_id'],
        document_title=chunk.get('filename', '未知文档'),
        chunk_index=chunk.get('chunk_index'),
        metadata=_parse_metadata(chunk.get('metadata'))
    )


def _parse_metadata(metadata_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    解析元数据字符串为字典

    Args:
        metadata_str: JSON字符串格式的元数据

    Returns:
        解析后的字典，如果解析失败返回空字典
    """
    if not metadata_str:
        return None

    # 如果已经是字典,直接返回
    if isinstance(metadata_str, dict):
        return metadata_str

    # 如果是 SQLAlchemy MetaData 对象,返回空字典
    # MetaData 类型没有 __module__ 属性,所以用类型名判断
    if type(metadata_str).__name__ == 'MetaData':
        logger.warning(f"收到 SQLAlchemy MetaData 对象,返回空字典")
        return {}

    # 如果是字符串,尝试解析 JSON
    if isinstance(metadata_str, str):
        try:
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            logger.warning(f"无法解析元数据 JSON: {metadata_str[:100] if len(metadata_str) > 100 else metadata_str}")
            return {}

    # 其他类型,记录警告并返回空字典
    logger.warning(f"未知的元数据类型: {type(metadata_str).__name__}")
    return {}


@router.get("/query/methods", summary="获取支持的检索方法")
async def get_retrieval_methods():
    """
    获取所有支持的检索方法及说明
    """
    return {
        "success": True,
        "data": {
            "retrieval_methods": [
                {
                    "method": "vector",
                    "name": "向量检索",
                    "description": "基于语义相似度的检索",
                    "pros": ["理解语义", "支持同义词", "跨语言"],
                    "cons": ["依赖embedding质量", "计算成本较高"],
                    "use_cases": ["语义查询", "模糊查询"]
                },
                {
                    "method": "bm25",
                    "name": "关键词检索",
                    "description": "基于BM25算法的关键词匹配",
                    "pros": ["精确匹配", "速度快", "可解释性强"],
                    "cons": ["无法理解语义", "对同义词不敏感"],
                    "use_cases": ["精确查询", "关键词搜索"]
                },
                {
                    "method": "hybrid",
                    "name": "混合检索",
                    "description": "结合向量和BM25的混合检索(推荐)",
                    "pros": ["准确度最高", "兼顾语义和关键词", "鲁棒性强"],
                    "cons": ["计算成本略高"],
                    "use_cases": ["通用场景(推荐默认使用)"]
                }
            ],
            "retrieval_modes": [
                {
                    "mode": "auto",
                    "name": "自动模式",
                    "description": "自动识别领域并选择检索策略"
                },
                {
                    "mode": "single",
                    "name": "单领域模式",
                    "description": "在指定领域内精确检索"
                },
                {
                    "mode": "cross",
                    "name": "跨领域模式",
                    "description": "在多个领域中检索并融合结果"
                }
            ]
        }
    }


@router.get("/query/test", summary="测试查询功能")
async def test_query(
    query: str = "如何配置API",
    namespace: Optional[str] = None,
    method: str = "hybrid",
    db: Session = Depends(get_db)
):
    """
    快速测试查询功能
    """
    try:
        request = QueryRequestV2(
            query=query,
            namespace=namespace,
            retrieval_mode='single' if namespace else 'auto',
            retrieval_method=method,
            top_k=5
        )

        # 创建临时用户对象(测试用)
        class TempUser:
            id = 1
            username = "test"

        # 模拟查询
        results = await _single_domain_retrieval(
            query=query,
            namespace=namespace or 'default',
            top_k=5,
            method=method,
            alpha=0.5,
            similarity_threshold=0.0,
            db=db
        )

        return {
            "success": True,
            "query": query,
            "namespace": namespace,
            "method": method,
            "result_count": len(results),
            "results": results[:3]  # 只返回前3个结果
        }

    except Exception as e:
        logger.error(f"测试查询失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
