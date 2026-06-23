<script setup lang="ts">
// src/views/student/SprintView.vue - 考前冲刺与押题
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const daysUntilExam = ref(10)
const highFreqPoints = ref([
  { name: '交通标志识别', errorRate: 68, count: 45 },
  { name: '交警手势信号', errorRate: 62, count: 38 },
  { name: '高速限速规定', errorRate: 59, count: 32 },
  { name: '扣分罚款标准', errorRate: 55, count: 40 },
  { name: '优先通行规则', errorRate: 52, count: 28 },
  { name: '灯光使用规范', errorRate: 48, count: 25 },
  { name: '安全距离判断', errorRate: 45, count: 30 },
  { name: '恶劣天气驾驶', errorRate: 42, count: 22 },
  { name: '紧急情况处理', errorRate: 40, count: 35 },
  { name: '超车变道规则', errorRate: 38, count: 20 }
])

const mockExams = ref([
  { id: 1, name: '押题卷 A', desc: '高频考点覆盖，命中率85%+', difficulty: 3, questionCount: 100 },
  { id: 2, name: '押题卷 B', desc: '近3月新增考点精编', difficulty: 2, questionCount: 100 },
  { id: 3, name: '押题卷 C', desc: '易错题专项整合', difficulty: 3, questionCount: 100 }
])

const todayTasks = ref([
  { title: '完成押题卷A', completed: false },
  { title: '复习高频考点 Top5', completed: false },
  { title: '错题本重做', completed: true }
])

function startSprintExam(examId: number) {
  router.push(`/student/exam?mode=sprint&examId=${examId}`)
}

onMounted(() => {
  // Mock 数据
})
</script>

<template>
  <div class="sprint-page">
    <div class="page-header">
      <h2>🔥 考前冲刺</h2>
    </div>

    <!-- 倒计时 -->
    <div class="countdown-banner">
      <div class="countdown-content">
        <span class="countdown-icon">⏰</span>
        <div>
          <p class="countdown-days">距考试还有 <strong>{{ daysUntilExam }}</strong> 天</p>
          <p class="countdown-hint">抓住最后时间，精准提分！</p>
        </div>
      </div>
    </div>

    <div class="sprint-grid">
      <!-- 今日任务 -->
      <div class="card">
        <h3>今日冲刺任务</h3>
        <div class="task-list">
          <div v-for="task in todayTasks" :key="task.title" class="task-row" :class="{ done: task.completed }">
            <span>{{ task.completed ? '✅' : '⬜' }}</span>
            <span>{{ task.title }}</span>
          </div>
        </div>
      </div>

      <!-- 押题卷 -->
      <div class="card">
        <h3>高概率押题卷</h3>
        <div class="exam-cards">
          <div v-for="exam in mockExams" :key="exam.id" class="exam-card" @click="startSprintExam(exam.id)">
            <div class="exam-name">{{ exam.name }}</div>
            <p class="exam-desc">{{ exam.desc }}</p>
            <div class="exam-meta">
              <span>{{ exam.questionCount }}题</span>
              <span>{{ '⭐'.repeat(exam.difficulty) }}</span>
            </div>
            <button class="btn btn-primary btn-block btn-sm">开始考试</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 高频考点 -->
    <div class="card high-freq-card">
      <h3>高频考点 Top 10（按错误率排序）</h3>
      <div class="freq-list">
        <div v-for="(point, idx) in highFreqPoints" :key="point.name" class="freq-item">
          <span class="freq-rank">{{ idx + 1 }}</span>
          <div class="freq-info">
            <span class="freq-name">{{ point.name }}</span>
            <span class="freq-count">{{ point.count }}题</span>
          </div>
          <div class="freq-bar">
            <div class="freq-fill" :style="{ width: point.errorRate + '%' }"></div>
          </div>
          <span class="freq-rate">{{ point.errorRate }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sprint-page { max-width: 1000px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.countdown-banner {
  background: linear-gradient(135deg, #FFF7E6, #FFF1CC);
  border-radius: var(--radius-xl); padding: 24px 32px; margin-bottom: 24px;
  border: 1px solid #FFD666;
}
.countdown-content { display: flex; align-items: center; gap: 16px; }
.countdown-icon { font-size: 48px; }
.countdown-days { font-size: var(--font-size-xl); font-weight: 500; }
.countdown-days strong { font-size: 36px; color: var(--color-warning); }
.countdown-hint { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-top: 4px; }

.sprint-grid { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-bottom: 24px; }
@media (max-width: 768px) { .sprint-grid { grid-template-columns: 1fr; } }

.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }

.task-list { display: flex; flex-direction: column; gap: 10px; }
.task-row { display: flex; align-items: center; gap: 8px; font-size: var(--font-size-sm); }
.task-row.done { opacity: 0.5; text-decoration: line-through; }

.exam-cards { display: flex; flex-direction: column; gap: 12px; }
.exam-card {
  padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--color-border);
  cursor: pointer; transition: all var(--transition-fast);
}
.exam-card:hover { border-color: var(--color-primary); box-shadow: var(--shadow-sm); }
.exam-name { font-size: var(--font-size-base); font-weight: 600; margin-bottom: 4px; }
.exam-desc { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-bottom: 8px; }
.exam-meta { display: flex; gap: 12px; font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: 10px; }
.btn-sm { padding: 6px 0; font-size: var(--font-size-xs); }

.high-freq-card { margin-bottom: 24px; }
.freq-list { display: flex; flex-direction: column; gap: 10px; }
.freq-item { display: flex; align-items: center; gap: 12px; }
.freq-rank {
  width: 24px; height: 24px; border-radius: 50%; background: var(--color-primary-light);
  color: var(--color-primary); display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.freq-info { width: 140px; }
.freq-name { display: block; font-size: var(--font-size-sm); }
.freq-count { font-size: 11px; color: var(--color-text-tertiary); }
.freq-bar { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.freq-fill { height: 100%; background: var(--color-error); border-radius: 4px; }
.freq-rate { width: 40px; font-size: var(--font-size-xs); font-weight: 600; color: var(--color-error); }
</style>
