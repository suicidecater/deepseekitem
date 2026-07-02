// src/utils/constants.ts
export const STORAGE_KEYS = {
  TOKEN: 'traffic_token',
  USER: 'traffic_user',
  REMEMBER: 'traffic_remember'
} as const

export const DEFAULT_AVATAR = '/avatar-default.svg'

export const SUBJECT_MAP: Record<number, string> = {
  1: '科目一',
  4: '科目四'
}

export const ABILITY_DIMENSIONS = ['交通标志', '交通法规', '安全常识', '驾驶理论']

export const ROLES = {
  STUDENT: 'student',
  COACH: 'coach',
  ADMIN: 'admin'
} as const
