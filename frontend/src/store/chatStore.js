import { defineStore } from 'pinia'
import api from '@/services/api'

// API 基础URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8800'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    activeSessionId: null,
    messages: {},
    eventSource: null,
    isGenerating: false
  }),

  getters: {
    currentSession: (state) => {
      return state.sessions.find(s => s.session_id === state.activeSessionId)
    },

    currentMessages: (state) => {
      return state.messages[state.activeSessionId] || []
    }
  },

  actions: {
    async loadSessions() {
      try {
        const response = await api.get('/api/chat/sessions')
        this.sessions = response.data

        // 如果没有活动会话，选择第一个
        if (!this.activeSessionId && this.sessions.length > 0) {
          this.activeSessionId = this.sessions[0].session_id
          await this.loadMessages(this.activeSessionId)
        }
      } catch (error) {
        console.error('Failed to load sessions:', error)
      }
    },

    async createSession(title = '新对话') {
      try {
        const response = await api.post('/api/chat/sessions', {
          title
        })
        const session = response.data
        this.sessions.unshift(session)
        this.activeSessionId = session.session_id
        this.messages[session.session_id] = []
        return session
      } catch (error) {
        console.error('Failed to create session:', error)
        return null
      }
    },

    async selectSession(sessionId) {
      this.activeSessionId = sessionId
      if (!this.messages[sessionId]) {
        await this.loadMessages(sessionId)
      }
    },

    async loadMessages(sessionId) {
      try {
        const response = await api.get(
          `/api/chat/sessions/${sessionId}/messages`
        )
        this.messages[sessionId] = response.data
      } catch (error) {
        console.error('Failed to load messages:', error)
        this.messages[sessionId] = []
      }
    },

    async sendMessage({ message, model = 'gpt-3.5-turbo', useRAG = true, stream = true, namespace = null }) {
      // 确保有活动会话
      if (!this.activeSessionId) {
        const session = await this.createSession(message.substring(0, 30))
        if (!session) return
      }

      // 添加用户消息到界面
      const userMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      }

      if (!this.messages[this.activeSessionId]) {
        this.messages[this.activeSessionId] = []
      }
      this.messages[this.activeSessionId].push(userMessage)

      // 准备助手消息
      const assistantMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }
      this.messages[this.activeSessionId].push(assistantMessage)
      const messageIndex = this.messages[this.activeSessionId].length - 1

      if (stream) {
        // 流式响应
        this.isGenerating = true
        const params = {
          session_id: this.activeSessionId,
          message: message,
          use_rag: useRAG,
          stream: true,
          model: model
        }

        // 如果指定了领域,添加到参数中
        if (namespace) {
          params.namespace = namespace
        }

        const eventSource = new EventSource(
          `${API_BASE_URL}/api/chat/send?` + new URLSearchParams(params)
        )

        this.eventSource = eventSource

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data)
          if (data.type === 'content') {
            this.messages[this.activeSessionId][messageIndex].content += data.content
          } else if (data.type === 'done') {
            this.isGenerating = false
            eventSource.close()
            this.eventSource = null

            // 【刷新会话列表】消息完成后刷新会话列表以更新标题
            setTimeout(() => {
              this.loadSessions()
            }, 800) // 延迟800ms确保后端标题已生成
          } else if (data.type === 'error') {
            console.error('Stream error:', data.error)
            this.isGenerating = false
            eventSource.close()
            this.eventSource = null
          }
        }

        eventSource.onerror = (error) => {
          console.error('EventSource error:', error)
          this.isGenerating = false
          eventSource.close()
          this.eventSource = null
        }
      } else {
        // 非流式响应
        try {
          const requestData = {
            session_id: this.activeSessionId,
            message,
            use_rag: useRAG,
            stream: false,
            model
          }

          // 如果指定了领域,添加到请求数据中
          if (namespace) {
            requestData.namespace = namespace
          }

          const response = await api.post('/api/chat/send', requestData)

          this.messages[this.activeSessionId][messageIndex].content = response.data.message

          // 【刷新会话列表】非流式响应完成后也刷新会话列表
          setTimeout(() => {
            this.loadSessions()
          }, 500)
        } catch (error) {
          console.error('Failed to send message:', error)
          this.messages[this.activeSessionId][messageIndex].content = '发送失败，请重试'
        }
      }
    },

    stopGeneration() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
        this.isGenerating = false
      }
    },

    async deleteSession(sessionId) {
      try {
        await api.delete(`/api/chat/sessions/${sessionId}`)
        const index = this.sessions.findIndex(s => s.session_id === sessionId)
        if (index !== -1) {
          this.sessions.splice(index, 1)
        }

        delete this.messages[sessionId]

        if (this.activeSessionId === sessionId) {
          this.activeSessionId = this.sessions[0]?.session_id || null
          if (this.activeSessionId) {
            await this.loadMessages(this.activeSessionId)
          }
        }
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
  }
})