<template>
  <div class="history-card" @click="$emit('view-detail', item)">
    <!-- 卡片头部 - 时间和状态 -->
    <div class="card-header">
      <div class="time-badge">
        <el-icon class="time-icon"><Clock /></el-icon>
        <span>{{ formatTime(item.timestamp || item.created_at) }}</span>
      </div>
      <div class="status-badges">
        <el-tag v-if="item.use_rag !== undefined" :type="item.use_rag ? 'success' : 'info'" size="small" effect="dark">
          <el-icon><DataAnalysis /></el-icon>
          {{ item.use_rag ? 'RAG' : '直接' }}
        </el-tag>
        <el-tag v-if="item.model" type="primary" size="small" effect="dark">
          {{ modelShortName(item.model) }}
        </el-tag>
      </div>
    </div>

    <!-- 主标题 - 查询内容 -->
    <div class="card-title">
      <el-icon class="title-icon">
        <ChatDotRound v-if="type === 'chat'" />
        <Search v-else />
      </el-icon>
      <h3 class="query-text">{{ item.query || item.title || '无标题' }}</h3>
    </div>

    <!-- 会话标题/摘要 -->
    <div v-if="item.title && item.query !== item.title" class="card-subtitle">
      <el-icon><Memo /></el-icon>
      <span>{{ item.title }}</span>
    </div>

    <!-- 响应预览 -->
    <div v-if="item.response && item.response.trim()" class="response-preview">
      <div class="preview-label">
        <el-icon><ChatLineRound /></el-icon>
        <span>AI 回复</span>
      </div>
      <p class="preview-text">
        {{ truncateText(item.response, 150) }}
      </p>
    </div>

    <!-- 元数据网格 -->
    <div class="metadata-grid">
      <!-- Token 使用 -->
      <div v-if="item.tokens_used" class="meta-item">
        <el-icon class="meta-icon"><Coin /></el-icon>
        <div class="meta-content">
          <span class="meta-label">Tokens</span>
          <span class="meta-value">{{ formatNumber(item.tokens_used) }}</span>
        </div>
      </div>

      <!-- 响应时间 -->
      <div v-if="item.response_time" class="meta-item">
        <el-icon class="meta-icon"><Timer /></el-icon>
        <div class="meta-content">
          <span class="meta-label">耗时</span>
          <span class="meta-value">{{ formatDuration(item.response_time) }}</span>
        </div>
      </div>

      <!-- 源文档数量 -->
      <div v-if="item.sources && item.sources.length > 0" class="meta-item">
        <el-icon class="meta-icon"><Document /></el-icon>
        <div class="meta-content">
          <span class="meta-label">源文档</span>
          <span class="meta-value">{{ item.sources.length }} 个</span>
        </div>
      </div>

      <!-- 相关性分数 -->
      <div v-if="item.relevance_score" class="meta-item">
        <el-icon class="meta-icon"><TrendCharts /></el-icon>
        <div class="meta-content">
          <span class="meta-label">相关性</span>
          <span class="meta-value">{{ (item.relevance_score * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <!-- 快速操作栏 -->
    <div class="card-actions" @click.stop>
      <el-button
        type="primary"
        size="small"
        text
        @click="$emit('view-detail', item)"
        class="action-btn"
      >
        <el-icon><View /></el-icon>
        详情
      </el-button>
      <el-button
        type="success"
        size="small"
        text
        @click="$emit('reuse', item)"
        class="action-btn"
      >
        <el-icon><RefreshRight /></el-icon>
        复用
      </el-button>
      <el-button
        type="danger"
        size="small"
        text
        @click="$emit('delete', item)"
        class="action-btn"
      >
        <el-icon><Delete /></el-icon>
        删除
      </el-button>
    </div>

    <!-- 悬停高亮边框 -->
    <div class="card-glow"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Clock,
  ChatDotRound,
  Search,
  ChatLineRound,
  Memo,
  DataAnalysis,
  Document,
  Coin,
  Timer,
  TrendCharts,
  View,
  RefreshRight,
  Delete
} from '@element-plus/icons-vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  type: {
    type: String,
    default: 'chat'
  }
})

defineEmits(['view-detail', 'reuse', 'delete'])

// 格式化时间
const formatTime = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date

  // 少于1分钟
  if (diff < 60000) return '刚刚'
  // 少于1小时
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  // 少于24小时
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  // 少于7天
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 模型名称缩写
const modelShortName = (model) => {
  if (!model) return '未知'
  const shortNames = {
    'gpt-4': 'GPT-4',
    'gpt-3.5-turbo': 'GPT-3.5',
    'GLM-4-Flash': 'GLM-4',
    'GLM-4V-Flash': 'GLM-4V'
  }
  return shortNames[model] || model.split('-')[0].toUpperCase()
}

// 截断文本
const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 格式化数字
const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 格式化时长
const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms >= 1000) return (ms / 1000).toFixed(2) + 's'
  return Math.round(ms) + 'ms'
}
</script>

<style scoped>
.history-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(123, 104, 238, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.history-card:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2);
}

.history-card:hover .card-glow {
  opacity: 1;
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

/* ===== 卡片头部 ===== */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 13px;
  color: var(--tech-text-secondary);
  font-weight: 500;
}

.time-icon {
  color: #00d4ff;
  font-size: 14px;
}

.status-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* ===== 主标题 ===== */
.card-title {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.title-icon {
  flex-shrink: 0;
  margin-top: 4px;
  font-size: 24px;
  color: #00d4ff;
}

.query-text {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--tech-text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== 子标题 ===== */
.card-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(123, 104, 238, 0.1);
  border-left: 3px solid #7b68ee;
  border-radius: 6px;
  font-size: 14px;
  color: var(--tech-text-secondary);
  font-weight: 500;
}

/* ===== 响应预览 ===== */
.response-preview {
  padding: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.preview-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #00d4ff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--tech-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== 元数据网格 ===== */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.meta-item:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
}

.meta-icon {
  flex-shrink: 0;
  font-size: 18px;
  color: #00d4ff;
}

.meta-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 11px;
  color: var(--tech-text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.meta-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--tech-text-primary);
}

/* ===== 操作栏 ===== */
.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.action-btn {
  flex: 1;
  font-weight: 600;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.05);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .card-title {
    gap: 8px;
  }

  .query-text {
    font-size: 16px;
  }

  .metadata-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
