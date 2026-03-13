# 第一阶段:基础架构实施详细任务

## 阶段概览

**阶段名称**: 基础架构搭建
**预计工期**: 2-3 周
**目标**: 完成数据库架构改造和领域管理基础功能
**前置条件**: 当前 RAG 系统正常运行,数据库已备份

---

## Week 1: 数据库架构改造

### 任务 1.1: 数据库备份与环境准备

**优先级**: P0 (必须完成)
**预计时间**: 0.5 天
**负责人**: 后端开发

#### 子任务清单

1. **完整数据库备份**
   ```bash
   # 执行命令
   pg_dump -U postgres -d rag_db > backup_$(date +%Y%m%d).sql

   # 验证备份文件
   - 检查文件大小 > 0
   - 检查文件内容完整性
   ```
   - [ ] 生产环境数据库备份
   - [ ] 测试环境数据库备份
   - [ ] 备份文件上传到云存储
   - [ ] 记录备份文件路径和哈希值

2. **创建开发分支**
   ```bash
   git checkout -b feature/multi-domain-phase1
   ```
   - [ ] 从 main 分支创建新特性分支
   - [ ] 推送到远程仓库

3. **准备数据库迁移环境**
   - [ ] 确认 Alembic 已安装和配置
   - [ ] 验证数据库连接正常
   - [ ] 创建迁移脚本目录结构

**交付物**:
- ✅ 数据库备份文件(带时间戳)
- ✅ Git 分支: feature/multi-domain-phase1
- ✅ 备份验证报告

---

### 任务 1.2: 扩展 documents 表结构

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 1.1

#### 子任务清单

1. **编写 Alembic 迁移脚本**

   文件: `backend/alembic/versions/xxxx_add_namespace_to_documents.py`

   ```python
   """add namespace to documents

   Revision ID: xxxx
   Revises: yyyy
   Create Date: 2025-11-17
   """

   # 迁移内容清单:
   ```

   - [ ] 添加 `namespace` 字段
     ```sql
     ALTER TABLE documents
     ADD COLUMN namespace VARCHAR(100) NOT NULL DEFAULT 'default';
     ```

   - [ ] 添加 `domain_tags` 字段
     ```sql
     ALTER TABLE documents
     ADD COLUMN domain_tags JSONB DEFAULT '{}';
     ```

   - [ ] 添加 `domain_confidence` 字段
     ```sql
     ALTER TABLE documents
     ADD COLUMN domain_confidence FLOAT DEFAULT 0.0;
     ```

   - [ ] 创建索引
     ```sql
     CREATE INDEX idx_documents_namespace
     ON documents(namespace, created_at DESC);

     CREATE INDEX idx_documents_domain_tags
     ON documents USING GIN(domain_tags);

     CREATE INDEX idx_documents_namespace_embedding
     ON documents(namespace, id) INCLUDE (embedding);
     ```

2. **编写回滚脚本**
   - [ ] 实现 downgrade() 方法
   - [ ] 测试回滚功能

3. **更新 SQLAlchemy 模型**

   文件: `backend/app/models/document.py`

   - [ ] 添加 namespace 字段到 Document 模型
     ```python
     namespace: Mapped[str] = mapped_column(
         String(100),
         nullable=False,
         default='default',
         index=True
     )
     ```

   - [ ] 添加 domain_tags 字段
     ```python
     domain_tags: Mapped[dict] = mapped_column(
         JSONB,
         default=dict,
         nullable=False
     )
     ```

   - [ ] 添加 domain_confidence 字段
     ```python
     domain_confidence: Mapped[float] = mapped_column(
         Float,
         default=0.0,
         nullable=False
     )
     ```

4. **执行迁移测试**
   - [ ] 在本地测试环境执行迁移
     ```bash
     alembic upgrade head
     ```
   - [ ] 验证字段创建成功
   - [ ] 验证索引创建成功
   - [ ] 测试回滚功能
     ```bash
     alembic downgrade -1
     alembic upgrade head
     ```
   - [ ] 验证默认值生效

5. **数据验证**
   - [ ] 查询所有文档的 namespace 字段
     ```sql
     SELECT id, namespace, domain_tags, domain_confidence
     FROM documents
     LIMIT 10;
     ```
   - [ ] 验证所有现有文档 namespace='default'
   - [ ] 验证 domain_tags 为空对象 {}
   - [ ] 验证 domain_confidence=0.0

**交付物**:
- ✅ Alembic 迁移脚本
- ✅ 更新后的 Document 模型
- ✅ 迁移测试报告
- ✅ 数据验证报告

---

### 任务 1.3: 扩展 document_chunks 表结构

**优先级**: P0
**预计时间**: 0.5 天
**依赖**: 任务 1.2

#### 子任务清单

