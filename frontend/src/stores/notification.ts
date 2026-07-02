/**
 * 通知系统 Pinia Store
 * 管理未读数量状态，供顶部铃铛组件使用
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
import {
  coachGetUnreadCount,
  studentGetUnreadCount,
} from '@/api/modules/notification'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  let pollTimer: ReturnType<typeof setInterval> | null = null

  /** 根据当前角色获取未读数量 */
  async function fetchUnreadCount() {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      unreadCount.value = 0
      return
    }

    try {
      const role = auth.role
      if (role === 'coach') {
        const res = await coachGetUnreadCount()
        unreadCount.value = res.data.data?.count ?? 0
      } else if (role === 'student') {
        const res = await studentGetUnreadCount()
        unreadCount.value = res.data.data?.count ?? 0
      } else {
        unreadCount.value = 0
      }
    } catch {
      // 静默失败
    }
  }

  /** 启动定时轮询（每30秒刷新一次未读数量） */
  function startPolling() {
    stopPolling()
    fetchUnreadCount()
    pollTimer = setInterval(fetchUnreadCount, 30_000)
  }

  /** 停止轮询 */
  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  /** 减少未读数量（已读一条后调用） */
  function decrementUnread(n: number = 1) {
    unreadCount.value = Math.max(0, unreadCount.value - n)
  }

  /** 清零未读数量 */
  function clearUnread() {
    unreadCount.value = 0
  }

  return {
    unreadCount,
    fetchUnreadCount,
    startPolling,
    stopPolling,
    decrementUnread,
    clearUnread,
  }
})
