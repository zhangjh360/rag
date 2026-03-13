<template>
  <div class="chat-container">
    <!-- 会话列表侧边栏 -->
    <div class="chat-sidebar">
      <ChatSidebar
        :sessions="sessions"
        :activeSessionId="activeSessionId"
        @select="selectSession"
        @create="createNewSession"
        @delete="deleteSession"
      />
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 聊天标题栏 -->
      <div class="chat-header">
        <div class="header-content">
          <h2 class="chat-title">
            {{ currentSession?.title || '新对话' }}
          </h2>
          <div class="header-controls">
            <!-- 模型选择 -->
            <el-select
              v-model="selectedModel"
              size="small"
              class="model-select"
              placeholder="选择模型"
              :loading="loadingModels"
            >
              <el-option-group
                v-for="(models, provider) in groupedModelOptions"
                :key="provider"
                :label="provider"
              >
                <el-option
                  v-for="model in models"
                  :key="model.value"
                  :label="model.label"
                  :value="model.value"
                />
              </el-option-group>
            </el-select>
            <!-- RAG开关 -->
            <el-switch
              v-model="useRAG"
              active-text="RAG"
              inactive-text="普通"
              size="small"
            />
            <!-- 检索设置 -->
            <RetrievalSettings
              v-if="useRAG"
              v-model="retrievalSettings"
              @apply="onRetrievalSettingsApply"
            />
            <!-- 查询结果侧边栏切换按钮 -->
            <el-button
              v-if="useRAG && currentQueryResult"
              size="small"
              :icon="resultSidebarVisible ? 'Hide' : 'View'"
              @click="toggleResultSidebar"
              class="toggle-sidebar-btn"
            >
              {{ resultSidebarVisible ? '隐藏' : '显示' }}检索结果
            </el-button>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <ChatWindow
        :messages="currentMessages"
        :loading="isLoading"
        ref="chatWindow"
        class="chat-messages"
        @regenerate="handleRegenerate"
      />

      <!-- 输入区域 -->
      <div class="chat-input-wrapper">
        <InputBar
          v-model="inputMessage"
          :disabled="isLoading"
          :session-id="activeSessionId || 'temp'"
          @send="sendMessage"
          @send-with-images="sendMessageWithImages"
          @stop="stopGeneration"
          :is-generating="isGenerating"
        />
      </div>
    </div>

    <!-- 查询结果侧边栏 -->
    <div
      v-if="useRAG && currentQueryResult"
      class="result-sidebar"
      :class="{ 'is-visible': resultSidebarVisible }"
    >
      <div class="sidebar-header">
        <h3 class="sidebar-title">检索结果</h3>
        <el-button
          text
          :icon="'Close'"
          @click="toggleResultSidebar"
          class="close-btn"
        />
      </div>
      <div class="sidebar-content">
        <QueryResult :result="currentQueryResult" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatWindow from '../components/chat/ChatWindow.vue'
import InputBar from '../components/chat/InputBar.vue'
import RetrievalSettings from '../components/query/RetrievalSettings.vue'
import QueryResult from '../components/query/QueryResult.vue'
import { useChatStore } from '../store/chatStore'
import llmService from '../services/llmService'
import { queryDocumentsV2, formatQueryResults } from '../services/queryService'
import api from '../services/api'  // 添加api导入

const chatStore = useChatStore()

// 状态
const sessions = computed(() => chatStore.sessions)
const activeSessionId = computed(() => chatStore.activeSessionId)
const currentSession = computed(() => chatStore.currentSession)
const currentMessages = computed(() => chatStore.currentMessages)
const isLoading = ref(false)
const isGenerating = ref(false)
const inputMessage = ref('')
const selectedModel = ref('') // 初始为空，将在加载模型后设置默认模型
const useRAG = ref(true)

// 检索相关状态
const retrievalSettings = ref({
  method: 'hybrid',
  mode: 'auto',
  namespace: null,
  topK: 10,
  alpha: 0.5,
  similarityThreshold: 0.0
})
const currentQueryResult = ref(null)
const resultSidebarVisible = ref(true) // 侧边栏默认显示

