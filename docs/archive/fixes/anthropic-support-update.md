# Anthropic 支持更新报告

## 更新概述

在 Settings.vue 中为 API 提供商选项添加了 Anthropic 兼容支持，并优化了自定义 API 地址的显示逻辑。

## 更改详情

### 1. API 提供商选项（已存在）

```vue
<el-select v-model="modelForm.provider" class="w-full">
  <el-option label="OpenAI" value="openai" />
  <el-option label="Anthropic" value="anthropic" />  <!-- ✓ 已存在 -->
  <el-option label="Azure" value="azure" />
  <el-option label="Custom" value="custom" />
</el-select>
```

### 2. 自定义 API 地址显示逻辑优化

**修改前**：
```vue
<el-form-item label="自定义API地址" v-if="modelForm.provider === 'custom'">
  <el-input v-model="modelForm.base_url" placeholder="https://api.example.com/v1" />
</el-form-item>
```

**修改后**：
```vue
<el-form-item label="自定义API地址" v-if="showCustomBaseUrl">
  <el-input v-model="modelForm.base_url" :placeholder="getBaseUrlPlaceholder()" />
  <div class="base-url-hint">
    <el-text size="small" type="info">
      {{ getBaseUrlHint() }}
    </el-text>
  </div>
</el-form-item>
```

### 3. 新增辅助方法

#### `getBaseUrlPlaceholder()` - 获取占位符
根据不同提供商返回合适的默认占位符：
- **Anthropic**: `https://api.anthropic.com/v1`
- **Azure**: `https://{resource-name}.openai.azure.com/`
- **Custom**: `https://api.example.com/v1`

#### `getBaseUrlHint()` - 获取提示信息
为每个提供商提供详细的使用说明：
- **Anthropic**: "默认使用官方API地址，如需使用兼容服务可自定义"
- **Azure**: "Azure OpenAI服务需要指定具体的资源端点"
- **Custom**: "请输入完整的API地址，包含版本路径，如：https://api.example.com/v1"

#### `showCustomBaseUrl` - 计算属性
控制是否显示自定义 API 地址输入框：
```javascript
const showCustomBaseUrl = computed(() => {
  return ['anthropic', 'azure', 'custom'].includes(modelForm.value.provider)
})
```

### 4. 样式优化

新增 `.base-url-hint` 样式类：
```scss
.base-url-hint {
  margin-top: 4px;
  padding-left: 0;
}

.base-url-hint .el-text {
  display: block;
  color: var(--tech-text-secondary);
  font-size: 12px;
  line-height: 1.4;
}
```

## 功能特性

### 支持的提供商

| 提供商 | 显示自定义 API 地址 | 占位符示例 | 提示信息 |
|--------|--------------------|------------|----------|
| OpenAI | ❌ | - | 使用默认地址 |
| **Anthropic** | ✅ | `https://api.anthropic.com/v1` | 支持自定义兼容服务 |
| Azure | ✅ | `https://{resource-name}.openai.azure.com/` | 需要指定资源端点 |
| Custom | ✅ | `https://api.example.com/v1` | 完全自定义 |

### 用户体验改进

1. **动态显示**
   - 根据选择的提供商动态显示/隐藏自定义 API 地址字段
   - 只在需要时显示该字段，减少界面噪音

2. **智能提示**
   - 每个提供商都有专门的占位符和提示信息
   - 帮助用户正确配置 API 地址

3. **视觉反馈**
   - 提示信息使用较小的字体和次要颜色
   - 不会干扰主要表单字段

4. **易于扩展**
   - 新的提供商可以轻松添加到支持列表
   - 只需在一个地方添加提供商名称

## 文件修改

**前端文件**：
- `/home/zhangjh/code/python/rag/frontend/src/views/Settings.vue`
  - 修改了自定义 API 地址的显示逻辑
  - 添加了三个新方法：`getBaseUrlPlaceholder()`, `getBaseUrlHint()`, `showCustomBaseUrl`
  - 添加了 `.base-url-hint` 样式

## 测试建议

1. **选择 Anthropic 提供商**
   - ✅ 应该显示自定义 API 地址输入框
   - ✅ 占位符应为：`https://api.anthropic.com/v1`
   - ✅ 提示信息应显示 Anthropic 相关说明

2. **选择 Azure 提供商**
   - ✅ 应该显示自定义 API 地址输入框
   - ✅ 占位符应为：`https://{resource-name}.openai.azure.com/`
   - ✅ 提示信息应显示 Azure 相关说明

3. **选择 Custom 提供商**
   - ✅ 应该显示自定义 API 地址输入框
   - ✅ 占位符应为：`https://api.example.com/v1`
   - ✅ 提示信息应显示自定义说明

4. **选择 OpenAI 提供商**
   - ❌ 不应显示自定义 API 地址输入框
   - ✅ 使用默认 API 地址

## 总结

✅ **已完成**：
- Anthropic 提供商选项已存在
- 自定义 API 地址支持 Anthropic、Azure、Custom 三个提供商
- 智能占位符和提示信息
- 优化的用户体验

**状态**：✅ 已完成并可以测试
