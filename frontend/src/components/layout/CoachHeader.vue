<script setup lang="ts">
// src/components/layout/CoachHeader.vue
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
  <header class="coach-header">
    <div class="header-left">
      <router-link to="/coach/students" class="logo">
        <span class="logo-icon">🚦</span>
        <span class="logo-text">教练管理平台</span>
      </router-link>
    </div>

    <div class="header-right">
      <NotificationBell />
      <span class="user-role-tag">{{ userRole }}</span>
      <span class="user-name">{{ userName }}</span>
      <button class="btn btn-outline logout-btn" @click="handleLogout">退出</button>
    </div>
  </header>
</template>

<style scoped>
.coach-header {
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
  text-decoration: none;
}

.logo-icon {
  font-size: 28px;
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
