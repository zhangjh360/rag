<template>
  <div class="performance-stats">
    <div class="stats-header">
      <h3>性能统计</h3>
      <div class="time-range">
        <el-select v-model="timeRange" @change="fetchStats" size="small">
          <el-option label="最近1小时" :value="1" />
          <el-option label="最近24小时" :value="24" />
          <el-option label="最近7天" :value="168" />
        </el-select>
        <el-button @click="refreshStats" size="small" :loading="loading">
          <i class="fas fa-sync-alt"></i>
        </el-button>
      </div>
    </div>

    <div v-if="stats && !loading" class="stats-content">
      <!-- 概览指标 -->
      <div class="overview-cards">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(64, 158, 255, 0.1);">
            <i class="fas fa-search" style="color: #409EFF;"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.summary?.total_queries || 0 }}</div>
            <div class="stat-label">总查询数</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(103, 194, 58, 0.1);">
            <i class="fas fa-clock" style="color: #67C23A;"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.summary?.avg_latency_ms?.toFixed(0) || 0 }}ms</div>
            <div class="stat-label">平均响应时间</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(245, 108, 108, 0.1);">
            <i class="fas fa-exclamation-triangle" style="color: #F56C6C;"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.summary?.error_rate?.toFixed(1) || 0 }}%</div>
            <div class="stat-label">错误率</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(230, 162, 60, 0.1);">
            <i class="fas fa-users" style="color: #E6A23C;"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.summary?.unique_sessions || 0 }}</div>
            <div class="stat-label">活跃会话</div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-grid">
        <!-- 每小时查询量趋势 -->
        <div class="chart-card">
          <h4>查询量趋势</h4>
          <div ref="queryTrendChart" class="chart-container"></div>
        </div>

        <!-- 响应时间分布 -->
        <div class="chart-card">
          <h4>检索模式分布</h4>
          <div ref="modeChart" class="chart-container"></div>
        </div>

        <!-- 领域分布 -->
        <div class="chart-card">
          <h4>领域查询分布</h4>
          <div ref="namespaceChart" class="chart-container"></div>
        </div>
      </div>

      <!-- 慢查询列表 -->
      <div class="slow-queries-section">
        <div class="section-header">
          <h4>慢查询列表</h4>
          <el-button @click="viewSlowQueries" size="small" type="primary">
            查看更多
          </el-button>
        </div>
        <div v-if="recentSlowQueries.length > 0" class="slow-queries-list">
          <div v-for="(query, index) in recentSlowQueries" :key="index" class="slow-query-item">
            <div class="query-info">
              <div class="query-text">{{ query.query }}</div>
              <div class="query-meta">
                <el-tag size="small">{{ query.retrieval_mode }}</el-tag>
                <span class="latency">{{ (query.total_latency_ms || query.latency_ms || 0).toFixed(0) }}ms</span>
                <span class="time">{{ formatTime(query.timestamp) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          暂无慢查询
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="loading-container">
      <el-loading :fullscreen="false" />
    </div>

    <div v-else class="no-data">
      暂无数据
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import performanceService from '../../services/performanceService'

// 响应式数据
const timeRange = ref(24)
const loading = ref(false)
const stats = ref(null)
const recentSlowQueries = ref([])

// 图表引用
const queryTrendChart = ref(null)
const modeChart = ref(null)
const namespaceChart = ref(null)

// 图表实例
let queryTrendChartInstance = null
let modeChartInstance = null
let namespaceChartInstance = null

// 获取性能统计
const fetchStats = async () => {
  loading.value = true
  try {
    const response = await performanceService.getStats({ hours: timeRange.value })
    if (response.success) {
      stats.value = response.data
      await nextTick()
      renderCharts()
    }

    // 获取慢查询
    await fetchSlowQueries()
  } catch (error) {
    console.error('获取性能统计失败:', error)
    ElMessage.error('获取性能统计失败')
  } finally {
    loading.value = false
  }
}

// 获取慢查询
const fetchSlowQueries = async () => {
  try {
    const response = await performanceService.getSlowQueries({ hours: timeRange.value, limit: 5 })
    if (response.success) {
      recentSlowQueries.value = response.data.slow_queries
    }
  } catch (error) {
    console.error('获取慢查询失败:', error)
  }
}

// 渲染图表
const renderCharts = () => {
  renderQueryTrendChart()
  renderModeChart()
  renderNamespaceChart()
}

// 查询量趋势图
const renderQueryTrendChart = () => {
  if (!queryTrendChart.value || !stats.value?.hourly_trend) return

  const data = stats.value.hourly_trend.reverse()

  if (queryTrendChartInstance) {
    queryTrendChartInstance.dispose()
  }

  queryTrendChartInstance = echarts.init(queryTrendChart.value)

  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => formatHour(item.hour)),
      axisLabel: {
        fontSize: 11
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '查询数',
        nameTextStyle: {
          fontSize: 12
        }
      },
      {
        type: 'value',
        name: '响应时间(ms)',
        nameTextStyle: {
          fontSize: 12
        }
      }
    ],
    series: [
      {
        name: '查询量',
        type: 'bar',
        data: data.map(item => item.count),
        itemStyle: {
          color: 'rgba(64, 158, 255, 0.7)'
        }
      },
      {
        name: '响应时间',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(item => item.avg_latency_ms),
        itemStyle: {
          color: '#67C23A'
        },
        smooth: true
      }
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['查询量', '响应时间'],
      bottom: 0
    }
  }

  queryTrendChartInstance.setOption(option)
}

