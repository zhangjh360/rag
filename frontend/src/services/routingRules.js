/**
 * 路由规则管理 API 服务
 * 提供路由规则的 CRUD 操作和匹配测试功能
 */
import api from './api'

/**
 * 获取所有路由规则
 * @param {Object} params - 查询参数
 * @param {boolean} params.include_inactive - 是否包含未激活的规则
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的最大记录数
 * @returns {Promise<{rules: Array, total: number}>}
 */
export const getAllRules = async (params = {}) => {
  const response = await api.get('/api/routing-rules', { params })
  return response.data
}

/**
 * 根据ID获取单个路由规则
 * @param {number} ruleId - 规则ID
 * @returns {Promise<Object>} 规则详情
 */
export const getRuleById = async (ruleId) => {
  const response = await api.get(`/api/routing-rules/${ruleId}`)
  return response.data
}

/**
 * 创建新的路由规则
 * @param {Object} ruleData - 规则数据
 * @param {string} ruleData.rule_name - 规则名称 (必填)
 * @param {string} ruleData.rule_type - 规则类型: keyword/regex/pattern (必填)
 * @param {string} ruleData.pattern - 匹配模式 (必填)
 * @param {string} ruleData.target_namespace - 目标领域命名空间 (必填)
 * @param {number} ruleData.confidence_threshold - 置信度阈值 (0.0-1.0)
 * @param {number} ruleData.priority - 优先级 (数值越大优先级越高)
 * @param {boolean} ruleData.is_active - 是否激活
 * @param {Object} ruleData.metadata - 元数据
 * @returns {Promise<Object>} 创建的规则
 */
export const createRule = async (ruleData) => {
  const response = await api.post('/api/routing-rules', ruleData)
  return response.data
}

/**
 * 更新路由规则
 * @param {number} ruleId - 规则ID
 * @param {Object} updateData - 更新数据 (部分字段)
 * @returns {Promise<Object>} 更新后的规则
 */
export const updateRule = async (ruleId, updateData) => {
  const response = await api.put(`/api/routing-rules/${ruleId}`, updateData)
  return response.data
}

/**
 * 删除路由规则
 * @param {number} ruleId - 规则ID
 * @returns {Promise<void>}
 */
export const deleteRule = async (ruleId) => {
  await api.delete(`/api/routing-rules/${ruleId}`)
}

/**
 * 测试路由规则匹配
 * @param {Object} matchRequest - 匹配请求
 * @param {string} matchRequest.query - 查询文本
 * @param {number} matchRequest.min_confidence - 最小置信度 (0.0-1.0)
 * @returns {Promise<Object>} 匹配结果
 */
export const testRuleMatch = async (matchRequest) => {
  const response = await api.post('/api/routing-rules/match', matchRequest)
  return response.data
}

/**
 * 规则类型选项
 */
export const RULE_TYPES = [
  { value: 'keyword', label: '关键词匹配', description: '使用 | 分隔多个关键词' },
  { value: 'regex', label: '正则表达式', description: '支持完整的正则表达式语法' },
  { value: 'pattern', label: '通配符模式', description: '支持 * 和 ? 通配符' }
]

/**
 * 获取规则类型标签
 */
export const getRuleTypeLabel = (ruleType) => {
  const type = RULE_TYPES.find(t => t.value === ruleType)
  return type ? type.label : ruleType
}

/**
 * 获取规则类型描述
 */
export const getRuleTypeDescription = (ruleType) => {
  const type = RULE_TYPES.find(t => t.value === ruleType)
  return type ? type.description : ''
}
