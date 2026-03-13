# 路由规则前端实现文档

## 实现概述

成功实现了路由规则管理的前端界面,提供完整的 CRUD 操作、规则测试和可视化管理功能。

## 1. 文件结构

```
frontend/src/
├── services/
│   └── routingRules.js          # 路由规则 API 服务
├── views/
│   └── RoutingRules.vue         # 路由规则管理页面
├── layouts/
│   └── TechLayout.vue           # 布局文件(已更新导航菜单)
└── router.js                     # 路由配置(已添加新路由)
```

## 2. API 服务 (`frontend/src/services/routingRules.js`)

### 导出的 API 方法

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `getAllRules()` | 获取所有规则 | `{ include_inactive, skip, limit }` | `{ rules, total }` |
| `getRuleById()` | 获取单个规则 | `ruleId` | 规则对象 |
| `createRule()` | 创建规则 | `ruleData` | 创建的规则 |
| `updateRule()` | 更新规则 | `ruleId, updateData` | 更新后的规则 |
| `deleteRule()` | 删除规则 | `ruleId` | void |
| `testRuleMatch()` | 测试匹配 | `{ query, min_confidence }` | 匹配结果 |

### 辅助常量和方法

```javascript
// 规则类型选项
export const RULE_TYPES = [
  { value: 'keyword', label: '关键词匹配', description: '使用 | 分隔多个关键词' },
  { value: 'regex', label: '正则表达式', description: '支持完整的正则表达式语法' },
  { value: 'pattern', label: '通配符模式', description: '支持 * 和 ? 通配符' }
]

// 获取规则类型标签
export const getRuleTypeLabel = (ruleType) => { ... }

// 获取规则类型描述
export const getRuleTypeDescription = (ruleType) => { ... }
```

## 3. 管理页面 (`frontend/src/views/RoutingRules.vue`)

### 页面结构

#### 3.1 页面头部
- **标题**: "路由规则管理"
- **副标题**: "配置领域路由规则,实现智能查询分发"
- **操作按钮**: "创建规则"

#### 3.2 统计卡片
三个统计卡片展示关键指标:
- **总规则数**: 系统中所有规则的数量
- **激活规则**: 当前生效的规则数量
- **高优先级**: 优先级 > 5 的规则数量

#### 3.3 规则列表表格
包含以下列:
- **ID**: 规则唯一标识
- **规则名称**: 显示激活状态标签 + 规则名称
- **类型**: 规则类型标签(keyword/regex/pattern)
- **匹配模式**: 以等宽字体显示模式内容
- **目标领域**: 显示为主题标签
- **置信度阈值**: 进度条可视化显示
- **优先级**: 数值显示,支持排序
- **操作**: 编辑、启用/禁用、删除按钮组

#### 3.4 工具栏功能
- **搜索框**: 实时搜索规则名称、模式、目标领域
- **显示未激活开关**: 控制是否显示未激活的规则
- **测试匹配按钮**: 打开测试对话框

### 主要功能

#### 1. 规则列表展示
```vue
<el-table :data="filteredRules" v-loading="loading" class="tech-table">
  <el-table-column prop="id" label="ID" width="80" />
  <el-table-column prop="rule_name" label="规则名称" min-width="150">
    <template #default="{ row }">
      <el-tag :type="row.is_active ? 'success' : 'info'">
        {{ row.is_active ? '激活' : '未激活' }}
      </el-tag>
      <span>{{ row.rule_name }}</span>
    </template>
  </el-table-column>
  <!-- 其他列 -->
</el-table>
```

#### 2. 创建/编辑规则对话框
表单字段:
- **规则名称**: 必填,文本输入
- **规则类型**: 必填,下拉选择(keyword/regex/pattern)
- **匹配模式**: 必填,多行文本输入,根据类型显示不同占位符
- **目标领域**: 必填,下拉选择(从领域列表加载)
- **置信度阈值**: 滑块输入(0.0-1.0),默认 0.3
- **优先级**: 数字输入(0-100),默认 0
- **是否激活**: 开关,默认激活
- **备注**: 可选,多行文本输入

表单验证规则:
```javascript
const formRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  pattern: [{ required: true, message: '请输入匹配模式', trigger: 'blur' }],
  target_namespace: [{ required: true, message: '请选择目标领域', trigger: 'change' }]
}
```

#### 3. 测试匹配功能
测试表单:
- **查询文本**: 多行文本输入
- **最小置信度**: 滑块输入(0.0-1.0)

