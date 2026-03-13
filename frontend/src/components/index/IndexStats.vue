<template>
  <div class="index-stats">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon><SuccessFilled /></el-icon>
        </div>
        <div class="stat-content">
          <h4>已索引文档</h4>
          <p class="stat-value">{{ stats.indexedCount || 0 }}</p>
          <p class="stat-subtitle">总计</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <h4>待索引文档</h4>
          <p class="stat-value">{{ stats.pendingCount || 0 }}</p>
          <p class="stat-subtitle">需要处理</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon info">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <h4>今日索引</h4>
          <p class="stat-value">{{ stats.todayCount || 0 }}</p>
          <p class="stat-subtitle">最近24小时</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon primary">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <h4>成本节省</h4>
          <p class="stat-value">{{ stats.costSavingPercent || 0 }}%</p>
          <p class="stat-subtitle">相比全量索引</p>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 索引趋势图 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>📈 索引趋势</h3>
          <el-radio-group v-model="trendPeriod" size="small" @change="loadStats">
            <el-radio-button label="7">最近7天</el-radio-button>
            <el-radio-button label="30">最近30天</el-radio-button>
          </el-radio-group>
        </div>
        <div class="chart-content">
          <div v-if="loading" class="chart-loading">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="trendData.length === 0" class="chart-empty">
            <el-empty description="暂无数据" />
          </div>
          <div v-else class="trend-chart">
            <!-- 简单的趋势图 -->
            <div class="trend-items" :class="{ 'trend-items-many': trendData.length > 15 }">
              <div
                v-for="(item, index) in trendData"
                :key="index"
                class="trend-item"
              >
                <div class="trend-bar-container">
                  <div
                    class="trend-bar"
                    :style="{
                      height: item.count > 0 ? `${Math.max((item.count / maxTrendValue) * 100, 5)}%` : '5%',
                      background: item.count > 0 ? 'var(--tech-gradient)' : 'rgba(144, 147, 153, 0.3)'
                    }"
                  >
                    <span v-if="item.count > 0" class="trend-value">{{ item.count }}</span>
                  </div>
                </div>
                <span class="trend-label">{{ item.date }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态分布饼图 -->
      <div class="chart-card">
        <div class="chart-header">
          <h3>📊 文档状态分布</h3>
        </div>
        <div class="chart-content">
          <div v-if="loading" class="chart-loading">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else class="status-distribution">
            <div class="distribution-items">
              <div
                v-for="item in statusDistribution"
                :key="item.status"
                class="distribution-item"
              >
                <div class="distribution-info">
                  <span class="distribution-dot" :style="{ background: item.color }"></span>
                  <span class="distribution-label">{{ item.label }}</span>
                </div>
                <div class="distribution-bar">
                  <div
                    class="distribution-fill"
                    :style="{
                      width: `${item.percentage}%`,
                      background: item.color
                    }"
                  ></div>
                </div>
                <span class="distribution-value">{{ item.count }} ({{ item.percentage }}%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能统计 -->
    <div class="performance-section">
      <div class="performance-card">
        <div class="performance-header">
          <h3>⚡ 性能统计</h3>
        </div>
        <div class="performance-content">
          <div class="performance-items">
            <div class="performance-item">
              <div class="performance-label">
                <el-icon><Timer /></el-icon>
                <span>平均索引时间</span>
              </div>
              <div class="performance-value">{{ stats.avgIndexTime || 0 }}s</div>
            </div>
            <div class="performance-item">
              <div class="performance-label">
                <el-icon><Odometer /></el-icon>
                <span>平均处理速度</span>
              </div>
              <div class="performance-value">{{ stats.avgProcessSpeed || 0 }} docs/min</div>
            </div>
            <div class="performance-item">
              <div class="performance-label">
                <el-icon><CreditCard /></el-icon>
                <span>估算节省成本</span>
              </div>
              <div class="performance-value success">¥{{ stats.estimatedSaving || 0 }}</div>
            </div>
            <div class="performance-item">
              <div class="performance-label">
                <el-icon><Lightning /></el-icon>
                <span>增量索引速度提升</span>
              </div>
              <div class="performance-value primary">{{ stats.speedupFactor || 0 }}x</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import indexTaskService from '../../services/indexTaskService'
import {
  SuccessFilled, Clock, Document, TrendCharts, Timer,
  Odometer, CreditCard, Lightning
} from '@element-plus/icons-vue'

const props = defineProps({
  namespace: {
    type: String,
    default: 'default'
  },
  autoRefresh: {
    type: Boolean,
    default: false
  },
  refreshInterval: {
    type: Number,
    default: 30000 // 30秒
  }
})

// 响应式数据
const loading = ref(false)
const trendPeriod = ref('7')
const stats = ref({
  indexedCount: 0,
  pendingCount: 0,
  todayCount: 0,
  costSavingPercent: 0,
  avgIndexTime: 0,
  avgProcessSpeed: 0,
  estimatedSaving: 0,
  speedupFactor: 0
})
const trendData = ref([])
const statusDistribution = ref([])

let refreshTimer = null

// 计算属性
const maxTrendValue = computed(() => {
  if (trendData.value.length === 0) return 1
  const max = Math.max(...trendData.value.map(item => item.count))
  // 如果最大值为0，返回1避免除以0；否则返回最大值
  return max > 0 ? max : 1
})

// 方法
const loadStats = async () => {
  loading.value = true
  try {
    const data = await indexTaskService.getIndexStats({
      namespace: props.namespace,
      days: parseInt(trendPeriod.value)
    })

    if (data) {
      // 更新统计数据 - 使用后端返回的camelCase字段名
      stats.value = {
        indexedCount: data.indexedCount || 0,
        pendingCount: data.pendingCount || 0,
        todayCount: data.todayCount || 0,
        costSavingPercent: data.costSavingPercent || 0,
        avgIndexTime: data.avgIndexTime?.toFixed(2) || 0,
        avgProcessSpeed: data.avgProcessSpeed?.toFixed(1) || 0,
        estimatedSaving: data.estimatedSaving?.toFixed(2) || 0,
        speedupFactor: data.speedupFactor?.toFixed(1) || 0
      }

      // 更新趋势数据 - 使用后端返回的trendData字段
      // 只有在有数据时才更新，避免闪现空状态
      if (data.trendData && Array.isArray(data.trendData) && data.trendData.length > 0) {
        trendData.value = data.trendData.map(item => ({
          date: formatDate(item.date),
          count: item.count || 0
        }))
      } else if (!trendData.value.length) {
        // 只有在当前没有数据时才设置为空数组
        trendData.value = []
      }

      // 更新状态分布 - 使用后端返回的statusDistribution字段
      if (data.statusDistribution) {
        const total = Object.values(data.statusDistribution).reduce((sum, count) => sum + count, 0)
        const newDistribution = [
          {
            status: 'indexed',
            label: '已索引',
            count: data.statusDistribution.indexed || 0,
            percentage: total > 0 ? Math.round((data.statusDistribution.indexed || 0) / total * 100) : 0,
            color: '#67c23a'
          },
          {
            status: 'pending',
            label: '待索引',
            count: data.statusDistribution.pending || 0,
            percentage: total > 0 ? Math.round((data.statusDistribution.pending || 0) / total * 100) : 0,
            color: '#e6a23c'
          },
          {
            status: 'outdated',
            label: '已过期',
            count: data.statusDistribution.outdated || 0,
            percentage: total > 0 ? Math.round((data.statusDistribution.outdated || 0) / total * 100) : 0,
            color: '#909399'
          },
          {
            status: 'failed',
            label: '失败',
            count: data.statusDistribution.failed || 0,
            percentage: total > 0 ? Math.round((data.statusDistribution.failed || 0) / total * 100) : 0,
            color: '#f56c6c'
          }
        ].filter(item => item.count > 0) // 只显示有数据的状态

        // 只有在有数据时才更新
        if (newDistribution.length > 0) {
          statusDistribution.value = newDistribution
        }
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(() => {
      loadStats()
    }, props.refreshInterval)
  }
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(() => {
  loadStats()
  startAutoRefresh()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})

// 暴露方法
defineExpose({
  refresh: loadStats
})
</script>

<style lang="scss" scoped>
.index-stats {
  width: 100%;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 240, 255, 0.2);
  }

  .stat-icon {
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    font-size: 28px;

    &.success {
      background: rgba(103, 194, 58, 0.1);
      color: #67c23a;
    }

    &.warning {
      background: rgba(230, 162, 60, 0.1);
      color: #e6a23c;
    }

    &.info {
      background: rgba(144, 147, 153, 0.1);
      color: #909399;
    }

    &.primary {
      background: rgba(0, 240, 255, 0.1);
      color: var(--tech-neon-blue);
    }
  }

  .stat-content {
    flex: 1;

    h4 {
      font-size: 14px;
      color: var(--tech-text-secondary);
      margin: 0 0 8px 0;
      font-weight: 500;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--tech-text-primary);
      margin: 0 0 4px 0;
    }

    .stat-subtitle {
      font-size: 12px;
      color: var(--tech-text-secondary);
      margin: 0;
    }
  }
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--tech-glass-border);

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--tech-text-primary);
      margin: 0;
    }
  }

  .chart-content {
    min-height: 250px;
  }

  .chart-loading,
  .chart-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 250px;
  }
}

