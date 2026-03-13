/**
 * Dashboard数据管理 Composable
 * 封装Dashboard页面的数据获取和状态管理逻辑
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDashboardStats } from '../services/dashboard'

export function useDashboard() {
  // 状态定义
  const loading = ref(false)
  const stats = ref({
    documents: { total: 0, recent_7days: 0, trend_percent: 0 },
    sessions: { total: 0, active_7days: 0, trend_percent: 0 },
    queries: { total: 0, recent_7days: 0, trend_percent: 0 },
    users: { total: 0, active: 0 }
  })

  const activityTimeline = ref([])
  const recentDocuments = ref([])
  const activeSessions = ref([])
  const lastUpdateTime = ref(null)

  // WebSocket连接
  let ws = null
  let reconnectTimer = null
  let refreshTimer = null
  const wsConnected = ref(false)

  /**
   * 加载Dashboard数据
   */
  const loadDashboardData = async () => {
    loading.value = true
    try {
      const data = await getDashboardStats()

      // 更新统计数据
      stats.value = {
        documents: data.documents || { total: 0, recent_7days: 0, trend_percent: 0 },
        sessions: data.sessions || { total: 0, active_7days: 0, trend_percent: 0 },
        queries: data.queries || { total: 0, recent_7days: 0, trend_percent: 0 },
        users: data.users || { total: 0, active: 0 }
      }

      // 更新活动时间线
      activityTimeline.value = data.activity_timeline || []

      // 更新最近文档
      recentDocuments.value = data.recent_documents || []

      // 更新活跃会话
      activeSessions.value = data.active_sessions || []

      // 更新时间戳
      lastUpdateTime.value = new Date()

      console.log('Dashboard数据加载成功', data)
    } catch (error) {
      console.error('加载Dashboard数据失败:', error)
      ElMessage.error('加载数据失败，请稍后重试')
    } finally {
      loading.value = false
    }
  }

  /**
   * 连接WebSocket实时推送
   */
  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = import.meta.env.VITE_WS_URL || 'localhost:8800'

      // 获取认证token
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.error('没有找到认证token，无法建立WebSocket连接')
        ElMessage.error('请先登录')
        return
      }

      // 将token作为查询参数传递
      const wsUrl = `${protocol}//${host}/ws/dashboard?token=${encodeURIComponent(token)}`

      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket连接已建立')
        wsConnected.value = true
        ElMessage.success('实时数据推送已连接')

        // 清除重连定时器
        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
          reconnectTimer = null
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('收到WebSocket消息:', data)

          // 根据消息类型更新相应数据
          if (data.type === 'stats_update') {
            handleStatsUpdate(data.data)
          } else if (data.type === 'document_uploaded') {
            handleDocumentUploaded(data.data)
          } else if (data.type === 'new_query') {
            handleNewQuery(data.data)
          } else if (data.type === 'new_message') {
            handleNewMessage(data.data)
          }
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        wsConnected.value = false
      }

      ws.onclose = () => {
        console.log('WebSocket连接已关闭')
        wsConnected.value = false

        // 5秒后尝试重连
        reconnectTimer = setTimeout(() => {
          console.log('尝试重新连接WebSocket...')
          connectWebSocket()
        }, 5000)
      }
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      wsConnected.value = false
    }
  }

  /**
   * 处理统计数据更新
   */
  const handleStatsUpdate = (data) => {
    if (data.documents) stats.value.documents = data.documents
    if (data.sessions) stats.value.sessions = data.sessions
    if (data.queries) stats.value.queries = data.queries
    if (data.users) stats.value.users = data.users
  }

  /**
   * 处理文档上传事件
   */
  const handleDocumentUploaded = (document) => {
    // 更新文档总数
    stats.value.documents.total++
    stats.value.documents.recent_7days++

    // 添加到最近文档列表
    recentDocuments.value.unshift(document)
    if (recentDocuments.value.length > 5) {
      recentDocuments.value.pop()
    }

    ElMessage.info(`新文档已上传: ${document.filename}`)
  }

  /**
   * 处理新查询事件
   */
  const handleNewQuery = (query) => {
    // 更新查询总数
    stats.value.queries.total++
    stats.value.queries.recent_7days++
  }

  /**
   * 处理新消息事件
   */
  const handleNewMessage = (message) => {
    // 查找对应的会话并更新
    const session = activeSessions.value.find(s => s.session_id === message.session_id)
    if (session) {
      session.message_count++
      session.last_message = message.content.substring(0, 50) + '...'
      session.relative_time = '刚刚'
    }
  }

  /**
   * 断开WebSocket连接
   */
  const disconnectWebSocket = () => {
    if (ws) {
      ws.close()
      ws = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    wsConnected.value = false
  }

  /**
   * 手动刷新数据
   */
  const refresh = async () => {
    await loadDashboardData()
    ElMessage.success('数据已刷新')
  }

  /**
   * 启动定时刷新 (作为WebSocket的备选方案)
   */
  const startAutoRefresh = (interval = 30000) => {
    // 如果WebSocket已连接，不需要定时刷新
    if (wsConnected.value) return

    refreshTimer = setInterval(() => {
      if (!wsConnected.value) {
        console.log('执行定时刷新...')
        loadDashboardData()
      }
    }, interval)
  }

  /**
   * 停止定时刷新
   */
  const stopAutoRefresh = () => {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  // 计算属性
  const hasData = computed(() => {
    return stats.value.documents.total > 0 ||
           stats.value.sessions.total > 0 ||
           stats.value.queries.total > 0
  })

  const formattedUpdateTime = computed(() => {
    if (!lastUpdateTime.value) return ''
    return lastUpdateTime.value.toLocaleTimeString('zh-CN')
  })

  // 生命周期钩子
  onMounted(() => {
    // 首次加载数据
    loadDashboardData()

    // 尝试连接WebSocket
    connectWebSocket()

    // 启动定时刷新 (作为备选)
    startAutoRefresh(30000)
  })

  onUnmounted(() => {
    // 清理资源
    disconnectWebSocket()
    stopAutoRefresh()
  })

  return {
    // 状态
    loading,
    stats,
    activityTimeline,
    recentDocuments,
    activeSessions,
    lastUpdateTime,
    wsConnected,
    hasData,
    formattedUpdateTime,

    // 方法
    loadDashboardData,
    refresh,
    connectWebSocket,
    disconnectWebSocket
  }
}