// 模型相关状态
const availableModels = ref([])
const loadingModels = ref(false)
const groupedModelOptions = ref({})

// Refs
const chatWindow = ref(null)

// 方法
const selectSession = async (sessionId) => {
  await chatStore.selectSession(sessionId)
}

const createNewSession = async () => {
  const session = await chatStore.createSession()
  if (session) {
    ElMessage.success('新会话已创建')
  }
}

const deleteSession = async (sessionId) => {
  await chatStore.deleteSession(sessionId)
  ElMessage.success('会话已删除')
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  const message = inputMessage.value
  inputMessage.value = ''
  isLoading.value = true
  isGenerating.value = true

  try {
    // 如果开启RAG,先执行查询v2
    if (useRAG.value) {
      console.log('执行查询v2...', retrievalSettings.value)

      const queryResponse = await queryDocumentsV2({
        query: message,
        retrievalMode: retrievalSettings.value.mode,
        retrievalMethod: retrievalSettings.value.method,
        namespace: retrievalSettings.value.namespace,
        topK: retrievalSettings.value.topK,
        alpha: retrievalSettings.value.alpha,
        similarityThreshold: retrievalSettings.value.similarityThreshold,
        sessionId: activeSessionId.value
      })

      if (queryResponse.success) {
        // 格式化并显示查询结果
        currentQueryResult.value = formatQueryResults(queryResponse.data)
        console.log('查询结果:', currentQueryResult.value)

        // 提取相关上下文(取前5个结果)
        const context = currentQueryResult.value.results
          .slice(0, 5)
          .map(r => `[${r.domainDisplayName}] ${r.content}`)
          .join('\n\n')

        console.log('提取上下文:', context.substring(0, 200) + '...')

        // 发送带上下文的消息
        await chatStore.sendMessage({
          message,
          model: selectedModel.value,
          useRAG: true,
          stream: true,
          namespace: retrievalSettings.value.namespace,  // 传递领域参数
          context  // 传递上下文
        })
      } else {
        console.error('查询失败:', queryResponse.error)
        ElMessage.warning(`检索失败: ${queryResponse.error}, 降级为普通对话`)

        // 降级为普通聊天
        await chatStore.sendMessage({
          message,
          model: selectedModel.value,
          useRAG: false,
          stream: true,
          namespace: retrievalSettings.value.namespace  // 即使降级也传递领域参数
        })
      }
    } else {
      // 普通聊天(不使用RAG)
      currentQueryResult.value = null
      await chatStore.sendMessage({
        message,
        model: selectedModel.value,
        useRAG: false,
        stream: true,
        namespace: retrievalSettings.value.namespace  // 普通聊天也可传递领域参数(虽然不会使用)
      })
    }

    // 滚动到底部
    await nextTick()
    chatWindow.value?.scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败：' + error.message)
  } finally {
    isLoading.value = false
    isGenerating.value = false
  }
}

