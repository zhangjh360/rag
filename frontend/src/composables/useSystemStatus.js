import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

export const useSystemStatus = () => {
  // 状态数据
  const apiStatus = ref('normal') // normal | warning | error
  const responseTime = ref(0) // 毫秒
  const uptime = ref(0) // 秒
  const lastUpdateTime = ref(new Date())
  const apiStatusHistory = ref([]) // 记录最近10次状态

  // 定时器
  let statusCheckInterval = null
  let uptimeInterval = null

  // API状态检查
  const checkApiStatus = async () => {
    const startTime = Date.now()
    try {
      const response = await api.get('/health', {
        timeout: 5000
      })
      const endTime = Date.now()
      const currentResponseTime = endTime - startTime

      // 更新响应时间
      updateResponseTime(currentResponseTime)

      // 更新API状态
      if (currentResponseTime > 5000) {
        updateApiStatus('error', '超时')
      } else if (currentResponseTime > 1000) {
        updateApiStatus('warning', '延迟')
      } else {
        updateApiStatus('normal', '正常')
      }

    } catch (error) {
      const endTime = Date.now()
      const currentResponseTime = endTime - startTime
      updateResponseTime(currentResponseTime)
      updateApiStatus('error', '异常')
      console.warn('API状态检查失败:', error.message)
    }
  }

  // 更新API状态
  const updateApiStatus = (status, reason) => {
    const timestamp = new Date()
    apiStatus.value = status

    // 记录历史
    apiStatusHistory.value.unshift({
      status,
      reason,
      timestamp,
      responseTime: responseTime.value
    })

    // 只保留最近10条记录
    if (apiStatusHistory.value.length > 10) {
      apiStatusHistory.value = apiStatusHistory.value.slice(0, 10)
    }

    lastUpdateTime.value = timestamp
  }

  // 更新响应时间
  const updateResponseTime = (time) => {
    // 获取最近的响应时间历史
    const recentTimes = apiStatusHistory.value
      .slice(0, 5) // 取最近5次
      .map(item => item.responseTime)
      .filter(t => t > 0)

    // 如果有历史数据，计算平均响应时间
    if (recentTimes.length > 0) {
      const avgTime = recentTimes.reduce((sum, t) => sum + t, 0) / recentTimes.length
      responseTime.value = Math.round(avgTime)
    } else {
      responseTime.value = Math.round(time)
    }
  }

  // 格式化运行时间
  const formattedUptime = computed(() => {
    const days = Math.floor(uptime.value / 86400)
    const hours = Math.floor((uptime.value % 86400) / 3600)
    const minutes = Math.floor((uptime.value % 3600) / 60)
    const seconds = uptime.value % 60

    if (days > 0) {
      return `${days}天${hours}小时${minutes}分${seconds}秒`
    } else if (hours > 0) {
      return `${hours}小时${minutes}分${seconds}秒`
    } else if (minutes > 0) {
      return `${minutes}分${seconds}秒`
    } else {
      return `${seconds}秒`
    }
  })

  // 状态文本
  const statusText = computed(() => {
    const status = apiStatus.value
    switch (status) {
      case 'normal':
        return 'API 正常'
      case 'warning':
        return 'API 延迟'
      case 'error':
        return 'API 异常'
      default:
        return 'API 检测中'
    }
  })

  // 状态样式类
  const statusClass = computed(() => {
    const status = apiStatus.value
    switch (status) {
      case 'normal':
        return 'text-green-400'
      case 'warning':
        return 'text-yellow-400'
      case 'error':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  })

  // 状态点样式
  const statusDotClass = computed(() => {
    const status = apiStatus.value
    switch (status) {
      case 'normal':
        return 'bg-green-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  })

  // 启动监控
  const startMonitoring = () => {
    // 启动时立即检查一次
    checkApiStatus()

    // 每30秒检查一次API状态
    statusCheckInterval = setInterval(checkApiStatus, 30000)

    // 每秒更新运行时间
    uptimeInterval = setInterval(() => {
      uptime.value++
    }, 1000)
  }

  // 停止监控
  const stopMonitoring = () => {
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
      statusCheckInterval = null
    }
    if (uptimeInterval) {
      clearInterval(uptimeInterval)
      uptimeInterval = null
    }
  }

  // 初始化
  onMounted(() => {
    // 获取应用启动时间
    const startTimeStr = localStorage.getItem('app_start_time')
    if (startTimeStr) {
      const startTime = parseInt(startTimeStr, 10)
      const now = Date.now()
      uptime.value = Math.floor((now - startTime) / 1000)
    } else {
      // 如果没有记录，设置为当前时间
      const now = Date.now()
      localStorage.setItem('app_start_time', now.toString())
      uptime.value = 0
    }

    startMonitoring()
  })

  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    // 状态
    apiStatus,
    responseTime,
    uptime,
    lastUpdateTime,

    // 计算属性
    statusText,
    statusClass,
    statusDotClass,
    formattedUptime,

    // 方法
    checkApiStatus
  }
}
