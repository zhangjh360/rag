# 第三阶段:检索集成详细任务

## 阶段概览

**阶段名称**: 检索集成与优化
**预计工期**: 2 周
**目标**: 实现单领域和跨领域检索,优化检索效果
**前置条件**: 第二阶段完成,智能分类系统可用

---

## Week 1: 单领域检索实现

### 任务 6.1: 向量检索服务重构

**优先级**: P0
**预计时间**: 2 天
**依赖**: 第二阶段完成

#### 子任务清单

1. **重构 VectorRetrieval 服务**

   文件: `backend/app/services/vector_retrieval.py`

   - [ ] **添加 namespace 过滤支持**
     ```python
     class VectorRetrieval:
         """向量检索服务"""

         async def search_by_namespace(
             self,
             query: str,
             namespace: str,
             top_k: int = 10,
             filters: Optional[Dict] = None
         ) -> List[DocumentChunk]:
             """
             在指定领域内进行向量检索

             Args:
                 query: 查询文本
                 namespace: 领域命名空间
                 top_k: 返回结果数量
                 filters: 额外过滤条件

             Returns:
                 List[DocumentChunk]: 排序后的文档块
             """

             # 1. 生成 query embedding
             query_embedding = await self.embedding_service.get_embedding(query)

             # 2. 向量检索(带 namespace 过滤)
             chunks = self.db.query(DocumentChunk).filter(
                 DocumentChunk.namespace == namespace,
                 DocumentChunk.embedding.isnot(None)
             )

             # 3. 应用额外过滤条件
             if filters:
                 if 'document_id' in filters:
                     chunks = chunks.filter(DocumentChunk.document_id == filters['document_id'])
                 if 'date_range' in filters:
                     start, end = filters['date_range']
                     chunks = chunks.join(Document).filter(
                         Document.created_at.between(start, end)
                     )

             # 4. 计算相似度
             all_chunks = chunks.all()

             scored_chunks = []
             for chunk in all_chunks:
                 similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                 scored_chunks.append((chunk, similarity))

             # 5. 排序并返回 Top-K
             scored_chunks.sort(key=lambda x: x[1], reverse=True)
             top_chunks = [chunk for chunk, score in scored_chunks[:top_k]]

             return top_chunks

         def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
             """计算余弦相似度"""
             import numpy as np
             vec1 = np.array(vec1)
             vec2 = np.array(vec2)
             return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
     ```

   - [ ] **优化:使用 PostgreSQL 向量扩展(可选)**
     ```python
     # 如果使用 pgvector
     async def search_by_namespace_pgvector(
         self,
         query: str,
         namespace: str,
         top_k: int = 10
     ) -> List[DocumentChunk]:
         """使用 pgvector 加速检索"""

         query_embedding = await self.embedding_service.get_embedding(query)

         # pgvector 查询
         chunks = self.db.query(DocumentChunk).filter(
             DocumentChunk.namespace == namespace
         ).order_by(
             DocumentChunk.embedding.cosine_distance(query_embedding)
         ).limit(top_k).all()

         return chunks
     ```

