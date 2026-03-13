<template>
  <div class="documents-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div>
          <h1 class="page-title">📄 文档管理</h1>
          <p class="page-subtitle">构建和检索您的RAG知识库</p>
        </div>
        <div class="header-actions">
          <el-input
            v-model="searchQuery"
            placeholder="语义搜索知识库..."
            class="search-input"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
          <el-button type="primary" @click="showUploadDialog = true" class="upload-btn">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </div>
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="documents-layout">
      <!-- 左侧导航栏 -->
      <div class="sidebar">
        <div class="sidebar-section">
          <h3 class="sidebar-title">📁 文件夹</h3>
          <div class="folder-list">
            <div
              v-for="folder in folders"
              :key="folder.id"
              :class="['folder-item', { active: selectedFolder === folder.id }]"
              @click="selectedFolder = folder.id"
            >
              <el-icon><Folder /></el-icon>
              <span>{{ folder.name }}</span>
              <span class="folder-count">({{ folder.count }})</span>
            </div>
          </div>
        </div>

        <div class="sidebar-section">
          <h3 class="sidebar-title">🏷️ 标签</h3>
          <div class="tag-list">
            <div
              v-for="tag in tags"
              :key="tag.id"
              :class="['tag-item', { active: selectedTags.includes(tag.id) }]"
              @click="toggleTag(tag.id)"
            >
              <span class="tag-dot" :style="{ backgroundColor: tag.color }"></span>
              <span>{{ tag.name }}</span>
              <span class="tag-count">({{ tag.count }})</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间文档列表 -->
      <div class="main-content">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <el-button
              v-if="selectedDocuments.length > 0"
              type="text"
              @click="clearSelection"
            >
              取消选择 ({{ selectedDocuments.length }})
            </el-button>
          </div>
          <div class="toolbar-right">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="grid">
                <el-icon><Grid /></el-icon>
              </el-radio-button>
              <el-radio-button label="list">
                <el-icon><List /></el-icon>
              </el-radio-button>
            </el-radio-group>
            <el-select v-model="sortBy" size="small" style="width: 120px;">
              <el-option label="最新上传" value="date" />
              <el-option label="文件名" value="name" />
              <el-option label="文件大小" value="size" />
            </el-select>
          </div>
        </div>

        <!-- 文档列表 -->
        <div class="documents-container" :class="viewMode">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>

          <div
            v-else
            v-for="document in filteredDocuments"
            :key="document.id"
            :class="['document-card', { selected: selectedDocuments.includes(document.id) }]"
            @click="selectDocument(document.id, $event)"
          >
            <!-- 网格视图 -->
            <template v-if="viewMode === 'grid'">
              <div class="document-icon">
                <el-icon size="48" :color="getFileTypeColor(document.name)">
                  <component :is="getFileTypeIcon(document.name)" />
                </el-icon>
                <div class="document-status processed"></div>
              </div>
              <div class="document-info">
                <h4 class="document-title" :title="document.name">{{ document.name }}</h4>
                <p class="document-meta">
                  <span>{{ formatFileSize(document.size) }}</span>
                  <span>•</span>
                  <span>{{ formatDate(document.uploadTime) }}</span>
                </p>
              </div>
              <!-- 领域标签 -->
              <div class="document-domain" v-if="document.namespace">
                <el-tag
                  size="small"
                  :type="document.namespace === 'default' ? 'info' : 'primary'"
                  effect="plain"
                >
                  {{ getDomainInfo(document.namespace).icon }} {{ getDomainInfo(document.namespace).display_name }}
                </el-tag>
              </div>
              <div class="document-tags" v-if="document.tags && document.tags.length > 0">
                <el-tag
                  v-for="(tag, tagIndex) in document.tags"
                  :key="`doc-tag-${document.id}-${tagIndex}`"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <!-- 快捷操作按钮 -->
              <div class="document-actions" @click.stop>
                <el-button
                  size="small"
                  type="text"
                  @click="handlePreviewDocument(document)"
                  title="预览"
                >
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button
                  size="small"
                  type="text"
                  @click="downloadDocument(document)"
                  title="下载"
                >
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button
                  size="small"
                  type="text"
                  @click="deleteDocument(document)"
                  title="删除"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>

            <!-- 列表视图 -->
            <template v-else>
              <div class="document-row">
                <div class="document-icon-small">
                  <el-icon size="24" :color="getFileTypeColor(document.name)">
                    <component :is="getFileTypeIcon(document.name)" />
                  </el-icon>
                </div>
                <div class="document-content">
                  <div class="document-header">
                    <h4 class="document-name">{{ document.name }}</h4>
                    <div class="document-status processed"></div>
                  </div>
                  <div class="document-details">
                    <span>{{ formatFileSize(document.size) }}</span>
                    <span>•</span>
                    <span>{{ formatDate(document.uploadTime) }}</span>
                    <span>•</span>
                    <span>{{ document.type.toUpperCase() }}</span>
                    <span v-if="document.namespace">•</span>
                    <el-tag
                      v-if="document.namespace"
                      size="small"
                      :type="document.namespace === 'default' ? 'info' : 'primary'"
                      effect="plain"
                      style="margin-left: 4px;"
                    >
                      {{ getDomainInfo(document.namespace).icon }} {{ getDomainInfo(document.namespace).display_name }}
                    </el-tag>
                  </div>
                </div>
                <div class="document-actions">
                  <el-button size="small" type="text" @click="handlePreviewDocument(document)">
                    <el-icon><View /></el-icon>
                  </el-button>
                  <el-button size="small" type="text" @click="downloadDocument(document)">
                    <el-icon><Download /></el-icon>
                  </el-button>
                  <el-button size="small" type="text" @click="deleteDocument(document)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredDocuments.length === 0" class="empty-state">
          <el-icon :size="64" color="#666"><Document /></el-icon>
          <h3>暂无文档</h3>
          <p>开始上传您的第一个文档吧</p>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传文档
          </el-button>
        </div>
      </div>

      <!-- 右侧详情面板 -->
      <div class="detail-panel" v-if="selectedDocument">
        <div class="panel-header">
          <h3>文档详情</h3>
          <el-button size="small" type="text" @click="selectedDocument = null">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <div class="panel-content" v-if="selectedDocument">
          <!-- 文档预览 -->
          <div class="document-preview">
            <el-icon size="64" :color="getFileTypeColor(selectedDocument.name)">
              <component :is="getFileTypeIcon(selectedDocument.name)" />
            </el-icon>
            <h4 class="document-name">{{ selectedDocument.name }}</h4>
            <div class="document-status processed"></div>
          </div>

          <!-- 文档内容预览 -->
          <div class="info-section">
            <h4>内容预览</h4>
            <div class="content-preview">
              <div class="content-text">
                {{ selectedDocument.content || '暂无内容' }}
              </div>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="info-section">
            <h4>基本信息</h4>
            <div class="info-item">
              <span class="info-label">文件名:</span>
              <span class="info-value">{{ selectedDocument.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">文件类型:</span>
              <span class="info-value">{{ selectedDocument.type.toUpperCase() }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">上传时间:</span>
              <span class="info-value">{{ formatDate(selectedDocument.uploadTime) }}</span>
            </div>
            <div class="info-item" v-if="selectedDocument.size">
              <span class="info-label">文件大小:</span>
              <span class="info-value">{{ formatFileSize(selectedDocument.size) }}</span>
            </div>
            <div class="info-item" v-if="selectedDocument.namespace">
              <span class="info-label">知识领域:</span>
              <span class="info-value">
                <el-tag
                  size="small"
                  :type="selectedDocument.namespace === 'default' ? 'info' : 'primary'"
                  effect="plain"
                >
                  {{ getDomainInfo(selectedDocument.namespace).icon }} {{ getDomainInfo(selectedDocument.namespace).display_name }}
                </el-tag>
              </span>
            </div>
            <div class="info-item" v-if="selectedDocument.domainConfidence > 0">
              <span class="info-label">分类置信度:</span>
              <span class="info-value">{{ (selectedDocument.domainConfidence * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <!-- 标签管理 -->
          <div class="info-section">
            <h4>标签</h4>
            <div class="tag-management">
              <div class="current-tags" v-if="selectedDocument.tags && selectedDocument.tags.length > 0">
                <el-tag
                  v-for="(tag, tagIndex) in selectedDocument.tags"
                  :key="`tag-${tagIndex}`"
                  closable
                  size="small"
                  @close="removeTag(tag)"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <el-input
                v-if="showTagInput"
                v-model="newTag"
                size="small"
                placeholder="添加标签..."
                @keyup.enter="addTag"
                @blur="addTag"
                style="width: 120px; margin-top: 8px;"
              />
              <el-button v-else size="small" type="text" @click="showTagInput = true">
                <el-icon><Plus /></el-icon>
                添加标签
              </el-button>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="info-section">
            <h4>操作</h4>
            <div class="action-buttons">
              <el-button type="primary" @click="handlePreviewDocument(selectedDocument)">
                <el-icon><View /></el-icon>
                预览
              </el-button>
              <el-button @click="downloadDocument(selectedDocument)">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
              <el-button type="danger" @click="deleteDocument(selectedDocument)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="600px">
      <!-- 文件选择区域 - 只在没有文件时显示 -->
      <div v-show="selectedFiles.length === 0" class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
        <el-icon :size="48" color="#409eff"><UploadFilled /></el-icon>
        <p>拖拽文件到此处或点击选择文件</p>
        <el-button @click="openFileDialog()">选择文件</el-button>
        <input
          ref="fileInput"
          type="file"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
      </div>

      <!-- 已选择的文件列表 - 选择文件后立即显示 -->
      <div v-show="selectedFiles.length > 0" class="file-selection-area">
        <div class="selection-header">
          <h4>已选择文件 ({{ selectedFiles.length }})</h4>
          <el-button size="small" @click="clearSelectedFiles">重新选择</el-button>
        </div>

        <!-- 领域选择 -->
        <div class="domain-selection">
          <label class="domain-label">知识领域:</label>
          <domain-selector
            v-model="selectedDomain"
            placeholder="选择知识领域 (可选)"
            clearable
            show-stats
          />
          <div class="domain-tip">
            选择领域后,文档将自动归类到对应的知识领域,便于精准检索
          </div>
        </div>

        <div class="file-list">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <div class="file-info">
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ file.name || '未命名文件' }}</span>
              <span class="file-size">({{ formatFileSize(file.size || 0) }})</span>
            </div>
            <el-button size="small" type="text" @click="removeFile(file)" class="remove-btn">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 继续添加文件按钮 -->
        <div class="add-more-files">
          <el-button size="small" type="primary" plain @click="openFileDialog()">
            <el-icon><Plus /></el-icon>
            继续添加文件
          </el-button>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploadingFiles.length > 0" class="upload-progress">
        <h4>上传进度</h4>
        <div v-for="(file, index) in uploadingFiles" :key="index" class="file-progress">
          <div class="file-info">
            <span class="file-name">{{ file.name || '上传中文件' }}</span>
            <span class="progress-text">{{ getUploadProgress(file, index) }}%</span>
          </div>
          <el-progress
            :percentage="getUploadProgress(file, index)"
            :show-text="false"
            :stroke-width="6"
          />
        </div>
      </div>

      <!-- 对话框底部按钮 -->
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeUploadDialog">取消</el-button>
          <el-button
            type="primary"
            @click="startUpload"
            :disabled="selectedFiles.length === 0 || uploading"
            :loading="uploading"
          >
            {{ uploading ? '上传中...' : '开始上传' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 文档预览对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="`预览: ${previewDocument?.filename || ''}`"
      width="70%"
      top="5vh"
      destroy-on-close
    >
      <div v-if="previewLoading" class="preview-loading">
        <el-skeleton :rows="10" animated />
      </div>
      <div v-else-if="previewDocument" class="preview-content">
        <div class="preview-header">
          <div class="preview-info">
            <span class="info-label">文件名:</span>
            <span class="info-value">{{ previewDocument.filename }}</span>
          </div>
          <div class="preview-info">
            <span class="info-label">文件类型:</span>
            <span class="info-value">{{ previewDocument.filename?.split('.').pop()?.toUpperCase() || 'TXT' }}</span>
          </div>
          <div class="preview-info" v-if="previewDocument.created_at">
            <span class="info-label">上传时间:</span>
            <span class="info-value">{{ formatDate(new Date(previewDocument.created_at)) }}</span>
          </div>
          <div class="preview-info" v-if="previewDocument.namespace">
            <span class="info-label">知识领域:</span>
            <el-tag
              size="small"
              :type="previewDocument.namespace === 'default' ? 'info' : 'primary'"
              effect="plain"
            >
              {{ getDomainInfo(previewDocument.namespace).icon }} {{ getDomainInfo(previewDocument.namespace).display_name }}
            </el-tag>
          </div>
        </div>
        <el-divider />
        <div class="preview-text">
          <pre>{{ previewDocument.content || '暂无内容' }}</pre>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPreviewDialog = false">关闭</el-button>
          <el-button type="primary" @click="downloadPreviewDocument">
            <el-icon><Download /></el-icon>
            下载
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRagStore } from '../store/ragStore'
import documentService from '../services/documentService'
import DomainSelector from '../components/domain/DomainSelector.vue'
import { getActiveDomains } from '../services/knowledgeDomains'
import {
  Search, Upload, Folder, Grid, List, View, Download, Delete, Close,
  Plus, Document, UploadFilled
} from '@element-plus/icons-vue'

const store = useRagStore()

// 响应式数据
const searchQuery = ref('')
const selectedFolder = ref('all')
const selectedTags = ref([])
const selectedDocuments = ref([])
const selectedDocument = ref(null)
const viewMode = ref('grid')
const sortBy = ref('date')
const showUploadDialog = ref(false)
const showTagInput = ref(false)
const newTag = ref('')
const loading = ref(false)
const uploadingFiles = ref([])
const uploadProgress = ref({})
const showFullContent = ref(false)
const selectedFiles = ref([])
const uploading = ref(false)
const fileInput = ref(null)
const selectedDomain = ref('default') // 添加领域选择
const showPreviewDialog = ref(false) // 预览对话框显示状态
const previewDocument = ref(null) // 预览的文档对象
const previewLoading = ref(false) // 预览加载状态

// 真实数据
const documents = ref([])
const documentStats = ref({
  total: 0,
  byType: {},
  recent: 0
})
const domainList = ref([]) // 知识领域列表

const folders = computed(() => {
  // 统计每个领域的文档数量
  const domainCounts = {}
  documents.value.forEach(doc => {
    const namespace = doc.namespace || 'default'
    domainCounts[namespace] = (domainCounts[namespace] || 0) + 1
  })

  // 构建文件夹列表
  const folderList = [
    { id: 'all', name: '📚 全部文档', count: documents.value.length },
    { id: 'recent', name: '🕒 最近上传', count: documentStats.value.recent || 0 }
  ]

  // 添加领域分类
  domainList.value.forEach(domain => {
    folderList.push({
      id: domain.namespace,
      name: `${domain.icon || '📁'} ${domain.display_name}`,
      count: domainCounts[domain.namespace] || 0,
      isDomain: true
    })
  })

  // 添加默认领域(未分类)
  if (domainCounts['default']) {
    folderList.push({
      id: 'default',
      name: '📁 未分类',
      count: domainCounts['default'] || 0,
      isDomain: true
    })
  }

  return folderList
})

const tags = computed(() => {
  const tagCounts = {}
  documents.value.forEach(doc => {
    if (doc.tags) {
      doc.tags.forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1
      })
    }
  })

  return [
    { id: 'important', name: '重要', color: '#ff4757', count: tagCounts['重要'] || 0 },
    { id: 'work', name: '工作', color: '#3742fa', count: tagCounts['工作'] || 0 },
    { id: 'personal', name: '个人', color: '#2ed573', count: tagCounts['个人'] || 0 },
    { id: 'study', name: '学习', color: '#ffa502', count: tagCounts['学习'] || 0 }
  ]
})

// 计算属性
const filteredDocuments = computed(() => {
  let filtered = documents.value

  // 搜索过滤
  if (searchQuery.value) {
    filtered = filtered.filter(doc => {
      const name = doc.filename || '未命名文档'
      const content = doc.content || ''
      const query = searchQuery.value.toLowerCase()
      return name.toLowerCase().includes(query) || content.toLowerCase().includes(query)
    })
  }

  // 文件夹过滤
  if (selectedFolder.value !== 'all') {
    filtered = filtered.filter(doc => {
      switch (selectedFolder.value) {
        case 'recent':
          return (Date.now() - doc.uploadTime.getTime()) < 7 * 24 * 60 * 60 * 1000
        default:
          // 按领域过滤
          return (doc.namespace || 'default') === selectedFolder.value
      }
    })
  }

  // 标签过滤
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(doc =>
      doc.tags.some(tag => selectedTags.value.includes(tag))
    )
  }

  // 排序
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'size':
        return b.size - a.size
      case 'date':
      default:
        return b.uploadTime - a.uploadTime
    }
  })

  return filtered
})

