# 第二阶段:智能分类系统详细任务

## 阶段概览

**阶段名称**: 智能领域分类系统
**预计工期**: 2-3 周
**目标**: 实现自动化领域识别和分类功能
**前置条件**: 第一阶段完成,领域配置表和数据就绪

---

## Week 1: 关键词分类器

### 任务 3.1: DomainClassifier 基础架构

**优先级**: P0
**预计时间**: 1 天
**依赖**: 第一阶段完成

#### 子任务清单

1. **创建 DomainClassifier 基类**

   文件: `backend/app/services/domain_classifier.py` (新建)

   - [ ] **定义分类结果数据结构**
     ```python
     from dataclasses import dataclass
     from typing import List, Optional, Dict, Any

     @dataclass
     class DomainClassificationResult:
         """领域分类结果"""
         namespace: str
         display_name: str
         confidence: float  # 0.0-1.0
         method: str  # 'keyword', 'llm', 'hybrid'
         reasoning: str  # 推理过程
         alternatives: List[Dict[str, Any]]  # 备选领域
         fallback_to_cross_domain: bool  # 是否建议跨领域检索
         metadata: Dict[str, Any]  # 额外元数据

         def to_dict(self) -> Dict[str, Any]:
             return {
                 'namespace': self.namespace,
                 'display_name': self.display_name,
                 'confidence': self.confidence,
                 'method': self.method,
                 'reasoning': self.reasoning,
                 'alternatives': self.alternatives,
                 'fallback_to_cross_domain': self.fallback_to_cross_domain,
                 'metadata': self.metadata
             }
     ```

   - [ ] **创建 DomainClassifier 基类**
     ```python
     from abc import ABC, abstractmethod

     class DomainClassifier(ABC):
         """领域分类器抽象基类"""

         def __init__(self, db: Session):
             self.db = db
             self._domains_cache = None
             self._cache_timestamp = None
             self.cache_ttl = 300  # 5分钟缓存

         async def get_active_domains(self) -> List[KnowledgeDomain]:
             """获取活跃领域(带缓存)"""
             now = time.time()
             if (self._domains_cache is None or
                 self._cache_timestamp is None or
                 now - self._cache_timestamp > self.cache_ttl):
                 self._domains_cache = self.db.query(KnowledgeDomain).filter(
                     KnowledgeDomain.is_active == True
                 ).order_by(KnowledgeDomain.priority.desc()).all()
                 self._cache_timestamp = now
             return self._domains_cache

         @abstractmethod
         async def classify(
             self,
             query: str,
             context: Optional[Dict[str, Any]] = None
         ) -> DomainClassificationResult:
             """
             分类查询到领域

             Args:
                 query: 用户查询
                 context: 上下文信息(如用户ID、会话ID、历史领域等)

             Returns:
                 DomainClassificationResult
             """
             pass

         def extract_keywords(self, text: str) -> List[str]:
             """提取关键词(简单实现)"""
             import jieba
             import re

             # 去除标点和特殊字符
             text = re.sub(r'[^\w\s]', ' ', text)
             # 分词
             words = jieba.cut(text)
             # 过滤停用词和短词
             keywords = [w.strip() for w in words
                        if len(w.strip()) > 1 and w not in self._stopwords]
             return keywords

         @property
         def _stopwords(self) -> set:
             """停用词列表"""
             return {'的', '了', '在', '是', '我', '有', '和', '就',
                    '不', '人', '都', '一', '一个', '上', '也', '很',
                    '到', '说', '要', '去', '你', '会', '着', '没有'}
     ```

2. **配置管理**

   文件: `backend/app/config/classifier_config.py` (新建)

   - [ ] 分类器配置类
     ```python
     from pydantic import BaseModel

     class ClassifierConfig(BaseModel):
         """分类器配置"""

         # 关键词分类器配置
         keyword_confidence_threshold: float = 0.7  # 关键词匹配阈值
         keyword_match_boost: float = 1.2  # 关键词权重提升
         use_tfidf: bool = True  # 是否使用 TF-IDF

         # LLM 分类器配置
         llm_model: str = "qwen-plus"  # LLM 模型
         llm_temperature: float = 0.1  # 温度
         llm_max_tokens: int = 100  # 最大 Token
         llm_confidence_threshold: float = 0.6  # LLM 置信度阈值

         # 混合分类器配置
         hybrid_keyword_first: bool = True  # 优先关键词分类
         hybrid_llm_fallback_threshold: float = 0.6  # LLM fallback 阈值
         cross_domain_threshold: float = 0.5  # 跨领域检索阈值

         # 缓存配置
         enable_cache: bool = True
         cache_ttl: int = 300  # 5分钟
         cache_max_size: int = 1000

         # 性能配置
         timeout: float = 5.0  # 分类超时时间
     ```

3. **单元测试框架**

   文件: `backend/tests/services/test_domain_classifier_base.py` (新建)

   - [ ] 测试基类方法
   - [ ] 测试缓存机制
   - [ ] 测试关键词提取

**交付物**:
- ✅ DomainClassifier 基类
- ✅ DomainClassificationResult 数据结构
- ✅ ClassifierConfig 配置类
- ✅ 基础单元测试

---

### 任务 3.2: 关键词分类器实现

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 3.1

#### 子任务清单