2. **BM25 关键词检索**

   文件: `backend/app/services/bm25_retrieval.py` (新建)

   - [ ] **实现 BM25 检索器**
     ```python
     from rank_bm25 import BM25Okapi
     import jieba

     class BM25Retrieval:
         """BM25 关键词检索"""

         def __init__(self, db: Session):
             self.db = db
             self._corpus = {}
             self._bm25 = {}

         async def initialize_for_namespace(self, namespace: str):
             """为指定领域初始化 BM25 索引"""

             # 1. 加载领域内所有文档块
             chunks = self.db.query(DocumentChunk).filter(
                 DocumentChunk.namespace == namespace
             ).all()

             if len(chunks) == 0:
                 return

             # 2. 分词构建语料库
             corpus = []
             chunk_ids = []

             for chunk in chunks:
                 tokens = list(jieba.cut(chunk.content))
                 corpus.append(tokens)
                 chunk_ids.append(chunk.id)

             # 3. 构建 BM25 索引
             self._corpus[namespace] = chunk_ids
             self._bm25[namespace] = BM25Okapi(corpus)

         async def search_by_namespace(
             self,
             query: str,
             namespace: str,
             top_k: int = 10
         ) -> List[Tuple[DocumentChunk, float]]:
             """BM25 检索"""

             # 1. 确保索引已初始化
             if namespace not in self._bm25:
                 await self.initialize_for_namespace(namespace)

             if namespace not in self._bm25 or len(self._corpus[namespace]) == 0:
                 return []

             # 2. 分词查询
             query_tokens = list(jieba.cut(query))

             # 3. BM25 评分
             scores = self._bm25[namespace].get_scores(query_tokens)

             # 4. 排序并获取 Top-K
             chunk_ids = self._corpus[namespace]
             scored_chunks = list(zip(chunk_ids, scores))
             scored_chunks.sort(key=lambda x: x[1], reverse=True)

             top_chunk_ids = [chunk_id for chunk_id, score in scored_chunks[:top_k]]

             # 5. 查询数据库
             chunks = self.db.query(DocumentChunk).filter(
                 DocumentChunk.id.in_(top_chunk_ids)
             ).all()

             # 6. 恢复排序
             chunk_dict = {c.id: c for c in chunks}
             result = [(chunk_dict[cid], score) for cid, score in scored_chunks[:top_k] if cid in chunk_dict]

             return result
     ```

3. **混合检索(RRF融合)**

   文件: `backend/app/services/hybrid_retrieval.py` (新建)

   - [ ] **RRF 融合算法**
     ```python
     class HybridRetrieval:
         """混合检索(向量 + BM25)"""

         def __init__(self, db: Session):
             self.db = db
             self.vector_retrieval = VectorRetrieval(db)
             self.bm25_retrieval = BM25Retrieval(db)

         async def search_by_namespace(
             self,
             query: str,
             namespace: str,
             top_k: int = 10,
             alpha: float = 0.5  # 向量检索权重
         ) -> List[DocumentChunk]:
             """
             混合检索

             Args:
                 alpha: 向量检索权重(0.0-1.0)
                        0.0 = 纯BM25, 1.0 = 纯向量, 0.5 = 均衡
             """

             # 1. 并行执行两种检索
             vector_results, bm25_results = await asyncio.gather(
                 self.vector_retrieval.search_by_namespace(query, namespace, top_k * 2),
                 self.bm25_retrieval.search_by_namespace(query, namespace, top_k * 2)
             )

             # 2. RRF 融合
             # RRF Score = sum(1 / (k + rank))
             k = 60  # RRF 参数
             scores = {}

             # 向量检索得分
             for rank, chunk in enumerate(vector_results, 1):
                 chunk_id = chunk.id
                 scores[chunk_id] = scores.get(chunk_id, 0) + alpha * (1 / (k + rank))

             # BM25 得分
             for rank, (chunk, _) in enumerate(bm25_results, 1):
                 chunk_id = chunk.id
                 scores[chunk_id] = scores.get(chunk_id, 0) + (1 - alpha) * (1 / (k + rank))

             # 3. 排序
             sorted_chunk_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

             # 4. 查询完整数据
             top_chunk_ids = sorted_chunk_ids[:top_k]
             chunks = self.db.query(DocumentChunk).filter(
                 DocumentChunk.id.in_(top_chunk_ids)
             ).all()

             # 5. 恢复排序
             chunk_dict = {c.id: c for c in chunks}
             result = [chunk_dict[cid] for cid in top_chunk_ids if cid in chunk_dict]

             return result
     ```

4. **单元测试**

   文件: `backend/tests/services/test_retrieval.py`

   - [ ] 测试向量检索(带 namespace)
   - [ ] 测试 BM25 检索
   - [ ] 测试混合检索
   - [ ] 测试性能(延迟、准确率)

