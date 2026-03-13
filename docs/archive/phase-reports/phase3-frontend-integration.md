# Phase 3 前端集成 - 多领域智能检索UI

## 📅 完成时间
2025-11-17

## ✅ 已完成的组件和服务

### 1. 查询服务 (queryService.js) ✅

#### frontend/src/services/queryService.js (新建, 332行)

**核心功能:**

1. **查询API v2调用**
   ```javascript
   async function queryDocumentsV2(params) {
     // 调用后端 /api/query/v2
     // 支持所有检索参数
     return {
       success: true,
       data: response.data
     }
   }
   ```

2. **结果格式化**
   ```javascript
   function formatQueryResults(queryResponse) {
     // 转换API响应为前端友好格式
     // 格式化分类、结果、统计等
     return {
       queryId, query, classification,
       results, crossDomainResults, stats
     }
   }
   ```

3. **辅助工具函数**
   - `getMethodInfo()` - 获取检索方法显示信息
   - `getModeInfo()` - 获取检索模式显示信息
   - `highlightKeywords()` - 关键词高亮
   - `getConfidenceLevel()` - 计算置信度等级

### 2. 查询结果展示组件 (QueryResult.vue) ✅

#### frontend/src/components/query/QueryResult.vue (新建, 365行)

**UI特性:**

1. **查询信息头部**
   - 显示查询文本
   - 检索模式和方法标签
   - 延迟和结果数统计

2. **领域分类展示**
   - 主领域徽章
   - 置信度标签(高/中/低)
   - 备选领域列表

3. **结果列表**
   ```vue
   <div class="result-item">
     <!-- 排名、领域徽章、得分 -->
     <div class="result-header">
       <span>#1</span>
       <DomainBadge />
       <el-tag>92.5%</el-tag>
     </div>

     <!-- 高亮的内容 -->
     <div class="result-content">
       <p v-html="highlightText(...)"></p>
     </div>

     <!-- 文档信息 -->
     <div class="result-footer">
       <span>API使用指南.pdf</span>
       <span>块 #2</span>
     </div>
   </div>
   ```

4. **样式特点**
   - 毛玻璃效果卡片
   - 霓虹蓝紫渐变强调
   - Hover动画效果
   - 响应式布局

### 3. 跨领域结果分组组件 (CrossDomainGroups.vue) ✅

#### frontend/src/components/query/CrossDomainGroups.vue (新建, 256行)

**功能特点:**

1. **折叠面板展示**
   ```vue
   <el-collapse>
     <el-collapse-item
       v-for="group in sortedGroups"
       :name="group.namespace"
     >
       <template #title>
         <DomainBadge />
         <el-tag>{{ group.count }} 个结果</el-tag>
       </template>

       <div class="group-content">
         <!-- 前3个结果 -->
         <div v-for="result in group.results">
           ...
         </div>

         <!-- 查看更多按钮 -->
         <el-button @click="loadMore">
           查看更多 ({{ remaining }} 个)
         </el-button>
       </div>
     </el-collapse-item>
   </el-collapse>
   ```

2. **智能排序**
   - 按结果数量降序
   - 自动展开第一个领域

3. **交互功能**
   - 点击展开/折叠
   - 加载更多结果
   - 关键词高亮

### 4. 检索设置面板 (RetrievalSettings.vue) ✅

#### frontend/src/components/query/RetrievalSettings.vue (新建, 338行)

**配置选项:**

1. **检索方法选择**
   - 混合(推荐) - ⚡
   - 向量 - 🔍
   - BM25 - 🔑

2. **检索模式选择**
   - 自动 - 🤖
   - 单领域 - 🎯
   - 跨领域 - 🌐

3. **高级设置(可折叠)**
   - 结果数量: 1-50
   - 混合权重: 0.0-1.0 (滑块)
   - 相似度阈值: 0.0-1.0

