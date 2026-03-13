<template>
  <div class="image-upload">
    <!-- 上传区域 -->
    <div
      class="upload-area"
      :class="{ 'dragover': isDragOver, 'disabled': isUploading || uploadedImages.length >= maxFiles }"
      @drop="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @click="selectFiles"
    >
      <el-icon class="upload-icon" :size="32">
        <UploadFilled />
      </el-icon>
      <p class="upload-text">点击或拖拽图片到此处上传</p>
      <p class="upload-hint">支持 JPG/PNG/GIF/WebP，最大5MB，最多{{ maxFiles }}张</p>

      <!-- 上传进度 -->
      <div v-if="isUploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :show-text="false" />
        <span>上传中... {{ uploadProgress }}%</span>
      </div>
    </div>

    <!-- 已上传图片列表 -->
    <div v-if="uploadedImages.length > 0" class="image-list">
      <div v-for="image in uploadedImages" :key="image.id" class="image-item">
        <div class="image-container">
          <img
            :src="image.thumbnail_url"
            :alt="image.original_name"
            @click="previewImageFunc(image)"
            class="thumbnail"
          />
          <div class="image-overlay" @click="previewImageFunc(image)">
            <el-icon><ZoomIn /></el-icon>
          </div>
          <el-button
            type="danger"
            size="small"
            circle
            class="delete-btn"
            @click="removeImage(image)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div class="image-info">
          <p class="image-name" :title="image.original_name">
            {{ image.original_name }}
          </p>
          <p class="image-size">{{ formatFileSize(image.file_size) }}</p>
          <p class="image-dimensions" v-if="image.width && image.height">
            {{ image.width }} × {{ image.height }}
          </p>
        </div>
      </div>
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

    <!-- 图片预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      :title="currentPreviewImage?.original_name"
      width="80%"
      center
      destroy-on-close
    >
      <div class="preview-container">
        <img
          :src="currentPreviewImage?.url"
          :alt="currentPreviewImage?.original_name"
          class="preview-image"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, ZoomIn, Delete } from '@element-plus/icons-vue'
import api from '../../services/api'

// Props
const props = defineProps({
  sessionId: {
    type: String,
    required: true
  },
  maxFiles: {
    type: Number,
    default: 3
  }
})

// Emits
const emit = defineEmits(['uploaded', 'removed'])

// 状态
const fileInput = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadedImages = ref([])
const previewVisible = ref(false)
const currentPreviewImage = ref(null)

// API base URL
const API_BASE = ''

// 选择文件
const selectFiles = () => {
  if (isUploading.value || uploadedImages.value.length >= props.maxFiles) {
    return
  }
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  handleFiles(files)
  // 清空input，允许重复选择同一文件
  event.target.value = ''
}

// 处理拖拽
const handleDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false

  const files = Array.from(event.dataTransfer.files)
  handleFiles(files)
}

// 处理文件列表
const handleFiles = async (files) => {
  // 过滤图片文件
  const imageFiles = files.filter(file => file.type.startsWith('image/'))

  if (imageFiles.length === 0) {
    ElMessage.warning('请选择图片文件')
    return
  }

  // 检查数量限制
  const totalFiles = uploadedImages.value.length + imageFiles.length
  if (totalFiles > props.maxFiles) {
    ElMessage.warning(`最多只能上传${props.maxFiles}张图片`)
    return
  }

  // 检查文件大小
  const oversizedFiles = imageFiles.filter(file => file.size > 5 * 1024 * 1024)
  if (oversizedFiles.length > 0) {
    ElMessage.warning('图片大小不能超过5MB')
    return
  }

  await uploadImages(imageFiles)
}

// 上传图片
const uploadImages = async (files) => {
  isUploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  formData.append('session_id', props.sessionId)

  try {
    const response = await api.post(`/api/chat/images/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        uploadProgress.value = percent
      }
    })

    if (response.data.success) {
      uploadedImages.value.push(...response.data.data)
      ElMessage.success(`成功上传${response.data.data.length}张图片`)
      emit('uploaded', response.data.data)
    }
  } catch (error) {
    console.error('Upload error:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

// 删除图片
const removeImage = async (image) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除图片 "${image.original_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/api/chat/images/${image.id}`)

    // 从列表中移除
    const index = uploadedImages.value.findIndex(img => img.id === image.id)
    if (index > -1) {
      uploadedImages.value.splice(index, 1)
    }

    ElMessage.success('图片已删除')
    emit('removed', image)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 预览图片
const previewImageFunc = (image) => {
  currentPreviewImage.value = image
  previewVisible.value = true
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 清空上传的图片
const clearImages = () => {
  uploadedImages.value = []
}

// 获取上传的图片列表
const getUploadedImages = () => {
  return uploadedImages.value
}

// 导出方法供父组件调用
defineExpose({
  clearImages,
  getUploadedImages
})
</script>

<style lang="scss" scoped>
.image-upload {
  width: 100%;
}

.upload-area {
  border: 2px dashed var(--tech-border-color);
  border-radius: var(--tech-radius-lg);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--tech-glass-bg);
  position: relative;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  &:hover, &.dragover {
    border-color: var(--tech-neon-blue);
    background: rgba(0, 212, 255, 0.05);
  }

  &.disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .upload-icon {
    color: var(--tech-neon-blue);
    margin-bottom: 16px;
  }

  .upload-text {
    margin: 0 0 8px 0;
    font-size: 16px;
    color: var(--tech-text-primary);
  }

  .upload-hint {
    margin: 0;
    font-size: 14px;
    color: var(--tech-text-secondary);
  }

  .upload-progress {
    position: absolute;
    bottom: 20px;
    left: 20px;
    right: 20px;
    display: flex;
    align-items: center;
    gap: 12px;

    .el-progress {
      flex: 1;
    }

    span {
      font-size: 14px;
      color: var(--tech-neon-blue);
      white-space: nowrap;
    }
  }
}

.image-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.image-item {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-border-color);
  border-radius: var(--tech-radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;

  &:hover {
    border-color: var(--tech-neon-blue);
    transform: translateY(-2px);
  }
}

.image-container {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;

  .thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    cursor: pointer;
    transition: transform 0.3s ease;

    &:hover {
      transform: scale(1.05);
    }
  }

  .image-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
    cursor: pointer;

    .el-icon {
      font-size: 32px;
      color: white;
    }
  }

  &:hover .image-overlay {
    opacity: 1;
  }

  .delete-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  &:hover .delete-btn {
    opacity: 1;
  }
}

.image-info {
  padding: 12px;

  .image-name {
    margin: 0 0 4px 0;
    font-size: 14px;
    font-weight: 500;
    color: var(--tech-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .image-size, .image-dimensions {
    margin: 0;
    font-size: 12px;
    color: var(--tech-text-secondary);
  }
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;

  .preview-image {
    max-width: 100%;
    max-height: 70vh;
    object-fit: contain;
    border-radius: var(--tech-radius-lg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .image-list {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }

  .upload-area {
    padding: 30px 15px;
    min-height: 150px;
  }
}
</style>