**交付物**:
- ✅ 重构后的 VectorRetrieval
- ✅ BM25Retrieval 实现
- ✅ HybridRetrieval 实现
- ✅ 单元测试

---

### 任务 6.2: 查询 API 完整实现

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 6.1

#### 子任务清单

1. **完善查询 API**

   文件: `backend/app/routers/query.py`

   - [ ] **完整实现查询流程**
     ```python
     @router.post("/query/v2", response_model=QueryResponse)
     async def query_documents_v2(
         request: QueryRequest,
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """
         查询文档 v2(支持自动分类和领域检索)

         请求参数:
         - query: 查询内容
         - namespace: 指定领域(可选)
         - retrieval_mode: 'single'/'cross'/'auto'
         - top_k: 返回结果数量
         - retrieval_method: 'vector'/'bm25'/'hybrid'
         - filters: 过滤条件
         """

         # === 步骤 1: 领域分类 ===
         namespace = request.namespace
         retrieval_mode = request.retrieval_mode or 'auto'
         classification_result = None

         if not namespace or retrieval_mode == 'auto':
             classifier = await ClassifierFactory.get_default_classifier(db)
             classification_result = await classifier.classify(
                 query=request.query,
                 context={
                     'user_id': current_user.id,
                     'session_id': request.session_id
                 }
             )

             namespace = classification_result.namespace

             # 判断是否需要跨领域检索
             if classification_result.fallback_to_cross_domain:
                 retrieval_mode = 'cross'
             else:
                 retrieval_mode = 'single'

         # === 步骤 2: 单领域检索 ===
         if retrieval_mode == 'single':
             results = await _single_domain_retrieval(
                 query=request.query,
                 namespace=namespace,
                 top_k=request.top_k,
                 method=request.retrieval_method,
                 filters=request.filters,
                 db=db
             )

         # === 步骤 3: 跨领域检索 ===
         elif retrieval_mode == 'cross':
             results = await _cross_domain_retrieval(
                 query=request.query,
                 namespaces=request.namespaces or None,  # None = 所有领域
                 top_k=request.top_k,
                 method=request.retrieval_method,
                 db=db
             )

         # === 步骤 4: 构建响应 ===
         response = QueryResponse(
             query_id=str(uuid.uuid4()),
             query=request.query,
             domain_classification=classification_result.to_dict() if classification_result else None,
             retrieval_mode=retrieval_mode,
             results=[_chunk_to_result(chunk, namespace) for chunk in results],
             retrieval_stats={
                 'total_candidates': len(results),
                 'method': request.retrieval_method,
                 'latency_ms': 0  # 计算实际延迟
             }
         )

         return response

     async def _single_domain_retrieval(
         query: str,
         namespace: str,
         top_k: int,
         method: str,
         filters: Optional[Dict],
         db: Session
     ) -> List[DocumentChunk]:
         """单领域检索"""

         if method == 'vector':
             retrieval = VectorRetrieval(db)
             return await retrieval.search_by_namespace(query, namespace, top_k, filters)

         elif method == 'bm25':
             retrieval = BM25Retrieval(db)
             results = await retrieval.search_by_namespace(query, namespace, top_k)
             return [chunk for chunk, score in results]

         elif method == 'hybrid':
             retrieval = HybridRetrieval(db)
             return await retrieval.search_by_namespace(query, namespace, top_k)

         else:
             raise ValueError(f"未知的检索方法: {method}")

     def _chunk_to_result(chunk: DocumentChunk, namespace: str) -> Dict:
         """将 DocumentChunk 转换为结果格式"""

         domain = db.query(KnowledgeDomain).filter(
             KnowledgeDomain.namespace == namespace
         ).first()

         return {
             'chunk_id': chunk.id,
             'content': chunk.content,
             'score': 0.0,  # 后续添加
             'namespace': namespace,
             'domain_display_name': domain.display_name if domain else namespace,
             'domain_color': domain.color if domain else '#999999',
             'domain_icon': domain.icon if domain else 'folder',
             'document_id': chunk.document_id,
             'document_title': chunk.document.filename if chunk.document else '',
             'metadata': chunk.metadata or {}
         }
     ```