4. **UI组件**
   ```vue
   <el-dropdown trigger="click">
     <el-button>检索设置</el-button>

     <template #dropdown>
       <div class="settings-panel">
         <!-- 检索方法 -->
         <el-radio-group v-model="method">
           <el-radio label="hybrid">混合(推荐)</el-radio>
           <el-radio label="vector">向量</el-radio>
           <el-radio label="bm25">BM25</el-radio>
         </el-radio-group>

         <!-- 检索模式 -->
         <el-radio-group v-model="mode">
           ...
         </el-radio-group>

         <!-- 高级设置 -->
         <el-collapse>
           <el-collapse-item name="advanced">
             <!-- 滑块、数字输入等 -->
           </el-collapse-item>
         </el-collapse>

         <!-- 应用/重置按钮 -->
         <div class="actions">
           <el-button @click="reset">重置</el-button>
           <el-button type="primary" @click="apply">应用</el-button>
         </div>
       </div>
     </template>
   </el-dropdown>
   ```

## 📊 组件架构

```
查询系统前端架构
├── 服务层 (services/)
│   └── queryService.js - API调用和数据格式化
│
├── 组件层 (components/query/)
│   ├── QueryResult.vue - 主结果展示
│   ├── CrossDomainGroups.vue - 跨领域分组
│   └── RetrievalSettings.vue - 配置面板
│
├── 页面层 (views/)
│   └── Chat.vue - 集成查询功能
│
└── 已有组件 (components/domain/)
    ├── DomainBadge.vue - 领域徽章
    └── DomainSelector.vue - 领域选择器
```

## 🎨 视觉设计

### 设计系统

**色彩:**
- 主色调: 霓虹蓝 `#00D4FF`
- 辅助色: 霓虹紫 `#9013FE`
- 成功: 霓虹绿 `#7ED321`
- 警告: 橙色 `#F5A623`
- 错误: 红色 `#D0021B`

**效果:**
- 毛玻璃: `backdrop-filter: blur(10px)`
- 边框: `rgba(255, 255, 255, 0.1)`
- 阴影: `0 8px 24px rgba(0, 0, 0, 0.3)`
- 渐变: `linear-gradient(135deg, blue, purple)`

**动画:**
- 过渡: `transition: all 0.3s ease`
- Hover上移: `transform: translateY(-2px)`
- 霓虹光晕: `box-shadow: 0 0 12px rgba(0, 212, 255, 0.4)`

### 组件样式特点

**1. 卡片容器**
```scss
.tech-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(10px);

  &:hover {
    border-color: var(--tech-border-hover);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
```

**2. 标题文本**
```scss
.title-gradient {
  background: linear-gradient(
    135deg,
    var(--tech-neon-blue),
    var(--tech-neon-purple)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

**3. 关键词高亮**
```scss
mark.highlight {
  background: rgba(0, 212, 255, 0.2);
  color: var(--tech-neon-blue);
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 600;
}
```

## 🚀 集成到 Chat 页面

### 使用方式

```vue
<template>
  <div class="chat-main">
    <!-- 标题栏 -->
    <div class="chat-header">
      <h2>{{ session.title }}</h2>

      <!-- 添加检索设置 -->
      <RetrievalSettings
        v-model="retrievalSettings"
        @apply="onSettingsApply"
      />
    </div>

    <!-- 消息列表 -->
    <ChatWindow :messages="messages" />

    <!-- 显示查询结果(当RAG开启时) -->
    <QueryResult
      v-if="currentQueryResult && useRAG"
      :result="currentQueryResult"
    />

    <!-- 输入框 -->
    <InputBar
      v-model="message"
      @send="sendWithQuery"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RetrievalSettings from '@/components/query/RetrievalSettings.vue'
import QueryResult from '@/components/query/QueryResult.vue'
import { queryDocumentsV2, formatQueryResults } from '@/services/queryService'

const retrievalSettings = ref({
  method: 'hybrid',
  mode: 'auto',
  topK: 10,
  alpha: 0.5
})

const currentQueryResult = ref(null)
const useRAG = ref(true)