const sendMessageWithImages = async ({ text, images }) => {
  console.log('sendMessageWithImages 被调用:', { text, images })

  if (!text.trim() && images.length === 0) {
    console.log('没有文本也没有图片，取消发送')
    return
  }

  // 设置加载状态
  isLoading.value = true
  isGenerating.value = true

  try {
    // 确保有活动会话
    if (!activeSessionId.value) {
      console.log('没有活动会话，创建新会话')
      await createNewSession()
    }

    // 提取图片ID列表
    const imageIds = images.map(img => img.id)
    console.log('图片ID列表:', imageIds)

    // 准备请求数据
    const requestData = {
      session_id: activeSessionId.value,
      message: text || '请查看图片',
      model: selectedModel.value,
      use_rag: useRAG.value,
      stream: false,  // 带图片的消息暂时不使用流式响应
      image_ids: imageIds,  // 传递图片ID列表
      // RAG相关参数
      namespace: retrievalSettings.value.namespace,
      retrieval_mode: retrievalSettings.value.mode,
      retrieval_method: retrievalSettings.value.method,
      top_k: retrievalSettings.value.topK,
      alpha: retrievalSettings.value.alpha,
      similarity_threshold: retrievalSettings.value.similarityThreshold
    }

    console.log('发送带图片的消息:', requestData)

    // 调用API发送消息
    const response = await api.post('/api/chat/send', requestData)

    console.log('发送响应:', response.data)

    if (response.data) {
      // 重新加载消息列表以获取最新消息（包括图片）
      await chatStore.loadMessages(activeSessionId.value)

      // 滚动到底部
      await nextTick()
      chatWindow.value?.scrollToBottom()

      ElMessage.success('消息发送成功')
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败：' + (error.response?.data?.detail || error.message))
  } finally {
    isLoading.value = false
    isGenerating.value = false
  }
}

const stopGeneration = () => {
  chatStore.stopGeneration()
  isGenerating.value = false
}

// 重新生成消息
const handleRegenerate = async (assistantMessage) => {
  try {
    // 找到要重新生成的助手消息在列表中的位置
    const messages = currentMessages.value
    const assistantIndex = messages.findIndex(m => m === assistantMessage)

    if (assistantIndex === -1 || assistantIndex === 0) {
      ElMessage.warning('无法重新生成此消息')
      return
    }

    // 找到上一条用户消息
    let userMessage = null
    for (let i = assistantIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMessage = messages[i]
        break
      }
    }

    if (!userMessage) {
      ElMessage.warning('找不到对应的用户消息')
      return
    }

    // 删除当前助手消息和之后的所有消息
    messages.splice(assistantIndex)

    isLoading.value = true
    isGenerating.value = true

    // 重新发送消息(使用相同的设置)
    const message = userMessage.content

    // 如果开启RAG,先执行查询v2
    if (useRAG.value) {
      const queryResponse = await queryDocumentsV2({
        query: message,
        retrievalMode: retrievalSettings.value.mode,
        retrievalMethod: retrievalSettings.value.method,
        namespace: retrievalSettings.value.namespace,
        topK: retrievalSettings.value.topK,
        alpha: retrievalSettings.value.alpha,
        similarityThreshold: retrievalSettings.value.similarityThreshold,
        sessionId: activeSessionId.value
      })

      if (queryResponse.success) {
        currentQueryResult.value = formatQueryResults(queryResponse.data)

        const context = currentQueryResult.value.results
          .slice(0, 5)
          .map(r => `[${r.domainDisplayName}] ${r.content}`)
          .join('\n\n')

        await chatStore.sendMessage({
          message,
          model: selectedModel.value,
          useRAG: true,
          stream: true,
          namespace: retrievalSettings.value.namespace,
          context
        })
      } else {
        await chatStore.sendMessage({
          message,
          model: selectedModel.value,
          useRAG: false,
          stream: true,
          namespace: retrievalSettings.value.namespace
        })
      }
    } else {
      currentQueryResult.value = null
      await chatStore.sendMessage({
        message,
        model: selectedModel.value,
        useRAG: false,
        stream: true,
        namespace: retrievalSettings.value.namespace
      })
    }

    await nextTick()
    chatWindow.value?.scrollToBottom()
  } catch (error) {
    console.error('重新生成失败:', error)
    ElMessage.error('重新生成失败：' + error.message)
  } finally {
    isLoading.value = false
    isGenerating.value = false
  }
}

const toggleResultSidebar = () => {
  resultSidebarVisible.value = !resultSidebarVisible.value
}

const onRetrievalSettingsApply = (newSettings) => {
  retrievalSettings.value = { ...newSettings }
  console.log('应用检索设置:', retrievalSettings.value)
  ElMessage.success('检索设置已更新')
}