2. **创建响应 Schema**

   文件: `backend/app/schemas/query.py`

   - [ ] QueryRequest Schema
   - [ ] QueryResponse Schema
   - [ ] ChunkResult Schema

3. **集成测试**

   文件: `backend/tests/routers/test_query_v2.py`

   - [ ] 测试自动分类查询
   - [ ] 测试指定领域查询
   - [ ] 测试不同检索方法
   - [ ] 测试过滤条件

**交付物**:
- ✅ 完整的查询 API v2
- ✅ 响应 Schema
- ✅ 集成测试

---

### 任务 6.3: 前端查询界面优化

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 6.2

#### 子任务清单

1. **优化查询页面**

   文件: `frontend/src/views/Query.vue`

   - [ ] **添加领域选择器**
     ```vue
     <template>
       <div class="query-page">
         <el-card>
           <template #header>
             <div class="header-row">
               <span>智能检索</span>
               <el-space>
                 <el-radio-group v-model="retrievalMode">
                   <el-radio label="auto">自动识别</el-radio>
                   <el-radio label="single">单领域</el-radio>
                   <el-radio label="cross">跨领域</el-radio>
                 </el-radio-group>

                 <el-select v-model="retrievalMethod" placeholder="检索方法" style="width: 120px">
                   <el-option label="混合检索" value="hybrid" />
                   <el-option label="向量检索" value="vector" />
                   <el-option label="关键词检索" value="bm25" />
                 </el-select>
               </el-space>
             </div>
           </template>

           <el-form>
             <el-form-item v-if="retrievalMode === 'single'">
               <domain-selector
                 v-model="selectedNamespace"
                 :clearable="false"
                 placeholder="选择检索领域"
               />
             </el-form-item>

             <el-form-item>
               <el-input
                 v-model="query"
                 type="textarea"
                 :rows="4"
                 placeholder="输入查询内容..."
                 @keyup.ctrl.enter="handleQuery"
               >
                 <template #append>
                   <el-button type="primary" @click="handleQuery" :loading="querying">
                     <el-icon><Search /></el-icon> 检索
                   </el-button>
                 </template>
               </el-input>
             </el-form-item>

             <el-form-item v-if="classificationResult" class="classification-hint">
               <el-alert :closable="false" type="info">
                 <template #title>
                   <div class="classification-info">
                     <span>识别领域:</span>
                     <domain-badge
                       :domain="classificationResult.domain"
                       :confidence="classificationResult.confidence"
                       show-confidence
                     />
                     <el-tag v-if="classificationResult.fallback_to_cross_domain" type="warning" size="small">
                       建议跨领域检索
                     </el-tag>
                   </div>
                 </template>
               </el-alert>
             </el-form-item>
           </el-form>
         </el-card>

         <el-card v-if="results.length > 0" class="results-card">
           <template #header>
             <div class="results-header">
               <span>检索结果 ({{ results.length }} 条)</span>
               <el-space>
                 <el-text type="info">
                   耗时: {{ retrievalStats.latency_ms }}ms
                 </el-text>
                 <el-text type="info">
                   方法: {{ retrievalMethodLabel }}
                 </el-text>
               </el-space>
             </div>
           </template>

           <el-space direction="vertical" fill :size="16">
             <query-result-item
               v-for="result in results"
               :key="result.chunk_id"
               :result="result"
               :query="query"
               @view-document="handleViewDocument"
             />
           </el-space>
         </el-card>
       </div>
     </template>

     <script setup>
     import { ref, computed } from 'vue'
     import { queryDocuments } from '@/services/query'
     import DomainSelector from '@/components/domain/DomainSelector.vue'
     import DomainBadge from '@/components/domain/DomainBadge.vue'
     import QueryResultItem from '@/components/query/QueryResultItem.vue'
     import { ElMessage } from 'element-plus'

     const query = ref('')
     const retrievalMode = ref('auto')
     const retrievalMethod = ref('hybrid')
     const selectedNamespace = ref(null)
     const querying = ref(false)

     const classificationResult = ref(null)
     const results = ref([])
     const retrievalStats = ref({})

     const retrievalMethodLabel = computed(() => {
       const labels = {
         'hybrid': '混合检索',
         'vector': '向量检索',
         'bm25': '关键词检索'
       }
       return labels[retrievalMethod.value] || retrievalMethod.value
     })

     const handleQuery = async () => {
       if (!query.value.trim()) {
         ElMessage.warning('请输入查询内容')
         return
       }

       try {
         querying.value = true

         const response = await queryDocuments({
           query: query.value,
           namespace: retrievalMode.value === 'single' ? selectedNamespace.value : null,
           retrieval_mode: retrievalMode.value,
           retrieval_method: retrievalMethod.value,
           top_k: 10
         })

         classificationResult.value = response.data.domain_classification
         results.value = response.data.results
         retrievalStats.value = response.data.retrieval_stats

       } catch (error) {
         ElMessage.error('检索失败: ' + error.message)
       } finally {
         querying.value = false
       }
     }

     const handleViewDocument = (documentId) => {
       // 跳转到文档详情页
     }
     </script>
     ```

