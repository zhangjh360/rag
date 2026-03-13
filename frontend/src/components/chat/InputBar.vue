<template>
  <div class="input-bar">
    <!-- 已上传图片预览（紧凑模式） -->
    <div v-if="uploadedImages.length > 0" class="compact-images-preview">
      <div class="preview-images-list">
        <div v-for="image in uploadedImages" :key="image.id" class="compact-image-item">
          <img :src="image.thumbnail_url" :alt="image.original_name" class="compact-thumbnail" />
          <el-button
            type="danger"
            size="small"
            circle
            class="remove-btn"
            @click="removeImage(image)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
          <div class="image-name-tooltip">{{ image.original_name }}</div>
        </div>
      </div>
    </div>

    <!-- 输入框容器 -->
    <div class="input-wrapper">
      <!-- 附件图标（放在输入框内左侧） -->
      <el-tooltip content="上传图片" placement="top">
        <el-button
          circle
          text
          :disabled="disabled || isGenerating || uploadedImages.length >= maxImages"
          @click="triggerFileSelect"
          class="attach-button-inner"
        >
          <el-icon><Paperclip /></el-icon>
        </el-button>
      </el-tooltip>

      <!-- 上传进度提示 -->
      <span v-if="isUploading" class="upload-status">上传中...</span>

      <!-- 输入框 -->
      <el-input
        v-model="localValue"
        type="textarea"
        :placeholder="placeholder"
        :disabled="disabled"
        :rows="3"
        @keydown.enter.prevent="handleEnter"
        class="tech-textarea"
      />

      <!-- 发送按钮（放在输入框内右侧） -->
      <el-button
        v-if="!isGenerating"
        @click="sendMessage"
        :disabled="disabled || (!localValue.trim() && uploadedImages.length === 0)"
        type="primary"
        circle
        class="send-button-inner"
      >
        <el-icon><Promotion /></el-icon>
      </el-button>
      <el-button
        v-else
        @click="$emit('stop')"
        type="danger"
        circle
        class="stop-button-inner"
      >
        <el-icon><VideoPause /></el-icon>
      </el-button>
    </div>

    <!-- 提示信息 -->
    <div class="input-tips">
      <span class="tip">Enter 发送 / Shift+Enter 换行</span>
      <span v-if="uploadedImages.length > 0" class="image-count">
        已选择 {{ uploadedImages.length }}/{{ maxImages }} 张图片
      </span>
      <span class="char-count">{{ charCount }}/4000</span>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      type="file"
      ref="fileInput"
      multiple
      accept="image/*"
      @change="handleFileSelect"
      style="display: none"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Promotion, VideoPause, Paperclip, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../../services/api'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '输入您的问题...'
  },
  sessionId: {
    type: String,
    required: true
  },
  maxImages: {
    type: Number,
    default: 3
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'stop', 'send-with-images'])

const localValue = ref(props.modelValue)
const uploadedImages = ref([])
const fileInput = ref(null)
const isUploading = ref(false)

watch(() => props.modelValue, (newVal) => {
  localValue.value = newVal
})

watch(localValue, (newVal) => {
  emit('update:modelValue', newVal)
})

const charCount = computed(() => localValue.value.length)

const handleEnter = (e) => {
  if (!e.shiftKey && (localValue.value.trim() || uploadedImages.value.length > 0)) {
    e.preventDefault()
    sendMessage()
  }
}

const sendMessage = () => {
  if ((localValue.value.trim() || uploadedImages.value.length > 0) && !props.disabled) {
    if (uploadedImages.value.length > 0) {
      emit('send-with-images', {
        text: localValue.value,
        images: uploadedImages.value
      })
      localValue.value = ''
      uploadedImages.value = []
    } else {
      emit('send')
      localValue.value = ''
    }
  }
}

const triggerFileSelect = () => {
  if (uploadedImages.value.length >= props.maxImages) {
    ElMessage.warning(`最多只能上传${props.maxImages}张图片`)
    return
  }
  fileInput.value?.click()
}

