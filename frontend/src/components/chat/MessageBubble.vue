<template>
  <div class="message-bubble" :class="messageClass">
    <div class="message-content">
      <!-- 头像 -->
      <div class="avatar">
        <el-icon v-if="message.role === 'user'" class="text-xl"><User /></el-icon>
        <el-icon v-else class="text-xl"><Monitor /></el-icon>
      </div>

      <!-- 消息内容 -->
      <div class="content">
        <!-- 多模态消息（包含图片） -->
        <div v-if="isMultimodalMessage" class="multimodal-content">
          <!-- 图片区域 -->
          <div v-if="message.content.images && message.content.images.length > 0" class="message-images">
            <ChatImage
              v-for="img in message.content.images"
              :key="img.url"
              :src="img.url"
              :thumbnail="img.thumbnail_url"
              :original-name="img.original_name"
              :width="img.width"
              :height="img.height"
              :file-size="img.file_size"
              :max-width="200"
              :inline="false"
              class="message-image-item"
            />
          </div>
          <!-- 文本内容 -->
          <div class="text" v-if="message.content.text" v-html="renderedMultimodalContent"></div>
        </div>
        <!-- 来自后端的带图片消息 -->
        <div v-else-if="message.images && message.images.length > 0" class="multimodal-content">
          <!-- 图片区域 -->
          <div class="message-images">
            <ChatImage
              v-for="img in message.images"
              :key="img.id"
              :src="img.url"
              :thumbnail="img.thumbnail_url"
              :original-name="img.original_name"
              :width="img.width"
              :height="img.height"
              :file-size="img.file_size"
              :max-width="200"
              :inline="false"
              class="message-image-item"
            />
          </div>
          <!-- 文本内容 -->
          <div class="text" v-if="message.content" v-html="renderedContent"></div>
        </div>
        <!-- 普通文本消息 -->
        <div v-else-if="message.content" class="text" v-html="renderedContent"></div>
        <!-- 加载动画 - 当消息为空且是助手消息时显示 -->
        <div v-else-if="message.role === 'assistant' && !message.content" class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div class="meta">
          <span class="time">{{ formatTime(message.timestamp) }}</span>
          <div class="action-buttons">
            <!-- 重新生成按钮 - 仅对助手消息显示 -->
            <el-tooltip v-if="message.role === 'assistant'" content="重新生成" placement="top">
              <el-button
                class="action-btn regenerate-btn"
                :icon="Refresh"
                size="small"
                text
                @click="regenerateMessage"
              />
            </el-tooltip>
            <!-- 复制按钮 -->
            <el-tooltip :content="copied ? '已复制!' : '复制内容'" placement="top">
              <el-button
                class="action-btn copy-btn"
                :icon="copied ? SuccessFilled : DocumentCopy"
                size="small"
                text
                @click="copyContent"
              />
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { User, Monitor, DocumentCopy, SuccessFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import ChatImage from './ChatImage.vue'

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (e) {
        console.error('Highlight error:', e)
      }
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,  // 支持 GitHub 风格的换行
  gfm: true,     // 启用 GitHub Flavored Markdown
  tables: true,  // 支持表格
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: true
})

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isLast: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['regenerate'])

const messageClass = computed(() => ({
  'user-message': props.message.role === 'user',
  'assistant-message': props.message.role === 'assistant',
  'is-last': props.isLast
}))

// 判断是否为多模态消息
const isMultimodalMessage = computed(() => {
  return props.message.content && typeof props.message.content === 'object' && props.message.content.type === 'multimodal'
})

// 渲染多模态消息的文本内容
const renderedMultimodalContent = computed(() => {
  const text = props.message.content.text || ''
  if (props.message.role === 'assistant') {
    return marked.parse(text)
  }
  return text.replace(/\n/g, '<br>')
})

// 渲染普通文本消息
const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return marked.parse(props.message.content || '')
  }
  return (props.message.content || '').replace(/\n/g, '<br>')
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 复制功能
const copied = ref(false)

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    ElMessage.success('内容已复制到剪贴板')

    // 2秒后恢复图标
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
    ElMessage.error('复制失败,请重试')
  }
}

// 重新生成功能
const regenerateMessage = () => {
  emit('regenerate', props.message)
}
</script>

<style lang="scss" scoped>
.message-bubble {
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;

  &.user-message {
    .message-content {
      flex-direction: row-reverse;
    }

    .content {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
      border: 1px solid rgba(102, 126, 234, 0.3);
      margin-right: 12px;
      margin-left: auto;
      max-width: 70%;
    }
  }

  &.assistant-message {
    .content {
      background: var(--tech-glass-bg);
      border: 1px solid var(--tech-glass-border);
      margin-left: 12px;
      max-width: 80%;
    }
  }
}

