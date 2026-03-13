# RAG 智能问答系统 - 用户认证与权限系统使用说明

## 系统概述

已完成基于 JWT 的用户认证和权限管理系统,包含三个用户角色:
- **管理员 (admin)**: 拥有所有权限,包括用户管理、角色管理
- **普通用户 (user)**: 可以上传文档、提问、查看历史
- **只读用户 (readonly)**: 只能查看文档和提问,不能上传或删除

## 快速启动

### 1. 初始化数据库

在首次使用前,需要初始化认证系统的数据库表和默认数据:

```bash
cd /home/zhangjh/code/python/rag/backend
python -m app.migrations.init_auth
```

此命令会:
- 创建所有必需的数据库表(users, roles, user_documents, user_queries)
- 创建三个默认角色(admin, user, readonly)
- 创建默认管理员账户
  - 用户名: `admin`
  - 密码: `admin123`
  - **重要**: 首次登录后请立即修改密码!

### 2. 启动后端服务

```bash
cd /home/zhangjh/code/python/rag/backend
uvicorn app.main:app --reload --port 8800
```

后端服务将在 `http://localhost:8800` 启动

### 3. 启动前端服务

```bash
cd /home/zhangjh/code/python/rag/frontend
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

## 功能说明

### 用户功能

1. **登录** (`/login`)
   - 支持用户名或邮箱登录
   - 记住我功能
   - 密码找回入口
   - 科技风格的动画效果

2. **注册** (`/register`)
   - 用户名、邮箱、密码注册
   - 实时密码强度检测
   - 服务条款确认

3. **个人中心** (`/profile`)
   - 查看和编辑个人信息
   - 修改密码
   - 查看账户安全信息
   - 使用统计数据

### 管理员功能

1. **用户管理** (`/admin/users`)
   - 查看所有用户列表
   - 创建/编辑/删除用户
   - 分配用户角色
   - 启用/禁用用户账户
   - 重置用户密码

2. **角色管理** (`/admin/roles`)
   - 查看所有角色
   - 创建/编辑/删除角色
   - 配置角色权限
   - 可视化权限分类

## 权限列表

### 文档权限
- `document_upload`: 上传文档
- `document_delete`: 删除文档
- `document_read`: 读取文档

### 查询权限
- `query_ask`: 提问
- `query_history`: 查看查询历史

### 系统权限
- `system_settings`: 系统设置
- `user_management`: 用户管理
- `role_management`: 角色管理

## 角色权限矩阵

| 权限 | 管理员 | 普通用户 | 只读用户 |
|------|--------|----------|----------|
| 文档上传 | ✅ | ✅ | ❌ |
| 文档删除 | ✅ | ✅ | ❌ |
| 文档读取 | ✅ | ✅ | ✅ |
| 提问 | ✅ | ✅ | ✅ |
| 查询历史 | ✅ | ✅ | ✅ |
| 系统设置 | ✅ | ❌ | ❌ |
| 用户管理 | ✅ | ❌ | ❌ |
| 角色管理 | ✅ | ❌ | ❌ |

## API 接口说明

### 认证接口

**POST** `/api/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**POST** `/api/auth/register`
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**POST** `/api/auth/refresh`
```json
{
  "refresh_token": "your-refresh-token"
}
```

**GET** `/api/auth/me`
- Headers: `Authorization: Bearer <access_token>`

**POST** `/api/auth/change-password`
```json
{
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

### 受保护的接口

所有需要认证的接口都需要在请求头中包含:
```
Authorization: Bearer <access_token>
```

前端的 `api.js` 已经自动处理了 token 的添加和刷新。

## 技术实现

### 后端架构

- **认证服务** (`backend/app/services/auth.py`)
  - JWT token 生成和验证
  - 密码加密和验证
  - 用户认证逻辑
  - 权限检查

- **认证中间件** (`backend/app/middleware/auth.py`)
  - 获取当前用户
  - 权限检查装饰器
  - 角色检查装饰器

- **认证路由** (`backend/app/routers/auth.py`)
  - 登录、注册、登出
  - Token 刷新
  - 密码管理
  - 用户信息获取

### 前端架构

- **状态管理** (`frontend/src/store/auth.js`)
  - Pinia store 管理认证状态
  - Token 持久化存储
  - 权限检查方法

- **API 服务** (`frontend/src/services/api.js`)
  - Axios 实例配置
  - 请求拦截器(自动添加 token)
  - 响应拦截器(自动刷新 token)

- **路由守卫** (`frontend/src/router.js`)
  - 路由级别的权限检查
  - 未登录重定向到登录页
  - 权限不足提示

### 安全特性

1. **JWT Token 机制**
   - Access Token: 30分钟有效期
   - Refresh Token: 7天有效期
   - 自动 token 刷新

2. **密码安全**
   - Bcrypt 加密存储
   - 密码强度验证
   - 防暴力破解(5次失败锁定账户)

3. **数据隔离**
   - 用户只能访问自己的数据
   - 管理员可以查看所有数据

## 数据库表结构

### users (用户表)
- id: 主键
- username: 用户名(唯一)
- email: 邮箱(唯一)
- password_hash: 密码哈希
- role_id: 角色ID
- is_active: 是否激活
- last_login: 最后登录时间
- failed_login_attempts: 失败登录次数
- locked_until: 锁定到期时间
- created_at: 创建时间

### roles (角色表)
- id: 主键
- name: 角色名称(唯一)
- description: 角色描述
- permissions: 权限列表(JSON格式)

### user_documents (用户文档关联表)
- id: 主键
- user_id: 用户ID
- document_id: 文档ID
- permission_level: 权限级别
- created_at: 创建时间

### user_queries (用户查询记录表)
- id: 主键
- user_id: 用户ID
- query: 查询内容
- response: 响应内容
- created_at: 创建时间

## 注意事项

### 生产环境配置

1. **修改 JWT 密钥**
   编辑 `backend/app/services/auth.py`:
   ```python
   self.secret_key = "your-secret-key-change-in-production"
   ```
   改为:
   ```python
   self.secret_key = os.getenv("JWT_SECRET_KEY", "随机生成的强密钥")
   ```

2. **配置环境变量**
   创建 `.env` 文件:
   ```
   JWT_SECRET_KEY=your-super-secret-key-here
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

3. **修改默认密码**
   首次登录后立即修改 admin 账户的默认密码

4. **配置邮件服务**
   如需启用密码重置功能,需配置邮件服务器

## 测试账号

- **管理员账号**
  - 用户名: `admin`
  - 密码: `admin123`
  - 权限: 所有权限

运行数据库初始化后,可以使用此账号登录系统并创建其他用户。

## 常见问题

### Q: 如何添加新的权限?

A: 编辑 `backend/app/migrations/init_auth.py` 中的 `permissions` 字段,然后重新初始化数据库。

### Q: 如何自定义 Token 过期时间?

A: 编辑 `backend/app/services/auth.py`:
```python
self.access_token_expire_minutes = 30  # 修改为所需分钟数
self.refresh_token_expire_days = 7     # 修改为所需天数
```

### Q: 如何禁用某个用户?

A: 使用管理员账号登录,在用户管理页面中可以切换用户的启用/禁用状态。

### Q: Token 过期后如何处理?

A: 前端已实现自动 token 刷新机制,当 access token 过期时,会自动使用 refresh token 获取新的 access token。

## 技术支持

如遇到问题,请检查:
1. 数据库是否正确初始化
2. 后端服务是否正常运行
3. 浏览器控制台是否有错误信息
4. 后端日志是否有错误信息

---

**当前版本**: v1.0.0
**更新日期**: 2025-11-10
