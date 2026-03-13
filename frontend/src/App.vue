<template>
  <div id="app">
    <router-view v-if="isPublicRoute" />
    <TechLayout v-else />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TechLayout from './layouts/TechLayout.vue'

const route = useRoute()

// 公共路由列表(不需要布局的页面)
const publicRoutes = ['/login', '/register', '/404']

const isPublicRoute = computed(() => {
  return publicRoutes.includes(route.path)
})
</script>

<style>
body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--tech-bg-primary);
  color: var(--tech-text-primary);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  overflow: hidden;
}
</style>