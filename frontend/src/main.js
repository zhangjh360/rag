// 尽早应用主题，防止闪白
import { getTheme, applyTheme } from './utils/themeManager'
applyTheme(getTheme())

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 导入自定义样式
import './styles/tailwind.css'
import './styles/theme.scss'
import './styles/global.css'
import './styles/element-override.css'
import './styles/table-fix.css'
import './styles/logs.scss'
import './styles/profile.scss'
import './styles/admin.scss'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './store/auth'
import { initTheme } from './utils/themeManager'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 再次初始化主题（确保所有样式已加载）
initTheme()

// 初始化认证状态
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')