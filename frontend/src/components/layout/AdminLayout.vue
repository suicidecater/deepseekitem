<script setup lang="ts">
// src/components/layout/AdminLayout.vue - 管理员独立布局（不共用 AppHeader）
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useRouter, useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'
import NotificationBell from '@/components/common/NotificationBell.vue'

const authStore = useAuthStore()
const notifyStore = useNotificationStore()
const router = useRouter()
const route = useRoute()

const userName = computed(() => authStore.userInfo?.name || '管理员')

const menuItems = [
  { label: '人员管理', icon: '👥', route: '/admin/users' },
  { label: '教练分配', icon: '🔄', route: '/admin/coach-assignment' },
  { label: '题库管理', icon: '📝', route: '/admin/questions' },
  { label: 'API 配置', icon: '⚙️', route: '/admin/api-config' },
  { label: '通知管理', icon: '📢', route: '/admin/notifications' },
]

function isActive(itemRoute: string) {
  return route.path === itemRoute || route.path.startsWith(itemRoute + '/')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  notifyStore.startPolling()
})
</script>

<template>
  <div class="admin-layout">
    <!-- 管理员独立顶部栏 -->
    <header class="admin-header">
      <div class="header-left">
        <span class="logo-icon">🚦</span>
        <span class="logo-text">管理后台</span>
      </div>
      <div class="header-right">
        <NotificationBell />
        <span class="admin-tag">管理员</span>
        <span class="user-name">{{ userName }}</span>
        <button class="btn-logout" @click="handleLogout">退出登录</button>
      </div>
    </header>

    <div class="layout-body">
      <!-- 左侧导航栏 -->
      <aside class="admin-sidebar">
        <router-link
          v-for="item in menuItems"
          :key="item.route"
          :to="item.route"
          class="menu-item"
          :class="{ active: isActive(item.route) }"
        >
          <span class="menu-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </aside>

      <!-- 内容区 -->
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* 顶部栏 */
.admin-header {
  height: 56px;
  background: #001529;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  color: #fff;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon { font-size: 24px; }
.logo-text { font-size: var(--font-size-lg); font-weight: 600; letter-spacing: 1px; }
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: var(--font-size-sm);
}
.admin-tag {
  font-size: var(--font-size-xs);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  background: rgba(24, 144, 255, 0.25);
  color: #69c0ff;
}
.user-name { color: rgba(255,255,255,0.85); }
.btn-logout {
  background: transparent;
  color: rgba(255,255,255,0.65);
  border: 1px solid rgba(255,255,255,0.3);
  padding: 4px 14px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-logout:hover { color: #fff; border-color: #fff; }

/* 主体 */
.layout-body {
  display: flex;
  flex: 1;
}

/* 左侧导航 */
.admin-sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid var(--color-border-light);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
}
.menu-item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.menu-item.active {
  background: var(--color-primary);
  color: #fff;
}
.menu-icon { font-size: 18px; }

/* 内容 */
.layout-content {
  flex: 1;
  overflow-y: auto;
}
</style>