1. **编写 Alembic 迁移脚本**

   文件: `backend/alembic/versions/xxxx_add_namespace_to_chunks.py`

   - [ ] 添加 `namespace` 字段
     ```sql
     ALTER TABLE document_chunks
     ADD COLUMN namespace VARCHAR(100) NOT NULL DEFAULT 'default';
     ```

   - [ ] 添加 `domain_tags` 字段
     ```sql
     ALTER TABLE document_chunks
     ADD COLUMN domain_tags JSONB DEFAULT '{}';
     ```

   - [ ] 创建索引
     ```sql
     CREATE INDEX idx_chunks_namespace
     ON document_chunks(namespace, document_id);

     CREATE INDEX idx_chunks_namespace_vector
     ON document_chunks(namespace)
     WHERE embedding IS NOT NULL;
     ```

   - [ ] 数据迁移:从父文档继承 namespace
     ```sql
     UPDATE document_chunks dc
     SET namespace = d.namespace,
         domain_tags = d.domain_tags
     FROM documents d
     WHERE dc.document_id = d.id;
     ```

2. **更新 SQLAlchemy 模型**

   文件: `backend/app/models/document.py`

   - [ ] 添加 namespace 字段到 DocumentChunk 模型
   - [ ] 添加 domain_tags 字段
   - [ ] 添加关系约束(namespace 继承自父文档)

3. **执行迁移和验证**
   - [ ] 执行迁移
   - [ ] 验证数据继承正确
     ```sql
     SELECT dc.id, dc.namespace, d.namespace as parent_namespace
     FROM document_chunks dc
     JOIN documents d ON dc.document_id = d.id
     WHERE dc.namespace != d.namespace;
     -- 结果应为空
     ```

**交付物**:
- ✅ Alembic 迁移脚本
- ✅ 更新后的 DocumentChunk 模型
- ✅ 数据继承验证报告

---

### 任务 1.4: 创建 knowledge_domains 配置表

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 1.3

#### 子任务清单

1. **编写 Alembic 迁移脚本**

   文件: `backend/alembic/versions/xxxx_create_knowledge_domains.py`

   - [ ] 创建 knowledge_domains 表
     ```sql
     CREATE TABLE knowledge_domains (
         id SERIAL PRIMARY KEY,
         namespace VARCHAR(100) UNIQUE NOT NULL,
         display_name VARCHAR(200) NOT NULL,
         description TEXT,
         keywords JSONB DEFAULT '[]',
         icon VARCHAR(50),
         color VARCHAR(20),
         is_active BOOLEAN DEFAULT TRUE,
         priority INTEGER DEFAULT 0,
         parent_namespace VARCHAR(100),
         permissions JSONB DEFAULT '{}',
         metadata JSONB DEFAULT '{}',
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```

   - [ ] 创建索引
     ```sql
     CREATE INDEX idx_domains_namespace ON knowledge_domains(namespace);
     CREATE INDEX idx_domains_keywords ON knowledge_domains USING GIN(keywords);
     CREATE INDEX idx_domains_active ON knowledge_domains(is_active, priority DESC);
     ```

   - [ ] 添加外键约束(可选)
     ```sql
     ALTER TABLE knowledge_domains
     ADD CONSTRAINT fk_parent_namespace
     FOREIGN KEY (parent_namespace)
     REFERENCES knowledge_domains(namespace);
     ```

   - [ ] 插入默认领域配置
     ```sql
     INSERT INTO knowledge_domains (namespace, display_name, description, keywords, icon, color, priority)
     VALUES
     ('default', '默认知识库', '未分类的通用知识', '[]', 'folder', '#999999', 0),
     ('technical_docs', '技术文档', 'API、SDK、技术配置相关文档',
      '["API", "SDK", "接口", "配置", "部署", "集成"]', 'code', '#4A90E2', 10),
     ('product_support', '产品支持', '退换货、保修、售后服务相关',
      '["退货", "换货", "保修", "发票", "售后", "维修"]', 'support', '#F5A623', 20);
     ```

2. **创建 SQLAlchemy 模型**

   文件: `backend/app/models/knowledge_domain.py` (新建)

   - [ ] 创建 KnowledgeDomain 模型类
     ```python
     class KnowledgeDomain(Base):
         __tablename__ = "knowledge_domains"

         id: Mapped[int] = mapped_column(primary_key=True)
         namespace: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
         display_name: Mapped[str] = mapped_column(String(200), nullable=False)
         description: Mapped[str] = mapped_column(Text, nullable=True)
         keywords: Mapped[list] = mapped_column(JSONB, default=list)
         icon: Mapped[str] = mapped_column(String(50), nullable=True)
         color: Mapped[str] = mapped_column(String(20), nullable=True)
         is_active: Mapped[bool] = mapped_column(Boolean, default=True)
         priority: Mapped[int] = mapped_column(Integer, default=0)
         parent_namespace: Mapped[str] = mapped_column(String(100), nullable=True)
         permissions: Mapped[dict] = mapped_column(JSONB, default=dict)
         metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
         created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
         updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
     ```

   - [ ] 添加模型方法
     - `to_dict()` - 转换为字典
     - `validate_permissions()` - 验证权限配置
     - `get_keyword_list()` - 获取关键词列表

