<template>
  <div class="chat-image" :class="{ 'inline': inline }">
    <!-- 缩略图（点击查看大图） -->
    <img
      :src="imageUrl"
      :alt="alt"
      @click="showPreview = true"
      :style="imageStyle"
      class="message-image"
    />

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="showPreview"
      :title="originalName"
      width="80%"
      center
      destroy-on-close
      append-to-body
    >
      <div class="image-preview-container">
        <img
          :src="imageUrl"
          :alt="alt"
          class="preview-image"
        />
        <div class="image-details">
          <p><strong>文件名：</strong>{{ originalName }}</p>
          <p v-if="width && height"><strong>尺寸：</strong>{{ width }} × {{ height }}</p>
          <p v-if="fileSize"><strong>大小：</strong>{{ formatFileSize(fileSize) }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
  src: {
    type: String,
    required: true
  },
  thumbnail: {
    type: String,
    default: ''
  },
  originalName: {
    type: String,
    default: ''
  },
  width: {
    type: Number,
    default: null
  },
  height: {
    type: Number,
    default: null
  },
  fileSize: {
    type: Number,
    default: null
  },
  maxWidth: {
    type: Number,
    default: 300
  },
  inline: {
    type: Boolean,
    default: false
  }
})

// 图片加载错误处理
const imageError = ref(false)

// 预览对话框
const showPreview = ref(false)

// 计算显示的图片URL（优先使用缩略图）
const imageUrl = computed(() => {
  if (imageError.value) {
    // 返回默认图片
    return '/src/assets/images/image-error.png'
  }
  return props.thumbnail || props.src
})

// 计算图片样式
const imageStyle = computed(() => {
  const style = {}

  // 设置最大宽度
  if (props.maxWidth) {
    style.maxWidth = `${props.maxWidth}px`
  }

  // 设置最大高度（内联模式）
  if (props.inline && props.maxWidth) {
    style.maxHeight = `${props.maxWidth}px`
  }

  return style
})

// 图片加载错误处理
const handleImageError = () => {
  imageError.value = true
  ElMessage.error('图片加载失败')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style lang="scss" scoped>
.chat-image {
  display: inline-block;
  margin: 4px;

  &.inline {
    display: inline-block;
    vertical-align: middle;
  }
}

.message-image {
  cursor: pointer;
  border-radius: var(--tech-radius-md);
  transition: all 0.3s ease;
  box-shadow: var(--tech-shadow-sm);

  &:hover {
    transform: scale(1.02);
    box-shadow: var(--tech-shadow-md);
  }
}

.image-preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;

  .preview-image {
    max-width: 100%;
    max-height: 70vh;
    object-fit: contain;
    border-radius: var(--tech-radius-lg);
    box-shadow: var(--tech-shadow-lg);
  }

  .image-details {
    text-align: center;
    color: var(--tech-text-secondary);

    p {
      margin: 4px 0;
      font-size: 14px;
    }
  }
}

// 深色主题下的对话框样式调整
:deep(.el-dialog) {
  background: var(--tech-bg-secondary);
  border: 1px solid var(--tech-border-color);

  .el-dialog__header {
    border-bottom: 1px solid var(--tech-border-color);

    .el-dialog__title {
      color: var(--tech-text-primary);
    }
  }

  .el-dialog__body {
    color: var(--tech-text-primary);
  }
}
</style>