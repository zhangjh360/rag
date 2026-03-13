<template>
  <div class="active-sessions">
    <div v-if="sessions.length === 0" class="empty-state">
      <el-icon class="empty-icon"><ChatDotRound /></el-icon>
      <p>暂无对话</p>
    </div>

    <div v-else class="session-list">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        @click="handleSessionClick(session)"
      >
        <div class="session-icon-wrapper">
          <el-icon class="session-icon"><ChatDotRound /></el-icon>
          <span class="message-count">{{ session.message_count }}</span>
        </div>

        <div class="session-info">
          <div class="session-title">{{ session.title }}</div>
          <div class="session-preview" v-if="session.last_message">
            {{ session.last_message }}
          </div>
          <div class="session-meta">
            <span class="session-time">{{ session.relative_time }}</span>
          </div>
        </div>

        <el-icon class="arrow-icon"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound, ArrowRight } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => []
  }
})

const router = useRouter()

/**
 * 处理会话点击
 */
const handleSessionClick = (session) => {
  router.push(`/chat?session=${session.session_id}`)
}
</script>

<style lang="scss" scoped>
.active-sessions {
  min-height: 200px;

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: var(--tech-text-muted);

    .empty-icon {
      font-size: 48px;
      margin-bottom: 12px;
      opacity: 0.3;
    }

    p {
      font-size: 14px;
      margin: 0;
    }
  }

  .session-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .session-item {
    display: flex;
    align-items: flex-start;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--tech-glass-border);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(168, 85, 247, 0.05);
      border-color: var(--tech-border-hover);
      transform: translateX(4px);

      .arrow-icon {
        opacity: 1;
        transform: translateX(4px);
      }
    }

    .session-icon-wrapper {
      position: relative;
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: rgba(168, 85, 247, 0.1);
      margin-right: 12px;

      .session-icon {
        font-size: 20px;
        color: var(--tech-neon-purple);
      }

      .message-count {
        position: absolute;
        top: -4px;
        right: -4px;
        min-width: 18px;
        height: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 4px;
        background: linear-gradient(135deg, #8b5cf6, #a78bfa);
        border-radius: 9px;
        font-size: 10px;
        font-weight: 600;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
      }
    }

    .session-info {
      flex: 1;
      min-width: 0;

      .session-title {
        color: var(--tech-text-primary);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .session-preview {
        color: var(--tech-text-secondary);
        font-size: 12px;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.4;
      }

      .session-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 11px;
        color: var(--tech-text-muted);

        .session-time {
          display: flex;
          align-items: center;

          &::before {
            content: '🕐';
            margin-right: 4px;
          }
        }
      }
    }

    .arrow-icon {
      flex-shrink: 0;
      font-size: 16px;
      color: var(--tech-text-muted);
      opacity: 0;
      transition: all 0.3s ease;
      margin-top: 12px;
    }
  }
}
</style>
