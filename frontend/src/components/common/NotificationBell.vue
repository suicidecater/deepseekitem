<template>
  <div class="notification-bell" @click="handleClick">
    <span class="bell-icon">🔔</span>
    <span v-if="unreadCount > 0" class="unread-badge">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const notifyStore = useNotificationStore()
const authStore = useAuthStore()

const unreadCount = computed(() => notifyStore.unreadCount)

function handleClick() {
  const role = authStore.role
  if (role === 'admin') {
    router.push('/admin/notifications')
  } else if (role === 'coach') {
    router.push('/coach/notifications')
  } else if (role === 'student') {
    router.push('/student/notifications')
  }
}
</script>

<style scoped>
.notification-bell {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.notification-bell:hover {
  background: rgba(255, 255, 255, 0.15);
}

.bell-icon {
  font-size: 20px;
  line-height: 1;
}

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #ff4d4f;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  line-height: 18px;
  text-align: center;
  white-space: nowrap;
  box-shadow: 0 0 0 2px #fff;
}
</style>