// 方法
const toggleTag = (tagId) => {
  const index = selectedTags.value.indexOf(tagId)
  if (index === -1) {
    selectedTags.value.push(tagId)
  } else {
    selectedTags.value.splice(index, 1)
  }
}

const selectDocument = (docId, event) => {
  if (event.ctrlKey || event.metaKey) {
    // 多选
    const index = selectedDocuments.value.indexOf(docId)
    if (index === -1) {
      selectedDocuments.value.push(docId)
    } else {
      selectedDocuments.value.splice(index, 1)
    }
  } else {
    // 单选并显示详情
    selectedDocuments.value = [docId]
    selectedDocument.value = documents.value.find(doc => doc.id === docId)
  }
}

const clearSelection = () => {
  selectedDocuments.value = []
  selectedDocument.value = null
}

const getFileType = (filename) => {
  if (!filename || typeof filename !== 'string') {
    return 'unknown'
  }
  const extension = filename.split('.').pop().toLowerCase()
  return extension || 'unknown'
}

const getFileTypeIcon = (filename) => {
  const type = getFileType(filename)
  const icons = {
    pdf: 'Document',
    docx: 'Document',
    doc: 'Document',
    txt: 'Document',
    default: 'Document'
  }
  return icons[type] || icons.default
}

const getFileTypeColor = (filename) => {
  const type = getFileType(filename)
  const colors = {
    pdf: '#ff4757',
    docx: '#3742fa',
    doc: '#3742fa',
    txt: '#2ed573',
    default: '#747d8c'
  }
  return colors[type] || colors.default
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

const handleDrop = (event) => {
  event.preventDefault()
  const files = Array.from(event.dataTransfer.files)
  console.log('Dropped files:', files)

  if (files.length > 0) {
    // 验证并添加文件
    const validFiles = files.filter(file => file && file.name)
    if (validFiles.length > 0) {
      nextTick(() => {
        selectedFiles.value.push(...validFiles)
        ElMessage.success(`拖拽成功，选择了 ${validFiles.length} 个文件`)
      })
    }
  }
}

const openFileDialog = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleFileSelect = (event) => {
  if (!event.target || !event.target.files) {
    console.error('Invalid file input event')
    return
  }

  const files = Array.from(event.target.files)
  console.log('Selected files:', files)

  // 验证文件对象
  const validFiles = files.filter(file => {
    if (!file || typeof file !== 'object' || !file.name) {
      console.warn('Invalid file object:', file)
      return false
    }
    return true
  })

  if (validFiles.length === 0) {
    ElMessage.warning('没有有效的文件被选择')
    return
  }

  // 使用 nextTick 确保响应式更新
  nextTick(() => {
    // 清空现有选择并添加新文件
    selectedFiles.value = [...validFiles]
    console.log('selectedFiles.value after update:', selectedFiles.value)
    console.log('selectedFiles.value.length:', selectedFiles.value.length)

    ElMessage.success(`选择了 ${validFiles.length} 个文件`)
  })

  // 清空input以便可以重复选择同一文件
  event.target.value = ''
}

const removeFile = (fileToRemove) => {
  const index = selectedFiles.value.findIndex(file => file.name === fileToRemove.name)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  }
}

