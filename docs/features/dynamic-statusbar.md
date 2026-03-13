# 动态状态栏实现说明

## 📊 功能概述

本实现为 RAG 系统的前端状态栏添加了动态监控功能，实时显示：
- **API 状态**：正常/延迟/异常
- **响应时间**：毫秒级精确显示
- **系统运行时间**：动态更新的运行时长

## 🛠 技术实现

### 1. 前端实现

#### 创建 `useSystemStatus.js` Composable
**路径**：`/frontend/src/composables/useSystemStatus.js`

**主要功能**：
- 每 30 秒自动检查 API 健康状态
- 实时计算平均响应时间
- 动态更新系统运行时间
- 状态历史记录（最近 10 次）

**API 状态判断规则**：
- ✅ **正常**：响应时间 < 1000ms
- ⚠️ **延迟**：响应时间 1000-5000ms
- ❌ **异常**：响应时间 > 5000ms 或请求失败

#### 修改 `TechLayout.vue`
**路径**：`/frontend/src/layouts/TechLayout.vue`

**主要修改**：
- 导入并使用 `useSystemStatus` composable
- 绑定动态状态数据到模板
- 使用响应式类名切换状态样式

### 2. 后端实现

#### 健康检查接口
**路径**：`/backend/app/main.py:98-101`

```python
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

**功能**：
- 简单快速的状态检查
- 返回系统健康状态
- 提供时间戳信息

## 📝 使用方式

### 在组件中使用

```vue
<script setup>
import { useSystemStatus } from '@/composables/useSystemStatus'

const {
  statusText,        // 状态文本
  statusClass,       // 状态样式类
  statusDotClass,    // 状态点样式类
  responseTime,      // 响应时间（毫秒）
  formattedUptime    // 格式化运行时间
} = useSystemStatus()
</script>

<template>
  <div class="status-item">
    <span class="status-dot" :class="statusDotClass">●</span>
    <span class="status-text" :class="statusClass">{{ statusText }}</span>
  </div>
</template>
```

## 🎨 样式设计

### 状态颜色
- 🟢 **正常**：绿色 (`text-green-400`, `bg-green-500`)
- 🟡 **延迟**：黄色 (`text-yellow-400`, `bg-yellow-500`)
- 🔴 **异常**：红色 (`text-red-400`, `bg-red-500`)
- ⚪ **检测中**：灰色 (`text-gray-400`, `bg-gray-500`)

### 响应时间显示
- 格式：`⏱ 响应时间: XXXms`
- 更新频率：每 30 秒（随健康检查更新）
- 显示最近 5 次检查的平均值

### 运行时间显示
- 格式：
  - `< 1分钟`：XX秒
  - `< 1小时`：XX分XX秒
  - `< 1天`：XX小时XX分XX秒
  - `≥ 1天`：XX天XX小时XX分XX秒
- 更新频率：每秒

## ⚙️ 配置选项

### 可调整参数（在 `useSystemStatus.js` 中）

```javascript
// 检查间隔（毫秒）
statusCheckInterval = setInterval(checkApiStatus, 30000)  // 30秒

// 响应时间阈值（毫秒）
if (currentResponseTime > 5000) {
  updateApiStatus('error', '超时')
} else if (currentResponseTime > 1000) {
  updateApiStatus('warning', '延迟')
}

// 历史记录数量
if (apiStatusHistory.value.length > 10) {
  apiStatusHistory.value = apiStatusHistory.value.slice(0, 10)
}

// 健康检查超时时间（毫秒）
const response = await api.get('/health', {
  timeout: 5000
})
```

## 🔄 数据流

```
定时器 (30秒)
    ↓
调用 /health 接口
    ↓
记录响应时间
    ↓
判断状态等级
    ↓
更新状态历史
    ↓
触发响应式更新
    ↓
UI 自动刷新显示
```

## 🚀 启动流程

1. 应用启动时记录开始时间到 localStorage
2. 初始化时立即执行一次健康检查
3. 启动定时器：
   - 每 30 秒检查 API 状态
   - 每秒更新运行时间
4. 组件卸载时清理定时器

## 📦 依赖项

- **Vue 3** - Composition API
- **Axios** - HTTP 请求
- **Element Plus** - UI 组件（如需要）

## 🎯 扩展建议

### 1. 添加更多监控指标
```javascript
// 可添加的指标
- 内存使用率
- CPU 使用率
- 活跃用户数
- 数据库连接数
- 错误率统计
```

### 2. 添加告警功能
```javascript
// 状态异常时自动告警
if (status === 'error' && !alertSent) {
  ElMessage.error('API 异常，请检查系统状态')
  alertSent = true
}
```

### 3. 添加历史数据图表
- 响应时间趋势图
- 状态变化时间线
- 可用性统计报表

### 4. 添加手动刷新
```javascript
const manualRefresh = () => {
  checkApiStatus()
}
```

## 🔍 调试

### 查看状态历史
打开浏览器控制台，运行：
```javascript
// 查看最近 10 次状态记录
console.log(apiStatusHistory.value)
```

### 查看当前状态
```javascript
// 打印当前状态
console.log({
  status: statusText.value,
  responseTime: responseTime.value,
  uptime: formattedUptime.value
})
```

## ✅ 测试

### 功能测试
1. 启动前端和后端服务
2. 打开浏览器开发者工具
3. 查看状态栏是否显示动态数据
4. 观察状态变化是否符合预期

### 性能测试
- 检查定时器是否正确清理
- 验证内存泄漏情况
- 测试网络异常时的处理

## 📚 参考资料

- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Axios Interceptors](https://axios-http.com/docs/interceptors)
- [JavaScript Date & Time](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date)
