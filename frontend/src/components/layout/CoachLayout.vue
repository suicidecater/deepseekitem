<script setup lang="ts">
// src/components/layout/CoachLayout.vue
import AppHeader from './AppHeader.vue'

const menuItems = [
  { label: '学情管理', icon: '👥', route: '/coach/students' },
  { label: 'AI辅导建议', icon: '🤖', route: '/coach/ai-advice' },
]
</script>

<template>
  <div class="coach-layout">
    <AppHeader />
    <div class="layout-body">
      <aside class="coach-sidebar">
        <router-link v-for="item in menuItems" :key="item.route" :to="item.route" class="menu-item" active-class="active">
          <span class="menu-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </aside>
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.coach-layout { min-height: 100vh; display: flex; flex-direction: column; }
.layout-body { display: flex; flex: 1; }
.coach-sidebar {
  width: 200px; background: #fff; border-right: 1px solid var(--color-border-light);
  padding: 12px 8px; display: flex; flex-direction: column; gap: 4px;
}
.menu-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  border-radius: var(--radius-md); font-size: var(--font-size-sm); color: var(--color-text-secondary);
  text-decoration: none; transition: all var(--transition-fast);
}
.menu-item:hover { background: var(--color-primary-light); color: var(--color-primary); }
.menu-item.active { background: var(--color-primary); color: #fff; }
.menu-icon { font-size: 18px; }
.layout-content { flex: 1; overflow-y: auto; background: var(--color-bg); }
</style>