const clearSelectedFiles = () => {
  selectedFiles.value = []
  // 清空input以便可以重复选择同一文件
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const getUploadProgress = (file, index) => {
  return uploadProgress.value[index] || 0
}

const startUpload = async () => {
  if (selectedFiles.value.length === 0) return

  uploading.value = true
  try {
    await handleFileUpload(selectedFiles.value)
    // 上传成功后关闭对话框
    showUploadDialog.value = false
    selectedFiles.value = []
  } finally {
    uploading.value = false
  }
}

const closeUploadDialog = () => {
  showUploadDialog.value = false
  selectedFiles.value = []
  uploadingFiles.value = []
  uploadProgress.value = {}
  uploading.value = false
}

const handlePreviewDocument = async (doc) => {
  try {
    previewLoading.value = true
    showPreviewDialog.value = true

    // 获取完整文档内容
    const fullDoc = await documentService.getDocument(doc.id)
    previewDocument.value = fullDoc
  } catch (error) {
    console.error('获取文档详情失败:', error)
    ElMessage.error('获取文档详情失败：' + (error.message || '未知错误'))
    showPreviewDialog.value = false
  } finally {
    previewLoading.value = false
  }
}

// 下载预览中的文档
const downloadPreviewDocument = async () => {
  if (!previewDocument.value) return

  try {
    const success = await documentService.downloadDocument(
      previewDocument.value.id,
      previewDocument.value.filename
    )

    if (success) {
      ElMessage.success(`文档 "${previewDocument.value.filename}" 已导出`)
    } else {
      ElMessage.error('下载失败，请稍后重试')
    }
  } catch (error) {
    console.error('下载文档失败:', error)
    ElMessage.error('下载失败：' + (error.message || '未知错误'))
  }
}

const downloadDocument = async (doc) => {
  try {
    loading.value = true
    const success = await documentService.downloadDocument(doc.id, doc.name)

    if (success) {
      ElMessage.success(`文档 "${doc.name}" 已导出`)
    } else {
      ElMessage.error('下载失败，请稍后重试')
    }
  } catch (error) {
    console.error('下载文档失败:', error)
    ElMessage.error('下载失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const deleteDocument = async (doc) => {
  try {
    // 二次确认
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.name}" 吗？此操作不可撤销。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    loading.value = true
    const success = await documentService.deleteDocument(doc.id)

    if (success) {
      ElMessage.success(`文档 "${doc.name}" 已删除`)

      // 关闭侧边栏如果删除的是当前选中的文档
      if (selectedDocument.value?.id === doc.id) {
        selectedDocument.value = null
        detailVisible.value = false
      }

      // 重新加载文档列表
      await loadDocuments()
    } else {
      ElMessage.error('删除失败，请稍后重试')
    }
  } catch (error) {
    // 用户取消删除
    if (error === 'cancel') {
      return
    }

    console.error('删除文档失败:', error)
    ElMessage.error('删除失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const addTag = () => {
  if (newTag.value.trim() && selectedDocument.value) {
    if (!selectedDocument.value.tags.includes(newTag.value)) {
      selectedDocument.value.tags.push(newTag.value)
    }
    newTag.value = ''
    showTagInput.value = false
  }
}

const removeTag = (tag) => {
  if (selectedDocument.value) {
    const index = selectedDocument.value.tags.indexOf(tag)
    if (index > -1) {
      selectedDocument.value.tags.splice(index, 1)
    }
  }
}

const handleSearch = async () => {
  if (searchQuery.value.trim()) {
    loading.value = true
    try {
      const results = await documentService.searchDocuments(searchQuery.value)
      documents.value =  results.map(doc => {
      // metadata可能是字符串或对象
      let metadata = {}
      if (typeof doc.metadata === 'string') {
        try {
          metadata = JSON.parse(doc.metadata)
        } catch (e) {
          metadata = {}
        }
      } else {
        metadata = doc.metadata || {}
      }

      return {
        id: String(doc.id), // 确保ID是字符串
        name: doc.filename || '未命名文档',
        content: doc.content || '',
        size: metadata.size || 0,
        type: metadata.type || 'txt',
        uploadTime: doc.created_at ? new Date(doc.created_at) : new Date(),
        status: 'indexed', // 假设已索引
        tags: metadata.tags || [],
        pageCount: metadata.pageCount || null,
        chunkIndex: metadata.chunk_index,
        totalChunks: metadata.total_chunks,
        namespace: doc.namespace || 'default', // 添加领域信息
        domainTags: doc.domain_tags || {},
        domainConfidence: doc.domain_confidence || 0
      }
    })
    } catch (error) {
      console.error('搜索失败:', error)
      ElMessage.error('搜索失败，请稍后重试')
    } finally {
      loading.value = false
    }
  } else {
    await loadDocuments()
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const docsData = await documentService.getDocuments()
    console.log('从API获取的原始数据:', docsData)

    // 转换数据格式以适配前端
    documents.value = docsData.map(doc => {
      // metadata可能是字符串或对象
      let metadata = {}
      if (typeof doc.metadata === 'string') {
        try {
          metadata = JSON.parse(doc.metadata)
        } catch (e) {
          metadata = {}
        }
      } else {
        metadata = doc.metadata || {}
      }

      return {
        id: String(doc.id), // 确保ID是字符串
        name: doc.filename || '未命名文档',
        content: doc.content || '',
        size: metadata.size || 0,
        type: metadata.type || 'txt',
        uploadTime: doc.created_at ? new Date(doc.created_at) : new Date(),
        status: 'indexed', // 假设已索引
        tags: metadata.tags || [],
        pageCount: metadata.pageCount || null,
        chunkIndex: metadata.chunk_index,
        totalChunks: metadata.total_chunks,
        namespace: doc.namespace || 'default', // 添加领域信息
        domainTags: doc.domain_tags || {},
        domainConfidence: doc.domain_confidence || 0
      }
    })

    const stats = await documentService.getDocumentStats()
    console.log('原始统计数据:', stats)

    // 将后端返回的 by_type 转换为前端的 byType
    if (stats) {
      documentStats.value = {
        total: stats.total || 0,
        byType: stats.by_type || {}, // 转换下划线为驼峰
        byStatus: stats.by_status || {},
        recent: stats.recent || 0
      }
    } else {
      documentStats.value = {
        total: 0,
        byType: {},
        byStatus: {},
        recent: 0
      }
    }

    console.log('已加载文档:', documents.value.length, '个')
    console.log('处理后的统计数据:', documentStats.value)
    console.log('处理后的文档数据:', documents.value)
  } catch (error) {
    console.error('加载文档失败:', error)
    ElMessage.error('加载文档失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

const handleFileUpload = async (files) => {
  if (!files || files.length === 0) return

  const validFiles = files.filter(file => {
    const isValidType = file.name.toLowerCase().endsWith('.pdf') ||
                      file.name.toLowerCase().endsWith('.txt') ||
                      file.name.toLowerCase().endsWith('.doc') ||
                      file.name.toLowerCase().endsWith('.docx')
    if (!isValidType) {
      ElMessage.warning(`文件 ${file.name} 不是支持的格式，仅支持PDF、TXT、DOC和DOCX文件`)
      return false
    }
    if (file.size > 10 * 1024 * 1024) { // 10MB
      ElMessage.warning(`文件 ${file.name} 超过10MB限制`)
      return false
    }
    return true
  })

  if (validFiles.length === 0) return

  uploadingFiles.value = validFiles

  try {
    // 初始化上传进度
    uploadProgress.value = {}
    for (let i = 0; i < validFiles.length; i++) {
      uploadProgress.value[i] = 0
    }

    // 传递选中的领域
    await documentService.uploadDocuments(validFiles, selectedDomain.value, (progress, loaded, total) => {
      // 找到当前正在上传的文件索引
      let currentFileIndex = 0
      let accumulatedSize = 0
      for (let i = 0; i < validFiles.length; i++) {
        if (loaded <= accumulatedSize + validFiles[i].size) {
          currentFileIndex = i
          break
        }
        accumulatedSize += validFiles[i].size
      }
      uploadProgress.value[currentFileIndex] = progress
    })

    ElMessage.success(`成功上传 ${validFiles.length} 个文档到 ${selectedDomain.value} 领域`)
    await loadDocuments() // 重新加载文档列表

    // 清理上传进度
    uploadingFiles.value = []
    uploadProgress.value = {}

  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败，请稍后重试')
    uploadingFiles.value = []
    uploadProgress.value = {}
  }
}


// 加载知识领域列表
const loadDomains = async () => {
  try {
    domainList.value = await getActiveDomains()
    console.log('已加载知识领域:', domainList.value.length, '个')
  } catch (error) {
    console.error('加载知识领域失败:', error)
    domainList.value = []
  }
}

// 获取领域信息
const getDomainInfo = (namespace) => {
  return domainList.value.find(d => d.namespace === namespace) || {
    display_name: '未分类',
    icon: '📁',
    color: '#999'
  }
}

onMounted(async () => {
  await Promise.all([
    loadDocuments(),
    loadDomains()
  ])
})
</script>

<style lang="scss" scoped>
.documents-page {
  max-width: 100%;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
  background: var(--tech-bg-primary);
}

.page-header {
  margin-bottom: 24px;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;

    .page-title {
      font-size: 28px;
      font-weight: 700;
      color: var(--tech-text-primary);
      margin: 0 0 8px 0;
    }

    .page-subtitle {
      color: var(--tech-text-secondary);
      margin: 0;
    }

    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;

      .search-input {
        width: 300px;
      }

      .upload-btn {
        background: var(--tech-gradient);
        border: none;
        color: white;
      }
    }
  }
}

.documents-layout {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 24px;
  height: calc(100vh - 160px);
}

.sidebar {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  overflow-y: auto;

  .sidebar-section {
    margin-bottom: 32px;

    .sidebar-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--tech-text-primary);
      margin-bottom: 12px;
    }
  }

  .folder-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 4px;

    &:hover {
      background: rgba(0, 240, 255, 0.1);
    }

    &.active {
      background: rgba(0, 240, 255, 0.2);
      color: var(--tech-neon-blue);
    }

    .folder-count {
      margin-left: auto;
      font-size: 12px;
      opacity: 0.7;
    }
  }

  .tag-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 4px;

    &:hover {
      background: rgba(0, 240, 255, 0.1);
    }

    &.active {
      background: rgba(0, 240, 255, 0.2);
    }

    .tag-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    .tag-count {
      margin-left: auto;
      font-size: 12px;
      opacity: 0.7;
    }
  }
}

.main-content {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--tech-glass-border);

  .toolbar-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.documents-container {
  flex: 1;
  overflow-y: auto;

  &.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }

  &.list {
    .document-card {
      margin-bottom: 8px;
    }
  }
}

