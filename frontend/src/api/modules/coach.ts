/**
 * src/api/modules/coach.ts
 * 教练端 API 模块
 */
import { get } from '../request'
import request from '../request'

// ======================== 类型定义 ========================

export interface StudentStats {
  total: number
  active: number
  avgScore: number
  avgAccuracy: number
  // 新增指标
  pendingTutorCount: number
  unfinishedExamCount: number
  totalErrors: number
  topWeakDimension: string
}

export interface StudentListItem {
  id: number
  name: string
  email: string
  carType: string
  score: number
  accuracy: number
  studyDays: number
  lastActive: string
  // 新增字段
  weakDimension: string
  weakDimensionScore: number
  pendingTags: string[]
}

export interface StudentListResult {
  list: StudentListItem[]
  pagination: {
    total: number
    page: number
    page_size: number
  }
}

export interface StudentDetail {
  student: Record<string, any>
  dimensions: { name: string; score: number }[]
  examHistory: Record<string, any>[]
  weakPoints: string[]
  latestEvaluation: Record<string, any> | null
  // 新增
  totalPracticeCount: number
  totalErrorCount: number
  trendData: { date: string; accuracy: number; count: number }[]
}

export interface AnalyticsData {
  activeTrend: { date: string; count: number }[]
  dimensionAvg: { name: string; score: number }[]
  accuracyDistribution: { range: string; count: number }[]
}

export interface PendingCoachingStudent {
  id: number
  name: string
  email: string
  carType: string
  weakDimension: string
  accuracy: number
  lastActive: string
  daysSinceActive: number
  reason: string
}

// ======================== API 方法 ========================

/** 获取学情统计（含扩展指标） */
export function getStudentStats(): Promise<{ data: { code: number; data: StudentStats } }> {
  return get('/api/coach/student-stat') as any
}

/** 获取全局分析图表数据 */
export function getAnalytics(): Promise<{ data: { code: number; data: AnalyticsData } }> {
  return get('/api/coach/student-analytics') as any
}

/** 获取学员列表（支持筛选） */
export function getStudentList(params?: {
  page?: number
  page_size?: number
  keyword?: string
  car_type?: string
  accuracy_range?: string
  active_days?: number
  pending_only?: boolean
}): Promise<{ data: { code: number; data: StudentListResult } }> {
  return get('/api/coach/student-list', params as any) as any
}

/** 获取学员详情 */
export function getStudentDetail(id: number): Promise<{ data: { code: number; data: StudentDetail } }> {
  return get(`/api/coach/students/${id}`) as any
}

/** 获取待辅导学员列表 */
export function getPendingCoachingStudents(): Promise<{ data: { code: number; data: PendingCoachingStudent[] } }> {
  return get('/api/coach/pending-coaching') as any
}

/** 导出学员数据 */
export function exportStudents(params?: {
  keyword?: string
  car_type?: string
  accuracy_range?: string
  student_ids?: string
  export_fields?: string
  export_type?: string
}): Promise<any> {
  return request.get('/api/coach/export-student', {
    params,
    responseType: 'blob',
  })
}

/** 导出单个学员数据 */
export function exportSingleStudent(id: number): Promise<any> {
  return request.get(`/api/coach/export-student/${id}`, {
    responseType: 'blob',
  })
}
