<template>
  <div class="task-monitor">
    <!-- 任务卡片 -->
    <div class="task-card" :class="taskStatusClass">
      <div class="task-header">
        <div class="task-info">
          <h4 class="task-title">
            <el-icon class="task-icon">
              <component :is="taskIconComponent" />
            </el-icon>
            {{ taskTitle }}
          </h4>
          <p class="task-id">任务ID: {{ taskId }}</p>
        </div>
        <div class="task-status">
          <el-tag :type="statusTagType" size="large">
            {{ statusText }}
          </el-tag>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="task-progress" v-if="showProgress">
        <el-progress
          :percentage="progress"
          :status="progressStatus"
          :stroke-width="12"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}%</span>
          </template>
        </el-progress>
        <p class="progress-message" v-if="message">{{ message }}</p>
        <p class="progress-details" v-if="current && total">
          处理进度: {{ current }} / {{ total }}
        </p>
      </div>

      <!-- 任务结果 -->
      <div class="task-result" v-if="result && status === 'completed'">
        <h5>执行结果</h5>
        <div class="result-stats">
          <div class="stat-item" v-if="result.indexed_count !== undefined">
            <span class="stat-label">已索引:</span>
            <span class="stat-value success">{{ result.indexed_count }}</span>
          </div>
          <div class="stat-item" v-if="result.skipped_count !== undefined">
            <span class="stat-label">已跳过:</span>
            <span class="stat-value info">{{ result.skipped_count }}</span>
          </div>
          <div class="stat-item" v-if="result.failed_count !== undefined">
            <span class="stat-label">失败:</span>
            <span class="stat-value danger">{{ result.failed_count }}</span>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div class="task-error" v-if="error && status === 'failed'">
        <h5>错误信息</h5>
        <el-alert
          :title="error"
          type="error"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 任务时间信息 -->
      <div class="task-time" v-if="startTime || endTime">
        <div class="time-item" v-if="startTime">
          <el-icon><Clock /></el-icon>
          <span>开始: {{ formatTime(startTime) }}</span>
        </div>
        <div class="time-item" v-if="endTime">
          <el-icon><Check /></el-icon>
          <span>完成: {{ formatTime(endTime) }}</span>
        </div>
        <div class="time-item" v-if="duration">
          <el-icon><Timer /></el-icon>
          <span>耗时: {{ duration }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="task-actions" v-if="showActions">
        <el-button
          v-if="status === 'failed' && allowRetry"
          type="primary"
          size="small"
          @click="handleRetry"
        >
          <el-icon><RefreshRight /></el-icon>
          重试任务
        </el-button>
        <el-button
          v-if="status === 'processing' && allowCancel"
          type="danger"
          size="small"
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消任务
        </el-button>
        <el-button
          v-if="status === 'completed' || status === 'failed'"
          size="small"
          @click="handleClose"
        >
          关闭
        </el-button>
      </div>
    </div>

    <!-- 连接状态指示 -->
    <div class="connection-status" v-if="showConnectionStatus">
      <el-tag :type="wsConnected ? 'success' : 'info'" size="small" effect="plain">
        <el-icon><Connection /></el-icon>
        {{ wsConnected ? 'WebSocket已连接' : 'WebSocket未连接' }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import indexTaskService from '../../services/indexTaskService'
import {
  Loading, SuccessFilled, CircleClose, Clock, Check, Timer,
  RefreshRight, Close, Connection, Document
} from '@element-plus/icons-vue'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  taskTitle: {
    type: String,
    default: '文档索引任务'
  },
  autoConnect: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  allowRetry: {
    type: Boolean,
    default: true
  },
  allowCancel: {
    type: Boolean,
    default: false
  },
  showConnectionStatus: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['completed', 'failed', 'retry', 'cancel', 'close'])

// 任务状态
const status = ref('pending') // pending, processing, completed, failed
const progress = ref(0)
const message = ref('')
const current = ref(null)
const total = ref(null)
const result = ref(null)
const error = ref('')
const startTime = ref(null)
const endTime = ref(null)
const wsConnected = ref(false)

// WebSocket连接
let ws = null

// 计算属性
const taskStatusClass = computed(() => {
  return `status-${status.value}`
})

const statusTagType = computed(() => {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status.value] || 'info'
})

const statusText = computed(() => {
  const texts = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status.value] || '未知'
})

const taskIconComponent = computed(() => {
  const icons = {
    pending: Clock,
    processing: Loading,
    completed: SuccessFilled,
    failed: CircleClose
  }
  return icons[status.value] || Document
})

const progressStatus = computed(() => {
  if (status.value === 'completed') return 'success'
  if (status.value === 'failed') return 'exception'
  return undefined
})

const showProgress = computed(() => {
  return status.value === 'processing' || status.value === 'completed'
})

const duration = computed(() => {
  if (!startTime.value) return null
  const end = endTime.value || new Date()
  const start = new Date(startTime.value)
  const diff = Math.floor((end - start) / 1000) // 秒

  if (diff < 60) return `${diff}秒`
  if (diff < 3600) return `${Math.floor(diff / 60)}分${diff % 60}秒`
  return `${Math.floor(diff / 3600)}小时${Math.floor((diff % 3600) / 60)}分`
})

