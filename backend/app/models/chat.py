"""
Chat相关的数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ChatSession(Base):
    """聊天会话模型"""
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    session_metadata = Column(JSON, default={})

    # 关系
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """聊天消息模型"""
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey('chat_sessions.session_id'))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    message_metadata = Column(JSON, default={})  # 存储额外信息如token数、模型等

    # 关系
    session = relationship("ChatSession", back_populates="messages")
    images = relationship("ChatImage", back_populates="message")