<template>
  <div class="profile-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <div class="profile-content">
      <!-- 用户信息卡片 -->
      <div class="profile-header-card">
        <div class="profile-avatar-section">
          <div class="avatar-container">
            <div class="tech-avatar" :class="roleAvatarClass">
              <span class="avatar-text">{{ userInitial }}</span>
              <div class="avatar-ring"></div>
            </div>
          </div>
          <div class="profile-info">
            <h1 class="username">{{ authStore.user?.username || 'Unknown' }}</h1>
            <div class="user-role" :class="roleTextClass">
              <i class="el-icon-medal role-icon"></i>
              {{ roleText }}
            </div>
            <div class="user-email">{{ authStore.user?.email || 'N/A' }}</div>
          </div>
        </div>

        <!-- 账户状态 -->
        <div class="account-status">
          <div class="status-item">
            <div class="status-label">账户状态</div>
            <div class="status-value" :class="accountStatusClass">
              <div class="status-dot" :class="statusDotClass"></div>
              {{ accountStatusText }}
            </div>
          </div>
          <div class="status-item">
            <div class="status-label">注册时间</div>
            <div class="status-value">{{ formatDate(authStore.user?.created_at) }}</div>
          </div>
          <div class="status-item">
            <div class="status-label">最后登录</div>
            <div class="status-value">{{ formatDate(authStore.user?.last_login) }}</div>
          </div>
        </div>
      </div>

      <!-- 功能选项卡 -->
      <div class="profile-tabs">
        <el-tabs v-model="activeTab" class="tech-tabs">
          <!-- 个人信息 -->
          <el-tab-pane label="个人信息" name="profile">
            <div class="tab-content">
              <div class="info-section">
                <h3 class="section-title">基本信息</h3>
                <div class="info-grid">
                  <div class="info-item">
                    <label>用户名</label>
                    <div class="info-value">{{ authStore.user?.username }}</div>
                  </div>
                  <div class="info-item">
                    <label>邮箱地址</label>
                    <div class="info-value">{{ authStore.user?.email }}</div>
                  </div>
                  <div class="info-item">
                    <label>用户角色</label>
                    <div class="info-value" :class="roleTextClass">{{ roleText }}</div>
                  </div>
                  <div class="info-item">
                    <label>用户ID</label>
                    <div class="info-value">#{{ authStore.user?.id }}</div>
                  </div>
                </div>
              </div>

              <div class="info-section">
                <h3 class="section-title">权限信息</h3>
                <div class="permissions-list">
                  <div class="permission-category" v-for="category in permissionCategories" :key="category.name">
                    <div class="category-header">
                      <i :class="category.icon"></i>
                      <span>{{ category.name }}</span>
                    </div>
                    <div class="permission-tags">
                      <el-tag
                        v-for="permission in category.permissions"
                        :key="permission.key"
                        :type="permission.has ? 'success' : 'info'"
                        size="small"
                        effect="plain"
                      >
                        {{ permission.name }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 安全设置 -->
          <el-tab-pane label="安全设置" name="security">
            <div class="tab-content">
              <div class="security-section">
                <h3 class="section-title">修改密码</h3>
                <el-form
                  ref="passwordForm"
                  :model="passwordForm"
                  :rules="passwordRules"
                  label-width="100px"
                  class="password-form"
                >
                  <el-form-item label="当前密码" prop="old_password">
                    <el-input
                      v-model="passwordForm.old_password"
                      type="password"
                      placeholder="请输入当前密码"
                      show-password
                      class="tech-input"
                    />
                  </el-form-item>
                  <el-form-item label="新密码" prop="new_password">
                    <el-input
                      v-model="passwordForm.new_password"
                      type="password"
                      placeholder="请输入新密码"
                      show-password
                      class="tech-input"
                      @input="checkPasswordStrength"
                    />
                    <div class="password-strength" v-if="passwordForm.new_password">
                      <div class="strength-bar">
                        <div
                          class="strength-fill"
                          :class="passwordStrengthClass"
                          :style="{ width: passwordStrengthWidth + '%' }"
                        ></div>
                      </div>
                      <div class="strength-text" :class="passwordStrengthClass">
                        密码强度：{{ passwordStrengthText }}
                      </div>
                    </div>
                  </el-form-item>
                  <el-form-item label="确认密码" prop="confirm_password">
                    <el-input
                      v-model="passwordForm.confirm_password"
                      type="password"
                      placeholder="请再次输入新密码"
                      show-password
                      class="tech-input"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="primary"
                      :loading="passwordLoading"
                      @click="handleChangePassword"
                      class="tech-button"
                    >
                      修改密码
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>

              <div class="security-section">
                <h3 class="section-title">登录历史</h3>
                <div class="login-history">
                  <el-timeline class="tech-timeline">
                    <el-timeline-item
                      v-for="record in loginHistory"
                      :key="record.id"
                      :timestamp="formatDateTime(record.time)"
                      placement="top"
                    >
                      <div class="history-item">
                        <div class="history-action">{{ record.action }}</div>
                        <div class="history-details">{{ record.details }}</div>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 使用统计 -->
          <el-tab-pane label="使用统计" name="statistics">
            <div class="tab-content">
              <div class="stats-grid">
                <div class="stat-card" v-for="stat in userStats" :key="stat.key">
                  <div class="stat-icon" :class="stat.iconClass">
                    <i :class="stat.icon"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                  </div>
                </div>
              </div>

              <div class="chart-section">
                <h3 class="section-title">最近7天查询趋势</h3>
                <div class="chart-container">
                  <div class="chart-placeholder">
                    <i class="el-icon-data-line"></i>
                    <p>图表功能开发中...</p>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import '@/styles/profile.scss'

const authStore = useAuthStore()

// 状态管理
const activeTab = ref('profile')
const passwordLoading = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 表单验证规则
const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const userInitial = computed(() => {
  const username = authStore.user?.username || 'U'
  return username.charAt(0).toUpperCase()
})

const roleText = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return '管理员'
    case 'user':
      return '普通用户'
    case 'readonly':
      return '只读用户'
    default:
      return '用户'
  }
})

