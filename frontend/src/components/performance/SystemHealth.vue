<template>
  <div class="system-health">
    <el-card class="health-card">
      <template #header>
        <div class="card-header">
          <span><i class="fas fa-heartbeat"></i> 系统健康状态</span>
          <el-button size="small" @click="refresh" :loading="loading">
            <i class="fas fa-sync-alt"></i>
          </el-button>
        </div>
      </template>

      <div v-if="healthData && !loading" class="health-content">
        <!-- 健康评分 -->
        <div class="health-score-section">
          <div class="score-circle" :style="{ borderColor: getScoreColor(healthData.health_score) }">
            <div class="score-value" :style="{ color: getScoreColor(healthData.health_score) }">
              {{ healthData.health_score }}
            </div>
            <div class="score-label">健康评分</div>
          </div>
          <div class="score-info">
            <div class="status-badge" :style="{ background: getScoreColor(healthData.health_score) }">
              {{ healthData.health_status }}
            </div>
            <div v-if="healthData.health_issues && healthData.health_issues.length > 0" class="health-issues">
              <h4>需要关注的问题:</h4>
              <ul>
                <li v-for="(issue, index) in healthData.health_issues" :key="index">
                  <i class="fas fa-exclamation-triangle"></i> {{ issue }}
                </li>
              </ul>
            </div>
            <div v-else class="no-issues">
              <i class="fas fa-check-circle"></i> 系统运行良好,无明显问题
            </div>
          </div>
        </div>

        <!-- 实时指标 -->
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-header">最近1小时</div>
            <div class="metric-items">
              <div class="metric-item">
                <span class="metric-label">查询总数</span>
                <span class="metric-value">{{ healthData.recent_hour?.total_queries || 0 }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">平均响应时间</span>
                <span class="metric-value" :style="{ color: getLatencyColor(healthData.recent_hour?.avg_latency_ms) }">
                  {{ formatLatency(healthData.recent_hour?.avg_latency_ms || 0) }}
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">错误率</span>
                <span class="metric-value" :style="{ color: getErrorRateColor(healthData.recent_hour?.error_rate) }">
                  {{ (healthData.recent_hour?.error_rate || 0).toFixed(1) }}%
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">慢查询数</span>
                <span class="metric-value" :style="{ color: getSlowQueryColor(healthData.recent_hour?.slow_queries_count) }">
                  {{ healthData.recent_hour?.slow_queries_count || 0 }}
                </span>
              </div>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-header">最近24小时</div>
            <div class="metric-items">
              <div class="metric-item">
                <span class="metric-label">查询总数</span>
                <span class="metric-value">{{ healthData.last_24h?.total_queries || 0 }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">平均响应时间</span>
                <span class="metric-value" :style="{ color: getLatencyColor(healthData.last_24h?.avg_latency_ms) }">
                  {{ formatLatency(healthData.last_24h?.avg_latency_ms || 0) }}
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">错误率</span>
                <span class="metric-value" :style="{ color: getErrorRateColor(healthData.last_24h?.error_rate) }">
                  {{ (healthData.last_24h?.error_rate || 0).toFixed(1) }}%
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">活跃会话</span>
                <span class="metric-value">{{ healthData.last_24h?.unique_sessions || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="loading" class="loading-container">
        <el-loading :fullscreen="false" />
      </div>

      <div v-else class="no-data">
        暂无数据
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import performanceService from '../../services/performanceService'

const loading = ref(false)
const healthData = ref(null)

// 获取健康状态
const fetchHealthData = async () => {
  loading.value = true
  try {
    const response = await performanceService.getSystemHealth()
    if (response.success) {
      healthData.value = response.data
    }
  } catch (error) {
    console.error('获取健康状态失败:', error)
    ElMessage.error('获取系统健康状态失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refresh = () => {
  fetchHealthData()
}

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 75) return '#409EFF'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}

// 获取延迟颜色
const getLatencyColor = (latency) => {
  if (!latency) return '#67C23A'
  if (latency < 500) return '#67C23A'
  if (latency < 1000) return '#E6A23C'
  return '#F56C6C'
}

// 获取错误率颜色
const getErrorRateColor = (errorRate) => {
  if (!errorRate || errorRate < 1) return '#67C23A'
  if (errorRate < 5) return '#E6A23C'
  return '#F56C6C'
}

// 获取慢查询颜色
const getSlowQueryColor = (count) => {
  if (!count || count < 5) return '#67C23A'
  if (count < 10) return '#E6A23C'
  return '#F56C6C'
}

// 格式化延迟
const formatLatency = (latency) => {
  if (latency < 1000) {
    return `${latency.toFixed(0)}ms`
  }
  return `${(latency / 1000).toFixed(1)}s`
}

// 组件挂载时获取数据
onMounted(() => {
  fetchHealthData()

  // 每30秒自动刷新
  setInterval(fetchHealthData, 30000)
})
</script>

<style scoped>
.system-health {
  width: 100%;
}

.health-card {
  background: var(--tech-glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--tech-glass-border);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.card-header i {
  margin-right: 8px;
}

.health-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.health-score-section {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 20px;
  background: var(--tech-dark-secondary);
  border-radius: 12px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 6px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 12px;
  color: var(--tech-text-secondary);
  margin-top: 4px;
}

.score-info {
  flex: 1;
}

.status-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 16px;
}

.health-issues h4 {
  margin: 0 0 12px 0;
  color: var(--tech-text-primary);
  font-size: 14px;
  font-weight: 500;
}

.health-issues ul {
  margin: 0;
  padding: 0 0 0 20px;
  list-style: none;
}

.health-issues li {
  color: var(--tech-text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.health-issues li i {
  color: #E6A23C;
}

.no-issues {
  color: #67C23A;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.metric-card {
  background: var(--tech-dark-secondary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--tech-glass-border);
}

.metric-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--tech-neon-blue);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--tech-glass-border);
}

.metric-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 13px;
  color: var(--tech-text-secondary);
}

.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.no-data {
  text-align: center;
  color: var(--tech-text-secondary);
  padding: 40px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .health-score-section {
    flex-direction: column;
    text-align: center;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