const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length === 0) return

  const remainingSlots = props.maxImages - uploadedImages.value.length
  if (files.length > remainingSlots) {
    ElMessage.warning(`最多还能上传${remainingSlots}张图片`)
    return
  }

  const imageFiles = files.filter(file => file.type.startsWith('image/'))
  if (imageFiles.length === 0) {
    ElMessage.warning('请选择图片文件')
    return
  }

  const oversizedFiles = imageFiles.filter(file => file.size > 5 * 1024 * 1024)
  if (oversizedFiles.length > 0) {
    ElMessage.warning('图片大小不能超过5MB')
    return
  }

  await uploadImages(imageFiles)
  event.target.value = ''
}

const uploadImages = async (files) => {
  isUploading.value = true

  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  formData.append('session_id', props.sessionId)

  try {
    const response = await api.post(`/api/chat/images/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      uploadedImages.value.push(...response.data.data)
      ElMessage.success(`成功上传${response.data.data.length}张图片`)
    }
  } catch (error) {
    console.error('Upload error:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    isUploading.value = false
  }
}

const removeImage = async (image) => {
  try {
    await api.delete(`/api/chat/images/${image.id}`)
    const index = uploadedImages.value.findIndex(img => img.id === image.id)
    if (index > -1) {
      uploadedImages.value.splice(index, 1)
    }
    ElMessage.success('图片已删除')
  } catch (error) {
    console.error('Delete error:', error)
    ElMessage.error('删除失败')
  }
}
</script>

<style lang="scss" scoped>
.input-bar {
  background: transparent;
  padding: 0;
}

// 紧凑图片预览
.compact-images-preview {
  margin-bottom: 12px;
  padding: 8px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-border-color);
  border-radius: var(--tech-radius-md);

  .preview-images-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .compact-image-item {
    position: relative;
    width: 60px;
    height: 60px;
    border-radius: var(--tech-radius-sm);
    overflow: hidden;
    transition: transform 0.2s;

    &:hover {
      transform: scale(1.05);

      .remove-btn {
        opacity: 1;
      }

      .image-name-tooltip {
        opacity: 1;
        visibility: visible;
      }
    }

    .compact-thumbnail {
      width: 100%;
      height: 100%;
      object-fit: cover;
      cursor: pointer;
    }

    .remove-btn {
      position: absolute;
      top: 2px;
      right: 2px;
      width: 20px;
      height: 20px;
      padding: 0;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 2;

      :deep(.el-icon) {
        font-size: 12px;
      }
    }

    .image-name-tooltip {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      font-size: 10px;
      padding: 4px;
      text-align: center;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      opacity: 0;
      visibility: hidden;
      transition: all 0.2s;
    }
  }
}

// 输入框容器（附件和发送按钮都在内部）
.input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 8px;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);

  &:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--tech-border-hover);
  }

  &:focus-within {
    background: rgba(255, 255, 255, 0.06);
    border-color: var(--tech-neon-blue);
    box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
  }

  .attach-button-inner {
    flex-shrink: 0;
    margin-bottom: 4px;
    transition: all 0.3s ease;

    &:hover:not(:disabled) {
      transform: scale(1.1);
      color: var(--tech-neon-blue);
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }

  .upload-status {
    flex-shrink: 0;
    font-size: 12px;
    color: var(--tech-neon-blue);
    margin-bottom: 8px;
    animation: pulse 1.5s ease-in-out infinite;
  }

  :deep(.tech-textarea) {
    flex: 1;

    .el-textarea__inner {
      background: transparent;
      border: none;
      color: var(--tech-text-primary);
      resize: none;
      padding: 4px 8px;
      font-size: 14px;
      line-height: 1.5;
      box-shadow: none;

      &:focus {
        box-shadow: none;
        background: transparent;
      }

      &::placeholder {
        color: var(--tech-text-tertiary);
      }
    }
  }

  .send-button-inner,
  .stop-button-inner {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    margin-bottom: 4px;

    &:hover:not(:disabled) {
      transform: scale(1.1);
      box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }

  .send-button-inner {
    background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
  }

  .stop-button-inner {
    background: linear-gradient(135deg, #ff4757, #ff6b81);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.input-tips {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--tech-text-tertiary);

  .tip {
    opacity: 0.7;
  }

  .image-count {
    color: var(--tech-neon-blue);
    font-weight: 500;
  }

  .char-count {
    opacity: 0.7;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .compact-images-preview {
    .compact-image-item {
      width: 50px;
      height: 50px;
    }
  }

  .input-wrapper {
    .send-button-inner,
    .stop-button-inner {
      width: 32px;
      height: 32px;
    }
  }
}
</style>
