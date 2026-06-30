<script setup lang="ts">
// src/views/student/AiQAView.vue - AI交规问答（支持历史对话恢复）
import { ref, nextTick, onMounted } from 'vue'
import { useSSE } from '@/composables/useSSE'
import { useAppStore } from '@/stores/app'
import { get, del } from '@/api/request'
import type { ChatMessage } from '@/types/ai'

onMounted(() => loadHistory())

const appStore = useAppStore()
const { isStreaming, error, streamChat, abort } = useSSE()

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  structured?: any
}

const welcomeMsg: DisplayMessage = {
  role: 'assistant',
  content: '你好！我是交通安全AI助手，基于DeepSeek大模型。你可以问我任何关于交通法规、驾驶技巧、考试题目相关的问题。',
  timestamp: Date.now()
}

const messages = ref<DisplayMessage[]>([welcomeMsg])
const inputText = ref('')
const chatContainer = ref<HTMLElement>()
const clearing = ref(false)
const showConfirm = ref(false)

// 从后端恢复历史对话
async function loadHistory() {
  try {
    const res = await get<Array<{ id: number; user_msg: string; ai_msg: string; create_time: string }>>('/api/ai/chat/history')
    const history = res.data.data
    if (history && history.length > 0) {
      const restored: DisplayMessage[] = []
      for (const h of history) {
        if (h.user_msg) {
          restored.push({ role: 'user', content: h.user_msg, timestamp: new Date(h.create_time).getTime() || Date.now() })
        }
        if (h.ai_msg) {
          restored.push({ role: 'assistant', content: h.ai_msg, timestamp: new Date(h.create_time).getTime() || Date.now() })
        }
      }
      if (restored.length > 0) {
        messages.value = restored
        await nextTick()
        scrollToBottom()
        return
      }
    }
  } catch {
    // 网络异常时保留默认欢迎语
  }
}

// 弹出确认弹窗
function confirmClear() {
  showConfirm.value = true
}

// 取消清空
function cancelClear() {
  showConfirm.value = false
}

// 确认清空对话（前端 + 后端同步清除）
async function clearHistory() {
  showConfirm.value = false
  try {
    clearing.value = true
    await del('/api/ai/chat/history')
    messages.value = [welcomeMsg]
    appStore.showToast('对话记录已清空', 'success')
  } catch {
    appStore.showToast('清空失败，请重试', 'error')
  } finally {
    clearing.value = false
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text, timestamp: Date.now() })
  await scrollToBottom()

  // 构建历史
  const history: ChatMessage[] = messages.value.map(m => ({
    role: m.role === 'assistant' ? 'assistant' : 'user',
    content: m.content
  }))

  // 添加 AI 占位消息
  const aiMsg: DisplayMessage = { role: 'assistant', content: '', timestamp: Date.now() }
  messages.value.push(aiMsg)
  const aiIdx = messages.value.length - 1

  try {
    const stream = streamChat(text, history)
    for await (const chunk of stream) {
      if (chunk === undefined) continue
      if (typeof chunk === 'object') {
        // 结构化数据（end 事件返回）
        messages.value[aiIdx].structured = chunk
        break
      }
      messages.value[aiIdx].content += String(chunk)
      await scrollToBottom()
    }
  } catch (e: any) {
    if (e.name !== 'AbortError') {
      messages.value[aiIdx].content = messages.value[aiIdx].content || `抱歉，出了点问题：${e.message}`
    }
  }
}

function handleAbort() {
  abort()
  // 移除最后一条未完成的消息
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant' && !last.content) {
    messages.value.pop()
  }
}