// 加载可用模型
const loadAvailableModels = async () => {
  try {
    loadingModels.value = true
    const models = await llmService.getAllModels()
    console.log('【调试】原始模型数据:', models)

    // 只保留聊天模型
    const chatModels = llmService.getChatModels(models)
    console.log('【调试】过滤后的聊天模型:', chatModels)
    availableModels.value = chatModels

    // 按提供商分组
    const grouped = llmService.getGroupedModelOptions(chatModels)
    console.log('【调试】分组的模型选项:', grouped)
    groupedModelOptions.value = grouped

    // 设置默认模型：优先选择 is_default=true 的模型，否则选择第一个
    if (chatModels.length > 0) {
      const defaultModel = chatModels.find(m => m.is_default === true)
      selectedModel.value = defaultModel ? defaultModel.name : chatModels[0].name
      console.log('✓ 选择默认模型:', selectedModel.value)
    }

    console.log('✓ 已加载模型:', chatModels.length, '个')
    console.log('✓ 分组结果:', Object.keys(grouped).join(', '))
  } catch (error) {
    console.error('✗ 加载模型失败:', error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

// 生命周期
onMounted(async () => {
  await chatStore.loadSessions()
  await loadAvailableModels()
})
</script>

<style lang="scss" scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 64px);
  background: transparent;
  gap: 1px;
  padding: 0;
}

.chat-sidebar {
  width: 320px;
  flex-shrink: 0;
  background: var(--tech-glass-bg);
  border-right: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(
      180deg,
      transparent,
      var(--tech-neon-blue) 30%,
      var(--tech-neon-blue) 70%,
      transparent
    );
    opacity: 0.3;
  }
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: transparent;
  overflow: hidden;
}

.chat-header {
  padding: 20px 24px;
  background: var(--tech-glass-bg);
  border-bottom: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-neon-blue) 50%,
      transparent
    );
    opacity: 0.4;
  }

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .chat-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--tech-text-primary);
    background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.chat-messages {
  flex: 1;
  overflow: auto;
}

.chat-input-wrapper {
  padding: 20px 24px;
  padding-bottom: 60px; // 增加底部内边距，避免与状态栏贴在一起
  background: var(--tech-glass-bg);
  border-top: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--tech-neon-purple) 50%,
      transparent
    );
    opacity: 0.4;
  }
}

// Element Plus 组件样式覆盖
:deep(.model-select) {
  width: 128px;

  .el-input__wrapper {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--tech-glass-border);
    box-shadow: none;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--tech-border-hover);
    }

    &.is-focus {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--tech-neon-blue);
      box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.2);
    }
  }

  .el-input__inner {
    color: var(--tech-text-primary);
  }
}

:deep(.el-switch) {
  &.is-checked .el-switch__core {
    background: var(--tech-neon-blue);
    border-color: var(--tech-neon-blue);
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.4);
  }

  .el-switch__core {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid var(--tech-glass-border);
  }

  .el-switch__action {
    background: #fff;
  }
}

// 查询结果侧边栏
.result-sidebar {
  width: 420px;
  flex-shrink: 0;
  background: var(--tech-glass-bg);
  border-left: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  position: relative;
  transform: translateX(100%);
  transition: transform 0.3s ease;

  &.is-visible {
    transform: translateX(0);
  }

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(
      180deg,
      transparent,
      var(--tech-neon-purple) 30%,
      var(--tech-neon-purple) 70%,
      transparent
    );
    opacity: 0.3;
  }

  .sidebar-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--tech-glass-border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 1px;
      background: linear-gradient(
        90deg,
        transparent,
        var(--tech-neon-purple) 50%,
        transparent
      );
      opacity: 0.4;
    }

    .sidebar-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--tech-text-primary);
      background: linear-gradient(135deg, var(--tech-neon-purple), var(--tech-neon-blue));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0;
    }

    .close-btn {
      color: var(--tech-text-secondary);
      transition: color 0.3s ease;

      &:hover {
        color: var(--tech-neon-blue);
      }
    }
  }

  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px 24px;

    // 自定义滚动条
    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--tech-neon-purple);
      border-radius: 3px;
      opacity: 0.6;

      &:hover {
        background: var(--tech-neon-blue);
      }
    }
  }
}

.toggle-sidebar-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--tech-glass-border);
  color: var(--tech-text-primary);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--tech-neon-blue);
    color: var(--tech-neon-blue);
  }
}
</style>