2. **创建检索结果组件**

   文件: `frontend/src/components/query/QueryResultItem.vue` (新建)

   - [ ] **结果项组件**
     ```vue
     <template>
       <el-card class="result-item" shadow="hover">
         <div class="result-header">
           <domain-badge :domain="domainInfo" />
           <el-text type="info" size="small">
             相似度: {{ (result.score * 100).toFixed(1) }}%
           </el-text>
         </div>

         <div class="result-content">
           <h4 class="document-title" @click="handleViewDocument">
             <el-icon><Document /></el-icon>
             {{ result.document_title }}
           </h4>

           <div class="chunk-content" v-html="highlightedContent"></div>
         </div>

         <div class="result-footer">
           <el-space>
             <el-button size="small" @click="handleViewDocument">
               查看文档
             </el-button>
             <el-button size="small" @click="handleCopyContent">
               复制内容
             </el-button>
           </el-space>
         </div>
       </el-card>
     </template>

     <script setup>
     import { computed } from 'vue'
     import DomainBadge from '@/components/domain/DomainBadge.vue'

     const props = defineProps({
       result: Object,
       query: String
     })

     const emit = defineEmits(['view-document'])

     const domainInfo = computed(() => ({
       namespace: props.result.namespace,
       display_name: props.result.domain_display_name,
       color: props.result.domain_color,
       icon: props.result.domain_icon
     }))

     const highlightedContent = computed(() => {
       // 高亮关键词
       let content = props.result.content
       const keywords = props.query.split(/\s+/)

       keywords.forEach(keyword => {
         if (keyword.length > 1) {
           const regex = new RegExp(keyword, 'gi')
           content = content.replace(regex, `<mark>${keyword}</mark>`)
         }
       })

       return content
     })

     const handleViewDocument = () => {
       emit('view-document', props.result.document_id)
     }

     const handleCopyContent = () => {
       navigator.clipboard.writeText(props.result.content)
       ElMessage.success('已复制到剪贴板')
     }
     </script>

     <style scoped>
     .result-item {
       cursor: pointer;
       transition: all 0.3s;
     }

     .result-item:hover {
       transform: translateY(-2px);
     }

     .result-header {
       display: flex;
       justify-content: space-between;
       margin-bottom: 12px;
     }

     .document-title {
       color: #409eff;
       cursor: pointer;
       margin: 8px 0;
     }

     .document-title:hover {
       text-decoration: underline;
     }

     .chunk-content {
       line-height: 1.6;
       color: #606266;
       max-height: 200px;
       overflow: hidden;
       text-overflow: ellipsis;
     }

     .chunk-content :deep(mark) {
       background-color: #ffd666;
       padding: 2px 4px;
       border-radius: 2px;
     }

     .result-footer {
       margin-top: 12px;
       padding-top: 12px;
       border-top: 1px solid #ebeef5;
     }
     </style>
     ```

