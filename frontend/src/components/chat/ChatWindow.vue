<template>
  <div class="chat-window" ref="scrollContainer">
    <div class="messages-container">
      <!-- 消息列表 -->
      <MessageBubble
        v-for="(message, index) in messages"
        :key="index"
        :message="message"
        :is-last="index === messages.length - 1"
        @regenerate="handleRegenerate"
      />

      <!-- 加载中状态 -->
      <div v-if="loading" class="flex justify-center py-4">
        <div class="loading-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="messages.length === 0 && !loading" class="empty-state">
        <div class="tech-card p-8 text-center">
          <el-icon class="text-6xl text-tech-neon-blue mb-4"><ChatDotRound /></el-icon>
          <h3 class="text-xl font-semibold text-tech-text-primary mb-2">开始新对话</h3>
          <p class="text-tech-text-secondary">输入您的问题，我将为您提供帮助</p>

          <!-- 快捷提示 -->
          <div class="mt-8 grid grid-cols-2 gap-4">
            <div
              v-for="prompt in quickPrompts"
              :key="prompt"
              @click="$emit('use-prompt', prompt)"
              class="quick-prompt"
            >
              <el-icon class="mr-2"><MagicStick /></el-icon>
              <span>{{ prompt }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { ChatDotRound, MagicStick } from '@element-plus/icons-vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['use-prompt', 'regenerate'])

const scrollContainer = ref(null)

const quickPrompts = [
  '帮我写一份项目计划',
  '解释一下这段代码',
  '优化这个算法',
  '生成测试用例'
]

// 滚动到底部
const scrollToBottom = () => {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

// 监听消息变化自动滚动
watch(() => props.messages, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })

// 处理重新生成
const handleRegenerate = (message) => {
  emit('regenerate', message)
}

// 暴露方法给父组件
defineExpose({
  scrollToBottom
})
</script>

<style lang="scss" scoped>
.chat-window {
  height: 100%;
  overflow-y: auto;
  background: var(--tech-bg-primary);
  padding: 24px;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: var(--tech-bg-secondary);
  }

  &::-webkit-scrollbar-thumb {
    background: var(--tech-glass-border);
    border-radius: 4px;

    &:hover {
      background: var(--tech-border-hover);
    }
  }
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.tech-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.quick-prompt {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
  color: var(--tech-text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(0, 212, 255, 0.1);
    border-color: var(--tech-neon-blue);
    color: var(--tech-neon-blue);
    transform: translateY(-2px);
  }
}

// 加载动画
.loading-indicator {
  display: flex;
  gap: 4px;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--tech-neon-blue);
    animation: pulse 1.5s ease-in-out infinite;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes pulse {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}
</style>