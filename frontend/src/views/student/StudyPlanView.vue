<script setup lang="ts">
// src/views/student/StudyPlanView.vue - AI学习路径规划页（多方向+真实功能映射+能力仪表盘）
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSWR } from '@/composables/useSWR'
import { get, post } from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 学习方向（从全局状态读取，首页唯一控制）
const currentDirection = ref<number>(authStore.studySubject)

// 任务类型 → 路由映射
const taskTypeMap: Record<string, { route: string; label: string }> = {
  practice:         { route: '/student/practice',          label: '智能题库' },
  exam:             { route: '/student/exam',               label: '模拟考试' },
  ai_qa:            { route: '/student/ai-qa',              label: 'AI问答' },
  error_book:       { route: '/student/error-book',         label: '错题本' },
  special_training: { route: '/student/special-training',   label: '专项训练' },
  scene_sim:        { route: '/student/scene-sim',          label: '场景模拟' },
}

interface DailyTask {
  id?: number; title: string; description?: string
  timeSlot: 'morning' | 'afternoon' | 'evening'
  type: string; completed: boolean
  knowledgePoint?: string; estimatedMinutes?: number
}

interface StudyDay {
  day: number; date: string; tasks: DailyTask[]
}

interface EvalSummary {
  hasEvaluation: boolean; subjectName?: string; studySubject?: number
  level?: string; overallScore?: number
  dimensions?: Record<string, number>
  dimensionsSorted?: { name: string; score: number; potentialGain: number }[]
  weakPoints?: { name: string; rate: number; potentialGain?: number }[]
  aiAdvice?: string
}

interface StudyPlanData {
  evaluationSummary: EvalSummary
  plan: StudyDay[] | null
  cached: boolean
  generatedAt: string | null
}

const planCacheKey = computed(() => `study-plan-${currentDirection.value}`)

const { data: planData, loading, fetch: fetchPlan, invalidate: invalidatePlan } = useSWR<StudyPlanData>(
  planCacheKey.value,
  async () => {
    const res = await get<StudyPlanData>(`/api/student/study-plan?direction=${currentDirection.value}`)
    return res.data.data
  },
  60_000
)

// 生成状态
const generating = ref(false)
const generateMsg = ref('')

// 计划天数据
const days = computed(() => planData.value?.plan || [])
const evalSummary = computed(() => planData.value?.evaluationSummary)

const weekStart = computed(() => days.value[0]?.date || '--')
const weekEnd = computed(() => days.value[days.value.length - 1]?.date || '--')
const totalTasks = computed(() => days.value.reduce((s, d) => s + (d.tasks?.length || 0), 0))

const timeSlotLabels: Record<string, string> = { morning: '上午', afternoon: '下午', evening: '晚上' }
const today = new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })

// 等级颜色
const levelColor: Record<string, string> = { '冲刺': '#52C41A', '进阶': '#1677FF', '基础': '#FAAD14', '入门': '#FF4D4F' }

// 薄弱点等级 (A: 等级标签化)
function weakLevel(rate: number) {
  if (rate < 40) return { emoji: '🔴', label: '急需抢救', color: '#FF4D4F', bg: '#FFF1F0' }
  if (rate < 70) return { emoji: '🟡', label: '重点关注', color: '#FAAD14', bg: '#FFFBE6' }
  return { emoji: '🟢', label: '保持优势', color: '#52C41A', bg: '#F6FFED' }
}

// 维度进度圆环参数 (B: 能力矩阵)
function circleParams(score: number) {
  const r = 28; const c = Math.PI * r * 2
  const offset = c * (1 - score / 100)
  return { r, c, offset }
}

// 监听首页方向切换 → 自动刷新
watch(() => authStore.studySubject, (newDir) => {
  if (newDir !== currentDirection.value) {
    currentDirection.value = newDir
    invalidatePlan()
    fetchPlan()
  }
})

