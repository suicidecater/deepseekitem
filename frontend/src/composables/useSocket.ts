/**
 * Socket.IO WebSocket 组合式函数
 * 用于教练-学员实时对话
 */
import { ref, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'
import { storage } from '@/utils/storage'

let socket: Socket | null = null
const connected = ref(false)
const connectionError = ref('')

/** 获取 WebSocket 连接（单例） */
export function useSocket() {
  if (!socket) {
    const token = storage.get<string>('token')
    if (!token) {
      connectionError.value = '未登录，无法建立WebSocket连接'
      return { socket: null, connected, connectionError }
    }

    const wsUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
    socket = io(wsUrl, {
      // 通过 auth 传递 token，服务端在 connect 事件中校验
      query: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000
    })

    socket.on('connect', () => {
      connected.value = true
      connectionError.value = ''
      console.log('[Socket] WebSocket 已连接:', socket?.id)
    })

    socket.on('connected', (data: any) => {
      console.log('[Socket] 认证成功:', data)
    })

    socket.on('auth_error', (data: any) => {
      connectionError.value = data.message || 'WebSocket认证失败'
      console.error('[Socket] 认证失败:', data.message)
      disconnectSocket()
    })

    socket.on('disconnect', (reason: string) => {
      connected.value = false
      console.log('[Socket] WebSocket 已断开:', reason)
    })

    socket.on('connect_error', (err: Error) => {
      connected.value = false
      connectionError.value = 'WebSocket连接失败，将使用HTTP轮询'
      console.warn('[Socket] 连接错误:', err.message)
    })
  }

  return { socket, connected, connectionError }
}

/** 断开 WebSocket */
export function disconnectSocket() {
  if (socket) {
    socket.removeAllListeners()
    socket.disconnect()
    socket = null
    connected.value = false
  }
}

/** 加入会话房间 */
export function joinConversationRoom(conversationId: number) {
  socket?.emit('join_conversation', { conversation_id: conversationId })
}

/** 离开会话房间 */
export function leaveConversationRoom(conversationId: number) {
  socket?.emit('leave_conversation', { conversation_id: conversationId })
}

/** WebSocket 发送消息 */
export function sendMessageViaSocket(conversationId: number, content: string, msgType = 1) {
  socket?.emit('send_message', {
    conversation_id: conversationId,
    content,
    message_type: msgType
  })
}

/** 发送正在输入事件 */
export function emitTyping(conversationId: number) {
  socket?.emit('typing', { conversation_id: conversationId })
}

/** 发送停止输入事件 */
export function emitStopTyping(conversationId: number) {
  socket?.emit('stop_typing', { conversation_id: conversationId })
}
