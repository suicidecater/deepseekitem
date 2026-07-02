<script setup lang="ts">
// src/views/student/ProgressView.vue - 学习进度可视化（全真实数据 + 方向切换）
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSWR } from '@/composables/useSWR'
import { get } from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 方向（从全局状态读取，首页唯一控制）
const currentDirection = ref<number>(authStore.studySubject)

interface DimItem { name: string; score: number }
interface TrendItem { date: string; questions: number; accuracy: number }
interface ModuleItem { name: string; type: string; done: number; target: number; route: string; color: string; icon: string }
interface HeatCell { date: string; minutes: number; level: number }

interface ProgressData {
  stats: {
    totalDays: number; totalQuestions: number; accuracy: number
    examCount: number; examBest: number; errorCount: number; aiChatCount: number
  }
  dimensions: DimItem[]
  weekTrend: TrendItem[]
  moduleProgress: ModuleItem[]
  heatmapCells: HeatCell[]
}

const { data: progressData, loading, fetch: fetchProgress, invalidate: invalidateProgress } = useSWR<ProgressData>(
  'student-progress',
  async () => {
    const res = await get<ProgressData>(`/api/student/progress?direction=${currentDirection.value}`)
    return res.data.data
  },
  60_000
)

// 监听首页方向切换 → 自动刷新
watch(() => authStore.studySubject, (newDir) => {
  if (newDir !== currentDirection.value) {
    currentDirection.value = newDir
    invalidateProgress()
    fetchProgress()
  }
})

// 环形进度参数
function circleParams(score: number) {
  const r = 28; const c = Math.PI * r * 2
  return { r, c, offset: c * (1 - score / 100) }
}
function dimColor(score: number) {
  return score >= 85 ? '#52C41A' : score >= 70 ? '#1677FF' : '#FF4D4F'
}

// 热力图颜色
function heatColor(level: number) {
  return ['#EBEDF0', '#C6E48B', '#7BC96F', '#239A3B', '#196127'][level] || '#EBEDF0'
}

// 模块百分比
function modulePercent(done: number, target: number) {
  return Math.min(100, Math.round((done / target) * 100))
}

// AI总览文本
const overviewText = computed(() => {
  const s = progressData.value?.stats
  if (!s) return ''
  const parts = []
  if (s.totalDays > 0) parts.push(`累计学习${s.totalDays}天`)
  if (s.totalQuestions > 0) parts.push(`完成${s.totalQuestions}道题`)
  if (s.accuracy > 0) parts.push(`正确率${s.accuracy}%`)
  if (s.examCount > 0) parts.push(`参加${s.examCount}次模考，最高${s.examBest}分`)
  if (!parts.length) return '开始你的第一次学习吧！'
  return '📊 ' + parts.join(' · ')
})

function goToModule(route: string) {
  router.push(route)
}

onMounted(() => { invalidateProgress(); fetchProgress() })
</script>

