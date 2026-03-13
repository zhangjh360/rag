<template>
  <div class="register-container">
    <!-- 动态网格背景 -->
    <div class="tech-grid-background"></div>

    <!-- 注册卡片 -->
    <div class="register-card">
      <div class="register-header">
        <div class="logo-container">
          <div class="tech-logo">
            <div class="logo-ring"></div>
            <div class="logo-core"></div>
          </div>
        </div>
        <h1 class="register-title">创建新账户</h1>
        <p class="register-subtitle">加入 RAG 智能问答系统，开启 AI 对话新体验</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            class="tech-input"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            type="email"
            placeholder="邮箱地址"
            class="tech-input"
            size="large"
            :prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            class="tech-input"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirm_password">
          <el-input
            v-model="registerForm.confirm_password"
            type="password"
            placeholder="确认密码"
            class="tech-input"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <!-- 密码强度指示器 -->
        <div class="password-strength" v-if="registerForm.password">
          <div class="strength-label">密码强度：</div>
          <div class="strength-bar">
            <div
              class="strength-fill"
              :class="passwordStrengthClass"
              :style="{ width: passwordStrengthWidth + '%' }"
            ></div>
          </div>
          <div class="strength-text" :class="passwordStrengthClass">
            {{ passwordStrengthText }}
          </div>
        </div>

        <!-- 服务条款 -->
        <div class="terms-agreement">
          <el-checkbox v-model="registerForm.agree_terms" class="terms-checkbox">
            我已阅读并同意
            <a href="#" class="terms-link" @click.prevent="showTerms">服务条款</a>
            和
            <a href="#" class="terms-link" @click.prevent="showPrivacy">隐私政策</a>
          </el-checkbox>
        </div>

        <el-button
          type="primary"
          size="large"
          class="register-button"
          :loading="loading"
          :disabled="!registerForm.agree_terms"
          @click="handleRegister"
        >
          <span v-if="!loading">创建账户</span>
          <span v-else>注册中...</span>
        </el-button>
      </el-form>

      <div class="register-footer">
        <p class="login-hint">
          已有账户？
          <router-link to="/login" class="login-link">立即登录</router-link>
        </p>
      </div>

      <!-- 安全提示 -->
      <div class="security-notice">
        <div class="notice-icon">
          <i class="el-icon-info"></i>
        </div>
        <p>新注册账户默认为普通用户权限</p>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import '@/styles/login.scss'

const router = useRouter()
const authStore = useAuthStore()

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  agree_terms: false
})

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3-20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
    { max: 50, message: '密码最多50个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const loading = ref(false)
const registerFormRef = ref(null)

// 密码强度计算
const passwordStrength = computed(() => {
  const password = registerForm.password
  if (!password) return 0

  let strength = 0

  // 长度检查
  if (password.length >= 8) strength += 1
  if (password.length >= 12) strength += 1

  // 字符类型检查
  if (/[a-z]/.test(password)) strength += 1
  if (/[A-Z]/.test(password)) strength += 1
  if (/[0-9]/.test(password)) strength += 1
  if (/[^a-zA-Z0-9]/.test(password)) strength += 1

  return Math.min(strength, 5)
})

const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 2) return 'weak'
  if (strength <= 4) return 'medium'
  return 'strong'
})

const passwordStrengthWidth = computed(() => {
  return (passwordStrength.value / 5) * 100
})

