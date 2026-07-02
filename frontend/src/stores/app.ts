// src/stores/app.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const globalLoading = ref(false)
  const toastMessage = ref('')
  const toastType = ref<'success' | 'error' | 'info'>('info')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
    toastMessage.value = message
    toastType.value = type
    setTimeout(() => { toastMessage.value = '' }, 3000)
  }

  return { sidebarCollapsed, globalLoading, toastMessage, toastType, toggleSidebar, showToast }
})
