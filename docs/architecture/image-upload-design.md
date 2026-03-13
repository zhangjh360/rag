# 聊天图片上传功能设计文档

## 1. 功能概述

在聊天对话框中支持图片上传功能，允许用户：
- 上传本地图片文件
- 在消息中插入图片
- 查看上传的图片缩略图
- 删除已上传的图片

## 2. 需求分析

### 2.1 功能需求
1. **图片上传**
   - 支持拖拽上传
   - 支持点击选择文件
   - 支持多选（最多3张）
   - 显示上传进度

2. **图片格式限制**
   - 支持：JPG, JPEG, PNG, GIF, WebP
   - 最大文件大小：5MB/张

3. **图片处理**
   - 自动生成缩略图
   - 保存原图和缩略图
   - 图片压缩优化

4. **界面功能**
   - 图片预览
   - 删除已上传图片
   - 错误提示

### 2.2 非功能需求
- 响应时间：上传完成 < 2秒
- 并发支持：最多10个同时上传
- 安全性：文件类型验证，防止恶意文件
- 存储：本地文件系统存储

## 3. 技术方案

### 3.1 系统架构

```
前端(Chat.vue) --> 图片上传组件 --> API请求 --> 后端(upload.py) --> 文件存储
                      |                     |
                      v                     v
                 图片预览组件          PIL图片处理
```

### 3.2 存储方案

```
uploads/
  ├── images/           # 原图存储
  │   ├── 2024/01/     # 按年月分目录
  │   └── ...
  └── thumbnails/      # 缩略图存储
      ├── 2024/01/
      └── ...
```

### 3.3 数据库设计

新增图片记录表：

```sql
CREATE TABLE chat_images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,          # 文件名
    original_name VARCHAR(255) NOT NULL,     # 原始文件名
    file_path VARCHAR(500) NOT NULL,         # 文件路径
    thumbnail_path VARCHAR(500),             # 缩略图路径
    file_size INTEGER NOT NULL,              # 文件大小(bytes)
    mime_type VARCHAR(100) NOT NULL,         # MIME类型
    width INTEGER,                           # 图片宽度
    height INTEGER,                          # 图片高度
    uploaded_by VARCHAR(100) NOT NULL,       # 上传用户
    upload_time TIMESTAMP DEFAULT NOW(),     # 上传时间
    session_id VARCHAR(100),                 # 会话ID
    message_id INTEGER REFERENCES messages(id) # 关联消息
);
```

### 3.4 API设计

#### 3.4.1 上传图片
```
POST /api/chat/images/upload
Content-Type: multipart/form-data

Request Body:
- files: File[] (最多3个)
- session_id: string

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "filename": "abc123.jpg",
      "original_name": "photo.jpg",
      "file_path": "/uploads/images/2024/01/abc123.jpg",
      "thumbnail_path": "/uploads/thumbnails/2024/01/abc123_thumb.jpg",
      "file_size": 1024000,
      "width": 1920,
      "height": 1080,
      "url": "/api/chat/images/view/abc123.jpg",
      "thumbnail_url": "/api/chat/images/thumb/abc123.jpg"
    }
  ]
}
```

#### 3.4.2 删除图片
```
DELETE /api/chat/images/{image_id}

Response:
{
  "success": true,
  "message": "图片已删除"
}
```

#### 3.4.3 获取图片
```
GET /api/chat/images/view/{filename}
GET /api/chat/images/thumb/{filename}
```

## 4. 前端实现方案

### 4.1 组件结构

```
components/chat/
├── ImageUpload.vue     # 图片上传组件
├── ImagePreview.vue    # 图片预览组件
├── MessageInput.vue    # 消息输入框（集成上传）
└── ChatMessage.vue     # 消息显示（含图片）
```

### 4.2 ImageUpload.vue 核心功能

```vue
<template>
  <div class="image-upload">
    <!-- 上传区域 -->
    <div class="upload-area"
         @drop="handleDrop"
         @dragover.prevent
         @click="selectFiles">
      <el-icon><Upload /></el-icon>
      <p>点击或拖拽图片到此处上传</p>
      <p class="hint">支持 JPG/PNG/GIF/WebP，最大5MB，最多3张</p>
    </div>

    <!-- 图片列表 -->
    <div class="image-list">
      <div v-for="img in uploadedImages" :key="img.id" class="image-item">
        <img :src="img.thumbnail_url" alt="preview" />
        <div class="image-info">
          <span>{{ img.original_name }}</span>
          <el-button type="danger" size="small" @click="removeImage(img.id)">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      type="file"
      ref="fileInput"
      multiple
      accept="image/*"
      @change="handleFileSelect"
      style="display: none">
  </div>
</template>
```