1. **实现 KeywordDomainClassifier**

   文件: `backend/app/services/keyword_domain_classifier.py` (新建)

   - [ ] **基础实现**
     ```python
     from app.services.domain_classifier import DomainClassifier, DomainClassificationResult
     from sklearn.feature_extraction.text import TfidfVectorizer
     import numpy as np

     class KeywordDomainClassifier(DomainClassifier):
         """基于关键词的领域分类器"""

         def __init__(self, db: Session, config: ClassifierConfig):
             super().__init__(db)
             self.config = config
             self.tfidf_vectorizer = None
             self.domain_vectors = {}

         async def initialize(self):
             """初始化 TF-IDF 模型"""
             domains = await self.get_active_domains()

             if self.config.use_tfidf and len(domains) > 0:
                 # 构建领域关键词文档
                 domain_texts = []
                 domain_namespaces = []

                 for domain in domains:
                     keywords = domain.keywords if isinstance(domain.keywords, list) else []
                     text = ' '.join(keywords)
                     domain_texts.append(text)
                     domain_namespaces.append(domain.namespace)

                 # 训练 TF-IDF
                 self.tfidf_vectorizer = TfidfVectorizer(
                     max_features=1000,
                     ngram_range=(1, 2)
                 )
                 tfidf_matrix = self.tfidf_vectorizer.fit_transform(domain_texts)

                 # 保存领域向量
                 for i, namespace in enumerate(domain_namespaces):
                     self.domain_vectors[namespace] = tfidf_matrix[i].toarray()[0]

         async def classify(
             self,
             query: str,
             context: Optional[Dict[str, Any]] = None
         ) -> DomainClassificationResult:
             """
             使用关键词匹配分类

             流程:
             1. 提取查询关键词
             2. 计算与各领域关键词的匹配度
             3. 使用 TF-IDF(如果启用)计算相似度
             4. 综合评分,返回最佳匹配
             """
             domains = await self.get_active_domains()

             if len(domains) == 0:
                 return self._create_default_result("无可用领域")

             # 提取查询关键词
             query_keywords = set(self.extract_keywords(query))

             # 计算每个领域的匹配得分
             scores = []

             for domain in domains:
                 domain_keywords = set(domain.keywords) if isinstance(domain.keywords, list) else set()

                 # 简单关键词匹配得分
                 if len(domain_keywords) > 0:
                     intersection = query_keywords & domain_keywords
                     simple_score = len(intersection) / len(domain_keywords)
                 else:
                     simple_score = 0.0

                 # TF-IDF 相似度得分
                 tfidf_score = 0.0
                 if self.config.use_tfidf and self.tfidf_vectorizer is not None:
                     try:
                         query_vector = self.tfidf_vectorizer.transform([query]).toarray()[0]
                         domain_vector = self.domain_vectors.get(domain.namespace, np.zeros_like(query_vector))
                         # 余弦相似度
                         tfidf_score = np.dot(query_vector, domain_vector) / (
                             np.linalg.norm(query_vector) * np.linalg.norm(domain_vector) + 1e-8
                         )
                     except Exception as e:
                         logger.warning(f"TF-IDF 计算失败: {e}")

                 # 综合得分(权重:简单匹配 0.4 + TF-IDF 0.6)
                 final_score = simple_score * 0.4 + tfidf_score * 0.6

                 scores.append({
                     'domain': domain,
                     'score': final_score,
                     'simple_score': simple_score,
                     'tfidf_score': tfidf_score,
                     'matched_keywords': list(intersection) if len(domain_keywords) > 0 else []
                 })

             # 排序
             scores.sort(key=lambda x: x['score'], reverse=True)

             # 最佳匹配
             best = scores[0]
             best_score = best['score']

             # 判断置信度
             if best_score >= self.config.keyword_confidence_threshold:
                 # 高置信度
                 return DomainClassificationResult(
                     namespace=best['domain'].namespace,
                     display_name=best['domain'].display_name,
                     confidence=best_score,
                     method='keyword',
                     reasoning=f"匹配关键词: {', '.join(best['matched_keywords'][:5])}",
                     alternatives=[
                         {'namespace': s['domain'].namespace, 'confidence': s['score']}
                         for s in scores[1:3]
                     ],
                     fallback_to_cross_domain=False,
                     metadata={
                         'simple_score': best['simple_score'],
                         'tfidf_score': best['tfidf_score'],
                         'matched_keywords': best['matched_keywords']
                     }
                 )
             else:
                 # 低置信度,建议跨领域或 LLM
                 return DomainClassificationResult(
                     namespace=best['domain'].namespace,
                     display_name=best['domain'].display_name,
                     confidence=best_score,
                     method='keyword',
                     reasoning=f"匹配关键词较少,置信度低",
                     alternatives=[
                         {'namespace': s['domain'].namespace, 'confidence': s['score']}
                         for s in scores[1:3]
                     ],
                     fallback_to_cross_domain=True,
                     metadata={
                         'simple_score': best['simple_score'],
                         'tfidf_score': best['tfidf_score']
                     }
                 )

         def _create_default_result(self, reason: str) -> DomainClassificationResult:
             """创建默认结果(降级到 default 领域)"""
             return DomainClassificationResult(
                 namespace='default',
                 display_name='默认知识库',
                 confidence=0.0,
                 method='keyword',
                 reasoning=reason,
                 alternatives=[],
                 fallback_to_cross_domain=True,
                 metadata={}
             )
     ```

2. **性能优化**

   - [ ] 关键词匹配缓存(LRU)
     ```python
     from functools import lru_cache

     @lru_cache(maxsize=1000)
     def _match_keywords(query_keywords_tuple, domain_keywords_tuple):
         """缓存关键词匹配结果"""
         return set(query_keywords_tuple) & set(domain_keywords_tuple)
     ```

   - [ ] TF-IDF 向量预计算
   - [ ] 并发查询处理

3. **单元测试**

   文件: `backend/tests/services/test_keyword_classifier.py` (新建)

   - [ ] 测试高置信度匹配
     ```python
     async def test_high_confidence_match():
         query = "API 接口认证失败怎么办"
         result = await classifier.classify(query)
         assert result.namespace == 'technical_docs'
         assert result.confidence >= 0.7
         assert result.method == 'keyword'
     ```

   - [ ] 测试低置信度匹配
   - [ ] 测试无匹配情况
   - [ ] 测试 TF-IDF 计算
   - [ ] 测试缓存效果
   - [ ] 测试边界条件(空查询、特殊字符等)

**交付物**:
- ✅ KeywordDomainClassifier 实现
- ✅ TF-IDF 集成
- ✅ 性能优化(缓存)
- ✅ 单元测试(覆盖率 > 85%)

---

### 任务 3.3: 关键词管理界面

**优先级**: P1
**预计时间**: 1.5 天
**依赖**: 任务 3.2

#### 子任务清单