function handleVoice() {
  appStore.showToast('语音输入功能开发中，请使用文字输入', 'info')
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="ai-qa-page">
    <div class="qa-header">
      <h2>AI交规问答</h2>
      <span class="qa-badge">DeepSeek 大模型驱动</span>
      <button
        class="btn btn-outline btn-sm"
        :disabled="clearing || messages.length <= 1"
        @click="confirmClear"
      >{{ clearing ? '清空中...' : '清空对话' }}</button>
    </div>

    <div ref="chatContainer" class="qa-messages">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="qa-message"
        :class="msg.role"
      >
        <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="msg-body">
          <div class="msg-content">{{ msg.content }}</div>
          <div v-if="msg.structured" class="msg-structured">
            <div v-if="msg.structured.knowledgePoint" class="structured-block">
              <strong>📚 知识点：</strong>{{ msg.structured.knowledgePoint }}
            </div>
            <div v-if="msg.structured.lawRef" class="structured-block">
              <strong>📜 法规引用：</strong>{{ msg.structured.lawRef }}
            </div>
            <div v-if="msg.structured.caseStudy" class="structured-block">
              <strong>📋 案例分析：</strong>{{ msg.structured.caseStudy }}
            </div>
          </div>
          <span v-if="isStreaming && idx === messages.length - 1 && msg.role === 'assistant'" class="typing-dot">...</span>
        </div>
      </div>
    </div>

    <div class="qa-input-area">
      <div class="qa-input-row">
        <button class="btn btn-icon" title="语音输入" @click="handleVoice">🎤</button>
        <textarea
          v-model="inputText"
          class="qa-input"
          placeholder="输入你的问题..."
          rows="1"
          @keydown="handleKeydown"
          :disabled="isStreaming"
        ></textarea>
        <button v-if="isStreaming" class="btn btn-outline" @click="handleAbort">中止</button>
        <button v-else class="btn btn-primary" :disabled="!inputText.trim()" @click="sendMessage">发送</button>
      </div>
    </div>

    <!-- 清空确认弹窗 -->
    <Teleport to="body">
      <div v-if="showConfirm" class="confirm-overlay" @click.self="cancelClear">
        <div class="confirm-dialog">
          <h3>确认清空</h3>
          <p>清空后将删除你所有的对话记录，此操作不可恢复。确定要继续吗？</p>
          <div class="confirm-actions">
            <button class="btn btn-outline" @click="cancelClear" :disabled="clearing">取消</button>
            <button class="btn btn-danger" @click="clearHistory" :disabled="clearing">
              {{ clearing ? '清空中...' : '确认清空' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.ai-qa-page { display: flex; flex-direction: column; height: calc(100vh - var(--header-height) - 24px); max-width: 900px; margin: 0 auto; padding: 20px; }

.qa-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.qa-header h2 { font-size: var(--font-size-xl); }
.qa-badge { font-size: var(--font-size-xs); padding: 2px 10px; background: var(--color-primary-light); color: var(--color-primary); border-radius: var(--radius-sm); }

.qa-messages { flex: 1; overflow-y: auto; padding: 16px; background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); margin-bottom: 12px; }

.qa-message { display: flex; gap: 12px; margin-bottom: 20px; }
.qa-message.user { flex-direction: row-reverse; }
.qa-message.user .msg-body { align-items: flex-end; }

.msg-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; background: var(--color-primary-light); }

.msg-body { display: flex; flex-direction: column; max-width: 75%; }
.msg-content {
  padding: 12px 16px; border-radius: var(--radius-lg); font-size: var(--font-size-sm); line-height: 1.7;
  white-space: pre-wrap; word-break: break-word;
}
.qa-message.user .msg-content { background: var(--color-primary); color: #fff; border-radius: var(--radius-lg) var(--radius-lg) 0 var(--radius-lg); }
.qa-message.assistant .msg-content { background: #F5F5F5; border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 0; }

.msg-structured { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.structured-block { padding: 8px 12px; background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-light); font-size: var(--font-size-xs); color: var(--color-text-secondary); }

.typing-dot { animation: blink 1s infinite; }
@keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0 } }

.qa-input-area { background: #fff; border-radius: var(--radius-lg); padding: 12px; border: 1px solid var(--color-border-light); }
.qa-input-row { display: flex; align-items: flex-end; gap: 8px; }
.qa-input { flex: 1; border: none; outline: none; resize: none; font-size: var(--font-size-sm); padding: 8px 0; max-height: 120px; font-family: inherit; }
.btn-icon { padding: 8px 10px; font-size: 20px; border-radius: var(--radius-md); }

/* 确认弹窗 */
.confirm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.confirm-dialog {
  background: #fff; border-radius: var(--radius-lg); padding: 28px 32px;
  width: 400px; max-width: 90vw; box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
.confirm-dialog h3 { font-size: var(--font-size-lg); margin-bottom: 12px; }
.confirm-dialog p { color: var(--color-text-secondary); font-size: var(--font-size-sm); line-height: 1.6; margin-bottom: 24px; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 12px; }
.btn-danger { background: var(--color-danger, #e74c3c); color: #fff; border: none; padding: 8px 20px; border-radius: var(--radius-md); cursor: pointer; font-size: var(--font-size-sm); }
.btn-danger:hover { opacity: 0.9; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
