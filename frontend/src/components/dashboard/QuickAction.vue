<template>
  <div class="quick-action" @click="$emit('click')">
    <el-icon class="action-icon" :size="20">
      <component :is="icon" />
    </el-icon>
    <span class="action-label">{{ label }}</span>
    <el-icon class="arrow-icon"><ArrowRight /></el-icon>
  </div>
</template>

<script setup>
import { ArrowRight } from '@element-plus/icons-vue'

defineProps({
  icon: Object, // 改为Object类型
  label: String
})

defineEmits(['click'])
</script>

<style lang="scss" scoped>
.quick-action {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--tech-glass-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(0, 212, 255, 0.05);
    border-color: var(--tech-neon-blue);
    transform: translateX(4px);

    .action-icon {
      color: var(--tech-neon-blue);
    }

    .arrow-icon {
      transform: translateX(4px);
    }
  }

  .action-icon {
    color: var(--tech-text-secondary);
    margin-right: 12px;
    transition: color 0.3s ease;
  }

  .action-label {
    flex: 1;
    color: var(--tech-text-primary);
    font-size: 14px;
  }

  .arrow-icon {
    color: var(--tech-text-muted);
    transition: transform 0.3s ease;
  }
}
</style>