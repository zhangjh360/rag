"""
聊天图片上传路由
提供图片上传、预览、删除等功能
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from PIL import Image, UnidentifiedImageError

from app.database import get_db
from app.models.chat_image import ChatImage
from app.middleware.auth import get_current_user
from app.models.database import User
from app.config.settings import get_settings

router = APIRouter(prefix="/api/chat/images", tags=["chat-images"])
settings = get_settings()
# 支持的图片格式
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}

# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# 最大上传数量
MAX_UPLOAD_COUNT = 3


def get_upload_dirs():
    """获取上传目录路径"""
    today = datetime.now().strftime("%Y/%m")
    upload_dir = Path(settings["upload_dir"]) / "images" / today
    thumb_dir = Path(settings["upload_dir"]) / "thumbnails" / today

    # 创建目录
    upload_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    return str(upload_dir), str(thumb_dir)


def validate_image_file(file: UploadFile) -> bool:
    """验证是否为有效的图片文件"""
    # 检查MIME类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False

    return True


def create_thumbnail(image_path: str, thumb_path: str, size: tuple = (200, 200)) -> Optional[tuple]:
    """
    创建图片缩略图

    Args:
        image_path: 原图路径
        thumb_path: 缩略图保存路径
        size: 缩略图尺寸

    Returns:
        图片尺寸 (width, height) 或 None
    """
    try:
        with Image.open(image_path) as img:
            # 获取原图尺寸
            original_size = img.size

            # 如果原图小于缩略图尺寸，直接复制
            if img.size[0] <= size[0] and img.size[1] <= size[1]:
                img.save(thumb_path, format=img.format, optimize=True)
                return original_size

            # 创建缩略图
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # 处理透明图片
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background

            # 保存缩略图
            img.save(thumb_path, 'JPEG', quality=85, optimize=True)
            return original_size

    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="无效的图片文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建缩略图失败: {str(e)}")


@router.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    session_id: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传图片

    Args:
        files: 上传的文件列表（最多3个）
        session_id: 会话ID

    Returns:
        上传成功的图片信息列表
    """
    # 验证文件数量
    if len(files) > MAX_UPLOAD_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"最多只能上传{MAX_UPLOAD_COUNT}张图片"
        )

    # 获取上传目录
    upload_dir, thumb_dir = get_upload_dirs()

    uploaded_images = []

    for file in files:
        # 验证文件类型
        if not validate_image_file(file):
            continue  # 跳过无效文件

        try:
            # 读取文件内容
            content = await file.read()

            # 验证文件大小
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件 {file.filename} 大小超过5MB限制"
                )

            # 验证是否为真实图片
            if not content.startswith(b'\xff\xd8') and not content.startswith(b'\x89PNG'):
                # 简单的魔数检查
                continue

            # 生成唯一文件名
            file_ext = os.path.splitext(file.filename)[1].lower()
            if not file_ext:
                # 根据MIME类型推断扩展名
                ext_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/webp": ".webp"
                }
                file_ext = ext_map.get(file.content_type, ".jpg")

            unique_name = f"{uuid.uuid4().hex}{file_ext}"

            # 保存文件
            file_path = os.path.join(upload_dir, unique_name)
            with open(file_path, "wb") as f:
                f.write(content)

            # 创建缩略图
            thumbnail_name = f"thumb_{unique_name}"
            thumbnail_path = os.path.join(thumb_dir, thumbnail_name)
            original_size = create_thumbnail(file_path, thumbnail_path)

            # 保存到数据库
            image_record = ChatImage(
                filename=unique_name,
                original_name=file.filename,
                file_path=file_path,
                thumbnail_path=thumbnail_path,
                file_size=len(content),
                mime_type=file.content_type,
                width=original_size[0] if original_size else None,
                height=original_size[1] if original_size else None,
                uploaded_by=current_user.username,  # User对象的username属性
                session_id=session_id
            )

            db.add(image_record)
            db.commit()
            db.refresh(image_record)

            # 构建返回数据
            uploaded_images.append({
                "id": image_record.id,
                "filename": unique_name,
                "original_name": file.filename,
                "file_size": len(content),
                "width": original_size[0] if original_size else None,
                "height": original_size[1] if original_size else None,
                "url": f"/api/chat/images/view/{unique_name}",
                "thumbnail_url": f"/api/chat/images/thumb/{unique_name}"
            })

        except Exception as e:
            # 清理已上传的文件
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            if 'thumbnail_path' in locals() and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

            raise HTTPException(
                status_code=500,
                detail=f"上传文件 {file.filename} 失败: {str(e)}"
            )

    if not uploaded_images:
        raise HTTPException(
            status_code=400,
            detail="没有有效的图片文件被上传"
        )

    return {
        "success": True,
        "message": f"成功上传{len(uploaded_images)}张图片",
        "data": uploaded_images
    }


@router.get("/view/{filename}")
async def get_image(filename: str, db: Session = Depends(get_db)):
    """
    获取图片文件

    Args:
        filename: 文件名

    Returns:
        图片文件响应
    """
    # 查找图片记录
    image = db.query(ChatImage).filter(ChatImage.filename == filename).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 检查文件是否存在
    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="图片文件已丢失")

    # 返回文件
    return FileResponse(
        image.file_path,
        media_type=image.mime_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # 缓存1天
        }
    )


@router.get("/thumb/{filename}")
async def get_thumbnail(filename: str, db: Session = Depends(get_db)):
    """
    获取缩略图文件

    Args:
        filename: 文件名（不含thumb_前缀）

    Returns:
        缩略图文件响应
    """
    # 查找图片记录
    image = db.query(ChatImage).filter(ChatImage.filename == filename).first()

    if not image or not image.thumbnail_path:
        raise HTTPException(status_code=404, detail="缩略图不存在")

    # 检查文件是否存在
    if not os.path.exists(image.thumbnail_path):
        raise HTTPException(status_code=404, detail="缩略图文件已丢失")

    # 返回文件
    return FileResponse(
        image.thumbnail_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=86400",  # 缓存1天
        }
    )


@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除图片

    Args:
        image_id: 图片ID

    Returns:
        删除结果
    """
    # 查找图片记录
    image = db.query(ChatImage).filter(ChatImage.id == image_id).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")

    # 检查权限
    if image.uploaded_by != current_user.username:
        raise HTTPException(status_code=403, detail="无权删除此图片")

    try:
        # 删除文件
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        if image.thumbnail_path and os.path.exists(image.thumbnail_path):
            os.remove(image.thumbnail_path)

        # 删除数据库记录
        db.delete(image)
        db.commit()

        return {
            "success": True,
            "message": "图片已删除"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除图片失败: {str(e)}"
        )


@router.get("/list/{session_id}")
async def list_session_images(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话中的所有图片

    Args:
        session_id: 会话ID

    Returns:
        图片列表
    """
    images = db.query(ChatImage).filter(
        ChatImage.session_id == session_id,
        ChatImage.uploaded_by == current_user.username
    ).order_by(ChatImage.upload_time.desc()).all()

    return {
        "success": True,
        "data": [
            {
                "id": img.id,
                "filename": img.filename,
                "original_name": img.original_name,
                "file_size": img.file_size,
                "width": img.width,
                "height": img.height,
                "upload_time": img.upload_time,
                "url": f"/api/chat/images/view/{img.filename}",
                "thumbnail_url": f"/api/chat/images/thumb/{img.filename}"
            }
            for img in images
        ]
    }