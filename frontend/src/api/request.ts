/**
 * src/api/request.ts
 * axios 封装 + 401 自动刷新 Token 拦截器
 *
 * 后端 JWT 配置：
 *   - access_token 过期 2 小时（config.py:41）
 *   - refresh_token 过期 7 天（config.py:42）
 *   - 统一响应：{ code: 0, message: "...", data: {...} }
 *   - 认证头：Authorization: Bearer <token>
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { storage } from '@/utils/storage'

// ======================== 常量 ========================

/** 用于跳过拦截器的请求标识（如 refresh 本身） */
const SKIP_AUTH_REFRESH = Symbol('skipAuthRefresh')

// ======================== 刷新 Token 锁 ========================

/** 正在刷新 Token 的 Promise（并发请求共享同一个刷新操作） */
let refreshPromise: Promise<boolean> | null = null

/**
 * 发起 Token 刷新请求（加锁，防止并发）
 * 返回 true 表示刷新成功，false 表示失败
 */
async function doRefreshToken(): Promise<boolean> {
  const refreshToken = storage.get<string>('refresh_token')
  if (!refreshToken) return false

  try {
    const res = await axios.post('/api/auth/refresh', null, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      },
      // 标记跳过拦截器，防止死循环
      [SKIP_AUTH_REFRESH as any]: true
    })

    if (res.data?.code === 0 && res.data?.data?.token) {
      storage.set('token', res.data.data.token)
      // 如果后端返回了新的 refresh_token 也更新
      if (res.data.data.refresh_token) {
        storage.set('refresh_token', res.data.data.refresh_token)
      }
      return true
    }
    return false
  } catch {
    return false
  }
}

/**
 * 获取新的 Token（带并发锁）
 * 如果已有刷新进行中，直接复用其 Promise
 */
function refreshTokenWithLock(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  refreshPromise = doRefreshToken().finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

// ======================== 创建 axios 实例 ========================

const request: AxiosInstance = axios.create({
  baseURL: '',          // 通过 Vite 代理转发，不需要设置 baseURL
  timeout: 30000,        // 30 秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// ======================== 请求拦截器 ========================

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.get<string>('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ======================== 响应拦截器 ========================

request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 业务层统一检查 code
    const { data } = response
    if (data && typeof data.code === 'number' && data.code !== 0) {
      // 非 0 的业务错误码，统一 reject，让调用方 catch 处理
      return Promise.reject({
        code: data.code,
        message: data.message || '请求失败',
        data: data.data
      })
    }
    return response
  },
  async (error) => {
    // 网络错误或 HTTP 状态码错误
    if (!error.response) {
      // 网络超时/中断
      return Promise.reject({
        code: -1,
        message: '网络连接失败，请检查网络',
        data: null
      })
    }

    const { status, config } = error.response

    // ======================== 401 自动刷新 Token ========================
    if (status === 401) {
      // 跳过标记的请求（如 refresh 自身）不重试
      if ((config as any)[SKIP_AUTH_REFRESH]) {
        return Promise.reject(error)
      }

      // 尝试刷新 Token
      const refreshed = await refreshTokenWithLock()

      if (refreshed) {
        // 刷新成功：更新 Authorization 头并重试原请求
        const newToken = storage.get<string>('token')
        if (newToken) {
          config.headers.Authorization = `Bearer ${newToken}`
        }
        return request(config)
      }

      // 刷新失败：清除登录状态，跳转登录页
      storage.remove('token')
      storage.remove('refresh_token')
      storage.remove('user')

      // 避免在登录页重复跳转
      if (window.location.pathname !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }

      return Promise.reject({
        code: 401,
        message: '登录已过期，请重新登录',
        data: null
      })
    }

    // ======================== 其他 HTTP 错误码 ========================
    const errorMessages: Record<number, string> = {
      400: '请求参数错误',
      403: '没有访问权限',
      404: '请求的资源不存在',
      405: '请求方法不允许',
      429: '请求过于频繁，请稍后重试',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂不可用',
      504: '网关超时'
    }

    return Promise.reject({
      code: status,
      message: errorMessages[status] || `请求失败 (${status})`,
      data: error.response?.data?.data ?? null
    })
  }
)

// ======================== 便捷方法 ========================

export function get<T = any>(url: string, params?: Record<string, any>, config?: AxiosRequestConfig) {
  return request.get<any, AxiosResponse<{ code: number; message: string; data: T }>>(url, { params, ...config })
}

export function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
  return request.post<any, AxiosResponse<{ code: number; message: string; data: T }>>(url, data, config)
}

export function put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
  return request.put<any, AxiosResponse<{ code: number; message: string; data: T }>>(url, data, config)
}

export function del<T = any>(url: string, config?: AxiosRequestConfig) {
  return request.delete<any, AxiosResponse<{ code: number; message: string; data: T }>>(url, config)
}

export default request