3. **创建 Pydantic Schemas**

   文件: `backend/app/schemas/knowledge_domain.py` (新建)

   - [ ] KnowledgeDomainBase
   - [ ] KnowledgeDomainCreate
   - [ ] KnowledgeDomainUpdate
   - [ ] KnowledgeDomainResponse
   - [ ] KnowledgeDomainListResponse

4. **执行迁移和验证**
   - [ ] 执行迁移
   - [ ] 验证表创建成功
   - [ ] 验证默认数据插入成功
     ```sql
     SELECT * FROM knowledge_domains ORDER BY priority DESC;
     ```
   - [ ] 验证索引创建成功

**交付物**:
- ✅ Alembic 迁移脚本
- ✅ KnowledgeDomain 模型
- ✅ Pydantic Schemas
- ✅ 默认领域配置数据

---

### 任务 1.5: 创建 domain_routing_rules 表

**优先级**: P1 (重要但非紧急)
**预计时间**: 0.5 天
**依赖**: 任务 1.4

#### 子任务清单

1. **编写 Alembic 迁移脚本**

   文件: `backend/alembic/versions/xxxx_create_domain_routing_rules.py`

   - [ ] 创建 domain_routing_rules 表
     ```sql
     CREATE TABLE domain_routing_rules (
         id SERIAL PRIMARY KEY,
         rule_name VARCHAR(200) NOT NULL,
         rule_type VARCHAR(50) NOT NULL,
         pattern TEXT NOT NULL,
         target_namespace VARCHAR(100) NOT NULL,
         confidence_threshold FLOAT DEFAULT 0.7,
         priority INTEGER DEFAULT 0,
         is_active BOOLEAN DEFAULT TRUE,
         metadata JSONB DEFAULT '{}',
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (target_namespace) REFERENCES knowledge_domains(namespace)
     );
     ```

   - [ ] 创建索引
     ```sql
     CREATE INDEX idx_rules_type ON domain_routing_rules(rule_type, is_active);
     CREATE INDEX idx_rules_priority ON domain_routing_rules(priority DESC);
     ```

   - [ ] 插入示例规则
     ```sql
     INSERT INTO domain_routing_rules (rule_name, rule_type, pattern, target_namespace, priority)
     VALUES
     ('API关键词规则', 'keyword', 'API|接口|SDK', 'technical_docs', 10),
     ('退货关键词规则', 'keyword', '退货|换货|退款', 'product_support', 10);
     ```

2. **创建 SQLAlchemy 模型**

   文件: `backend/app/models/domain_routing_rule.py` (新建)

   - [ ] 创建 DomainRoutingRule 模型类
   - [ ] 添加模型方法
     - `match(query)` - 匹配查询
     - `get_compiled_pattern()` - 获取编译后的正则

3. **创建 Pydantic Schemas**

   文件: `backend/app/schemas/domain_routing_rule.py` (新建)

   - [ ] DomainRoutingRuleBase
   - [ ] DomainRoutingRuleCreate
   - [ ] DomainRoutingRuleUpdate
   - [ ] DomainRoutingRuleResponse

**交付物**:
- ✅ Alembic 迁移脚本
- ✅ DomainRoutingRule 模型
- ✅ Pydantic Schemas

---

### 任务 1.6: 数据库单元测试

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 1.5

#### 子任务清单

1. **编写模型测试**

   文件: `backend/tests/models/test_knowledge_domain.py` (新建)

   - [ ] 测试 KnowledgeDomain 创建
   - [ ] 测试唯一约束(namespace)
   - [ ] 测试默认值
   - [ ] 测试 JSONB 字段(keywords, permissions, metadata)
   - [ ] 测试外键约束(parent_namespace)
   - [ ] 测试软删除(is_active)

2. **编写迁移测试**

   文件: `backend/tests/migrations/test_phase1_migrations.py` (新建)

   - [ ] 测试迁移执行(upgrade)
   - [ ] 测试迁移回滚(downgrade)
   - [ ] 测试数据完整性
   - [ ] 测试索引存在性

3. **编写集成测试**

   文件: `backend/tests/integration/test_database_schema.py`

   - [ ] 测试 documents 和 knowledge_domains 的关联
   - [ ] 测试 document_chunks 继承 namespace
   - [ ] 测试跨表查询性能

