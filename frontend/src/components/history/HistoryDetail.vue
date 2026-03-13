<template>
  <div class="history-detail">
    <!-- 头部概要 -->
    <div class="detail-header">
      <div class="header-icon">
        <el-icon :size="40">
          <ChatDotRound v-if="type === 'chat'" />
          <Search v-else />
        </el-icon>
      </div>
      <div class="header-info">
        <h2 class="detail-title">{{ item.query || item.title || '无标题' }}</h2>
        <div class="header-meta">
          <span class="meta-time">
            <el-icon><Clock /></el-icon>
            {{ formatFullTime(item.timestamp || item.created_at) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 状态标签 -->
    <div class="detail-tags">
      <el-tag v-if="item.use_rag !== undefined" :type="item.use_rag ? 'success' : 'info'" size="large" effect="dark">
        <el-icon><DataAnalysis /></el-icon>
        {{ item.use_rag ? 'RAG 增强' : '直接对话' }}
      </el-tag>
      <el-tag v-if="item.model" type="primary" size="large" effect="dark">
        <el-icon><Monitor /></el-icon>
        {{ item.model }}
      </el-tag>
      <el-tag v-if="item.stream !== undefined" type="warning" size="large" effect="dark">
        <el-icon><Connection /></el-icon>
        {{ item.stream ? '流式输出' : '标准输出' }}
      </el-tag>
    </div>

    <!-- 性能指标 -->
    <div class="metrics-section">
      <h3 class="section-title">
        <el-icon><TrendCharts /></el-icon>
        性能指标
      </h3>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon">
            <el-icon :size="24"><Coin /></el-icon>
          </div>
          <div class="metric-content">
            <span class="metric-label">Token 使用</span>
            <span class="metric-value">{{ item.tokens_used || 0 }}</span>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon">
            <el-icon :size="24"><Timer /></el-icon>
          </div>
          <div class="metric-content">
            <span class="metric-label">响应时间</span>
            <span class="metric-value">{{ formatDuration(item.response_time) }}</span>
          </div>
        </div>

        <div v-if="item.relevance_score" class="metric-card">
          <div class="metric-icon">
            <el-icon :size="24"><Aim /></el-icon>
          </div>
          <div class="metric-content">
            <span class="metric-label">相关性</span>
            <span class="metric-value">{{ (item.relevance_score * 100).toFixed(0) }}%</span>
          </div>
        </div>

        <div v-if="item.sources && item.sources.length > 0" class="metric-card">
          <div class="metric-icon">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="metric-content">
            <span class="metric-label">源文档</span>
            <span class="metric-value">{{ item.sources.length }} 个</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户查询 -->
    <div v-if="item.query" class="content-section">
      <h3 class="section-title">
        <el-icon><ChatLineSquare /></el-icon>
        用户查询
      </h3>
      <div class="content-box user-query">
        <p>{{ item.query || '无查询内容' }}</p>
      </div>
    </div>

    <!-- 完整对话历史 -->
    <div v-if="item.messages && item.messages.length > 0" class="content-section">
      <h3 class="section-title">
        <el-icon><ChatDotRound /></el-icon>
        完整对话 ({{ item.messages.length }} 条消息)
      </h3>
      <div class="conversation-timeline">
        <div
          v-for="(message, index) in item.messages"
          :key="message.id"
          :class="['message-item', `message-${message.role}`]"
        >
          <!-- 消息头部 -->
          <div class="message-header">
            <div class="message-avatar">
              <el-icon :size="20">
                <User v-if="message.role === 'user'" />
                <Avatar v-else />
              </el-icon>
            </div>
            <div class="message-meta">
              <span class="message-role">{{ message.role === 'user' ? '用户' : 'AI 助手' }}</span>
              <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
            </div>
            <el-tag v-if="index === 0" size="small" type="primary">首条</el-tag>
          </div>

          <!-- 图片（如果有）-->
          <div v-if="message.images && message.images.length > 0" class="message-images">
            <div v-for="img in message.images" :key="img.id" class="message-image">
              <el-image
                :src="img.url"
                :preview-src-list="[img.url]"
                fit="cover"
                class="image-preview"
              >
                <template #placeholder>
                  <div class="image-loading">加载中...</div>
                </template>
              </el-image>
              <span class="image-name">{{ img.original_name }}</span>
            </div>
          </div>

          <!-- 消息内容 -->
          <div class="message-content">
            <div v-if="message.role === 'user'" class="user-message-text">
              {{ message.content }}
            </div>
            <div v-else class="assistant-message-text" v-html="formatResponse(message.content)"></div>
          </div>

          <!-- 消息元数据 -->
          <div v-if="message.metadata && Object.keys(message.metadata).length > 0" class="message-metadata">
            <el-tag v-if="message.metadata.model" size="small" type="info">
              <el-icon><Monitor /></el-icon>
              {{ message.metadata.model }}
            </el-tag>
            <el-tag v-if="message.metadata.tokens_used" size="small" type="warning">
              <el-icon><Coin /></el-icon>
              {{ message.metadata.tokens_used }} tokens
            </el-tag>
            <el-tag v-if="message.metadata.response_time" size="small" type="success">
              <el-icon><Timer /></el-icon>
              {{ formatDuration(message.metadata.response_time) }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 响应（如果没有完整对话历史，则显示单独的响应）-->
    <div v-else-if="item.response" class="content-section">
      <h3 class="section-title">
        <el-icon><ChatLineRound /></el-icon>
        AI 响应
      </h3>
      <div class="content-box ai-response">
        <div v-html="formatResponse(item.response)"></div>
      </div>
    </div>

    <!-- 源文档 -->
    <div v-if="item.sources && item.sources.length > 0" class="content-section">
      <h3 class="section-title">
        <el-icon><FolderOpened /></el-icon>
        引用来源 ({{ item.sources.length }})
      </h3>
      <div class="sources-list">
        <div v-for="(source, index) in item.sources" :key="index" class="source-item">
          <div class="source-header">
            <span class="source-index">#{{ index + 1 }}</span>
            <span class="source-title">{{ source.title || '未命名文档' }}</span>
            <el-tag v-if="source.score" size="small" type="success">
              相关度: {{ (source.score * 100).toFixed(0) }}%
            </el-tag>
          </div>
          <div v-if="source.content" class="source-content">
            {{ truncateText(source.content, 200) }}
          </div>
          <div v-if="source.metadata" class="source-meta">
            <span v-if="source.metadata.page">页码: {{ source.metadata.page }}</span>
            <span v-if="source.metadata.chunk_id">片段: {{ source.metadata.chunk_id }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 检索参数 -->
    <div v-if="item.retrieval_params" class="content-section">
      <h3 class="section-title">
        <el-icon><Setting /></el-icon>
        检索配置
      </h3>
      <div class="params-grid">
        <div v-for="(value, key) in item.retrieval_params" :key="key" class="param-item">
          <span class="param-key">{{ formatParamKey(key) }}</span>
          <span class="param-value">{{ formatParamValue(value) }}</span>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="detail-footer">
      <el-button type="success" size="large" @click="$emit('reuse', item)">
        <el-icon><RefreshRight /></el-icon>
        复用此查询
      </el-button>
      <el-button type="danger" size="large" @click="$emit('delete', item)">
        <el-icon><Delete /></el-icon>
        删除记录
      </el-button>
    </div>
  </div>
</template>

<script setup>
import {
  ChatDotRound,
  Search,
  Clock,
  DataAnalysis,
  Monitor,
  Connection,
  TrendCharts,
  Coin,
  Timer,
  Aim,
  Document,
  ChatLineSquare,
  ChatLineRound,
  FolderOpened,
  Setting,
  RefreshRight,
  Delete,
  User,
  Avatar
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

defineEmits(['reuse', 'delete'])

const formatFullTime = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatMessageTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (ms) => {
  if (!ms) return '0ms'
  if (ms >= 1000) return (ms / 1000).toFixed(2) + 's'
  return Math.round(ms) + 'ms'
}

const formatResponse = (text) => {
  if (!text) return ''
  // 简单的 markdown 转换
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const formatParamKey = (key) => {
  const keyMap = {
    top_k: 'Top K',
    threshold: '相似度阈值',
    method: '检索方法',
    namespace: '命名空间',
    alpha: 'Alpha 参数'
  }
  return keyMap[key] || key
}

const formatParamValue = (value) => {
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return value.toString()
  return value || '-'
}
</script>

<style scoped>
.history-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

/* ===== 头部 ===== */
.detail-header {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(123, 104, 238, 0.08) 100%);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.header-icon {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(123, 104, 238, 0.15) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 16px;
  color: #00d4ff;
}

.header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #e8eaed;
  line-height: 1.4;
}

.header-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #9aa0a6;
}

/* ===== 标签 ===== */
.detail-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* ===== 分节标题 ===== */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 700;
  color: #00d4ff;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* ===== 性能指标 ===== */
.metrics-section {
  padding: 24px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(123, 104, 238, 0.08) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.metric-card:hover {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.12) 0%, rgba(123, 104, 238, 0.12) 100%);
  border-color: rgba(0, 212, 255, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 212, 255, 0.15);
}

.metric-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(123, 104, 238, 0.15) 100%);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 10px;
  color: #00d4ff;
}

.metric-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #9aa0a6;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #e8eaed;
}

