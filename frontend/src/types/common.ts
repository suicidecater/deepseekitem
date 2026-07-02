// src/types/common.ts
export interface UserProfile {
  userId: number
  name: string
  avatar: string
  email: string
  role: 'student' | 'coach' | 'admin'
  adminType?: 1 | 2 | 3 // 1=超级管理员, 2=内容管理, 3=运营管理
  studySubject?: 1 | 4 | 5 // 学习方向: 1=科目一/4=科目四/5=专业人员
  evaluationStatus?: 0 | 1 // 测评状态: 0=未测评/1=已完成
  evaluationStatusMap?: Record<string, 0 | 1> // 各方向测评状态 {"1":1,"4":0,"5":0}
  coach_id?: number | null // 分配的教练ID
  coach_name?: string // 教练名称
  coach_phone?: string // 教练电话
}

// ======================== 认证相关类型 ========================

/** 发送验证码 */
export interface SendCodeRequest {
  email: string
  type: 'register' | 'login'
}

/** 学员注册 */
export interface StudentRegisterRequest {
  email: string
  password: string
  name: string
  trainType: 1 | 2 | 3 | 4
  carType?: string
  code: string
}

/** 教练注册 */
export interface CoachRegisterRequest {
  email: string
  password: string
  schoolName: string
  trainType: 1 | 2 | 3 | 4
  schoolAddress?: string
  schoolPhone?: string
  code: string
}

/** 管理员注册 */
export interface AdminRegisterRequest {
  email: string
  password: string
  adminType: 1 | 2 | 3
  code: string
}

/** 登录请求 */
export interface LoginRequest {
  email: string
  password?: string
  code?: string
}

/** 登录响应 */
export interface LoginResponse {
  token: string
  refresh_token: string
  user: UserProfile
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}
