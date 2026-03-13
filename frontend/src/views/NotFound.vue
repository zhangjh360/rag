<template>
  <div class="not-found-container">
    <div class="tech-grid-background"></div>

    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面未找到</h1>
      <p class="error-message">抱歉，您访问的页面不存在或已被移动</p>

      <div class="error-actions">
        <el-button type="primary" size="large" @click="goHome">
          返回首页
        </el-button>
        <el-button size="large" @click="goBack">
          返回上页
        </el-button>
      </div>
    </div>

    <div class="decoration-elements">
      <div class="tech-circle circle-1"></div>
      <div class="tech-circle circle-2"></div>
      <div class="tech-line line-1"></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--tech-bg-primary);
  overflow: hidden;
}

.tech-grid-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(236, 72, 153, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(236, 72, 153, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.not-found-content {
  text-align: center;
  z-index: 10;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--tech-neon-pink) 0%, var(--tech-neon-purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from { text-shadow: 0 0 20px rgba(236, 72, 153, 0.5); }
  to { text-shadow: 0 0 30px rgba(168, 85, 247, 0.8); }
}

.error-title {
  font-size: 36px;
  font-weight: 600;
  color: var(--tech-text-primary);
  margin: 0 0 16px 0;
}

.error-message {
  font-size: 18px;
  color: var(--tech-text-secondary);
  margin: 0 0 40px 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.decoration-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.tech-circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border: 1px solid var(--tech-glass-border);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 100px;
  height: 100px;
  top: 15%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 60px;
  height: 60px;
  bottom: 20%;
  right: 15%;
  animation-delay: 3s;
}

.tech-line {
  position: absolute;
  background: linear-gradient(135deg, var(--tech-neon-pink), var(--tech-neon-purple));
  opacity: 0.3;
}

.line-1 {
  width: 1px;
  height: 200px;
  top: 25%;
  right: 25%;
  transform: rotate(45deg);
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}
</style>