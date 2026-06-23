<script setup lang="ts">
// src/components/layout/StudentLayout.vue
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<template>
  <div class="student-layout">
    <AppHeader />
    <div class="layout-body">
      <AppSidebar />
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.student-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-body {
  display: flex;
  flex: 1;
}

.layout-content {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
