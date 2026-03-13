# RAG 智能问答系统使用指南

## 系统概述

本系统是一个基于检索增强生成（RAG）技术的智能问答系统，能够处理用户上传的文档并提供智能问答服务。

**📖 完整技术文档**: [文档中心](docs/INDEX.md)

## 功能特性

- **文档上传**: 支持 PDF 和 TXT 格式的文档上传
- **智能检索**: 基于向量相似度的文档检索
- **自然语言回答**: 使用 OpenAI API 生成自然的回答
- **查询历史**: 保存和查看历史查询记录
- **用户友好界面**: 现代化的 Web 界面

## 系统要求

### 后端环境
- Python 3.10+
- PostgreSQL 15+ (安装 pgvector 扩展)
- OpenAI API 密钥

### 前端环境
- Node.js 16+
- 现代浏览器

## 安装和配置

### 1. 数据库设置

```bash
# 安装 PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb ragdb
sudo -u postgres psql -c "CREATE USER raguser WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;"

# 启用 pgvector 扩展
sudo -u postgres psql -d ragdb -c "CREATE EXTENSION vector;"
```

### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API 密钥和数据库连接信息

# 初始化数据库
python database.py
```

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

## 运行系统

### 启动后端服务

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8800
```

### 启动前端服务

```bash
cd frontend
npm run dev
```

访问 http://localhost:3000 即可使用系统。

## 使用说明

### 1. 上传文档

1. 在首页的"文档上传"区域，点击或拖拽文件到上传区域
2. 支持的文件格式：PDF、TXT
3. 点击"上传文档"按钮完成上传
4. 上传成功后，文档会显示在下方的"已上传文档"列表中

### 2. 智能查询

1. 在"智能查询"区域的文本框中输入您的问题
2. 点击"查询"按钮或按 Enter 键
3. 系统会检索相关文档并生成回答
4. 查询结果包括：
   - 生成的回答
   - 相关文档列表（显示相似度和内容预览）

### 3. 查看历史记录

1. 点击左侧菜单的"查询历史"
2. 可以查看所有历史查询记录
3. 每条记录包含问题、回答和相关文档信息
4. 点击"刷新"按钮可以更新历史记录

## API 文档

### 文档管理接口

#### 上传文档
- **URL**: `POST /api/upload`
- **参数**: 
  - `file`: 文件对象 (PDF 或 TXT)
- **返回**: 
  ```json
  {
    "message": "Document uploaded successfully",
    "document_id": 1,
    "filename": "example.pdf"
  }
  ```

#### 获取文档列表
- **URL**: `GET /api/documents`
- **返回**: 文档列表

### 查询接口

#### 执行查询
- **URL**: `POST /api/query`
- **参数**: 
  ```json
  {
    "query": "您的问题"
  }
  ```
- **返回**: 
  ```json
  {
    "response": "生成的回答",
    "sources": [
      {
        "id": 1,
        "filename": "document.pdf",
        "similarity": 0.95,
        "content_preview": "文档内容预览..."
      }
    ]
  }
  ```

#### 获取查询历史
- **URL**: `GET /api/history`
- **返回**: 查询历史记录列表

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 PostgreSQL 服务是否运行
   - 验证数据库连接字符串是否正确
   - 确认 pgvector 扩展已安装

2. **OpenAI API 调用失败**
   - 检查 API 密钥是否正确
   - 确认 API 密钥有足够的额度
   - 检查网络连接

3. **文档上传失败**
   - 确认文件格式为 PDF 或 TXT
   - 检查文件大小是否超过限制
   - 确认文件内容可读

4. **前端无法访问后端 API**
   - 检查后端服务是否运行在 8800 端口
   - 确认 CORS 配置正确
   - 检查防火墙设置

### 日志查看

- 后端日志：查看控制台输出或配置日志文件
- 前端日志：使用浏览器开发者工具查看控制台

## 扩展功能

### 支持更多文件格式
可以在后端添加对应的文件解析库，如：
- Word 文档：`python-docx`
- Excel 文件：`openpyxl`
- 图片 OCR：`pytesseract`

### 性能优化
- 添加 Redis 缓存
- 实现文档分块处理
- 优化向量索引

### 安全性增强
- 添加用户认证
- 实现 API 访问控制
- 添加请求频率限制

## 技术栈

### 后端
- FastAPI: Web 框架
- SQLAlchemy: ORM 框架
- PostgreSQL + pgvector: 数据库
- OpenAI API: 嵌入和生成
- PyPDF2: PDF 解析

### 前端
- Vue 3: 前端框架
- Element Plus: UI 组件库
- Pinia: 状态管理
- Axios: HTTP 客户端
- Vite: 构建工具

## 文档资源

### 📖 技术文档
完整的技术文档请访问 **[文档中心](docs/INDEX.md)**

### 快速导航
- **[快速开始](docs/getting-started/)** - 快速了解和上手项目
- **[架构设计](docs/architecture/)** - 系统架构和数据库设计
- **[功能文档](docs/features/)** - 各功能模块的实现文档
- **[运维指南](docs/operations/)** - 部署、配置、监控和优化
- **[开发指南](docs/development/)** - 开发环境和代码规范

### 核心文档
- [增量索引系统](docs/features/incremental-indexing.md) - 智能文档增量更新
- [系统设计文档](docs/architecture/system-design.md) - 整体架构设计
- [性能优化指南](docs/operations/performance-optimization.md) - 系统性能优化

## 许可证

本项目仅用于学习和演示目的。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 GitHub Issue
- 发送邮件至维护者
- 查阅 [文档中心](docs/INDEX.md) 获取详细技术资料