async function sendWithQuery(message) {
  if (!useRAG.value) {
    // 普通聊天
    await sendMessage(message)
    return
  }

  // 先执行查询v2
  const queryResponse = await queryDocumentsV2({
    query: message,
    ...retrievalSettings.value
  })

  if (queryResponse.success) {
    // 格式化并显示结果
    currentQueryResult.value = formatQueryResults(queryResponse.data)

    // 构建带上下文的消息发送给LLM
    const context = currentQueryResult.value.results
      .slice(0, 5)
      .map(r => r.content)
      .join('\n\n')

    await sendMessage(message, { context })
  } else {
    // 查询失败,降级为普通聊天
    await sendMessage(message)
  }
}
</script>
```

## 📱 响应式设计

### 断点设置

```scss
// 移动端
@media (max-width: 768px) {
  .query-result {
    .result-item {
      padding: 12px;

      .result-header {
        flex-wrap: wrap;
        gap: 8px;
      }
    }
  }

  .cross-domain-groups {
    .group-result-item {
      font-size: 13px;
    }
  }
}

// 平板
@media (min-width: 769px) and (max-width: 1024px) {
  .query-header {
    .query-meta {
      flex-wrap: wrap;
    }
  }
}

// 桌面
@media (min-width: 1025px) {
  .results-list {
    grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  }
}
```

## 🎯 用户交互流程

### 标准查询流程

```
1. 用户输入查询
   ↓
2. 检查RAG开关
   ├─ 关闭 → 直接发送LLM
   └─ 开启 → 继续
   ↓
3. 调用查询v2 API
   - 使用当前检索设置
   - 自动领域分类
   ↓
4. 展示查询结果
   ├─ 单领域: 显示结果列表
   └─ 跨领域: 显示分组折叠面板
   ↓
5. 提取相关上下文
   - 取Top 5结果
   - 拼接内容
   ↓
6. 发送给LLM
   - 附带上下文
   - 生成回答
   ↓
7. 流式显示回答
```

### 高级交互

**1. 实时配置调整**
```javascript
// 用户点击"检索设置"
→ 弹出设置面板
→ 调整参数(方法、模式、权重等)
→ 点击"应用"
→ 立即生效(下次查询使用新配置)
```

**2. 跨领域结果交互**
```javascript
// 点击领域分组
→ 展开该领域结果
→ 查看前3个结果
→ 点击"查看更多"
→ 加载该领域所有结果
```

**3. 关键词高亮**
```javascript
// 用户查询: "API 配置 密钥"
→ 分词: ["API", "配置", "密钥"]
→ 在结果中高亮匹配
→ 显示霓虹蓝背景
```

## 🔧 配置参数说明

### retrievalSettings 对象

```javascript
{
  // 检索方法
  method: 'hybrid',    // 'vector' | 'bm25' | 'hybrid'

  // 检索模式
  mode: 'auto',        // 'auto' | 'single' | 'cross'

  // 指定领域(单领域模式)
  namespace: null,     // string | null

  // 返回结果数
  topK: 10,            // 1-50

  // 混合权重(仅hybrid)
  alpha: 0.5,          // 0.0(纯BM25) - 1.0(纯向量)

  // 相似度阈值(仅vector)
  similarityThreshold: 0.0  // 0.0-1.0
}
```

### 默认配置推荐

```javascript
// 通用场景(推荐)
{
  method: 'hybrid',
  mode: 'auto',
  topK: 10,
  alpha: 0.5
}

// 精确查询
{
  method: 'bm25',
  mode: 'single',
  namespace: 'technical_docs',
  topK: 5
}

// 语义查询
{
  method: 'vector',
  mode: 'auto',
  topK: 15,
  similarityThreshold: 0.3
}

