<script setup lang="ts">
// src/views/auth/ForbiddenView.vue
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">403</h1>
      <p class="error-title">访问被拒绝</p>
      <p class="error-desc">抱歉，您没有权限访问此页面</p>
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
.error-code { font-size: 80px; font-weight: 800; color: var(--color-primary); }
.error-title { font-size: var(--font-size-2xl); margin: 12px 0 8px; }
.error-desc { color: var(--color-text-tertiary); margin-bottom: 24px; }
</style>
