/**
 * 主题管理器
 * 用于在应用中切换和持久化主题设置
 */

const THEME_KEY = 'app-theme'
const VALID_THEMES = ['tech', 'dark', 'light']

/**
 * 获取当前主题
 * @returns {string} 当前主题名称
 */
export function getTheme() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved && VALID_THEMES.includes(saved)) {
    return saved
  }
  return 'tech' // 默认主题
}

/**
 * 设置主题
 * @param {string} theme - 主题名称 (tech/dark/light)
 */
export function setTheme(theme) {
  if (!VALID_THEMES.includes(theme)) {
    console.warn(`Invalid theme: ${theme}, using default 'tech'`)
    theme = 'tech'
  }

  // 保存到 localStorage
  localStorage.setItem(THEME_KEY, theme)

  // 应用主题到 document
  applyTheme(theme)
}

/**
 * 应用主题到 DOM
 * @param {string} theme - 主题名称
 */
export function applyTheme(theme) {
  // 设置 data-theme 属性到 html 和 body
  document.documentElement.setAttribute('data-theme', theme)
  document.body.setAttribute('data-theme', theme)

  // 延迟更新背景色，确保 CSS 变量已生效
  requestAnimationFrame(() => {
    const root = document.documentElement
    const bgColor = getComputedStyle(root).getPropertyValue('--tech-bg-primary').trim()
    if (bgColor) {
      document.body.style.backgroundColor = bgColor
    }
  })

  console.log('Theme applied:', theme)
}

/**
 * 初始化主题（在应用启动时调用）
 */
export function initTheme() {
  const theme = getTheme()
  applyTheme(theme)
}

/**
 * 获取所有可用主题
 * @returns {Array} 主题列表
 */
export function getAvailableThemes() {
  return [
    { value: 'tech', label: '科技感', description: '深色背景配霓虹蓝色调' },
    { value: 'dark', label: '暗黑', description: '纯黑背景柔和配色' },
    { value: 'light', label: '明亮', description: '浅色背景深色文字' }
  ]
}

export default {
  getTheme,
  setTheme,
  applyTheme,
  initTheme,
  getAvailableThemes
}
