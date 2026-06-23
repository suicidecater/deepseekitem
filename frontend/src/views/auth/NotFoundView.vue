<script setup lang="ts">
// src/views/auth/NotFoundView.vue
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">404</h1>
      <p class="error-title">页面未找到</p>
      <p class="error-desc">您访问的页面不存在或已被移除</p>
      <button class="btn btn-primary" @click="router.push('/student/home')">返回首页</button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--color-bg);
}
.error-content { text-align: center; }
.error-code { font-size: 80px; font-weight: 800; color: var(--color-text-tertiary); }
.error-title { font-size: var(--font-size-2xl); margin: 12px 0 8px; }
.error-desc { color: var(--color-text-tertiary); margin-bottom: 24px; }
</style>