.trend-chart {
  .trend-items {
    display: flex;
    gap: 8px;
    align-items: flex-end;
    height: 220px;
    padding: 0 10px;
    transition: all 0.3s ease;

    &.trend-items-many {
      // 当数据点超过15个时，启用横向滚动
      overflow-x: auto;
      overflow-y: hidden;
      justify-content: flex-start;

      // 自定义滚动条样式
      &::-webkit-scrollbar {
        height: 6px;
      }

      &::-webkit-scrollbar-track {
        background: rgba(17, 24, 39, 0.6);
        border-radius: 3px;
      }

      &::-webkit-scrollbar-thumb {
        background: var(--tech-glass-border);
        border-radius: 3px;

        &:hover {
          background: var(--tech-neon-blue);
        }
      }
    }

    .trend-item {
      flex: 1;
      min-width: 30px; // 设置最小宽度，避免30天时太窄
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      .trend-items-many & {
        // 在多数据模式下，设置固定宽度而非flex
        flex: 0 0 auto;
        width: 40px;
      }

      .trend-bar-container {
        flex: 1;
        width: 100%;
        display: flex;
        align-items: flex-end;
        justify-content: center;

        .trend-bar {
          width: 100%;
          max-width: 40px;
          border-radius: 4px 4px 0 0;
          position: relative;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding-top: 4px;
          transition: all 0.3s ease;
          min-height: 5%; // 设置最小高度

          &:hover {
            opacity: 0.8;
            transform: translateY(-2px);
          }

          .trend-value {
            font-size: 11px;
            font-weight: 600;
            color: white;
          }
        }
      }

      .trend-label {
        font-size: 11px;
        color: var(--tech-text-secondary);
        white-space: nowrap;

        .trend-items-many & {
          // 在多数据模式下，旋转标签以节省空间
          transform: rotate(-45deg);
          transform-origin: center;
          font-size: 10px;
        }
      }
    }
  }
}

