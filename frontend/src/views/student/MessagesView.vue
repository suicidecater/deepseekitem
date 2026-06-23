<script setup lang="ts">
// src/views/student/MessagesView.vue - 消息通知
import { ref, computed } from 'vue'

interface Message {
  id: number
  type: 'system' | 'exam' | 'study' | 'reward'
  title: string
  content: string
  time: string
  read: boolean
}

const messages = ref<Message[]>([
  { id: 1, type: 'exam', title: '模拟考试提醒', content: '你已经有3天没有进行模拟考试了，保持练习才能更好通过考试！', time: '2026-06-01 10:30', read: false },
  { id: 2, type: 'reward', title: '勋章获得！', content: '恭喜你获得"初出茅庐"勋章，已连续学习7天！', time: '2026-05-28 08:00', read: false },
  { id: 3, type: 'study', title: '学习报告生成', content: '你的5月学习报告已生成，正确率85%，查看详情了解你的进步。', time: '2026-05-31 00:01', read: true },
  { id: 4, type: 'system', title: '系统通知', content: '平台已更新题库，新增200道交通法规题目，快来练习吧！', time: '2026-05-25 14:00', read: true },
  { id: 5, type: 'exam', title: '考试倒计时', content: '距离你的驾考还有10天，建议开启考前冲刺模式！', time: '2026-05-30 09:00', read: false },
])

const unreadCount = computed(() => messages.value.filter(m => !m.read).length)

const typeIcons: Record<string, string> = {
  system: '📢', exam: '📝', study: '📊', reward: '🏅'
}

function markAllRead() {
  messages.value.forEach(m => m.read = true)
}

function toggleRead(id: number) {
  const msg = messages.value.find(m => m.id === id)
  if (msg) msg.read = !msg.read
}
</script>

<template>
  <div class="messages-page">
    <div class="page-header">
      <h2>消息通知</h2>
      <button v-if="unreadCount > 0" class="btn btn-outline btn-sm" @click="markAllRead">
        全部标为已读 ({{ unreadCount }})
      </button>
    </div>

    <div class="message-list">
      <div v-if="messages.length === 0" class="empty-state">暂无消息</div>
      <div
        v-for="msg in messages" :key="msg.id"
        class="message-item card"
        :class="{ unread: !msg.read }"
        @click="toggleRead(msg.id)"
      >
        <div class="msg-icon">{{ typeIcons[msg.type] }}</div>
        <div class="msg-body">
          <div class="msg-header">
            <span class="msg-title">{{ msg.title }}</span>
            <span class="msg-time">{{ msg.time }}</span>
          </div>
          <p class="msg-content">{{ msg.content }}</p>
        </div>
        <div v-if="!msg.read" class="msg-dot"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.messages-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { font-size: var(--font-size-2xl); }
.btn-sm { padding: 4px 12px; font-size: var(--font-size-xs); }

.empty-state { text-align: center; padding: 60px; color: var(--color-text-tertiary); }

.message-list { display: flex; flex-direction: column; gap: 8px; }
.message-item {
  display: flex; align-items: flex-start; gap: 14px; padding: 16px; cursor: pointer;
  transition: all var(--transition-fast); border: 1px solid var(--color-border-light);
}
.message-item.unread { background: #F0F7FF; border-color: #BAE0FF; }
.message-item:hover { box-shadow: var(--shadow-sm); }
.card { background: #fff; border-radius: var(--radius-lg); }

.msg-icon { font-size: 28px; flex-shrink: 0; margin-top: 2px; }
.msg-body { flex: 1; min-width: 0; }
.msg-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.msg-title { font-size: var(--font-size-sm); font-weight: 600; }
.msg-time { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.msg-content { font-size: var(--font-size-xs); color: var(--color-text-secondary); line-height: 1.5; }
.msg-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-primary); flex-shrink: 0; margin-top: 6px; }
</style>
