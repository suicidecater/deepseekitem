// src/composables/useSWR.ts
import { ref } from 'vue'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

const cache = new Map<string, CacheEntry<any>>()

export function useSWR<T>(key: string, fetcher: () => Promise<T>, ttl = 30_000) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch() {
    // 检查缓存
    const cached = cache.get(key)
    if (cached && Date.now() - cached.timestamp < ttl) {
      data.value = cached.data
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await fetcher()
      data.value = result
      cache.set(key, { data: result, timestamp: Date.now() })
    } catch (e: any) {
      error.value = e.message || '请求失败'
    } finally {
      loading.value = false
    }
  }

  function invalidate() {
    cache.delete(key)
  }

  // 全局清缓存（如退出登录时）
  function clearAll() {
    cache.clear()
  }

  return { data, loading, error, fetch, invalidate, clearAll }
}
