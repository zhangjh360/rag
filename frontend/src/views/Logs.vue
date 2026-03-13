<template>
  <div class="logs-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="flex items-center space-x-3">
        <div class="text-4xl">📊</div>
        <h1 class="text-3xl font-bold gradient-text">日志管理</h1>
      </div>
      <p class="text-gray-400 mt-2">系统日志查看、搜索和管理</p>
    </div>

    <!-- 统计信息卡片 -->
    <div class="grid grid-cols-4 gap-6 mb-8">
      <LogStatsCard
        v-for="stat in logStats"
        :key="stat.key"
        :icon="stat.icon"
        :title="stat.title"
        :value="stat.value"
        :color="stat.color"
        :trend="stat.trend"
      />
    </div>

    <!-- 操作工具栏 -->
    <div class="tech-card mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- 左侧搜索和筛选 -->
        <div class="flex flex-wrap items-center gap-3">
          <!-- 搜索框 -->
          <div class="relative">
            <el-input
              v-model="searchQuery"
              placeholder="搜索日志内容..."
              class="search-input"
              clearable
              @clear="handleSearchClear"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <div class="text-gray-400">🔍</div>
              </template>
            </el-input>
          </div>

          <!-- 日志类型筛选 -->
          <el-select
            v-model="selectedLogType"
            placeholder="日志类型"
            clearable
            class="log-type-select"
            @change="handleLogTypeChange"
          >
            <el-option label="全部类型" value="" />
            <el-option
              v-for="type in logTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            >
              <span class="flex items-center gap-2">
                <span>{{ logsService.getLogTypeIcon(type.value) }}</span>
                <span>{{ type.label }}</span>
              </span>
            </el-option>
          </el-select>

          <!-- 时间范围筛选 -->
          <el-select
            v-model="timeRange"
            placeholder="时间范围"
            class="time-range-select"
            @change="handleTimeRangeChange"
          >
            <el-option label="最近1小时" :value="1" />
            <el-option label="最近6小时" :value="6" />
            <el-option label="最近24小时" :value="24" />
            <el-option label="最近3天" :value="72" />
            <el-option label="最近7天" :value="168" />
          </el-select>

          <!-- 搜索按钮 -->
          <el-button
            type="primary"
            class="tech-button"
            :loading="searchLoading"
            @click="handleSearch"
          >
            搜索
          </el-button>
        </div>

        <!-- 右侧操作按钮 -->
        <div class="flex items-center gap-3">
          <!-- 刷新按钮 -->
          <el-button
            class="tech-button"
            :loading="refreshing"
            @click="handleRefresh"
          >
            🔄 刷新
          </el-button>

          <!-- 导出按钮 -->
          <el-dropdown @command="handleExportCommand">
            <el-button class="tech-button">
              📤 导出 <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="current">导出当前筛选结果</el-dropdown-item>
                <el-dropdown-item command="all">导出所有日志</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 清理按钮 -->
          <el-button
            type="warning"
            class="tech-button"
            @click="showCleanDialog = true"
          >
            🗑️ 清理日志
          </el-button>

          <!-- 归档按钮 -->
          <el-button
            type="info"
            class="tech-button"
            @click="showArchiveDialog = true"
          >
            📦 归档日志
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="logs-content-wrapper">
      <!-- 左侧日志文件列表 -->
      <div class="logs-sidebar lg:order-1">
        <div class="tech-card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">日志文件</h3>
            <el-button
              size="small"
              text
              @click="toggleFileList"
            >
              {{ showFileList ? '收起' : '展开' }}
            </el-button>
          </div>

          <div v-if="showFileList" class="file-list">
            <div
              v-for="file in logFiles"
              :key="file.path"
              class="file-item"
              :class="{ active: selectedFile === file.path }"
              @click="handleFileSelect(file)"
            >
              <div class="flex items-start gap-3">
                <div class="file-icon">
                  {{ logsService.getLogTypeIcon(file.type) }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="file-name" :title="file.name">
                    {{ file.name }}
                  </div>
                  <div class="file-meta">
                    <span class="file-size">{{ logsService.formatFileSize(file.size) }}</span>
                    <span class="file-type">{{ file.type }}</span>
                  </div>
                  <div class="file-time">
                    {{ logsService.formatTimestamp(file.modified) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="logFiles.length === 0" class="empty-state">
              <div class="text-gray-500">暂无日志文件</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧日志内容显示 -->
      <div class="logs-main lg:order-2">
        <div class="tech-card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">
              {{ selectedFile ? '日志内容' : '搜索结果' }}
            </h3>
            <div class="flex items-center gap-3">
              <!-- 显示行数控制 -->
              <div v-if="selectedFile" class="flex items-center gap-2">
                <span class="text-gray-400 text-sm">显示行数:</span>
                <el-select
                  v-model="displayLines"
                  size="small"
                  class="lines-select"
                  @change="handleLinesChange"
                >
                  <el-option label="50行" :value="50" />
                  <el-option label="100行" :value="100" />
                  <el-option label="200行" :value="200" />
                  <el-option label="500行" :value="500" />
                  <el-option label="全部" :value="0" />
                </el-select>
              </div>

              <!-- 清空显示 -->
              <el-button
                size="small"
                text
                @click="handleClearDisplay"
              >
                清空
              </el-button>
            </div>
          </div>

          <!-- 日志内容显示区域 -->
          <div class="log-content-container">
            <div v-if="logLoading" class="loading-container">
              <el-loading-spinner />
              <p class="text-gray-400 mt-3">正在加载日志内容...</p>
            </div>

            <div v-else-if="logContent.length === 0" class="empty-state">
              <div class="text-gray-500">
                {{ searchQuery ? '未找到匹配的日志内容' : '请选择日志文件或进行搜索' }}
              </div>
            </div>

            <div v-else class="log-content">
              <div
                v-for="(line, index) in logContent"
                :key="index"
                class="log-line"
                :class="{ 'highlight': shouldHighlightLine(line) }"
                @click="handleLineClick(line, index)"
              >
                <div class="line-number">{{ getLineNumber(line, index) }}</div>
                <div class="line-content">
                  <span v-html="highlightSearchTerm(line.content)"></span>
                </div>
                <div v-if="line.timestamp" class="line-time">
                  {{ logsService.formatTimestamp(line.timestamp) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 分页控制 -->
          <div v-if="paginatedResults.total > 0" class="pagination-container">
            <el-pagination
              v-model:current-page="paginatedResults.page"
              v-model:page-size="paginatedResults.pageSize"
              :total="paginatedResults.total"
              :page-sizes="[20, 50, 100, 200]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 清理日志对话框 -->
    <el-dialog
      v-model="showCleanDialog"
      title="清理旧日志"
      width="500px"
      class="tech-dialog"
    >
      <div class="space-y-4">
        <div class="text-gray-300">
          选择要保留的日志天数，超过天数的日志将被永久删除。
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            保留天数
          </label>
          <el-input-number
            v-model="cleanDays"
            :min="1"
            :max="365"
            class="w-full"
          />
          <div class="text-xs text-gray-500 mt-1">
            将删除 {{ cleanDays }} 天前的所有日志文件
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="showCleanDialog = false">取消</el-button>
          <el-button
            type="warning"
            :loading="cleanLoading"
            @click="handleCleanLogs"
          >
            确认清理
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 归档日志对话框 -->
    <el-dialog
      v-model="showArchiveDialog"
      title="归档日志"
      width="500px"
      class="tech-dialog"
    >
      <div class="space-y-4">
        <div class="text-gray-300">
          选择要归档的日志天数，这些日志将被压缩归档保存。
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            归档天数前的日志
          </label>
          <el-input-number
            v-model="archiveDays"
            :min="1"
            :max="30"
            class="w-full"
          />
          <div class="text-xs text-gray-500 mt-1">
            将归档 {{ archiveDays }} 天前的所有日志文件
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="showArchiveDialog = false">取消</el-button>
          <el-button
            type="info"
            :loading="archiveLoading"
            @click="handleArchiveLogs"
          >
            确认归档
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { logsService } from '@/services/logsService'
import LogStatsCard from '@/components/logs/LogStatsCard.vue'

// 响应式数据
const searchQuery = ref('')
const selectedLogType = ref('')
const timeRange = ref(24)
const selectedFile = ref('')
const displayLines = ref(100)
const showFileList = ref(true)

// 加载状态
const refreshing = ref(false)
const searchLoading = ref(false)
const logLoading = ref(false)
const cleanLoading = ref(false)
const archiveLoading = ref(false)

// 对话框状态
const showCleanDialog = ref(false)
const showArchiveDialog = ref(false)
const cleanDays = ref(30)
const archiveDays = ref(7)

// 数据状态
const logFiles = ref([])
const logContent = ref([])
const logStats = ref([])
const searchResults = ref([])

// 分页状态
const paginatedResults = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

// 日志类型选项
const logTypes = [
  { label: '应用日志', value: 'app' },
  { label: '错误日志', value: 'error' },
  { label: '访问日志', value: 'access' },
  { label: '系统日志', value: 'system' },
  { label: '数据库日志', value: 'database' }
]

// 计算属性
const hasSearchContent = computed(() => {
  return searchQuery.value.trim() !== ''
})

// 生命周期
onMounted(() => {
  loadData()
})

// 方法
const loadData = async () => {
  await Promise.all([
    loadLogFiles(),
    loadLogStatistics()
  ])
}

const loadLogFiles = async () => {
  try {
    const files = await logsService.getLogFiles(selectedLogType.value || null)
    logFiles.value = files.sort((a, b) => new Date(b.modified) - new Date(a.modified))
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const loadLogStatistics = async () => {
  try {
    const stats = await logsService.getLogStatistics()

    // 转换为统计卡片格式
    logStats.value = [
      {
        key: 'totalFiles',
        icon: '📄',
        title: '日志文件',
        value: stats.total_files,
        color: 'blue',
        trend: 'stable'
      },
      {
        key: 'totalSize',
        icon: '💾',
        title: '总大小',
        value: logsService.formatFileSize(stats.total_size_mb * 1024 * 1024),
        color: 'green',
        trend: 'up'
      },
      {
        key: 'oldestFile',
        icon: '📅',
        title: '最早日志',
        value: stats.oldest_file ? logsService.formatTimestamp(stats.oldest_file.modified) : '-',
        color: 'yellow',
        trend: 'stable'
      },
      {
        key: 'newestFile',
        icon: '🆕',
        title: '最新日志',
        value: stats.newest_file ? logsService.formatTimestamp(stats.newest_file.modified) : '-',
        color: 'purple',
        trend: 'up'
      }
    ]
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleFileSelect = async (file) => {
  selectedFile.value = file.path
  searchQuery.value = '' // 清空搜索
  await loadLogContent()
}

const loadLogContent = async () => {
  if (!selectedFile.value) return

  logLoading.value = true
  try {
    const result = await logsService.readLogFile(selectedFile.value, displayLines.value)
    logContent.value = result.content.map((line, index) => ({
      content: line,
      line: index + 1,
      file: selectedFile.value
    }))
  } catch (error) {
    ElMessage.error(error.message)
    logContent.value = []
  } finally {
    logLoading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searchLoading.value = true
  try {
    const results = await logsService.searchLogs(
      searchQuery.value,
      selectedLogType.value || null,
      timeRange.value
    )

    searchResults.value = results.map(result => ({
      content: result.content,
      line: result.line,
      file: result.file,
      timestamp: result.timestamp,
      type: result.type
    }))

    logContent.value = searchResults.value
    selectedFile.value = '' // 清空文件选择，显示搜索结果
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    searchLoading.value = false
  }
}

const handleSearchClear = () => {
  searchQuery.value = ''
  logContent.value = []
  selectedFile.value = ''
}

const handleLogTypeChange = () => {
  loadLogFiles()
}

const handleTimeRangeChange = () => {
  if (searchQuery.value) {
    handleSearch()
  }
}

const handleLinesChange = () => {
  if (selectedFile.value) {
    loadLogContent()
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    await loadData()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

const handleClearDisplay = () => {
  logContent.value = []
  selectedFile.value = ''
  searchQuery.value = ''
}

const handleExportCommand = async (command) => {
  try {
    let outputFile = `logs_export_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.txt`

    if (command === 'current') {
      if (selectedFile.value) {
        outputFile = `export_${selectedFile.value.split('/').pop()}`
      } else if (searchQuery.value) {
        outputFile = `search_results_${searchQuery.value.slice(0, 20)}_${new Date().toISOString().slice(0, 19)}.txt`
      }
    }

    const result = await logsService.exportLogs(
      outputFile,
      selectedLogType.value || null,
      command === 'current' ? timeRange.value : 168 // 7天
    )

    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleCleanLogs = async () => {
  try {
    const result = await logsService.cleanOldLogs(cleanDays.value)
    ElMessage.success(`成功清理 ${result.cleaned_files} 个日志文件，释放 ${result.freed_space_mb} MB 空间`)
    showCleanDialog.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleArchiveLogs = async () => {
  try {
    const result = await logsService.archiveLogs(archiveDays.value)
    ElMessage.success(`成功归档 ${result.cleaned_files} 个日志文件，大小 ${result.freed_space_mb} MB`)
    showArchiveDialog.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const toggleFileList = () => {
  showFileList.value = !showFileList.value
}

const getLineNumber = (line, index) => {
  return line.line || index + 1
}

const shouldHighlightLine = (line) => {
  return searchQuery.value && line.content.toLowerCase().includes(searchQuery.value.toLowerCase())
}

const highlightSearchTerm = (content) => {
  if (!searchQuery.value) return content

  const regex = new RegExp(`(${searchQuery.value})`, 'gi')
  return content.replace(regex, '<mark class="search-highlight">$1</mark>')
}

const handleLineClick = (line, index) => {
  // 可以实现复制行号等功能
  console.log('Line clicked:', line, index)
}

const handlePageChange = (page) => {
  paginatedResults.page = page
  // 实现分页逻辑
}

const handlePageSizeChange = (size) => {
  paginatedResults.pageSize = size
  paginatedResults.page = 1
  // 实现分页逻辑
}
</script>

<style scoped>
.logs-page {
  padding: 2rem;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 2rem;
}

/* 统计卡片 */
.log-stats-card {
  transition: all 0.3s ease;
}

.log-stats-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 40px rgba(0, 212, 255, 0.3);
}

/* 搜索和筛选 */
.search-input {
  width: 300px;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1);
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2);
}

.log-type-select, .time-range-select, .lines-select {
  width: 150px;
}

.log-type-select :deep(.el-select__wrapper),
.time-range-select :deep(.el-select__wrapper),
.lines-select :deep(.el-select__wrapper) {
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.3);
}

/* 文件列表 */
.file-list {
  max-height: 500px;
  overflow-y: auto;
}

.file-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.file-item:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateX(5px);
}

.file-item.active {
  background: rgba(0, 212, 255, 0.15);
  border-color: var(--tech-neon-blue);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.file-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.file-name {
  font-weight: 500;
  color: white;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.file-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* 日志内容区域 */
.log-content-container {
  max-height: 600px;
  overflow-y: auto !important;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 16px;
  min-height: 0;
}

/* 确保滚动条样式 */
.log-content-container::-webkit-scrollbar {
  width: 10px;
}

.log-content-container::-webkit-scrollbar-track {
  background: rgba(0, 212, 255, 0.1);
  border-radius: 5px;
}

.log-content-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #00d4ff, #a855f7);
  border-radius: 5px;
  transition: all 0.3s ease;
}

.log-content-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #a855f7, #00d4ff);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.log-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
}

.log-line {
  display: flex;
  align-items: flex-start;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.log-line:hover {
  background: rgba(0, 212, 255, 0.1);
}

.log-line.highlight {
  background: rgba(0, 212, 255, 0.2);
  border-left: 3px solid var(--tech-neon-blue);
}

.line-number {
  width: 60px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  text-align: right;
  padding-right: 16px;
  flex-shrink: 0;
}

.line-content {
  flex: 1;
  color: rgba(255, 255, 255, 0.9);
  white-space: pre-wrap;
  word-break: break-all;
}

.line-time {
  width: 160px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  text-align: right;
  padding-left: 16px;
  flex-shrink: 0;
}

/* 搜索高亮 */
:deep(.search-highlight) {
  background: rgba(251, 191, 36, 0.3);
  color: #fbbf24;
  padding: 2px 4px;
  border-radius: 2px;
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.pagination-container :deep(.el-pagination) {
  background: transparent;
}

.pagination-container :deep(.el-pagination .el-select__wrapper) {
  background: rgba(17, 24, 39, 0.6);
  border-color: rgba(0, 212, 255, 0.3);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: rgba(255, 255, 255, 0.5);
}

/* 对话框样式 */
:deep(.tech-dialog .el-dialog) {
  background: rgba(17, 24, 39, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

:deep(.tech-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

:deep(.tech-dialog .el-dialog__title) {
  color: white;
}

/* 滚动条样式 */
.file-list::-webkit-scrollbar,
.log-content-container::-webkit-scrollbar {
  width: 8px;
}

.file-list::-webkit-scrollbar-track,
.log-content-container::-webkit-scrollbar-track {
  background: rgba(0, 212, 255, 0.1);
  border-radius: 4px;
}

.file-list::-webkit-scrollbar-thumb,
.log-content-container::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.5);
  border-radius: 4px;
}

.file-list::-webkit-scrollbar-thumb:hover,
.log-content-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.7);
}
</style>