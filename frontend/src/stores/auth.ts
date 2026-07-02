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

  const studySubject = computed(() => userInfo.value?.studySubject ?? 1)
  const evaluationStatusMap = computed(() => userInfo.value?.evaluationStatusMap ?? {})
  const evaluationStatus = computed(() => {
    const key = String(studySubject.value)
    return evaluationStatusMap.value[key] ?? 0
  })
  const needsEvaluation = computed(() => role.value === 'student' && evaluationStatus.value === 0)
  const isAuthenticated = computed(() => !!token.value)

  let refreshTimer: ReturnType<typeof setInterval> | null = null

  // ======================== 设置认证信息 ========================
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

  function clearAuth() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    role.value = ''
    storage.remove('token')
    storage.remove('refresh_token')
    storage.remove('user')
    stopRefreshTimer()
  }

  // 兼容旧代码的 logout 别名
  const logout = clearAuth

  // ======================== Token 刷新 ========================
  async function refreshTokenAction(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken.value}`
        }
      })
      const json = await res.json()
      if (json.code === 0 && json.data) {
        token.value = json.data.access_token || json.data.token
        refreshToken.value = json.data.refresh_token || refreshToken.value
        storage.set('token', token.value)
        storage.set('refresh_token', refreshToken.value)
        return true
      }
      return false
    } catch {
      return false
    }
  }

  function startRefreshTimer() {
    stopRefreshTimer()
    if (!refreshToken.value) return
    refreshTimer = setInterval(async () => {
      try {
        const res = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refreshToken.value}`
          }
        })
        const json = await res.json()
        if (json.code === 0 && json.data) {
          token.value = json.data.access_token || json.data.token
          refreshToken.value = json.data.refresh_token || refreshToken.value
          storage.set('token', token.value)
          storage.set('refresh_token', refreshToken.value)
        } else {
          clearAuth()
          window.location.href = '/login'
        }
      } catch {
        clearAuth()
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

  // ======================== 退出登录 ========================
  async function logoutAction(): Promise<void> {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.value}`
        }
      })
    } catch {
      // 忽略网络错误
    }
    clearAuth()
  }

  return {
    token, refreshToken, userInfo, role, studySubject,
    evaluationStatus, evaluationStatusMap, needsEvaluation, isAuthenticated,
    setAuth, clearAuth, logout,
    refreshTokenAction, logoutAction,
    startRefreshTimer, stopRefreshTimer
  }
})