1. **后端:关键词建议 API**

   文件: `backend/app/routers/knowledge_domains.py`

   - [ ] **GET /api/knowledge-domains/{namespace}/suggest-keywords** - 关键词建议
     ```python
     @router.get("/knowledge-domains/{namespace}/suggest-keywords")
     async def suggest_keywords(
         namespace: str,
         sample_size: int = 100,
         top_k: int = 20,
         db: Session = Depends(get_db),
         current_user: User = Depends(require_admin)
     ):
         """
         基于领域内文档,建议关键词

         算法:
         1. 抽取领域内文档样本
         2. 提取关键词(TF-IDF)
         3. 返回 Top-K 高频关键词
         """
         # 获取领域文档
         documents = db.query(Document).filter(
             Document.namespace == namespace
         ).limit(sample_size).all()

         if len(documents) == 0:
             return {"keywords": []}

         # 提取文本
         texts = [doc.content or doc.filename for doc in documents]

         # TF-IDF 提取关键词
         from sklearn.feature_extraction.text import TfidfVectorizer
         import jieba

         def tokenizer(text):
             return list(jieba.cut(text))

         vectorizer = TfidfVectorizer(
             tokenizer=tokenizer,
             max_features=top_k,
             stop_words=list(stopwords)
         )

         try:
             vectorizer.fit(texts)
             keywords = vectorizer.get_feature_names_out()
             return {"keywords": list(keywords)}
         except Exception as e:
             logger.error(f"关键词提取失败: {e}")
             return {"keywords": []}
     ```

2. **前端:关键词编辑器增强**

   文件: `frontend/src/components/domain/KeywordEditor.vue` (新建)

   - [ ] **关键词编辑器组件**
     ```vue
     <template>
       <div class="keyword-editor">
         <div class="keyword-list">
           <el-tag
             v-for="(keyword, index) in modelValue"
             :key="index"
             closable
             @close="handleRemove(index)"
             class="keyword-tag"
           >
             {{ keyword }}
           </el-tag>
         </div>

         <div class="keyword-input">
           <el-input
             v-model="newKeyword"
             placeholder="输入关键词后按回车添加"
             @keyup.enter="handleAdd"
             size="small"
           >
             <template #append>
               <el-button @click="handleAdd" :icon="Plus">添加</el-button>
             </template>
           </el-input>
         </div>

         <div class="keyword-suggestions" v-if="suggestions.length > 0">
           <div class="suggestions-header">
             <span>智能建议</span>
             <el-button size="small" @click="loadSuggestions" :loading="loadingSuggestions">
               刷新建议
             </el-button>
           </div>
           <div class="suggestions-list">
             <el-tag
               v-for="(keyword, index) in suggestions"
               :key="index"
               type="info"
               class="suggestion-tag"
               @click="handleAddSuggestion(keyword)"
             >
               <el-icon><Plus /></el-icon>
               {{ keyword }}
             </el-tag>
           </div>
         </div>
       </div>
     </template>

     <script setup>
     import { ref, onMounted } from 'vue'
     import { Plus } from '@element-plus/icons-vue'
     import { suggestKeywords } from '@/services/knowledgeDomains'

     const props = defineProps({
       modelValue: {
         type: Array,
         default: () => []
       },
       namespace: String
     })

     const emit = defineEmits(['update:modelValue'])

     const newKeyword = ref('')
     const suggestions = ref([])
     const loadingSuggestions = ref(false)

     const handleAdd = () => {
       const keyword = newKeyword.value.trim()
       if (keyword && !props.modelValue.includes(keyword)) {
         emit('update:modelValue', [...props.modelValue, keyword])
         newKeyword.value = ''
       }
     }

     const handleRemove = (index) => {
       const keywords = [...props.modelValue]
       keywords.splice(index, 1)
       emit('update:modelValue', keywords)
     }

     const handleAddSuggestion = (keyword) => {
       if (!props.modelValue.includes(keyword)) {
         emit('update:modelValue', [...props.modelValue, keyword])
       }
     }

     const loadSuggestions = async () => {
       if (!props.namespace) return

       try {
         loadingSuggestions.value = true
         const response = await suggestKeywords(props.namespace, {
           sample_size: 100,
           top_k: 20
         })
         // 过滤掉已存在的关键词
         suggestions.value = response.data.keywords.filter(
           k => !props.modelValue.includes(k)
         )
       } catch (error) {
         console.error('加载关键词建议失败', error)
       } finally {
         loadingSuggestions.value = false
       }
     }

     onMounted(() => {
       if (props.namespace) {
         loadSuggestions()
       }
     })
     </script>

     <style scoped>
     .keyword-editor {
       border: 1px solid #dcdfe6;
       border-radius: 4px;
       padding: 12px;
     }

     .keyword-list {
       display: flex;
       flex-wrap: wrap;
       gap: 8px;
       margin-bottom: 12px;
       min-height: 32px;
     }

     .keyword-tag {
       cursor: pointer;
     }

     .keyword-input {
       margin-bottom: 12px;
     }

     .suggestions-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       margin-bottom: 8px;
       font-size: 14px;
       color: #606266;
     }

     .suggestions-list {
       display: flex;
       flex-wrap: wrap;
       gap: 8px;
     }

     .suggestion-tag {
       cursor: pointer;
       transition: all 0.3s;
     }

     .suggestion-tag:hover {
       transform: scale(1.05);
     }
     </style>
     ```

3. **集成到领域编辑对话框**

   文件: `frontend/src/views/admin/KnowledgeDomains.vue`

   - [ ] 替换原有的简单关键词输入
   - [ ] 使用 KeywordEditor 组件

**交付物**:
- ✅ 关键词建议 API
- ✅ KeywordEditor 组件
- ✅ 集成到领域管理页面

---

### 任务 3.4: 分类测试工具

**优先级**: P1
**预计时间**: 1 天
**依赖**: 任务 3.2

#### 子任务清单

1. **后端:分类测试 API**

   文件: `backend/app/routers/knowledge_domains.py`

   - [ ] **POST /api/knowledge-domains/classify/test** - 测试分类
     ```python
     @router.post("/knowledge-domains/classify/test")
     async def test_classification(
         query: str = Body(...),
         method: str = Body('keyword'),  # keyword/llm/hybrid
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """
         测试领域分类

         用于管理员测试分类器效果
         """
         from app.services.keyword_domain_classifier import KeywordDomainClassifier
         from app.config.classifier_config import ClassifierConfig

         config = ClassifierConfig()
         classifier = KeywordDomainClassifier(db, config)
         await classifier.initialize()

         result = await classifier.classify(query)

         return {
             "query": query,
             "classification": result.to_dict()
         }
     ```