.document-card {
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 240, 255, 0.2);
    border-color: rgba(0, 240, 255, 0.3);
  }

  &.selected {
    border-color: var(--tech-neon-blue);
    box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.3);
  }

  .document-icon {
    text-align: center;
    margin-bottom: 12px;
    position: relative;

    .document-status {
      position: absolute;
      top: 0;
      right: 0;
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }
  }

  .document-info {
    .document-title {
      font-size: 14px;
      font-weight: 500;
      color: var(--tech-text-primary);
      margin: 0 0 8px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .document-meta {
      font-size: 12px;
      color: var(--tech-text-secondary);
      margin: 0;
    }
  }

  .document-domain {
    margin-top: 8px;
  }

  .document-tags {
    margin-top: 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .document-actions {
    margin-top: 12px;
    display: flex;
    gap: 8px;
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  &:hover .document-actions {
    opacity: 1;
  }

  .document-row {
    display: flex;
    align-items: center;
    gap: 12px;

    .document-icon-small {
      flex-shrink: 0;
    }

    .document-content {
      flex: 1;

      .document-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;

        .document-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--tech-text-primary);
          margin: 0;
        }
      }

      .document-details {
        font-size: 12px;
        color: var(--tech-text-secondary);
        display: flex;
        gap: 8px;
      }
    }

    .document-actions {
      display: flex;
      gap: 4px;
      opacity: 0;
      transition: opacity 0.2s ease;
    }

    &:hover .document-actions {
      opacity: 1;
    }
  }
}