**交付物**:
- ✅ 优化后的查询页面
- ✅ QueryResultItem 组件
- ✅ 关键词高亮功能

---

## Week 2: 跨领域检索实现

### 任务 7.1: 跨领域检索服务

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 6.3

#### 子任务清单

1. **实现跨领域检索**

   文件: `backend/app/services/cross_domain_retrieval.py` (新建)

   - [ ] **跨领域检索实现**
     ```python
     class CrossDomainRetrieval:
         """跨领域检索服务"""

         def __init__(self, db: Session):
             self.db = db
             self.hybrid_retrieval = HybridRetrieval(db)

         async def search_across_domains(
             self,
             query: str,
             namespaces: Optional[List[str]] = None,
             top_k: int = 10,
             domain_weights: Optional[Dict[str, float]] = None
         ) -> List[Tuple[DocumentChunk, str, float]]:
             """
             跨领域检索

             Args:
                 query: 查询文本
                 namespaces: 指定领域列表(None = 所有活跃领域)
                 top_k: 总返回结果数
                 domain_weights: 领域权重字典

             Returns:
                 List[Tuple[chunk, namespace, score]]
             """

             # 1. 确定检索领域
             if namespaces is None:
                 domains = self.db.query(KnowledgeDomain).filter(
                     KnowledgeDomain.is_active == True
                 ).all()
                 namespaces = [d.namespace for d in domains]

             if len(namespaces) == 0:
                 return []

             # 2. 并行检索所有领域
             tasks = []
             for namespace in namespaces:
                 task = self._search_single_domain(query, namespace, top_k * 2)
                 tasks.append(task)

             domain_results = await asyncio.gather(*tasks)

             # 3. 合并并重排序
             all_results = []

             for namespace, chunks in zip(namespaces, domain_results):
                 weight = domain_weights.get(namespace, 1.0) if domain_weights else 1.0

                 for rank, chunk in enumerate(chunks, 1):
                     # 计算得分(结合排名和领域权重)
                     score = (1 / rank) * weight
                     all_results.append((chunk, namespace, score))

             # 4. 全局排序
             all_results.sort(key=lambda x: x[2], reverse=True)

             # 5. 去重(同一文档块只保留得分最高的)
             seen_chunks = set()
             unique_results = []

             for chunk, namespace, score in all_results:
                 if chunk.id not in seen_chunks:
                     seen_chunks.add(chunk.id)
                     unique_results.append((chunk, namespace, score))

                 if len(unique_results) >= top_k:
                     break

             return unique_results

         async def _search_single_domain(
             self,
             query: str,
             namespace: str,
             top_k: int
         ) -> List[DocumentChunk]:
             """单领域检索(内部方法)"""
             return await self.hybrid_retrieval.search_by_namespace(query, namespace, top_k)
     ```

2. **领域权重计算**

   - [ ] **基于分类置信度的权重**
     ```python
     def calculate_domain_weights(
         classification_result: DomainClassificationResult
     ) -> Dict[str, float]:
         """基于分类结果计算领域权重"""

         weights = {
             classification_result.namespace: 2.0  # 主领域权重 x2
         }

         # 备选领域降权
         for alt in classification_result.alternatives:
             weights[alt['namespace']] = 0.5 + alt['confidence']

         return weights
     ```

   - [ ] **基于领域优先级的权重**
   - [ ] **基于用户历史的权重**