// 生成学习路径
async function handleGenerate() {
  generating.value = true
  generateMsg.value = ''
  try {
    const res = await post('/api/student/study-plan/generate', { study_subject: currentDirection.value })
    const json = res.data
    if (json.code === 0) {
      generateMsg.value = 'AI学习路径已生成！'
      await fetchPlan()
    } else {
      generateMsg.value = json.message || '生成失败'
    }
  } catch {
    generateMsg.value = '网络异常，请重试'
  } finally {
    generating.value = false
  }
}

// 根据任务类型跳转到对应功能页
function goToTask(type: string) {
  const target = taskTypeMap[type]
  if (target) {
    router.push(target.route)
  } else {
    router.push('/student/practice')
  }
}

// 任务类型中文标签
function taskTypeLabel(type: string): string {
  return taskTypeMap[type]?.label || type
}

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const dirParam = params.get('direction')
  if (dirParam) {
    const d = parseInt(dirParam)
    if ([1, 4, 5].includes(d)) currentDirection.value = d
  }
  invalidatePlan()
  await fetchPlan()
})
</script>

<template>
  <div class="study-plan-page">
    <div class="page-header">
      <h2>AI学习路径规划</h2>
      <p class="page-desc">基于你的能力测评结果，AI为你生成了个性化学习计划</p>
    </div>

    <!-- 操作区 -->
    <div class="header-actions">
      <button
        class="btn btn-primary"
        :disabled="generating"
        @click="handleGenerate"
      >
        {{ generating ? '⏳ 生成中...' : '🔄 重新生成' }}
      </button>
    </div>

    <!-- C: AI一句话诊断横幅 -->
    <div v-if="evalSummary?.aiAdvice" class="ai-advice-banner">
      <span class="advice-icon">💡</span>
      <span class="advice-text">{{ evalSummary.aiAdvice }}</span>
    </div>

    <!-- B: 能力矩阵 + A/D/E: 薄弱点分析 -->
    <div v-if="evalSummary?.hasEvaluation" class="ability-dashboard">
      <!-- 左侧：四维能力矩阵 (B) -->
      <div class="ability-grid">
        <div
          v-for="dim in evalSummary.dimensionsSorted || []"
          :key="dim.name"
          class="ability-card"
          :class="{ weak: dim.score < 70, strong: dim.score >= 85 }"
        >
          <svg class="progress-ring" width="72" height="72" viewBox="0 0 72 72">
            <circle class="ring-bg" cx="36" cy="36" :r="circleParams(dim.score).r"
              fill="none" stroke-width="5" />
            <circle class="ring-fill" cx="36" cy="36" :r="circleParams(dim.score).r"
              fill="none" stroke-width="5"
              :stroke="dim.score >= 85 ? '#52C41A' : dim.score >= 70 ? '#1677FF' : '#FF4D4F'"
              :stroke-dasharray="circleParams(dim.score).c"
              :stroke-dashoffset="circleParams(dim.score).offset"
              stroke-linecap="round" />
          </svg>
          <span class="dim-name">{{ dim.name }}</span>
          <span class="dim-score">{{ dim.score }}分</span>
        </div>
      </div>

      <!-- 右侧：薄弱点分析面板 (A + D + E) -->
      <div class="weak-panel">
        <div class="panel-title">📋 薄弱点分析</div>

        <!-- D: 建议学习顺序 -->
        <div v-if="evalSummary.dimensionsSorted?.length" class="study-order">
          <span class="order-label">建议学习顺序：</span>
          <span class="order-flow">
            <template v-for="(dim, idx) in evalSummary.dimensionsSorted" :key="dim.name">
              <span class="order-step" :class="{ first: idx === 0 }">{{ dim.name }}</span>
              <span v-if="idx < (evalSummary.dimensionsSorted?.length || 0) - 1" class="order-arrow">→</span>
            </template>
          </span>
        </div>

        <!-- A: 等级标签 + E: 进步空间 -->
        <div v-if="evalSummary.weakPoints?.length" class="weak-list">
          <div
            v-for="w in evalSummary.weakPoints"
            :key="w.name"
            class="weak-item"
            :style="{ '--level-color': weakLevel(w.rate).color, '--level-bg': weakLevel(w.rate).bg }"
          >
            <div class="weak-top">
              <span class="weak-level-tag">{{ weakLevel(w.rate).emoji }} {{ weakLevel(w.rate).label }}</span>
              <span class="weak-name">{{ w.name }}</span>
            </div>
            <div class="weak-bottom">
              <div class="weak-bar-bg">
                <div class="weak-bar-fill" :style="{ width: w.rate + '%', background: weakLevel(w.rate).color }"></div>
              </div>
              <span class="weak-rate">{{ w.rate }}%</span>
              <!-- E: 进步空间 -->
              <span v-if="w.potentialGain && w.potentialGain > 0" class="potential-gain">提升潜力 +{{ w.potentialGain }}分</span>
            </div>
          </div>
        </div>
        <div v-else class="weak-empty">暂无薄弱项，各维度表现良好 🎉</div>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>加载学习计划...</p></div>

    <!-- 无计划 -->
    <div v-else-if="!days.length && !generating" class="empty-state">
      <div class="empty-icon">🧭</div>
      <h3>尚未生成学习路径</h3>
      <p v-if="!evalSummary?.hasEvaluation">请先完成{{ {1:'科目一',4:'科目四',5:'专业人员'}[currentDirection] || '' }}能力测评，系统将自动为你生成个性化学习计划</p>
      <p v-else>点击上方"生成学习路径"按钮，AI将根据你的测评结果定制7天计划</p>
      <p v-if="generateMsg" class="gen-msg">{{ generateMsg }}</p>
    </div>

    <template v-else-if="days.length">
      <!-- 周概览 -->
      <div class="plan-overview">
        <div class="overview-card">
          <span class="overview-value">7</span><span class="overview-label">天计划</span>
        </div>
        <div class="overview-card">
          <span class="overview-value">{{ totalTasks }}</span><span class="overview-label">总任务</span>
        </div>
      </div>

      <p v-if="generateMsg" class="gen-msg">{{ generateMsg }}</p>

      <!-- 7天计划 -->
      <h3 class="week-title">本周计划 ({{ weekStart }} ~ {{ weekEnd }})</h3>
      <div class="days-grid">
        <div v-for="(day, dayIdx) in days" :key="day.date" class="day-card" :class="{ today: day.date === today }">
          <div class="day-header">
            <span class="day-num">第{{ day.day }}天</span>
            <span class="day-date">{{ day.date }}</span>
            <span v-if="day.date === today" class="today-badge">今天</span>
          </div>
          <div class="day-tasks">
            <div v-for="task in (day.tasks || [])" :key="task.title + dayIdx" class="task-row">
              <div class="task-left">
                <span class="task-dot" :class="task.type"></span>
                <div class="task-info">
                  <span class="task-title">{{ task.title }}</span>
                  <span class="task-meta">
                    <span class="task-type-tag">{{ taskTypeLabel(task.type) }}</span>
                    {{ timeSlotLabels[task.timeSlot] || '' }}
                    <template v-if="task.estimatedMinutes"> · {{ task.estimatedMinutes }}分钟</template>
                  </span>
                </div>
              </div>
              <button
                class="btn btn-outline btn-sm"
                @click="goToTask(task.type)"
              >去学习</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.study-plan-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header { margin-bottom: 12px; }