.document-status {
  &.indexed {
    background: #2ed573;
  }

  &.processing {
    background: #ffa502;
    animation: pulse 2s infinite;
  }

  &.error {
    background: #ff4757;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;

  h3 {
    color: var(--tech-text-primary);
    margin: 16px 0 8px 0;
  }

  p {
    color: var(--tech-text-secondary);
    margin: 0 0 24px 0;
  }
}

.detail-panel {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  overflow-y: auto;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--tech-glass-border);

    h3 {
      margin: 0;
      color: var(--tech-text-primary);
    }
  }

  .panel-content {
    .document-preview {
      text-align: center;
      margin-bottom: 24px;

      .document-name {
        color: var(--tech-text-primary);
        margin: 16px 0 8px 0;
      }
    }

    .info-section {
      margin-bottom: 24px;

      h4 {
        font-size: 14px;
        color: var(--tech-text-primary);
        margin-bottom: 12px;
      }

      .info-item {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        font-size: 13px;

        .info-label {
          color: var(--tech-text-secondary);
        }

        .info-value {
          color: var(--tech-text-primary);
        }
      }

      .tag-management {
        .current-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          margin-bottom: 8px;
        }
      }

      .action-buttons {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .content-preview {
        .content-text {
          background: rgba(17, 24, 39, 0.6);
          border: 1px solid var(--tech-glass-border);
          border-radius: 8px;
          padding: 12px;
          font-size: 13px;
          line-height: 1.6;
          color: var(--tech-text-primary);
          max-height: 200px;
          overflow-y: auto;
          white-space: pre-wrap;
        }

        .full-content {
          background: rgba(17, 24, 39, 0.6);
          border: 1px solid var(--tech-glass-border);
          border-radius: 8px;
          padding: 12px;
          font-size: 13px;
          line-height: 1.6;
          color: var(--tech-text-primary);
          max-height: 300px;
          overflow-y: auto;
          white-space: pre-wrap;
          margin-top: 8px;
        }
      }
    }
  }
}

