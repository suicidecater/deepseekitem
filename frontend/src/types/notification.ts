/**
 * 通知系统类型定义
 */

/** 通知类型 */
export type NotificationType = 1 | 2 | 3
export const NotificationTypeMap: Record<NotificationType, string> = {
  1: '系统公告',
  2: '培训通知',
  3: '其他',
}

/** 接收角色 */
export type TargetRole = 1 | 2 | 3
export const TargetRoleMap: Record<TargetRole, string> = {
  1: '教练',
  2: '学员',
  3: '全部',
}

/** 通知状态 */
export type NotificationStatus = 1 | 2 | 3
export const NotificationStatusMap: Record<NotificationStatus, string> = {
  1: '草稿',
  2: '已发布',
  3: '已撤回',
}

/** 通知实体 */
export interface NotificationItem {
  id: number
  title: string
  content: string
  type: NotificationType
  target_role: TargetRole
  publisher_id: number
  status: NotificationStatus
  create_time: string
  publish_time: string | null
  /** 以下字段来自 user_notification 联表查询 */
  is_read?: number
  read_time?: string | null
}

/** 发布/编辑通知请求 */
export interface NotificationFormData {
  title: string
  content: string
  type: NotificationType
  target_role: TargetRole
  status?: NotificationStatus
}

/** 未读数量 */
export interface UnreadCountData {
  count: number
}
