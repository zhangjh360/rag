<template>
  <div class="routing-rules-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <div class="rules-content">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon class="title-icon"><Connection /></el-icon>
            路由规则管理
          </h1>
          <p class="page-subtitle">配置领域路由规则,实现智能查询分发</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog = true" class="tech-button-primary">
            <el-icon><Plus /></el-icon>
            创建规则
          </el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="tech-stat-card">
          <div class="stat-icon icon-blue">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ totalRules }}</div>
            <div class="stat-label">总规则数</div>
          </div>
        </div>
        <div class="tech-stat-card">
          <div class="stat-icon icon-green">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeRules }}</div>
            <div class="stat-label">激活规则</div>
          </div>
        </div>
        <div class="tech-stat-card">
          <div class="stat-icon icon-purple">
            <el-icon><Star /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ highPriorityRules }}</div>
            <div class="stat-label">高优先级</div>
          </div>
        </div>
      </div>

      <!-- 规则列表 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">
            <el-icon class="mr-2"><List /></el-icon>
            路由规则列表
          </h2>
        </div>
        <div class="card-body">
          <!-- 工具栏 -->
          <div class="toolbar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索规则..."
              :prefix-icon="Search"
              class="tech-input"
              style="width: 300px"
              clearable
              @input="handleSearch"
            />
            <div class="toolbar-actions">
              <el-switch
                v-model="showInactive"
                active-text="显示未激活"
                @change="loadRules"
                class="tech-switch"
              />
              <el-button @click="showTestDialog = true" class="tech-button">
                <el-icon><Search /></el-icon>
                测试匹配
              </el-button>
            </div>
          </div>

          <!-- 规则表格 -->
          <el-table
            :data="filteredRules"
            v-loading="loading"
            class="tech-table"
            :header-cell-style="{ background: 'var(--tech-bg-secondary)', color: 'var(--tech-text-primary)' }"
            stripe
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="rule_name" label="规则名称" min-width="150">
              <template #default="{ row }">
                <div class="rule-name-cell">
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                    {{ row.is_active ? '激活' : '未激活' }}
                  </el-tag>
                  <span class="ml-2">{{ row.rule_name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="rule_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getRuleTypeColor(row.rule_type)" size="small">
                  {{ getRuleTypeLabel(row.rule_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="pattern" label="匹配模式" min-width="200">
              <template #default="{ row }">
                <el-text class="pattern-text" truncated>{{ row.pattern }}</el-text>
              </template>
            </el-table-column>
            <el-table-column prop="target_namespace" label="目标领域" width="150">
              <template #default="{ row }">
                <el-tag type="primary" size="small">{{ row.target_namespace }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="confidence_threshold" label="置信度阈值" width="120" align="center">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.confidence_threshold * 100"
                  :color="getConfidenceColor(row.confidence_threshold)"
                  :stroke-width="8"
                  :show-text="true"
                  :format="() => row.confidence_threshold.toFixed(2)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100" align="center" sortable />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="handleEdit(row)" class="tech-button-sm">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    @click="handleToggleActive(row)"
                    :type="row.is_active ? 'warning' : 'success'"
                    class="tech-button-sm"
                  >
                    <el-icon><SwitchButton /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="handleDelete(row)"
                    class="tech-button-sm"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalRules"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadRules"
              @current-change="loadRules"
              class="tech-pagination"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingRule ? '编辑规则' : '创建规则'"
      width="600px"
      class="tech-dialog"
    >
      <el-form :model="ruleForm" :rules="formRules" ref="ruleFormRef" label-width="120px">
        <el-form-item label="规则名称" prop="rule_name">
          <el-input v-model="ruleForm.rule_name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="规则类型" prop="rule_type">
          <el-select v-model="ruleForm.rule_type" placeholder="请选择规则类型" style="width: 100%">
            <el-option
              v-for="type in ruleTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            >
              <div class="rule-type-option">
                <span>{{ type.label }}</span>
                <span class="option-description">{{ type.description }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="匹配模式" prop="pattern">
          <el-input
            v-model="ruleForm.pattern"
            type="textarea"
            :rows="3"
            :placeholder="getPatternPlaceholder()"
          />
          <div class="form-hint">{{ getRuleTypeDescription(ruleForm.rule_type) }}</div>
        </el-form-item>
        <el-form-item label="目标领域" prop="target_namespace">
          <el-select v-model="ruleForm.target_namespace" placeholder="请选择目标领域" style="width: 100%">
            <el-option
              v-for="domain in availableDomains"
              :key="domain.namespace"
              :label="domain.display_name"
              :value="domain.namespace"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度阈值" prop="confidence_threshold">
          <el-slider
            v-model="ruleForm.confidence_threshold"
            :min="0"
            :max="1"
            :step="0.05"
            :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number
            v-model="ruleForm.priority"
            :min="0"
            :max="100"
            controls-position="right"
          />
          <div class="form-hint">数值越大优先级越高</div>
        </el-form-item>
        <el-form-item label="是否激活" prop="is_active">
          <el-switch v-model="ruleForm.is_active" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="ruleForm.metadata.description"
            type="textarea"
            :rows="2"
            placeholder="可选,规则说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false" class="tech-button">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" class="tech-button-primary">
            {{ editingRule ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 测试匹配对话框 -->
    <el-dialog
      v-model="showTestDialog"
      title="测试规则匹配"
      width="600px"
      class="tech-dialog"
    >
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="查询文本">
          <el-input
            v-model="testForm.query"
            type="textarea"
            :rows="3"
            placeholder="请输入要测试的查询文本"
          />
        </el-form-item>
        <el-form-item label="最小置信度">
          <el-slider
            v-model="testForm.min_confidence"
            :min="0"
            :max="1"
            :step="0.05"
            :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
            show-input
            :input-size="'small'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTestDialog = false" class="tech-button">关闭</el-button>
          <el-button type="primary" @click="handleTest" :loading="testing" class="tech-button-primary">
            开始测试
          </el-button>
        </span>
      </template>

      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result">
        <el-divider />
        <h3>
          <el-icon><TrendCharts /></el-icon>
          测试结果
        </h3>
        <el-alert
          :type="testResult.matched ? 'success' : 'info'"
          :title="testResult.message"
          :closable="false"
          show-icon
        />
        <div v-if="testResult.matched" class="result-details">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="匹配规则">{{ testResult.rule_name }}</el-descriptions-item>
            <el-descriptions-item label="目标领域">
              <el-tag type="primary">{{ testResult.target_namespace }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="置信度">
              <el-progress
                :percentage="testResult.confidence * 100"
                :color="getConfidenceColor(testResult.confidence)"
                :stroke-width="12"
              />
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Plus,
  CircleCheck,
  Star,
  List,
  Search,
  Edit,
  Delete,
  SwitchButton,
  TrendCharts
} from '@element-plus/icons-vue'
import {
  getAllRules,
  createRule,
  updateRule,
  deleteRule,
  testRuleMatch,
  RULE_TYPES,
  getRuleTypeLabel as getTypeLabel,
  getRuleTypeDescription as getTypeDescription
} from '@/services/routingRules'
import { getAllDomains } from '@/services/knowledgeDomains'

// 状态
const loading = ref(false)
const submitting = ref(false)
const testing = ref(false)
const showCreateDialog = ref(false)
const showTestDialog = ref(false)
const showInactive = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 数据
const rules = ref([])
const editingRule = ref(null)
const availableDomains = ref([])
const testResult = ref(null)

// 表单
const ruleFormRef = ref(null)
const ruleForm = ref({
  rule_name: '',
  rule_type: 'keyword',
  pattern: '',
  target_namespace: '',
  confidence_threshold: 0.3,
  priority: 0,
  is_active: true,
  metadata: {
    description: ''
  }
})

const testForm = ref({
  query: '',
  min_confidence: 0.0
})

// 规则类型
const ruleTypes = RULE_TYPES

// 表单验证规则
const formRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  rule_type: [{ required: true, message: '请选择规则类型', trigger: 'change' }],
  pattern: [{ required: true, message: '请输入匹配模式', trigger: 'blur' }],
  target_namespace: [{ required: true, message: '请选择目标领域', trigger: 'change' }]
}

// 计算属性
const totalRules = computed(() => rules.value.length)
const activeRules = computed(() => rules.value.filter(r => r.is_active).length)
const highPriorityRules = computed(() => rules.value.filter(r => r.priority > 5).length)

const filteredRules = computed(() => {
  let filtered = rules.value

  if (!showInactive.value) {
    filtered = filtered.filter(r => r.is_active)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(
      r =>
        r.rule_name.toLowerCase().includes(keyword) ||
        r.pattern.toLowerCase().includes(keyword) ||
        r.target_namespace.toLowerCase().includes(keyword)
    )
  }

  return filtered
})

// 方法
const loadRules = async () => {
  loading.value = true
  try {
    const data = await getAllRules({
      include_inactive: true,
      skip: 0,
      limit: 500
    })
    rules.value = data.rules
  } catch (error) {
    ElMessage.error('加载规则失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const loadDomains = async () => {
  try {
    const data = await getAllDomains({
      include_inactive: false,
      skip: 0,
      limit: 500
    })
    availableDomains.value = data.domains
  } catch (error) {
    console.error('加载领域失败:', error)
  }
}

const handleSearch = () => {
  // 搜索功能由 computed 属性自动处理
}

const handleEdit = (row) => {
  editingRule.value = row
  ruleForm.value = {
    rule_name: row.rule_name,
    rule_type: row.rule_type,
    pattern: row.pattern,
    target_namespace: row.target_namespace,
    confidence_threshold: row.confidence_threshold,
    priority: row.priority,
    is_active: row.is_active,
    metadata: row.metadata || { description: '' }
  }
  showCreateDialog.value = true
}

const handleToggleActive = async (row) => {
  try {
    await updateRule(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已禁用规则' : '已启用规则')
    await loadRules()
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则 "${row.rule_name}" 吗?`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteRule(row.id)
    ElMessage.success('删除成功')
    await loadRules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

const handleSubmit = async () => {
  if (!ruleFormRef.value) return

  await ruleFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (editingRule.value) {
        await updateRule(editingRule.value.id, ruleForm.value)
        ElMessage.success('更新成功')
      } else {
        await createRule(ruleForm.value)
        ElMessage.success('创建成功')
      }

      showCreateDialog.value = false
      resetForm()
      await loadRules()
    } catch (error) {
      ElMessage.error((editingRule.value ? '更新' : '创建') + '失败: ' + error.message)
    } finally {
      submitting.value = false
    }
  })
}

const handleTest = async () => {
  if (!testForm.value.query) {
    ElMessage.warning('请输入查询文本')
    return
  }

  testing.value = true
  try {
    testResult.value = await testRuleMatch(testForm.value)
  } catch (error) {
    ElMessage.error('测试失败: ' + error.message)
  } finally {
    testing.value = false
  }
}

const resetForm = () => {
  editingRule.value = null
  ruleForm.value = {
    rule_name: '',
    rule_type: 'keyword',
    pattern: '',
    target_namespace: '',
    confidence_threshold: 0.3,
    priority: 0,
    is_active: true,
    metadata: {
      description: ''
    }
  }
  testResult.value = null
}

const getRuleTypeColor = (ruleType) => {
  const colors = {
    keyword: '',
    regex: 'warning',
    pattern: 'success'
  }
  return colors[ruleType] || ''
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.7) return '#67c23a'
  if (confidence >= 0.4) return '#e6a23c'
  return '#f56c6c'
}

const getPatternPlaceholder = () => {
  const placeholders = {
    keyword: '例如: API|接口|SDK|文档 (使用 | 分隔)',
    regex: '例如: ^(退货|换货|售后).*(流程|方式)',
    pattern: '例如: *简历* 或 *.pdf'
  }
  return placeholders[ruleForm.value.rule_type] || ''
}

const getRuleTypeDescription = (ruleType) => {
  return getTypeDescription(ruleType)
}

const getRuleTypeLabel = (ruleType) => {
  return getTypeLabel(ruleType)
}

// 生命周期
onMounted(() => {
  loadRules()
  loadDomains()
})
</script>

<style scoped>
.routing-rules-container {
  position: relative;
  min-height: 100vh;
  padding: 24px;
}

.tech-grid-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
  z-index: 0;
}

.rules-content {
  position: relative;
  z-index: 1;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
  color: var(--tech-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--tech-text-secondary);
  margin: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.tech-stat-card {
  background: var(--tech-bg-card);
  border: 1px solid var(--tech-border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.tech-stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(59, 130, 246, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.icon-blue {
  background: rgba(59, 130, 246, 0.1);
  color: var(--tech-primary);
}

.icon-green {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.icon-purple {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--tech-text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--tech-text-secondary);
}

.tech-card {
  background: var(--tech-bg-card);
  border: 1px solid var(--tech-border-color);
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--tech-border-color);
}

.card-body {
  padding: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.rule-name-cell {
  display: flex;
  align-items: center;
}

.pattern-text {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.rule-type-option {
  display: flex;
  flex-direction: column;
}

.option-description {
  font-size: 12px;
  color: var(--tech-text-secondary);
  margin-top: 4px;
}

.form-hint {
  font-size: 12px;
  color: var(--tech-text-secondary);
  margin-top: 4px;
}

.test-result {
  margin-top: 16px;
}

.result-details {
  margin-top: 16px;
}
</style>