4. **执行测试**
   ```bash
   pytest backend/tests/models/test_knowledge_domain.py -v
   pytest backend/tests/migrations/ -v
   pytest backend/tests/integration/test_database_schema.py -v
   ```

   - [ ] 所有测试通过
   - [ ] 测试覆盖率 > 80%
   - [ ] 生成测试报告

**交付物**:
- ✅ 单元测试代码
- ✅ 测试报告(覆盖率 > 80%)
- ✅ 测试通过截图

---

## Week 2-3: 领域管理功能开发

### 任务 2.1: 领域管理 Service 层

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 1.6

#### 子任务清单

1. **创建 DomainService 类**

   文件: `backend/app/services/domain_service.py` (新建)

   - [ ] 实现 `get_all_domains()` 方法
     ```python
     async def get_all_domains(
         self,
         include_inactive: bool = False,
         order_by: str = "priority"
     ) -> List[KnowledgeDomain]
     ```

   - [ ] 实现 `get_domain_by_namespace()` 方法
     ```python
     async def get_domain_by_namespace(
         self,
         namespace: str
     ) -> Optional[KnowledgeDomain]
     ```

   - [ ] 实现 `create_domain()` 方法
     ```python
     async def create_domain(
         self,
         domain_data: KnowledgeDomainCreate
     ) -> KnowledgeDomain
     ```
     - 验证 namespace 唯一性
     - 验证 parent_namespace 存在性
     - 验证 keywords 格式
     - 验证 permissions 格式

   - [ ] 实现 `update_domain()` 方法
     ```python
     async def update_domain(
         self,
         namespace: str,
         domain_data: KnowledgeDomainUpdate
     ) -> KnowledgeDomain
     ```

   - [ ] 实现 `delete_domain()` 方法
     ```python
     async def delete_domain(
         self,
         namespace: str,
         force: bool = False,
         migrate_to: Optional[str] = None
     ) -> bool
     ```
     - 检查是否有关联文档
     - 如果 force=False 且有文档,抛出异常
     - 如果 migrate_to 提供,迁移文档
     - 软删除(is_active=False)或硬删除

   - [ ] 实现 `get_domain_stats()` 方法
     ```python
     async def get_domain_stats(
         self,
         namespace: str
     ) -> Dict[str, Any]
     ```
     返回:
     - document_count: 文档数量
     - chunk_count: 分块数量
     - avg_confidence: 平均分类置信度
     - recent_uploads: 最近上传数量(7天)

2. **异常处理**

   文件: `backend/app/exceptions/domain_exceptions.py` (新建)

   - [ ] DomainNotFoundException
   - [ ] DomainAlreadyExistsException
   - [ ] DomainHasDocumentsException
   - [ ] InvalidDomainConfigException

3. **Service 单元测试**

   文件: `backend/tests/services/test_domain_service.py` (新建)

   - [ ] 测试所有 CRUD 方法
   - [ ] 测试异常情况
   - [ ] 测试边界条件
   - [ ] 使用 Mock 数据库

**交付物**:
- ✅ DomainService 实现
- ✅ 异常类定义
- ✅ 单元测试(覆盖率 > 85%)

---

### 任务 2.2: 领域管理 API 端点

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 2.1

#### 子任务清单

1. **创建 Router**

   文件: `backend/app/routers/knowledge_domains.py` (新建)

   - [ ] **GET /api/knowledge-domains** - 获取领域列表
     ```python
     @router.get("/knowledge-domains", response_model=List[KnowledgeDomainResponse])
     async def get_domains(
         include_inactive: bool = False,
         order_by: str = "priority",
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """
         获取所有领域配置

         参数:
         - include_inactive: 是否包含禁用的领域
         - order_by: 排序字段(priority/created_at/name)
         """
     ```

   - [ ] **GET /api/knowledge-domains/{namespace}** - 获取单个领域
     ```python
     @router.get("/knowledge-domains/{namespace}", response_model=KnowledgeDomainResponse)
     async def get_domain(
         namespace: str,
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """获取指定领域详情"""
     ```

   - [ ] **POST /api/knowledge-domains** - 创建领域
     ```python
     @router.post("/knowledge-domains", response_model=KnowledgeDomainResponse, status_code=201)
     async def create_domain(
         domain: KnowledgeDomainCreate,
         db: Session = Depends(get_db),
         current_user: User = Depends(require_admin)  # 需要管理员权限
     ):
         """
         创建新领域

         权限: 需要管理员权限
         """
     ```

   - [ ] **PUT /api/knowledge-domains/{namespace}** - 更新领域
     ```python
     @router.put("/knowledge-domains/{namespace}", response_model=KnowledgeDomainResponse)
     async def update_domain(
         namespace: str,
         domain: KnowledgeDomainUpdate,
         db: Session = Depends(get_db),
         current_user: User = Depends(require_admin)
     ):
         """更新领域配置"""
     ```

   - [ ] **DELETE /api/knowledge-domains/{namespace}** - 删除领域
     ```python
     @router.delete("/knowledge-domains/{namespace}", status_code=204)
     async def delete_domain(
         namespace: str,
         force: bool = False,
         migrate_to: Optional[str] = None,
         db: Session = Depends(get_db),
         current_user: User = Depends(require_admin)
     ):
         """
         删除领域

         参数:
         - force: 强制删除(即使有关联文档)
         - migrate_to: 迁移目标领域
         """
     ```

   - [ ] **GET /api/knowledge-domains/{namespace}/stats** - 获取领域统计
     ```python
     @router.get("/knowledge-domains/{namespace}/stats")
     async def get_domain_stats(
         namespace: str,
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """获取领域统计信息"""
     ```

