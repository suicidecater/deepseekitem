/**
 * 通知系统 API
 */
import { get, post, put, del } from '@/api/request'
import type {
  NotificationItem,
  NotificationFormData,
  UnreadCountData,
} from '@/types/notification'
import type { PaginatedData } from '@/types/common'

// ======================== 管理员端 ========================

/** 管理员 - 获取通知列表 */
export function adminGetNotifications(params?: {
  page?: number
  page_size?: number
  type?: number
  status?: number
  target_role?: number
}) {
  return get<PaginatedData<NotificationItem>>('/api/admin/notifications', params)
}

/** 管理员 - 发布通知 */
export function adminCreateNotification(data: NotificationFormData) {
  return post<NotificationItem>('/api/admin/notifications', data)
}

/** 管理员 - 编辑通知 */
export function adminUpdateNotification(id: number, data: Partial<NotificationFormData>) {
  return put<NotificationItem>(`/api/admin/notifications/${id}`, data)
}

/** 管理员 - 删除通知 */
export function adminDeleteNotification(id: number) {
  return del(`/api/admin/notifications/${id}`)
}

/** 管理员 - 撤回通知 */
export function adminRecallNotification(id: number) {
  return put<NotificationItem>(`/api/admin/notifications/${id}/recall`)
}

// ======================== 教练端 ========================

/** 教练 - 获取通知列表 */
export function coachGetNotifications(params?: { page?: number; page_size?: number }) {
  return get<PaginatedData<NotificationItem>>('/api/coach/notifications', params)
}

/** 教练 - 获取未读数量 */
export function coachGetUnreadCount() {
  return get<UnreadCountData>('/api/coach/notifications/unread-count')
}

/** 教练 - 标记单条已读 */
export function coachReadNotification(id: number) {
  return put(`/api/coach/notifications/${id}/read`)
}

/** 教练 - 全部标记已读 */
export function coachReadAllNotifications() {
  return put('/api/coach/notifications/read-all')
}

// ======================== 学员端 ========================

/** 学员 - 获取通知列表 */
export function studentGetNotifications(params?: { page?: number; page_size?: number }) {
  return get<PaginatedData<NotificationItem>>('/api/student/notifications', params)
}

/** 学员 - 获取未读数量 */
export function studentGetUnreadCount() {
  return get<UnreadCountData>('/api/student/notifications/unread-count')
}

/** 学员 - 标记单条已读 */
export function studentReadNotification(id: number) {
  return put(`/api/student/notifications/${id}/read`)
}

/** 学员 - 全部标记已读 */
export function studentReadAllNotifications() {
  return put('/api/student/notifications/read-all')
}
