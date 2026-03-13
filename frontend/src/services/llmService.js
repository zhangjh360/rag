import api from './api'

// 使用统一的api实例(已配置认证token)
const apiClient = api

export const llmService = {
  /**
   * 获取所有可用的LLM模型
   */
  async getAllModels() {
    try {
      const response = await apiClient.get('/api/llm/models')
      return response.data || []
    } catch (error) {
      console.error('获取模型列表失败:', error)
      // 返回默认模型作为后备
      return [
        {
          id: 1,
          name: 'gpt-3.5-turbo',
          display_name: 'GPT-3.5',
          provider: 'openai',
          model_type: 'chat'
        },
        {
          id: 2,
          name: 'gpt-4',
          display_name: 'GPT-4',
          provider: 'openai',
          model_type: 'chat'
        },
        {
          id: 3,
          name: 'gpt-4o',
          display_name: 'GPT-4o',
          provider: 'openai',
          model_type: 'chat'
        },
        {
          id: 4,
          name: 'glm-4',
          display_name: 'GLM-4',
          provider: 'zhipuai',
          model_type: 'chat'
        }
      ]
    }
  },

  /**
   * 获取模型组
   */
  async getModelGroups() {
    try {
      const response = await apiClient.get('/api/llm/groups')
      return response.data || []
    } catch (error) {
      console.error('获取模型组失败:', error)
      return []
    }
  },

  /**
   * 根据提供商过滤模型
   */
  getModelsByProvider(models, provider) {
    return models.filter(model => model.provider === provider)
  },

  /**
   * 获取聊天模型（所有模型都是聊天模型，直接返回）
   */
  getChatModels(models) {
    return models
  },

  /**
   * 格式化模型选项用于下拉框
   */
  formatModelOptions(models) {
    return models.map(model => ({
      label: model.display_name || model.name,
      value: model.name,
      provider: model.provider,
      type: model.model_type || model.type
    }))
  },

  /**
   * 按提供商分组的模型选项
   */
  getGroupedModelOptions(models) {
    const providers = {}
    models.forEach(model => {
      const provider = model.provider || '其他'
      if (!providers[provider]) {
        providers[provider] = []
      }
      providers[provider].push({
        label: model.display_name || model.name,
        value: model.name,
        type: model.model_type || model.type
      })
    })

    return providers
  }
}

export default llmService
