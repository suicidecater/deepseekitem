/**
 * src/api/modules/ai.ts
 * AI 相关 API
 */
import { get, post } from '@/api/request'
import type { ChatMessage } from '@/types/ai'

// ======================== 请求/响应类型 ========================

export interface ChatStreamParams {
  question: string
  history?: ChatMessage[]
}

export interface GenerateSceneResult {
  scene: {
    title: string
    description: string
    image: string
  }
  question: {
    content: string
    options: string[]
    answer: string
  }
}

// ======================== API 方法 ========================

/**
 * AI 问答（非流式，兼容旧版）
 * 流式版本请使用 useSSE composable
 */
export function chatSync(params: ChatStreamParams) {
  return post<{
    reply: string
    structured?: {
      knowledgePoint?: string
      lawRef?: string
      caseStudy?: string
    }
  }>('/api/ai/chat/stream', params)
}

/** 生成场景题 */
export function generateScene(params?: { subject?: number }) {
  return post<GenerateSceneResult>('/api/ai/generate-scene', params)
}
