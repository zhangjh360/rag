"""
改进的查询路由
解决当前查询接口的性能和上下文截断问题
"""

from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from sqlalchemy.orm import Session
from database import get_db
from app.services.embedding import embedding_service
from app.services.advanced_retrieval import advanced_retrieval_service
from app.services.generation import generation_service
from app.models.database import Query
from app.models.schemas import QueryRequest, QueryResponse
from app.config.logging_config import get_app_logger
import json
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()
logger = get_app_logger()

class AdvancedQueryRequest(BaseModel):
    """高级查询请求模型"""
    query: str
    use_chunks: bool = True  # 是否使用文档块检索
    max_context_length: int = 4000  # 最大上下文长度
    top_k: int = 10  # 返回的文档数量
    include_similarity: bool = True  # 是否包含相似度信息

class AdvancedQueryResponse(BaseModel):
    """高级查询响应模型"""
    response: str
    sources: List[dict]
    context_length: int
    retrieval_method: str
    processing_time: float

@router.post("/advanced-query", response_model=AdvancedQueryResponse)
async def advanced_query_documents(
    request: AdvancedQueryRequest, 
    db: Session = Depends(get_db)
):
    """处理高级文档查询请求"""
    import time
    start_time = time.time()
    
    try:
        logger.info(f"开始处理高级查询: {request.query[:50]}...")
        
        # 根据配置选择检索方法
        if request.use_chunks:
            # 使用文档块检索
            retrieved_items = await advanced_retrieval_service.retrieve_relevant_chunks(
                db, request.query, request.top_k
            )
            context = advanced_retrieval_service.format_context_with_chunks(
                retrieved_items, request.query
            )
            retrieval_method = "chunk_based"
        else:
            # 使用传统文档检索
            retrieved_items = await advanced_retrieval_service.retrieve_documents(
                db, request.query, request.top_k
            )
            context = advanced_retrieval_service.smart_format_context(
                retrieved_items, request.query
            )
            retrieval_method = "document_based"
        
        if not retrieved_items:
            processing_time = time.time() - start_time
            return AdvancedQueryResponse(
                response="未找到相关文档信息",
                sources=[],
                context_length=0,
                retrieval_method=retrieval_method,
                processing_time=processing_time
            )
        
        # 生成回答
        response = await generation_service.generate_response(request.query, context)
        
        # 保存查询历史
        query_record = Query(
            query_text=request.query,
            response=response,
            sources=json.dumps(retrieved_items),
            created_at=str(datetime.now())
        )
        db.add(query_record)
        db.commit()
        
        # 准备返回的源文档信息
        sources = []
        for item in retrieved_items:
            source_info = {
                "id": item.get("id", item.get("doc_id")),
                "filename": item["filename"],
                "content_preview": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"]
            }
            
            if request.include_similarity and "similarity" in item:
                source_info["similarity"] = item["similarity"]
            
            if "chunk_index" in item:
                source_info["chunk_index"] = item["chunk_index"]
                source_info["is_chunk"] = True
            else:
                source_info["is_chunk"] = False
            
            sources.append(source_info)
        
        processing_time = time.time() - start_time
        
        logger.info(f"高级查询完成，处理时间: {processing_time:.3f}s，上下文长度: {len(context)}")
        
        return AdvancedQueryResponse(
            response=response,
            sources=sources,
            context_length=len(context),
            retrieval_method=retrieval_method,
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"高级查询处理失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"高级查询处理失败: {str(e)}"
        )

