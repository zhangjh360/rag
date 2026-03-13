<template>
  <el-tag
    :type="tagType"
    :color="customColor"
    :size="size"
    :effect="effect"
    :closable="closable"
    :disable-transitions="false"
    class="domain-badge"
    @close="handleClose"
  >
    <el-icon v-if="showIcon && icon" class="badge-icon" :size="iconSize">
      <component :is="iconComponent" />
    </el-icon>
    <span class="badge-text">{{ displayName }}</span>
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import {
  Folder,
  Document,
  Tools,
  ShoppingCart,
  Ticket,
  QuestionFilled
} from '@element-plus/icons-vue'

const props = defineProps({
  // 领域命名空间
  namespace: {
    type: String,
    required: true
  },
  // 显示名称 (如果不提供,使用 namespace)
  displayName: {
    type: String,
    default: ''
  },
  // 图标名称
  icon: {
    type: String,
    default: ''
  },
  // 自定义颜色 (hex)
  color: {
    type: String,
    default: ''
  },
  // 尺寸: large / default / small
  size: {
    type: String,
    default: 'default'
  },
  // 主题: dark / light / plain
  effect: {
    type: String,
    default: 'light'
  },
  // 是否可关闭
  closable: {
    type: Boolean,
    default: false
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close'])

// 显示名称
const displayName = computed(() => {
  return props.displayName || props.namespace
})

// Element Plus Tag 类型映射
const tagType = computed(() => {
  if (props.color) return '' // 有自定义颜色时不使用预设类型

  // 根据命名空间返回不同的类型
  const typeMap = {
    'default': '',
    'technical_docs': 'primary',
    'product_support': 'warning',
    'customer_service': 'success',
    'internal': 'info',
    'public': 'success'
  }
  return typeMap[props.namespace] || ''
})

// 自定义颜色
const customColor = computed(() => {
  return props.color || ''
})

// 图标尺寸
const iconSize = computed(() => {
  const sizeMap = {
    'large': 16,
    'default': 14,
    'small': 12
  }
  return sizeMap[props.size] || 14
})

// 图标组件映射
const iconComponent = computed(() => {
  const iconMap = {
    'folder': Folder,
    'document': Document,
    'code': Document,
    'tools': Tools,
    'support': Tools,
    'shopping': ShoppingCart,
    'ticket': Ticket
  }
  return iconMap[props.icon] || QuestionFilled
})

// 关闭处理
const handleClose = () => {
  emit('close', props.namespace)
}
</script>

<style lang="scss" scoped>
.domain-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: default;
  transition: all 0.3s ease;

  .badge-icon {
    display: inline-flex;
    align-items: center;
  }

  .badge-text {
    line-height: 1;
  }

  &:hover {
    opacity: 0.9;
  }
}

// 自定义颜色时的样式调整
.domain-badge[style*="background-color"] {
  color: white;
  border: none;

  :deep(.el-icon) {
    color: white;
  }

  &:hover {
    opacity: 0.85;
  }
}
</style>