2. **前端:分类测试页面**

   文件: `frontend/src/views/admin/ClassifierTest.vue` (新建)

   - [ ] **测试界面**
     ```vue
     <template>
       <div class="classifier-test">
         <el-card>
           <template #header>
             <div class="card-header">
               <span>领域分类器测试</span>
               <el-radio-group v-model="method">
                 <el-radio label="keyword">关键词分类</el-radio>
                 <el-radio label="llm" disabled>LLM分类(即将支持)</el-radio>
                 <el-radio label="hybrid" disabled>混合分类(即将支持)</el-radio>
               </el-radio-group>
             </div>
           </template>

           <el-form>
             <el-form-item label="测试查询">
               <el-input
                 v-model="query"
                 type="textarea"
                 :rows="3"
                 placeholder="输入查询内容,测试领域分类效果"
               />
             </el-form-item>

             <el-form-item>
               <el-button type="primary" @click="handleTest" :loading="testing">
                 测试分类
               </el-button>
               <el-button @click="handleClear">清空</el-button>
             </el-form-item>
           </el-form>

           <el-divider />

           <div v-if="result" class="result-section">
             <h3>分类结果</h3>

             <el-descriptions :column="2" border>
               <el-descriptions-item label="分类领域">
                 <domain-badge :domain="result.domain" :confidence="result.confidence" show-confidence />
               </el-descriptions-item>

               <el-descriptions-item label="置信度">
                 <el-progress
                   :percentage="Math.round(result.confidence * 100)"
                   :color="getConfidenceColor(result.confidence)"
                 />
               </el-descriptions-item>

               <el-descriptions-item label="分类方法">
                 <el-tag>{{ result.method }}</el-tag>
               </el-descriptions-item>

               <el-descriptions-item label="推理过程">
                 {{ result.reasoning }}
               </el-descriptions-item>

               <el-descriptions-item label="跨领域建议" :span="2">
                 <el-tag :type="result.fallback_to_cross_domain ? 'warning' : 'success'">
                   {{ result.fallback_to_cross_domain ? '建议跨领域检索' : '单领域检索即可' }}
                 </el-tag>
               </el-descriptions-item>
             </el-descriptions>

             <div v-if="result.alternatives.length > 0" class="alternatives">
               <h4>备选领域</h4>
               <el-space>
                 <el-tag
                   v-for="(alt, index) in result.alternatives"
                   :key="index"
                   type="info"
                 >
                   {{ alt.namespace }} ({{ (alt.confidence * 100).toFixed(1) }}%)
                 </el-tag>
               </el-space>
             </div>

             <div v-if="result.metadata" class="metadata">
               <h4>详细信息</h4>
               <pre>{{ JSON.stringify(result.metadata, null, 2) }}</pre>
             </div>
           </div>
         </el-card>

         <el-card class="test-cases">
           <template #header>
             <span>预设测试用例</span>
           </template>

           <el-space direction="vertical" fill>
             <el-button
               v-for="(testCase, index) in testCases"
               :key="index"
               @click="handleTestCase(testCase)"
               text
             >
               {{ testCase.query }} → <el-tag size="small">{{ testCase.expected }}</el-tag>
             </el-button>
           </el-space>
         </el-card>
       </div>
     </template>

     <script setup>
     import { ref } from 'vue'
     import { testClassification } from '@/services/knowledgeDomains'
     import DomainBadge from '@/components/domain/DomainBadge.vue'
     import { ElMessage } from 'element-plus'

     const query = ref('')
     const method = ref('keyword')
     const testing = ref(false)
     const result = ref(null)

     const testCases = [
       { query: 'API 接口认证失败怎么办', expected: 'technical_docs' },
       { query: '如何集成支付 SDK', expected: 'technical_docs' },
       { query: '我要退货,怎么操作', expected: 'product_support' },
       { query: '保修期是多久', expected: 'product_support' },
       { query: '价格优惠活动', expected: 'sales' },
     ]

     const handleTest = async () => {
       if (!query.value.trim()) {
         ElMessage.warning('请输入测试查询')
         return
       }

       try {
         testing.value = true
         const response = await testClassification({
           query: query.value,
           method: method.value
         })
         result.value = response.data.classification
       } catch (error) {
         ElMessage.error('测试失败: ' + error.message)
       } finally {
         testing.value = false
       }
     }

     const handleClear = () => {
       query.value = ''
       result.value = null
     }

     const handleTestCase = (testCase) => {
       query.value = testCase.query
       handleTest()
     }

     const getConfidenceColor = (confidence) => {
       if (confidence >= 0.7) return '#67c23a'
       if (confidence >= 0.5) return '#e6a23c'
       return '#f56c6c'
     }
     </script>

     <style scoped>
     .classifier-test {
       display: grid;
       grid-template-columns: 2fr 1fr;
       gap: 20px;
     }

     .card-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
     }

     .result-section {
       margin-top: 20px;
     }

     .alternatives,
     .metadata {
       margin-top: 20px;
     }

     .metadata pre {
       background: #f5f7fa;
       padding: 12px;
       border-radius: 4px;
       font-size: 12px;
     }
     </style>
     ```

3. **路由和菜单**

   - [ ] 添加路由
   - [ ] 添加菜单项(管理员可见)

**交付物**:
- ✅ 分类测试 API
- ✅ 分类测试页面
- ✅ 预设测试用例

---

## Week 2: LLM 分类器

### 任务 4.1: LLM 分类器实现

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 3.4

#### 子任务清单

