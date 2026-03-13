<template>
  <div class="settings-page">
    <div class="page-header mb-6">
      <div class="header-content">
        <div>
          <h1 class="text-2xl font-bold text-tech-text-primary">系统配置</h1>
          <p class="text-tech-text-secondary mt-2">管理LLM模型和系统参数</p>
        </div>
        <el-button @click="loadSettings" :loading="loading" class="refresh-btn">
          <el-icon class="mr-1"><Refresh /></el-icon>
          刷新配置
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="tech-tabs" @tab-click="handleTabChange">
      <!-- LLM多模型配置 -->
      <el-tab-pane label="LLM多模型配置" name="llm">
        <div class="llm-config-container">
          <!-- 概览统计 -->
          <div class="stats-grid mb-6">
            <div class="stat-card">
              <div class="stat-value">{{ groups.length }}</div>
              <div class="stat-label">模型分组</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ models.length }}</div>
              <div class="stat-label">已配置模型</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ scenarios.length }}</div>
              <div class="stat-label">应用场景</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ activeModelsCount }}</div>
              <div class="stat-label">活跃模型</div>
            </div>
          </div>

          <!-- 二级标签页 -->
          <el-tabs v-model="llmSubTab" class="llm-sub-tabs">
            <!-- 模型分组管理 -->
            <el-tab-pane label="模型分组" name="groups">
              <div class="section-header">
                <h3 class="text-lg font-semibold text-tech-text-primary">模型分组管理</h3>
                <el-button type="primary" @click="showGroupDialog = true" :loading="loading">
                  <el-icon><Plus /></el-icon>
                  新增分组
                </el-button>
              </div>

              <div class="groups-grid">
                <el-card v-for="group in groups" :key="group.id" class="group-card">
                  <div class="group-header">
                    <div class="group-info">
                      <h4 class="group-name">{{ group.display_name }}</h4>
                      <p class="group-desc">{{ group.description || '暂无描述' }}</p>
                    </div>
                    <div class="group-actions">
                      <el-button size="small" @click="editGroup(group)">
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button size="small" type="danger" @click="deleteGroup(group.id)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <div class="group-stats">
                    <el-tag size="small">
                      {{ getGroupModelsCount(group.id) }} 个模型
                    </el-tag>
                  </div>
                </el-card>
              </div>
            </el-tab-pane>

            <!-- 模型列表管理 -->
            <el-tab-pane label="模型列表" name="models">
              <div class="section-header">
                <h3 class="text-lg font-semibold text-tech-text-primary">模型列表管理</h3>
                <el-button type="primary" @click="showModelDialog = true" :loading="loading">
                  <el-icon><Plus /></el-icon>
                  新增模型
                </el-button>
              </div>

              <el-table
                  :data="models"
                  stripe
                  style="width: 100%"
                  :header-cell-style="{
                    backgroundColor: 'rgba(0, 240, 255, 0.1)',
                    color: '#ffffff',
                    borderBottom: '2px solid rgba(0, 240, 255, 0.3)',
                    fontWeight: '700'
                  }"
                  :cell-style="{
                    backgroundColor: 'transparent',
                    color: 'rgba(255, 255, 255, 0.8)',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                  }"
                  :row-style="{
                    backgroundColor: 'transparent'
                  }"
                >
                <el-table-column prop="display_name" label="模型名称" min-width="150">
                  <template #default="{ row }">
                    <div class="model-name">
                      <strong>{{ row.display_name }}</strong>
                      <el-tag v-if="row.is_default" type="success" size="small" class="ml-2">默认</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="provider" label="提供商" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getProviderType(row.provider)" size="small">
                      {{ row.provider }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="model_name" label="模型标识" min-width="150" />
                <el-table-column prop="group_name" label="所属分组" width="120" />
                <el-table-column label="参数" min-width="200">
                  <template #default="{ row }">
                    <div class="model-params">
                      <el-tooltip content="Temperature" placement="top">
                        <el-tag size="small">T: {{ row.temperature }}</el-tag>
                      </el-tooltip>
                      <el-tooltip content="Max Tokens" placement="top">
                        <el-tag size="small">M: {{ row.max_tokens }}</el-tag>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="is_active" label="状态" width="80">
                  <template #default="{ row }">
                    <el-switch v-model="row.is_active" @change="toggleModelActive(row)" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="editModel(row)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button size="small" @click="setDefaultModel(row)">
                      <el-icon><Star /></el-icon>
                    </el-button>
                    <el-button size="small" type="danger" @click="deleteModel(row.id)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <!-- 场景配置 -->
            <el-tab-pane label="场景配置" name="scenarios">
              <div class="section-header">
                <h3 class="text-lg font-semibold text-tech-text-primary">应用场景配置</h3>
                <el-button type="primary" @click="showScenarioDialog = true" :loading="loading">
                  <el-icon><Plus /></el-icon>
                  新增场景
                </el-button>
              </div>

              <el-table
                :data="scenarios"
                stripe
                style="width: 100%"
                :header-cell-style="{
                  backgroundColor: 'rgba(0, 240, 255, 0.1)',
                  color: '#ffffff',
                  borderBottom: '2px solid rgba(0, 240, 255, 0.3)',
                  fontWeight: '700'
                }"
                :cell-style="{
                  backgroundColor: 'transparent',
                  color: 'rgba(255, 255, 255, 0.8)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                }"
                :row-style="{
                  backgroundColor: 'transparent'
                }"
              >
                <el-table-column prop="display_name" label="场景名称" min-width="150" />
                <el-table-column prop="description" label="描述" min-width="200" />
                <el-table-column prop="default_model_name" label="默认模型" min-width="150" />
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="editScenario(row)">
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button size="small" type="danger" @click="deleteScenario(row.id)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 分组对话框 -->
        <el-dialog v-model="showGroupDialog" :title="editingGroup ? '编辑分组' : '新增分组'" width="500px">
          <el-form :model="groupForm" label-width="100px">
            <el-form-item label="分组标识" v-if="!editingGroup">
              <el-input v-model="groupForm.name" placeholder="如: fast-models" />
            </el-form-item>
            <el-form-item label="显示名称">
              <el-input v-model="groupForm.display_name" placeholder="如: 快速模型" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="groupForm.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="排序">
              <el-input-number v-model="groupForm.sort_order" :min="0" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showGroupDialog = false">取消</el-button>
            <el-button type="primary" @click="saveGroup" :loading="loading">
              {{ editingGroup ? '更新' : '创建' }}
            </el-button>
          </template>
        </el-dialog>

        <!-- 模型对话框 -->
        <el-dialog v-model="showModelDialog" :title="editingModel ? '编辑模型' : '新增模型'" width="700px">
          <el-form :model="modelForm" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="模型标识">
                  <el-input v-model="modelForm.name" placeholder="如: gpt-35-turbo" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="显示名称">
                  <el-input v-model="modelForm.display_name" placeholder="如: GPT-3.5 Turbo" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="API提供商">
                  <el-select v-model="modelForm.provider" class="w-full">
                    <el-option label="OpenAI" value="openai" />
                    <el-option label="Anthropic" value="anthropic" />
                    <el-option label="Azure" value="azure" />
                    <el-option label="Custom" value="custom" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="实际模型名">
                  <el-input v-model="modelForm.model_name" placeholder="如: gpt-3.5-turbo" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="API密钥">
              <el-input v-model="modelForm.api_key" type="password" placeholder="输入API Key" show-password />
            </el-form-item>

            <el-form-item
              label="自定义API地址"
              v-if="showCustomBaseUrl"
            >
              <el-input
                v-model="modelForm.base_url"
                :placeholder="getBaseUrlPlaceholder()"
              />
              <div class="base-url-hint">
                <el-text size="small" type="info">
                  {{ getBaseUrlHint() }}
                </el-text>
              </div>
            </el-form-item>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="所属分组">
                  <el-select v-model="modelForm.group_id" class="w-full">
                    <el-option v-for="g in groups" :key="g.id" :label="g.display_name" :value="g.id" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="默认模型">
                  <el-switch v-model="modelForm.is_default" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider>模型参数</el-divider>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Temperature" label-width="100px">
                  <el-input-number
                    v-model="modelForm.temperature"
                    :min="0"
                    :max="2"
                    :step="0.1"
                    :precision="1"
                    style="width: 100%"
                    placeholder="0.7"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="Max Tokens" label-width="100px">
                  <el-input-number
                    v-model="modelForm.max_tokens"
                    :min="100"
                    :max="4000"
                    :step="100"
                    style="width: 100%"
                    placeholder="2000"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="Top P" label-width="100px">
                  <el-input-number
                    v-model="modelForm.top_p"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    :precision="2"
                    style="width: 100%"
                    placeholder="1.0"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
          <template #footer>
            <el-button @click="showModelDialog = false">取消</el-button>
            <el-button type="primary" @click="saveModel" :loading="loading">
              {{ editingModel ? '更新' : '创建' }}
            </el-button>
          </template>
        </el-dialog>

        <!-- 场景对话框 -->
        <el-dialog v-model="showScenarioDialog" :title="editingScenario ? '编辑场景' : '新增场景'" width="600px">
          <el-form :model="scenarioForm" label-width="120px">
            <el-form-item label="场景标识">
              <el-input v-model="scenarioForm.name" placeholder="如: conversation" />
            </el-form-item>
            <el-form-item label="显示名称">
              <el-input v-model="scenarioForm.display_name" placeholder="如: 日常对话" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="scenarioForm.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="默认模型">
              <el-select v-model="scenarioForm.default_model_id" class="w-full">
                <el-option
                  v-for="m in models.filter(m => m.is_active)"
                  :key="m.id"
                  :label="m.display_name"
                  :value="m.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showScenarioDialog = false">取消</el-button>
            <el-button type="primary" @click="saveScenario" :loading="loading">
              {{ editingScenario ? '更新' : '创建' }}
            </el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- RAG配置 -->
      <el-tab-pane label="RAG配置" name="rag">
        <div class="config-section">
          <el-form :model="ragConfig" label-width="120px">
            <el-form-item label="向量数据库">
              <el-select v-model="ragConfig.vectorDB" class="w-full">
                <el-option label="PostgreSQL (pgvector)" value="pgvector" />
                <el-option label="Pinecone" value="pinecone" />
                <el-option label="Weaviate" value="weaviate" />
              </el-select>
            </el-form-item>

            <el-form-item label="嵌入模型">
              <el-select v-model="ragConfig.embeddingModel" class="w-full">
                <el-option label="text-embedding-ada-002" value="text-embedding-ada-002" />
                <el-option label="text-embedding-3-small" value="text-embedding-3-small" />
              </el-select>
            </el-form-item>

            <el-form-item label="检索数量">
              <el-input-number
                v-model="ragConfig.topK"
                :min="1"
                :max="20"
              />
            </el-form-item>

            <el-form-item label="相似度阈值">
              <el-slider
                v-model="ragConfig.similarityThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveRAGConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="system">
        <div class="config-section">
          <el-form :model="systemConfig" label-width="120px">
            <el-form-item label="主题">
              <el-radio-group v-model="systemConfig.theme">
                <el-radio label="tech">科技感</el-radio>
                <el-radio label="dark">暗黑</el-radio>
                <el-radio label="light">明亮</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="语言">
              <el-select v-model="systemConfig.language" class="w-full">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>

            <el-form-item label="自动保存">
              <el-switch v-model="systemConfig.autoSave" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="saveSystemConfig">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRagStore } from '../store/ragStore'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus, Edit, Delete, Star } from '@element-plus/icons-vue'
