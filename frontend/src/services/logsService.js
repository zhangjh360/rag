import api from './api'
import { ElMessage } from 'element-plus'

/**
 * 日志管理服务
 * 提供日志查看、搜索、清理等功能的API调用
 */
export const logsService = {
  /**
   * 获取日志文件列表
   * @param {string} logType - 日志类型过滤
   * @returns {Promise<Array>} 日志文件列表
   */
  async getLogFiles(logType = null) {
    try {
      const params = logType ? { log_type: logType } : {}
      const response = await api.get('/api/logs/files', { params })
      return response.data
    } catch (error) {
      throw new Error(`获取日志文件列表失败: ${error.message}`)
    }
  },

  /**
   * 读取日志文件内容
   * @param {string} filePath - 文件路径
   * @param {number} lines - 读取行数，0表示全部
   * @returns {Promise<Object>} 日志内容
   */
  async readLogFile(filePath, lines = 100) {
    try {
      const response = await api.get(`/api/logs/read/${encodeURIComponent(filePath)}`, {
        params: { lines }
      })
      return response.data
    } catch (error) {
      throw new Error(`读取日志文件失败: ${error.message}`)
    }
  },

  /**
   * 搜索日志内容
   * @param {string} query - 搜索关键词
   * @param {string} logType - 日志类型
   * @param {number} hours - 搜索最近几小时的日志
   * @returns {Promise<Array>} 搜索结果
   */
  async searchLogs(query, logType = null, hours = 24) {
    try {
      const params = { query, hours }
      if (logType) params.log_type = logType

      const response = await api.get('/api/logs/search', { params })
      return response.data
    } catch (error) {
      throw new Error(`搜索日志失败: ${error.message}`)
    }
  },

  /**
   * 获取日志统计信息
   * @returns {Promise<Object>} 统计信息
   */
  async getLogStatistics() {
    try {
      const response = await api.get('/api/logs/statistics')
      return response.data
    } catch (error) {
      throw new Error(`获取日志统计失败: ${error.message}`)
    }
  },

  /**
   * 清理旧日志文件
   * @param {number} days - 保留天数
   * @returns {Promise<Object>} 清理结果
   */
  async cleanOldLogs(days = 30) {
    try {
      const response = await api.post('/api/logs/clean', null, {
        params: { days }
      })
      return response.data
    } catch (error) {
      throw new Error(`清理日志失败: ${error.message}`)
    }
  },

  /**
   * 归档日志文件
   * @param {number} days - 归档多少天前的日志
   * @returns {Promise<Object>} 归档结果
   */
  async archiveLogs(days = 7) {
    try {
      const response = await api.post('/api/logs/archive', null, {
        params: { days }
      })
      return response.data
    } catch (error) {
      throw new Error(`归档日志失败: ${error.message}`)
    }
  },

  /**
   * 导出日志到文件
   * @param {string} outputFile - 输出文件路径
   * @param {string} logType - 日志类型
   * @param {number} hours - 导出最近几小时的日志
   * @returns {Promise<Object>} 导出结果
   */
  async exportLogs(outputFile, logType = null, hours = 24) {
    try {
      const params = { output_file: outputFile, hours }
      if (logType) params.log_type = logType

      const response = await api.post('/api/logs/export', null, { params })
      return response.data
    } catch (error) {
      throw new Error(`导出日志失败: ${error.message}`)
    }
  },

  /**
   * 获取日志目录结构
   * @returns {Promise<Object>} 目录结构
   */
  async getLogDirectories() {
    try {
      const response = await api.get('/api/logs/directories')
      return response.data
    } catch (error) {
      throw new Error(`获取日志目录结构失败: ${error.message}`)
    }
  },

  /**
   * 格式化文件大小
   * @param {number} size - 字节数
   * @returns {string} 格式化后的文件大小
   */
  formatFileSize(size) {
    if (size === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(size) / Math.log(k))
    return parseFloat((size / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  /**
   * 格式化时间戳
   * @param {string} timestamp - ISO时间戳
   * @returns {string} 格式化后的时间
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return '-'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch {
      return timestamp
    }
  },

  /**
   * 获取日志级别对应的颜色
   * @param {string} level - 日志级别
   * @returns {string} 对应的颜色类
   */
  getLogLevelColor(level) {
    const colors = {
      'ERROR': 'text-red-400',
      'WARNING': 'text-yellow-400',
      'INFO': 'text-blue-400',
      'DEBUG': 'text-gray-400',
      'CRITICAL': 'text-red-500'
    }
    return colors[level?.toUpperCase()] || 'text-gray-300'
  },

  /**
   * 获取日志类型的图标
   * @param {string} type - 日志类型
   * @returns {string} 对应的图标
   */
  getLogTypeIcon(type) {
    const icons = {
      'app': '📱',
      'error': '❌',
      'access': '📊',
      'system': '⚙️',
      'user': '👤',
      'database': '🗄️',
      'api': '🌐'
    }
    return icons[type] || '📄'
  }
}