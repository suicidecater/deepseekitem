<script setup lang="ts">
// src/components/layout/AppSidebar.vue
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'

const appStore = useAppStore()

interface MenuItem {
  label: string
  icon: string
  route: string
  badge?: number
}

const menuItems = computed<MenuItem[]>(() => [
  { label: '学习首页', icon: '🏠', route: '/student/home' },
  { label: '能力测评', icon: '📊', route: '/student/evaluation' },
  { label: 'AI学习路径', icon: '🧭', route: '/student/study-plan' },
  { label: 'AI交规问答', icon: '🤖', route: '/student/ai-qa' },
  { label: '智能题库', icon: '📝', route: '/student/practice' },
  { label: '模拟考试', icon: '📋', route: '/student/exam' },
  { label: '错题本', icon: '📕', route: '/student/error-book', badge: 5 },
  { label: '易混淆训练', icon: '🔄', route: '/student/confusing' },
  { label: '场景模拟', icon: '🎮', route: '/student/scene-sim' },
  { label: '考前冲刺', icon: '🚀', route: '/student/sprint' },
  { label: '学习进度', icon: '📈', route: '/student/progress' },
  { label: '勋章奖励', icon: '🏅', route: '/student/rewards' },
  { label: '学习报告', icon: '📄', route: '/student/report' },
  { label: '消息通知', icon: '🔔', route: '/student/messages', badge: 3 },
])
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
    <nav class="sidebar-menu">
      <router-link
        v-for="item in menuItems"
        :key="item.route"
        :to="item.route"
        class="menu-item"
        :class="{ active: $route.path === item.route }"
      >
        <span class="menu-icon">{{ item.icon }}</span>
        <span v-if="!appStore.sidebarCollapsed" class="menu-label">{{ item.label }}</span>
        <span v-if="item.badge && !appStore.sidebarCollapsed" class="menu-badge">{{ item.badge }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: var(--sidebar-width);
  background: #fff;
  border-right: 1px solid var(--color-border-light);
  height: calc(100vh - var(--header-height));
  position: sticky;
  top: var(--header-height);
  overflow-y: auto;
  padding: 12px 8px;
  transition: width var(--transition-normal);
}

.app-sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

.menu-item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.menu-item.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 500;
}

.menu-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.menu-label {
  flex: 1;
}

.menu-badge {
  font-size: 11px;
  background: var(--color-error);
  color: #fff;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}
</style>
