// src/composables/useFullscreen.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useFullscreen(onForceSubmit?: () => void) {
  const isFullscreen = ref(false)
  const warningCount = ref(0)
  const showWarning = ref(false)
  const warningMessage = ref('')
  const MAX_WARNINGS = 3

  async function enterFullscreen() {
    try {
      await document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } catch {
      // 降级处理
    }
  }

  function exitFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    }
    isFullscreen.value = false
  }

  function handleFullscreenChange() {
    if (!document.fullscreenElement) {
      isFullscreen.value = false
      warningCount.value++
      if (warningCount.value >= MAX_WARNINGS) {
        showWarning.value = false
        onForceSubmit?.()
      } else {
        showWarning.value = true
        warningMessage.value = `警告！请不要切出全屏（${warningCount.value}/${MAX_WARNINGS}），再次切出将自动交卷！`
        setTimeout(() => { showWarning.value = false }, 3000)
      }
    } else {
      isFullscreen.value = true
    }
  }

  function handleVisibilityChange() {
    if (document.hidden && isFullscreen.value) {
      warningCount.value++
      if (warningCount.value >= MAX_WARNINGS) {
        onForceSubmit?.()
      } else {
        showWarning.value = true
        warningMessage.value = `检测到切屏行为（${warningCount.value}/${MAX_WARNINGS}），请立即返回！`
        setTimeout(() => { showWarning.value = false }, 3000)
      }
    }
  }

  function preventCheat(e: KeyboardEvent) {
    const blocked = ['F12', 'F5']
    const combos = e.ctrlKey && ['s', 'u', 'p'].includes(e.key)
    const shiftCombo = e.ctrlKey && e.shiftKey && e.key === 'I'
    if (blocked.includes(e.key) || combos || shiftCombo) {
      e.preventDefault()
    }
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    document.addEventListener('keydown', preventCheat)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    document.addEventListener('contextmenu', (e) => e.preventDefault())
  })

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    document.removeEventListener('keydown', preventCheat)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    document.removeEventListener('contextmenu', (e) => e.preventDefault())
  })

  return { isFullscreen, warningCount, showWarning, warningMessage, enterFullscreen, exitFullscreen }
}
