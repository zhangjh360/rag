<template>
  <div class="stats-card" :class="`stats-card--${color}`">
    <div class="stats-icon">
      <el-icon :size="24">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="stats-content">
      <div class="stats-title">{{ title }}</div>
      <div class="stats-value">
        <span class="value">{{ formattedValue }}</span>
        <span v-if="trend" class="trend" :class="{ positive: trend > 0 }">
          <el-icon><ArrowUp v-if="trend > 0" /><ArrowDown v-else /></el-icon>
          {{ Math.abs(trend) }}%
        </span>
      </div>
      <div v-if="subtitle" class="stats-subtitle">{{ subtitle }}</div>
    </div>
    <div class="stats-bg"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  title: String,
  value: Number,
  icon: Object, // 改为Object类型接收图标组件
  color: {
    type: String,
    default: 'blue'
  },
  trend: Number,
  subtitle: String
})

const formattedValue = computed(() => {
  if (props.value >= 1000) {
    return (props.value / 1000).toFixed(1) + 'k'
  }
  return props.value.toString()
})
</script>

<style lang="scss" scoped>
.stats-card {
  position: relative;
  padding: 20px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  overflow: hidden;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 200px;
  margin: 0 4px; // 添加左右边距
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--tech-shadow-glow);
    border-color: var(--tech-border-hover);

    .stats-bg {
      opacity: 0.15;
    }
  }

  &--blue {
    .stats-icon { color: var(--tech-neon-blue); }
    .stats-bg { background: linear-gradient(135deg, var(--tech-neon-blue), transparent); }
  }

  &--purple {
    .stats-icon { color: var(--tech-neon-purple); }
    .stats-bg { background: linear-gradient(135deg, var(--tech-neon-purple), transparent); }
  }

  &--green {
    .stats-icon { color: var(--tech-neon-green); }
    .stats-bg { background: linear-gradient(135deg, var(--tech-neon-green), transparent); }
  }

  &--yellow {
    .stats-icon { color: var(--tech-neon-yellow); }
    .stats-bg { background: linear-gradient(135deg, var(--tech-neon-yellow), transparent); }
  }

  .stats-icon {
    margin-bottom: 8px;
  }

  .stats-title {
    font-size: 12px;
    color: var(--tech-text-secondary);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .stats-subtitle {
    font-size: 11px;
    color: var(--tech-text-muted);
    margin-top: 4px;
  }

  .stats-value {
    display: flex;
    align-items: baseline;
    gap: 6px;
    flex-wrap: wrap;

    .value {
      font-size: 24px;
      font-weight: bold;
      color: var(--tech-text-primary);
    }

    .trend {
      display: flex;
      align-items: center;
      font-size: 12px;
      color: var(--tech-neon-pink);

      &.positive {
        color: var(--tech-neon-green);
      }
    }
  }

  .stats-bg {
    position: absolute;
    top: 0;
    right: -20px;
    width: 100px;
    height: 100px;
    opacity: 0.1;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }
}
</style>