// 检索模式分布图
const renderModeChart = () => {
  if (!modeChart.value || !stats.value?.by_retrieval_mode) return

  const data = stats.value.by_retrieval_mode

  if (modeChartInstance) {
    modeChartInstance.dispose()
  }

  modeChartInstance = echarts.init(modeChart.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '检索模式',
        type: 'pie',
        radius: '50%',
        data: data.map(item => ({
          value: item.count,
          name: item.mode
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  modeChartInstance.setOption(option)
}

// 领域分布图
const renderNamespaceChart = () => {
  if (!namespaceChart.value || !stats.value?.by_namespace) return

  const data = stats.value.by_namespace.slice(0, 10)

  if (namespaceChartInstance) {
    namespaceChartInstance.dispose()
  }

  namespaceChartInstance = echarts.init(namespaceChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.namespace)
    },
    series: [
      {
        name: '查询数',
        type: 'bar',
        data: data.map(item => item.count),
        itemStyle: {
          color: function(params) {
            const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
            return colors[params.dataIndex % colors.length]
          }
        }
      }
    ]
  }

  namespaceChartInstance.setOption(option)
}

// 刷新数据
const refreshStats = () => {
  fetchStats()
}

// 查看慢查询
const viewSlowQueries = () => {
  // 这里可以跳转到慢查询详情页或打开对话框
  ElMessage.info('慢查询详情功能开发中...')
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

// 格式化小时
const formatHour = (hourStr) => {
  const date = new Date(hourStr)
  return `${date.getHours()}:00`
}

// 响应式处理
window.addEventListener('resize', () => {
  queryTrendChartInstance?.resize()
  modeChartInstance?.resize()
  namespaceChartInstance?.resize()
})

// 组件挂载时获取数据
onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.performance-stats {
  padding: 20px;
  background: var(--tech-glass-bg);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid var(--tech-glass-border);
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.stats-header h3 {
  margin: 0;
  color: var(--tech-neon-blue);
  font-size: 20px;
  font-weight: 600;
}

.time-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--tech-dark-secondary);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--tech-glass-border);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--tech-text-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--tech-text-secondary);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.chart-card {
  background: var(--tech-dark-secondary);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--tech-glass-border);
}

.chart-card h4 {
  margin: 0 0 16px 0;
  color: var(--tech-text-primary);
  font-size: 16px;
  font-weight: 500;
}

.chart-container {
  height: 250px;
  width: 100%;
}

.slow-queries-section {
  background: var(--tech-dark-secondary);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--tech-glass-border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  color: var(--tech-text-primary);
  font-size: 16px;
  font-weight: 500;
}

.slow-queries-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slow-query-item {
  background: var(--tech-glass-bg);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--tech-glass-border);
}

.query-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.query-text {
  color: var(--tech-text-primary);
  font-size: 14px;
  line-height: 1.4;
}

.query-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--tech-text-secondary);
}

.latency {
  color: #F56C6C;
  font-weight: 500;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.no-data {
  text-align: center;
  color: var(--tech-text-secondary);
  padding: 40px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .performance-stats {
    padding: 16px;
  }

  .overview-cards {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .stats-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>