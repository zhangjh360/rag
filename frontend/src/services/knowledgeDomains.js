/**
 * 知识领域管理 API 服务
 * 提供知识领域的 CRUD 操作和统计功能
 */
import api from './api'

/**
 * 获取所有知识领域
 * @param {Object} params - 查询参数
 * @param {boolean} params.include_inactive - 是否包含未启用的领域
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的最大记录数
 * @param {boolean} params.with_stats - 是否包含统计信息
 * @returns {Promise<{domains: Array, total: number}>}
 */
export const getAllDomains = async (params = {}) => {
  const response = await api.get('/api/knowledge-domains', { params })
  return response.data
}

/**
 * 根据命名空间获取单个领域
 * @param {string} namespace - 领域命名空间
 * @returns {Promise<Object>} 领域详情
 */
export const getDomainByNamespace = async (namespace) => {
  const response = await api.get(`/api/knowledge-domains/${namespace}`)
  return response.data
}

/**
 * 创建新的知识领域
 * @param {Object} domainData - 领域数据
 * @param {string} domainData.namespace - 命名空间 (必填)
 * @param {string} domainData.display_name - 显示名称 (必填)
 * @param {string} domainData.description - 描述
 * @param {Array<string>} domainData.keywords - 关键词列表
 * @param {string} domainData.icon - 图标标识
 * @param {string} domainData.color - 主题色
 * @param {boolean} domainData.is_active - 是否启用
 * @param {number} domainData.priority - 优先级
 * @param {Object} domainData.permissions - 权限配置
 * @param {Object} domainData.metadata - 扩展元数据
 * @returns {Promise<Object>} 创建的领域
 */
export const createDomain = async (domainData) => {
  const response = await api.post('/api/knowledge-domains', domainData)
  return response.data
}

/**
 * 更新知识领域
 * @param {string} namespace - 领域命名空间
 * @param {Object} domainData - 更新的数据 (所有字段可选)
 * @returns {Promise<Object>} 更新后的领域
 */
export const updateDomain = async (namespace, domainData) => {
  const response = await api.put(`/api/knowledge-domains/${namespace}`, domainData)
  return response.data
}

/**
 * 删除知识领域
 * @param {string} namespace - 领域命名空间
 * @param {boolean} force - 是否强制删除 (即使有关联文档)
 * @returns {Promise<void>}
 */
export const deleteDomain = async (namespace, force = false) => {
  await api.delete(`/api/knowledge-domains/${namespace}`, {
    params: { force }
  })
}

/**
 * 获取知识领域统计信息
 * @param {string} namespace - 领域命名空间
 * @returns {Promise<Object>} 统计信息
 */
export const getDomainStats = async (namespace) => {
  const response = await api.get(`/api/knowledge-domains/${namespace}/stats`)
  return response.data
}

/**
 * 搜索知识领域
 * @param {string} keyword - 搜索关键词
 * @param {boolean} includeInactive - 是否包含未启用的领域
 * @returns {Promise<Array>} 匹配的领域列表
 */
export const searchDomains = async (keyword, includeInactive = false) => {
  const response = await api.get(`/api/knowledge-domains/search/${keyword}`, {
    params: { include_inactive: includeInactive }
  })
  return response.data
}

/**
 * 获取活跃的领域列表 (用于选择器)
 * @returns {Promise<Array>} 活跃的领域列表
 */
export const getActiveDomains = async () => {
  const response = await getAllDomains({
    include_inactive: false,
    limit: 100
  })
  return response.domains
}

/**
 * 批量更新领域优先级
 * @param {Array} domains - 领域列表 [{namespace: string, priority: number}]
 * @returns {Promise<Array>} 更新后的领域列表
 */
export const batchUpdatePriorities = async (domains) => {
  const response = await api.put('/api/knowledge-domains/batch-priority', { domains })
  return response.data
}

/**
 * 获取领域关系图数据
 * @param {string} namespace - 可选，指定领域命名空间
 * @returns {Promise<Object>} 关系图数据
 */
export const getDomainRelations = async (namespace = null) => {
  const url = namespace ? `/api/knowledge-domains/${namespace}/relations` : '/api/knowledge-domains/relations'
  const response = await api.get(url)
  return response.data
}

/**
 * 导出领域数据
 * @param {string} namespace - 可选，指定领域命名空间
 * @param {string} format - 导出格式 (json, csv)
 * @returns {Promise<Blob>} 导出的文件数据
 */
export const exportDomains = async (namespace = null, format = 'json') => {
  const url = namespace ? `/api/knowledge-domains/${namespace}/export` : '/api/knowledge-domains/export'
  const response = await api.get(url, {
    params: { format },
    responseType: 'blob'
  })
  return response.data
}

/**
 * 导入领域数据
 * @param {FormData} formData - 包含文件的表单数据
 * @returns {Promise<Object>} 导入结果
 */
export const importDomains = async (formData) => {
  const response = await api.post('/api/knowledge-domains/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export default {
  getAllDomains,
  getDomainByNamespace,
  createDomain,
  updateDomain,
  deleteDomain,
  getDomainStats,
  searchDomains,
  getActiveDomains,
  batchUpdatePriorities,
  getDomainRelations,
  exportDomains,
  importDomains
}
