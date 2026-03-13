/**
 * 文档索引任务服务
 * 提供增量索引、任务管理和WebSocket实时更新功能
 */
import api from './api'
import { ElMessage } from 'element-plus'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800'
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

export const indexTaskService = {
  /**
   * ========================
   * Phase 1: 变更检测与增量索引
   * ========================
   */

  // 检测文档变更
  async detectChanges(params = {}) {
    try {
      const response = await api.post('/api/index/detect-changes', {
        namespace: params.namespace || 'default',
        since_hours: params.sinceHours || 24
      })
      // 解包IndexResponse，返回data字段
      return response.data.data || response.data
    } catch (error) {
      console.error('检测文档变更失败:', error)
      ElMessage.error('检测文档变更失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 一键自动更新(检测+索引)
  async autoUpdate(params = {}) {
    try {
      const response = await api.post('/api/index/auto-update', {
        namespace: params.namespace || 'default',
        since_hours: params.sinceHours || 24
      })
      return response.data.data || response.data
    } catch (error) {
      console.error('自动更新失败:', error)
      ElMessage.error('自动更新失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 索引单个文档
  async indexDocument(docId, options = {}) {
    try {
      // 使用批量索引接口处理单个文档
      const response = await api.post('/api/index/index-documents', {
        doc_ids: [docId],  // 传递单个文档ID的数组
        force: options.force || false,
        priority: options.priority || 5
      })
      return response.data.data || response.data
    } catch (error) {
      console.error('索引文档失败:', error)
      ElMessage.error('索引文档失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 批量索引文档
  async batchIndexDocuments(docIds) {
    try {
      const response = await api.post('/api/index/index-documents', {
        doc_ids: docIds,
        force: false,
        priority: 5
      })
      return response.data.data || response.data
    } catch (error) {
      console.error('批量索引失败:', error)
      ElMessage.error('批量索引失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 删除文档索引
  async deleteDocumentIndex(docId) {
    try {
      const response = await api.delete(`/api/index/document/${docId}`)
      return response.data.data || response.data
    } catch (error) {
      console.error('删除索引失败:', error)
      ElMessage.error('删除索引失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 获取索引记录
  async getIndexRecords(params = {}) {
    try {
      const response = await api.get('/api/index/records', {
        params: {
          namespace: params.namespace,
          status: params.status,
          limit: params.limit || 100,
          offset: params.offset || 0
        }
      })
      return response.data.data || { records: [], total: 0 }
    } catch (error) {
      console.error('获取索引记录失败:', error)
      return { records: [], total: 0 }
    }
  },

  /**
   * ========================
   * Phase 2: 任务队列管理
   * ========================
   */

  // 获取任务状态
  async getTaskStatus(taskId) {
    try {
      const response = await api.get(`/api/index/task/${taskId}`)
      return response.data.data || response.data
    } catch (error) {
      console.error('获取任务状态失败:', error)
      throw error
    }
  },

  // 获取任务列表
  async getTaskList(params = {}) {
    try {
      const response = await api.get('/api/index/tasks', {
        params: {
          status: params.status,
          limit: params.limit || 50,
          offset: params.offset || 0
        }
      })
      return response.data.data || { tasks: [], total: 0 }
    } catch (error) {
      console.error('获取任务列表失败:', error)
      return { tasks: [], total: 0 }
    }
  },

  // 重试失败的任务
  async retryTask(taskId) {
    try {
      const response = await api.post(`/api/index/task/${taskId}/retry`)
      return response.data.data || response.data
    } catch (error) {
      console.error('重试任务失败:', error)
      ElMessage.error('重试任务失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  // 取消任务
  async cancelTask(taskId) {
    try {
      const response = await api.post(`/api/index/task/${taskId}/cancel`)
      return response.data.data || response.data
    } catch (error) {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败: ' + (error.response?.data?.detail || error.message))
      throw error
    }
  },

  /**
   * ========================
   * 统计与历史
   * ========================
   */

  // 获取索引统计信息
  async getIndexStats(params = {}) {
    try {
      const response = await api.get('/api/index/stats', {
        params: {
          namespace: params.namespace,
          days: params.days || 7
        }
      })
      // 解包IndexResponse，返回data字段中的统计数据
      return response.data.data || response.data || null
    } catch (error) {
      console.error('获取索引统计失败:', error)
      return null
    }
  },

  // 获取变更历史
  async getChangeHistory(params = {}) {
    try {
      const response = await api.get('/api/index/history', {
        params: {
          doc_id: params.docId,
          limit: params.limit || 50,
          offset: params.offset || 0
        }
      })
      return response.data.data || { history: [], total: 0 }
    } catch (error) {
      console.error('获取变更历史失败:', error)
      return { history: [], total: 0 }
    }
  },

  /**
   * ========================
   * Phase 3: WebSocket实时推送
   * ========================
   */

  // WebSocket连接池
  _wsConnections: new Map(),

  // 连接到任务进度WebSocket
  connectTaskProgress(taskId, callbacks = {}) {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.error('未找到认证token')
      ElMessage.error('请先登录')
      return null
    }

    // 如果已存在连接,先关闭
    if (this._wsConnections.has(taskId)) {
      this.disconnectTaskProgress(taskId)
    }

    const wsUrl = `${WS_BASE_URL}/ws/task/${taskId}?token=${token}`
    console.log('连接WebSocket:', wsUrl)

    const ws = new WebSocket(wsUrl)

    // 连接建立
    ws.onopen = () => {
      console.log(`WebSocket已连接: task_id=${taskId}`)
      if (callbacks.onConnected) {
        callbacks.onConnected()
      }

      // 启动心跳
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 30000) // 每30秒发送一次心跳

      ws._heartbeat = heartbeat
    }

    // 接收消息
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        console.log('WebSocket消息:', message)

        // 根据消息类型分发回调
        switch (message.type) {
          case 'connected':
            if (callbacks.onConnected) {
              callbacks.onConnected(message)
            }
            break

          case 'progress':
            if (callbacks.onProgress) {
              callbacks.onProgress(message)
            }
            break

          case 'completed':
            if (callbacks.onComplete) {
              callbacks.onComplete(message)
            }
            // 自动关闭连接
            setTimeout(() => this.disconnectTaskProgress(taskId), 1000)
            break

          case 'error':
            if (callbacks.onError) {
              callbacks.onError(message)
            }
            // 自动关闭连接
            setTimeout(() => this.disconnectTaskProgress(taskId), 1000)
            break

          case 'pong':
            // 心跳响应,忽略
            break

          default:
            console.warn('未知消息类型:', message.type)
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error, event.data)
      }
    }

    // 连接错误
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      if (callbacks.onError) {
        callbacks.onError({ error: 'WebSocket连接错误' })
      }
    }

    // 连接关闭
    ws.onclose = (event) => {
      console.log(`WebSocket已断开: task_id=${taskId}, code=${event.code}`)

      // 清理心跳
      if (ws._heartbeat) {
        clearInterval(ws._heartbeat)
      }

      // 从连接池移除
      this._wsConnections.delete(taskId)

      if (callbacks.onDisconnected) {
        callbacks.onDisconnected(event)
      }
    }

    // 保存到连接池
    this._wsConnections.set(taskId, ws)

    return ws
  },

  // 断开WebSocket连接
  disconnectTaskProgress(taskId) {
    const ws = this._wsConnections.get(taskId)
    if (ws) {
      // 清理心跳
      if (ws._heartbeat) {
        clearInterval(ws._heartbeat)
      }

      // 关闭连接
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }

      this._wsConnections.delete(taskId)
      console.log(`已断开WebSocket: task_id=${taskId}`)
    }
  },

  // 断开所有WebSocket连接
  disconnectAll() {
    for (const [taskId, ws] of this._wsConnections) {
      if (ws._heartbeat) {
        clearInterval(ws._heartbeat)
      }
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    }
    this._wsConnections.clear()
    console.log('已断开所有WebSocket连接')
  }
}

// 页面卸载时自动断开所有连接
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    indexTaskService.disconnectAll()
  })
}

export default indexTaskService