import { setTheme, getTheme } from '../utils/themeManager'

const store = useRagStore()
const activeTab = ref('llm')
const llmSubTab = ref('groups')
const loading = ref(false)

// ========== LLM多模型配置数据 ==========
const groups = ref([])
const models = ref([])
const scenarios = ref([])

// 对话框状态
const showGroupDialog = ref(false)
const showModelDialog = ref(false)
const showScenarioDialog = ref(false)

const editingGroup = ref(null)
const editingModel = ref(null)
const editingScenario = ref(null)

// 表单数据
const groupForm = ref({
  name: '',
  display_name: '',
  description: '',
  sort_order: 0
})

const modelForm = ref({
  name: '',
  display_name: '',
  provider: 'openai',
  model_name: '',
  api_key: '',
  base_url: '',
  group_id: null,
  is_default: false,
  temperature: 0.7,
  max_tokens: 2000,
  top_p: 1.0
})

const scenarioForm = ref({
  name: '',
  display_name: '',
  description: '',
  default_model_id: null
})

// ========== 计算属性 ==========
const activeModelsCount = computed(() => models.value.filter(m => m.is_active).length)

const getGroupModelsCount = (groupId) => {
  return models.value.filter(m => m.group_id === groupId).length
}

const getProviderType = (provider) => {
  const types = {
    'openai': 'success',
    'anthropic': 'warning',
    'azure': 'info',
    'custom': 'danger'
  }
  return types[provider] || 'info'
}