1. **LLM 分类器基础实现**

   文件: `backend/app/services/llm_domain_classifier.py` (新建)

   - [ ] **实现 LLMDomainClassifier**
     ```python
     from app.services.domain_classifier import DomainClassifier, DomainClassificationResult
     from app.services.llm_service import LLMService
     import json

     class LLMDomainClassifier(DomainClassifier):
         """基于 LLM 的领域分类器"""

         def __init__(self, db: Session, config: ClassifierConfig):
             super().__init__(db)
             self.config = config
             self.llm_service = LLMService()

         async def classify(
             self,
             query: str,
             context: Optional[Dict[str, Any]] = None
         ) -> DomainClassificationResult:
             """
             使用 LLM 分类领域

             流程:
             1. 构建包含所有领域描述的 Prompt
             2. 调用 LLM(使用 JSON Mode)
             3. 解析返回的结构化结果
             4. 返回分类结果
             """
             domains = await self.get_active_domains()

             if len(domains) == 0:
                 return self._create_default_result("无可用领域")

             # 构建 Prompt
             prompt = self._build_classification_prompt(query, domains)

             try:
                 # 调用 LLM
                 response = await self.llm_service.get_completion(
                     prompt=prompt,
                     model=self.config.llm_model,
                     temperature=self.config.llm_temperature,
                     max_tokens=self.config.llm_max_tokens,
                     response_format={"type": "json_object"}
                 )

                 # 解析结果
                 result_json = json.loads(response)
                 return self._parse_llm_response(result_json, domains)

             except Exception as e:
                 logger.error(f"LLM 分类失败: {e}")
                 return self._create_default_result(f"LLM 调用失败: {str(e)}")

         def _build_classification_prompt(
             self,
             query: str,
             domains: List[KnowledgeDomain]
         ) -> str:
             """构建分类 Prompt"""

             domains_desc = []
             for i, domain in enumerate(domains, 1):
                 keywords_str = ', '.join(domain.keywords[:10]) if domain.keywords else '无'
                 domains_desc.append(
                     f"{i}. {domain.namespace} - {domain.display_name}\n"
                     f"   描述: {domain.description or '无'}\n"
                     f"   关键词: {keywords_str}"
                 )

             domains_text = '\n'.join(domains_desc)

             prompt = f"""你是一个领域分类专家。根据用户的问题,判断属于哪个知识库领域。

可用领域:
{domains_text}

用户问题: {query}

请分析用户问题的意图和关键词,判断最匹配的领域。

要求:
1. 仔细分析用户问题的核心意图
2. 匹配领域的描述和关键词
3. 给出置信度(0.0-1.0),置信度计算依据:
   - 0.9-1.0: 问题明确属于某领域,关键词高度匹配
   - 0.7-0.9: 问题较明确,有清晰的领域特征
   - 0.5-0.7: 问题模糊,可能属于多个领域
   - 0.0-0.5: 问题很模糊,难以判断领域
4. 如果置信度 < 0.6,建议使用跨领域检索

返回 JSON 格式(不要包含任何其他文本):
{{
  "namespace": "领域标识(如 technical_docs)",
  "confidence": 0.85,
  "reasoning": "判断理由(50字以内)",
  "alternatives": [
    {{"namespace": "备选领域1", "confidence": 0.15}},
    {{"namespace": "备选领域2", "confidence": 0.10}}
  ]
}}"""

             return prompt

         def _parse_llm_response(
             self,
             result_json: Dict[str, Any],
             domains: List[KnowledgeDomain]
         ) -> DomainClassificationResult:
             """解析 LLM 返回的 JSON"""

             namespace = result_json.get('namespace', 'default')
             confidence = float(result_json.get('confidence', 0.0))
             reasoning = result_json.get('reasoning', '')
             alternatives = result_json.get('alternatives', [])

             # 查找领域
             domain = next((d for d in domains if d.namespace == namespace), None)

             if domain is None:
                 logger.warning(f"LLM 返回的领域不存在: {namespace}")
                 domain = next((d for d in domains if d.namespace == 'default'), domains[0])
                 confidence = 0.0

             return DomainClassificationResult(
                 namespace=domain.namespace,
                 display_name=domain.display_name,
                 confidence=confidence,
                 method='llm',
                 reasoning=reasoning,
                 alternatives=alternatives,
                 fallback_to_cross_domain=(confidence < self.config.llm_confidence_threshold),
                 metadata={
                     'model': self.config.llm_model,
                     'temperature': self.config.llm_temperature
                 }
             )

         def _create_default_result(self, reason: str) -> DomainClassificationResult:
             """创建默认结果"""
             return DomainClassificationResult(
                 namespace='default',
                 display_name='默认知识库',
                 confidence=0.0,
                 method='llm',
                 reasoning=reason,
                 alternatives=[],
                 fallback_to_cross_domain=True,
                 metadata={}
             )
     ```

2. **Prompt 优化**

   - [ ] 测试不同 Prompt 模板
   - [ ] 添加 Few-shot 示例
   - [ ] 优化 JSON Schema

3. **单元测试**

   文件: `backend/tests/services/test_llm_classifier.py` (新建)

   - [ ] 测试 LLM 分类准确性
   - [ ] 测试 JSON 解析
   - [ ] 测试异常处理
   - [ ] 测试超时处理
   - [ ] Mock LLM 调用

**交付物**:
- ✅ LLMDomainClassifier 实现
- ✅ Prompt 模板优化
- ✅ 单元测试

---

### 任务 4.2: LLM 分类缓存

**优先级**: P1
**预计时间**: 1 天
**依赖**: 任务 4.1

#### 子任务清单

