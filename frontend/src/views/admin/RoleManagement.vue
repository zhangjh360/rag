<template>
  <div class="role-management-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <div class="management-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <i class="el-icon-medal"></i>
            角色管理
          </h1>
          <p class="page-subtitle">管理系统角色和权限配置</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showAddRoleDialog" class="tech-button">
            <i class="el-icon-plus"></i>
            添加角色
          </el-button>
        </div>
      </div>

      <!-- 角色统计 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon icon-blue">
            <i class="el-icon-medal"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ roleStats.total }}</div>
            <div class="stat-label">总角色数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-green">
            <i class="el-icon-user"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ roleStats.assigned }}</div>
            <div class="stat-label">已分配</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-purple">
            <i class="el-icon-key"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ roleStats.permissions }}</div>
            <div class="stat-label">权限项</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-orange">
            <i class="el-icon-warning-outline"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ roleStats.system }}</div>
            <div class="stat-label">系统角色</div>
          </div>
        </div>
      </div>

      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <div class="filter-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索角色名称或描述"
            prefix-icon="el-icon-search"
            clearable
            class="search-input"
            @input="handleSearch"
          />
          <el-select v-model="typeFilter" placeholder="类型筛选" clearable class="type-filter">
            <el-option label="全部类型" value="" />
            <el-option label="系统角色" value="system" />
            <el-option label="自定义角色" value="custom" />
          </el-select>
        </div>
        <div class="filter-right">
          <el-button @click="refreshData" :loading="loading" class="refresh-button">
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 角色表格 -->
      <div class="table-container">
        <el-table
          :data="filteredRoles"
          v-loading="loading"
          class="tech-table"
          stripe
          empty-text="暂无角色数据"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="角色名称" min-width="150">
            <template #default="{ row }">
              <div class="role-info">
                <div class="role-icon" :class="getRoleIconClass(row.name)">
                  <i :class="getRoleIcon(row.name)"></i>
                </div>
                <span>{{ row.name }}</span>
                <el-tag v-if="row.is_system" size="mini" type="info">系统</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="角色描述" min-width="200" />
          <el-table-column prop="user_count" label="用户数量" width="120">
            <template #default="{ row }">
              <el-badge :value="row.user_count || 0" class="user-badge">
                <span>{{ row.user_count || 0 }} 人</span>
              </el-badge>
            </template>
          </el-table-column>
          <el-table-column label="权限数量" width="120">
            <template #default="{ row }">
              <el-tag type="success" size="small">
                {{ getPermissionCount(row) }} 项
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" min-width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                @click="viewRole(row)"
                class="action-button view"
              >
                <i class="el-icon-view"></i>
                查看
              </el-button>
              <el-button
                size="small"
                @click="editRole(row)"
                :disabled="row.is_system"
                class="action-button edit"
              >
                <i class="el-icon-edit"></i>
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteRole(row)"
                :disabled="row.is_system"
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
            :total="totalRoles"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            class="tech-pagination"
          />
        </div>
      </div>
    </div>

    <!-- 添加/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditing ? '编辑角色' : '添加角色'"
      width="800px"
      class="tech-dialog"
    >
      <el-form
        ref="roleForm"
        :model="roleFormData"
        :rules="roleFormRules"
        label-width="100px"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input
            v-model="roleFormData.name"
            placeholder="请输入角色名称"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleFormData.description"
            placeholder="请输入角色描述"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="权限配置" prop="permissions">
          <div class="permissions-config">
            <div class="permission-category" v-for="category in permissionCategories" :key="category.name">
              <div class="category-header">
                <el-checkbox
                  :indeterminate="getCategoryIndeterminate(category)"
                  v-model="category.selected"
                  @change="handleCategoryChange(category)"
                >
                  {{ category.name }}
                </el-checkbox>
              </div>
              <div class="permission-list">
                <el-checkbox-group v-model="roleFormData.permissions">
                  <div v-for="permission in category.permissions" :key="permission.key" class="permission-item">
                    <el-checkbox :label="permission.key">
                      <span class="permission-name">{{ permission.name }}</span>
                      <span class="permission-desc">{{ permission.description }}</span>
                    </el-checkbox>
                  </div>
                </el-checkbox-group>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="roleDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRole" :loading="submitLoading">
            {{ isEditing ? '更新' : '添加' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看角色详情对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="角色详情"
      width="600px"
      class="tech-dialog"
    >
      <div class="role-detail" v-if="viewRoleData">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-info">
            <div class="info-row">
              <span class="info-label">角色名称：</span>
              <span class="info-value">{{ viewRoleData.name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">角色描述：</span>
              <span class="info-value">{{ viewRoleData.description }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">用户数量：</span>
              <span class="info-value">{{ viewRoleData.user_count || 0 }} 人</span>
            </div>
            <div class="info-row">
              <span class="info-label">创建时间：</span>
              <span class="info-value">{{ formatDateTime(viewRoleData.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>权限列表</h4>
          <div class="permissions-view">
            <div v-for="category in getRolePermissionCategories(viewRoleData)" :key="category.name" class="view-category">
              <div class="view-category-header">{{ category.name }}</div>
              <div class="view-permissions">
                <el-tag
                  v-for="permission in category.permissions"
                  :key="permission.key"
                  type="success"
                  size="small"
                  effect="plain"
                  class="permission-tag"
                >
                  {{ permission.name }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiService from '@/services/api'
import '@/styles/admin.scss'

// 状态管理
const loading = ref(false)
const submitLoading = ref(false)
const roles = ref([])
const roleDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEditing = ref(false)

// 筛选状态
const searchQuery = ref('')
const typeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 表单数据
const roleFormData = reactive({
  id: null,
  name: '',
  description: '',
  permissions: []
})

// 查看数据
const viewRoleData = ref(null)

// 表单验证规则
const roleFormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度为 2-50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入角色描述', trigger: 'blur' },
    { min: 5, max: 200, message: '角色描述长度为 5-200 个字符', trigger: 'blur' }
  ]
}

// 权限分类配置
const permissionCategories = ref([
  {
    name: '文档管理',
    key: 'document',
    selected: false,
    permissions: [
      { key: 'document_upload', name: '上传文档', description: '允许上传新文档到系统' },
      { key: 'document_delete', name: '删除文档', description: '允许删除系统中的文档' },
      { key: 'document_read', name: '查看文档', description: '允许查看和读取文档内容' }
    ]
  },
  {
    name: '查询功能',
    key: 'query',
    selected: false,
    permissions: [
      { key: 'query_ask', name: '智能查询', description: '允许使用AI问答功能' },
      { key: 'query_history', name: '查询历史', description: '允许查看查询历史记录' }
    ]
  },
  {
    name: '系统管理',
    key: 'system',
    selected: false,
    permissions: [
      { key: 'system_settings', name: '系统设置', description: '允许修改系统配置' },
      { key: 'user_management', name: '用户管理', description: '允许管理系统用户' },
      { key: 'role_management', name: '角色管理', description: '允许管理系统角色和权限' }
    ]
  }
])

// 计算属性
const roleStats = computed(() => {
  const total = roles.value.length
  const system = roles.value.filter(r => r.is_system).length
  const assigned = roles.value.filter(r => r.user_count > 0).length
  const permissions = new Set(roles.value.flatMap(r => r.permissions || [])).size

  return { total, system, assigned, permissions }
})

const filteredRoles = computed(() => {
  let filtered = roles.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(role =>
      role.name.toLowerCase().includes(query) ||
      role.description.toLowerCase().includes(query)
    )
  }

  // 类型过滤
  if (typeFilter.value) {
    const isSystem = typeFilter.value === 'system'
    filtered = filtered.filter(role => role.is_system === isSystem)
  }

  return filtered
})

const totalRoles = computed(() => filteredRoles.value.length)

// 方法
const loadRoles = async () => {
  loading.value = true
  try {
    //调用实际的API
    const response = await apiService.get('/api/roles')
    roles.value = response.data

    // 模拟数据
    // roles.value = [
    //   {
    //     id: 1,
    //     name: 'admin',
    //     description: '管理员角色，拥有系统所有权限',
    //     permissions: ['document_upload', 'document_delete', 'document_read', 'query_ask', 'query_history', 'system_settings', 'user_management', 'role_management'],
    //     user_count: 1,
    //     is_system: true,
    //     created_at: '2024-01-01T00:00:00Z',
    //     updated_at: '2024-01-01T00:00:00Z'
    //   },
    //   {
    //     id: 2,
    //     name: 'user',
    //     description: '普通用户角色，可上传文档和使用查询功能',
    //     permissions: ['document_upload', 'document_delete', 'document_read', 'query_ask', 'query_history'],
    //     user_count: 5,
    //     is_system: true,
    //     created_at: '2024-01-01T00:00:00Z',
    //     updated_at: '2024-01-01T00:00:00Z'
    //   },
    //   {
    //     id: 3,
    //     name: 'readonly',
    //     description: '只读用户角色，仅可查询和查看历史',
    //     permissions: ['document_read', 'query_ask', 'query_history'],
    //     user_count: 2,
    //     is_system: true,
    //     created_at: '2024-01-01T00:00:00Z',
    //     updated_at: '2024-01-01T00:00:00Z'
    //   }
    // ]
  } catch (error) {
    ElMessage.error('加载角色列表失败')
    console.error('加载角色失败:', error)
  } finally {
    loading.value = false
  }
}

const showAddRoleDialog = () => {
  isEditing.value = false
  resetForm()
  roleDialogVisible.value = true
}

const editRole = (role) => {
  isEditing.value = true
  Object.assign(roleFormData, {
    id: role.id,
    name: role.name,
    description: role.description,
    permissions: role.permissions || []
  })
  updatePermissionCategories()
  roleDialogVisible.value = true
}

const viewRole = (role) => {
  viewRoleData.value = role
  viewDialogVisible.value = true
}

const saveRole = async () => {
  submitLoading.value = true
  try {
    if (isEditing.value) {
      // 调用更新角色API
      await apiService.put(`/api/roles/${roleFormData.id}`, roleFormData)
      ElMessage.success('角色更新成功')
    } else {
      // 调用添加角色API
      await apiService.post('/api/roles', { ...roleFormData, is_system: false })
      ElMessage.success('角色添加成功')
    }

    roleDialogVisible.value = false
    await loadRoles()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error('保存角色失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const deleteRole = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 ${role.name} 吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    //调用删除角色API
    await apiService.delete(`/api/roles/${role.id}`)

    roles.value = roles.value.filter(r => r.id !== role.id)
    ElMessage.success('角色删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除角色失败:', error)
    }
  }
}

const refreshData = () => {
  loadRoles()
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
  Object.assign(roleFormData, {
    id: null,
    name: '',
    description: '',
    permissions: []
  })
  resetPermissionCategories()
}

const resetPermissionCategories = () => {
  permissionCategories.value.forEach(category => {
    category.selected = false
  })
}

const updatePermissionCategories = () => {
  permissionCategories.value.forEach(category => {
    const categoryPermissions = category.permissions.map(p => p.key)
    const selectedPermissions = roleFormData.permissions.filter(p => categoryPermissions.includes(p))

    category.selected = selectedPermissions.length === category.permissions.length
  })
}

const handleCategoryChange = (category) => {
  const categoryPermissions = category.permissions.map(p => p.key)

  if (category.selected) {
    // 选中分类下的所有权限
    categoryPermissions.forEach(permission => {
      if (!roleFormData.permissions.includes(permission)) {
        roleFormData.permissions.push(permission)
      }
    })
  } else {
    // 取消选中分类下的所有权限
    roleFormData.permissions = roleFormData.permissions.filter(p => !categoryPermissions.includes(p))
  }
}

const getCategoryIndeterminate = (category) => {
  const categoryPermissions = category.permissions.map(p => p.key)
  const selectedPermissions = roleFormData.permissions.filter(p => categoryPermissions.includes(p))

  return selectedPermissions.length > 0 && selectedPermissions.length < categoryPermissions.length
}

const getPermissionCount = (role) => {
  return Array.isArray(role.permissions) ? role.permissions.length : 0
}

const getRoleIconClass = (roleName) => {
  switch (roleName) {
    case 'admin':
      return 'role-icon-admin'
    case 'user':
      return 'role-icon-user'
    case 'readonly':
      return 'role-icon-readonly'
    default:
      return 'role-icon-default'
  }
}

const getRoleIcon = (roleName) => {
  switch (roleName) {
    case 'admin':
      return 'el-icon-user-solid'
    case 'user':
      return 'el-icon-user'
    case 'readonly':
      return 'el-icon-view'
    default:
      return 'el-icon-medal'
  }
}

const getRolePermissionCategories = (role) => {
  const rolePermissions = role.permissions || []

  return permissionCategories.value.map(category => ({
    name: category.name,
    permissions: category.permissions.filter(p => rolePermissions.includes(p.key))
  })).filter(category => category.permissions.length > 0)
}

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.role-management-container {
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

.type-filter {
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

.role-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  flex-shrink: 0;
}

.role-icon.role-admin {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.role-icon.role-user {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.role-icon.role-readonly {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.role-icon.role-default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.user-badge {
  :deep(.el-badge__content) {
    background-color: var(--tech-neon-blue);
    border-color: var(--tech-neon-blue);
  }
}

.action-button {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid var(--tech-glass-border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--tech-text-secondary);
  transition: all var(--tech-transition-fast);

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
    color: var(--tech-text-primary);
  }

  &.view:hover {
    background: rgba(16, 185, 129, 0.1);
    border-color: #10b981;
    color: #10b981;
  }

  &.edit:hover:not(:disabled) {
    background: rgba(59, 130, 246, 0.1);
    border-color: #3b82f6;
    color: #3b82f6;
  }

  &.delete:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.1);
    border-color: #ef4444;
    color: #ef4444;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

.permissions-config {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--tech-border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--tech-bg-secondary);
}

.permission-category {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.category-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--tech-border-color);
}

.permission-list {
  padding-left: 20px;
}

.permission-item {
  margin-bottom: 8px;

  .permission-name {
    font-weight: 600;
    color: var(--tech-text-primary);
    margin-right: 8px;
  }

  .permission-desc {
    color: var(--tech-text-muted);
    font-size: 12px;
  }
}

.detail-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }

  h4 {
    color: var(--tech-text-primary);
    font-weight: 600;
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--tech-border-color);
  }
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
}

.info-label {
  min-width: 80px;
  color: var(--tech-text-secondary);
  font-weight: 500;
}

.info-value {
  color: var(--tech-text-primary);
  flex: 1;
}

.view-category {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

.view-category-header {
  font-weight: 600;
  color: var(--tech-text-primary);
  margin-bottom: 8px;
}

.view-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-left: 16px;
}

.permission-tag {
  margin: 0;
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

  .type-filter {
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