2. **注册 Router**

   文件: `backend/app/main.py`

   - [ ] 导入 knowledge_domains router
   - [ ] 注册到 app
     ```python
     from app.routers import knowledge_domains
     app.include_router(knowledge_domains.router, prefix="/api", tags=["Knowledge Domains"])
     ```

3. **API 文档**

   - [ ] 添加详细的 docstring
   - [ ] 添加请求/响应示例
   - [ ] 验证 Swagger UI 显示正常

4. **API 集成测试**

   文件: `backend/tests/routers/test_knowledge_domains.py` (新建)

   - [ ] 测试所有端点
   - [ ] 测试权限控制(管理员 vs 普通用户)
   - [ ] 测试参数验证
   - [ ] 测试错误响应

**交付物**:
- ✅ API Router 实现
- ✅ API 集成测试
- ✅ Swagger API 文档

---

### 任务 2.3: 文档上传支持 namespace

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 2.2

#### 子任务清单

1. **修改上传 API**

   文件: `backend/app/routers/upload.py`

   - [ ] 添加 `namespace` 参数(可选,默认 'default')
     ```python
     @router.post("/upload")
     async def upload_document(
         file: UploadFile,
         namespace: str = Form('default'),
         auto_classify: bool = Form(False),
         domain_tags: Optional[str] = Form(None),  # JSON 字符串
         ...
     ):
     ```

   - [ ] 验证 namespace 存在性
     ```python
     domain = await domain_service.get_domain_by_namespace(namespace)
     if not domain or not domain.is_active:
         raise HTTPException(404, "领域不存在或已禁用")
     ```

   - [ ] 保存文档时设置 namespace
     ```python
     document = Document(
         filename=file.filename,
         namespace=namespace,
         domain_tags=json.loads(domain_tags) if domain_tags else {},
         ...
     )
     ```

   - [ ] 保存文档块时继承 namespace
     ```python
     chunk = DocumentChunk(
         document_id=document.id,
         namespace=document.namespace,
         domain_tags=document.domain_tags,
         ...
     )
     ```

2. **修改响应格式**

   - [ ] 在响应中包含 namespace 信息
     ```python
     return {
         "document_id": document.id,
         "namespace": document.namespace,
         "domain_display_name": domain.display_name,
         "domain_color": domain.color,
         ...
     }
     ```

3. **更新前端上传组件** (简单修改,详细开发在后续任务)

   文件: `frontend/src/views/Upload.vue`

   - [ ] 添加领域选择下拉框
     ```vue
     <el-select v-model="uploadForm.namespace" placeholder="选择领域">
       <el-option
         v-for="domain in domains"
         :key="domain.namespace"
         :label="domain.display_name"
         :value="domain.namespace"
       />
     </el-select>
     ```

4. **测试**
   - [ ] 测试上传到不同领域
   - [ ] 验证 namespace 正确保存
   - [ ] 验证文档块继承 namespace

**交付物**:
- ✅ 修改后的上传 API
- ✅ 简单的前端领域选择器
- ✅ 上传测试报告

---

### 任务 2.4: 前端领域管理页面

**优先级**: P0
**预计时间**: 3 天
**依赖**: 任务 2.2

#### 子任务清单