.message-content {
  display: flex;
  align-items: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tech-neon-blue) 0%, var(--tech-neon-purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

// 多模态消息样式
.multimodal-content {
  .message-images {
    margin-bottom: 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;

    .message-image-item {
      border-radius: var(--tech-radius-md);
      overflow: hidden;
      box-shadow: var(--tech-shadow-sm);
      transition: all 0.3s ease;

      &:hover {
        transform: scale(1.02);
        box-shadow: var(--tech-shadow-md);
      }
    }
  }

  .text {
    margin-top: 8px;
  }
}

.content {
  padding: 12px 16px;
  border-radius: 12px;
  backdrop-filter: blur(10px);

  .text {
    color: var(--tech-text-primary);
    line-height: 1.8;
    font-size: 14px;
    word-wrap: break-word;
    overflow-wrap: break-word;

    // 段落间距
    :deep(p) {
      margin: 0.8em 0;
      line-height: 1.8;

      &:first-child {
        margin-top: 0;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }

    // 标题样式
    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
      margin: 1.2em 0 0.6em 0;
      font-weight: 600;
      line-height: 1.4;
      color: var(--tech-neon-blue);

      &:first-child {
        margin-top: 0;
      }
    }

    :deep(h1) { font-size: 1.8em; border-bottom: 2px solid rgba(0, 212, 255, 0.3); padding-bottom: 0.3em; }
    :deep(h2) { font-size: 1.5em; border-bottom: 1px solid rgba(0, 212, 255, 0.2); padding-bottom: 0.3em; }
    :deep(h3) { font-size: 1.3em; }
    :deep(h4) { font-size: 1.1em; }
    :deep(h5) { font-size: 1em; }
    :deep(h6) { font-size: 0.9em; color: var(--tech-text-secondary); }

    // 列表样式
    :deep(ul), :deep(ol) {
      margin: 0.8em 0;
      padding-left: 2em;

      li {
        margin: 0.4em 0;
        line-height: 1.6;
      }

      ul, ol {
        margin: 0.4em 0;
      }
    }

    :deep(ul) {
      list-style-type: disc;

      ul {
        list-style-type: circle;

        ul {
          list-style-type: square;
        }
      }
    }

    // 任务列表
    :deep(input[type="checkbox"]) {
      margin-right: 0.5em;
    }

    // 代码块样式
    :deep(pre) {
      background: rgba(13, 17, 23, 0.95);
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 1em 0;
      border: 1px solid rgba(0, 212, 255, 0.2);
      position: relative;

      code {
        background: transparent;
        padding: 0;
        color: #e6edf3;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
      }
    }

    // 行内代码样式
    :deep(code) {
      background: rgba(0, 212, 255, 0.15);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--tech-neon-blue);
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 0.9em;
      border: 1px solid rgba(0, 212, 255, 0.2);
    }

    // 引用块样式
    :deep(blockquote) {
      margin: 1em 0;
      padding: 0.8em 1em;
      border-left: 4px solid var(--tech-neon-blue);
      background: rgba(0, 212, 255, 0.05);
      border-radius: 0 4px 4px 0;
      color: var(--tech-text-secondary);

      p {
        margin: 0.4em 0;
      }
    }

    // 表格样式
    :deep(table) {
      border-collapse: collapse;
      width: 100%;
      margin: 1em 0;
      font-size: 0.95em;
      border: 1px solid rgba(0, 212, 255, 0.2);
      border-radius: 8px;
      overflow: hidden;

      thead {
        background: rgba(0, 212, 255, 0.1);

        th {
          font-weight: 600;
          color: var(--tech-neon-blue);
        }
      }

      th, td {
        padding: 10px 12px;
        text-align: left;
        border: 1px solid rgba(0, 212, 255, 0.15);
      }

      tbody tr {
        &:nth-child(even) {
          background: rgba(0, 212, 255, 0.03);
        }

        &:hover {
          background: rgba(0, 212, 255, 0.08);
        }
      }
    }

    // 链接样式
    :deep(a) {
      color: var(--tech-neon-blue);
      text-decoration: none;
      border-bottom: 1px solid transparent;
      transition: all 0.2s ease;

      &:hover {
        border-bottom-color: var(--tech-neon-blue);
        text-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
      }
    }

    // 水平分割线
    :deep(hr) {
      margin: 1.5em 0;
      border: none;
      border-top: 2px solid rgba(0, 212, 255, 0.2);
    }

    // 图片样式
    :deep(img) {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      margin: 1em 0;
      border: 1px solid rgba(0, 212, 255, 0.2);
    }

    // 强调和粗体
    :deep(strong), :deep(b) {
      font-weight: 600;
      color: var(--tech-neon-blue);
    }

    :deep(em), :deep(i) {
      font-style: italic;
      color: var(--tech-text-secondary);
    }

    // 删除线
    :deep(del), :deep(s) {
      text-decoration: line-through;
      opacity: 0.7;
    }
  }

  .meta {
    margin-top: 8px;
    font-size: 12px;
    color: var(--tech-text-muted);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;

    .action-buttons {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .action-btn {
      color: var(--tech-text-muted);
      opacity: 0;
      transition: all 0.2s ease;

      &:hover {
        color: var(--tech-neon-blue);
        transform: scale(1.1);
      }

      &.regenerate-btn:hover {
        color: var(--tech-neon-purple);
        animation: rotate 0.6s ease-in-out;
      }
    }
  }

  &:hover .meta .action-btn {
    opacity: 1;
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 加载动画
.loading-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--tech-text-muted);
    animation: typing 1.4s ease-in-out infinite;

    &:nth-child(1) {
      animation-delay: 0s;
    }

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.3;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}
</style>