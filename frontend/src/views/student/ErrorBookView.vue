<script setup lang="ts">
// src/views/student/ErrorBookView.vue - 智能错题本
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

interface ErrorItem {
  id: number
  questionContent: string
  subject: 1 | 4
  errorType: string
  errorCount: number
  lastErrorTime: string
  status: 'review' | 'reviewed' | 'mastered'
  correctAnswer: string
  myAnswer: string
}

const errorList = ref<ErrorItem[]>([])
const filterSubject = ref<number>(0)
const filterStatus = ref<string>('')
const filterErrorType = ref<string>('')

const stats = computed(() => ({
  total: errorList.value.length,
  toReview: errorList.value.filter(e => e.status === 'review').length,
  reviewed: errorList.value.filter(e => e.status === 'reviewed').length,
  mastered: errorList.value.filter(e => e.status === 'mastered').length
}))

const filteredList = computed(() => {
  return errorList.value.filter(e => {
    if (filterSubject.value && e.subject !== filterSubject.value) return false
    if (filterStatus.value && e.status !== filterStatus.value) return false
    if (filterErrorType.value && e.errorType !== filterErrorType.value) return false
    return true
  })
})

function loadErrorBook() {
  // Mock 数据
  errorList.value = [
    { id: 1, questionContent: '在高速公路上遇到紧急情况时，以下做法正确的是？', subject: 1, errorType: '概念不清', errorCount: 3, lastErrorTime: '2026-06-01 14:30', status: 'review', correctAnswer: 'C', myAnswer: 'A' },
    { id: 2, questionContent: '夜间会车应当在距对方来车多少米以外改用近光灯？', subject: 1, errorType: '审题失误', errorCount: 1, lastErrorTime: '2026-05-30 10:15', status: 'reviewed', correctAnswer: 'C', myAnswer: 'B' },
    { id: 3, questionContent: '在冰雪路面上行车时，应降低车速，增大安全距离。', subject: 4, errorType: '概念不清', errorCount: 2, lastErrorTime: '2026-05-28 16:00', status: 'review', correctAnswer: 'A', myAnswer: 'B' },
    { id: 4, questionContent: '驾驶人进入驾驶室前，首先应做什么？', subject: 4, errorType: '混淆记忆', errorCount: 4, lastErrorTime: '2026-06-01 09:00', status: 'review', correctAnswer: 'A', myAnswer: 'D' },
    { id: 5, questionContent: '这个标志表示什么含义？', subject: 1, errorType: '概念不清', errorCount: 5, lastErrorTime: '2026-05-25 11:20', status: 'mastered', correctAnswer: 'B', myAnswer: 'C' },
  ]
}

function redoErrors() {
  router.push('/student/practice?mode=error-book')
}

function removeItem(id: number) {
  errorList.value = errorList.value.filter(e => e.id !== id)
}

function markMastered(id: number) {
  const item = errorList.value.find(e => e.id === id)
  if (item) item.status = 'mastered'
}

const statusLabels: Record<string, string> = { review: '待复习', reviewed: '已复习', mastered: '已掌握' }
const statusColors: Record<string, string> = { review: 'tag-orange', reviewed: 'tag-blue', mastered: 'tag-green' }

onMounted(loadErrorBook)
</script>

<template>
  <div class="error-book-page">
    <div class="page-header">
      <h2>智能错题本</h2>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card"><span class="stat-num">{{ stats.total }}</span><span class="stat-label">总错题</span></div>
      <div class="stat-card warn"><span class="stat-num">{{ stats.toReview }}</span><span class="stat-label">待复习</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.reviewed }}</span><span class="stat-label">已复习</span></div>
      <div class="stat-card success"><span class="stat-num">{{ stats.mastered }}</span><span class="stat-label">已掌握</span></div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <select v-model="filterSubject" class="filter-select">
        <option :value="0">全部科目</option>
        <option :value="1">科目一</option>
        <option :value="4">科目四</option>
      </select>
      <select v-model="filterErrorType" class="filter-select">
        <option value="">全部错因</option>
        <option value="概念不清">概念不清</option>
        <option value="审题失误">审题失误</option>
        <option value="混淆记忆">混淆记忆</option>
      </select>
      <select v-model="filterStatus" class="filter-select">
        <option value="">全部状态</option>
        <option value="review">待复习</option>
        <option value="reviewed">已复习</option>
        <option value="mastered">已掌握</option>
      </select>
      <button class="btn btn-primary" @click="redoErrors">重做错题</button>
    </div>

    <!-- 错题列表 -->
    <div class="error-list">
      <div v-if="filteredList.length === 0" class="empty-state">暂无错题记录</div>
      <div v-for="item in filteredList" :key="item.id" class="error-item card">
        <div class="error-main">
          <div class="error-header">
            <span class="tag" :class="item.subject === 1 ? 'tag-blue' : 'tag-green'">科目{{ item.subject === 1 ? '一' : '四' }}</span>
            <span class="tag tag-orange">{{ item.errorType }}</span>
            <span class="tag" :class="statusColors[item.status]">{{ statusLabels[item.status] }}</span>
          </div>
          <p class="error-question">{{ item.questionContent }}</p>
          <div class="error-meta">
            <span>错误 {{ item.errorCount }} 次</span>
            <span>最后错误：{{ item.lastErrorTime }}</span>
          </div>
        </div>
        <div class="error-actions">
          <button class="btn btn-outline btn-sm" @click="markMastered(item.id)">标记已掌握</button>
          <button class="btn btn-outline btn-sm" @click="removeItem(item.id)">移除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-book-page { max-width: 1000px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-card.warn { border-color: var(--color-warning); background: #FFFBE6; }
.stat-card.success { border-color: var(--color-success); background: #F6FFED; }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-card.warn .stat-num { color: var(--color-warning); }
.stat-card.success .stat-num { color: var(--color-success); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-select { padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: var(--font-size-sm); background: #fff; }

.empty-state { text-align: center; padding: 60px 0; color: var(--color-text-tertiary); }

.error-list { display: flex; flex-direction: column; gap: 12px; }
.error-item { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.error-main { flex: 1; }
.error-header { display: flex; gap: 8px; margin-bottom: 8px; }
.error-question { font-size: var(--font-size-sm); margin-bottom: 6px; line-height: 1.5; }
.error-meta { display: flex; gap: 16px; font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.error-actions { display: flex; gap: 8px; flex-shrink: 0; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 16px 20px; border: 1px solid var(--color-border-light); }
.btn-sm { padding: 4px 12px; font-size: var(--font-size-xs); }
</style>
