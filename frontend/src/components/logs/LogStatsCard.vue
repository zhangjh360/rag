<template>
  <div class="log-stats-card tech-card" :class="[`color-${color}`]">
    <div class="card-content">
      <div class="icon-wrapper">
        <div class="icon">{{ icon }}</div>
        <div class="pulse-ring"></div>
      </div>

      <div class="stats-content">
        <div class="title">{{ title }}</div>
        <div class="value">{{ value }}</div>
        <div v-if="trend" class="trend">
          <span :class="['trend-icon', `trend-${trend}`]">
            {{ getTrendIcon(trend) }}
          </span>
          <span class="trend-text">{{ getTrendText(trend) }}</span>
        </div>
      </div>
    </div>

    <div class="glow-effect"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  color: {
    type: String,
    default: 'blue',
    validator: (value) => ['blue', 'green', 'yellow', 'purple', 'pink', 'red'].includes(value)
  },
  trend: {
    type: String,
    default: null,
    validator: (value) => ['up', 'down', 'stable', null].includes(value)
  }
})

const getTrendIcon = (trend) => {
  const icons = {
    up: '📈',
    down: '📉',
    stable: '📊'
  }
  return icons[trend] || ''
}

const getTrendText = (trend) => {
  const texts = {
    up: '增长',
    down: '下降',
    stable: '稳定'
  }
  return texts[trend] || ''
}
</script>

<style scoped>
.log-stats-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.log-stats-card:hover {
  transform: translateY(-5px) scale(1.02);
}

.log-stats-card:hover .glow-effect {
  opacity: 1;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  z-index: 2;
}

.icon-wrapper {
  position: relative;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 2rem;
  line-height: 1;
  z-index: 2;
  position: relative;
  transition: transform 0.3s ease;
}

.log-stats-card:hover .icon {
  transform: scale(1.1) rotate(5deg);
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 50%;
  animation: pulse-ring 2s infinite;
}

.stats-content {
  flex: 1;
}

.title {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.value {
  color: white;
  font-size: 1.75rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
  text-shadow: 0 0 10px currentColor;
}

.trend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.trend-icon {
  font-size: 1rem;
}

.trend-text {
  color: rgba(255, 255, 255, 0.6);
}

.glow-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
  pointer-events: none;
}

/* 颜色主题 */
.color-blue {
  --card-color: #00d4ff;
}

.color-blue .pulse-ring {
  border: 2px solid rgba(0, 212, 255, 0.3);
}

.color-blue .glow-effect {
  background: radial-gradient(circle at center, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(0, 212, 255, 0.2);
}

.color-green {
  --card-color: #10b981;
}

.color-green .pulse-ring {
  border: 2px solid rgba(16, 185, 129, 0.3);
}

.color-green .glow-effect {
  background: radial-gradient(circle at center, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(16, 185, 129, 0.2);
}

.color-yellow {
  --card-color: #fbbf24;
}

.color-yellow .pulse-ring {
  border: 2px solid rgba(251, 191, 36, 0.3);
}

.color-yellow .glow-effect {
  background: radial-gradient(circle at center, rgba(251, 191, 36, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(251, 191, 36, 0.2);
}

.color-purple {
  --card-color: #a855f7;
}

.color-purple .pulse-ring {
  border: 2px solid rgba(168, 85, 247, 0.3);
}

.color-purple .glow-effect {
  background: radial-gradient(circle at center, rgba(168, 85, 247, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(168, 85, 247, 0.2);
}

.color-pink {
  --card-color: #ec4899;
}

.color-pink .pulse-ring {
  border: 2px solid rgba(236, 72, 153, 0.3);
}

.color-pink .glow-effect {
  background: radial-gradient(circle at center, rgba(236, 72, 153, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(236, 72, 153, 0.2);
}

.color-red {
  --card-color: #ef4444;
}

.color-red .pulse-ring {
  border: 2px solid rgba(239, 68, 68, 0.3);
}

.color-red .glow-effect {
  background: radial-gradient(circle at center, rgba(239, 68, 68, 0.1) 0%, transparent 70%);
  box-shadow: inset 0 0 30px rgba(239, 68, 68, 0.2);
}

/* 趋势颜色 */
.trend-up {
  color: var(--tech-neon-green);
}

.trend-down {
  color: var(--tech-neon-pink);
}

.trend-stable {
  color: var(--tech-neon-blue);
}

/* 动画 */
@keyframes pulse-ring {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.4);
    opacity: 0;
  }
}

/* 边框发光效果 */
.log-stats-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.log-stats-card:hover {
  border-color: var(--card-color);
  box-shadow: 0 0 30px rgba(var(--card-color), 0.3);
}

/* 响应式 */
@media (max-width: 768px) {
  .card-content {
    gap: 0.75rem;
  }

  .icon-wrapper {
    width: 45px;
    height: 45px;
  }

  .icon {
    font-size: 1.25rem;
  }

  .value {
    font-size: 1.25rem;
  }

  .title {
    font-size: 0.7rem;
  }
}

@media (max-width: 640px) {
  .card-content {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }

  .icon-wrapper {
    width: 40px;
    height: 40px;
  }

  .icon {
    font-size: 1.1rem;
  }

  .value {
    font-size: 1.1rem;
    line-height: 1.2;
  }

  .title {
    font-size: 0.65rem;
    margin-bottom: 0.25rem;
  }

  .trend {
    font-size: 0.65rem;
  }
}
</style>