const passwordStrengthText = computed(() => {
  const strength = passwordStrength.value
  if (strength <= 2) return '弱'
  if (strength <= 4) return '中等'
  return '强'
})

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return

    if (!registerForm.agree_terms) {
      ElMessage.warning('请先同意服务条款和隐私政策')
      return
    }

    loading.value = true

    const result = await authStore.register(registerForm)

    if (result.success) {
      ElMessage.success('注册成功！即将跳转到登录页面')

      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } else {
      ElMessage.error(result.message || '注册失败')
    }
  } catch (error) {
    console.error('注册错误:', error)
    ElMessage.error('注册失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 显示服务条款
const showTerms = () => {
  ElMessageBox.alert(
    '1. 用户应当遵守国家法律法规，不得利用本系统进行违法活动。\n' +
    '2. 用户承诺上传的文档内容合法，不侵犯他人知识产权。\n' +
    '3. 系统将根据用户角色提供相应的功能权限。\n' +
    '4. 管理员有权对违规用户进行封禁处理。\n' +
    '5. 本系统保留对服务条款的最终解释权。',
    '服务条款',
    {
      confirmButtonText: '同意',
      type: 'info',
      customClass: 'terms-message-box'
    }
  )
}

// 显示隐私政策
const showPrivacy = () => {
  ElMessageBox.alert(
    '1. 我们重视用户隐私保护，承诺不会泄露用户个人信息。\n' +
    '2. 用户上传的文档内容将进行加密存储。\n' +
    '3. 查询记录仅用于改进服务质量，不会向第三方透露。\n' +
    '4. 用户有权要求删除个人数据和账户信息。\n' +
    '5. 我们采用行业标准的安全技术保护数据安全。',
    '隐私政策',
    {
      confirmButtonText: '同意',
      type: 'info',
      customClass: 'privacy-message-box'
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
.register-container {
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
    linear-gradient(rgba(168, 85, 247, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(168, 85, 247, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.register-card {
  width: 450px;
  padding: 40px;
  background: var(--tech-glass-bg);
  backdrop-filter: var(--tech-backdrop-blur);
  border-radius: 20px;
  border: 1px solid var(--tech-glass-border);
  box-shadow: 0 0 40px rgba(168, 85, 247, 0.3);
  position: relative;
  z-index: 10;
  animation: card-float 3s ease-in-out infinite;
}

@keyframes card-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
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
  border: 3px solid var(--tech-neon-purple);
  border-radius: 50%;
  animation: ring-rotate 3s linear infinite;
  box-shadow: 0 0 30px var(--tech-neon-purple);
}

.logo-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  background: var(--tech-gradient-accent);
  border-radius: 50%;
  box-shadow: 0 0 20px var(--tech-neon-purple);
}

@keyframes ring-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.register-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--tech-text-primary);
  margin: 0 0 8px 0;
  background: var(--tech-gradient-accent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-subtitle {
  font-size: 14px;
  color: var(--tech-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.register-form {
  margin-bottom: 20px;
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
  color: var(--tech-neon-purple);
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
  border-color: var(--tech-neon-purple);
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
}

:deep(.tech-input .el-input__inner::placeholder) {
  color: var(--tech-text-muted);
}

.password-strength {
  margin-bottom: 20px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.strength-label {
  font-size: 12px;
  color: var(--tech-text-secondary);
  margin-bottom: 8px;
}

.strength-bar {
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: all var(--tech-transition-normal);
}

.strength-fill.weak {
  background: var(--tech-neon-pink);
}

.strength-fill.medium {
  background: var(--tech-neon-yellow);
}

.strength-fill.strong {
  background: var(--tech-neon-green);
}

.strength-text {
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}

.strength-text.weak {
  color: var(--tech-neon-pink);
}

.strength-text.medium {
  color: var(--tech-neon-yellow);
}

.strength-text.strong {
  color: var(--tech-neon-green);
}

.terms-agreement {
  margin-bottom: 30px;
}

.terms-checkbox {
  color: var(--tech-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.terms-link {
  color: var(--tech-neon-purple);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--tech-transition-fast);
}

.terms-link:hover {
  color: var(--tech-neon-pink);
  text-shadow: 0 0 10px var(--tech-neon-purple);
}

.register-button {
  width: 100%;
  height: 48px;
  background: var(--tech-gradient-accent);
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  position: relative;
  overflow: hidden;
  transition: all var(--tech-transition-normal);
}

.register-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(168, 85, 247, 0.5);
}

.register-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.register-footer {
  text-align: center;
  margin-bottom: 20px;
}

.login-hint {
  color: var(--tech-text-secondary);
  font-size: 14px;
  margin: 0;
}

.login-link {
  color: var(--tech-neon-purple);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--tech-transition-fast);
}

.login-link:hover {
  color: var(--tech-neon-pink);
  text-shadow: 0 0 10px var(--tech-neon-purple);
}

.security-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
}

.notice-icon {
  color: var(--tech-neon-green);
  font-size: 16px;
}

.security-notice p {
  color: var(--tech-neon-green);
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
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
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
  background: var(--tech-gradient-accent);
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