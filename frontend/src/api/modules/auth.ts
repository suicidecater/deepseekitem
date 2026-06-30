/**
 * src/api/modules/auth.ts
 * 认证相关 API — 三种用户分开注册/登录
 */
import { get, post } from '@/api/request'
import type {
  ApiResponse,
  UserProfile,
  SendCodeRequest,
  StudentRegisterRequest,
  CoachRegisterRequest,
  AdminRegisterRequest,
  LoginRequest,
  LoginResponse,
} from '@/types/common'

// ======================== 通用 ========================

/** 发送验证码 */
export function sendCode(params: SendCodeRequest) {
  return post<ApiResponse>('/api/auth/send-code', params)
}

/** 刷新 Token */
export function refreshToken() {
  return post<{ token: string; refresh_token?: string }>('/api/auth/refresh')
}

/** 退出登录 */
export function logout() {
  return post('/api/auth/logout')
}

/** 获取当前用户信息 */
export function getCurrentUser() {
  return get<UserProfile>('/api/auth/me')
}

// ======================== 学员 ========================

/** 学员注册 */
export function studentRegister(params: StudentRegisterRequest) {
  return post<LoginResponse>('/api/auth/student/register', params)
}

/** 学员登录 */
export function studentLogin(params: LoginRequest) {
  return post<LoginResponse>('/api/auth/student/login', params)
}

// ======================== 教练 ========================

/** 教练注册 */
export function coachRegister(params: CoachRegisterRequest) {
  return post<LoginResponse>('/api/auth/coach/register', params)
}

/** 教练登录 */
export function coachLogin(params: LoginRequest) {
  return post<LoginResponse>('/api/auth/coach/login', params)
}

// ======================== 平台管理员 ========================

/** 管理员注册 */
export function adminRegister(params: AdminRegisterRequest) {
  return post<LoginResponse>('/api/auth/admin/register', params)
}

/** 管理员登录 */
export function adminLogin(params: LoginRequest) {
  return post<LoginResponse>('/api/auth/admin/login', params)
}
