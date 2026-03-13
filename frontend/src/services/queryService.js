/**
 * 查询服务 - 支持多领域智能检索
 *
 * 功能:
 * - 查询 API v2 调用
 * - 检索方法管理
 * - 结果格式化
 */
import api from './api'

/**
 * 查询文档 v2 (支持自动分类和多领域检索)
 *
 * @param {Object} params - 查询参数
 * @param {string} params.query - 查询内容
 * @param {string} [params.namespace] - 指定领域命名空间(可选)
 * @param {string} [params.retrievalMode='auto'] - 检索模式: 'auto'(自动), 'single'(单领域), 'cross'(跨领域)
 * @param {string} [params.retrievalMethod='hybrid'] - 检索方法: 'vector'(向量), 'bm25'(关键词), 'hybrid'(混合)
 * @param {Array<string>} [params.namespaces] - 跨领域检索时指定的领域列表
 * @param {number} [params.topK=10] - 返回结果数量
 * @param {number} [params.alpha=0.5] - 混合检索权重(0.0=纯BM25, 1.0=纯向量, 0.5=均衡)
 * @param {number} [params.similarityThreshold=0.0] - 相似度阈值(仅向量检索)
 * @param {string} [params.sessionId] - 会话ID
 * @returns {Promise<Object>} 查询响应
 */
export async function queryDocumentsV2(params) {
  try {
    const response = await api.post('/api/query/v2', {
      query: params.query,
      namespace: params.namespace || null,
      retrieval_mode: params.retrievalMode || 'auto',
      retrieval_method: params.retrievalMethod || 'hybrid',
      namespaces: params.namespaces || null,
      top_k: params.topK || 10,
      alpha: params.alpha !== undefined ? params.alpha : 0.5,
      similarity_threshold: params.similarityThreshold || 0.0,
      session_id: params.sessionId || null
    })

    return {
      success: true,
      data: response.data
    }
  } catch (error) {
    console.error('查询失败:', error)
    return {
      success: false,
      error: error.response?.data?.detail || error.message || '查询失败'
    }
  }
}

/**
 * 获取支持的检索方法
 *
 * @returns {Promise<Object>} 检索方法列表和说明
 */