.upload-area {
  border: 2px dashed var(--tech-glass-border);
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  transition: border-color 0.3s ease;

  &:hover {
    border-color: var(--tech-neon-blue);
  }

  p {
    color: var(--tech-text-secondary);
    margin: 16px 0;
  }
}

.selected-files {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--tech-glass-border);

  h4 {
    color: var(--tech-text-primary);
    margin-bottom: 16px;
  }

  .file-list {
    max-height: 200px;
    overflow-y: auto;

    .file-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: rgba(17, 24, 39, 0.6);
      border: 1px solid var(--tech-glass-border);
      border-radius: 8px;
      margin-bottom: 8px;

      .file-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .file-name {
          color: var(--tech-text-primary);
          font-size: 14px;
        }

        .file-size {
          color: var(--tech-text-secondary);
          font-size: 12px;
        }
      }
    }
  }
}

.upload-progress {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--tech-glass-border);

  h4 {
    color: var(--tech-text-primary);
    margin-bottom: 16px;
  }

  .file-progress {
    margin-bottom: 16px;

    .file-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .file-name {
        color: var(--tech-text-primary);
        font-size: 14px;
      }

      .progress-text {
        color: var(--tech-text-secondary);
        font-size: 12px;
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .documents-layout {
    grid-template-columns: 240px 1fr;
  }

  .detail-panel {
    display: none;
  }
}

@media (max-width: 768px) {
  .documents-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .search-input {
    flex: 1;
  }
}

/* 文件选择区域样式 */
.file-selection-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--tech-glass-border);
}

