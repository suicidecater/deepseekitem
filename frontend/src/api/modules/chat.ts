/**
 * 对话系统 API
 */
import { get, post, put } from '@/api/request'

/** 获取会话列表 */
export function getConversations(page = 1, pageSize = 20) {
  return get<{ list: any[]; pagination: any }>('/api/chat/conversations', { page, page_size: pageSize })
}

/** 创建/恢复会话 */
export function createConversation(data: { coach_id?: number; student_id?: number }) {
  return post<any>('/api/chat/conversations', data)
}

/** 获取会话消息列表 */
export function getMessages(conversationId: number, page = 1, pageSize = 50) {
  return get<{ list: any[]; pagination: any }>(
    `/api/chat/conversations/${conversationId}/messages`,
    { page, page_size: pageSize }
  )
}

/** 发送消息 (REST方式) */
export function sendMessage(conversationId: number, content: string, messageType = 1) {
  return post<any>(`/api/chat/conversations/${conversationId}/messages`, {
    content,
    message_type: messageType
  })
}

/** 标记已读 */
export function markRead(conversationId: number) {
  return put<any>(`/api/chat/conversations/${conversationId}/read`)
}

/** 归档会话 */
export function archiveConversation(conversationId: number) {
  return put<any>(`/api/chat/conversations/${conversationId}/archive`)
}

/** 获取总未读数 */
export function getUnreadCount() {
  return get<{ unread_count: number }>('/api/chat/unread-count')
}