1. **创建领域管理页面**

   文件: `frontend/src/views/admin/KnowledgeDomains.vue` (新建)

   - [ ] **页面布局**
     - 顶部工具栏(新建按钮、刷新按钮)
     - 领域列表表格
     - 分页组件

   - [ ] **领域列表表格**
     ```vue
     <el-table :data="domains" stripe>
       <el-table-column prop="namespace" label="命名空间" width="150" />
       <el-table-column prop="display_name" label="显示名称" width="180" />
       <el-table-column prop="description" label="描述" />
       <el-table-column label="图标" width="80">
         <template #default="{ row }">
           <el-icon :color="row.color" :size="24">
             <component :is="row.icon" />
           </el-icon>
         </template>
       </el-table-column>
       <el-table-column label="文档数" width="100">
         <template #default="{ row }">
           {{ row.document_count || 0 }}
         </template>
       </el-table-column>
       <el-table-column label="状态" width="100">
         <template #default="{ row }">
           <el-switch
             v-model="row.is_active"
             @change="handleToggleActive(row)"
           />
         </template>
       </el-table-column>
       <el-table-column label="优先级" width="100">
         <template #default="{ row }">
           {{ row.priority }}
         </template>
       </el-table-column>
       <el-table-column label="操作" width="200" fixed="right">
         <template #default="{ row }">
           <el-button size="small" @click="handleEdit(row)">编辑</el-button>
           <el-button size="small" @click="handleViewStats(row)">统计</el-button>
           <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
         </template>
       </el-table-column>
     </el-table>
     ```

2. **创建/编辑领域对话框**

   - [ ] **对话框组件**
     ```vue
     <el-dialog
       :title="dialogMode === 'create' ? '创建领域' : '编辑领域'"
       v-model="dialogVisible"
       width="600px"
     >
       <el-form :model="domainForm" :rules="domainRules" ref="domainFormRef">
         <el-form-item label="命名空间" prop="namespace">
           <el-input v-model="domainForm.namespace" :disabled="dialogMode === 'edit'" />
         </el-form-item>
         <el-form-item label="显示名称" prop="display_name">
           <el-input v-model="domainForm.display_name" />
         </el-form-item>
         <el-form-item label="描述" prop="description">
           <el-input v-model="domainForm.description" type="textarea" :rows="3" />
         </el-form-item>
         <el-form-item label="图标" prop="icon">
           <el-select v-model="domainForm.icon" placeholder="选择图标">
             <el-option label="代码" value="code" />
             <el-option label="支持" value="support" />
             <el-option label="文档" value="document" />
             <!-- 更多图标选项 -->
           </el-select>
         </el-form-item>
         <el-form-item label="颜色" prop="color">
           <el-color-picker v-model="domainForm.color" />
         </el-form-item>
         <el-form-item label="关键词" prop="keywords">
           <el-tag
             v-for="(keyword, index) in domainForm.keywords"
             :key="index"
             closable
             @close="handleRemoveKeyword(index)"
           >
             {{ keyword }}
           </el-tag>
           <el-input
             v-model="newKeyword"
             size="small"
             style="width: 120px"
             @keyup.enter="handleAddKeyword"
             placeholder="添加关键词"
           />
         </el-form-item>
         <el-form-item label="优先级" prop="priority">
           <el-input-number v-model="domainForm.priority" :min="0" :max="100" />
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="dialogVisible = false">取消</el-button>
         <el-button type="primary" @click="handleSubmit">确定</el-button>
       </template>
     </el-dialog>
     ```

3. **领域统计对话框**

   - [ ] **统计信息展示**
     ```vue
     <el-dialog title="领域统计" v-model="statsDialogVisible" width="500px">
       <el-descriptions :column="2" border>
         <el-descriptions-item label="文档数量">
           {{ currentStats.document_count }}
         </el-descriptions-item>
         <el-descriptions-item label="分块数量">
           {{ currentStats.chunk_count }}
         </el-descriptions-item>
         <el-descriptions-item label="平均置信度">
           {{ (currentStats.avg_confidence * 100).toFixed(1) }}%
         </el-descriptions-item>
         <el-descriptions-item label="最近上传(7天)">
           {{ currentStats.recent_uploads }}
         </el-descriptions-item>
       </el-descriptions>
     </el-dialog>
     ```

4. **数据交互逻辑**

   - [ ] 加载领域列表
     ```javascript
     const loadDomains = async () => {
       try {
         loading.value = true
         const response = await getDomains({ include_inactive: false })
         domains.value = response.data
       } catch (error) {
         ElMessage.error('加载领域列表失败')
       } finally {
         loading.value = false
       }
     }
     ```

   - [ ] 创建领域
     ```javascript
     const handleCreate = async () => {
       await domainFormRef.value.validate()
       try {
         await createDomain(domainForm.value)
         ElMessage.success('创建成功')
         dialogVisible.value = false
         loadDomains()
       } catch (error) {
         ElMessage.error('创建失败: ' + error.message)
       }
     }
     ```

   - [ ] 更新领域
   - [ ] 删除领域(带确认)
   - [ ] 切换启用状态
   - [ ] 查看统计信息

