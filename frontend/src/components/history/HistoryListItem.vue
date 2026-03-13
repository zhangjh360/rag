<template>
  <div class="history-list-item" @click="$emit('view-detail', item)">
    <!-- 左侧：图标和主要信息 -->
    <div class="item-left">
      <div class="icon-wrapper">
        <el-icon class="item-icon">
          <ChatDotRound v-if="type === 'chat'" />
          <Search v-else />
        </el-icon>
      </div>

      <div class="item-main">
        <!-- 标题行 -->
        <div class="title-row">
          <h4 class="item-title">{{ item.query || item.title || '无标题' }}</h4>
          <div class="badges">
            <el-tag v-if="item.use_rag !== undefined" :type="item.use_rag ? 'success' : 'info'" size="small">
              {{ item.use_rag ? 'RAG' : '直接' }}
            </el-tag>
            <el-tag v-if="item.model" type="primary" size="small">
              {{ modelShortName(item.model) }}
            </el-tag>
          </div>
        </div>

        <!-- 副标题/预览 -->
        <div v-if="item.response" class="item-preview">
          {{ truncateText(item.response, 200) }}
        </div>
      </div>
    </div>

    <!-- 右侧：元数据和操作 -->
    <div class="item-right">
      <!-- 元数据指标 -->
      <div class="meta-indicators">
        <div v-if="item.tokens_used" class="indicator" title="Token 使用量">
          <el-icon><Coin /></el-icon>
          <span>{{ formatNumber(item.tokens_used) }}</span>
        </div>
        <div v-if="item.response_time" class="indicator" title="响应时间">
          <el-icon><Timer /></el-icon>
          <span>{{ formatDuration(item.response_time) }}</span>
        </div>
        <div v-if="item.sources && item.sources.length > 0" class="indicator" title="源文档数量">
          <el-icon><Document /></el-icon>
          <span>{{ item.sources.length }}</span>
        </div>
      </div>

      <!-- 时间 -->
      <div class="item-time">
        {{ formatTime(item.timestamp || item.created_at) }}
      </div>

      <!-- 快速操作 -->
      <div class="item-actions" @click.stop>
        <el-button type="primary" size="small" circle @click="$emit('view-detail', item)" title="查看详情">
          <el-icon><View /></el-icon>
        </el-button>
        <el-button type="success" size="small" circle @click="$emit('reuse', item)" title="复用查询">
          <el-icon><RefreshRight /></el-icon>
        </el-button>
        <el-button type="danger" size="small" circle @click="$emit('delete', item)" title="删除">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ChatDotRound,
  Search,
  Coin,
  Timer,
  Document,
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

const formatTime = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

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

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms >= 1000) return (ms / 1000).toFixed(2) + 's'
  return Math.round(ms) + 'ms'
}
</script>

<style scoped>
.history-list-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-list-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
  transform: translateX(4px);
}

/* ===== 左侧 ===== */
.item-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.icon-wrapper {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(123, 104, 238, 0.2) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 12px;
}

.item-icon {
  font-size: 24px;
  color: #00d4ff;
}

.item-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.item-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--tech-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.badges {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.item-preview {
  font-size: 14px;
  line-height: 1.5;
  color: var(--tech-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ===== 右侧 ===== */
.item-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.meta-indicators {
  display: flex;
  gap: 16px;
}

.indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #00d4ff;
  white-space: nowrap;
}

.item-time {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--tech-text-secondary);
  white-space: nowrap;
}

.item-actions {
  display: flex;
  gap: 8px;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .meta-indicators {
    flex-direction: column;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .history-list-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .item-left {
    width: 100%;
  }

  .item-right {
    width: 100%;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .meta-indicators {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
