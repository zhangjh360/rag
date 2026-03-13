<template>
  <div class="chat-sidebar-wrapper">
    <!-- 新建会话按钮 -->
    <div class="sidebar-header">
      <el-button
        @click="$emit('create')"
        type="primary"
        class="new-chat-btn"
      >
        <el-icon class="mr-2"><Plus /></el-icon>
        新建对话
      </el-button>
    </div>

    <!-- 会话列表 -->
    <div class="sessions-list">
      <div class="sessions-container">
        <div
          v-for="session in sessions"
          :key="session.session_id"
          class="session-item"
          :class="{ active: session.session_id === activeSessionId }"
          @click="$emit('select', session.session_id)"
        >
          <div class="session-content">
            <div class="session-info">
              <h4 class="session-title">
                {{ session.title }}
              </h4>
              <p class="session-message">
                {{ session.last_message || '暂无消息' }}
              </p>
              <div class="session-meta">
                <el-icon class="meta-icon"><Clock /></el-icon>
                <span>{{ formatTime(session.updated_at) }}</span>
                <span class="message-count">{{ session.message_count }} 条消息</span>
              </div>
            </div>
            <el-button
              @click.stop="handleDelete(session.session_id)"
              type="danger"
              size="small"
              text
              class="delete-btn"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="sessions.length === 0" class="empty-state">
          <el-icon class="empty-icon"><ChatDotRound /></el-icon>
          <p class="empty-text">暂无会话记录</p>
          <p class="empty-hint">点击上方按钮创建新对话</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Delete, Clock, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

defineProps({
  sessions: {
    type: Array,
    default: () => []
  },
  activeSessionId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select', 'create', 'delete'])

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `今天 ${hours}:${minutes}`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString()
  }
}

const handleDelete = async (sessionId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    emit('delete', sessionId)
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss" scoped>
.chat-sidebar-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--tech-glass-border);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-neon-blue) 50%,
      transparent
    );
    opacity: 0.3;
  }
}

.new-chat-btn {
  width: 100%;
  background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
  border: 1px solid var(--tech-neon-blue);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
    border-color: var(--tech-neon-purple);
  }

  &:active {
    transform: translateY(0);
  }
}

.sessions-list {
  flex: 1;
  max-height: calc(100vh - 64px - 80px); /* 减去顶部导航栏和侧边栏头部高度 */
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 212, 255, 0.2);
    border-radius: 3px;

    &:hover {
      background: rgba(0, 212, 255, 0.3);
    }
  }
}

.sessions-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  padding: 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--tech-neon-blue), var(--tech-neon-purple));
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }

  &:hover {
    background: rgba(0, 212, 255, 0.05);
    border-color: rgba(0, 212, 255, 0.2);
    transform: translateX(4px);

    .delete-btn {
      opacity: 1;
    }
  }

  &.active {
    background: rgba(0, 212, 255, 0.08);
    border-color: var(--tech-neon-blue);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);

    &::before {
      transform: translateX(0);
    }

    .session-title {
      color: var(--tech-neon-blue);
    }
  }
}

.session-content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--tech-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.session-message {
  font-size: 12px;
  color: var(--tech-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.session-meta {
  display: flex;
  align-items: center;
  font-size: 11px;
  color: var(--tech-text-muted);
  gap: 4px;

  .meta-icon {
    font-size: 12px;
  }

  .message-count {
    margin-left: 8px;
  }
}

.delete-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
  color: var(--tech-neon-pink);

  &:hover {
    color: #ff4757;
  }
}

.empty-state {
  text-align: center;
  padding: 48px 20px;

  .empty-icon {
    font-size: 48px;
    color: var(--tech-text-muted);
    margin-bottom: 12px;
    opacity: 0.5;
  }

  .empty-text {
    font-size: 14px;
    color: var(--tech-text-secondary);
    margin-bottom: 4px;
  }

  .empty-hint {
    font-size: 12px;
    color: var(--tech-text-muted);
  }
}
</style>