5. **路由配置**

   文件: `frontend/src/router/index.js`

   - [ ] 添加路由
     ```javascript
     {
       path: '/admin/knowledge-domains',
       name: 'KnowledgeDomains',
       component: () => import('@/views/admin/KnowledgeDomains.vue'),
       meta: {
         requiresAuth: true,
         requiresAdmin: true,
         title: '领域管理'
       }
     }
     ```

6. **侧边栏菜单**

   文件: `frontend/src/layouts/AdminLayout.vue`

   - [ ] 添加菜单项
     ```vue
     <el-menu-item index="/admin/knowledge-domains">
       <el-icon><Setting /></el-icon>
       <span>领域管理</span>
     </el-menu-item>
     ```

**交付物**:
- ✅ 领域管理页面
- ✅ 创建/编辑对话框
- ✅ 统计信息对话框
- ✅ 路由和菜单配置

---

### 任务 2.5: API Service 层(前端)

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 2.2

#### 子任务清单

1. **创建 API Service**

   文件: `frontend/src/services/knowledgeDomains.js` (新建)

   - [ ] **getDomains()** - 获取领域列表
     ```javascript
     export async function getDomains(params = {}) {
       return request({
         url: '/api/knowledge-domains',
         method: 'get',
         params
       })
     }
     ```

   - [ ] **getDomainByNamespace()** - 获取单个领域
     ```javascript
     export async function getDomainByNamespace(namespace) {
       return request({
         url: `/api/knowledge-domains/${namespace}`,
         method: 'get'
       })
     }
     ```

   - [ ] **createDomain()** - 创建领域
     ```javascript
     export async function createDomain(data) {
       return request({
         url: '/api/knowledge-domains',
         method: 'post',
         data
       })
     }
     ```

   - [ ] **updateDomain()** - 更新领域
     ```javascript
     export async function updateDomain(namespace, data) {
       return request({
         url: `/api/knowledge-domains/${namespace}`,
         method: 'put',
         data
       })
     }
     ```

   - [ ] **deleteDomain()** - 删除领域
     ```javascript
     export async function deleteDomain(namespace, params = {}) {
       return request({
         url: `/api/knowledge-domains/${namespace}`,
         method: 'delete',
         params
       })
     }
     ```

   - [ ] **getDomainStats()** - 获取领域统计
     ```javascript
     export async function getDomainStats(namespace) {
       return request({
         url: `/api/knowledge-domains/${namespace}/stats`,
         method: 'get'
       })
     }
     ```

**交付物**:
- ✅ API Service 文件
- ✅ 完整的 API 方法

---

### 任务 2.6: 领域选择器组件

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 2.5

#### 子任务清单

1. **创建 DomainSelector 组件**

   文件: `frontend/src/components/domain/DomainSelector.vue` (新建)

   - [ ] **组件模板**
     ```vue
     <template>
       <div class="domain-selector">
         <el-select
           v-model="selectedNamespace"
           placeholder="选择领域"
           :clearable="clearable"
           @change="handleChange"
         >
           <el-option
             v-for="domain in domains"
             :key="domain.namespace"
             :label="domain.display_name"
             :value="domain.namespace"
           >
             <div class="domain-option">
               <el-icon :color="domain.color" :size="18">
                 <component :is="domain.icon" />
               </el-icon>
               <span class="domain-name">{{ domain.display_name }}</span>
               <el-tag size="small" type="info">
                 {{ domain.document_count || 0 }} 文档
               </el-tag>
             </div>
           </el-option>
         </el-select>
       </div>
     </template>
     ```

   - [ ] **组件逻辑**
     ```javascript
     <script setup>
     import { ref, onMounted, watch } from 'vue'
     import { getDomains } from '@/services/knowledgeDomains'

     const props = defineProps({
       modelValue: String,
       clearable: {
         type: Boolean,
         default: true
       },
       includeInactive: {
         type: Boolean,
         default: false
       }
     })

     const emit = defineEmits(['update:modelValue', 'change'])

     const selectedNamespace = ref(props.modelValue)
     const domains = ref([])

     const loadDomains = async () => {
       try {
         const response = await getDomains({
           include_inactive: props.includeInactive
         })
         domains.value = response.data
       } catch (error) {
         console.error('加载领域失败', error)
       }
     }

     const handleChange = (value) => {
       emit('update:modelValue', value)
       const domain = domains.value.find(d => d.namespace === value)
       emit('change', domain)
     }

     watch(() => props.modelValue, (newVal) => {
       selectedNamespace.value = newVal
     })

     onMounted(() => {
       loadDomains()
     })
     </script>
     ```

   - [ ] **组件样式**
     ```vue
     <style scoped>
     .domain-option {
       display: flex;
       align-items: center;
       gap: 8px;
     }

     .domain-name {
       flex: 1;
     }
     </style>
     ```