### 4.3 上传逻辑

```javascript
const uploadImages = async (files) => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  formData.append('session_id', sessionId.value)

  try {
    const response = await axios.post('/api/chat/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progress) => {
        const percent = Math.round((progress.loaded * 100) / progress.total)
        updateProgress(percent)
      }
    })

    if (response.data.success) {
      uploadedImages.value.push(...response.data.data)
      emit('uploaded', response.data.data)
    }
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  }
}
```

## 5. 后端实现方案

### 5.1 路由文件结构

```
backend/app/routers/
├── chat_images.py     # 图片上传路由
└── websocket.py       # WebSocket实时通知
```

### 5.2 核心上传逻辑

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from PIL import Image
import uuid
import os
from datetime import datetime

router = APIRouter(prefix="/api/chat/images", tags=["chat-images"])

@router.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # 限制文件数量
    if len(files) > 3:
        raise HTTPException(status_code=400, detail="最多上传3张图片")

    uploaded_images = []

    for file in files:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            continue

        # 生成文件名
        file_ext = file.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"

        # 按日期创建目录
        today = datetime.now().strftime("%Y/%m")
        upload_dir = f"uploads/images/{today}"
        thumb_dir = f"uploads/thumbnails/{today}"
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(thumb_dir, exist_ok=True)

        # 保存原图
        file_path = f"{upload_dir}/{unique_name}"
        with open(file_path, "wb") as f:
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:  # 5MB限制
                raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
            f.write(content)

        # 生成缩略图
        thumbnail_path = f"{thumb_dir}/{unique_name}"
        create_thumbnail(file_path, thumbnail_path)

        # 保存到数据库
        image_record = ChatImage(
            filename=unique_name,
            original_name=file.filename,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            file_size=len(content),
            mime_type=file.content_type,
            uploaded_by=current_user,
            session_id=session_id
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)

        uploaded_images.append({
            "id": image_record.id,
            "filename": unique_name,
            "original_name": file.filename,
            "url": f"/api/chat/images/view/{unique_name}",
            "thumbnail_url": f"/api/chat/images/thumb/{unique_name}",
            "file_size": len(content)
        })

    return {"success": True, "data": uploaded_images}
```

### 5.3 缩略图生成

```python
def create_thumbnail(image_path: str, thumb_path: str, size: tuple = (200, 200)):
    """创建图片缩略图"""
    with Image.open(image_path) as img:
        # 保持宽高比缩放
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # 处理透明图片
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        img.save(thumb_path, 'JPEG', quality=85, optimize=True)
```

## 6. 安全考虑

1. **文件类型验证**
   - 检查 MIME 类型
   - 验证文件头魔数
   - 使用 PIL 验证是否为有效图片

2. **文件大小限制**
   - 前端预检查
   - 后端强制限制

3. **存储安全**
   - 随机文件名
   - 按日期分目录
   - 定期清理临时文件

4. **访问控制**
   - 登录用户才能上传
   - 通过会话ID限制访问

## 7. 性能优化

1. **前端优化**
   - 图片压缩后再上传
   - 使用 Web Workers 处理大图
   - 上传进度显示

2. **后端优化**
   - 异步上传处理
   - 图片缓存机制
   - CDN 加速图片访问

3. **存储优化**
   - 定期清理未关联图片
   - 使用对象存储(可选)

## 8. 测试计划

1. **单元测试**
   - 文件上传API
   - 图片处理函数
   - 数据库操作

2. **集成测试**
   - 上传流程端到端
   - 并发上传测试
   - 异常处理测试

3. **用户测试**
   - 不同浏览器兼容性
   - 大文件上传
   - 网络异常处理

## 9. 部署说明

1. **环境配置**
   ```bash
   pip install Pillow  # 图片处理库
   ```

2. **存储配置**
   - 确保uploads目录可写
   - 配置静态文件服务
   - 设置磁盘空间监控

3. **Nginx配置**
   ```nginx
   location /uploads/ {
       alias /path/to/uploads/;
       expires 7d;
   }
   ```

## 10. 后续扩展

1. 支持视频上传
2. OCR文字识别
3. AI图片分析
4. 云存储集成
5. 图片编辑功能