1. **实现分类结果缓存**

   文件: `backend/app/services/classification_cache.py` (新建)

   - [ ] **Redis 缓存实现**
     ```python
     import redis
     import hashlib
     import json
     from typing import Optional

     class ClassificationCache:
         """分类结果缓存"""

         def __init__(self, redis_client: redis.Redis, ttl: int = 300):
             self.redis = redis_client
             self.ttl = ttl
             self.prefix = "domain_classification:"

         def _get_cache_key(self, query: str, method: str) -> str:
             """生成缓存键"""
             content = f"{query}:{method}"
             hash_value = hashlib.md5(content.encode()).hexdigest()
             return f"{self.prefix}{hash_value}"

         async def get(
             self,
             query: str,
             method: str
         ) -> Optional[DomainClassificationResult]:
             """获取缓存的分类结果"""
             key = self._get_cache_key(query, method)

             try:
                 cached = self.redis.get(key)
                 if cached:
                     data = json.loads(cached)
                     return DomainClassificationResult(**data)
             except Exception as e:
                 logger.warning(f"缓存读取失败: {e}")

             return None

         async def set(
             self,
             query: str,
             method: str,
             result: DomainClassificationResult
         ):
             """缓存分类结果"""
             key = self._get_cache_key(query, method)

             try:
                 data = result.to_dict()
                 self.redis.setex(key, self.ttl, json.dumps(data))
             except Exception as e:
                 logger.warning(f"缓存写入失败: {e}")

         async def invalidate(self, query: str = None):
             """清除缓存"""
             if query:
                 # 清除特定查询的缓存
                 for method in ['keyword', 'llm', 'hybrid']:
                     key = self._get_cache_key(query, method)
                     self.redis.delete(key)
             else:
                 # 清除所有分类缓存
                 keys = self.redis.keys(f"{self.prefix}*")
                 if keys:
                     self.redis.delete(*keys)
     ```

   - [ ] **集成到分类器**
     ```python
     # 在 LLMDomainClassifier 中
     async def classify(self, query: str, context: Optional[Dict] = None):
         # 1. 检查缓存
         if self.cache:
             cached_result = await self.cache.get(query, 'llm')
             if cached_result:
                 logger.info(f"缓存命中: {query[:50]}")
                 return cached_result

         # 2. 执行分类
         result = await self._do_classify(query, context)

         # 3. 写入缓存
         if self.cache:
             await self.cache.set(query, 'llm', result)

         return result
     ```

2. **缓存管理 API**

   文件: `backend/app/routers/knowledge_domains.py`

   - [ ] **DELETE /api/knowledge-domains/classify/cache** - 清除缓存
     ```python
     @router.delete("/knowledge-domains/classify/cache")
     async def clear_classification_cache(
         query: Optional[str] = None,
         current_user: User = Depends(require_admin)
     ):
         """清除分类缓存"""
         from app.services.classification_cache import classification_cache

         await classification_cache.invalidate(query)

         return {"message": "缓存已清除"}
     ```

3. **缓存统计**

   - [ ] 缓存命中率统计
   - [ ] 缓存大小监控

**交付物**:
- ✅ ClassificationCache 实现
- ✅ 集成到分类器
- ✅ 缓存管理 API

---

### 任务 4.3: Prompt 工程和优化

**优先级**: P1
**预计时间**: 2 天
**依赖**: 任务 4.1

#### 子任务清单

1. **创建 Prompt 模板库**

   文件: `backend/app/prompts/domain_classification.py` (新建)

   - [ ] **基础模板**
     ```python
     BASE_CLASSIFICATION_PROMPT = """你是一个领域分类专家..."""
     ```

   - [ ] **Few-shot 模板**
     ```python
     FEW_SHOT_CLASSIFICATION_PROMPT = """你是一个领域分类专家...

示例 1:
用户问题: API 认证失败怎么办
分析: 问题涉及 API 技术问题
领域: technical_docs
置信度: 0.95

示例 2:
用户问题: 我要退货
分析: 问题涉及退货服务
领域: product_support
置信度: 0.90

现在,请分析下面的用户问题:
用户问题: {query}
"""
     ```

   - [ ] **中文优化模板**
   - [ ] **多意图识别模板**

2. **A/B 测试框架**

   - [ ] 支持多个 Prompt 版本
   - [ ] 记录每个版本的准确率
   - [ ] 自动选择最佳 Prompt

3. **Prompt 评估工具**

   文件: `backend/scripts/evaluate_prompts.py` (新建)

   - [ ] **评估脚本**
     ```python
     import asyncio
     from app.services.llm_domain_classifier import LLMDomainClassifier
     from app.prompts.domain_classification import *

     async def evaluate_prompt(test_cases, prompt_template):
         """评估 Prompt 准确率"""
         correct = 0
         total = len(test_cases)

         for case in test_cases:
             result = await classify_with_prompt(case['query'], prompt_template)
             if result.namespace == case['expected']:
                 correct += 1

         accuracy = correct / total
         return accuracy

     # 测试用例
     TEST_CASES = [
         {'query': 'API 认证失败', 'expected': 'technical_docs'},
         {'query': '我要退货', 'expected': 'product_support'},
         # ... 更多测试用例
     ]

     # 评估多个 Prompt
     prompts = [BASE_CLASSIFICATION_PROMPT, FEW_SHOT_CLASSIFICATION_PROMPT]
     for i, prompt in enumerate(prompts):
         accuracy = await evaluate_prompt(TEST_CASES, prompt)
         print(f"Prompt {i+1} 准确率: {accuracy:.2%}")
     ```

**交付物**:
- ✅ Prompt 模板库
- ✅ A/B 测试框架
- ✅ Prompt 评估工具
- ✅ 评估报告

---

## Week 3: 混合分类器

### 任务 5.1: 混合分类器实现

**优先级**: P0
**预计时间**: 2 天
**依赖**: 任务 4.3

#### 子任务清单

1. **实现 HybridDomainClassifier**

   文件: `backend/app/services/hybrid_domain_classifier.py` (新建)

   - [ ] **混合分类器实现**
     ```python
     from app.services.domain_classifier import DomainClassifier, DomainClassificationResult
     from app.services.keyword_domain_classifier import KeywordDomainClassifier
     from app.services.llm_domain_classifier import LLMDomainClassifier

     class HybridDomainClassifier(DomainClassifier):
         """混合领域分类器(关键词 + LLM)"""

         def __init__(self, db: Session, config: ClassifierConfig):
             super().__init__(db)
             self.config = config
             self.keyword_classifier = KeywordDomainClassifier(db, config)
             self.llm_classifier = LLMDomainClassifier(db, config)

         async def initialize(self):
             """初始化子分类器"""
             await self.keyword_classifier.initialize()

         async def classify(
             self,
             query: str,
             context: Optional[Dict[str, Any]] = None
         ) -> DomainClassificationResult:
             """
             混合分类策略:

             1. 首先尝试关键词分类
             2. 如果置信度 >= threshold,直接返回
             3. 否则,使用 LLM 分类作为 fallback
             4. 如果 LLM 置信度仍然低,建议跨领域检索
             """

             # 步骤 1: 关键词分类
             keyword_result = await self.keyword_classifier.classify(query, context)

             # 步骤 2: 高置信度直接返回
             if keyword_result.confidence >= self.config.hybrid_llm_fallback_threshold:
                 logger.info(f"关键词分类命中(置信度: {keyword_result.confidence:.2f}): {query[:50]}")
                 keyword_result.method = 'hybrid(keyword)'
                 return keyword_result

             # 步骤 3: LLM Fallback
             logger.info(f"关键词分类置信度低({keyword_result.confidence:.2f}),使用 LLM: {query[:50]}")

             try:
                 llm_result = await self.llm_classifier.classify(query, context)

                 # 步骤 4: 选择更可信的结果
                 if llm_result.confidence > keyword_result.confidence:
                     llm_result.method = 'hybrid(llm)'
                     llm_result.metadata['keyword_confidence'] = keyword_result.confidence
                     return llm_result
                 else:
                     keyword_result.method = 'hybrid(keyword)'
                     keyword_result.metadata['llm_confidence'] = llm_result.confidence
                     return keyword_result

             except Exception as e:
                 logger.error(f"LLM 分类失败,降级到关键词结果: {e}")
                 keyword_result.method = 'hybrid(keyword-fallback)'
                 keyword_result.metadata['llm_error'] = str(e)
                 return keyword_result
     ```

