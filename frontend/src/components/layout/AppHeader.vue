<script setup lang="ts">
// src/components/layout/AppHeader.vue
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useRouter } from 'vue-router'
import { computed, onMounted } from 'vue'
import NotificationBell from '@/components/common/NotificationBell.vue'

const authStore = useAuthStore()
const notifyStore = useNotificationStore()
const router = useRouter()

const userName = computed(() => authStore.userInfo?.name || '用户')
const userRole = computed(() => {
  const map: Record<string, string> = { student: '学员', coach: '教练', admin: '管理员' }
  return map[authStore.role] || ''
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  notifyStore.startPolling()
})
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/student/home" class="logo">
        <span class="logo-icon">🚦</span>
        <span class="logo-text">交通安全培训</span>
      </router-link>
    </div>

    <nav class="header-nav">
      <router-link to="/student/home" class="nav-item">首页</router-link>
      <router-link to="/student/practice" class="nav-item">题库练习</router-link>
      <router-link to="/student/exam" class="nav-item">模拟考试</router-link>
      <router-link to="/student/ai-qa" class="nav-item">AI问答</router-link>
      <router-link to="/student/error-book" class="nav-item">错题本</router-link>
      <router-link to="/student/progress" class="nav-item">学习进度</router-link>
    </nav>

    <div class="header-right">
      <NotificationBell />
      <span class="user-role-tag">{{ userRole }}</span>
      <span class="user-name">{{ userName }}</span>
      <button class="btn btn-outline logout-btn" @click="handleLogout">退出</button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-primary);
}

.logo-icon {
  font-size: 28px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-item {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}
.nav-item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.nav-item.router-link-active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-role-tag {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.user-name {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.logout-btn {
  padding: 4px 12px;
  font-size: var(--font-size-xs);
}
</style>