// 方法
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const connectWebSocket = () => {
  if (ws) {
    indexTaskService.disconnectTaskProgress(props.taskId)
  }

  ws = indexTaskService.connectTaskProgress(props.taskId, {
    onConnected: (msg) => {
      console.log('WebSocket连接成功:', msg)
      wsConnected.value = true

      // 更新初始状态
      if (msg.current_status) {
        status.value = msg.current_status
      }
      if (msg.current_progress !== undefined) {
        progress.value = msg.current_progress
      }
    },

    onProgress: (msg) => {
      console.log('收到进度更新:', msg)
      status.value = msg.status || 'processing'
      progress.value = msg.progress || 0
      message.value = msg.message || ''

      if (msg.current !== undefined) current.value = msg.current
      if (msg.total !== undefined) total.value = msg.total

      if (!startTime.value && status.value === 'processing') {
        startTime.value = new Date()
      }
    },

    onComplete: (msg) => {
      console.log('任务完成:', msg)
      status.value = 'completed'
      progress.value = 100
      message.value = msg.message || '任务完成'
      result.value = msg.result || {}
      endTime.value = new Date()

      ElMessage.success(message.value)
      emit('completed', result.value)
    },

    onError: (msg) => {
      console.error('任务错误:', msg)
      status.value = 'failed'
      error.value = msg.error || '任务执行失败'
      endTime.value = new Date()

      ElMessage.error(error.value)
      emit('failed', error.value)
    },

    onDisconnected: (event) => {
      console.log('WebSocket断开:', event)
      wsConnected.value = false
    }
  })
}

const handleRetry = async () => {
  try {
    await indexTaskService.retryTask(props.taskId)
    ElMessage.success('已提交重试请求')
    emit('retry')

    // 重置状态
    status.value = 'pending'
    progress.value = 0
    error.value = ''
    result.value = null
    startTime.value = null
    endTime.value = null

    // 重新连接WebSocket
    if (props.autoConnect) {
      connectWebSocket()
    }
  } catch (error) {
    console.error('重试失败:', error)
  }
}

const handleCancel = async () => {
  try {
    await indexTaskService.cancelTask(props.taskId)
    ElMessage.info('已取消任务')
    emit('cancel')

    status.value = 'failed'
    error.value = '任务已被用户取消'
    endTime.value = new Date()
  } catch (error) {
    console.error('取消失败:', error)
  }
}

const handleClose = () => {
  emit('close')
}

// 生命周期
onMounted(() => {
  if (props.autoConnect) {
    connectWebSocket()
  }
})

onBeforeUnmount(() => {
  if (ws) {
    indexTaskService.disconnectTaskProgress(props.taskId)
  }
})

// 暴露方法给父组件
defineExpose({
  connectWebSocket,
  status,
  progress
})
</script>

<style lang="scss" scoped>
.task-monitor {
  width: 100%;
}

.task-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &.status-pending {
    border-left: 4px solid #909399;
  }

  &.status-processing {
    border-left: 4px solid #e6a23c;
    animation: pulse 2s infinite;
  }

  &.status-completed {
    border-left: 4px solid #67c23a;
  }

  &.status-failed {
    border-left: 4px solid #f56c6c;
  }
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.4);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(230, 162, 60, 0);
  }
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.task-info {
  flex: 1;

  .task-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: var(--tech-text-primary);
    margin: 0 0 8px 0;

    .task-icon {
      font-size: 20px;
    }
  }

  .task-id {
    font-size: 12px;
    color: var(--tech-text-secondary);
    margin: 0;
  }
}

.task-status {
  flex-shrink: 0;
}

.task-progress {
  margin-bottom: 16px;

  .progress-text {
    font-size: 12px;
    font-weight: 600;
    color: var(--tech-text-primary);
  }

  .progress-message {
    margin: 8px 0 0 0;
    font-size: 14px;
    color: var(--tech-text-primary);
  }

  .progress-details {
    margin: 4px 0 0 0;
    font-size: 12px;
    color: var(--tech-text-secondary);
  }
}

.task-result {
  margin-bottom: 16px;

  h5 {
    font-size: 14px;
    color: var(--tech-text-primary);
    margin: 0 0 12px 0;
  }

  .result-stats {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;

    .stat-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(17, 24, 39, 0.6);
      border-radius: 8px;

      .stat-label {
        font-size: 12px;
        color: var(--tech-text-secondary);
      }

      .stat-value {
        font-size: 16px;
        font-weight: 600;

        &.success {
          color: #67c23a;
        }

        &.info {
          color: #909399;
        }

        &.danger {
          color: #f56c6c;
        }
      }
    }
  }
}

.task-error {
  margin-bottom: 16px;

  h5 {
    font-size: 14px;
    color: var(--tech-text-primary);
    margin: 0 0 12px 0;
  }
}

.task-time {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--tech-glass-border);

  .time-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--tech-text-secondary);

    .el-icon {
      font-size: 14px;
    }
  }
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.connection-status {
  margin-top: 12px;
  text-align: right;
}
</style>
