<script setup lang="ts">
/**
 * 学员对话页面
 * 与教练实时聊天
 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useSocket, joinConversationRoom, leaveConversationRoom, sendMessageViaSocket, emitTyping, emitStopTyping, disconnectSocket } from '@/composables/useSocket'
import { getConversations, getMessages, sendMessage, createConversation, markRead, getUnreadCount } from '@/api/modules/chat'
import { get } from '@/api/request'
import { useAuthStore } from '@/stores/auth'
import { storage } from '@/utils/storage'

const authStore = useAuthStore()

// ==================== 类型定义 ====================
interface Conversation {
  id: number
  coach_id: number
  student_id: number
  last_message: string
  last_message_time: string
  unread_count: number
  coach_name?: string
  status: number
}

interface ChatMsg {
  id: number
  conversation_id: number
  sender_type: string  // 'student' | 'coach'
  sender_id: number
  content: string
  message_type: number
  status: number
  create_time: string
}

// ==================== 状态 ====================
const { socket, connected: wsConnected } = useSocket()
const conversations = ref<Conversation[]>([])
const messages = ref<ChatMsg[]>([])
const currentConversationId = ref<number | null>(null)
const newMsgText = ref('')
const loading = ref(false)
const loadingMsgs = ref(false)
const errorMessage = ref('')
const totalUnread = ref(0)
const coachTyping = ref(false)
const availableCoaches = ref<any[]>([])
const showCoachSelector = ref(false)
let typingTimer: ReturnType<typeof setTimeout> | null = null

const currentUser = computed(() => {
  return authStore.userInfo || storage.get<any>('user') || {}
})

// ==================== 数据获取 ====================
async function fetchConversations() {
  try {
    const res = await getConversations()
    if (res.data?.code === 0) {
      conversations.value = res.data.data?.list || []
    }
  } catch (e) {
    console.error('获取会话列表失败:', e)
  }
}

async function fetchUnreadCount() {
  try {
    const res = await getUnreadCount()
    if (res.data?.code === 0) {
      totalUnread.value = res.data.data?.unread_count || 0
    }
  } catch { /* ignore */ }
}

async function fetchMessages(conversationId: number) {
  loadingMsgs.value = true
  try {
    const res = await getMessages(conversationId, 1, 100)
    if (res.data?.code === 0) {
      messages.value = res.data.data?.list || []
      await scrollToBottom()
    }
  } catch (e) {
    console.error('获取消息失败:', e)
  } finally {
    loadingMsgs.value = false
  }
}

// ==================== 会话操作 ====================
async function selectConversation(conv: Conversation) {
  if (currentConversationId.value === conv.id) return

  // 离开旧房间
  if (currentConversationId.value) {
    leaveConversationRoom(currentConversationId.value)
  }

  currentConversationId.value = conv.id
  messages.value = []

  // 加入新房间
  joinConversationRoom(conv.id)

  // 获取消息并标记已读
  await fetchMessages(conv.id)
  try {
    await markRead(conv.id)
    conv.unread_count = 0
    fetchUnreadCount()
  } catch { /* ignore */ }
}

async function fetchAvailableCoaches() {
  try {
    const res = await get<any>('/api/student/coaches')
    if (res.data?.code === 0) {
      availableCoaches.value = res.data.data?.list || []
    }
  } catch (e) {
    console.error('获取教练列表失败:', e)
  }
}

async function handleStartChat() {
  // 自动获取当前学生的教练ID
  const coachId = currentUser.value?.coach_id

  if (!coachId) {
    // 没有分配教练，尝试获取可选教练列表
    if (availableCoaches.value.length === 0) {
      await fetchAvailableCoaches()
    }
    if (availableCoaches.value.length > 0) {
      showCoachSelector.value = true
    } else {
      alert('暂无可选教练，请联系管理员')
    }
    return
  }

  await createConversationWithCoach(coachId)
}

async function createConversationWithCoach(coachId: number) {
  try {
    const res = await createConversation({ coach_id: coachId })
    if (res.data?.code === 0) {
      const newConv = res.data.data
      await fetchConversations()
      if (newConv && newConv.id) {
        selectConversation(newConv)
      }
    }
  } catch (e: any) {
    errorMessage.value = e?.message || '创建会话失败'
  } finally {
    showCoachSelector.value = false
  }
}

function selectCoach(coach: any) {
  createConversationWithCoach(coach.id)
}

// ==================== 发送消息 ====================
async function handleSend() {
  const text = newMsgText.value.trim()
  if (!text || !currentConversationId.value) return

  // 优先使用 WebSocket（低延迟）
  if (wsConnected.value) {
    sendMessageViaSocket(currentConversationId.value, text)
    // 乐观添加消息到列表（id暂时为0，等服务器确认后更新）
    messages.value.push({
      id: 0, // 临时ID
      conversation_id: currentConversationId.value,
      sender_type: 'student',
      sender_id: currentUser.value?.userId || 0,
      content: text,
      message_type: 1,
      status: 1,
      create_time: new Date().toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
    })
  } else {
    // 降级为 REST API
    try {
      const res = await sendMessage(currentConversationId.value, text)
      if (res.data?.code === 0) {
        messages.value.push(res.data.data)
      }
    } catch (e) {
      console.error('发送失败:', e)
    }
  }

  newMsgText.value = ''
  await scrollToBottom()
  emitStopTyping(currentConversationId.value)
}

