/**
 * 性能监控服务
 */

import api from './api'

const performanceService = {
  /**
   * 获取性能统计
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @param {string} params.namespace - 筛选领域
   * @returns {Promise} API响应
   */
  async getStats(params = {}) {
    const queryParams = new URLSearchParams()

    if (params.hours !== undefined) {
      queryParams.append('hours', params.hours)
    }
    if (params.namespace) {
      queryParams.append('namespace', params.namespace)
    }

    const response = await api.get(`/api/performance/stats?${queryParams.toString()}`)
    return response.data
  },

  /**
   * 获取慢查询列表
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @param {number} params.limit - 返回数量限制
   * @returns {Promise} API响应
   */
  async getSlowQueries(params = {}) {
    const queryParams = new URLSearchParams()

    if (params.hours !== undefined) {
      queryParams.append('hours', params.hours)
    }
    if (params.limit !== undefined) {
      queryParams.append('limit', params.limit)
    }

    const response = await api.get(`/api/performance/slow-queries?${queryParams.toString()}`)
    return response.data
  },

  /**
   * 获取系统健康状态
   * @returns {Promise} API响应
   */
  async getSystemHealth() {
    const response = await api.get('/api/performance/system-health')
    return response.data
  },

  /**
   * 清理旧日志
   * @param {Object} params - 查询参数
   * @param {number} params.days - 保留天数
   * @returns {Promise} API响应
   */
  async cleanupLogs(params = {}) {
    const queryParams = new URLSearchParams()

    if (params.days !== undefined) {
      queryParams.append('days', params.days)
    }

    const response = await api.post(`/api/performance/cleanup-logs?${queryParams.toString()}`)
    return response.data
  },

  /**
   * 获取日志保留策略信息
   * @returns {Promise} API响应
   */
  async getLogRetention() {
    const response = await api.get('/api/performance/retention')
    return response.data
  },

  /**
   * 获取性能趋势数据
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @param {string} params.namespace - 筛选领域
   * @returns {Promise} 趋势数据
   */
  async getPerformanceTrend(params = {}) {
    try {
      const stats = await this.getStats(params)

      if (!stats.success || !stats.data?.hourly_trend) {
        return []
      }

      // 格式化趋势数据
      return stats.data.hourly_trend.map(item => ({
        time: item.hour,
        count: item.count,
        avgLatency: item.avg_latency_ms
      }))
    } catch (error) {
      console.error('获取性能趋势失败:', error)
      return []
    }
  },

  /**
   * 获取检索模式分布
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @returns {Promise} 模式分布数据
   */
  async getRetrievalModeDistribution(params = {}) {
    try {
      const stats = await this.getStats(params)

      if (!stats.success || !stats.data?.by_retrieval_mode) {
        return []
      }

      return stats.data.by_retrieval_mode.map(item => ({
        mode: item.mode,
        count: item.count,
        avgLatency: item.avg_latency_ms
      }))
    } catch (error) {
      console.error('获取检索模式分布失败:', error)
      return []
    }
  },

  /**
   * 获取领域查询分布
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @param {number} params.limit - 返回数量限制
   * @returns {Promise} 领域分布数据
   */
  async getNamespaceDistribution(params = {}) {
    try {
      const stats = await this.getStats(params)

      if (!stats.success || !stats.data?.by_namespace) {
        return []
      }

      let data = stats.data.by_namespace
      if (params.limit) {
        data = data.slice(0, params.limit)
      }

      return data.map(item => ({
        namespace: item.namespace,
        count: item.count,
        avgLatency: item.avg_latency_ms
      }))
    } catch (error) {
      console.error('获取领域分布失败:', error)
      return []
    }
  },

  /**
   * 获取性能指标摘要
   * @param {Object} params - 查询参数
   * @param {number} params.hours - 时间范围(小时)
   * @returns {Promise} 性能指标摘要
   */
  async getPerformanceSummary(params = {}) {
    try {
      const [stats, health] = await Promise.all([
        this.getStats(params),
        this.getSystemHealth()
      ])

      if (!stats.success) {
        throw new Error('获取统计数据失败')
      }

      const summary = stats.data?.summary || {}
      const healthData = health.data || {}

      return {
        totalQueries: summary.total_queries || 0,
        avgLatency: summary.avg_latency_ms || 0,
        errorRate: summary.error_rate || 0,
        healthScore: healthData.health_score || 100,
        healthStatus: healthData.health_status || '优秀',
        uniqueSessions: summary.unique_sessions || 0,
        minLatency: summary.min_latency_ms || 0,
        maxLatency: summary.max_latency_ms || 0,
        avgCandidates: summary.avg_candidates || 0,
        avgFiltered: summary.avg_filtered || 0
      }
    } catch (error) {
      console.error('获取性能摘要失败:', error)
      return {
        totalQueries: 0,
        avgLatency: 0,
        errorRate: 0,
        healthScore: 100,
        healthStatus: '未知',
        uniqueSessions: 0,
        minLatency: 0,
        maxLatency: 0,
        avgCandidates: 0,
        avgFiltered: 0
      }
    }
  },

  /**
   * 格式化响应时间显示
   * @param {number} latencyMs - 响应时间(毫秒)
   * @returns {Object} 格式化后的时间和颜色
   */
  formatLatency(latencyMs) {
    if (latencyMs < 100) {
      return { text: `${latencyMs.toFixed(0)}ms`, color: '#67C23A' }
    } else if (latencyMs < 500) {
      return { text: `${latencyMs.toFixed(0)}ms`, color: '#E6A23C' }
    } else if (latencyMs < 1000) {
      return { text: `${(latencyMs / 1000).toFixed(1)}s`, color: '#F56C6C' }
    } else {
      return { text: `${(latencyMs / 1000).toFixed(1)}s`, color: '#F56C6C' }
    }
  },

  /**
   * 格式化错误率显示
   * @param {number} errorRate - 错误率(百分比)
   * @returns {Object} 格式化后的错误率和颜色
   */
  formatErrorRate(errorRate) {
    if (errorRate < 1) {
      return { text: `${errorRate.toFixed(1)}%`, color: '#67C23A' }
    } else if (errorRate < 5) {
      return { text: `${errorRate.toFixed(1)}%`, color: '#E6A23C' }
    } else {
      return { text: `${errorRate.toFixed(1)}%`, color: '#F56C6C' }
    }
  },

  /**
   * 格式化健康状态
   * @param {number} healthScore - 健康评分
   * @returns {Object} 健康状态信息
   */
  formatHealthStatus(healthScore) {
    if (healthScore >= 90) {
      return {
        status: '优秀',
        color: '#67C23A',
        icon: 'fas fa-check-circle'
      }
    } else if (healthScore >= 75) {
      return {
        status: '良好',
        color: '#409EFF',
        icon: 'fas fa-thumbs-up'
      }
    } else if (healthScore >= 60) {
      return {
        status: '一般',
        color: '#E6A23C',
        icon: 'fas fa-exclamation-circle'
      }
    } else {
      return {
        status: '需要关注',
        color: '#F56C6C',
        icon: 'fas fa-times-circle'
      }
    }
  }
}

export default performanceService