/* ===== 对话时间轴 ===== */
.conversation-timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-radius: 12px;
  transition: all 0.2s ease;
  position: relative;
}

.message-user {
  background: linear-gradient(135deg, rgba(123, 104, 238, 0.08) 0%, rgba(123, 104, 238, 0.05) 100%);
  border: 1px solid rgba(123, 104, 238, 0.2);
  border-left: 4px solid #7b68ee;
}

.message-assistant {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-left: 4px solid #00d4ff;
}

.message-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-user .message-avatar {
  background: linear-gradient(135deg, #7b68ee 0%, #9370db 100%);
  color: white;
}

.message-assistant .message-avatar {
  background: linear-gradient(135deg, #00d4ff 0%, #00bfff 100%);
  color: white;
}

.message-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-role {
  font-size: 14px;
  font-weight: 700;
  color: #e8eaed;
}

.message-time {
  font-size: 12px;
  color: #9aa0a6;
}

.message-images {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding: 8px 0;
}

.message-image {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 200px;
}

.image-preview {
  width: 100%;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 212, 255, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.image-preview:hover {
  border-color: rgba(0, 212, 255, 0.5);
  transform: scale(1.02);
}

.image-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: rgba(0, 0, 0, 0.2);
  color: #9aa0a6;
  font-size: 13px;
}

.image-name {
  font-size: 12px;
  color: #9aa0a6;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-content {
  padding: 4px 0;
}

.user-message-text {
  font-size: 15px;
  line-height: 1.7;
  color: #e8eaed;
  font-weight: 500;
  white-space: pre-wrap;
  word-break: break-word;
}

.assistant-message-text {
  font-size: 15px;
  line-height: 1.8;
  color: #c5cad1;
  white-space: pre-wrap;
  word-break: break-word;
}

.assistant-message-text :deep(strong) {
  color: #e8eaed;
  font-weight: 600;
}

.assistant-message-text :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.message-metadata {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

/* ===== 内容区 ===== */
.content-section {
  padding: 24px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.content-box {
  padding: 18px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.8;
}

.user-query {
  background: rgba(123, 104, 238, 0.12);
  border-left: 4px solid #7b68ee;
  color: #e8eaed;
  font-weight: 500;
}

.user-query p {
  margin: 0;
  color: #e8eaed;
}

.ai-response {
  background: rgba(0, 212, 255, 0.08);
  border-left: 4px solid #00d4ff;
  color: #c5cad1;
}

.ai-response :deep(p) {
  margin: 0 0 12px 0;
  color: #c5cad1;
}

.ai-response :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-response :deep(strong) {
  color: #e8eaed;
  font-weight: 600;
}

.ai-response :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

/* ===== 源文档 ===== */
.sources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  padding: 18px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(123, 104, 238, 0.05) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.source-item:hover {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(123, 104, 238, 0.08) 100%);
  border-color: rgba(0, 212, 255, 0.4);
  transform: translateX(4px);
}

.source-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.source-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 100%);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.source-title {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #e8eaed;
  min-width: 150px;
}

.source-content {
  padding: 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: #c5cad1;
  margin-bottom: 10px;
}

.source-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #9aa0a6;
}

.source-meta span {
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 6px;
  border: 1px solid rgba(0, 212, 255, 0.15);
}

/* ===== 参数网格 ===== */
.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.05) 0%, rgba(123, 104, 238, 0.05) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.param-item:hover {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(123, 104, 238, 0.08) 100%);
  border-color: rgba(0, 212, 255, 0.3);
}

.param-key {
  font-size: 13px;
  font-weight: 500;
  color: #9aa0a6;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.param-value {
  font-size: 15px;
  font-weight: 700;
  color: #00d4ff;
}

/* ===== 底部操作 ===== */
.detail-footer {
  display: flex;
  gap: 12px;
  padding: 24px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.detail-footer .el-button {
  flex: 1;
  font-weight: 600;
  font-size: 15px;
  padding: 14px 24px;
  height: auto;
}
</style>
