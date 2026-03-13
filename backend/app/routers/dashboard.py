"""
Dashboard统计API路由
提供Dashboard页面所需的所有统计数据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import cast, DateTime, func
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import logging

from app.database.connection import get_db
from app.models.database import Document, Query, User, UserDocument
from app.models.chat import ChatSession, ChatMessage
from app.middleware.auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取Dashboard统计数据汇总

    Returns:
        {
            "documents": { "total": int, "recent_7days": int, "trend_percent": float },
            "sessions": { "total": int, "active_7days": int, "trend_percent": float },
            "queries": { "total": int, "recent_7days": int, "trend_percent": float },
            "users": { "total": int, "active": int },
            "activity_timeline": [...],
            "recent_documents": [...],
            "active_sessions": [...]
        }
    """
    try:
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        # 1. 文档统计
        total_documents = db.query(Document).count()

        # 最近7天的文档数
        recent_docs_7d = db.query(Document).filter(
            cast(Document.created_at, DateTime) >= seven_days_ago
        ).count()

        # 前7天的文档数 (用于计算趋势)
        previous_docs_7d = db.query(Document).filter(
            cast(Document.created_at, DateTime) >= fourteen_days_ago,
            cast(Document.created_at, DateTime) < seven_days_ago
        ).count()

        # 计算文档趋势百分比
        docs_trend = 0.0
        if previous_docs_7d > 0:
            docs_trend = ((recent_docs_7d - previous_docs_7d) / previous_docs_7d) * 100
        elif recent_docs_7d > 0:
            docs_trend = 100.0

        # 2. 对话会话统计
        total_sessions = db.query(ChatSession).count()

        # 最近7天活跃的会话
        active_sessions_7d = db.query(ChatSession).filter(
            ChatSession.updated_at >= seven_days_ago
        ).count()

        # 前7天活跃的会话
        previous_sessions_7d = db.query(ChatSession).filter(
            ChatSession.updated_at >= fourteen_days_ago,
            ChatSession.updated_at < seven_days_ago
        ).count()

        # 计算会话趋势
        sessions_trend = 0.0
        if previous_sessions_7d > 0:
            sessions_trend = ((active_sessions_7d - previous_sessions_7d) / previous_sessions_7d) * 100
        elif active_sessions_7d > 0:
            sessions_trend = 100.0

        # 3. 查询统计
        total_queries = db.query(Query).count()

        # 最近7天的查询
        recent_queries_7d = db.query(Query).filter(
            cast(Query.created_at, DateTime) >= seven_days_ago
        ).count()

        # 前7天的查询
        previous_queries_7d = db.query(Query).filter(
            cast(Query.created_at, DateTime) >= fourteen_days_ago,
            cast(Query.created_at, DateTime) < seven_days_ago
        ).count()

        # 计算查询趋势
        queries_trend = 0.0
        if previous_queries_7d > 0:
            queries_trend = ((recent_queries_7d - previous_queries_7d) / previous_queries_7d) * 100
        elif recent_queries_7d > 0:
            queries_trend = 100.0

        # 4. 用户统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == 'Y').count()

        # 5. 活动时间线 (最近7天)
        activity_timeline = []
        for i in range(6, -1, -1):  # 从6天前到今天
            date = now - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)

            # 统计当天的文档、查询、对话数量
            docs_count = db.query(Document).filter(
                cast(Document.created_at, DateTime) >= date_start,
                cast(Document.created_at, DateTime) < date_end
            ).count()

            queries_count = db.query(Query).filter(
                cast(Query.created_at, DateTime) >= date_start,
                cast(Query.created_at, DateTime) < date_end
            ).count()

            # 对话消息数量
            messages_count = db.query(ChatMessage).filter(
                ChatMessage.timestamp >= date_start,
                ChatMessage.timestamp < date_end
            ).count()

            activity_timeline.append({
                "date": date.strftime("%Y-%m-%d"),
                "date_label": date.strftime("%m/%d"),
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()],
                "documents": docs_count,
                "queries": queries_count,
                "messages": messages_count
            })

        # 6. 最近文档 (Top 5)
        recent_documents_query = db.query(Document).order_by(
            Document.created_at.desc()
        ).limit(5).all()

        recent_documents = []
        for doc in recent_documents_query:
            metadata = json.loads(doc.doc_metadata) if doc.doc_metadata else {}
            file_type = metadata.get("type", "unknown")

            # 计算相对时间
            try:
                created_time = datetime.fromisoformat(doc.created_at) if isinstance(doc.created_at, str) else doc.created_at
                time_diff = now - created_time

                if time_diff.days > 0:
                    relative_time = f"{time_diff.days}天前"
                elif time_diff.seconds >= 3600:
                    relative_time = f"{time_diff.seconds // 3600}小时前"
                elif time_diff.seconds >= 60:
                    relative_time = f"{time_diff.seconds // 60}分钟前"
                else:
                    relative_time = "刚刚"
            except:
                relative_time = "未知"

            recent_documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_type": file_type,
                "created_at": doc.created_at,
                "relative_time": relative_time
            })

        # 7. 活跃对话会话 (Top 5)
        active_sessions_query = db.query(ChatSession).order_by(
            ChatSession.updated_at.desc()
        ).limit(5).all()

        active_sessions = []
        for session in active_sessions_query:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).count()

            # 获取最后一条消息
            last_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).order_by(ChatMessage.timestamp.desc()).first()

            last_message_preview = None
            if last_message:
                content = last_message.content
                last_message_preview = content[:50] + "..." if len(content) > 50 else content

            # 计算相对时间
            try:
                updated_time = session.updated_at
                time_diff = now - updated_time

                if time_diff.days > 0:
                    relative_time = f"{time_diff.days}天前"
                elif time_diff.seconds >= 3600:
                    relative_time = f"{time_diff.seconds // 3600}小时前"
                elif time_diff.seconds >= 60:
                    relative_time = f"{time_diff.seconds // 60}分钟前"
                else:
                    relative_time = "刚刚"
            except:
                relative_time = "未知"

            active_sessions.append({
                "session_id": session.session_id,
                "title": session.title or "未命名对话",
                "message_count": message_count,
                "last_message": last_message_preview,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "relative_time": relative_time
            })

        # 返回完整统计数据
        return {
            "documents": {
                "total": total_documents,
                "recent_7days": recent_docs_7d,
                "trend_percent": round(docs_trend, 1)
            },
            "sessions": {
                "total": total_sessions,
                "active_7days": active_sessions_7d,
                "trend_percent": round(sessions_trend, 1)
            },
            "queries": {
                "total": total_queries,
                "recent_7days": recent_queries_7d,
                "trend_percent": round(queries_trend, 1)
            },
            "users": {
                "total": total_users,
                "active": active_users
            },
            "activity_timeline": activity_timeline,
            "recent_documents": recent_documents,
            "active_sessions": active_sessions,
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")
