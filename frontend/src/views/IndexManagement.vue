<template>
  <div class="index-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div>
          <h1 class="page-title">🔄 文档索引管理</h1>
          <p class="page-subtitle">智能增量索引 · 实时任务监控 · 性能分析</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="handleAutoUpdate" :loading="updating">
            <el-icon><Refresh /></el-icon>
            一键自动更新
          </el-button>
          <el-button @click="handleDetectChanges" :loading="detecting">
            <el-icon><Search /></el-icon>
            检测变更
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计面板 -->
    <div class="stats-section">
      <index-stats ref="indexStatsRef" :namespace="selectedNamespace" auto-refresh />
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <el-tabs v-model="activeTab" class="index-tabs">
        <!-- Tab 1: 变更检测 -->
        <el-tab-pane label="变更检测" name="changes">
          <div class="changes-panel">
            <!-- 检测配置 -->
            <div class="detect-config">
              <el-form :model="detectForm" inline>
                <el-form-item label="知识领域">
                  <domain-selector
                    v-model="detectForm.namespace"
                    placeholder="选择领域"
                    clearable
                    style="width: 200px;"
                  />
                </el-form-item>
                <el-form-item label="检测范围">
                  <el-select v-model="detectForm.sinceHours" style="width: 150px;">
                    <el-option label="最近1小时" :value="1" />
                    <el-option label="最近6小时" :value="6" />
                    <el-option label="最近24小时" :value="24" />
                    <el-option label="最近7天" :value="168" />
                    <el-option label="最近30天" :value="720" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-checkbox v-model="detectForm.forceCheck">强制检查</el-checkbox>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="handleDetectChanges" :loading="detecting">
                    开始检测
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 变更结果 -->
            <div v-if="changeResult" class="change-result">
              <div class="result-summary">
                <div class="summary-item">
                  <h4>新增文档</h4>
                  <p class="count new">{{ changeResult.new_documents?.length || 0 }}</p>
                </div>
                <div class="summary-item">
                  <h4>已修改</h4>
                  <p class="count modified">{{ changeResult.modified_documents?.length || 0 }}</p>
                </div>
                <div class="summary-item">
                  <h4>未变更</h4>
                  <p class="count unchanged">{{ changeResult.unchanged_count || 0 }}</p>
                </div>
                <div class="summary-item">
                  <h4>需要处理</h4>
                  <p class="count total">{{ (changeResult.new_documents?.length || 0) + (changeResult.modified_documents?.length || 0) }}</p>
                </div>
              </div>

              <!-- 变更文档列表 -->
              <div v-if="changedDocuments.length > 0" class="changed-documents">
                <h4>需要索引的文档</h4>
                <el-table :data="changedDocuments" style="width: 100%" max-height="400">
                  <el-table-column type="selection" width="55" />
                  <el-table-column prop="filename" label="文件名" min-width="200" />
                  <el-table-column prop="change_type" label="变更类型" width="100">
                    <template #default="{ row }">
                      <el-tag :type="row.change_type === 'new' ? 'success' : 'warning'" size="small">
                        {{ row.change_type === 'new' ? '新增' : '修改' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="namespace" label="领域" width="120" />
                  <el-table-column label="操作" width="150" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" size="small" @click="handleIndexDocument(row.id)">
                        索引
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <div class="batch-actions" style="margin-top: 16px;">
                  <el-button type="primary" @click="handleBatchIndex">
                    批量索引全部
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 任务监控 -->
        <el-tab-pane label="任务监控" name="tasks">
          <div class="tasks-panel">
            <!-- 活跃任务 -->
            <div class="active-tasks" v-if="activeTasks.length > 0">
              <h3>🔄 进行中的任务</h3>
              <div class="task-list">
                <task-monitor
                  v-for="task in activeTasks"
                  :key="task.task_id"
                  :task-id="task.task_id"
                  :task-title="task.description || '文档索引任务'"
                  :auto-connect="true"
                  :show-actions="true"
                  @completed="handleTaskCompleted"
                  @failed="handleTaskFailed"
                  @close="removeActiveTask(task.task_id)"
                  style="margin-bottom: 16px;"
                />
              </div>
            </div>

            <!-- 任务历史 -->
            <div class="task-history">
              <div class="history-header">
                <h3>📋 任务历史</h3>
                <div class="history-filters">
                  <el-select v-model="taskFilter" size="small" style="width: 120px;" @change="loadTaskList">
                    <el-option label="全部" value="all" />
                    <el-option label="进行中" value="processing" />
                    <el-option label="已完成" value="completed" />
                    <el-option label="失败" value="failed" />
                  </el-select>
                  <el-button size="small" @click="loadTaskList">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
              <el-table :data="taskHistory" v-loading="loadingTasks" style="width: 100%">
                <el-table-column prop="task_id" label="任务ID" width="280" />
                <el-table-column prop="description" label="描述" min-width="150" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getTaskStatusType(row.status)" size="small">
                      {{ getTaskStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="progress" label="进度" width="100">
                  <template #default="{ row }">
                    <el-progress :percentage="row.progress || 0" :status="row.status === 'completed' ? 'success' : undefined" />
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160">
                  <template #default="{ row }">
                    {{ formatDateTime(row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      v-if="row.status === 'processing'"
                      type="text"
                      size="small"
                      @click="viewTaskProgress(row.task_id)"
                    >
                      查看进度
                    </el-button>
                    <el-button
                      v-if="row.status === 'failed'"
                      type="text"
                      size="small"
                      @click="retryTask(row.task_id)"
                    >
                      重试
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-pagination
                v-if="taskTotal > taskPageSize"
                v-model:current-page="taskPage"
                v-model:page-size="taskPageSize"
                :total="taskTotal"
                layout="total, prev, pager, next"
                @current-change="loadTaskList"
                style="margin-top: 16px; justify-content: flex-end;"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 3: 索引记录 -->
        <el-tab-pane label="索引记录" name="records">
          <div class="records-panel">
            <div class="records-filters">
              <el-form inline>
                <el-form-item label="领域">
                  <domain-selector
                    v-model="recordFilter.namespace"
                    placeholder="全部领域"
                    clearable
                    style="width: 200px;"
                  />
                </el-form-item>
                <el-form-item label="状态">
                  <el-select v-model="recordFilter.status" clearable style="width: 150px;">
                    <el-option label="已索引" value="indexed" />
                    <el-option label="待索引" value="pending" />
                    <el-option label="失败" value="failed" />
                    <el-option label="已过期" value="outdated" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="loadIndexRecords">
                    查询
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <el-table :data="indexRecords" v-loading="loadingRecords" style="width: 100%">
              <el-table-column prop="document_id" label="文档ID" width="100" />
              <el-table-column prop="filename" label="文件名" min-width="200" />
              <el-table-column prop="namespace" label="领域" width="120" />
              <el-table-column prop="content_hash" label="内容哈希" width="200" show-overflow-tooltip />
              <el-table-column prop="chunk_count" label="分块数" width="100" />
              <el-table-column prop="index_status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getIndexStatusType(row.index_status)" size="small">
                    {{ row.index_status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="last_indexed_at" label="最后索引时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.last_indexed_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button
                    type="text"
                    size="small"
                    @click="handleReindex(row.document_id)"
                  >
                    重新索引
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="recordTotal > recordPageSize"
              v-model:current-page="recordPage"
              v-model:page-size="recordPageSize"
              :total="recordTotal"
              layout="total, prev, pager, next"
              @current-change="loadIndexRecords"
              style="margin-top: 16px; justify-content: flex-end;"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import indexTaskService from '../services/indexTaskService'
import IndexStats from '../components/index/IndexStats.vue'
import TaskMonitor from '../components/index/TaskMonitor.vue'
import DomainSelector from '../components/domain/DomainSelector.vue'
import { Refresh, Search } from '@element-plus/icons-vue'

// 响应式数据
const activeTab = ref('changes')
const selectedNamespace = ref('default')
const detecting = ref(false)
const updating = ref(false)
const indexStatsRef = ref(null)

// 变更检测
const detectForm = ref({
  namespace: 'default',
  sinceHours: 24,
  forceCheck: false
})
const changeResult = ref(null)

// 计算变更文档列表
const changedDocuments = computed(() => {
  if (!changeResult.value) return []

  const newDocs = (changeResult.value.new_documents || []).map(doc => ({
    ...doc,
    change_type: 'new'
  }))

  const modifiedDocs = (changeResult.value.modified_documents || []).map(doc => ({
    ...doc,
    change_type: 'modified'
  }))

  return [...newDocs, ...modifiedDocs]
})

// 任务管理
const activeTasks = ref([])
const taskHistory = ref([])
const taskFilter = ref('all')
const taskPage = ref(1)
const taskPageSize = ref(20)
const taskTotal = ref(0)
const loadingTasks = ref(false)

// 索引记录
const indexRecords = ref([])
const recordFilter = ref({
  namespace: null,
  status: null
})
const recordPage = ref(1)
const recordPageSize = ref(20)
const recordTotal = ref(0)
const loadingRecords = ref(false)

// 方法
const handleDetectChanges = async () => {
  detecting.value = true
  try {
    const result = await indexTaskService.detectChanges({
      namespace: detectForm.value.namespace,
      sinceHours: detectForm.value.sinceHours,
      forceCheck: detectForm.value.forceCheck
    })

    changeResult.value = result

    const totalChanges = (result.new_documents?.length || 0) + (result.modified_documents?.length || 0)
    ElMessage.success(`检测完成! 发现 ${totalChanges} 个需要索引的文档`)
  } catch (error) {
    console.error('检测变更失败:', error)
  } finally {
    detecting.value = false
  }
}

const handleAutoUpdate = async () => {
  updating.value = true
  try {
    const result = await indexTaskService.autoUpdate({
      namespace: selectedNamespace.value,
      sinceHours: 24
    })

    if (result.task_id) {
      ElMessage.success('已创建自动更新任务')

      // 添加到活跃任务列表
      activeTasks.value.unshift({
        task_id: result.task_id,
        description: '自动更新任务',
        status: 'processing',
        progress: 0,
        created_at: new Date().toISOString()
      })

      // 切换到任务监控标签
      activeTab.value = 'tasks'
    }
  } catch (error) {
    console.error('自动更新失败:', error)
  } finally {
    updating.value = false
  }
}

const handleIndexDocument = async (docId) => {
  try {
    const result = await indexTaskService.indexDocument(docId, { force: false })

    if (result.task_id) {
      ElMessage.success('已创建索引任务')

      activeTasks.value.unshift({
        task_id: result.task_id,
        description: `索引文档 ${docId}`,
        status: 'processing',
        progress: 0,
        created_at: new Date().toISOString()
      })

      activeTab.value = 'tasks'
    }
  } catch (error) {
    console.error('索引文档失败:', error)
  }
}

const handleBatchIndex = async () => {
  if (changedDocuments.value.length === 0) {
    ElMessage.warning('没有需要索引的文档')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要批量索引 ${changedDocuments.value.length} 个文档吗?`,
      '批量索引确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const docIds = changedDocuments.value.map(doc => doc.id)
    const result = await indexTaskService.batchIndexDocuments(docIds)

    if (result.task_id) {
      ElMessage.success('已创建批量索引任务')

      activeTasks.value.unshift({
        task_id: result.task_id,
        description: `批量索引 ${docIds.length} 个文档`,
        status: 'processing',
        progress: 0,
        created_at: new Date().toISOString()
      })

      activeTab.value = 'tasks'
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量索引失败:', error)
    }
  }
}

const handleReindex = async (docId) => {
  try {
    await ElMessageBox.confirm(
      '确定要重新索引此文档吗?',
      '重新索引确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await handleIndexDocument(docId)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重新索引失败:', error)
    }
  }
}

const loadTaskList = async () => {
  loadingTasks.value = true
  try {
    const result = await indexTaskService.getTaskList({
      status: taskFilter.value === 'all' ? null : taskFilter.value,
      limit: taskPageSize.value,
      offset: (taskPage.value - 1) * taskPageSize.value
    })

    taskHistory.value = result.tasks || []
    taskTotal.value = result.total || 0
  } catch (error) {
    console.error('加载任务列表失败:', error)
  } finally {
    loadingTasks.value = false
  }
}

const loadIndexRecords = async () => {
  loadingRecords.value = true
  try {
    const result = await indexTaskService.getIndexRecords({
      namespace: recordFilter.value.namespace,
      status: recordFilter.value.status,
      limit: recordPageSize.value,
      offset: (recordPage.value - 1) * recordPageSize.value
    })

    indexRecords.value = result.records || []
    recordTotal.value = result.total || 0
  } catch (error) {
    console.error('加载索引记录失败:', error)
  } finally {
    loadingRecords.value = false
  }
}

const viewTaskProgress = (taskId) => {
  const task = activeTasks.value.find(t => t.task_id === taskId)
  if (!task) {
    activeTasks.value.unshift({
      task_id: taskId,
      description: '查看任务进度',
      status: 'processing',
      progress: 0,
      created_at: new Date().toISOString()
    })
  }
}

const retryTask = async (taskId) => {
  try {
    await indexTaskService.retryTask(taskId)
    ElMessage.success('已提交重试请求')
    loadTaskList()
  } catch (error) {
    console.error('重试任务失败:', error)
  }
}

const handleTaskCompleted = (result) => {
  ElMessage.success('任务执行成功!')

  // 刷新统计数据
  if (indexStatsRef.value) {
    indexStatsRef.value.refresh()
  }

  // 刷新任务列表
  loadTaskList()
}

const handleTaskFailed = (error) => {
  ElMessage.error('任务执行失败: ' + error)
  loadTaskList()
}

const removeActiveTask = (taskId) => {
  const index = activeTasks.value.findIndex(t => t.task_id === taskId)
  if (index > -1) {
    activeTasks.value.splice(index, 1)
  }
}

const getTaskStatusType = (status) => {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getTaskStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getIndexStatusType = (status) => {
  const types = {
    indexed: 'success',
    pending: 'info',
    failed: 'danger',
    outdated: 'warning'
  }
  return types[status] || 'info'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生命周期
onMounted(() => {
  loadTaskList()
  loadIndexRecords()
})

onBeforeUnmount(() => {
  // 断开所有WebSocket连接
  indexTaskService.disconnectAll()
})
</script>

<style lang="scss" scoped>
.index-management-page {
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
    }
  }
}

.stats-section {
  margin-bottom: 24px;
}

.main-content {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.index-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 24px;
  }
}

.changes-panel {
  .detect-config {
    margin-bottom: 24px;
    padding: 20px;
    background: rgba(17, 24, 39, 0.6);
    border-radius: 8px;
  }

  .change-result {
    .result-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;

      .summary-item {
        padding: 20px;
        background: rgba(17, 24, 39, 0.6);
        border-radius: 8px;
        text-align: center;

        h4 {
          font-size: 14px;
          color: var(--tech-text-secondary);
          margin: 0 0 12px 0;
        }

        .count {
          font-size: 32px;
          font-weight: 700;
          margin: 0;

          &.new {
            color: #67c23a;
          }

          &.modified {
            color: #e6a23c;
          }

          &.unchanged {
            color: #909399;
          }

          &.total {
            color: var(--tech-neon-blue);
          }
        }
      }
    }

    .changed-documents {
      h4 {
        font-size: 16px;
        color: var(--tech-text-primary);
        margin: 0 0 16px 0;
      }

      .batch-actions {
        display: flex;
        justify-content: flex-end;
      }
    }
  }
}

.tasks-panel {
  .active-tasks {
    margin-bottom: 32px;

    h3 {
      font-size: 18px;
      color: var(--tech-text-primary);
      margin: 0 0 16px 0;
    }
  }

  .task-history {
    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      h3 {
        font-size: 18px;
        color: var(--tech-text-primary);
        margin: 0;
      }

      .history-filters {
        display: flex;
        gap: 12px;
      }
    }
  }
}

.records-panel {
  .records-filters {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .page-header .header-content {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
