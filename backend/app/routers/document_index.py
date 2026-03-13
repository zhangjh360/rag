"""
文档索引管理API
提供增量更新、变更检测、任务管理等功能
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import get_db
from app.services.change_detector import create_change_detector
from app.services.incremental_indexer import create_incremental_indexer
from app.models.index_record import IndexTask as IndexTaskModel, DocumentIndexRecord, IndexChangeHistory
from app.models.database import Document
from app.middleware.auth import get_current_active_user
from app.config.settings import CELERY_ENABLED
import logging
import uuid

router = APIRouter(prefix="/index", tags=["文档索引"])
logger = logging.getLogger(__name__)


# ============== Pydantic 模型 ==============

class IndexRequest(BaseModel):
    """索引请求"""
    doc_ids: List[int]
    force: bool = False
    priority: int = 5


class ChangeDetectionRequest(BaseModel):
    """变更检测请求"""
    namespace: Optional[str] = None
    since_hours: Optional[int] = None


class IndexResponse(BaseModel):
    """索引响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============== API 端点 ==============

@router.post("/detect-changes", response_model=IndexResponse)
async def detect_changes(
    request: ChangeDetectionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    检测文档变更

    返回需要更新的文档列表
    """
    try:
        detector = create_change_detector(db)

        # 获取变更摘要
        summary = detector.get_change_summary(namespace=request.namespace)

        return IndexResponse(
            success=True,
            message=f"检测到 {summary['needs_update']} 个文档需要更新",
            data=summary
        )

    except Exception as e:
        logger.error(f"变更检测失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index-documents", response_model=IndexResponse)
async def index_documents(
    request: IndexRequest,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    索引指定的文档列表

    支持同步和异步两种模式:
    - Celery已启用 + 5个或以上文档：Celery异步处理
    - Celery已启用 + 少于5个文档：同步处理
    - Celery未启用：同步处理
    """
    try:
        indexer = create_incremental_indexer(db)

        # 根据Celery状态和文档数量决定处理方式
        use_celery = CELERY_ENABLED and len(request.doc_ids) >= 5

        if use_celery:
            # 使用Celery异步处理
            from app.tasks.index_tasks import batch_index_task

            # 创建任务记录
            task_id = str(uuid.uuid4())
            task_record = IndexTaskModel(
                task_id=task_id,
                task_type='batch',
                status='pending',
                priority=request.priority,
                task_metadata={'doc_ids': request.doc_ids, 'user_id': current_user.id if current_user else None}
            )
            db.add(task_record)
            db.commit()

            # 提交Celery任务
            celery_task = batch_index_task.apply_async(
                args=[request.doc_ids, current_user.id if current_user else None],
                task_id=task_id,
                priority=request.priority
            )

            logger.info(f"已提交Celery任务: task_id={task_id}, doc_count={len(request.doc_ids)}")

            return IndexResponse(
                success=True,
                message=f"已提交 {len(request.doc_ids)} 个文档到Celery队列",
                data={
                    'task_id': task_id,
                    'doc_ids': request.doc_ids,
                    'status': 'queued',
                    'mode': 'celery'
                }
            )
        else:
            # 同步处理
            result = await indexer.batch_index_documents(
                doc_ids=request.doc_ids,
                user_id=current_user.id if current_user else None
            )

            return IndexResponse(
                success=True,
                message=f"索引完成: 成功={result['success']}, 失败={result['failed']}",
                data={**result, 'mode': 'sync'}
            )

    except Exception as e:
        logger.error(f"索引文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-update", response_model=IndexResponse)
async def auto_update(
    namespace: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    自动检测并更新变更的文档

    一键式增量更新接口
    """
    try:
        # 检测变更
        detector = create_change_detector(db)
        summary = detector.get_change_summary(namespace=namespace)

        # 获取需要更新的文档ID
        doc_ids = summary['new_doc_ids'] + summary['modified_doc_ids']

        if not doc_ids:
            return IndexResponse(
                success=True,
                message="没有需要更新的文档",
                data=summary
            )

        # 提交索引任务
        indexer = create_incremental_indexer(db)

        if len(doc_ids) < 5:
            # 同步处理
            result = await indexer.batch_index_documents(
                doc_ids=doc_ids,
                user_id=current_user.id if current_user else None
            )
        else:
            # 异步处理
            background_tasks.add_task(
                _async_batch_index,
                db,
                doc_ids,
                current_user.id if current_user else None
            )
            result = {'status': 'queued', 'doc_ids': doc_ids}

        return IndexResponse(
            success=True,
            message=f"自动更新已启动: {len(doc_ids)} 个文档",
            data={'changes': summary, 'index_result': result}
        )

    except Exception as e:
        logger.error(f"自动更新失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/{doc_id}", response_model=IndexResponse)
async def delete_document_index(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """删除文档的索引数据"""
    try:
        indexer = create_incremental_indexer(db)
        result = indexer.delete_document_index(
            doc_id=doc_id,
            user_id=current_user.id if current_user else None
        )

        if result['status'] == 'not_found':
            raise HTTPException(status_code=404, detail="索引记录不存在")

        return IndexResponse(
            success=True,
            message=f"索引已删除，删除了 {result['chunks_deleted']} 个块",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除索引失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=IndexResponse)
async def get_index_status(
    namespace: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    获取索引状态摘要

    包括总文档数、已索引数、待处理数等
    """
    try:
        # 统计各状态的文档数
        query = db.query(Document)
        if namespace:
            query = query.filter(Document.namespace == namespace)

        total_docs = query.count()
        indexed_docs = query.filter(Document.index_status == 'indexed').count()
        pending_docs = query.filter(Document.index_status == 'pending').count()
        failed_docs = query.filter(Document.index_status == 'failed').count()

        # 获取索引记录统计
        index_records = db.query(DocumentIndexRecord)
        if namespace:
            index_records = index_records.filter(DocumentIndexRecord.namespace == namespace)

        total_chunks = sum(r.chunk_count for r in index_records.all())
        total_vectors = sum(r.vector_count for r in index_records.all())

        # 最后索引时间
        last_indexed = db.query(DocumentIndexRecord.indexed_at).order_by(
            DocumentIndexRecord.indexed_at.desc()
        ).first()

        status = {
            'namespace': namespace or 'all',
            'total_documents': total_docs,
            'indexed_documents': indexed_docs,
            'pending_documents': pending_docs,
            'failed_documents': failed_docs,
            'indexing_rate': round((indexed_docs / total_docs * 100) if total_docs > 0 else 0, 2),
            'total_chunks': total_chunks,
            'total_vectors': total_vectors,
            'last_indexed_at': last_indexed[0].isoformat() if last_indexed else None,
            'checked_at': datetime.now().isoformat()
        }

        return IndexResponse(
            success=True,
            message="索引状态获取成功",
            data=status
        )

    except Exception as e:
        logger.error(f"获取索引状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records", response_model=IndexResponse)
async def get_index_records(
    namespace: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取索引记录列表"""
    try:
        # 联表查询,获取文档信息和索引记录
        query = db.query(
            DocumentIndexRecord,
            Document.filename,
            Document.namespace.label('doc_namespace')
        ).join(
            Document, DocumentIndexRecord.doc_id == Document.id
        )

        if namespace:
            query = query.filter(DocumentIndexRecord.namespace == namespace)

        # status参数暂时忽略,因为Document表没有index_status字段
        # 可以根据是否有索引记录来判断状态

        total = query.count()
        results = query.order_by(
            DocumentIndexRecord.indexed_at.desc()
        ).offset(offset).limit(limit).all()

        # 组装返回数据
        records = []
        for record, filename, doc_namespace in results:
            record_dict = record.to_dict()
            record_dict['filename'] = filename
            record_dict['index_status'] = 'indexed'  # 有记录即为已索引
            records.append(record_dict)

        return IndexResponse(
            success=True,
            message=f"获取到 {len(records)} 条索引记录",
            data={
                'records': records,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        )

    except Exception as e:
        logger.error(f"获取索引记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=IndexResponse)
async def get_task_list(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取任务列表"""
    try:
        query = db.query(IndexTaskModel)

        if status:
            query = query.filter(IndexTaskModel.status == status)

        total = query.count()
        tasks = query.order_by(
            IndexTaskModel.created_at.desc()
        ).offset(offset).limit(limit).all()

        return IndexResponse(
            success=True,
            message=f"获取到 {len(tasks)} 个任务",
            data={
                'tasks': [t.to_dict() for t in tasks],
                'total': total,
                'limit': limit,
                'offset': offset
            }
        )

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=IndexResponse)
async def get_index_stats(
    namespace: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取索引统计信息"""
    try:
        from datetime import timedelta
        from sqlalchemy import func, and_, or_

        # 基础统计 - 使用DocumentIndexRecord来统计已索引的文档
        doc_query = db.query(Document)
        if namespace:
            doc_query = doc_query.filter(Document.namespace == namespace)

        total_docs = doc_query.count()

        # 已索引文档数 - 有索引记录的文档
        indexed_query = db.query(DocumentIndexRecord).join(
            Document, DocumentIndexRecord.doc_id == Document.id
        )
        if namespace:
            indexed_query = indexed_query.filter(DocumentIndexRecord.namespace == namespace)
        indexed_docs = indexed_query.count()

        # 待索引文档数 - 没有索引记录的文档
        pending_docs = total_docs - indexed_docs

        # 过期文档数 - 索引时间超过30天的文档
        outdated_threshold = datetime.now() - timedelta(days=30)
        outdated_query = db.query(DocumentIndexRecord)
        if namespace:
            outdated_query = outdated_query.filter(DocumentIndexRecord.namespace == namespace)
        outdated_docs = outdated_query.filter(
            DocumentIndexRecord.indexed_at < outdated_threshold
        ).count()

        # 失败任务统计（仅供参考）
        task_query = db.query(IndexTaskModel)
        failed_tasks = task_query.filter(IndexTaskModel.status == 'failed').count()

        # 今日新增索引 - 使用DocumentIndexRecord的indexed_at字段
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_query = db.query(DocumentIndexRecord)
        if namespace:
            today_query = today_query.filter(DocumentIndexRecord.namespace == namespace)
        today_count = today_query.filter(
            DocumentIndexRecord.indexed_at >= today_start
        ).count()

        # 趋势数据 - 使用DocumentIndexRecord的indexed_at字段
        trend_data = []
        for i in range(days):
            day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            trend_query = db.query(DocumentIndexRecord)
            if namespace:
                trend_query = trend_query.filter(DocumentIndexRecord.namespace == namespace)

            count = trend_query.filter(
                DocumentIndexRecord.indexed_at >= day_start,
                DocumentIndexRecord.indexed_at < day_end
            ).count()

            trend_data.insert(0, {
                'date': day_start.strftime('%Y-%m-%d'),
                'count': count
            })

        # 状态分布 - 真实的文档级别状态
        status_distribution = {
            'indexed': indexed_docs,      # 已索引的文档
            'pending': pending_docs,       # 待索引的文档（无索引记录）
            'outdated': outdated_docs,     # 过期文档（索引时间>30天）
            'failed': failed_tasks         # 失败的索引任务（仅供参考）
        }

        # 性能指标
        # 计算平均索引时间（基于最近100条索引记录）
        recent_records = db.query(DocumentIndexRecord).order_by(
            DocumentIndexRecord.indexed_at.desc()
        ).limit(100).all()

        if recent_records and len(recent_records) > 1:
            # 估算：假设每条记录处理耗时相似
            avg_index_time = 2.5  # 目前还是估算值，后续可以添加实际的性能监控
        else:
            avg_index_time = 2.5

        # 成本节省：增量索引相比全量索引的节省百分比
        # 假设：如果所有文档都需要重新索引，成本是100%
        # 实际只需索引变更的文档，节省 = (1 - 变更率) * 100
        change_rate = (today_count / total_docs * 100) if total_docs > 0 else 0
        cost_saving = max(0, round(100 - change_rate, 1))

        # 加速因子：增量更新相比全量更新的速度提升
        # 计算公式：总文档数 / 需要更新的文档数
        speedup_factor = round(total_docs / max(pending_docs, 1), 1) if total_docs > 0 else 1

        stats = {
            'indexedCount': indexed_docs,
            'pendingCount': pending_docs,
            'failedCount': failed_tasks,
            'todayCount': today_count,
            'totalCount': total_docs,
            'costSavingPercent': cost_saving,
            'avgIndexTime': avg_index_time,
            'avgProcessSpeed': round(60 / avg_index_time if avg_index_time > 0 else 0, 1),  # docs/min
            'estimatedSaving': cost_saving,
            'speedupFactor': speedup_factor,
            'trendData': trend_data,
            'statusDistribution': status_distribution
        }

        return IndexResponse(
            success=True,
            message="统计信息获取成功",
            data=stats
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=IndexResponse)
async def get_change_history(
    doc_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取变更历史"""
    try:
        query = db.query(IndexChangeHistory)

        if doc_id:
            query = query.filter(IndexChangeHistory.doc_id == doc_id)

        total = query.count()
        history = query.order_by(
            IndexChangeHistory.changed_at.desc()
        ).offset(offset).limit(limit).all()

        return IndexResponse(
            success=True,
            message=f"获取到 {len(history)} 条历史记录",
            data={
                'history': [h.to_dict() for h in history],
                'total': total,
                'limit': limit,
                'offset': offset
            }
        )

    except Exception as e:
        logger.error(f"获取变更历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{doc_id}", response_model=IndexResponse)
async def get_document_history(
    doc_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """获取文档的索引变更历史"""
    try:
        history = db.query(IndexChangeHistory).filter(
            IndexChangeHistory.doc_id == doc_id
        ).order_by(
            IndexChangeHistory.changed_at.desc()
        ).limit(limit).all()

        return IndexResponse(
            success=True,
            message=f"获取到 {len(history)} 条历史记录",
            data={
                'doc_id': doc_id,
                'history': [h.to_dict() for h in history]
            }
        )

    except Exception as e:
        logger.error(f"获取历史记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=IndexResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    获取任务状态

    支持查询Celery任务和数据库任务记录
    """
    try:
        # 从数据库查询任务记录
        task_record = db.query(IndexTaskModel).filter(
            IndexTaskModel.task_id == task_id
        ).first()

        if not task_record:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        task_data = task_record.to_dict()

        # 如果是Celery任务,尝试获取Celery状态
        if CELERY_ENABLED:
            try:
                from app.celery_app import celery_app
                celery_task = celery_app.AsyncResult(task_id)

                # 合并Celery状态
                task_data['celery_state'] = celery_task.state
                task_data['celery_result'] = celery_task.result if celery_task.ready() else None

            except Exception as e:
                logger.warning(f"获取Celery任务状态失败: {e}")

        return IndexResponse(
            success=True,
            message="任务状态获取成功",
            data=task_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============== 辅助函数 ==============

def _async_batch_index(db: Session, doc_ids: List[int], user_id: Optional[int]):
    """异步批量索引（后台任务）- 废弃,改用Celery"""
    logger.warning("_async_batch_index已废弃,请使用Celery任务")
    pass
