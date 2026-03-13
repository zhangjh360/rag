import { defineStore } from 'pinia'
import api from '@/services/api'

export const useRagStore = defineStore('rag', {
  state: () => ({
    documents: [],
    queryHistory: [],
    chatHistory: [],
    activeHistoryTab: 'chat', // 'chat' 或 'query'
    currentQuery: '',
    currentResponse: '',
    currentSources: [],
    loading: false,
    uploading: false,
    // 分页相关
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
      totalPages: 0
    }
  }),

  getters: {
    hasNextPage: (state) => state.pagination.page < state.pagination.totalPages,
    hasPrevPage: (state) => state.pagination.page > 1
  },

  actions: {
    async uploadDocument(file) {
      this.uploading = true
      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        await this.fetchDocuments()
        return response.data
      } catch (error) {
        console.error('Upload failed:', error)
        throw error
      } finally {
        this.uploading = false
      }
    },

    async fetchDocuments() {
      try {
        const response = await api.get('/api/documents')
        this.documents = response.data
      } catch (error) {
        console.error('Failed to fetch documents:', error)
      }
    },

    async queryDocuments(query) {
      this.loading = true
      this.currentQuery = query
      try {
        const response = await api.post('/api/query', { query })
        this.currentResponse = response.data.response
        this.currentSources = response.data.sources

        await this.fetchQueryHistory(1, this.pagination.pageSize)
        return response.data
      } catch (error) {
        console.error('Query failed:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchQueryHistory(page = 1, pageSize = 20) {
      try {
        this.loading = true
        const response = await api.get('/api/query/history', {
          params: { page, page_size: pageSize }
        })

        this.queryHistory = response.data.data
        this.pagination = {
          page: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total,
          totalPages: response.data.total_pages
        }
      } catch (error) {
        console.error('Failed to fetch query history:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchChatHistory(page = 1, pageSize = 20) {
      try {
        this.loading = true
        const response = await api.get('/api/chat/history', {
          params: { page, page_size: pageSize }
        })

        this.chatHistory = response.data.data
        this.pagination = {
          page: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total,
          totalPages: response.data.total_pages
        }
      } catch (error) {
        console.error('Failed to fetch chat history:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async goToPage(page) {
      if (page < 1 || page > this.pagination.totalPages) {
        return
      }
      await this.fetchQueryHistory(page, this.pagination.pageSize)
    },

    async nextPage() {
      if (this.hasNextPage) {
        await this.fetchQueryHistory(this.pagination.page + 1, this.pagination.pageSize)
      }
    },

    async prevPage() {
      if (this.hasPrevPage) {
        await this.fetchQueryHistory(this.pagination.page - 1, this.pagination.pageSize)
      }
    },

    // 设置管理
    async fetchSettings() {
      try {
        const response = await api.get('/api/settings')
        return response.data
      } catch (error) {
        console.error('Failed to fetch settings:', error)
        throw error
      }
    },

    async updateSettings(type, settings) {
      try {
        const response = await api.put(`/api/settings/${type}`, settings)
        return response.data
      } catch (error) {
        console.error(`Failed to update ${type} settings:`, error)
        throw error
      }
    },

    // LLM模型管理
    async fetchLLMConfig() {
      try {
        const response = await api.get('/api/llm/config')
        return response.data
      } catch (error) {
        console.error('Failed to fetch LLM config:', error)
        throw error
      }
    },

    // 模型分组管理
    async fetchLLMGroups() {
      try {
        const response = await api.get('/api/llm/groups')
        return response.data
      } catch (error) {
        console.error('Failed to fetch LLM groups:', error)
        throw error
      }
    },

    async createLLMGroup(groupData) {
      try {
        const response = await api.post('/api/llm/groups', groupData)
        return response.data
      } catch (error) {
        console.error('Failed to create LLM group:', error)
        throw error
      }
    },

    async updateLLMGroup(groupId, groupData) {
      try {
        const response = await api.put(`/api/llm/groups/${groupId}`, groupData)
        return response.data
      } catch (error) {
        console.error('Failed to update LLM group:', error)
        throw error
      }
    },

    async deleteLLMGroup(groupId) {
      try {
        const response = await api.delete(`/api/llm/groups/${groupId}`)
        return response.data
      } catch (error) {
        console.error('Failed to delete LLM group:', error)
        throw error
      }
    },

    // 模型管理
    async fetchLLMModels() {
      try {
        const response = await api.get('/api/llm/models')
        return response.data
      } catch (error) {
        console.error('Failed to fetch LLM models:', error)
        throw error
      }
    },

    async createLLMModel(modelData) {
      try {
        const response = await api.post('/api/llm/models', modelData)
        return response.data
      } catch (error) {
        console.error('Failed to create LLM model:', error)
        throw error
      }
    },

    async updateLLMModel(modelId, modelData) {
      try {
        const response = await api.put(`/api/llm/models/${modelId}`, modelData)
        return response.data
      } catch (error) {
        console.error('Failed to update LLM model:', error)
        throw error
      }
    },

    async deleteLLMModel(modelId) {
      try {
        const response = await api.delete(`/api/llm/models/${modelId}`)
        return response.data
      } catch (error) {
        console.error('Failed to delete LLM model:', error)
        throw error
      }
    },

    // 场景管理
    async fetchLLMScenarios() {
      try {
        const response = await api.get('/api/llm/scenarios')
        return response.data
      } catch (error) {
        console.error('Failed to fetch LLM scenarios:', error)
        throw error
      }
    },

    async createLLMScenario(scenarioData) {
      try {
        const response = await api.post('/api/llm/scenarios', scenarioData)
        return response.data
      } catch (error) {
        console.error('Failed to create LLM scenario:', error)
        throw error
      }
    },

    async updateLLMScenario(scenarioId, scenarioData) {
      try {
        const response = await api.put(`/api/llm/scenarios/${scenarioId}`, scenarioData)
        return response.data
      } catch (error) {
        console.error('Failed to update LLM scenario:', error)
        throw error
      }
    },

    async deleteLLMScenario(scenarioId) {
      try {
        const response = await api.delete(`/api/llm/scenarios/${scenarioId}`)
        return response.data
      } catch (error) {
        console.error('Failed to delete LLM scenario:', error)
        throw error
      }
    }
  }
})