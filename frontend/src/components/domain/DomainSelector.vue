<template>
  <div class="domain-selector">
    <el-select
      v-model="selectedNamespace"
      :placeholder="placeholder"
      :size="size"
      :clearable="clearable"
      :filterable="true"
      :loading="loading"
      :disabled="disabled"
      class="selector"
      @change="handleChange"
    >
      <el-option
        v-for="domain in domains"
        :key="domain.namespace"
        :label="domain.display_name"
        :value="domain.namespace"
        :disabled="!domain.is_active"
      >
        <div class="domain-option">
          <el-icon v-if="domain.icon" :size="16" class="option-icon">
            <component :is="getIconComponent(domain.icon)" />
          </el-icon>
          <span class="option-text">{{ domain.display_name }}</span>
          <el-tag
            v-if="showStats && domain.document_count !== undefined"
            size="small"
            type="info"
            class="option-stats"
          >
            {{ domain.document_count }} 文档
          </el-tag>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Folder,
  Document,
  Tools,
  ShoppingCart,
  Ticket,
  QuestionFilled
} from '@element-plus/icons-vue'
import { getAllDomains } from '@/services/knowledgeDomains'

const props = defineProps({
  // v-model 绑定的值
  modelValue: {
    type: String,
    default: ''
  },
  // 占位符文本
  placeholder: {
    type: String,
    default: '请选择知识领域'
  },
  // 尺寸
  size: {
    type: String,
    default: 'default'
  },
  // 是否可清除
  clearable: {
    type: Boolean,
    default: true
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否显示统计信息
  showStats: {
    type: Boolean,
    default: false
  },
  // 是否包含未启用的领域
  includeInactive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'domain-loaded'])

// 状态
const domains = ref([])
const loading = ref(false)
const selectedNamespace = ref(props.modelValue)

// 监听外部 v-model 变化
watch(() => props.modelValue, (newVal) => {
  selectedNamespace.value = newVal
})

// 获取图标组件
const getIconComponent = (iconName) => {
  const iconMap = {
    'folder': Folder,
    'document': Document,
    'code': Document,
    'tools': Tools,
    'support': Tools,
    'shopping': ShoppingCart,
    'ticket': Ticket
  }
  return iconMap[iconName] || QuestionFilled
}

// 加载领域列表
const loadDomains = async () => {
  loading.value = true
  try {
    const response = await getAllDomains({
      include_inactive: props.includeInactive,
      with_stats: props.showStats,
      limit: 100
    })
    domains.value = response.domains || []
    emit('domain-loaded', domains.value)
  } catch (error) {
    console.error('加载领域列表失败:', error)
    ElMessage.error('加载领域列表失败')
  } finally {
    loading.value = false
  }
}

// 处理选择变化
const handleChange = (namespace) => {
  emit('update:modelValue', namespace)

  // 找到选中的领域对象
  const selectedDomain = domains.value.find(d => d.namespace === namespace)
  emit('change', selectedDomain)
}

// 刷新领域列表 (暴露给父组件)
const refresh = () => {
  loadDomains()
}

// 挂载时加载
onMounted(() => {
  loadDomains()
})

// 暴露方法给父组件
defineExpose({
  refresh,
  loadDomains
})
</script>

<style lang="scss" scoped>
.domain-selector {
  .selector {
    width: 100%;
  }

  .domain-option {
    display: flex;
    align-items: center;
    gap: 8px;

    .option-icon {
      color: var(--el-text-color-secondary);
    }

    .option-text {
      flex: 1;
    }

    .option-stats {
      margin-left: auto;
      font-size: 12px;
    }
  }
}

// 下拉选项悬停效果
:deep(.el-select-dropdown__item) {
  transition: all 0.2s ease;

  &:hover {
    background: var(--el-fill-color-light);
  }
}
</style>
