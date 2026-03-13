"""
领域分类 API

提供智能领域分类功能的 REST API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.domain_classifier import get_classifier, DomainClassificationResult
from app.services.llm_service import LLMService
from app.middleware.auth import AuthMiddleware

router = APIRouter()


# ==================== Request/Response Models ====================

class ClassifyQueryRequest(BaseModel):
    """分类查询请求"""
    query: str = Field(..., description="用户查询文本", min_length=1, max_length=1000)
    context: Optional[dict] = Field(default=None, description="上下文信息(如用户ID、会话ID等)")
    classifier_type: str = Field(default='hybrid', description="分类器类型: keyword, llm, hybrid")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "如何配置API密钥?",
                "context": {"user_id": "user123", "session_id": "session456"},
                "classifier_type": "hybrid"
            }
        }


class ClassifyQueryResponse(BaseModel):
    """分类查询响应"""
    success: bool = Field(description="是否分类成功")
    result: dict = Field(description="分类结果")
    message: str = Field(default="", description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": {
                    "namespace": "technical_docs",
                    "display_name": "技术文档",
                    "confidence": 0.85,
                    "method": "hybrid",
                    "reasoning": "匹配到关键词: API, 配置",
                    "alternatives": [
                        {"namespace": "default", "display_name": "默认知识库", "confidence": 0.3}
                    ],
                    "fallback_to_cross_domain": False,
                    "metadata": {
                        "strategy": "keyword_only",
                        "matched_keywords": ["API", "配置"]
                    }
                },
                "message": "分类完成"
            }
        }


class BatchClassifyRequest(BaseModel):
    """批量分类请求"""
    queries: list[str] = Field(..., description="查询文本列表", min_length=1, max_length=50)
    classifier_type: str = Field(default='keyword', description="分类器类型 (批量建议使用keyword)")

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    "如何退货?",
                    "API文档在哪里?",
                    "保修期多长?"
                ],
                "classifier_type": "keyword"
            }
        }


class BatchClassifyResponse(BaseModel):
    """批量分类响应"""
    success: bool
    results: list[dict]
    message: str = ""


# ==================== API Endpoints ====================

@router.post(
    "/classify-query",
    response_model=ClassifyQueryResponse,
    summary="分类单个查询",
    description="根据用户查询自动识别所属知识领域"
)
async def classify_query(
    request: ClassifyQueryRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(AuthMiddleware.check_permission("query_ask"))
):
    """
    对单个查询进行领域分类

    支持三种分类器:
    - keyword: 基于关键词的快速分类(推荐用于实时查询)
    - llm: 基于大模型的智能分类(更准确但较慢)
    - hybrid: 混合分类(综合两者优势,默认推荐)

    Returns:
        ClassifyQueryResponse: 分类结果,包含领域、置信度、推理过程等
    """
    try:
        # 验证分类器类型
        if request.classifier_type not in ['keyword', 'llm', 'hybrid']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的分类器类型: {request.classifier_type}, 必须是 keyword, llm 或 hybrid"
            )

        # 获取分类器
        llm_service = LLMService(db=db) if request.classifier_type in ['llm', 'hybrid'] else None
        classifier = get_classifier(
            db=db,
            classifier_type=request.classifier_type,
            llm_service=llm_service
        )

        # 执行分类
        result = await classifier.classify(
            query=request.query,
            context=request.context
        )

        return ClassifyQueryResponse(
            success=True,
            result=result.to_dict(),
            message="分类完成"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分类失败: {str(e)}"
        )


@router.post(
    "/classify-batch",
    response_model=BatchClassifyResponse,
    summary="批量分类查询",
    description="对多个查询进行批量领域分类"
)
async def classify_batch(
    request: BatchClassifyRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(AuthMiddleware.check_permission("query_ask"))
):
    """
    批量对多个查询进行领域分类

    Note:
        - 批量分类建议使用 keyword 分类器以提升性能
        - 最多支持一次处理 50 个查询
        - 每个查询独立分类,互不影响

    Returns:
        BatchClassifyResponse: 每个查询的分类结果列表
    """
    try:
        # 验证分类器类型
        if request.classifier_type not in ['keyword', 'llm', 'hybrid']:
            raise HTTPException(
                status_code=400,
                detail=f"无效的分类器类型: {request.classifier_type}"
            )

        # 获取分类器
        llm_service = LLMService(db=db ) if request.classifier_type in ['llm', 'hybrid'] else None
        classifier = get_classifier(
            db=db,
            classifier_type=request.classifier_type,
            llm_service=llm_service
        )

        # 批量分类
        results = []
        for query in request.queries:
            try:
                result = await classifier.classify(query=query, context=None)
                results.append({
                    "query": query,
                    "success": True,
                    "result": result.to_dict()
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })

        return BatchClassifyResponse(
            success=True,
            results=results,
            message=f"批量分类完成,共 {len(results)} 个查询"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量分类失败: {str(e)}"
        )


@router.get(
    "/classifier-types",
    summary="获取分类器类型列表",
    description="获取所有支持的分类器类型及说明"
)
async def get_classifier_types():
    """
    获取支持的分类器类型

    Returns:
        dict: 分类器类型列表及其说明
    """
    return {
        "success": True,
        "data": {
            "classifier_types": [
                {
                    "type": "keyword",
                    "name": "关键词分类器",
                    "description": "基于规则和关键词匹配的快速分类",
                    "pros": ["速度快", "无需LLM调用", "成本低"],
                    "cons": ["准确度相对较低", "依赖关键词配置"],
                    "use_cases": ["实时查询", "批量分类", "快速响应场景"]
                },
                {
                    "type": "llm",
                    "name": "LLM分类器",
                    "description": "基于大语言模型的智能分类",
                    "pros": ["准确度高", "理解上下文", "灵活性强"],
                    "cons": ["速度较慢", "需要LLM调用", "成本较高"],
                    "use_cases": ["复杂查询", "准确性要求高的场景"]
                },
                {
                    "type": "hybrid",
                    "name": "混合分类器",
                    "description": "结合关键词和LLM的混合策略",
                    "pros": ["平衡速度和准确度", "智能降级", "灵活适应"],
                    "cons": ["逻辑较复杂"],
                    "use_cases": ["通用场景", "推荐默认使用"]
                }
            ]
        },
        "message": "获取分类器类型成功"
    }


@router.get(
    "/test-classification",
    summary="测试分类功能",
    description="使用预设查询测试分类器"
)
async def test_classification(
    query: str = Query(default="如何配置API密钥?", description="测试查询"),
    classifier_type: str = Query(default="hybrid", description="分类器类型"),
    db: Session = Depends(get_db)
):
    """
    测试分类功能的简单端点

    Args:
        query: 测试查询文本
        classifier_type: 分类器类型

    Returns:
        dict: 分类结果
    """
    try:
        llm_service = LLMService(db=db) if classifier_type in ['llm', 'hybrid'] else None
        classifier = get_classifier(
            db=db,
            classifier_type=classifier_type,
            llm_service=llm_service
        )

        result = await classifier.classify(query=query, context=None)

        return {
            "success": True,
            "query": query,
            "classifier_type": classifier_type,
            "result": result.to_dict()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
