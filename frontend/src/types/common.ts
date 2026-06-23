// src/types/common.ts
export interface UserProfile {
  userId: number
  name: string
  avatar: string
  phone: string
  email: string
  role: 'student' | 'coach' | 'admin'
  adminType?: 1 | 2 | 3 // 1=超级管理员, 2=内容编辑, 3=运营管理
}

export interface LoginRequest {
  account: string  // 邮箱或手机号
  password: string
  loginType: 'email' | 'phone'
}

export interface LoginResponse {
  token: string
  user: UserProfile
}

export interface RegisterRequest {
  name: string
  account: string
  password: string
  registerType: 'email' | 'phone'
  agreeTerms: boolean
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
