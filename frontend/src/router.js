import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './store/auth'
import { ElMessage } from 'element-plus'

// 路由配置
const routes = [
  // 公共路由
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: '登录'
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('./views/Register.vue'),
    meta: {
      requiresAuth: false,
      title: '注册'
    }
  },

  // 需要认证的路由
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue'),
    meta: {
      requiresAuth: true,
      title: '仪表盘',
      permissions: ['query_ask']
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('./views/Chat.vue'),
    meta: {
      requiresAuth: true,
      title: '智能对话',
      permissions: ['query_ask']
    }
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('./views/Documents.vue'),
    meta: {
      requiresAuth: true,
      title: '文档管理',
      permissions: ['document_read']
    }
  },
  {
    path: '/index-management',
    name: 'IndexManagement',
    component: () => import('./views/IndexManagement.vue'),
    meta: {
      requiresAuth: true,
      title: '索引管理',
      permissions: ['document_write']
    }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('./views/History.vue'),
    meta: {
      requiresAuth: true,
      title: '查询历史',
      permissions: ['query_history']
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('./views/Profile.vue'),
    meta: {
      requiresAuth: true,
      title: '个人中心'
    }
  },

  // 管理员路由
  {
    path: '/performance',
    name: 'Performance',
    component: () => import('./views/Performance.vue'),
    meta: {
      requiresAuth: true,
      title: '性能监控',
      permissions: ['system_settings']
    }
  },
  {
    path: '/knowledge-domains',
    name: 'KnowledgeDomains',
    component: () => import('./views/KnowledgeDomains.vue'),
    meta: {
      requiresAuth: true,
      title: '知识领域管理',
      permissions: ['system_settings']
    }
  },
  {
    path: '/routing-rules',
    name: 'RoutingRules',
    component: () => import('./views/RoutingRules.vue'),
    meta: {
      requiresAuth: true,
      title: '路由规则管理',
      permissions: ['system_settings']
    }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('./views/Logs.vue'),
    meta: {
      requiresAuth: true,
      title: '系统日志',
      permissions: ['system_settings']
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./views/Settings.vue'),
    meta: {
      requiresAuth: true,
      title: '系统设置',
      permissions: ['system_settings']
    }
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: () => import('./views/admin/UserManagement.vue'),
    meta: {
      requiresAuth: true,
      title: '用户管理',
      permissions: ['user_management']
    }
  },
  {
    path: '/role-management',
    name: 'RoleManagement',
    component: () => import('./views/admin/RoleManagement.vue'),
    meta: {
      requiresAuth: true,
      title: '角色管理',
      permissions: ['role_management']
    }
  },

  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('./views/NotFound.vue'),
    meta: {
      requiresAuth: false,
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - RAG 智能问答系统`
  }

  // 初始化认证状态
  if (!authStore.token && localStorage.getItem('access_token')) {
    authStore.initializeAuth()
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 检查权限
    if (to.meta.permissions) {
      const hasPermission = authStore.hasAnyPermission(to.meta.permissions)
      if (!hasPermission) {
        ElMessage.error('您没有权限访问此页面')
        next('/dashboard')
        return
      }
    }
  }

  // 如果已登录用户访问登录/注册页面，重定向到仪表盘
  if (authStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/dashboard')
    return
  }

  next()
})

// API 错误处理
router.onError((error) => {
  console.error('路由错误:', error)

  // 如果是认证相关错误，清除登录状态
  if (error.response?.status === 401) {
    const authStore = useAuthStore()
    authStore.logout()
    router.push('/login')
  }
})

export default router