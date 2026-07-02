<script setup lang="ts">
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<template>
  <div class="app-root">
    <!-- 全局 Toast -->
    <Transition name="toast-fade">
      <div
        v-if="appStore.toastMessage"
        class="global-toast"
        :class="`toast-${appStore.toastType}`"
      >
        {{ appStore.toastMessage }}
      </div>
    </Transition>

    <router-view v-slot="{ Component }">
      <Transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.global-toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast-success { background: var(--color-success); }
.toast-error { background: var(--color-error); }
.toast-info { background: var(--color-primary); }
</style>