2. **智能 Fallback 策略**

   - [ ] **用户历史偏好**
     ```python
     def _get_user_preferred_domain(self, context: Optional[Dict]) -> Optional[str]:
         """获取用户偏好领域"""
         if not context or 'user_id' not in context:
             return None

         user_id = context['user_id']

         # 查询用户最近访问的领域
         recent_queries = db.query(QueryLog).filter(
             QueryLog.user_id == user_id
         ).order_by(QueryLog.created_at.desc()).limit(10).all()

         if len(recent_queries) == 0:
             return None

         # 统计领域频率
         domain_counts = {}
         for q in recent_queries:
             namespace = q.namespace
             domain_counts[namespace] = domain_counts.get(namespace, 0) + 1

         # 返回最高频领域
         preferred = max(domain_counts, key=domain_counts.get)
         return preferred
     ```

   - [ ] **会话上下文**
     ```python
     def _get_session_domain(self, context: Optional[Dict]) -> Optional[str]:
         """获取会话当前领域"""
         if not context or 'session_id' not in context:
             return None

         session_id = context['session_id']
         session = db.query(ChatSession).filter(
             ChatSession.id == session_id
         ).first()

         if session and session.metadata:
             return session.metadata.get('current_namespace')

         return None
     ```

3. **分类决策日志**

   - [ ] 记录每次分类的决策过程
   - [ ] 用于后续分析和优化

**交付物**:
- ✅ HybridDomainClassifier 实现
- ✅ 智能 Fallback 策略
- ✅ 分类决策日志

---

### 任务 5.2: 分类器工厂和服务集成

**优先级**: P0
**预计时间**: 1 天
**依赖**: 任务 5.1

#### 子任务清单

1. **创建分类器工厂**

   文件: `backend/app/services/classifier_factory.py` (新建)

   - [ ] **工厂类**
     ```python
     from enum import Enum

     class ClassifierType(Enum):
         KEYWORD = "keyword"
         LLM = "llm"
         HYBRID = "hybrid"

     class ClassifierFactory:
         """分类器工厂"""

         @staticmethod
         def create_classifier(
             classifier_type: ClassifierType,
             db: Session,
             config: ClassifierConfig
         ) -> DomainClassifier:
             """创建分类器实例"""

             if classifier_type == ClassifierType.KEYWORD:
                 classifier = KeywordDomainClassifier(db, config)
             elif classifier_type == ClassifierType.LLM:
                 classifier = LLMDomainClassifier(db, config)
             elif classifier_type == ClassifierType.HYBRID:
                 classifier = HybridDomainClassifier(db, config)
             else:
                 raise ValueError(f"未知的分类器类型: {classifier_type}")

             return classifier

         @staticmethod
         async def get_default_classifier(
             db: Session
         ) -> DomainClassifier:
             """获取默认分类器(Hybrid)"""
             config = ClassifierConfig()
             classifier = ClassifierFactory.create_classifier(
                 ClassifierType.HYBRID,
                 db,
                 config
             )
             await classifier.initialize()
             return classifier
     ```

2. **集成到查询 API**

   文件: `backend/app/routers/query.py`

   - [ ] **修改查询接口,添加自动分类**
     ```python
     @router.post("/query")
     async def query_documents(
         request: QueryRequest,
         db: Session = Depends(get_db),
         current_user: User = Depends(get_current_active_user)
     ):
         """
         查询文档(支持自动领域分类)

         参数:
         - query: 查询内容
         - namespace: 指定领域(可选,如果不提供则自动分类)
         - retrieval_mode: 'single'/'cross'/'auto'
         """

         namespace = request.namespace
         retrieval_mode = request.retrieval_mode or 'auto'

         classification_result = None

         # 自动分类
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

         # 执行检索(后续任务实现)
         # ...

         return {
             "domain_classification": classification_result.to_dict() if classification_result else None,
             "retrieval_mode": retrieval_mode,
             "results": []  # 检索结果(第三阶段实现)
         }
     ```

3. **更新文档上传自动分类**

   文件: `backend/app/routers/upload.py`

   - [ ] **支持自动分类文档**
     ```python
     @router.post("/upload")
     async def upload_document(
         file: UploadFile,
         namespace: Optional[str] = Form(None),
         auto_classify: bool = Form(True),
         ...
     ):
         """上传文档(支持自动分类)"""

         # 如果未指定 namespace 且启用自动分类
         if not namespace and auto_classify:
             # 提取文档文本用于分类
             text_sample = extract_text_sample(file, max_length=1000)

             classifier = await ClassifierFactory.get_default_classifier(db)
             classification_result = await classifier.classify(text_sample)

             namespace = classification_result.namespace
             domain_confidence = classification_result.confidence

         else:
             namespace = namespace or 'default'
             domain_confidence = 1.0

         # 保存文档
         document = Document(
             filename=file.filename,
             namespace=namespace,
             domain_confidence=domain_confidence,
             ...
         )
         db.add(document)
         db.commit()

         return {
             "document_id": document.id,
             "namespace": namespace,
             "domain_confidence": domain_confidence,
             ...
         }
     ```

