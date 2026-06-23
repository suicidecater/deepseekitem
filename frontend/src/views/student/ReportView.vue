<script setup lang="ts">
// src/views/student/ReportView.vue - 学习效果评估报告
import { ref, onMounted } from 'vue'
import { useSWR } from '@/composables/useSWR'

interface ReportData {
  growthCurve: { date: string; scores: number[] }[]
  knowledgeMatrix: { name: string; dimensions: { name: string; score: number }[] }[]
  examHistory: { date: string; score: number; passed: boolean }[]
  aiAdvices: string[]
  overallLevel: string
  overallScore: number
}

const { data: reportData, loading, fetch: fetchReport } = useSWR<ReportData>(
  'student-report',
  async () => {
    const res = await fetch('/api/student/report')
    const json = await res.json()
    if (json.code !== 0) throw new Error(json.message)
    return json.data
  },
  120_000
)

function exportPDF() {
  window.print()
}

onMounted(() => fetchReport())
</script>

<template>
  <div class="report-page">
    <div class="page-header">
      <h2>学习效果评估报告</h2>
      <button class="btn btn-outline" @click="exportPDF">导出 PDF</button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>生成报告中...</p></div>

    <template v-else-if="reportData">
      <!-- 总评 -->
      <div class="overall-card card">
        <div class="overall-score">{{ reportData.overallScore }}分</div>
        <div class="overall-level">{{ reportData.overallLevel }}</div>
      </div>

      <!-- 能力成长曲线 -->
      <div class="card">
        <h3>能力成长曲线</h3>
        <div class="growth-table">
          <div class="growth-header">
            <span>日期</span>
            <span>交通标志</span>
            <span>交通法规</span>
            <span>安全常识</span>
            <span>驾驶理论</span>
          </div>
          <div v-for="row in reportData.growthCurve" :key="row.date" class="growth-row">
            <span>{{ row.date }}</span>
            <span v-for="(s, i) in row.scores" :key="i" :class="{ low: s < 60 }">{{ s }}</span>
          </div>
        </div>
      </div>

      <!-- 历次模拟考 -->
      <div class="card">
        <h3>历次模拟考成绩</h3>
        <div class="exam-history">
          <div v-for="exam in reportData.examHistory" :key="exam.date" class="exam-row">
            <span>{{ exam.date }}</span>
            <span class="exam-score" :class="exam.passed ? 'passed' : 'failed'">{{ exam.score }}分</span>
            <span class="exam-tag" :class="exam.passed ? 'tag-green' : 'tag-orange'">
              {{ exam.passed ? '通过' : '未通过' }}
            </span>
          </div>
        </div>
      </div>

      <!-- AI建议 -->
      <div class="card">
        <h3>AI 改进建议</h3>
        <ul class="advice-list">
          <li v-for="(advice, idx) in reportData.aiAdvices" :key="idx">{{ advice }}</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-page { max-width: 900px; margin: 0 auto; padding: 24px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.overall-card { text-align: center; padding: 32px; margin-bottom: 20px; }
.overall-score { font-size: 48px; font-weight: 800; color: var(--color-primary); }
.overall-level { font-size: var(--font-size-lg); color: var(--color-text-secondary); margin-top: 4px; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }

.growth-table { width: 100%; }
.growth-header, .growth-row {
  display: grid; grid-template-columns: 100px repeat(4, 1fr); gap: 8px;
  padding: 8px 0; font-size: var(--font-size-sm);
}
.growth-header { font-weight: 600; border-bottom: 1px solid var(--color-border); margin-bottom: 8px; }
.growth-row { border-bottom: 1px solid var(--color-border-light); }
.growth-row span { text-align: center; }
.low { color: var(--color-error); font-weight: 600; }

.exam-history { display: flex; flex-direction: column; gap: 8px; }
.exam-row { display: flex; align-items: center; gap: 16px; font-size: var(--font-size-sm); padding: 8px 0; border-bottom: 1px solid var(--color-border-light); }
.exam-score { font-weight: 700; }
.exam-score.passed { color: var(--color-success); }
.exam-score.failed { color: var(--color-error); }
.exam-tag { font-size: 11px; padding: 1px 8px; border-radius: var(--radius-sm); }

.advice-list { padding-left: 20px; }
.advice-list li { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 8px; line-height: 1.6; }
</style>