3. **跨领域结果展示优化**

   - [ ] **按领域分组**
     ```python
     def group_results_by_domain(
         results: List[Tuple[DocumentChunk, str, float]]
     ) -> Dict[str, List[Dict]]:
         """按领域分组结果"""

         grouped = {}

         for chunk, namespace, score in results:
             if namespace not in grouped:
                 grouped[namespace] = []

             grouped[namespace].append({
                 'chunk': chunk,
                 'score': score
             })

         return grouped
     ```

**交付物**:
- ✅ CrossDomainRetrieval 实现
- ✅ 领域权重计算
- ✅ 结果分组功能

---

### 任务 7.2: 跨领域检索 API

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 7.1

#### 子任务清单

1. **完善查询 API**

   文件: `backend/app/routers/query.py`

   - [ ] **实现 _cross_domain_retrieval 方法**
     ```python
     async def _cross_domain_retrieval(
         query: str,
         namespaces: Optional[List[str]],
         top_k: int,
         method: str,
         db: Session
     ) -> List[Tuple[DocumentChunk, str, float]]:
         """跨领域检索"""

         cross_retrieval = CrossDomainRetrieval(db)

         results = await cross_retrieval.search_across_domains(
             query=query,
             namespaces=namespaces,
             top_k=top_k
         )

         return results
     ```

   - [ ] **修改响应格式**
     ```python
     # 在 query_documents_v2 中
     if retrieval_mode == 'cross':
         results_with_namespace = await _cross_domain_retrieval(...)

         # 按领域分组
         grouped_results = group_results_by_domain(results_with_namespace)

         response = QueryResponse(
             ...
             results=[
                 _chunk_to_result(chunk, namespace, score)
                 for chunk, namespace, score in results_with_namespace
             ],
             cross_domain_results=[
                 {
                     'namespace': namespace,
                     'display_name': get_domain_display_name(namespace),
                     'count': len(chunks),
                     'results': [
                         _chunk_to_result(c['chunk'], namespace, c['score'])
                         for c in chunks[:3]  # 每个领域显示前3个
                     ]
                 }
                 for namespace, chunks in grouped_results.items()
             ]
         )
     ```

**交付物**:
- ✅ 跨领域检索 API
- ✅ 分组响应格式

---

### 任务 7.3: 前端跨领域结果展示

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 7.2

#### 子任务清单

1. **跨领域结果组件**

   文件: `frontend/src/components/query/CrossDomainResults.vue` (新建)

   - [ ] **分组展示组件**
     ```vue
     <template>
       <div class="cross-domain-results">
         <el-collapse v-model="activeNames" accordion>
           <el-collapse-item
             v-for="group in groupedResults"
             :key="group.namespace"
             :name="group.namespace"
           >
             <template #title>
               <div class="group-header">
                 <domain-badge :domain="group.domain" />
                 <el-tag type="info" size="small">
                   {{ group.count }} 条结果
                 </el-tag>
               </div>
             </template>

             <el-space direction="vertical" fill :size="12">
               <query-result-item
                 v-for="result in group.results"
                 :key="result.chunk_id"
                 :result="result"
                 :query="query"
                 @view-document="handleViewDocument"
               />

               <el-button
                 v-if="group.count > 3"
                 text
                 @click="handleViewMore(group.namespace)"
               >
                 查看更多 ({{ group.count - 3 }} 条)
               </el-button>
             </el-space>
           </el-collapse-item>
         </el-collapse>
       </div>
     </template>

     <script setup>
     import { ref, computed } from 'vue'
     import DomainBadge from '@/components/domain/DomainBadge.vue'
     import QueryResultItem from '@/components/query/QueryResultItem.vue'

     const props = defineProps({
       crossDomainResults: Array,
       query: String
     })

     const emit = defineEmits(['view-document', 'view-more'])

     const activeNames = ref([])

     const groupedResults = computed(() => {
       return props.crossDomainResults.map(group => ({
         ...group,
         domain: {
           namespace: group.namespace,
           display_name: group.display_name,
           color: group.results[0]?.domain_color || '#999999',
           icon: group.results[0]?.domain_icon || 'folder'
         }
       }))
     })

     const handleViewDocument = (documentId) => {
       emit('view-document', documentId)
     }

     const handleViewMore = (namespace) => {
       emit('view-more', namespace)
     }
     </script>

     <style scoped>
     .group-header {
       display: flex;
       align-items: center;
       gap: 12px;
       flex: 1;
     }

     .cross-domain-results {
       margin-top: 20px;
     }
     </style>
     ```