// ==================== 正在输入 ====================
function handleTyping() {
  if (!currentConversationId.value) return
  emitTyping(currentConversationId.value)
  if (typingTimer) clearTimeout(typingTimer)
  typingTimer = setTimeout(() => {
    emitStopTyping(currentConversationId.value!)
  }, 2000)
}

// ==================== WebSocket 事件监听 ====================
function setupSocketListeners() {
  if (!socket) return

  socket.on('new_message', (msg: ChatMsg) => {
    // 只处理当前会话的消息
    if (msg.conversation_id === currentConversationId.value) {
      // 替换临时消息（id=0 的本地乐观消息）
      const tempIdx = messages.value.findIndex(m => m.id === 0 && m.content === msg.content)
      if (tempIdx >= 0) {
        messages.value[tempIdx] = msg
      } else {
        messages.value.push(msg)
      }
      scrollToBottom()
    }
    // 刷新会话列表以更新最后消息
    fetchConversations()
    fetchUnreadCount()
  })

  socket.on('message_sent', (msg: ChatMsg) => {
    // 服务器确认发送成功，替换临时消息
    const tempIdx = messages.value.findIndex(m => m.id === 0 && m.content === msg.content)
    if (tempIdx >= 0) {
      messages.value[tempIdx] = msg
    }
  })

  socket.on('user_typing', (data: { conversation_id: number; user_type: string }) => {
    if (data.conversation_id === currentConversationId.value && data.user_type === 'coach') {
      coachTyping.value = true
    }
  })

  socket.on('user_stop_typing', (data: { conversation_id: number; user_type: string }) => {
    if (data.conversation_id === currentConversationId.value && data.user_type === 'coach') {
      coachTyping.value = false
    }
  })

  socket.on('messages_read', (data: { conversation_id: number; reader_type: string }) => {
    if (data.conversation_id === currentConversationId.value) {
      // 对方已读，更新消息状态
      messages.value.forEach(m => m.status = m.status === 1 ? 2 : m.status)
    }
  })

  // 实时接收未读计数更新（接收方获得红点 / 已读后红点消失）
  socket.on('unread_count_updated', (data: { conversation_id: number; conversation_unread: number; total_unread: number }) => {
    // 更新对应会话的未读数
    const conv = conversations.value.find(c => c.id === data.conversation_id)
    if (conv) {
      conv.unread_count = data.conversation_unread
    }
    // 更新总未读数
    totalUnread.value = data.total_unread
  })
}

// ==================== 辅助 ====================
async function scrollToBottom() {
  await nextTick()
  const el = document.getElementById('msg-container')
  if (el) el.scrollTop = el.scrollHeight
}

function isSelf(msg: ChatMsg): boolean {
  // 统一用 sender_type 判断：学员端自己发的是 'student'
  return msg.sender_type === 'student'
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await fetchConversations()
  await fetchUnreadCount()
  setupSocketListeners()
})

onUnmounted(() => {
  if (currentConversationId.value) {
    leaveConversationRoom(currentConversationId.value)
  }
})
</script>