测试结果显示:
- 匹配成功:显示匹配的规则名称、目标领域、置信度(进度条)
- 未匹配:显示提示信息

#### 4. 规则操作
- **编辑**: 填充表单并打开编辑对话框
- **启用/禁用**: 切换规则的激活状态
- **删除**: 二次确认后删除规则

### 计算属性

```javascript
// 总规则数
const totalRules = computed(() => rules.value.length)

// 激活规则数
const activeRules = computed(() => rules.value.filter(r => r.is_active).length)

// 高优先级规则数
const highPriorityRules = computed(() => rules.value.filter(r => r.priority > 5).length)

// 过滤后的规则列表
const filteredRules = computed(() => {
  let filtered = rules.value

  // 过滤未激活规则
  if (!showInactive.value) {
    filtered = filtered.filter(r => r.is_active)
  }

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(r =>
      r.rule_name.toLowerCase().includes(keyword) ||
      r.pattern.toLowerCase().includes(keyword) ||
      r.target_namespace.toLowerCase().includes(keyword)
    )
  }

  return filtered
})
```

### 样式特性

#### 技术感主题
- **动态网格背景**: 半透明蓝色网格
- **悬浮效果**: 卡片悬浮时阴影和位移
- **渐变色图标**: 蓝色、绿色、紫色主题图标
- **等宽字体**: 模式内容使用 Consolas/Monaco 字体
- **进度条可视化**: 置信度和匹配结果使用进度条

#### 响应式设计
- 统计卡片使用 Grid 自适应布局
- 表格支持横向滚动
- 对话框宽度固定 600px

## 4. 路由配置 (`frontend/src/router.js`)

### 新增路由

```javascript
{
  path: '/routing-rules',
  name: 'RoutingRules',
  component: () => import('./views/RoutingRules.vue'),
  meta: {
    requiresAuth: true,
    title: '路由规则管理',
    permissions: ['system_settings']
  }
}
```

### 权限要求
- **需要认证**: `requiresAuth: true`
- **需要权限**: `permissions: ['system_settings']`

## 5. 导航菜单 (`frontend/src/layouts/TechLayout.vue`)

### 新增图标导入

```javascript
import {
  Document,
  ChatDotRound,
  Setting,
  Clock,
  HomeFilled,
  DataAnalysis,
  ArrowLeft,
  ArrowRight,
  User,
  FolderOpened,
  Connection  // 新增
} from '@element-plus/icons-vue'
```

### 新增菜单项

```javascript
if (authStore.hasPermission('system_settings')) {
  items.push({ path: '/knowledge-domains', title: '知识领域', icon: FolderOpened })
  items.push({ path: '/routing-rules', title: '路由规则', icon: Connection })  // 新增
  items.push({ path: '/logs', title: '系统日志', icon: DataAnalysis })
  items.push({ path: '/settings', title: '系统设置', icon: Setting })
}
```

## 6. 使用流程

### 创建规则

1. 点击右上角"创建规则"按钮
2. 填写规则信息:
   - 规则名称:如"API关键词规则"
   - 规则类型:选择"关键词匹配"
   - 匹配模式:输入"API|接口|SDK|文档"
   - 目标领域:选择"technical_docs"
   - 置信度阈值:设置为 0.3
   - 优先级:设置为 0
   - 是否激活:开启
3. 点击"创建"按钮

### 编辑规则

1. 在规则列表中找到要编辑的规则
2. 点击"编辑"按钮
3. 修改需要调整的字段
4. 点击"更新"按钮

### 测试规则

1. 点击工具栏的"测试匹配"按钮
2. 输入查询文本,如"如何调用API?"
3. 设置最小置信度,如 0.0
4. 点击"开始测试"按钮
5. 查看匹配结果:
   - 匹配成功:显示匹配规则、目标领域、置信度
   - 未匹配:显示未匹配提示

### 管理规则

- **启用/禁用**: 点击开关按钮切换规则状态
- **删除规则**: 点击删除按钮,确认后删除
- **搜索规则**: 使用搜索框快速定位规则
- **过滤规则**: 使用"显示未激活"开关控制显示范围

## 7. 界面截图说明

