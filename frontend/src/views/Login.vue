<template>
  <div class="login-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="login-header">
        <div class="logo-container">
          <div class="tech-logo">
            <div class="logo-ring"></div>
            <div class="logo-core"></div>
          </div>
        </div>
        <h1 class="login-title">RAG 智能问答系统</h1>
        <p class="login-subtitle">基于检索增强生成技术的智能对话平台</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名或邮箱"
            class="tech-input"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            class="tech-input"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <div class="login-options">
          <el-checkbox v-model="loginForm.remember_me" class="remember-checkbox">
            记住我
          </el-checkbox>
          <a href="#" class="forgot-password" @click.prevent="handleForgotPassword">
            忘记密码？
          </a>
        </div>

        <el-button
          type="primary"
          size="large"
          class="login-button"
          :loading="loading"
          @click="handleLogin"
        >
          <span v-if="!loading">安全登录</span>
          <span v-else>登录中...</span>
        </el-button>
      </el-form>

      <div class="login-footer">
        <p class="register-hint">
          还没有账户？
          <router-link to="/register" class="register-link">立即注册</router-link>
        </p>
      </div>

      <!-- 安全提示 -->
      <div class="security-notice">
        <div class="notice-icon">
          <i class="el-icon-warning-outline"></i>
        </div>
        <p>默认管理员账户：admin / admin123</p>
      </div>
    </div>

    <!-- 装饰元素 -->
    <div class="decoration-elements">
      <div class="tech-circle circle-1"></div>
      <div class="tech-circle circle-2"></div>
      <div class="tech-circle circle-3"></div>
      <div class="tech-line line-1"></div>
      <div class="tech-line line-2"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import '@/styles/login.scss'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loginForm = reactive({
  username: '',
  password: '',
  remember_me: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ]
}

const loading = ref(false)
const loginFormRef = ref(null)

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return

    loading.value = true

    const result = await authStore.login(loginForm)

    if (result.success) {
      ElMessage.success('登录成功')

      // 跳转到目标页面或首页
      const redirect = route.query.redirect || '/dashboard'
      router.push(redirect)
    } else {
      ElMessage.error(result.message || '登录失败')
    }
  } catch (error) {
    console.error('登录错误:', error)
    ElMessage.error('登录失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 处理忘记密码
const handleForgotPassword = () => {
  ElMessageBox.alert(
    '请联系系统管理员重置密码，或使用默认管理员账户：admin / admin123',
    '密码重置',
    {
      confirmButtonText: '知道了',
      type: 'info'
    }
  )
}

// 组件挂载时检查是否已登录
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.login-container {
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
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.login-card {
  width: 400px;
  padding: 40px;
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border-radius: 20px;
  border: 1px solid var(--tech-glass-border);
  box-shadow: var(--tech-shadow-neon);
  position: relative;
  z-index: 10;
  animation: card-float 3s ease-in-out infinite;
}

@keyframes card-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.tech-logo {
  position: relative;
  width: 80px;
  height: 80px;
}

.logo-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid var(--tech-neon-blue);
  border-radius: 50%;
  animation: ring-rotate 3s linear infinite;
  box-shadow: 0 0 30px var(--tech-neon-blue);
}

.logo-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: var(--tech-gradient-secondary);
  border-radius: 50%;
  box-shadow: 0 0 20px var(--tech-neon-blue);
}

@keyframes ring-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 8px 0;
  background: var(--tech-gradient-secondary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  font-size: 14px;
  color: var(--tech-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.login-form {
  margin-bottom: 30px;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  z-index: 1;
  color: var(--tech-neon-blue);
  font-size: 16px;
  pointer-events: none;
}

.tech-input {
  flex: 1;
}

:deep(.tech-input .el-input__inner) {
  padding-left: 40px;
  height: 48px;
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-border-color);
  border-radius: 12px;
  color: var(--tech-text-primary);
  font-size: 15px;
  transition: all var(--tech-transition-normal);
}

:deep(.tech-input .el-input__inner:focus) {
  border-color: var(--tech-neon-blue);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

:deep(.tech-input .el-input__inner::placeholder) {
  color: var(--tech-text-muted);
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.remember-checkbox {
  color: var(--tech-text-secondary);
  font-size: 14px;
}

.forgot-password {
  color: var(--tech-neon-blue);
  text-decoration: none;
  font-size: 14px;
  transition: all var(--tech-transition-fast);
}

.forgot-password:hover {
  color: var(--tech-neon-purple);
  text-shadow: 0 0 10px var(--tech-neon-blue);
}

.login-button {
  width: 100%;
  height: 48px;
  background: var(--tech-gradient-secondary);
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  position: relative;
  overflow: hidden;
  transition: all var(--tech-transition-normal);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0, 212, 255, 0.5);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  margin-bottom: 20px;
}

.register-hint {
  color: var(--tech-text-secondary);
  font-size: 14px;
  margin: 0;
}

.register-link {
  color: var(--tech-neon-blue);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--tech-transition-fast);
}

.register-link:hover {
  color: var(--tech-neon-purple);
  text-shadow: 0 0 10px var(--tech-neon-blue);
}

.security-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 8px;
}

.notice-icon {
  color: var(--tech-neon-yellow);
  font-size: 16px;
}

.security-notice p {
  color: var(--tech-neon-yellow);
  font-size: 12px;
  margin: 0;
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
  background: var(--tech-gradient-mesh);
  border: 1px solid var(--tech-glass-border);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 100px;
  height: 100px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 60px;
  height: 60px;
  top: 20%;
  right: 15%;
  animation-delay: 2s;
}

.circle-3 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

.tech-line {
  position: absolute;
  background: var(--tech-gradient-secondary);
  opacity: 0.3;
}

.line-1 {
  width: 1px;
  height: 200px;
  top: 15%;
  right: 25%;
  transform: rotate(45deg);
}

.line-2 {
  width: 150px;
  height: 1px;
  bottom: 25%;
  left: 10%;
  transform: rotate(-30deg);
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}
</style>