.page-header h2 { font-size: var(--font-size-2xl); }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.header-actions { margin-bottom: 16px; }

/* C: AI诊断横幅 */
.ai-advice-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #E6F7FF, #F0F5FF);
  border: 1px solid #91CAFF;
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
}
.advice-icon { font-size: 20px; flex-shrink: 0; }
.advice-text { font-size: 14px; color: #1D39C4; line-height: 1.5; }

/* B: 能力仪表盘 = 能力矩阵 + 薄弱分析 */
.ability-dashboard {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
@media (max-width: 900px) { .ability-dashboard { grid-template-columns: 1fr; } }

/* B: 四维能力矩阵 */
.ability-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.ability-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: var(--radius-lg);
  background: #fff;
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-fast);
}
.ability-card.weak { border-color: #FFD8D8; background: #FFFBFB; }
.ability-card.strong { border-color: #B7EB8F; background: #FBFFF9; }
.dim-name { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; }
.dim-score { font-size: 16px; font-weight: 700; color: var(--color-text-primary); }

/* SVG 环形进度 */
.progress-ring { display: block; }
.ring-bg { stroke: #F0F0F0; }
.ring-fill { transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s ease; }

/* 薄弱分析面板 (A + D + E) */
.weak-panel {
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
}
.panel-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; }

/* D: 建议学习顺序 */
.study-order {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #FAFAFA;
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.order-label { font-size: 12px; color: var(--color-text-tertiary); white-space: nowrap; }
.order-flow { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.order-step {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-border-light);
}
.order-step.first { background: var(--color-primary); color: #fff; }
.order-arrow { font-size: 11px; color: var(--color-text-tertiary); }

/* A/E: 薄弱列表 */
.weak-list { display: flex; flex-direction: column; gap: 8px; }
.weak-item {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--level-bg);
  border: 1px solid var(--level-color);
  opacity: 0.95;
}
.weak-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.weak-level-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--level-color);
  color: #fff;
  font-weight: 500;
  white-space: nowrap;
}
.weak-name { font-size: 13px; font-weight: 500; }
.weak-bottom { display: flex; align-items: center; gap: 8px; }
.weak-bar-bg {
  flex: 1;
  height: 6px;
  background: #F0F0F0;
  border-radius: 3px;
  overflow: hidden;
}
.weak-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.weak-rate {
  font-size: 12px;
  font-weight: 600;
  color: var(--level-color);
  min-width: 32px;
}
/* E: 进步空间 */
.potential-gain {
  font-size: 11px;
  color: #1677FF;
  font-weight: 500;
  white-space: nowrap;
}
.weak-empty { text-align: center; padding: 20px; font-size: 13px; color: var(--color-text-tertiary); }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px; color: var(--color-text-tertiary); gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { font-size: 20px; margin-bottom: 8px; }
.empty-state p { color: var(--color-text-tertiary); }
.gen-msg { text-align: center; color: var(--color-primary); font-size: 14px; margin-top: 12px; }

.plan-overview { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.overview-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.overview-value { display: block; font-size: 32px; font-weight: 700; color: var(--color-primary); }
.overview-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.week-title { font-size: var(--font-size-lg); margin-bottom: 16px; }
.days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; }
@media (max-width: 1400px) { .days-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 900px) { .days-grid { grid-template-columns: repeat(2, 1fr); } }

.day-card { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); padding: 14px; transition: all var(--transition-fast); }
.day-card.today { border-color: var(--color-primary); box-shadow: 0 0 0 2px var(--color-primary-light); }
.day-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--color-border-light); }
.day-num { font-size: var(--font-size-base); font-weight: 600; }
.day-date { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.today-badge { font-size: 10px; background: var(--color-primary); color: #fff; padding: 1px 6px; border-radius: var(--radius-sm); margin-left: auto; }
.day-tasks { display: flex; flex-direction: column; gap: 10px; }
.task-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.task-left { display: flex; align-items: flex-start; gap: 8px; flex: 1; min-width: 0; }

/* 6种任务类型颜色 */
.task-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; background: var(--color-border); }
.task-dot.practice         { background: #1677FF; }
.task-dot.exam             { background: #FA8C16; }
.task-dot.ai_qa            { background: #722ED1; }
.task-dot.error_book       { background: #FF4D4F; }
.task-dot.special_training { background: #13C2C2; }
.task-dot.scene_sim        { background: #52C41A; }
/* 兼容旧 type */
.task-dot.review           { background: #722ED1; }
.task-dot.lesson           { background: #52C41A; }

.task-info { min-width: 0; }
.task-title { display: block; font-size: 12px; line-height: 1.4; }
.task-meta { font-size: 10px; color: var(--color-text-tertiary); display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.task-type-tag {
  display: inline-block;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 500;
  background: #F0F0F0;
  color: var(--color-text-secondary);
}
.btn-sm { padding: 2px 8px; font-size: 10px; white-space: nowrap; }
</style>