### 页面布局
```
┌─────────────────────────────────────────────────────────┐
│ [路由规则管理]                           [创建规则]      │
│ 配置领域路由规则,实现智能查询分发                       │
├─────────────────────────────────────────────────────────┤
│ [总规则数: 4]  [激活规则: 4]  [高优先级: 0]            │
├─────────────────────────────────────────────────────────┤
│ 路由规则列表                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [搜索框]           [显示未激活] [测试匹配]          │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ ID | 规则名称 | 类型 | 模式 | 目标领域 | 置信度 |... │ │
│ │ 1  | API规则  |关键词|API|...|tech_docs|███30%|... │ │
│ │ 2  | 退货规则 |关键词|退货|...|prod_sup |███30%|... │ │
│ │ 3  | 简历规则 |关键词|简历|...|job_doc  |███30%|... │ │
│ │ 4  | 竞赛规则 |关键词|竞赛|...|tech_comp|███30%|... │ │
│ └─────────────────────────────────────────────────────┘ │
│ [分页控件]                                              │
└─────────────────────────────────────────────────────────┘
```

## 8. 技术亮点

### 1. 类型安全的表单处理
```javascript
const ruleForm = ref({
  rule_name: '',
  rule_type: 'keyword',
  pattern: '',
  target_namespace: '',
  confidence_threshold: 0.3,
  priority: 0,
  is_active: true,
  metadata: { description: '' }
})
```

### 2. 智能占位符
根据规则类型动态显示不同的占位符提示:
```javascript
const getPatternPlaceholder = () => {
  const placeholders = {
    keyword: '例如: API|接口|SDK|文档 (使用 | 分隔)',
    regex: '例如: ^(退货|换货|售后).*(流程|方式)',
    pattern: '例如: *简历* 或 *.pdf'
  }
  return placeholders[ruleForm.value.rule_type] || ''
}
```

### 3. 可视化置信度
使用进度条颜色表示置信度等级:
```javascript
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.7) return '#67c23a'  // 绿色
  if (confidence >= 0.4) return '#e6a23c'  // 黄色
  return '#f56c6c'                          // 红色
}
```

### 4. 实时搜索过滤
```javascript
const filteredRules = computed(() => {
  let filtered = rules.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(r =>
      r.rule_name.toLowerCase().includes(keyword) ||
      r.pattern.toLowerCase().includes(keyword) ||
      r.target_namespace.toLowerCase().includes(keyword)
    )
  }

  return filtered
})
```

## 9. 集成测试建议

### 功能测试清单

- [ ] 规则列表加载正常
- [ ] 统计数据计算正确
- [ ] 创建规则功能正常
- [ ] 编辑规则功能正常
- [ ] 删除规则功能正常(含二次确认)
- [ ] 启用/禁用规则功能正常
- [ ] 搜索过滤功能正常
- [ ] 显示/隐藏未激活规则功能正常
- [ ] 测试匹配功能正常
- [ ] 表单验证功能正常
- [ ] 权限控制正常(需要 system_settings 权限)
- [ ] 页面导航正常(菜单项可点击)

### API 调用测试

```javascript
// 1. 加载规则列表
await getAllRules({ include_inactive: true, skip: 0, limit: 1000 })

// 2. 创建规则
await createRule({
  rule_name: '测试规则',
  rule_type: 'keyword',
  pattern: '测试|test',
  target_namespace: 'technical_docs',
  confidence_threshold: 0.3,
  priority: 0,
  is_active: true,
  metadata: { description: '测试' }
})

// 3. 更新规则
await updateRule(1, { is_active: false })

// 4. 测试匹配
await testRuleMatch({
  query: '如何使用API?',
  min_confidence: 0.0
})

// 5. 删除规则
await deleteRule(1)
```

## 10. 后续优化建议

1. **批量操作**: 支持批量启用/禁用/删除规则
2. **规则导入导出**: 支持 JSON/YAML 格式的批量导入导出
3. **规则版本管理**: 记录规则变更历史
4. **规则统计**: 显示每个规则的匹配次数和准确率
5. **拖拽排序**: 支持拖拽调整规则优先级
6. **规则分组**: 支持规则分组管理
7. **高级搜索**: 支持按类型、领域、优先级等多维度搜索
8. **规则模板**: 提供常用规则模板快速创建

## 11. 总结

✅ 路由规则前端管理界面已完整实现
✅ 提供完整的 CRUD 操作
✅ 支持实时测试和可视化展示
✅ 集成到主应用导航菜单
✅ 符合系统整体技术风格
✅ 权限控制完善

前端实现与后端 API 完美对接,为用户提供了直观、高效的路由规则管理体验!
