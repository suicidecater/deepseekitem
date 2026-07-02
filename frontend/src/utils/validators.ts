// src/utils/validators.ts
export const emailRules = [
  {
    validator: (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
    message: '请输入正确的邮箱格式'
  }
]

export const phoneRules = [
  {
    validator: (v: string) => /^1[3-9]\d{9}$/.test(v),
    message: '请输入正确的手机号'
  }
]

export const passwordRules = [
  {
    validator: (v: string) => v.length >= 6,
    message: '密码至少6位'
  },
  {
    validator: (v: string) => v.length <= 20,
    message: '密码不超过20位'
  }
]

export const nameRules = [
  {
    validator: (v: string) => v.trim().length >= 2,
    message: '姓名至少2个字符'
  },
  {
    validator: (v: string) => v.trim().length <= 20,
    message: '姓名不超过20个字符'
  }
]

export const requiredRule = (label: string) => [
  {
    validator: (v: string) => v.trim().length > 0,
    message: `请输入${label}`
  }
]