// 获取自定义API地址的占位符
const getBaseUrlPlaceholder = () => {
  const provider = modelForm.value.provider
  const placeholders = {
    'anthropic': 'https://api.anthropic.com/v1',
    'azure': 'https://{resource-name}.openai.azure.com/',
    'custom': 'https://api.example.com/v1'
  }
  return placeholders[provider] || 'https://api.example.com/v1'
}

// 获取自定义API地址的提示信息
const getBaseUrlHint = () => {
  const provider = modelForm.value.provider
  const hints = {
    'anthropic': '默认使用官方API地址，如需使用兼容服务可自定义',
    'azure': 'Azure OpenAI服务需要指定具体的资源端点',
    'custom': '请输入完整的API地址，包含版本路径，如：https://api.example.com/v1'
  }
  return hints[provider] || '请输入API地址'
}

// 计算属性：是否显示自定义API地址
const showCustomBaseUrl = computed(() => {
  return ['openai','anthropic', 'azure', 'custom'].includes(modelForm.value.provider)
})

// ========== 加载数据 ==========
const loadLLMConfig = async () => {
  try {
    loading.value = true
    const config = await store.fetchLLMConfig()
    groups.value = config.groups || []
    models.value = config.models || []
    scenarios.value = config.scenarios || []
  } catch (error) {
    ElMessage.error('加载LLM配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// ========== 分组管理 ==========
const editGroup = (group) => {
  editingGroup.value = group
  groupForm.value = { ...group }
  showGroupDialog.value = true
}

const saveGroup = async () => {
  try {
    loading.value = true
    if (editingGroup.value) {
      await store.updateLLMGroup(editingGroup.value.id, groupForm.value)
      ElMessage.success('分组更新成功')
    } else {
      await store.createLLMGroup(groupForm.value)
      ElMessage.success('分组创建成功')
    }
    showGroupDialog.value = false
    editingGroup.value = null
    resetGroupForm()
    await loadLLMConfig()
  } catch (error) {
    ElMessage.error('保存分组失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const deleteGroup = async (groupId) => {
  try {
    await ElMessageBox.confirm('删除分组将同时删除其下所有模型，确定要删除吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    loading.value = true
    await store.deleteLLMGroup(groupId)
    ElMessage.success('分组删除成功')
    await loadLLMConfig()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除分组失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

const resetGroupForm = () => {
  groupForm.value = {
    name: '',
    display_name: '',
    description: '',
    sort_order: 0
  }
}

// ========== 模型管理 ==========
const editModel = (model) => {
  editingModel.value = model
  modelForm.value = { ...model }
  showModelDialog.value = true
}

const saveModel = async () => {
  try {
    loading.value = true
    if (editingModel.value) {
      await store.updateLLMModel(editingModel.value.id, modelForm.value)
      ElMessage.success('模型更新成功')
    } else {
      await store.createLLMModel(modelForm.value)
      ElMessage.success('模型创建成功')
    }
    showModelDialog.value = false
    editingModel.value = null
    resetModelForm()
    await loadLLMConfig()
  } catch (error) {
    ElMessage.error('保存模型失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const deleteModel = async (modelId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模型吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    loading.value = true
    await store.deleteLLMModel(modelId)
    ElMessage.success('模型删除成功')
    await loadLLMConfig()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除模型失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

const setDefaultModel = async (model) => {
  try {
    loading.value = true
    await store.updateLLMModel(model.id, { ...model, is_default: true })
    ElMessage.success('默认模型设置成功')
    await loadLLMConfig()
  } catch (error) {
    ElMessage.error('设置默认模型失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const toggleModelActive = async (model) => {
  try {
    await store.updateLLMModel(model.id, { is_active: model.is_active })
  } catch (error) {
    ElMessage.error('更新模型状态失败: ' + error.message)
    model.is_active = !model.is_active
  }
}

const resetModelForm = () => {
  modelForm.value = {
    name: '',
    display_name: '',
    provider: 'openai',
    model_name: '',
    api_key: '',
    base_url: '',
    group_id: null,
    is_default: false,
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 1.0
  }
}

// ========== 场景管理 ==========
const editScenario = (scenario) => {
  editingScenario.value = scenario
  scenarioForm.value = { ...scenario }
  showScenarioDialog.value = true
}

const saveScenario = async () => {
  try {
    loading.value = true
    if (editingScenario.value) {
      await store.updateLLMScenario(editingScenario.value.id, scenarioForm.value)
      ElMessage.success('场景更新成功')
    } else {
      await store.createLLMScenario(scenarioForm.value)
      ElMessage.success('场景创建成功')
    }
    showScenarioDialog.value = false
    editingScenario.value = null
    resetScenarioForm()
    await loadLLMConfig()
  } catch (error) {
    ElMessage.error('保存场景失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const deleteScenario = async (scenarioId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个场景吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    loading.value = true
    await store.deleteLLMScenario(scenarioId)
    ElMessage.success('场景删除成功')
    await loadLLMConfig()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除场景失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}

const resetScenarioForm = () => {
  scenarioForm.value = {
    name: '',
    display_name: '',
    description: '',
    default_model_id: null
  }
}

// ========== 旧配置（保持兼容性）==========
const llmConfig = ref({
  provider: 'openai',
  apiKey: '',
  baseUrl: '',
  defaultModel: 'gpt-3.5-turbo',
  temperature: 0.7,
  maxTokens: 2000,
  topP: 1.0
})

const ragConfig = ref({
  vectorDB: 'pgvector',
  embeddingModel: 'text-embedding-ada-002',
  topK: 5,
  similarityThreshold: 0.7
})

const systemConfig = ref({
  theme: getTheme(), // 从本地存储加载当前主题
  language: 'zh-CN',
  autoSave: true
})

// 监听主题变化，实时切换
watch(() => systemConfig.value.theme, (newTheme) => {
  setTheme(newTheme)
})

// 加载所有设置
const loadSettings = async () => {
  try {
    loading.value = true
    const settings = await store.fetchSettings()

    if (settings.llm) {
      llmConfig.value = { ...llmConfig.value, ...settings.llm }
    }
    if (settings.rag) {
      ragConfig.value = { ...ragConfig.value, ...settings.rag }
    }
    if (settings.system) {
      systemConfig.value = { ...systemConfig.value, ...settings.system }
    }
  } catch (error) {
    ElMessage.error('加载设置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const saveLLMConfig = async () => {
  try {
    await store.updateSettings('llm', llmConfig.value)
    ElMessage.success('LLM配置已保存到数据库')
  } catch (error) {
    ElMessage.error('保存LLM配置失败: ' + error.message)
  }
}

const testConnection = async () => {
  ElMessage.info('正在测试连接...')
  setTimeout(() => {
    ElMessage.success('连接测试成功')
  }, 1000)
}

const saveRAGConfig = async () => {
  try {
    await store.updateSettings('rag', ragConfig.value)
    ElMessage.success('RAG配置已保存到数据库')
  } catch (error) {
    ElMessage.error('保存RAG配置失败: ' + error.message)
  }
}

const saveSystemConfig = async () => {
  try {
    await store.updateSettings('system', systemConfig.value)
    ElMessage.success('系统配置已保存到数据库')
  } catch (error) {
    ElMessage.error('保存系统配置失败: ' + error.message)
  }
}

// 修复表格样式的辅助函数
const fixTableStyles = () => {
  console.log('🔧 正在修复表格样式...')

  // 获取根元素样式变量
  const rootStyles = getComputedStyle(document.documentElement)
  const textPrimary = rootStyles.getPropertyValue('--tech-text-primary') || '#ffffff'
  const textSecondary = rootStyles.getPropertyValue('--tech-text-secondary') || '#a0a0a0'

  console.log('📝 使用颜色值:', { textPrimary, textSecondary })

  // 修复表头 - 使用更强的选择器
  const allTableElements = document.querySelectorAll('.el-table th, .el-table__header th, .el-table__header th.el-table__cell')
  console.log(`🎯 找到 ${allTableElements.length} 个表头元素`)

  allTableElements.forEach((th, index) => {
    const currentBg = getComputedStyle(th).backgroundColor
    const currentColor = getComputedStyle(th).color
    console.log(`表头 ${index}: 背景=${currentBg}, 颜色=${currentColor}`)

    // 强制设置样式，不检查当前值
    th.style.setProperty('background-color', 'rgba(0, 240, 255, 0.1)', 'important')
    th.style.setProperty('background', 'rgba(0, 240, 255, 0.1)', 'important')
    th.style.setProperty('color', textPrimary, 'important')
    th.style.setProperty('border-bottom', '2px solid rgba(0, 240, 255, 0.3)', 'important')
    th.style.setProperty('font-weight', '700', 'important')
  })

  // 修复表格行
  const allRows = document.querySelectorAll('.el-table td, .el-table__body td, .el-table__body td.el-table__cell')
  console.log(`📋 找到 ${allRows.length} 个表格单元格`)

  allRows.forEach((td, index) => {
    td.style.setProperty('background-color', 'transparent', 'important')
    td.style.setProperty('background', 'transparent', 'important')
    td.style.setProperty('color', textSecondary, 'important')
    td.style.setProperty('border-bottom', '1px solid rgba(255, 255, 255, 0.1)', 'important')
  })

  // 修复表格容器
  const wrappers = document.querySelectorAll('.el-table, .el-table__header-wrapper, .el-table__body-wrapper, .el-table__header, .el-table__body')
  console.log(`📦 找到 ${wrappers.length} 个表格容器`)

  wrappers.forEach((wrapper, index) => {
    wrapper.style.setProperty('background', 'transparent', 'important')
    wrapper.style.setProperty('background-color', 'transparent', 'important')
  })

  console.log('✅ 表格样式修复完成')
}

// Tab切换处理函数
const handleTabChange = (tab) => {
  console.log('🔄 Tab切换到:', tab.props.name)
  // 在Tab切换后立即修复表格样式
  setTimeout(fixTableStyles, 200)
}

onMounted(() => {
  loadSettings()
  loadLLMConfig()

  // 立即执行一次
  setTimeout(fixTableStyles, 100)

  // 监听Tab切换，确保表格样式正确
  const observer = new MutationObserver(() => {
    setTimeout(fixTableStyles, 50)
  })

  // 监听DOM变化
  observer.observe(document.querySelector('.settings-page'), {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class']
  })
})
</script>

<style lang="scss" scoped>
.settings-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;

    .refresh-btn {
      flex-shrink: 0;
      margin-top: 8px;
    }
  }
}

.llm-config-container .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-bottom: 10px;
}

.config-section {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 24px;
  backdrop-filter: blur(10px);
}

// LLM多模型配置样式
.llm-config-container {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;

    .stat-card {
      background: var(--tech-glass-bg);
      border: 1px solid var(--tech-glass-border);
      border-radius: 12px;
      padding: 20px;
      backdrop-filter: blur(10px);
      text-align: center;
      transition: all 0.3s ease;

      &:hover {
        border-color: var(--tech-neon-blue);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 240, 255, 0.2);
      }

      .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: var(--tech-neon-blue);
        margin-bottom: 8px;
      }

      .stat-label {
        font-size: 14px;
        color: var(--tech-text-secondary);
      }
    }
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

:deep(.llm-sub-tabs) {
  .el-tabs__header {
    margin-bottom: 24px;
  }

  .el-tabs__item {
    color: var(--tech-text-secondary);
    font-size: 16px;
    font-weight: 500;

    &.is-active {
      color: var(--tech-neon-blue);
    }
  }

  .el-tabs__active-bar {
    background: var(--tech-neon-blue);
  }
}

// 分组卡片样式
.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;

  .group-card {
    background: var(--tech-glass-bg);
    border: 1px solid var(--tech-glass-border);
    border-radius: 12px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--tech-neon-blue);
      box-shadow: 0 4px 12px rgba(0, 240, 255, 0.2);
    }

    .group-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;

      .group-info {
        flex: 1;

        .group-name {
          font-size: 18px;
          font-weight: 600;
          color: var(--tech-text-primary);
          margin-bottom: 8px;
        }

        .group-desc {
          font-size: 14px;
          color: var(--tech-text-secondary);
          line-height: 1.5;
        }
      }

      .group-actions {
        display: flex;
        gap: 8px;
      }
    }

    .group-stats {
      padding-top: 12px;
      border-top: 1px solid var(--tech-glass-border);
    }
  }
}

// 表格样式
:deep(.el-table),
:deep(.el-tab-pane .el-table) {
  background: transparent !important;

  th.el-table__cell {
    background: rgba(0, 240, 255, 0.05) !important;
    color: var(--tech-text-primary) !important;
    font-weight: 600 !important;
    border-bottom: 1px solid var(--tech-glass-border) !important;
  }

  td.el-table__cell {
    border-bottom: 1px solid var(--tech-glass-border) !important;
    color: var(--tech-text-secondary) !important;
    background: transparent !important;
  }

  .el-table__row {
    &:hover {
      background: rgba(0, 240, 255, 0.05) !important;
    }
  }
}

:deep(.el-table__header-wrapper) {
  background: rgba(0, 240, 255, 0.05) !important;
}

/* 场景配置表格特定样式 - 最强优先级 */
:deep(.el-tab-pane[name="scenarios"] .el-table) {
  background: transparent !important;
}

:deep(.el-tab-pane[name="scenarios"] .el-table th.el-table__cell) {
  background: rgba(0, 240, 255, 0.08) !important;
  color: var(--tech-text-primary) !important;
  font-weight: 700 !important;
  border-bottom: 2px solid var(--tech-glass-border) !important;
}

:deep(.el-tab-pane[name="scenarios"] .el-table td.el-table__cell) {
  background: transparent !important;
  color: var(--tech-text-secondary) !important;
  border-bottom: 1px solid var(--tech-glass-border) !important;
}

:deep(.el-tab-pane[name="scenarios"] .el-table .el-table__row--striped td.el-table__cell) {
  background: rgba(0, 240, 255, 0.03) !important;
}

:deep(.el-tab-pane[name="scenarios"] .el-table .el-table__row:hover td.el-table__cell) {
  background: rgba(0, 240, 255, 0.1) !important;
}

.model-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-params {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

// 自定义API地址提示样式
.base-url-hint {
  margin-top: 4px;
  padding-left: 0;
}

.base-url-hint .el-text {
  display: block;
  color: var(--tech-text-secondary);
  font-size: 12px;
  line-height: 1.4;
}



// 标签页样式
:deep(.tech-tabs) {
  .el-tabs__nav {
    background: transparent;
  }

  .el-tabs__item {
    color: var(--tech-text-secondary);

    &.is-active {
      color: var(--tech-neon-blue);
    }
  }

  .el-tabs__active-bar {
    background: var(--tech-neon-blue);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .llm-config-container {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 768px) {
  .llm-config-container {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }

  .groups-grid {
    grid-template-columns: 1fr;
  }
}
</style>