export async function getRetrievalMethods() {
  try {
    const response = await api.get('/api/query/methods')
    return {
      success: true,
      data: response.data.data
    }
  } catch (error) {
    console.error('获取检索方法失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 测试查询功能
 *
 * @param {Object} params - 测试参数
 * @param {string} params.query - 查询内容
 * @param {string} [params.namespace] - 领域命名空间
 * @param {string} [params.method='hybrid'] - 检索方法
 * @returns {Promise<Object>} 测试结果
 */
export async function testQuery(params) {
  try {
    const response = await api.get('/api/query/test', {
      params: {
        query: params.query,
        namespace: params.namespace || null,
        method: params.method || 'hybrid'
      }
    })
    return {
      success: true,
      data: response.data
    }
  } catch (error) {
    console.error('测试查询失败:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

/**
 * 格式化查询结果用于展示
 *
 * @param {Object} queryResponse - 查询API响应
 * @returns {Object} 格式化后的结果
 */
export function formatQueryResults(queryResponse) {
  if (!queryResponse) return null

  const {
    query_id,
    query,
    domain_classification,
    retrieval_mode,
    retrieval_method,
    results,
    cross_domain_results,
    retrieval_stats
  } = queryResponse

  return {
    queryId: query_id,
    query,
    classification: domain_classification ? {
      namespace: domain_classification.namespace,
      displayName: domain_classification.display_name,
      confidence: domain_classification.confidence,
      method: domain_classification.method,
      alternatives: domain_classification.alternatives || []
    } : null,
    retrievalMode: retrieval_mode,
    retrievalMethod: retrieval_method,
    results: results.map(formatChunkResult),
    crossDomainResults: cross_domain_results?.map(formatDomainGroup) || null,
    stats: {
      totalCandidates: retrieval_stats.total_candidates,
      method: retrieval_stats.method,
      latencyMs: retrieval_stats.latency_ms,
      vectorCount: retrieval_stats.vector_count,
      bm25Count: retrieval_stats.bm25_count
    }
  }
}

/**
 * 格式化文档块结果
 *
 * @param {Object} chunk - 文档块
 * @returns {Object} 格式化后的文档块
 */
function formatChunkResult(chunk) {
  return {
    chunkId: chunk.chunk_id,
    content: chunk.content,
    score: chunk.score,
    namespace: chunk.namespace,
    domainDisplayName: chunk.domain_display_name,
    domainColor: chunk.domain_color || '#999999',
    domainIcon: chunk.domain_icon || 'folder',
    documentId: chunk.document_id,
    documentTitle: chunk.document_title,
    chunkIndex: chunk.chunk_index,
    metadata: chunk.metadata || {}
  }
}

/**
 * 格式化领域分组结果
 *
 * @param {Object} group - 领域分组
 * @returns {Object} 格式化后的领域分组
 */
function formatDomainGroup(group) {
  return {
    namespace: group.namespace,
    displayName: group.display_name,
    count: group.count,
    results: group.results.map(formatChunkResult)
  }
}

/**
 * 获取检索方法的显示信息
 *
 * @param {string} method - 检索方法名称
 * @returns {Object} 方法信息
 */
export function getMethodInfo(method) {
  const methodMap = {
    vector: {
      name: '向量检索',
      icon: '🔍',
      color: '#4A90E2',
      description: '基于语义相似度'
    },
    bm25: {
      name: '关键词检索',
      icon: '🔑',
      color: '#F5A623',
      description: '基于BM25算法'
    },
    hybrid: {
      name: '混合检索',
      icon: '⚡',
      color: '#7ED321',
      description: '向量+BM25融合(推荐)'
    }
  }

  return methodMap[method] || {
    name: method,
    icon: '❓',
    color: '#999999',
    description: '未知方法'
  }
}

/**
 * 获取检索模式的显示信息
 *
 * @param {string} mode - 检索模式名称
 * @returns {Object} 模式信息
 */
export function getModeInfo(mode) {
  const modeMap = {
    auto: {
      name: '自动模式',
      icon: '🤖',
      color: '#9013FE',
      description: '自动识别领域并选择策略'
    },
    single: {
      name: '单领域模式',
      icon: '🎯',
      color: '#4A90E2',
      description: '在指定领域内精确检索'
    },
    cross: {
      name: '跨领域模式',
      icon: '🌐',
      color: '#F5A623',
      description: '在多个领域中检索并融合'
    }
  }

  return modeMap[mode] || {
    name: mode,
    icon: '❓',
    color: '#999999',
    description: '未知模式'
  }
}

/**
 * 高亮文本中的关键词
 *
 * @param {string} text - 原始文本
 * @param {string} query - 查询关键词
 * @returns {string} 高亮后的HTML
 */
export function highlightKeywords(text, query) {
  if (!text || !query) return text

  // 分词(简单按空格分)
  const keywords = query.split(/\s+/).filter(k => k.length > 0)

  let highlightedText = text
  keywords.forEach(keyword => {
    // 使用正则表达式进行大小写不敏感的匹配
    const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi')
    highlightedText = highlightedText.replace(
      regex,
      '<mark class="highlight">$1</mark>'
    )
  })

  return highlightedText
}

/**
 * 转义正则表达式特殊字符
 *
 * @param {string} string - 原始字符串
 * @returns {string} 转义后的字符串
 */
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 计算置信度等级
 *
 * @param {number} confidence - 置信度(0-1)
 * @returns {Object} 等级信息
 */
export function getConfidenceLevel(confidence) {
  if (confidence >= 0.8) {
    return {
      level: 'high',
      text: '高',
      color: '#7ED321',
      description: '强烈推荐该领域'
    }
  } else if (confidence >= 0.6) {
    return {
      level: 'medium',
      text: '中',
      color: '#F5A623',
      description: '推荐该领域'
    }
  } else {
    return {
      level: 'low',
      text: '低',
      color: '#D0021B',
      description: '可能不在该领域'
    }
  }
}

export default {
  queryDocumentsV2,
  getRetrievalMethods,
  testQuery,
  formatQueryResults,
  getMethodInfo,
  getModeInfo,
  highlightKeywords,
  getConfidenceLevel
}