2. **集成到查询页面**

   文件: `frontend/src/views/Query.vue`

   - [ ] 添加跨领域结果展示
   - [ ] 支持展开/收起领域组

**交付物**:
- ✅ CrossDomainResults 组件
- ✅ 集成到查询页面

---

### 任务 7.4: 检索性能优化

**优先级**: P1
**预计时间**: 2 天
**依赖**: 任务 7.3

#### 子任务清单

1. **数据库查询优化**

   - [ ] **添加复合索引**
     ```sql
     -- 向量检索优化
     CREATE INDEX idx_chunks_namespace_embedding
     ON document_chunks(namespace)
     WHERE embedding IS NOT NULL;

     -- 跨领域检索优化
     CREATE INDEX idx_chunks_multi_namespace
     ON document_chunks(namespace, id)
     INCLUDE (content, embedding);
     ```

   - [ ] **使用数据库连接池**
   - [ ] **查询结果缓存**

2. **并发优化**

   - [ ] **并行领域检索**
     ```python
     # 使用 asyncio.gather 并行查询
     results = await asyncio.gather(*[
         search_domain(namespace)
         for namespace in namespaces
     ])
     ```

   - [ ] **超时控制**
     ```python
     try:
         results = await asyncio.wait_for(
             search_across_domains(query, namespaces),
             timeout=5.0
         )
     except asyncio.TimeoutError:
         # 降级处理
         results = await search_default_domain(query)
     ```

3. **缓存策略**

   - [ ] **检索结果缓存(Redis)**
   - [ ] **领域索引预加载**
   - [ ] **热点查询识别和优化**

4. **性能测试**

   文件: `backend/tests/performance/test_retrieval_performance.py` (新建)

   - [ ] 单领域检索性能测试
   - [ ] 跨领域检索性能测试
   - [ ] 并发查询测试
   - [ ] 生成性能报告

**交付物**:
- ✅ 数据库索引优化
- ✅ 并发和缓存优化
- ✅ 性能测试报告

---

## 阶段验收标准

### 功能验收

- [ ] ✅ 单领域检索正常工作
- [ ] ✅ 跨领域检索正常工作
- [ ] ✅ 混合检索(向量+BM25)效果提升 > 15%
- [ ] ✅ 领域自动识别准确率 > 85%
- [ ] ✅ 前端界面友好,支持领域选择和结果展示
- [ ] ✅ 关键词高亮显示正常

### 质量验收

- [ ] ✅ 单元测试覆盖率 > 85%
- [ ] ✅ 集成测试全部通过
- [ ] ✅ 性能测试达标

### 性能验收

- [ ] ✅ 单领域检索延迟 P95 < 500ms
- [ ] ✅ 跨领域检索延迟 P95 < 1.5s
- [ ] ✅ 支持并发查询 QPS > 50
- [ ] ✅ 混合检索准确率 > 纯向量检索 15%

---

## 风险与应对

### 风险 1: 跨领域检索延迟过高

**应对**:
- 并行查询
- 限制检索领域数量
- 异步结果返回

### 风险 2: 检索准确率不理想

**应对**:
- 优化 BM25 参数
- 调整 RRF 融合权重
- 引入 Rerank 模型(第四阶段)

---

## 下一阶段预告

完成第三阶段后,进入**第四阶段:高级特性**:

1. 权限与安全
2. 监控与优化
3. Rerank 精排
4. 领域关系管理