**交付物**:
- ✅ ClassifierFactory 实现
- ✅ 集成到查询 API
- ✅ 集成到上传 API

---

### 任务 5.3: 分类准确性评估

**优先级**: P1
**预计时间**: 2 天
**依赖**: 任务 5.2

#### 子任务清单

1. **创建标注数据集**

   文件: `backend/tests/data/classification_test_set.json` (新建)

   - [ ] **人工标注测试用例**
     ```json
     [
       {
         "id": 1,
         "query": "API 接口认证失败怎么办",
         "expected_namespace": "technical_docs",
         "expected_confidence": 0.9,
         "tags": ["api", "authentication", "error"]
       },
       {
         "id": 2,
         "query": "我要退货,流程是什么",
         "expected_namespace": "product_support",
         "expected_confidence": 0.95,
         "tags": ["refund", "process"]
       },
       // ... 至少 100 个测试用例
     ]
     ```

   - [ ] 收集 100+ 真实查询样本
   - [ ] 人工标注正确领域
   - [ ] 标注难度等级(简单/中等/困难)

2. **评估脚本**

   文件: `backend/scripts/evaluate_classifiers.py` (新建)

   - [ ] **评估所有分类器**
     ```python
     import asyncio
     import json
     from app.services.classifier_factory import ClassifierFactory, ClassifierType

     async def evaluate_classifier(classifier, test_set):
         """评估分类器准确率"""
         results = {
             'total': len(test_set),
             'correct': 0,
             'confident_correct': 0,
             'by_difficulty': {
                 'easy': {'total': 0, 'correct': 0},
                 'medium': {'total': 0, 'correct': 0},
                 'hard': {'total': 0, 'correct': 0}
             },
             'avg_confidence': 0.0,
             'avg_latency': 0.0
         }

         for case in test_set:
             start_time = time.time()

             result = await classifier.classify(case['query'])

             latency = (time.time() - start_time) * 1000  # ms

             # 统计准确率
             if result.namespace == case['expected_namespace']:
                 results['correct'] += 1
                 if result.confidence >= 0.7:
                     results['confident_correct'] += 1

             # 按难度统计
             difficulty = case.get('difficulty', 'medium')
             results['by_difficulty'][difficulty]['total'] += 1
             if result.namespace == case['expected_namespace']:
                 results['by_difficulty'][difficulty]['correct'] += 1

             results['avg_confidence'] += result.confidence
             results['avg_latency'] += latency

         # 计算平均值
         results['accuracy'] = results['correct'] / results['total']
         results['confident_accuracy'] = results['confident_correct'] / results['total']
         results['avg_confidence'] /= results['total']
         results['avg_latency'] /= results['total']

         return results

     async def main():
         # 加载测试集
         with open('tests/data/classification_test_set.json') as f:
             test_set = json.load(f)

         # 评估所有分类器
         classifiers = {
             'Keyword': ClassifierType.KEYWORD,
             'LLM': ClassifierType.LLM,
             'Hybrid': ClassifierType.HYBRID
         }

         for name, classifier_type in classifiers.items():
             print(f"\n=== 评估 {name} 分类器 ===")

             classifier = ClassifierFactory.create_classifier(classifier_type, db, config)
             await classifier.initialize()

             results = await evaluate_classifier(classifier, test_set)

             print(f"总样本数: {results['total']}")
             print(f"准确率: {results['accuracy']:.2%}")
             print(f"高置信准确率: {results['confident_accuracy']:.2%}")
             print(f"平均置信度: {results['avg_confidence']:.2f}")
             print(f"平均延迟: {results['avg_latency']:.1f} ms")
             print(f"\n按难度统计:")
             for difficulty, stats in results['by_difficulty'].items():
                 if stats['total'] > 0:
                     acc = stats['correct'] / stats['total']
                     print(f"  {difficulty}: {acc:.2%} ({stats['correct']}/{stats['total']})")

     asyncio.run(main())
     ```

3. **生成评估报告**

   文件: `docs/evaluation/CLASSIFICATION_EVALUATION_REPORT.md` (新建)

   - [ ] 各分类器准确率对比
   - [ ] 性能对比(延迟)
   - [ ] 错误案例分析
   - [ ] 优化建议

**交付物**:
- ✅ 标注测试数据集(100+ 样本)
- ✅ 评估脚本
- ✅ 评估报告

---

## 阶段验收标准

### 功能验收

- [ ] ✅ 关键词分类器准确率 > 70%
- [ ] ✅ LLM 分类器准确率 > 85%
- [ ] ✅ 混合分类器准确率 > 88%
- [ ] ✅ 分类延迟 P95 < 300ms(混合模式)
- [ ] ✅ 缓存命中率 > 40%
- [ ] ✅ 分类测试工具正常工作
- [ ] ✅ 查询 API 集成分类功能
- [ ] ✅ 上传 API 支持自动分类

### 质量验收

- [ ] ✅ 单元测试覆盖率 > 85%
- [ ] ✅ 集成测试全部通过
- [ ] ✅ 评估报告完整,包含错误案例分析
- [ ] ✅ Prompt 模板经过 A/B 测试优化

### 性能验收

- [ ] ✅ 关键词分类延迟 < 50ms
- [ ] ✅ LLM 分类延迟 < 500ms
- [ ] ✅ 混合分类延迟(有缓存) < 100ms
- [ ] ✅ 支持并发分类请求(QPS > 100)

---

## 风险与应对

### 风险 1: LLM API 不稳定

**概率**: 中
**影响**: 高

**应对措施**:
- 设置超时和重试机制
- Fallback 到关键词分类
- 多 LLM 提供商支持

### 风险 2: 分类准确率不达标

**概率**: 中
**影响**: 高

**应对措施**:
- 持续优化 Prompt
- 扩充关键词库
- 人工反馈闭环

### 风险 3: 分类延迟过高

**概率**: 低
**影响**: 中

**应对措施**:
- 启用缓存
- 使用轻量级 LLM
- 异步预分类

---

## 下一阶段预告

完成第二阶段后,将进入**第三阶段:检索集成**,主要任务:

1. 单领域检索实现
2. 跨领域检索实现
3. 前端检索界面优化
4. 领域权重和排序优化

第二阶段的智能分类将为第三阶段的精准检索提供关键支持。
