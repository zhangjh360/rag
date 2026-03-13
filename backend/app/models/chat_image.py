"""
聊天图片模型
用于存储上传的图片信息
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 导入统一的 Base
from app.models.chat import Base


class ChatImage(Base):
    """聊天图片记录表"""
    __tablename__ = "chat_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment="存储的文件名")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    thumbnail_path = Column(String(500), nullable=True, comment="缩略图路径")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(bytes)")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    width = Column(Integer, nullable=True, comment="图片宽度")
    height = Column(Integer, nullable=True, comment="图片高度")
    uploaded_by = Column(String(100), nullable=False, comment="上传用户")
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")
    session_id = Column(String(100), nullable=True, comment="会话ID")
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True, comment="关联的消息ID")

    # 关系
    message = relationship("ChatMessage", back_populates="images")

    def __repr__(self):
        return f"<ChatImage(id={self.id}, filename='{self.filename}', uploaded_by='{self.uploaded_by}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "uploaded_by": self.uploaded_by,
            "upload_time": self.upload_time,
            "session_id": self.session_id,
            "message_id": self.message_id
        }