@router.post("/query-with-chunks", response_model=QueryResponse)
async def query_with_chunks(
    request: QueryRequest, 
    db: Session = Depends(get_db)
):
    """使用文档块进行查询（简化版本）"""
    try:
        logger.info(f"开始文档块查询: {request.query[:50]}...")
        
        # 使用文档块检索
        retrieved_chunks = await advanced_retrieval_service.retrieve_relevant_chunks(
            db, request.query, 15  # 获取更多块
        )
        
        if not retrieved_chunks:
            return QueryResponse(
                response="未找到相关文档信息",
                sources=[]
            )
        
        # 格式化上下文
        context = advanced_retrieval_service.format_context_with_chunks(
            retrieved_chunks, request.query
        )
        
        # 生成回答
        response = await generation_service.generate_response(request.query, context)
        
        # 保存查询历史
        query_record = Query(
            query_text=request.query,
            response=response,
            sources=json.dumps(retrieved_chunks),
            created_at=str(datetime.now())
        )
        db.add(query_record)
        db.commit()
        
        # 准备返回的源文档信息
        sources = []
        for chunk in retrieved_chunks:
            sources.append({
                "id": chunk["id"],
                "filename": chunk["filename"],
                "similarity": chunk["similarity"],
                "chunk_index": chunk["chunk_index"],
                "content_preview": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
            })
        
        return QueryResponse(
            response=response,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"文档块查询失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"文档块查询失败: {str(e)}"
        )

@router.get("/query/performance")
async def get_query_performance(db: Session = Depends(get_db)):
    """获取查询性能统计"""
    try:
        # 获取最近的查询记录
        recent_queries = db.query(Query).order_by(Query.created_at.desc()).limit(100).all()
        
        if not recent_queries:
            return {"message": "暂无查询记录"}
        
        # 分析查询性能
        total_queries = len(recent_queries)
        avg_response_length = sum(len(q.response) for q in recent_queries) / total_queries
        
        # 分析源文档数量
        source_counts = []
        for query in recent_queries:
            if query.sources:
                try:
                    sources = json.loads(query.sources)
                    source_counts.append(len(sources))
                except:
                    source_counts.append(0)
        
        avg_sources = sum(source_counts) / len(source_counts) if source_counts else 0
        
        return {
            "total_queries": total_queries,
            "avg_response_length": round(avg_response_length, 2),
            "avg_sources_per_query": round(avg_sources, 2),
            "recent_queries": [
                {
                    "id": q.id,
                    "query": q.query_text[:50] + "..." if len(q.query_text) > 50 else q.query_text,
                    "response_length": len(q.response),
                    "sources_count": len(json.loads(q.sources)) if q.sources else 0,
                    "created_at": q.created_at
                }
                for q in recent_queries[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"获取查询性能统计失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"获取查询性能统计失败: {str(e)}"
        )

@router.post("/query/optimize")
async def optimize_query_context(
    request: QueryRequest,
    max_length: int = QueryParam(4000, description="最大上下文长度"),
    db: Session = Depends(get_db)
):
    """优化查询上下文"""
    try:
        logger.info(f"开始优化查询上下文: {request.query[:50]}...")
        
        # 获取相关文档
        retrieved_docs = await advanced_retrieval_service.retrieve_documents(
            db, request.query, 20
        )
        
        if not retrieved_docs:
            return {"message": "未找到相关文档"}
        
        # 使用智能格式化
        context = advanced_retrieval_service.smart_format_context(
            retrieved_docs, request.query
        )
        
        # 如果上下文仍然太长，进一步优化
        if len(context) > max_length:
            # 按相似度排序，只保留最相关的部分
            sorted_docs = sorted(retrieved_docs, key=lambda x: x['similarity'], reverse=True)
            
            optimized_context = ""
            current_length = 0
            
            for doc in sorted_docs:
                doc_content = f"文档: {doc['filename']}\n{doc['content'][:500]}...\n\n"
                
                if current_length + len(doc_content) <= max_length:
                    optimized_context += doc_content
                    current_length += len(doc_content)
                else:
                    break
            
            context = optimized_context
        
        return {
            "original_length": sum(len(doc['content']) for doc in retrieved_docs),
            "optimized_length": len(context),
            "compression_ratio": round(len(context) / sum(len(doc['content']) for doc in retrieved_docs), 3),
            "context": context,
            "sources_count": len(retrieved_docs)
        }
        
    except Exception as e:
        logger.error(f"优化查询上下文失败: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"优化查询上下文失败: {str(e)}"
        )