const roleTextClass = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return 'text-red-400'
    case 'user':
      return 'text-blue-400'
    case 'readonly':
      return 'text-green-400'
    default:
      return 'text-gray-400'
  }
})

const roleAvatarClass = computed(() => {
  const role = authStore.user?.role || 'user'
  switch (role) {
    case 'admin':
      return 'avatar-admin'
    case 'user':
      return 'avatar-user'
    case 'readonly':
      return 'avatar-readonly'
    default:
      return 'avatar-default'
  }
})

const statusDotClass = computed(() => {
  return authStore.user?.is_active === true ? 'bg-green-500' : 'bg-red-500'
})

const accountStatusClass = computed(() => {
  return authStore.user?.is_active === true ? 'text-green-400' : 'text-red-400'
})

const accountStatusText = computed(() => {
  return authStore.user?.is_active === true ? '正常' : '已禁用'
})

// 密码强度计算
const passwordStrength = computed(() => {
  const password = passwordForm.new_password
  if (!password) return 0

  let strength = 0
  if (password.length >= 8) strength += 1
  if (/[a-z]/.test(password)) strength += 1
  if (/[A-Z]/.test(password)) strength += 1
  if (/[0-9]/.test(password)) strength += 1
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1

  return Math.min(strength, 4)
})

const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 2) return 'weak'
  if (strength <= 3) return 'medium'
  return 'strong'
})

const passwordStrengthWidth = computed(() => {
  return (passwordStrength.value / 4) * 100
})

const passwordStrengthText = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 2) return '弱'
  if (strength <= 3) return '中等'
  return '强'
})

// 权限分类
const permissionCategories = computed(() => {
  const permissions = authStore.permissions || []

  return [
    {
      name: '文档管理',
      icon: 'el-icon-document',
      permissions: [
        { key: 'document_upload', name: '上传文档', has: permissions.includes('document_upload') },
        { key: 'document_delete', name: '删除文档', has: permissions.includes('document_delete') },
        { key: 'document_read', name: '查看文档', has: permissions.includes('document_read') }
      ]
    },
    {
      name: '查询功能',
      icon: 'el-icon-chat-dot-round',
      permissions: [
        { key: 'query_ask', name: '智能查询', has: permissions.includes('query_ask') },
        { key: 'query_history', name: '查询历史', has: permissions.includes('query_history') }
      ]
    },
    {
      name: '系统管理',
      icon: 'el-icon-setting',
      permissions: [
        { key: 'system_settings', name: '系统设置', has: permissions.includes('system_settings') },
        { key: 'user_management', name: '用户管理', has: permissions.includes('user_management') },
        { key: 'role_management', name: '角色管理', has: permissions.includes('role_management') }
      ]
    }
  ]
})

// 用户统计数据
const userStats = ref([
  { key: 'queries', label: '查询次数', value: '0', icon: 'el-icon-chat-dot-round', iconClass: 'icon-blue' },
  { key: 'documents', label: '上传文档', value: '0', icon: 'el-icon-document', iconClass: 'icon-green' },
  { key: 'days_active', label: '活跃天数', value: '0', icon: 'el-icon-calendar', iconClass: 'icon-purple' }
])

// 登录历史
const loginHistory = ref([
  {
    id: 1,
    time: new Date().toISOString(),
    action: '登录成功',
    details: 'IP: 127.0.0.1'
  }
])

// 方法
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

const checkPasswordStrength = () => {
  // 密码强度已在计算属性中处理
}

