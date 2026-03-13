/**
 * Dashboard数据服务
 * 提供Dashboard页面所需的所有API调用
 */
import api from './api'

/**
 * 获取Dashboard统计数据汇总
 * @returns {Promise} Dashboard统计数据
 */
export async function getDashboardStats() {
  try {
    const response = await api.get('/api/dashboard/stats')
    return response.data
  } catch (error) {
    console.error('获取Dashboard统计数据失败:', error)
    throw error
  }
}

/**
 * 获取文档列表
 * @param {Object} params - 查询参数
 * @param {number} params.limit - 返回数量限制
 * @returns {Promise} 文档列表
 */
export async function getDocuments(params = {}) {
  try {
    const response = await api.get('/api/documents', { params })
    return response.data
  } catch (error) {
    console.error('获取文档列表失败:', error)
    throw error
  }
}

/**
 * 获取聊天会话列表
 * @param {Object} params - 查询参数
 * @param {number} params.limit - 返回数量限制
 * @returns {Promise} 会话列表
 */
export async function getChatSessions(params = {}) {
  try {
    const response = await api.get('/api/chat/sessions', { params })
    return response.data
  } catch (error) {
    console.error('获取会话列表失败:', error)
    throw error
  }
}

/**
 * 获取查询历史
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @returns {Promise} 查询历史
 */
export async function getQueryHistory(params = {}) {
  try {
    const response = await api.get('/api/query/history', { params })
    return response.data
  } catch (error) {
    console.error('获取查询历史失败:', error)
    throw error
  }
}

/**
 * 获取用户列表
 * @returns {Promise} 用户列表
 */
export async function getUsers() {
  try {
    const response = await api.get('/api/users')
    return response.data
  } catch (error) {
    console.error('获取用户列表失败:', error)
    throw error
  }
}

export default {
  getDashboardStats,
  getDocuments,
  getChatSessions,
  getQueryHistory,
  getUsers
}
