import api from './api'
import { ElMessage } from 'element-plus'

// 使用统一的api实例(已配置认证token)
const apiClient = api

export const documentService = {
  // 获取所有文档
  async getDocuments() {
    try {
      const response = await apiClient.get('/api/documents')
      return response.data || []
    } catch (error) {
      console.error('获取文档列表失败:', error)
      return []
    }
  },

  // 获取单个文档详情
  async getDocument(id) {
    try {
      const response = await apiClient.get(`/api/documents/${id}`)
      return response.data
    } catch (error) {
      console.error('获取文档详情失败:', error)
      return null
    }
  },

  // 上传文档
  async uploadDocuments(files, namespace = 'default', onProgress) {
    const results = []
    const filesArray = Array.from(files)
    let totalProgress = 0
    const totalSize = filesArray.reduce((sum, file) => sum + file.size, 0)
    let processedSize = 0

    try {
      for (const file of filesArray) {
        const formData = new FormData()
        formData.append('file', file) // 后端期望单个file字段
        formData.append('namespace', namespace) // 添加领域参数

        const response = await apiClient.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (onProgress) {
              const fileProgress = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              )
              const totalProgress = Math.round(
                ((processedSize + progressEvent.loaded) * 100) / totalSize
              )
              onProgress(totalProgress, processedSize + progressEvent.loaded, totalSize)
            }
          }
        })

        results.push({
          file: file.name,
          success: true,
          data: response
        })

        processedSize += file.size
      }

      return {
        success: true,
        results,
        totalFiles: filesArray.length,
        totalSize
      }
    } catch (error) {
      console.error('上传文档失败:', error)
      throw {
        success: false,
        error: error.message,
        results
      }
    }
  },

  // 删除文档
  async deleteDocument(id) {
    try {
      await apiClient.delete(`/api/documents/${id}`)
      return true
    } catch (error) {
      console.error('删除文档失败:', error)
      return false
    }
  },

  // 批量删除文档
  async deleteDocuments(ids) {
    try {
      await apiClient.post('/api/documents/batch', {
        data: { ids }
      })
      return true
    } catch (error) {
      console.error('批量删除文档失败:', error)
      return false
    }
  },

  // 下载文档功能在RAG系统中可能不可用，因为文档被处理成向量
  async downloadDocument(id, filename) {
    try {
      // RAG系统中通常不保留原始文件，只保留处理后的文本
      // 可以导出文本内容
      const doc = await this.getDocument(id)

      // 创建文本文件并下载
      const blob = new Blob([doc.content], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${doc.filename}_content.txt`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return true
    } catch (error) {
      console.error('导出文档内容失败:', error)
      return false
    }
  },

  // 搜索文档
  async searchDocuments(query, filters = {}) {
    try {
      const params = { query, ...filters }
      const response = await apiClient.get('/api/documents/search', { params })
      return response.data || []
    } catch (error) {
      console.error('搜索文档失败:', error)
      return []
    }
  },

  // 获取文档统计信息
  async getDocumentStats() {
    try {
      const response = await apiClient.get('/api/documents/stats')

      // 转换后端返回的数据结构（下划线->驼峰）
      if (response) {
        return {
          total: response.total || 0,
          byType: response.by_type || {},
          byStatus: response.by_status || {},
          recent: response.recent || 0
        }
      }

      return {
        total: 0,
        byType: {},
        byStatus: {},
        recent: 0
      }
    } catch (error) {
      console.error('获取文档统计失败:', error)
      return {
        total: 0,
        byType: {},
        byStatus: {},
        recent: 0
      }
    }
  },

  // 更新文档元数据
  async updateDocument(id, metadata) {
    try {
      const response = await apiClient.put(`/api/documents/${id}`, metadata)
      return response.data
    } catch (error) {
      console.error('更新文档元数据失败:', error)
      return null
    }
  },

  // 获取文档预览URL
  getPreviewUrl(id) {
    return `${API_BASE_URL}/api/documents/${id}/preview`
  },

  // 获取文档缩略图URL
  getThumbnailUrl(id) {
    return `${API_BASE_URL}/api/documents/${id}/thumbnail`
  }
}

export default documentService