const handleChangePassword = async () => {
  try {
    const result = await authStore.changePassword(passwordForm)

    if (result.success) {
      ElMessage.success('密码修改成功')
      // 重置表单
      Object.assign(passwordForm, {
        old_password: '',
        new_password: '',
        confirm_password: ''
      })
    } else {
      ElMessage.error(result.message || '密码修改失败')
    }
  } catch (error) {
    console.error('修改密码错误:', error)
    ElMessage.error('修改密码失败，请稍后重试')
  }
}

// 生命周期
onMounted(() => {
  // 加载用户统计数据
  // TODO: 调用API获取真实数据
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  padding: 20px;
  position: relative;
}

.tech-grid-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.profile-content {
  position: relative;
  z-index: 10;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header-card {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.profile-avatar-section {
  display: flex;
  align-items: center;
  gap: 30px;
  margin-bottom: 30px;
}

.avatar-container {
  position: relative;
}

.tech-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all var(--tech-transition-normal);
}

.tech-avatar.avatar-admin {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.5);
}

.tech-avatar.avatar-user {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
}

.tech-avatar.avatar-readonly {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
}

.avatar-text {
  font-size: 36px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.avatar-ring {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  animation: ring-rotate 10s linear infinite;
}

@keyframes ring-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.profile-info {
  flex: 1;
}

.username {
  font-size: 32px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, var(--tech-neon-blue) 0%, var(--tech-neon-purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.user-role {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.role-icon {
  font-size: 18px;
}

.user-email {
  font-size: 14px;
  color: var(--tech-text-secondary);
}

.account-status {
  display: flex;
  gap: 40px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-label {
  font-size: 12px;
  color: var(--tech-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}

.profile-tabs {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.tab-content {
  padding: 30px;
}

:deep(.tech-tabs .el-tabs__header) {
  background: rgba(255, 255, 255, 0.02);
  margin: 0;
}

:deep(.tech-tabs .el-tabs__nav-wrap) {
  padding: 0 20px;
}

:deep(.tech-tabs .el-tabs__item) {
  color: var(--tech-text-secondary);
  border: none;
  padding: 0 20px;
  height: 60px;
  line-height: 60px;
  font-weight: 600;
}

:deep(.tech-tabs .el-tabs__item.is-active) {
  color: var(--tech-neon-blue);
  background: rgba(0, 212, 255, 0.1);
}

:deep(.tech-tabs .el-tabs__active-bar) {
  background: var(--tech-neon-blue);
  height: 3px;
}

.info-section, .security-section, .chart-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item label {
  font-size: 12px;
  color: var(--tech-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.permissions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.permission-category {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--tech-text-primary);
  margin-bottom: 12px;
}

.permission-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.el-tag--success) {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--tech-neon-green);
}

:deep(.el-tag--info) {
  background: rgba(156, 163, 175, 0.1);
  border-color: rgba(156, 163, 175, 0.3);
  color: var(--tech-text-muted);
}

.password-form {
  max-width: 500px;
}

:deep(.tech-input .el-input__inner) {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-border-color);
  border-radius: 8px;
  color: var(--tech-text-primary);
}

:deep(.tech-input .el-input__inner:focus) {
  border-color: var(--tech-neon-blue);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

.password-strength {
  margin-top: 8px;
}

.strength-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 6px;
}

.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: all var(--tech-transition-normal);
}

.strength-fill.weak {
  background: var(--tech-neon-pink);
}

.strength-fill.medium {
  background: var(--tech-neon-yellow);
}

.strength-fill.strong {
  background: var(--tech-neon-green);
}

.strength-text {
  font-size: 12px;
  font-weight: 600;
}

.strength-text.weak {
  color: var(--tech-neon-pink);
}

.strength-text.medium {
  color: var(--tech-neon-yellow);
}

.strength-text.strong {
  color: var(--tech-neon-green);
}

.tech-button {
  background: var(--tech-gradient-secondary);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all var(--tech-transition-normal);
}

.tech-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
}

.login-history {
  max-height: 400px;
  overflow-y: auto;
}

:deep(.tech-timeline .el-timeline-item__tail) {
  border-left: 2px solid var(--tech-border-color);
}

:deep(.tech-timeline .el-timeline-item__node) {
  background: var(--tech-bg-secondary);
  border: 2px solid var(--tech-neon-blue);
}

.history-item {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
}

.history-action {
  font-weight: 600;
  color: var(--tech-text-primary);
  margin-bottom: 4px;
}

.history-details {
  font-size: 14px;
  color: var(--tech-text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--tech-transition-normal);
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.04);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.icon-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-icon.icon-green {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.stat-icon.icon-purple {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--tech-text-secondary);
}

.chart-container {
  height: 300px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
  color: var(--tech-text-muted);
}

.chart-placeholder i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.chart-placeholder p {
  font-size: 16px;
  margin: 0;
}
</style>