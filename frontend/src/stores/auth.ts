// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserProfile } from '@/types/common'
import { storage } from '@/utils/storage'

const REFRESH_INTERVAL = 25 * 60 * 1000 // 25分钟自动刷新

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(storage.get('token') || '')
  const refreshToken = ref<string>(storage.get('refresh_token') || '')
  const userInfo = ref<UserProfile | null>(storage.get('user'))
  const role = ref<string>(userInfo.value?.role || '')

  const isAuthenticated = computed(() => !!token.value)

  let refreshTimer: ReturnType<typeof setInterval> | null = null

  function startRefreshTimer() {
    stopRefreshTimer()
    if (!refreshToken.value) return
    refreshTimer = setInterval(async () => {
      try {
        const res = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken.value })
        })
        const json = await res.json()
        if (json.code === 0) {
          token.value = json.data.token
          refreshToken.value = json.data.refresh_token || refreshToken.value
          storage.set('token', token.value)
          storage.set('refresh_token', refreshToken.value)
        } else {
          // refresh 失败 → 登出
          logout()
          window.location.href = '/login'
        }
      } catch {
        logout()
        window.location.href = '/login'
      }
    }, REFRESH_INTERVAL)
  }

  function stopRefreshTimer() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  interface AuthData {
    token: string
    refresh_token?: string
    user: UserProfile
  }

  function setAuth(data: AuthData) {
    token.value = data.token
    refreshToken.value = data.refresh_token || ''
    userInfo.value = data.user
    role.value = data.user.role
    storage.set('token', data.token)
    storage.set('refresh_token', refreshToken.value)
    storage.set('user', data.user)
    startRefreshTimer()
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    role.value = ''
    storage.remove('token')
    storage.remove('refresh_token')
    storage.remove('user')
    stopRefreshTimer()
  }

  return { token, refreshToken, userInfo, role, isAuthenticated, setAuth, logout, startRefreshTimer, stopRefreshTimer }
})
