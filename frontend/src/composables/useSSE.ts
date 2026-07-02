// src/composables/useSSE.ts
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { ChatMessage } from '@/types/ai'

export function useSSE() {
  const isStreaming = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null

  async function* streamChat(question: string, history: ChatMessage[] = []) {
    const authStore = useAuthStore()
    isStreaming.value = true
    error.value = null
    abortController = new AbortController()

    const response = await fetch(`/api/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ question, history }),
      signal: abortController.signal
    })

    if (!response.ok) {
      const retryAfter = response.status === 429
      error.value = retryAfter ? '请求过于频繁，请稍后重试' : `服务错误 (${response.status})`
      isStreaming.value = false
      throw new Error(error.value)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const raw = line.slice(6).trim()
          // 处理 [DONE] 结束标记
          if (raw === '[DONE]') {
            isStreaming.value = false
            return ''
          }
          try {
            const event = JSON.parse(raw)
            if (event.error) {
              error.value = event.error
              isStreaming.value = false
              throw new Error(event.error)
            }
            // 兼容有/无 type 字段
            if (event.type === 'end') {
              isStreaming.value = false
              return event.structured || ''
            }
            if (event.content) {
              yield event.content
            }
          } catch {
            // 非 JSON 行跳过
          }
        }
      }
    }
    isStreaming.value = false
  }

  function abort() {
    abortController?.abort()
    isStreaming.value = false
  }

  function clearError() {
    error.value = null
  }

  return { isStreaming, error, streamChat, abort, clearError }
}
