<script setup lang="ts">
// src/views/student/AiQAView.vue - AI交规问答
import { ref, nextTick } from 'vue'
import { useSSE } from '@/composables/useSSE'
import { useAppStore } from '@/stores/app'
import type { ChatMessage } from '@/types/ai'

const appStore = useAppStore()
const { isStreaming, error, streamChat, abort } = useSSE()

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  structured?: any
}

const messages = ref<DisplayMessage[]>([
  {
    role: 'assistant',
    content: '你好！我是交通安全AI助手，基于DeepSeek大模型。你可以问我任何关于交通法规、驾驶技巧、考试题目相关的问题。',
    timestamp: Date.now()
  }
])
const inputText = ref('')
const chatContainer = ref<HTMLElement>()

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
</style>