.status-distribution {
  .distribution-items {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .distribution-item {
      display: grid;
      grid-template-columns: 120px 1fr 100px;
      align-items: center;
      gap: 12px;

      .distribution-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .distribution-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .distribution-label {
          font-size: 14px;
          color: var(--tech-text-primary);
        }
      }

      .distribution-bar {
        height: 24px;
        background: rgba(17, 24, 39, 0.6);
        border-radius: 12px;
        overflow: hidden;

        .distribution-fill {
          height: 100%;
          transition: width 0.5s ease;
        }
      }

      .distribution-value {
        font-size: 13px;
        font-weight: 600;
        color: var(--tech-text-primary);
        text-align: right;
      }
    }
  }
}

.performance-section {
  .performance-card {
    background: var(--tech-glass-bg);
    border: 1px solid var(--tech-glass-border);
    border-radius: 12px;
    padding: 20px;
    backdrop-filter: blur(10px);

    .performance-header {
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--tech-glass-border);

      h3 {
        font-size: 16px;
        font-weight: 600;
        color: var(--tech-text-primary);
        margin: 0;
      }
    }

    .performance-items {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;

      .performance-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        background: rgba(17, 24, 39, 0.6);
        border-radius: 8px;

        .performance-label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--tech-text-secondary);

          .el-icon {
            font-size: 18px;
          }
        }

        .performance-value {
          font-size: 20px;
          font-weight: 700;
          color: var(--tech-text-primary);

          &.success {
            color: #67c23a;
          }

          &.primary {
            color: var(--tech-neon-blue);
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }

  .charts-section {
    grid-template-columns: 1fr;
  }
}
</style>