// 探索性查询
{
  method: 'hybrid',
  mode: 'cross',
  topK: 20,
  alpha: 0.6
}
```

## 📦 依赖组件清单

### 需要的现有组件

1. **DomainBadge.vue** ✅
   - 路径: `frontend/src/components/domain/DomainBadge.vue`
   - 用途: 显示领域徽章

2. **DomainSelector.vue** ✅
   - 路径: `frontend/src/components/domain/DomainSelector.vue`
   - 用途: 选择单个领域

### Element Plus 组件

```javascript
import {
  ElButton,
  ElTag,
  ElIcon,
  ElDropdown,
  ElDropdownMenu,
  ElRadioGroup,
  ElRadio,
  ElCollapse,
  ElCollapseItem,
  ElSlider,
  ElInputNumber,
  ElTooltip,
  ElEmpty,
  ElMessage
} from 'element-plus'
```

### 图标

```javascript
import {
  Document,
  Connection,
  Setting,
  Search,
  Key,
  MagicStick,
  Position,
  Tools,
  QuestionFilled
} from '@element-plus/icons-vue'
```

## 🎓 使用示例

### 1. 基础查询

```javascript
import { queryDocumentsV2, formatQueryResults } from '@/services/queryService'

// 自动模式查询
const response = await queryDocumentsV2({
  query: '如何配置API密钥?',
  method: 'hybrid',
  mode: 'auto',
  topK: 10
})

if (response.success) {
  const result = formatQueryResults(response.data)
  console.log('查询结果:', result)
  // {
  //   queryId: 'uuid-123',
  //   classification: { namespace: 'technical_docs', confidence: 0.85 },
  //   results: [...],
  //   stats: { latencyMs: 125.5, totalCandidates: 10 }
  // }
}
```

### 2. 跨领域查询

```javascript
// 指定多领域
const response = await queryDocumentsV2({
  query: '退货流程',
  mode: 'cross',
  namespaces: ['product_support', 'order_management'],
  method: 'hybrid',
  topK: 15
})

const result = formatQueryResults(response.data)
console.log('跨领域结果:', result.crossDomainResults)
// [
//   { namespace: 'product_support', count: 8, results: [...] },
//   { namespace: 'order_management', count: 7, results: [...] }
// ]
```

### 3. 精确查询

```javascript
// BM25 + 单领域
const response = await queryDocumentsV2({
  query: 'API authentication token',
  method: 'bm25',
  mode: 'single',
  namespace: 'technical_docs',
  topK: 5
})
```

### 4. 语义查询

```javascript
// 纯向量 + 相似度阈值
const response = await queryDocumentsV2({
  query: '如何提高系统性能',
  method: 'vector',
  mode: 'auto',
  topK: 10,
  similarityThreshold: 0.3
})
```

## 📈 性能优化建议

### 已实现
- ✅ 组件懒加载
- ✅ 结果虚拟滚动准备
- ✅ 防抖输入(500ms)
- ✅ 结果缓存(本地)

### 待优化
- [ ] 骨架屏加载
- [ ] 图片懒加载
- [ ] 分页加载结果
- [ ] IndexedDB持久化
- [ ] Web Worker处理高亮

## 🐛 错误处理

### API错误

```javascript
try {
  const response = await queryDocumentsV2(params)
  if (!response.success) {
    ElMessage.error(`查询失败: ${response.error}`)
    // 降级处理
  }
} catch (error) {
  ElMessage.error('网络错误,请重试')
  console.error('查询异常:', error)
}
```

### 组件错误边界

```vue
<el-empty
  v-if="error"
  description="加载失败"
  :image-size="120"
>
  <el-button @click="retry">重试</el-button>
</el-empty>
```

## 🎉 总结

### 完成的工作

- ✅ 查询服务 API封装
- ✅ 结果展示组件
- ✅ 跨领域分组组件
- ✅ 检索设置面板
- ✅ 完整的样式系统
- ✅ 交互流程设计

### 技术特点

1. **组件化**: 高内聚低耦合
2. **响应式**: 适配多端设备
3. **可配置**: 灵活的检索参数
4. **可扩展**: 易于添加新功能
5. **美观**: 科技感UI设计

### 代码量统计

- 查询服务: ~332行
- 结果展示: ~365行
- 跨领域分组: ~256行
- 检索设置: ~338行
- **总计: ~1291行**

### 下一步

**优先级:**
1. 集成到 Chat.vue 页面
2. 完善错误处理和加载状态
3. 添加单元测试
4. 性能优化和监控
5. 用户反馈收集

准备好部署和测试! 🚀
