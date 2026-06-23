<script setup lang="ts">
// src/views/student/StudyPlanView.vue - AI学习路径规划页
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSWR } from '@/composables/useSWR'

const router = useRouter()

interface DailyTask {
  id: number
  title: string
  description: string
  timeSlot: 'morning' | 'afternoon' | 'evening'
  type: string
  completed: boolean
  knowledgePoint?: string
}

interface StudyDay {
  date: string
  dayOfWeek: string
  tasks: DailyTask[]
  isToday: boolean
}

interface StudyPlan {
  weekStart: string
  weekEnd: string
  days: StudyDay[]
  totalTasks: number
  completedTasks: number
}

const { data: planData, loading, fetch: fetchPlan } = useSWR<StudyPlan>(
  'study-plan',
  async () => {
    const res = await fetch('/api/student/study-plan')
    const json = await res.json()
    if (json.code !== 0) throw new Error(json.message)
    return json.data
  },
  60_000
)

const todayDay = computed(() => planData.value?.days.find(d => d.isToday))

const timeSlotLabels: Record<string, string> = {
  morning: '上午', afternoon: '下午', evening: '晚上'
}

function toggleTask(dayIdx: number, taskId: number) {
  if (!planData.value) return
  const day = planData.value.days[dayIdx]
  const task = day.tasks.find(t => t.id === taskId)
  if (task) {
    task.completed = !task.completed
    planData.value.completedTasks = planData.value.days.reduce((sum, d) =>
      sum + d.tasks.filter(t => t.completed).length, 0)
  }
}

function goToPractice(knowledgePoint?: string) {
  const query = knowledgePoint ? `?category=${encodeURIComponent(knowledgePoint)}` : ''
  router.push(`/student/practice${query}`)
}

onMounted(async () => {
  await fetchPlan()
})
</script>

<template>
  <div class="study-plan-page">
    <div class="page-header">
      <h2>AI学习路径规划</h2>
      <p class="page-desc">基于你的能力测评结果，AI为你生成了个性化学习计划</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div><p>加载学习计划...</p>
    </div>

    <template v-else-if="planData">
      <!-- 进度概览 -->
      <div class="plan-overview">
        <div class="overview-card">
          <span class="overview-value">{{ planData.completedTasks }}</span>
          <span class="overview-label">已完成</span>
        </div>
        <div class="overview-card">
          <span class="overview-value">{{ planData.totalTasks - planData.completedTasks }}</span>
          <span class="overview-label">待完成</span>
        </div>
        <div class="overview-card">
          <span class="overview-value">{{ planData.totalTasks }}</span>
          <span class="overview-label">总任务</span>
        </div>
      </div>

      <!-- 本周学习计划 -->
      <div class="week-plan">
        <h3 class="week-title">
          本周计划 ({{ planData.weekStart }} ~ {{ planData.weekEnd }})
        </h3>

        <div class="days-grid">
          <div
            v-for="(day, dayIdx) in planData.days"
            :key="day.date"
            class="day-card"
            :class="{ today: day.isToday }"
          >
            <div class="day-header">
              <span class="day-name">{{ day.dayOfWeek }}</span>
              <span class="day-date">{{ day.date }}</span>
              <span v-if="day.isToday" class="today-badge">今天</span>
            </div>

            <div class="day-tasks">
              <div
                v-for="task in day.tasks"
                :key="task.id"
                class="task-row"
              >
                <div class="task-left">
                  <button
                    class="task-check"
                    :class="{ done: task.completed }"
                    @click="toggleTask(dayIdx, task.id)"
                  >
                    {{ task.completed ? '✓' : '○' }}
                  </button>
                  <div class="task-info">
                    <span class="task-title">{{ task.title }}</span>
                    <span class="task-time">{{ timeSlotLabels[task.timeSlot] }}</span>
                  </div>
                </div>
                <button
                  v-if="task.knowledgePoint"
                  class="btn btn-outline btn-sm"
                  @click="goToPractice(task.knowledgePoint)"
                >练习</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.study-plan-page { max-width: 1200px; margin: 0 auto; padding: 24px; }

.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 40vh; gap: 16px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.plan-overview { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.overview-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.overview-value { display: block; font-size: 32px; font-weight: 700; color: var(--color-primary); }
.overview-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.week-title { font-size: var(--font-size-lg); margin-bottom: 16px; }

.days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; }

@media (max-width: 1400px) { .days-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 900px) { .days-grid { grid-template-columns: repeat(2, 1fr); } }

.day-card {
  background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light);
  padding: 14px; transition: all var(--transition-fast);
}
.day-card.today { border-color: var(--color-primary); box-shadow: 0 0 0 2px var(--color-primary-light); }

.day-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--color-border-light); }
.day-name { font-size: var(--font-size-base); font-weight: 600; }
.day-date { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.today-badge { font-size: 10px; background: var(--color-primary); color: #fff; padding: 1px 6px; border-radius: var(--radius-sm); margin-left: auto; }

.day-tasks { display: flex; flex-direction: column; gap: 8px; }

.task-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.task-left { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }

.task-check {
  width: 22px; height: 22px; border-radius: 50%; border: 2px solid var(--color-border);
  display: flex; align-items: center; justify-content: center; font-size: 12px; cursor: pointer;
  flex-shrink: 0; transition: all var(--transition-fast);
}
.task-check.done { background: var(--color-success); border-color: var(--color-success); color: #fff; }

.task-info { min-width: 0; }
.task-title { display: block; font-size: var(--font-size-xs); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.task-time { font-size: 10px; color: var(--color-text-tertiary); }

.btn-sm { padding: 2px 8px; font-size: 10px; }
</style>
