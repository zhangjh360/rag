"""
Chat对话相关的API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
import asyncio
import base64
import os
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.chat_rag_service import ChatRAGService
from app.config.settings import get_settings, SERVER_URL
import logging

router = APIRouter()
settings = get_settings()

# RAG服务(保留旧服务作为降级备用)
rag_service = RAGService()
logger = logging.getLogger(__name__)


def get_llm_service(db: Session = Depends(get_db)) -> LLMService:
    """
    获取LLM服务实例（带数据库依赖注入）
    """
    return LLMService(db=db)

class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: Optional[str] = None
    message: str
    use_rag: bool = True
    stream: bool = True
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000

    # RAG检索参数(与query_v2保持一致)
    namespace: Optional[str] = None  # 可选的知识领域过滤参数
    retrieval_mode: Optional[str] = 'auto'  # auto/single/cross
    retrieval_method: Optional[str] = 'hybrid'  # vector/bm25/hybrid
    top_k: int = 5  # 返回结果数量
    similarity_threshold: float = 0.2  # 相似度阈值
    alpha: float = 0.5  # 混合检索权重(0.0=纯BM25, 1.0=纯向量)
    enable_query_rewrite: bool = True  # 是否启用查询重写
    # 新增图片支持
    image_ids: Optional[List[int]] = []  # 关联的图片ID列表

class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str
    message: str
    sources: Optional[List[Dict]] = None
    tokens_used: Optional[int] = None
    timestamp: Optional[datetime] = None
    # 新增可选字段(向后兼容)
    domain_classification: Optional[Dict] = None
    retrieval_stats: Optional[Dict] = None
    # 新增图片信息
    message_id: Optional[int] = None  # 消息ID，用于前端获取图片
    images: Optional[List[Dict]] = None  # 关联的图片信息

class SessionCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = "新对话"
    metadata: Optional[Dict] = {}

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None

@router.post("/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, llm_svc: LLMService = Depends(get_llm_service), db: Session = Depends(get_db)):
    """
    发送聊天消息
    支持流式响应和RAG增强
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        # 获取或创建会话
        session_id = request.session_id or str(uuid.uuid4())

        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()

        if not session:
            session = ChatSession(
                session_id=session_id,
                title=request.message[:50] if len(request.message) > 50 else request.message
            )
            db.add(session)
            db.commit()

        # 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # 关联图片到消息（如果有）
        if request.image_ids:
            from app.models.chat_image import ChatImage
            # 更新图片记录的 message_id
            db.query(ChatImage).filter(
                ChatImage.id.in_(request.image_ids),
                ChatImage.session_id == session_id
            ).update({"message_id": user_message.id}, synchronize_session=False)
            db.commit()

        # 【自动生成标题】检查是否为第一条用户消息
        user_message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).count()

        if user_message_count == 1 and session.title in ["新对话", "新会话", request.message[:50]]:
            # 这是第一条消息,自动生成标题
            try:
                logger.info(f"为会话 {session_id} 生成标题...")
                new_title = await llm_svc.generate_session_title(
                    first_message=request.message,
                    model=request.model
                )

                session.title = new_title
                session.updated_at = datetime.utcnow()
                db.commit()

                logger.info(f"会话标题已更新: {new_title}")
            except Exception as title_error:
                logger.error(f"生成标题失败: {title_error}")
                # 标题生成失败不影响主流程,使用默认标题

        # 获取历史消息作为上下文
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).limit(10).all()

        # 构造消息列表（支持多模态格式）
        def build_message_content(msg: ChatMessage) -> Dict[str, Any]:
            """构造消息内容，支持多模态格式"""
            # 如果消息有关联图片，使用多模态格式
            if msg.images and len(msg.images) > 0:
                content = []

                # 添加文本内容
                if msg.content and msg.content.strip():
                    content.append({
                        "type": "text",
                        "text": msg.content
                    })

                # 添加图片内容（转换为base64）
                for img in msg.images:
                    try:
                        # 读取图片文件并转换为base64
                        if os.path.exists(img.file_path):
                            with open(img.file_path, "rb") as image_file:
                                image_data = image_file.read()
                                base64_image = base64.b64encode(image_data).decode('utf-8')

                                # 构造data URL格式
                                mime_type = img.mime_type or "image/jpeg"
                                data_url = f"data:{mime_type};base64,{base64_image}"

                                content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url
                                    }
                                })
                        else:
                            logger.warning(f"图片文件不存在: {img.file_path}")
                    except Exception as e:
                        logger.error(f"读取图片失败: {e}")
                        continue

                return {"role": msg.role, "content": content}
            else:
                # 纯文本消息
                return {"role": msg.role, "content": msg.content}

        messages = [build_message_content(msg) for msg in history]

        # 如果启用RAG，获取相关文档
        sources = None
        rag_metadata = None
        if request.use_rag:
            msg = ""
            if len(request.message) > 50:
                msg = request.message[:50]
            else:
                msg = request.message

            logger.info(f"开始检索相关文档: {msg}...")

            try:
                # 获取上一轮对话的领域信息
                previous_domain = None
                previous_confidence = 0.0
                last_user_msg = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == 'user'
                ).order_by(ChatMessage.timestamp.desc()).offset(1).first()  # offset(1)跳过当前刚添加的消息

                if last_user_msg and last_user_msg.message_metadata:
                    previous_domain = last_user_msg.message_metadata.get('domain_namespace')
                    previous_confidence = last_user_msg.message_metadata.get('domain_confidence', 0.0)
                    logger.info(
                        f"上一轮领域: {previous_domain} (置信度: {previous_confidence:.2f})"
                    )

                # 准备聊天历史(用于查询重写)
                recent_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.timestamp.desc()).limit(10).all()

                chat_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in reversed(recent_messages)
                ]

                # 使用新的ChatRAGService (多领域检索 + 会话上下文感知)
                chat_rag_service = ChatRAGService(db=db)
                sources, rag_metadata = await chat_rag_service.search_for_chat(
                    query=request.message,
                    session_id=session_id,
                    top_k=request.top_k,  # 使用请求中的参数
                    similarity_threshold=request.similarity_threshold,  # 使用请求中的参数
                    alpha=request.alpha,  # 混合检索权重
                    namespace=request.namespace,  # 传递用户指定的领域参数
                    chat_history=chat_history,  # 新增:聊天历史
                    previous_domain=previous_domain,  # 新增:上一轮领域
                    enable_query_rewrite=request.enable_query_rewrite  # 使用请求中的参数
                )

                if sources:
                    # 将相关文档添加到上下文
                    context = "\n".join([doc["content"] for doc in sources[:3]])
                    messages.append({
                        "role": "system",
                        "content": f"参考以下文档内容回答用户问题：\n{context}"
                    })

                    # 记录检索元数据
                    if rag_metadata:
                        logger.info(
                            f"检索完成: mode={rag_metadata.get('retrieval_mode')}, "
                            f"domain={rag_metadata.get('classification', {}).get('namespace')}, "
                            f"results={len(sources)}, "
                            f"latency={rag_metadata.get('total_latency_ms', 0):.0f}ms"
                        )

                        # 【数据持久化 - 层1: message_metadata】
                        # 保存领域分类结果到用户消息的metadata
                        classification = rag_metadata.get('classification', {})
                        query_rewrite_info = rag_metadata.get('query_rewrite', {})
                        session_context = rag_metadata.get('session_context', {})

                        user_message.message_metadata = {
                            # 领域信息
                            'domain_namespace': classification.get('namespace'),
                            'domain_confidence': classification.get('confidence', 0.0),
                            'domain_method': classification.get('method'),
                            'domain_inherited': session_context.get('domain_inherited', False),
                            # 查询重写信息
                            'query_rewritten': query_rewrite_info.get('was_rewritten', False),
                            'original_query': query_rewrite_info.get('original_query'),
                            'rewritten_query': query_rewrite_info.get('rewritten_query'),
                            # 检索统计
                            'retrieval_mode': rag_metadata.get('retrieval_mode'),
                            'retrieval_results_count': len(sources),
                            'retrieval_latency_ms': rag_metadata.get('retrieval_latency_ms', 0)
                        }
                        db.commit()  # 提交更新

                        # 【数据持久化 - 层2: session_metadata】
                        # 更新会话级别的领域历史
                        if session:
                            session_meta = session.session_metadata or {}

                            # 记录领域切换历史
                            domain_history = session_meta.get('domain_history', [])
                            current_domain = classification.get('namespace')

                            if not domain_history or domain_history[-1].get('namespace') != current_domain:
                                domain_history.append({
                                    'namespace': current_domain,
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'confidence': classification.get('confidence', 0.0),
                                    'inherited': session_context.get('domain_inherited', False)
                                })

                            # 记录主要领域(出现次数最多的领域)
                            domain_counts = {}
                            for item in domain_history:
                                ns = item.get('namespace')
                                if ns:
                                    domain_counts[ns] = domain_counts.get(ns, 0) + 1

                            primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0] if domain_counts else current_domain

                            session.session_metadata = {
                                **session_meta,
                                'domain_history': domain_history[-10:],  # 保留最近10次
                                'primary_domain': primary_domain,
                                'domain_switch_count': len(domain_history),
                                'last_domain': current_domain
                            }
                            db.commit()

            except Exception as e:
                logger.error(f"多领域检索失败，降级到旧方法: {e}")
                # 降级到旧RAG方法
                try:
                    sources = await rag_service.search_relevant_docs(
                        request.message,
                        similarity_threshold=0.2
                    )
                    if sources:
                        context = "\n".join([doc["content"] for doc in sources[:3]])
                        messages.append({
                            "role": "system",
                            "content": f"参考以下文档内容回答用户问题：\n{context}"
                        })
                except Exception as e2:
                    logger.error(f"RAG检索完全失败: {e2}")
                    # 完全失败时，继续对话但不使用RAG
                    sources = None

        # 生成响应
        if request.stream:
            # 流式响应
            return StreamingResponse(
                llm_svc.stream_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    session_id=session_id,
                    db=db
                ),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            response = await llm_svc.get_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            # 保存助手响应
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response["content"],
                message_metadata={
                    "model": request.model,
                    "tokens": response.get("tokens_used", 0)
                }
            )
            db.add(assistant_message)
            db.commit()

            # 获取消息关联的图片（如果有）
            images = []
            if request.image_ids:
                from app.models.chat_image import ChatImage
                image_records = db.query(ChatImage).filter(
                    ChatImage.message_id == user_message.id
                ).all()
                images = [
                    {
                        "id": img.id,
                        "filename": img.filename,
                        "original_name": img.original_name,
                        "file_size": img.file_size,
                        "width": img.width,
                        "height": img.height,
                        "url": f"/api/chat/images/view/{img.filename}",
                        "thumbnail_url": f"/api/chat/images/thumb/{img.filename}"
                    }
                    for img in image_records
                ]

            # 构建响应
            chat_response = ChatResponse(
                session_id=session_id,
                message=response["content"],
                sources=sources,
                tokens_used=response.get("tokens_used"),
                timestamp=datetime.utcnow(),
                message_id=user_message.id,  # 添加消息ID
                images=images if images else None  # 添加图片信息
            )

            # 【数据持久化 - 层3: 响应体增强】
            # 添加扩展信息(可选)
            if rag_metadata:
                chat_response.domain_classification = rag_metadata.get('classification')
                chat_response.retrieval_stats = {
                    'retrieval_mode': rag_metadata.get('retrieval_mode'),
                    'retrieval_method': rag_metadata.get('retrieval_method'),
                    'total_latency_ms': rag_metadata.get('total_latency_ms'),
                    'total_results': rag_metadata.get('total_results'),
                    # 新增:查询重写信息
                    'query_rewrite': rag_metadata.get('query_rewrite'),
                    # 新增:会话上下文信息
                    'session_context': rag_metadata.get('session_context')
                }

            return chat_response

    except Exception as e:
        logger.error(f"Chat API 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/send", response_model=ChatResponse)