.selection-header h4 {
  margin: 0;
  color: var(--tech-text-primary);
  font-weight: 500;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
}

.file-list .file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(17, 24, 39, 0.6);
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.file-list .file-item:hover {
  background: rgba(17, 24, 39, 0.8);
}

.file-list .file-item .file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-list .file-item .file-info .el-icon {
  color: var(--tech-primary);
  font-size: 16px;
}

.file-list .file-item .file-info .file-name {
  color: var(--tech-text-primary);
  font-size: 14px;
  font-weight: 500;
}

.file-list .file-item .file-info .file-size {
  color: var(--tech-text-secondary);
  font-size: 12px;
}

.file-list .file-item .remove-btn {
  color: var(--tech-text-secondary);
  transition: color 0.2s ease;
}

.file-list .file-item .remove-btn:hover {
  color: var(--tech-danger);
}

.add-more-files {
  display: flex;
  justify-content: center;
  padding-top: 12px;
}

/* 领域选择样式 */
.domain-selection {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
}

.domain-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--tech-text-primary);
}

.domain-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--tech-text-secondary);
  line-height: 1.5;
}

/* 预览对话框样式 */
.preview-loading {
  padding: 20px;
  min-height: 400px;
}

.preview-content {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-header {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .info-label {
    font-size: 12px;
    color: var(--tech-text-secondary);
    font-weight: 500;
  }

  .info-value {
    font-size: 14px;
    color: var(--tech-text-primary);
  }
}

.preview-text {
  background: var(--tech-bg-secondary);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
  padding: 16px;
  max-height: 60vh;
  overflow-y: auto;

  pre {
    margin: 0;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--tech-text-primary);
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  /* 自定义滚动条 */
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
</style>