<template>
  <div class="progress-page">
    <div class="page-header">
      <h2>学习进度</h2>
      <p class="page-desc">真实数据追踪你的每一步成长</p>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>加载中...</p></div>

    <template v-else-if="progressData">
      <!-- 总览横幅 -->
      <div class="overview-banner">{{ overviewText }}</div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.totalDays }}</span><span class="stat-label">学习天数</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.totalQuestions }}</span><span class="stat-label">做题总数</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.accuracy }}%</span><span class="stat-label">正确率</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.examBest }}</span><span class="stat-label">模考最高分</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.errorCount }}</span><span class="stat-label">错题数</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.aiChatCount }}</span><span class="stat-label">AI问答</span></div>
      </div>

      <!-- 能力矩阵 + 本周趋势 -->
      <div class="two-col">
        <!-- 能力矩阵圆环 -->
        <div class="card">
          <h3>能力矩阵</h3>
          <div class="ability-grid">
            <div v-for="dim in progressData.dimensions" :key="dim.name" class="ability-item">
              <svg width="72" height="72" viewBox="0 0 72 72">
                <circle cx="36" cy="36" :r="circleParams(dim.score).r" fill="none" stroke="#F0F0F0" stroke-width="5" />
                <circle cx="36" cy="36" :r="circleParams(dim.score).r" fill="none" stroke-width="5"
                  :stroke="dimColor(dim.score)" :stroke-dasharray="circleParams(dim.score).c"
                  :stroke-dashoffset="circleParams(dim.score).offset"
                  stroke-linecap="round"
                  style="transform:rotate(-90deg);transform-origin:50% 50%;transition:stroke-dashoffset 1s ease" />
              </svg>
              <span class="dim-name">{{ dim.name }}</span>
              <span class="dim-score" :style="{ color: dimColor(dim.score) }">{{ dim.score }}分</span>
            </div>
          </div>
        </div>

        <!-- 本周趋势 -->
        <div class="card">
          <h3>本周学习趋势</h3>
          <div class="trend-chart">
            <div v-for="t in progressData.weekTrend" :key="t.date" class="trend-col">
              <div class="trend-bar-wrap">
                <div class="trend-bar" :style="{ height: t.questions * 5 + 'px', maxHeight: '80px', background: t.questions > 0 ? '#1677FF' : '#E8E8E8' }"></div>
              </div>
              <div class="trend-date">{{ t.date.slice(5) }}</div>
              <div class="trend-val">{{ t.questions }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 6大模块进度 -->
      <div class="card">
        <h3>功能模块进度</h3>
        <div class="module-list">
          <div v-for="m in progressData.moduleProgress" :key="m.type" class="module-row"
            @click="goToModule(m.route)" :style="{ '--m-color': m.color }">
            <span class="module-icon">{{ m.icon }}</span>
            <span class="module-name">{{ m.name }}</span>
            <div class="module-bar-bg">
              <div class="module-bar-fill" :style="{ width: modulePercent(m.done, m.target) + '%', background: m.color }"></div>
            </div>
            <span class="module-num">{{ m.done }}/{{ m.target }}</span>
            <span class="module-arrow">→</span>
          </div>
        </div>
      </div>

      <!-- 热力图 -->
      <div class="card">
        <h3>近12周学习热力图</h3>
        <div class="heatmap-grid">
          <div v-for="cell in progressData.heatmapCells" :key="cell.date"
            class="heat-cell" :style="{ background: heatColor(cell.level) }"
            :title="cell.date + ': ' + cell.minutes + 'min'"></div>
        </div>
        <div class="heat-legend">
          <span>少</span>
          <span v-for="l in 5" :key="l" class="lg-block" :style="{ background: heatColor(l - 1) }"></span>
          <span>多</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.progress-page { max-width: 1100px; margin: 0 auto; padding: 24px; }
.page-header { margin-bottom: 12px; }
.page-header h2 { font-size: var(--font-size-2xl); }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px; color: var(--color-text-tertiary); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 总览横幅 */
.overview-banner { display: flex; align-items: center; gap: 10px; padding: 14px 20px; background: linear-gradient(135deg, #E6F7FF, #F0F5FF); border: 1px solid #91CAFF; border-radius: var(--radius-lg); margin-bottom: 20px; font-size: 14px; color: #1D39C4; }

/* 统计卡片 */
.stats-row { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 20px; }
@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(3, 1fr); } }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 16px 10px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-num { display: block; font-size: 24px; font-weight: 700; color: var(--color-primary); }
.stat-label { font-size: 11px; color: var(--color-text-tertiary); margin-top: 4px; display: block; }

/* 双列 */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
@media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }
.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: 16px; }

/* 能力矩阵 */
.ability-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.ability-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dim-name { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; }
.dim-score { font-size: 15px; font-weight: 700; }

/* 本周趋势 */
.trend-chart { display: flex; align-items: flex-end; gap: 8px; height: 130px; padding: 0 4px; }
.trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.trend-bar-wrap { flex: 1; display: flex; align-items: flex-end; width: 100%; }
.trend-bar { width: 100%; border-radius: 3px 3px 0 0; min-height: 2px; transition: height 0.5s ease; }
.trend-date { font-size: 10px; color: var(--color-text-tertiary); }
.trend-val { font-size: 10px; font-weight: 600; color: var(--color-text-secondary); }

/* 模块进度 */
.module-list { display: flex; flex-direction: column; gap: 10px; }
.module-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: var(--radius-md); border: 1px solid var(--color-border-light); cursor: pointer; transition: all var(--transition-fast); }
.module-row:hover { border-color: var(--m-color); background: #FAFAFA; }
.module-icon { font-size: 18px; flex-shrink: 0; }
.module-name { width: 72px; font-size: 13px; font-weight: 500; flex-shrink: 0; }
.module-bar-bg { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.module-bar-fill { height: 100%; border-radius: 4px; transition: width 1s ease; }
.module-num { font-size: 11px; color: var(--color-text-tertiary); min-width: 52px; text-align: right; }
.module-arrow { font-size: 12px; color: var(--color-border); }

/* 热力图 */
.heatmap-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 4px; margin-bottom: 8px; }
.heat-cell { aspect-ratio: 1; border-radius: 3px; min-height: 28px; }
.heat-legend { display: flex; align-items: center; gap: 4px; justify-content: flex-end; font-size: 11px; color: var(--color-text-tertiary); }
.lg-block { width: 14px; height: 14px; border-radius: 2px; }
</style>