2. **创建 DomainBadge 组件**

   文件: `frontend/src/components/domain/DomainBadge.vue` (新建)

   - [ ] **徽章组件**
     ```vue
     <template>
       <el-tag
         :color="domain.color"
         :style="{
           backgroundColor: domain.color + '20',
           borderColor: domain.color,
           color: domain.color
         }"
         @click="handleClick"
       >
         <el-icon :size="14">
           <component :is="domain.icon" />
         </el-icon>
         <span>{{ domain.display_name }}</span>
         <span v-if="showConfidence && confidence" class="confidence">
           {{ (confidence * 100).toFixed(0) }}%
         </span>
       </el-tag>
     </template>
     ```

3. **使用组件**

   - [ ] 在文档上传页面使用 DomainSelector
   - [ ] 在查询页面使用 DomainSelector
   - [ ] 在文档列表使用 DomainBadge

**交付物**:
- ✅ DomainSelector 组件
- ✅ DomainBadge 组件
- ✅ 组件使用示例

---

### 任务 2.7: 集成测试与文档

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 2.6

#### 子任务清单

1. **端到端测试**

   - [ ] 测试创建领域
   - [ ] 测试上传文档到指定领域
   - [ ] 测试领域列表显示
   - [ ] 测试领域编辑
   - [ ] 测试领域删除(有文档 vs 无文档)
   - [ ] 测试领域启用/禁用

2. **性能测试**

   - [ ] 测试领域列表加载性能
   - [ ] 测试大量领域下的选择器性能
   - [ ] 测试数据库查询性能(EXPLAIN ANALYZE)

3. **编写用户文档**

   文件: `docs/user/DOMAIN_MANAGEMENT_GUIDE.md` (新建)

   - [ ] 领域管理功能介绍
   - [ ] 创建和配置领域
   - [ ] 上传文档到指定领域
   - [ ] 领域权限管理
   - [ ] 常见问题解答

4. **编写开发文档**

   文件: `docs/developer/PHASE1_IMPLEMENTATION.md` (新建)

   - [ ] 数据库架构说明
   - [ ] API 接口文档
   - [ ] 前端组件使用指南
   - [ ] 扩展和自定义

5. **创建 Postman 测试集合**

   - [ ] 导出所有领域管理 API
   - [ ] 添加测试用例
   - [ ] 添加环境变量

**交付物**:
- ✅ 端到端测试报告
- ✅ 性能测试报告
- ✅ 用户使用文档
- ✅ 开发者文档
- ✅ Postman 测试集合

---

## 阶段验收标准

### 功能验收

- [ ] ✅ 数据库迁移成功,所有表和索引创建完成
- [ ] ✅ 默认领域(default, technical_docs, product_support)配置完成
- [ ] ✅ 所有现有文档自动标记为 'default' 命名空间
- [ ] ✅ 领域管理 CRUD API 全部正常工作
- [ ] ✅ 前端领域管理页面可用,UI 友好
- [ ] ✅ 文档上传支持选择领域
- [ ] ✅ DomainSelector 组件可在多处复用

### 质量验收

- [ ] ✅ 单元测试覆盖率 > 80%
- [ ] ✅ 集成测试全部通过
- [ ] ✅ 代码 Review 完成,无严重问题
- [ ] ✅ API 文档完整,Swagger UI 可访问
- [ ] ✅ 用户文档和开发文档齐全

### 性能验收

- [ ] ✅ 领域列表查询 < 100ms
- [ ] ✅ 领域统计查询 < 500ms
- [ ] ✅ 数据库迁移 < 5 分钟(10万文档)

### 安全验收

- [ ] ✅ 权限控制正确(管理员 vs 普通用户)
- [ ] ✅ 输入验证完整(namespace 格式、SQL 注入防护)
- [ ] ✅ 无敏感信息泄露

---

## 风险与应对

### 风险 1: 数据库迁移失败

**概率**: 低
**影响**: 高

**应对措施**:
- 迁移前完整备份
- 先在测试环境验证
- 准备回滚脚本
- 分步执行,每步验证

### 风险 2: 现有功能受影响

**概率**: 中
**影响**: 高

**应对措施**:
- 向后兼容:默认 namespace='default'
- 保留原有 API,逐步迁移
- 全面回归测试
- 灰度发布

### 风险 3: 前端组件兼容性

**概率**: 低
**影响**: 中

**应对措施**:
- 使用成熟的 Element Plus 组件
- 兼容性测试(Chrome、Firefox、Safari)
- 渐进增强,降级方案

---

## 下一阶段预告

完成第一阶段后,将进入**第二阶段:智能分类系统**,主要任务:

1. 实现关键词分类器
2. 集成 LLM 分类器
3. 开发混合分类器
4. 分类效果测试和优化

第一阶段为后续智能分类奠定了坚实的数据基础。