async def send_message_get(
    session_id: Optional[str] = None,
    message: str = "",
    use_rag: bool = True,
    stream: bool = True,
    model: str = "gpt-3.5-turbo",
    namespace: Optional[str] = None,  # 添加知识领域参数
    llm_svc: LLMService = Depends(get_llm_service),
    db: Session = Depends(get_db)
):
    """
    发送聊天消息 (GET方法,支持URL参数)
    """
    try:
        # 构建请求对象
        request = ChatRequest(
            session_id=session_id,
            message=message,
            use_rag=use_rag,
            stream=stream,
            model=model,
            namespace=namespace  # 传递 namespace 参数
        )
        return await send_message(request, llm_svc, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions", response_model=List[SessionResponse])
async def get_sessions(db: Session = Depends(get_db)):
    """获取所有聊天会话"""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

    result = []
    for session in sessions:
        message_count = len(session.messages)
        last_message = None
        if session.messages:
            last_msg = sorted(session.messages, key=lambda m: m.timestamp)[-1]
            last_message = last_msg.content[:100] if len(last_msg.content) > 100 else last_msg.content

        result.append(SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message
        ))

    return result

@router.post("/chat/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate, db: Session = Depends(get_db)):
    """创建新的聊天会话"""
    session_id = str(uuid.uuid4())

    session = ChatSession(
        session_id=session_id,
        title=request.title,
        session_metadata=request.metadata
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
        last_message=None
    )

@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """获取会话的所有消息"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()

    # 获取所有消息关联的图片
    from app.models.chat_image import ChatImage
    message_ids = [msg.id for msg in messages]
    images_by_message = {}

    if message_ids:
        image_records = db.query(ChatImage).filter(
            ChatImage.message_id.in_(message_ids)
        ).all()

        for img in image_records:
            if img.message_id not in images_by_message:
                images_by_message[img.message_id] = []
            images_by_message[img.message_id].append({
                "id": img.id,
                "filename": img.filename,
                "original_name": img.original_name,
                "file_size": img.file_size,
                "width": img.width,
                "height": img.height,
                "url": f"/api/chat/images/view/{img.filename}",
                "thumbnail_url": f"/api/chat/images/thumb/{img.filename}"
            })

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "metadata": msg.message_metadata,
            "images": images_by_message.get(msg.id, [])  # 添加图片信息
        }
        for msg in messages
    ]

@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}

@router.put("/chat/sessions/{session_id}")
async def update_session_title(
    session_id: str,
    title: str,
    db: Session = Depends(get_db)
):
    """更新会话标题"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = title
    session.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Session title updated successfully"}

@router.get("/chat/history")
async def get_query_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取查询历史记录
    支持分页
    """
    try:
        # 计算总数
        total = db.query(ChatSession).count()

        # 获取分页会话，按更新时间倒序
        sessions = db.query(ChatSession)\
            .order_by(ChatSession.updated_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        # 转换为历史记录格式
        history = []
        for session in sessions:
            # 获取会话中的第一条用户消息作为查询
            first_user_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id,
                ChatMessage.role == "user"
            ).order_by(ChatMessage.timestamp.asc()).first()

            # 获取会话的所有消息（用于详情展示）
            all_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).order_by(ChatMessage.timestamp.asc()).all()

            # 获取图片关联
            from app.models.chat_image import ChatImage
            message_ids = [msg.id for msg in all_messages]
            images_by_message = {}

            if message_ids:
                image_records = db.query(ChatImage).filter(
                    ChatImage.message_id.in_(message_ids)
                ).all()

                for img in image_records:
                    if img.message_id not in images_by_message:
                        images_by_message[img.message_id] = []
                    images_by_message[img.message_id].append({
                        "id": img.id,
                        "filename": img.filename,
                        "original_name": img.original_name,
                        "url": f"/api/chat/images/view/{img.filename}",
                        "thumbnail_url": f"/api/chat/images/thumb/{img.filename}"
                    })

            # 格式化所有消息
            messages_data = [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.message_metadata,
                    "images": images_by_message.get(msg.id, [])
                }
                for msg in all_messages
            ]

            # 获取第一个助手回复（用于预览）
            first_assistant_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id,
                ChatMessage.role == "assistant"
            ).order_by(ChatMessage.timestamp.asc()).first()

            if first_user_message:
                history.append({
                    "id": session.session_id,
                    "query": first_user_message.content,
                    "response": first_assistant_message.content if first_assistant_message else None,
                    "timestamp": session.created_at.isoformat(),
                    "session_id": session.session_id,
                    "title": session.title,
                    "messages": messages_data,  # 完整的对话历史
                    "message_count": len(messages_data),
                    # 从第一条消息的元数据中提取信息
                    "model": first_user_message.message_metadata.get("model") if first_user_message.message_metadata else None,
                    "use_rag": first_user_message.message_metadata.get("use_rag") if first_user_message.message_metadata else None,
                    "tokens_used": first_assistant_message.message_metadata.get("tokens_used") if first_assistant_message and first_assistant_message.message_metadata else None,
                    "response_time": first_assistant_message.message_metadata.get("response_time") if first_assistant_message and first_assistant_message.message_metadata else None,
                })

        # 返回分页数据和元信息
        return {
            "data": history,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))