<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <h3>对话列表</h3>
        <button class="btn-new-chat" @click="handleStartChat">+ 新对话</button>
      </div>

      <div class="conversation-list" v-if="conversations.length > 0">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: conv.id === currentConversationId }"
          @click="selectConversation(conv)"
        >
          <div class="conv-avatar">👤</div>
          <div class="conv-info">
            <div class="conv-name">
              {{ conv.coach_name || `教练 #${conv.coach_id}` }}
              <span v-if="conv.unread_count > 0" class="badge">{{ conv.unread_count }}</span>
            </div>
            <div class="conv-preview">{{ conv.last_message || '暂无消息' }}</div>
          </div>
          <div class="conv-time">{{ conv.last_message_time?.slice(5, 16) }}</div>
        </div>
      </div>

      <div class="empty-conversations" v-else-if="!showCoachSelector">
        <p>暂无对话</p>
        <p class="hint">点击「新对话」开始与教练沟通</p>
      </div>

      <!-- 教练选择器 -->
      <div class="coach-selector" v-if="showCoachSelector">
        <div class="selector-header">
          <h4>选择一位教练</h4>
          <button class="btn-close-selector" @click="showCoachSelector = false">✕</button>
        </div>
        <div class="coach-list">
          <div
            v-for="coach in availableCoaches"
            :key="coach.id"
            class="coach-item"
            @click="selectCoach(coach)"
          >
            <div class="coach-avatar">👨‍🏫</div>
            <div class="coach-info">
              <div class="coach-name">{{ coach.school_name || `教练 #${coach.id}` }}</div>
              <div class="coach-detail" v-if="coach.email">{{ coach.email }}</div>
            </div>
          </div>
          <div v-if="availableCoaches.length === 0" class="no-coaches">
            暂无可选教练
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧消息区域 -->
    <main class="chat-main">
      <!-- 空状态 -->
      <div v-if="!currentConversationId" class="empty-state">
        <div class="empty-icon">💬</div>
        <h3>选择一个对话</h3>
        <p>从左侧列表选择一位教练开始聊天</p>
      </div>

      <!-- 聊天区域 -->
      <template v-else>
        <div class="chat-messages" id="msg-container">
          <div v-if="loadingMsgs" class="loading">加载中...</div>
          <div v-for="msg in messages" :key="msg.id || (msg.create_time + msg.content)" class="msg-row" :class="{ self: isSelf(msg) }">
            <div class="msg-bubble" :class="{ self: isSelf(msg) }">
              <div class="msg-text">{{ msg.content }}</div>
              <div class="msg-meta">
                <span class="msg-time">{{ msg.create_time?.slice(11, 19) }}</span>
                <span v-if="isSelf(msg)" class="msg-status">
                  {{ msg.status === 2 ? '已读' : msg.status === 3 ? '已撤回' : '' }}
                </span>
              </div>
            </div>
          </div>
          <!-- 对方正在输入 -->
          <div v-if="coachTyping" class="typing-indicator">
            <span></span><span></span><span></span> 对方正在输入...
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input-bar">
          <input
            v-model="newMsgText"
            type="text"
            class="msg-input"
            placeholder="输入消息..."
            maxlength="5000"
            @keyup.enter="handleSend"
            @input="handleTyping"
          />
          <button class="btn-send" :disabled="!newMsgText.trim()" @click="handleSend">发送</button>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
/* ====== 布局 ====== */
.chat-page {
  display: flex;
  height: calc(100vh - 60px);
  background: #f5f6fa;
}

/* ====== 侧边栏 ====== */
.chat-sidebar {
  width: 320px;
  min-width: 320px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1a1a1a;
}

.btn-new-chat {
  padding: 6px 14px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background .2s;
}
.btn-new-chat:hover { background: #4096ff; }

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  cursor: pointer;
  transition: background .15s;
  border-bottom: 1px solid #f8f8f8;
}
.conv-item:hover { background: #f0f5ff; }
.conv-item.active { background: #e6f4ff; }

.conv-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}

.conv-info {
  flex: 1;
  min-width: 0;
}
.conv-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge {
  background: #ff4d4f;
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}
.conv-preview {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-time {
  font-size: 11px;
  color: #bbb;
  flex-shrink: 0;
  margin-left: 8px;
}

.empty-conversations {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.empty-conversations .hint { font-size: 12px; margin-top: 8px; }

/* ====== 聊天主区域 ====== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { margin: 0 0 8px; color: #666; }
.empty-state p { margin: 0; font-size: 14px; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading { text-align: center; color: #999; padding: 40px 0; }

.msg-row {
  display: flex;
}
.msg-row.self { justify-content: flex-end; }

.msg-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f0f0f0;
  word-break: break-word;
}
.msg-bubble.self {
  background: #1677ff;
  color: #fff;
}
.msg-text {
  font-size: 14px;
  line-height: 1.6;
}
.msg-meta {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 4px;
  font-size: 11px;
  color: #bbb;
}
.msg-bubble.self .msg-meta { color: rgba(255,255,255,.7); }

/* 正在输入动画 */
.typing-indicator {
  margin-left: 20px;
  padding: 8px 14px;
  font-size: 13px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 4px;
}
.typing-indicator span {
  width: 8px; height: 8px;
  background: #ccc;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* ====== 输入栏 ====== */
.chat-input-bar {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
  gap: 12px;
}
.msg-input {
  flex: 1;
  height: 40px;
  padding: 0 14px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 14px;
  outline: none;
  transition: border-color .2s;
}
.msg-input:focus { border-color: #1677ff; }
.btn-send {
  height: 40px;
  padding: 0 24px;
  background: #1677ff;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: background .2s;
}
.btn-send:disabled { background: #d9d9d9; cursor: not-allowed; }
.btn-send:not(:disabled):hover { background: #4096ff; }

/* ====== 教练选择器 ====== */
.coach-selector {
  flex: 1;
  overflow-y: auto;
  border-top: 1px solid #f0f0f0;
}
.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  position: sticky;
  top: 0;
  z-index: 1;
}
.selector-header h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
}
.btn-close-selector {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid #e0e0e0;
  background: #fff;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s;
}
.btn-close-selector:hover {
  background: #ff4d4f;
  color: #fff;
  border-color: #ff4d4f;
}
.coach-list {
  padding: 8px 0;
}
.coach-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background .15s;
  border-bottom: 1px solid #f8f8f8;
}
.coach-item:hover { background: #f0f5ff; }
.coach-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}
.coach-info { flex: 1; min-width: 0; }
.coach-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}
.coach-detail {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.no-coaches {
  padding: 40px 16px;
  text-align: center;
  color: #999;
  font-size: 13px;
}
</style>
