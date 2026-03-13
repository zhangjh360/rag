<template>
  <div class="history-container">
    <!-- 页面标题和工具栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">历史记录</h1>
        <div class="stats-chips">
          <span class="stat-chip">
            <el-icon><Document /></el-icon>
            共 {{ total }} 条记录
          </span>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="refreshHistory" :loading="loading" class="action-btn">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选工具栏 -->
    <div class="toolbar">
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索历史记录..."
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch" class="search-btn">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>

      <div class="filter-group">
        <!-- 类型选择 -->
        <el-segmented v-model="activeTab" :options="tabOptions" size="large" @change="handleTabChange" />

        <!-- 时间范围筛选 -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleDateChange"
          class="date-picker"
          size="large"
        />

        <!-- 视图切换 -->
        <el-tooltip content="切换布局" placement="top">
          <el-button-group class="view-toggle">
            <el-button
              :type="viewMode === 'grid' ? 'primary' : ''"
              @click="viewMode = 'grid'"
              :icon="Grid"
            />
            <el-button
              :type="viewMode === 'list' ? 'primary' : ''"
              @click="viewMode = 'list'"
              :icon="List"
            />
          </el-button-group>
        </el-tooltip>
      </div>
    </div>

    <!-- 历史记录内容区域 -->
    <div class="history-content">
      <!-- 空状态 -->
      <div v-if="filteredHistory.length === 0" class="empty-state">
        <el-empty :description="searchKeyword ? '没有找到匹配的记录' : '暂无历史记录'" />
      </div>

      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="grid-view">
        <TransitionGroup name="card">
          <HistoryCard
            v-for="item in filteredHistory"
            :key="item.id"
            :item="item"
            :type="activeTab"
            @view-detail="handleViewDetail"
            @reuse="handleReuse"
            @delete="handleDelete"
          />
        </TransitionGroup>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <TransitionGroup name="list">
          <HistoryListItem
            v-for="item in filteredHistory"
            :key="item.id"
            :item="item"
            :type="activeTab"
            @view-detail="handleViewDetail"
            @reuse="handleReuse"
            @delete="handleDelete"
          />
        </TransitionGroup>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[12, 24, 48, 96]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        background
      />
    </div>

    <!-- 详情弹窗 -->
    <el-drawer
      v-model="detailDrawerVisible"
      :title="detailItem?.title || '记录详情'"
      size="600px"
      direction="rtl"
    >
      <HistoryDetail v-if="detailItem" :item="detailItem" :type="activeTab" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRagStore } from '../store/ragStore'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Search,
  Document,
  Grid,
  List,
  ChatDotRound,
  DataAnalysis
} from '@element-plus/icons-vue'
import HistoryCard from '../components/history/HistoryCard.vue'
import HistoryListItem from '../components/history/HistoryListItem.vue'
import HistoryDetail from '../components/history/HistoryDetail.vue'

const store = useRagStore()

// 状态管理
const loading = computed(() => store.loading)
const queryHistory = computed(() => store.queryHistory)
const chatHistory = computed(() => store.chatHistory)
const pagination = computed(() => store.pagination)

// UI 状态
const activeTab = ref('chat')
const viewMode = ref('grid') // 'grid' 或 'list'
const searchKeyword = ref('')
const dateRange = ref([])
const detailDrawerVisible = ref(false)
const detailItem = ref(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(12)
const total = computed(() => pagination.value.total)

// 标签页选项
const tabOptions = [
  {
    label: 'Chat 对话',
    value: 'chat',
    icon: ChatDotRound
  },
  {
    label: 'RAG 查询',
    value: 'query',
    icon: DataAnalysis
  }
]

// 计算属性：当前显示的历史记录
const currentHistory = computed(() => {
  return activeTab.value === 'chat' ? chatHistory.value : queryHistory.value
})

// 计算属性：过滤后的历史记录
const filteredHistory = computed(() => {
  let result = currentHistory.value

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item => {
      const query = (item.query || '').toLowerCase()
      const title = (item.title || '').toLowerCase()
      const response = (item.response || '').toLowerCase()
      return query.includes(keyword) || title.includes(keyword) || response.includes(keyword)
    })
  }

  // 日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    result = result.filter(item => {
      const itemDate = new Date(item.timestamp || item.created_at)
      return itemDate >= startDate && itemDate <= endDate
    })
  }

  return result
})

