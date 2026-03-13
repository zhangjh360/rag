import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('user_permissions') || '[]'))

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isUser = computed(() => user.value?.role === 'user')
  const isReadonly = computed(() => user.value?.role === 'readonly')

  // 登录
  const login = async (credentials) => {
    try {
      const response = await apiService.post('/api/auth/login', credentials)
      const data = response.data

      if (data.access_token) {
        // 存储令牌
        token.value = data.access_token
        refreshToken.value = data.refresh_token
        user.value = data.user
        permissions.value = data.user.permissions || []

        // 持久化存储
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        localStorage.setItem('user_info', JSON.stringify(data.user))
        localStorage.setItem('user_permissions', JSON.stringify(data.user.permissions || []))

        // 设置API默认头部
        apiService.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

        return { success: true, message: '登录成功' }
      } else {
        return { success: false, message: '登录失败' }
      }
    } catch (error) {
      console.error('登录错误:', error)
      const message = error.response?.data?.detail || '登录失败，请检查用户名和密码'
      return { success: false, message }
    }
  }

  // 注册
  const register = async (userData) => {
    try {
      const response = await apiService.post('/api/auth/register', userData)
      const data = response.data

      if (data.access_token) {
        // 自动登录
        token.value = data.access_token
        refreshToken.value = data.refresh_token
        user.value = data.user
        permissions.value = data.user.permissions || []

        // 持久化存储
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        localStorage.setItem('user_info', JSON.stringify(data.user))
        localStorage.setItem('user_permissions', JSON.stringify(data.user.permissions || []))

        // 设置API默认头部
        apiService.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

        return { success: true, message: '注册成功' }
      } else {
        return { success: false, message: '注册失败' }
      }
    } catch (error) {
      console.error('注册错误:', error)
      const message = error.response?.data?.detail || '注册失败，请稍后重试'
      return { success: false, message }
    }
  }

  // 登出
  const logout = async () => {
    try {
      // 通知服务器登出
      if (token.value) {
        await apiService.post('/api/auth/logout')
      }
    } catch (error) {
      console.error('登出通知失败:', error)
    } finally {
      // 清除本地数据
      token.value = null
      refreshToken.value = null
      user.value = null
      permissions.value = []

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      localStorage.removeItem('user_permissions')

      // 清除API头部
      delete apiService.defaults.headers.common['Authorization']
    }
  }

  // 刷新令牌
  const refreshAccessToken = async () => {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }

      const response = await apiService.post('/api/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const data = response.data
      if (data.access_token) {
        token.value = data.access_token
        localStorage.setItem('access_token', data.access_token)
        apiService.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        return true
      }
      return false
    } catch (error) {
      console.error('刷新令牌失败:', error)
      await logout() // 刷新失败时登出
      return false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const response = await apiService.get('/api/auth/me')
      const data = response.data

      user.value = data
      permissions.value = data.permissions || []

      localStorage.setItem('user_info', JSON.stringify(data))
      localStorage.setItem('user_permissions', JSON.stringify(data.permissions || []))

      return data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    }
  }

  // 修改密码
  const changePassword = async (passwordData) => {
    try {
      const response = await apiService.post('/api/auth/change-password', passwordData)
      return { success: true, message: '密码修改成功' }
    } catch (error) {
      console.error('修改密码失败:', error)
      const message = error.response?.data?.detail || '密码修改失败'
      return { success: false, message }
    }
  }

  // 检查权限
  const hasPermission = (permission) => {
    return permissions.value.includes(permission)
  }

  // 检查多个权限（需要全部满足）
  const hasAllPermissions = (permissionList) => {
    return permissionList.every(permission => permissions.value.includes(permission))
  }

  // 检查多个权限（满足其中一个即可）
  const hasAnyPermission = (permissionList) => {
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  // 初始化认证状态
  const initializeAuth = () => {
    const savedToken = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('user_info')
    const savedPermissions = localStorage.getItem('user_permissions')

    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
      permissions.value = JSON.parse(savedPermissions || '[]')

      // 设置API默认头部
      apiService.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
    }
  }

  // 更新用户信息
  const updateUser = (newUserInfo) => {
    user.value = { ...user.value, ...newUserInfo }
    localStorage.setItem('user_info', JSON.stringify(user.value))
  }

  return {
    // 状态
    token,
    refreshToken,
    user,
    permissions,

    // 计算属性
    isAuthenticated,
    isAdmin,
    isUser,
    isReadonly,

    // 方法
    login,
    register,
    logout,
    refreshAccessToken,
    getCurrentUser,
    changePassword,
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    initializeAuth,
    updateUser
  }
})