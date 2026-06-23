<script setup lang="ts">
// src/components/layout/AdminLayout.vue
import AppHeader from './AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

const authStore = useAuthStore()
const adminType = computed(() => authStore.userInfo?.adminType || 1)

const allMenuItems = [
  { label: '驾校管理', icon: '🏫', route: '/admin/school', roles: ['admin'] },
  { label: '运营管理', icon: '📊', route: '/admin/operation', roles: ['admin', 'operator'] },
  { label: '内容管理', icon: '📝', route: '/admin/cms', roles: ['admin', 'editor'] },
]

const menuItems = computed(() => {
  const adminTypeMap: Record<number, string[]> = {
    1: ['admin'], 2: ['editor'], 3: ['operator']
  }
  const allowed = adminTypeMap[adminType.value] || []
  return allMenuItems.filter(item => allowed.some(r => item.roles.includes(r)))
})
</script>

<template>
  <div class="admin-layout">
    <AppHeader />
    <div class="layout-body">
      <aside class="admin-sidebar">
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
.admin-layout { min-height: 100vh; display: flex; flex-direction: column; }
.layout-body { display: flex; flex: 1; }
.admin-sidebar {
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
