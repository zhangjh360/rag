<template>
  <div class="user-management-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <div class="management-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <i class="el-icon-user"></i>
            用户管理
          </h1>
          <p class="page-subtitle">管理系统用户账户和权限</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showAddUserDialog" class="tech-button">
            <i class="el-icon-plus"></i>
            添加用户
          </el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon icon-blue">
            <i class="el-icon-user"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.total }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-green">
            <i class="el-icon-check"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.active }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-purple">
            <i class="el-icon-user-solid"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.admins }}</div>
            <div class="stat-label">管理员</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-orange">
            <i class="el-icon-warning"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ userStats.inactive }}</div>
            <div class="stat-label">未激活</div>
          </div>
        </div>
      </div>

      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <div class="filter-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名或邮箱"
            prefix-icon="el-icon-search"
            clearable
            class="search-input"
            @input="handleSearch"
          />
          <el-select v-model="roleFilter" placeholder="角色筛选" clearable class="role-filter">
            <el-option label="全部角色" value="" />
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="只读用户" value="readonly" />
          </el-select>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable class="status-filter">
            <el-option label="全部状态" value="" />
            <el-option label="正常" value="Y" />
            <el-option label="禁用" value="N" />
          </el-select>
        </div>
        <div class="filter-right">
          <el-button @click="refreshData" :loading="loading" class="refresh-button">
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 用户表格 -->
      <div class="table-container">
        <el-table
          :data="filteredUsers"
          v-loading="loading"
          class="tech-table"
          stripe
          empty-text="暂无用户数据"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" min-width="120">
            <template #default="{ row }">
              <div class="user-info">
                <div class="user-avatar" :class="getUserRoleClass(row.role)">
                  {{ row.username.charAt(0).toUpperCase() }}
                </div>
                <span>{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="role_name" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role_name)" size="small">
                {{ getRoleText(row.role_name) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active === 'Y' ? 'success' : 'danger'" size="small">
                {{ row.is_active === 'Y' ? '正常' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_login" label="最后登录" min-width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.last_login) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" min-width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                @click="editUser(row)"
                class="action-button edit"
              >
                <i class="el-icon-edit"></i>
                编辑
              </el-button>
              <el-button
                size="small"
                @click="toggleUserStatus(row)"
                :type="row.is_active === 'Y' ? 'warning' : 'success'"
                class="action-button"
              >
                <i :class="row.is_active === 'Y' ? 'el-icon-video-pause' : 'el-icon-video-play'"></i>
                {{ row.is_active === 'Y' ? '禁用' : '启用' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteUser(row)"
                class="action-button delete"
              >
                <i class="el-icon-delete"></i>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalUsers"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            class="tech-pagination"
          />
        </div>
      </div>
    </div>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="isEditing ? '编辑用户' : '添加用户'"
      width="600px"
      class="tech-dialog"
    >
      <el-form
        ref="userForm"
        :model="userFormData"
        :rules="userFormRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userFormData.username"
            placeholder="请输入用户名"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="userFormData.email"
            placeholder="请输入邮箱"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEditing">
          <el-input
            v-model="userFormData.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="userFormData.role_id" placeholder="请选择角色">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.description"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-radio-group v-model="userFormData.is_active">
            <el-radio label="Y">正常</el-radio>
            <el-radio label="N">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser" :loading="submitLoading">
            {{ isEditing ? '更新' : '添加' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import apiService from '@/services/api'
import '@/styles/admin.scss'

const authStore = useAuthStore()

// 状态管理
const loading = ref(false)
const submitLoading = ref(false)
const users = ref([])
const roles = ref([])
const userDialogVisible = ref(false)
const isEditing = ref(false)

// 筛选状态
const searchQuery = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 表单数据
const userFormData = reactive({
  id: null,
  username: '',
  email: '',
  password: '',
  role_id: null,
  is_active: 'Y'
})

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 计算属性
const userStats = computed(() => {
  const total = users.value.length
  const active = users.value.filter(u => u.is_active === 'Y').length
  const admins = users.value.filter(u => u.role_name === 'admin').length
  const inactive = total - active

  return { total, active, admins, inactive }
})

const filteredUsers = computed(() => {
  let filtered = users.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(user =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
    )
  }

  // 角色过滤
  if (roleFilter.value) {
    filtered = filtered.filter(user => user.role_name === roleFilter.value)
  }

  // 状态过滤
  if (statusFilter.value) {
    filtered = filtered.filter(user => user.is_active === statusFilter.value)
  }

  return filtered
})

const totalUsers = computed(() => filteredUsers.value.length)

// 方法
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await apiService.get('/api/users')
    users.value = response.data.users || []

    // 模拟数据
    // users.value = [
    //   {
    //     id: 1,
    //     username: 'admin',
    //     email: 'admin@example.com',
    //     role: 'admin',
    //     is_active: 'Y',
    //     last_login: new Date().toISOString(),
    //     created_at: '2024-01-01T00:00:00Z'
    //   },
    //   {
    //     id: 2,
    //     username: 'user1',
    //     email: 'user1@example.com',
    //     role: 'user',
    //     is_active: 'Y',
    //     last_login: new Date(Date.now() - 86400000).toISOString(),
    //     created_at: '2024-01-02T00:00:00Z'
    //   }
    // ]
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error('加载用户失败:', error)
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    //调用实际的API
    const response = await apiService.get('/api/roles')
    roles.value = response.data.roles || []

    // 模拟数据
    // roles.value = [
    //   { id: 1, name: 'admin', description: '管理员' },
    //   { id: 2, name: 'user', description: '普通用户' },
    //   { id: 3, name: 'readonly', description: '只读用户' }
    // ]
  } catch (error) {
    ElMessage.error('加载角色列表失败')
    console.error('加载角色失败:', error)
  }
}

const showAddUserDialog = () => {
  isEditing.value = false
  resetForm()
  userDialogVisible.value = true
}

const editUser = (user) => {
  isEditing.value = true
  Object.assign(userFormData, {
    ...user,
    role_id: user.role_id || roles.value.find(r => r.name === user.role_name)?.id
  })
  userDialogVisible.value = true
}

const saveUser = async () => {
  submitLoading.value = true
  try {
    if (isEditing.value) {
      // 调用更新用户API
      await apiService.put(`/api/users/${userFormData.id}`, userFormData)
      ElMessage.success('用户更新成功')
    } else {
      //调用添加用户API
      await apiService.post('/api/users', userFormData)
      ElMessage.success('用户添加成功')
    }

    userDialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('保存用户失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const toggleUserStatus = async (user) => {
  try {
    const action = user.is_active === 'Y' ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.username} 吗？`,
      `${action}确认`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const newStatus = user.is_active === 'Y' ? 'N' : 'Y'
    // 调用更新状态API
    await apiService.patch(`/api/users/${user.id}/status`, { is_active: newStatus })

    user.is_active = newStatus
    ElMessage.success(`用户${action}成功`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
      console.error('更新用户状态失败:', error)
    }
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.username} 吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    //调用删除用户API
    await apiService.delete(`/api/users/${user.id}`)

    users.value = users.value.filter(u => u.id !== user.id)
    ElMessage.success('用户删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除用户失败:', error)
    }
  }
}

const refreshData = () => {
  loadUsers()
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
}

const resetForm = () => {
  Object.assign(userFormData, {
    id: null,
    username: '',
    email: '',
    password: '',
    role_id: null,
    is_active: 'Y'
  })
}

const getUserRoleClass = (role) => {
  switch (role) {
    case 'admin':
      return 'role-admin'
    case 'user':
      return 'role-user'
    case 'readonly':
      return 'role-readonly'
    default:
      return 'role-default'
  }
}

const getRoleText = (role) => {
  switch (role) {
    case 'admin':
      return '管理员'
    case 'user':
      return '普通用户'
    case 'readonly':
      return '只读用户'
    default:
      return '未知'
  }
}

const getRoleTagType = (role) => {
  switch (role) {
    case 'admin':
      return 'danger'
    case 'user':
      return 'primary'
    case 'readonly':
      return 'success'
    default:
      return 'info'
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped>
.user-management-container {
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
    linear-gradient(rgba(168, 85, 247, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(168, 85, 247, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.management-content {
  position: relative;
  z-index: 10;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, var(--tech-neon-purple) 0%, var(--tech-neon-pink) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  color: var(--tech-text-secondary);
  font-size: 16px;
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--tech-transition-normal);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(168, 85, 247, 0.15);
  border-color: var(--tech-neon-purple);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.icon-blue {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
  color: #3b82f6;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.stat-icon.icon-green {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
  color: #10b981;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.stat-icon.icon-purple {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(168, 85, 247, 0.05));
  color: #a855f7;
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
}

.stat-icon.icon-orange {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.1), rgba(251, 146, 60, 0.05));
  color: #fb923c;
  box-shadow: 0 0 20px rgba(251, 146, 60, 0.3);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--tech-text-secondary);
  font-weight: 500;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 16px 20px;
}

.filter-left {
  display: flex;
  gap: 16px;
  flex: 1;
}

.search-input {
  max-width: 300px;
  flex: 1;
}

.role-filter, .status-filter {
  width: 150px;
}

.refresh-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--tech-glass-border);
  color: var(--tech-text-primary);
}

.table-container {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

:deep(.tech-table) {
  background: transparent;

  .el-table__header-wrapper {
    background: rgba(255, 255, 255, 0.02);
  }

  .el-table__header th {
    background: transparent;
    border-bottom: 1px solid var(--tech-glass-border);
    color: var(--tech-text-primary);
    font-weight: 600;
  }

  .el-table__row {
    background: transparent;

    &:hover {
      background: rgba(255, 255, 255, 0.02);
    }
  }

  .el-table__body td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--tech-text-secondary);
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.user-avatar.role-admin {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.user-avatar.role-user {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.user-avatar.role-readonly {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.user-avatar.role-default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.action-button {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--tech-glass-border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--tech-text-secondary);
  transition: all var(--tech-transition-fast);

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--tech-text-primary);
  }

  &.edit:hover {
    background: rgba(59, 130, 246, 0.1);
    border-color: #3b82f6;
    color: #3b82f6;
  }

  &.delete:hover {
    background: rgba(239, 68, 68, 0.1);
    border-color: #ef4444;
    color: #ef4444;
  }
}

.pagination-container {
  padding: 20px;
  display: flex;
  justify-content: center;
}

:deep(.tech-pagination) {
  .el-pagination__total,
  .el-pagination__sizes,
  .el-pager li,
  .el-pagination__jump {
    color: var(--tech-text-secondary);
  }

  .el-pager li.active {
    background: var(--tech-neon-purple);
    color: white;
  }
}

.tech-button {
  background: var(--tech-gradient-accent);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all var(--tech-transition-normal);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(168, 85, 247, 0.4);
  }
}

:deep(.tech-dialog) {
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border: 1px solid var(--tech-glass-border);
  border-radius: 16px;

  .el-dialog__header {
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid var(--tech-glass-border);
    border-radius: 16px 16px 0 0;
  }

  .el-dialog__title {
    color: var(--tech-text-primary);
    font-weight: 600;
  }

  .el-dialog__body {
    color: var(--tech-text-secondary);
  }

  .el-form-item__label {
    color: var(--tech-text-primary);
  }

  .el-input__inner,
  .el-textarea__inner {
    background: var(--tech-bg-secondary);
    border: 1px solid var(--tech-border-color);
    border-radius: 8px;
    color: var(--tech-text-primary);

    &:focus {
      border-color: var(--tech-neon-purple);
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.2);
    }
  }
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .filter-section {
    flex-direction: column;
    gap: 16px;
  }

  .filter-left {
    flex-direction: column;
    gap: 12px;
  }

  .search-input {
    max-width: none;
  }

  .role-filter,
  .status-filter {
    width: 100%;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  :deep(.tech-table .el-table__body-wrapper) {
    overflow-x: auto;
  }
}
</style>