// 方法
const loadHistory = async (tab = activeTab.value, page = 1, size = pageSize.value) => {
  try {
    if (tab === 'chat') {
      await store.fetchChatHistory(page, size)
    } else {
      await store.fetchQueryHistory(page, size)
    }
  } catch (error) {
    ElMessage.error('加载历史记录失败: ' + error.message)
  }
}

const refreshHistory = async () => {
  try {
    await loadHistory()
    ElMessage.success('历史记录已刷新')
  } catch (error) {
    ElMessage.error('刷新失败: ' + error.message)
  }
}

const handleTabChange = async (tab) => {
  activeTab.value = tab
  currentPage.value = 1
  searchKeyword.value = ''
  dateRange.value = []
  await loadHistory(tab, 1, pageSize.value)
}

const handleSizeChange = async (size) => {
  pageSize.value = size
  currentPage.value = 1
  await loadHistory(activeTab.value, 1, size)
}

const handleCurrentChange = async (page) => {
  currentPage.value = page
  await loadHistory(activeTab.value, page, pageSize.value)
}

const handleSearch = () => {
  // 搜索在 computed 中自动完成，这里可以添加额外逻辑
  currentPage.value = 1
}

const handleDateChange = () => {
  // 日期筛选在 computed 中自动完成
  currentPage.value = 1
}

const handleViewDetail = (item) => {
  detailItem.value = item
  detailDrawerVisible.value = true
}

const handleReuse = (item) => {
  // 复用查询，跳转到对话页面
  ElMessage.success('已复用查询内容')
  // TODO: 实现跳转到 Chat 页面并填充查询内容
}

const handleDelete = async (item) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条记录吗？',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // TODO: 实现删除功能
    ElMessage.success('删除成功')
    await refreshHistory()
  } catch {
    // 用户取消
  }
}

// 生命周期
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  height: calc(100vh - 64px - 50px);
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
  overflow: hidden;
  gap: 20px;
}

/* ===== 页面标题 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: -0.5px;
}

.stats-chips {
  display: flex;
  gap: 8px;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 20px;
  font-size: 13px;
  color: #00d4ff;
  font-weight: 500;
}

.header-right {
  display: flex;
  gap: 12px;
}

.action-btn {
  background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 10px 20px;
  height: auto;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 212, 255, 0.4);
}

/* ===== 工具栏 ===== */
.toolbar {
  display: flex;
  gap: 16px;
  flex-shrink: 0;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(20px);
}

.search-box {
  flex: 1;
  max-width: 500px;
}

.search-input {
  --el-input-border-color: rgba(255, 255, 255, 0.1);
  --el-input-hover-border-color: rgba(0, 212, 255, 0.5);
  --el-input-focus-border-color: #00d4ff;
}

.search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 8px 16px;
  box-shadow: none;
}

.search-btn {
  background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 100%);
  border: none;
  color: white;
  font-weight: 600;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.date-picker {
  width: 280px;
}

.date-picker :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.view-toggle {
  border-radius: 8px;
  overflow: hidden;
}

/* ===== 内容区域 ===== */
.history-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;

  /* 自定义滚动条 */
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

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

/* 网格视图 */
.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
  padding: 4px;
}

/* 列表视图 */
.list-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ===== 分页 ===== */
.pagination-wrapper {
  flex-shrink: 0;
  padding: 20px;
  display: flex;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(20px);
}

:deep(.el-pagination) {
  --el-pagination-bg-color: rgba(255, 255, 255, 0.05);
  --el-pagination-hover-color: #00d4ff;
}

:deep(.el-pagination.is-background .el-pager li) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--tech-text-primary);
}

:deep(.el-pagination.is-background .el-pager li:not(.is-disabled):hover) {
  color: #00d4ff;
  border-color: #00d4ff;
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 100%);
  border-color: transparent;
  color: white;
}

/* ===== 动画 ===== */
.card-move,
.card-enter-active,
.card-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.9);
}

.card-leave-to {
  opacity: 0;
  transform: translateY(-30px) scale(0.9);
}

.card-leave-active {
  position: absolute;
}

.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* ===== 响应式设计 ===== */
@media (max-width: 768px) {
  .history-container {
    padding: 16px;
  }

  .toolbar {
    flex-direction: column;
    gap: 12px;
  }

  .search-box {
    max-width: none;
  }

  .filter-group {
    flex-wrap: wrap;
  }

  .grid-view {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 22px;
  }
}
</style>
