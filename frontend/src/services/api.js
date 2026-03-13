import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    console.error('响应错误:', error)

    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.detail || error.response.data?.message || '请求失败'

      switch (status) {
        case 401:
          // Token 过期或无效
          if (error.config.url !== '/api/auth/login' && error.config.url !== '/api/auth/register') {
            // 尝试刷新 token
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken && !error.config._retry) {
              error.config._retry = true
              try {
                const response = await api.post('/api/auth/refresh', {
                  refresh_token: refreshToken
                })
                const { access_token } = response.data
                localStorage.setItem('access_token', access_token)
                error.config.headers.Authorization = `Bearer ${access_token}`
                return api(error.config)
              } catch (refreshError) {
                // 刷新失败，清除登录状态
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                localStorage.removeItem('user_info')
                localStorage.removeItem('user_permissions')
                window.location.href = '/login'
                return Promise.reject(refreshError)
              }
            } else {
              // 没有刷新令牌或已经重试过
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('user_info')
              localStorage.removeItem('user_permissions')
              window.location.href = '/login'
            }
          }
          break

        case 403:
          ElMessage.error('权限不足，无法访问')
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 422:
          // 表单验证错误
          if (error.response.data?.detail) {
            const details = error.response.data.detail
            if (Array.isArray(details)) {
              details.forEach(detail => {
                ElMessage.error(`${detail.loc?.join('.')} ${detail.msg}`)
              })
            } else {
              ElMessage.error(details)
            }
          } else {
            ElMessage.error('请求参数错误')
          }
          break

        case 500:
          ElMessage.error('服务器内部错误，请稍后重试')
          break

        default:
          ElMessage.error(message)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查连接')
    } else {
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default api