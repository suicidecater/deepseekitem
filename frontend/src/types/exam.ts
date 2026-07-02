// src/types/exam.ts
export interface ExamQuestion {
  id: number
  type: 'single' | 'multiple' | 'judge'
  subject: 1 | 4 // 1=科目一, 4=科目四
  content: string
  options: string[]
  answer: string
  explanation: string
  category: string
  difficulty: number
  image?: string
}
