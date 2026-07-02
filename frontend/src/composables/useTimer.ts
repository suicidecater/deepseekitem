// src/composables/useTimer.ts
import { ref, computed, onUnmounted } from 'vue'

export function useTimer(initialSeconds: number, onTimeout?: () => void) {
  const remaining = ref(initialSeconds)
  const isRunning = ref(false)
  const isWarning = ref(false)
  const warnAt = ref(300) // 5分钟默认
  let timer: ReturnType<typeof setInterval> | null = null

  const displayTime = computed(() => {
    const h = Math.floor(remaining.value / 3600)
    const m = Math.floor((remaining.value % 3600) / 60)
    const s = remaining.value % 60
    if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  })

  const progress = computed(() => ((initialSeconds - remaining.value) / initialSeconds) * 100)

  function start() {
    if (isRunning.value) return
    isRunning.value = true
    timer = setInterval(() => {
      remaining.value--
      if (remaining.value <= warnAt.value) {
        isWarning.value = true
      }
      if (remaining.value <= 0) {
        stop()
        onTimeout?.()
      }
    }, 1000)
  }

  function pause() {
    if (timer) { clearInterval(timer); timer = null }
    isRunning.value = false
  }

  function stop() {
    pause()
    remaining.value = 0
  }

  function reset(seconds?: number) {
    pause()
    remaining.value = seconds ?? initialSeconds
    isWarning.value = false
  }

  onUnmounted(() => pause())

  return { remaining, isRunning, isWarning, displayTime, progress, start, pause, stop, reset }
}
