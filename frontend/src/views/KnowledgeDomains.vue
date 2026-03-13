<template>
  <div class="knowledge-domains-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <div class="domains-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon class="title-icon"><FolderOpened /></el-icon>
            知识领域管理
          </h1>
          <p class="page-subtitle">管理多领域知识库,实现知识分类和精准检索</p>
        </div>
        <div class="header-right">
          <!-- <el-dropdown @command="handleBulkAction" class="tech-dropdown">
            <el-button class="tech-button">
              批量操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu class="tech-dropdown-menu">
                <el-dropdown-item command="export" class="dropdown-item">
                  <el-icon><Download /></el-icon>导出数据
                </el-dropdown-item>
                <el-dropdown-item command="import" class="dropdown-item">
                  <el-icon><Upload /></el-icon>导入数据
                </el-dropdown-item>
                <el-dropdown-item command="priority" :disabled="selectedDomains.length === 0" class="dropdown-item">
                  <el-icon><Sort /></el-icon>批量更新优先级
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown> -->
          <el-button type="primary" @click="showCreateDialog = true" class="tech-button-primary">
            <el-icon><Plus /></el-icon>
            创建领域
          </el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="tech-stat-card">
          <div class="stat-icon icon-blue">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalDomains }}</div>
            <div class="stat-label">总领域数</div>
          </div>
        </div>
        <div class="tech-stat-card">
          <div class="stat-icon icon-green">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeDomains }}</div>
            <div class="stat-label">启用领域</div>
          </div>
        </div>
        <div class="tech-stat-card">
          <div class="stat-icon icon-purple">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalDocuments }}</div>
            <div class="stat-label">总文档数</div>
          </div>
        </div>
      </div>

    <!-- 领域列表 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">
            <el-icon class="mr-2"><FolderOpened /></el-icon>
            知识领域列表
          </h2>
        </div>
        <div class="card-body">
          <!-- 工具栏 -->
          <div class="toolbar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索领域..."
              :prefix-icon="Search"
              class="tech-input"
              style="width: 300px"
              clearable
              @input="handleSearch"
            />
            <div class="toolbar-actions">
              <el-switch
                v-model="showInactive"
                active-text="显示未启用"
                @change="loadDomains"
                class="tech-switch"
              />
            </div>
          </div>

        <!-- 表格 -->
        <el-table
          v-loading="loading"
          :data="filteredDomains"
          style="width: 100%"
          :default-sort="{ prop: 'priority', order: 'descending' }"
          @selection-change="handleSelectionChange"
        >
          <!-- 选择列 -->
          <el-table-column type="selection" width="55" />
          <el-table-column prop="namespace" label="命名空间" width="180">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.namespace }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="领域信息" min-width="250">
            <template #default="{ row }">
              <div class="domain-info">
                <div class="domain-name">
                  <el-icon v-if="row.icon" :size="18" :style="{ color: row.color }">
                    <component :is="getIcon(row.icon)" />
                  </el-icon>
                  <span>{{ row.display_name }}</span>
                </div>
                <div class="domain-desc">{{ row.description }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="keywords" label="关键词" width="200">
            <template #default="{ row }">
              <el-tag
                v-for="(keyword, index) in row.keywords.slice(0, 3)"
                :key="index"
                size="small"
                type="info"
                class="keyword-tag"
              >
                {{ keyword }}
              </el-tag>
              <el-tag v-if="row.keywords.length > 3" size="small" type="info">
                +{{ row.keywords.length - 3 }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="统计" width="150" align="center">
            <template #default="{ row }">
              <div class="domain-stats">
                <div class="stat-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ row.document_count || 0 }}</span>
                </div>
                <div class="stat-item">
                  <el-icon><Files /></el-icon>
                  <span>{{ row.chunk_count || 0 }}</span>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="priority" label="优先级" width="100" align="center" sortable />

          <el-table-column prop="is_active" label="状态" width="100" align="center">
            <template #default="{ row }">
              <div
                class="status-indicator"
                :class="{ 'status-active': row.is_active, 'status-inactive': !row.is_active }"
                @click="handleToggleActive(row)"
                title="点击切换状态"
              >
                <span class="status-text">{{ row.is_active ? '启用' : '禁用' }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                text
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                type="info"
                size="small"
                text
                @click="handleViewStats(row)"
              >
                统计
              </el-button>
              <el-button
                v-if="row.namespace !== 'default'"
                type="danger"
                size="small"
                text
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </div>
    </div>
  </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingDomain ? '编辑领域' : '创建领域'"
      width="600px"
    >
      <el-form
        ref="domainFormRef"
        :model="domainForm"
        :rules="domainFormRules"
        label-width="100px"
      >
        <el-form-item label="命名空间" prop="namespace">
          <el-input
            v-model="domainForm.namespace"
            placeholder="例如: technical_docs"
            :disabled="!!editingDomain"
          />
          <div class="form-tip">只能包含小写字母、数字、下划线和连字符</div>
        </el-form-item>

        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="domainForm.display_name" placeholder="例如: 技术文档" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="domainForm.description"
            type="textarea"
            :rows="3"
            placeholder="领域的详细描述..."
          />
        </el-form-item>

        <el-form-item label="关键词">
          <el-select
            v-model="domainForm.keywords"
            multiple
            filterable
            allow-create
            placeholder="输入关键词后按回车"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="图标">
          <el-select v-model="domainForm.icon" placeholder="选择图标">
            <el-option label="文件夹" value="folder">
              <el-icon><Folder /></el-icon> 文件夹
            </el-option>
            <el-option label="文档" value="document">
              <el-icon><Document /></el-icon> 文档
            </el-option>
            <el-option label="代码" value="code">
              <el-icon><Document /></el-icon> 代码
            </el-option>
            <el-option label="工具" value="tools">
              <el-icon><Tools /></el-icon> 工具
            </el-option>
            <el-option label="支持" value="support">
              <el-icon><Tools /></el-icon> 支持
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="主题色">
          <el-color-picker v-model="domainForm.color" />
          <span class="color-preview" :style="{ backgroundColor: domainForm.color }">
            {{ domainForm.color }}
          </span>
        </el-form-item>

        <el-form-item label="优先级">
          <el-input-number v-model="domainForm.priority" :min="0" :max="100" />
          <div class="form-tip">数值越大优先级越高</div>
        </el-form-item>

        <el-form-item label="启用">
          <el-switch v-model="domainForm.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingDomain ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 统计详情对话框 -->
    <el-dialog v-model="showStatsDialog" title="领域统计" width="500px">
      <div v-if="currentStats" class="stats-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="命名空间">
            {{ currentStats.namespace }}
          </el-descriptions-item>
          <el-descriptions-item label="文档数量">
            <el-tag type="primary">{{ currentStats.document_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分块数量">
            <el-tag type="success">{{ currentStats.chunk_count }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="平均置信度">
            <el-progress
              :percentage="currentStats.avg_confidence * 100"
              :color="getConfidenceColor(currentStats.avg_confidence)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="最近7天上传">
            <el-tag type="warning">{{ currentStats.recent_uploads }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 批量更新优先级对话框 -->
    <el-dialog v-model="showPriorityDialog" title="批量更新优先级" width="400px">
      <el-form>
        <el-form-item label="设置优先级">
          <el-input-number
            v-model="batchPriority"
            :min="0"
            :max="100"
            style="width: 100%"
            placeholder="输入新的优先级"
          />
          <div class="form-tip">将为选中的 {{ selectedDomains.length }} 个领域设置相同的优先级</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPriorityDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchUpdatePriority" :loading="submitting">
          确认更新
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入数据对话框 -->
    <el-dialog v-model="showImportDialog" title="导入领域数据" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".json,.csv"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JSON 和 CSV 格式文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="submitting" :disabled="!importFile">
          导入
        </el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  FolderOpened,
  CircleCheck,
  Document,
  Files,
  Folder,
  Tools,
  ArrowDown,
  UploadFilled,
  Download,
  Upload,
  Sort
} from '@element-plus/icons-vue'
import {
  getAllDomains,
  createDomain,
  updateDomain,
  deleteDomain,
  getDomainStats,
  batchUpdatePriorities,
  exportDomains,
  importDomains
} from '@/services/knowledgeDomains'

// 状态
const loading = ref(false)
const submitting = ref(false)
const domains = ref([])
const selectedDomains = ref([])
const searchKeyword = ref('')
const showInactive = ref(false)
const showCreateDialog = ref(false)
const showStatsDialog = ref(false)
const showPriorityDialog = ref(false)
const showImportDialog = ref(false)
const editingDomain = ref(null)
const currentStats = ref(null)
const batchPriority = ref(0)
const importFile = ref(null)
const uploadRef = ref(null)

// 表单
const domainFormRef = ref(null)
const domainForm = ref({
  namespace: '',
  display_name: '',
  description: '',
  keywords: [],
  icon: 'folder',
  color: '#4A90E2',
  priority: 0,
  is_active: true,
  permissions: {},
  metadata: {}
})

// 表单验证规则
const domainFormRules = {
  namespace: [
    { required: true, message: '请输入命名空间', trigger: 'blur' },
    { pattern: /^[a-z0-9_-]+$/, message: '只能包含小写字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ]
}

// 统计数据
const totalDomains = computed(() => domains.value.length)
const activeDomains = computed(() => domains.value.filter(d => d.is_active).length)
const totalDocuments = computed(() => {
  return domains.value.reduce((sum, d) => sum + (d.document_count || 0), 0)
})

// 过滤后的领域列表
const filteredDomains = computed(() => {
  if (!searchKeyword.value) return domains.value
  const keyword = searchKeyword.value.toLowerCase()
  return domains.value.filter(d =>
    d.namespace.toLowerCase().includes(keyword) ||
    d.display_name.toLowerCase().includes(keyword) ||
    (d.description && d.description.toLowerCase().includes(keyword))
  )
})

// 获取图标组件
const getIcon = (iconName) => {
  const iconMap = {
    'folder': Folder,
    'document': Document,
    'code': Document,
    'tools': Tools,
    'support': Tools
  }
  return iconMap[iconName] || Folder
}

// 获取置信度颜色
const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 加载领域列表
const loadDomains = async () => {
  loading.value = true
  try {
    const response = await getAllDomains({
      include_inactive: showInactive.value,
      with_stats: true
    })
    domains.value = response.domains || []
  } catch (error) {
    ElMessage.error('加载领域列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  // 搜索由 computed 自动处理
}

// 切换启用状态
const handleToggleActive = async (domain) => {
  // 先切换本地状态
  const newStatus = !domain.is_active
  const oldStatus = domain.is_active
  domain.is_active = newStatus

  try {
    await updateDomain(domain.namespace, {
      is_active: newStatus
    })
    ElMessage.success(`状态已更新为: ${newStatus ? '启用' : '禁用'}`)
  } catch (error) {
    domain.is_active = oldStatus // 回滚
    ElMessage.error('更新失败')
  }
}

// 编辑领域
const handleEdit = (domain) => {
  editingDomain.value = domain
  domainForm.value = {
    namespace: domain.namespace,
    display_name: domain.display_name,
    description: domain.description || '',
    keywords: domain.keywords || [],
    icon: domain.icon || 'folder',
    color: domain.color || '#4A90E2',
    priority: domain.priority || 0,
    is_active: domain.is_active,
    permissions: domain.permissions || {},
    metadata: domain.metadata || {}
  }
  showCreateDialog.value = true
}

// 查看统计
const handleViewStats = async (domain) => {
  try {
    currentStats.value = await getDomainStats(domain.namespace)
    showStatsDialog.value = true
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
}

// 删除领域
const handleDelete = async (domain) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除领域 "${domain.display_name}" 吗?如果有关联文档将无法删除。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteDomain(domain.namespace)
    ElMessage.success('删除成功')
    loadDomains()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!domainFormRef.value) return

  await domainFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingDomain.value) {
        // 编辑
        const { namespace, ...updateData } = domainForm.value
        await updateDomain(namespace, updateData)
        ElMessage.success('更新成功')
      } else {
        // 创建
        await createDomain(domainForm.value)
        ElMessage.success('创建成功')
      }

      showCreateDialog.value = false
      editingDomain.value = null
      resetForm()
      loadDomains()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  domainForm.value = {
    namespace: '',
    display_name: '',
    description: '',
    keywords: [],
    icon: 'folder',
    color: '#4A90E2',
    priority: 0,
    is_active: true,
    permissions: {},
    metadata: {}
  }
  editingDomain.value = null
}

// 处理表格选择变化
const handleSelectionChange = (selection) => {
  selectedDomains.value = selection
}

// 处理批量操作
const handleBulkAction = async (command) => {
  switch (command) {
    case 'export':
      await handleExport()
      break
    case 'import':
      showImportDialog.value = true
      break
    case 'priority':
      showPriorityDialog.value = true
      break
  }
}

// 导出数据
const handleExport = async () => {
  try {
    const data = await exportDomains(null, 'json')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `knowledge-domains-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 处理文件变化
const handleFileChange = (file) => {
  importFile.value = file.raw
}

// 处理导入
const handleImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择要导入的文件')
    return
  }

  const formData = new FormData()
  formData.append('file', importFile.value)

  submitting.value = true
  try {
    const result = await importDomains(formData)
    ElMessage.success(`导入成功，共导入 ${result.imported_count || 0} 条记录`)
    showImportDialog.value = false
    importFile.value = null
    if (uploadRef.value) {
      uploadRef.value.clearFiles()
    }
    loadDomains()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    submitting.value = false
  }
}

// 批量更新优先级
const handleBatchUpdatePriority = async () => {
  if (selectedDomains.value.length === 0) {
    ElMessage.warning('请先选择要更新的领域')
    return
  }

  submitting.value = true
  try {
    const domainList = selectedDomains.value.map(domain => ({
      namespace: domain.namespace,
      priority: batchPriority.value
    }))
    await batchUpdatePriorities(domainList)
    ElMessage.success('批量更新成功')
    showPriorityDialog.value = false
    selectedDomains.value = []
    loadDomains()
  } catch (error) {
    ElMessage.error('批量更新失败')
  } finally {
    submitting.value = false
  }
}

// 挂载时加载
onMounted(() => {
  loadDomains()
})
</script>

<style lang="scss" scoped>
.knowledge-domains-container {
  position: relative;
  padding: 24px;
  min-height: calc(100vh - 64px - 48px);
  overflow-y: auto;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 212, 255, 0.3);
    border-radius: 4px;

    &:hover {
      background: rgba(0, 212, 255, 0.5);
    }
  }
}

.tech-grid-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: -1;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.domains-content {
  position: relative;
  z-index: 1;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;

  .header-left {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 2rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
      color: #00d4ff;
      text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);

      .title-icon {
        font-size: 2rem;
      }
    }

    .page-subtitle {
      color: #9ca3af;
      margin: 0;
      font-size: 0.875rem;
    }
  }

  .header-right {
    display: flex;
    gap: 12px;
  }
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.tech-stat-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(0, 212, 255, 0.4);
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;

    &.icon-blue {
      background: rgba(0, 212, 255, 0.1);
      color: #00d4ff;
      border: 1px solid rgba(0, 212, 255, 0.3);
    }

    &.icon-green {
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }

    &.icon-purple {
      background: rgba(168, 85, 247, 0.1);
      color: #a855f7;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }
  }

  .stat-content {
    .stat-value {
      font-size: 2rem;
      font-weight: 600;
      color: #f3f4f6;
      line-height: 1;
    }

    .stat-label {
      font-size: 0.875rem;
      color: #9ca3af;
      margin-top: 0.5rem;
    }
  }
}

.tech-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  margin-bottom: 2rem;

  .card-header {
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    h2 {
      display: flex;
      align-items: center;
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
    }
  }

  .card-body {
    padding: 1.5rem;

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;

      .toolbar-actions {
        display: flex;
        gap: 1rem;
        align-items: center;
      }
    }

    .tech-input {
      :deep(.el-input__wrapper) {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        box-shadow: none;

        &:hover, &.is-focus {
          border-color: rgba(0, 212, 255, 0.6);
          background: rgba(255, 255, 255, 0.08);
        }
      }

      :deep(.el-input__inner) {
        color: #f3f4f6;
        &::placeholder {
          color: #9ca3af;
        }
      }
    }

    .tech-switch {
      :deep(.el-switch__label) {
        color: #9ca3af;
      }
    }
  }
}

.tech-button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.3);
  color: #00d4ff;

  &:hover {
    background: rgba(0, 212, 255, 0.1);
    border-color: #00d4ff;
    color: #00d4ff;
  }
}

.tech-button-primary {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00d4ff;

  &:hover {
    background: rgba(0, 212, 255, 0.2);
    border-color: #00d4ff;
    color: #00d4ff;
  }
}

.tech-dropdown-menu {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(0, 212, 255, 0.3);
  backdrop-filter: blur(10px);

  .dropdown-item {
    color: #9ca3af;
    display: flex;
    align-items: center;
    gap: 8px;

    &:hover {
      background: rgba(0, 212, 255, 0.1);
      color: #00d4ff;
    }

    .el-icon {
      margin-right: 8px;
    }
  }
}

.domain-info {
  .domain-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    margin-bottom: 4px;
    color: #f3f4f6;
  }

  .domain-desc {
    font-size: 0.75rem;
    color: #9ca3af;
  }
}

.keyword-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.domain-stats {
  display: flex;
  gap: 12px;
  justify-content: center;

  .stat-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.875rem;
    color: #9ca3af;
  }
}

.form-tip {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 4px;
}

.color-preview {
  display: inline-block;
  margin-left: 12px;
  padding: 4px 12px;
  border-radius: 4px;
  color: white;
  font-size: 0.75rem;
}

.stats-detail {
  margin-top: 20px;
}

.el-upload {
  .el-upload-dragger {
    background: rgba(255, 255, 255, 0.05);
    border: 2px dashed rgba(0, 212, 255, 0.3);
    border-radius: 8px;

    &:hover {
      border-color: rgba(0, 212, 255, 0.6);
      background: rgba(255, 255, 255, 0.08);
    }

    .el-upload__text {
      color: #9ca3af;
    }

    .el-icon-upload {
      color: #00d4ff;
      font-size: 48px;
      margin-bottom: 16px;
    }
  }

  .el-upload__tip {
    color: #9ca3af;
    font-size: 0.75rem;
    margin-top: 8px;
  }
}

// 表格样式
:deep(.el-table) {
  background: transparent;

  .el-table__header-wrapper {
    th {
      background: rgba(255, 255, 255, 0.05);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      color: #f3f4f6;
      font-weight: 600;
    }
  }

  .el-table__body-wrapper {
    tr {
      background: transparent;

      &:hover td {
        background: rgba(255, 255, 255, 0.05);
      }
    }

    td {
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #9ca3af;
    }
  }

  .el-table__empty-block {
    background: transparent;
    color: #9ca3af;
  }
}

// 状态指示器样式
.status-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  font-weight: 500;
  font-size: 10px;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
  }

  &.status-active {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(16, 185, 129, 0.1));
    border: 2px solid #10b981;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);

    .status-text {
      color: #10b981;
      text-shadow: 0 0 3px rgba(16, 185, 129, 0.6);
    }
  }

  &.status-inactive {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1));
    border: 2px solid #ef4444;
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);

    .status-text {
      color: #ef4444;
      text-shadow: 0 0 3px rgba(239, 68, 68, 0.6);
    }
  }

  .status-text {
    font-weight: 600;
    user-select: none;
  }
}

// 对话框样式
:deep(.el-dialog) {
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(0, 212, 255, 0.3);
  backdrop-filter: blur(20px);

  .el-dialog__header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .el-dialog__title {
      color: #f3f4f6;
    }
  }

  .el-dialog__body {
    color: #9ca3af;
  }

  .el-form-item__label {
    color: #9ca3af;
  }

  .el-input__wrapper,
  .el-textarea__inner,
  .el-select__wrapper {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(0, 212, 255, 0.3);

    &:hover, &.is-focus {
      border-color: rgba(0, 212, 255, 0.6);
    }
  }

  .el-input__inner,
  .el-textarea__inner {
    color: #f3f4f6;

    &::placeholder {
      color: #6b7280;
    }
  }
}
</style>
