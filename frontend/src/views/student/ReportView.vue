<script setup lang="ts">
// src/views/student/ReportView.vue - 学习效果评估报告（展示测评结果 + 成长曲线 + 方向切换）
import { ref, onMounted, computed, watch } from 'vue'
import { useSWR } from '@/composables/useSWR'
import { useAuthStore } from '@/stores/auth'
import { get } from '@/api/request'
import RadarChart from '@/components/charts/RadarChart.vue'

const authStore = useAuthStore()

// 学习方向（从全局状态读取，首页唯一控制）
const currentDirection = ref<number>(authStore.studySubject)

interface WeakPoint { name: string; rate: number }

interface ReportData {
  subjectName: string
  studySubject: number
  hasEvaluation: boolean
  overallScore: number
  overallLevel: string
  radarData: { dimensions: string[]; current: number[]; baseline: number[] } | null
  weakPoints: WeakPoint[]
  difficultyBreakdown: Record<string, number> | null
  growthCurve: { date: string; subject: string; scores: number[] }[]
  examHistory: { date: string; score: number; passed: boolean; subject: string }[]
  aiAdvices: string[]
}

const { data: reportData, loading, fetch: fetchReport, invalidate: invalidateReport } = useSWR<ReportData>(
  'student-report',
  async () => {
    const res = await get<ReportData>(`/api/student/report?direction=${currentDirection.value}`)
    return res.data.data
  },
  120_000
)

// 雷达图数据
const radarChartData = computed(() => {
  const rd = reportData.value?.radarData
  if (!rd) return []
  return [
    { label: '当前能力', data: rd.current, color: '#1677FF' },
    { label: '基准线', data: rd.baseline, color: '#999', fill: false, dashed: true },
  ]
})

// 等级颜色
const levelColorMap: Record<string, string> = {
  '冲刺水平': '#52C41A', '进阶水平': '#1677FF', '基础水平': '#FAAD14', '入门水平': '#FF4D4F',
  '未测评': '#999',
}

// 薄弱项颜色
const weakColors = ['#FF4D4F', '#FA8C16', '#FAAD14', '#FF7A45', '#FF7875']

function exportPDF() { window.print() }

// 监听首页方向切换 → 自动刷新
watch(() => authStore.studySubject, (newDir) => {
  if (newDir !== currentDirection.value) {
    currentDirection.value = newDir
    invalidateReport()
    fetchReport()
  }
})

onMounted(() => { invalidateReport(); fetchReport() })
</script>

<template>
  <div class="report-page">
    <div class="page-header">
      <h2>学习效果评估报告</h2>
      <span class="page-sub">{{ reportData?.subjectName || '' }}</span>
      <button class="btn btn-outline" @click="exportPDF">导出 PDF</button>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>生成报告中...</p></div>

    <template v-else-if="reportData && reportData.hasEvaluation">
      <!-- 总评 -->
      <div class="card overall-card">
        <div class="overall-score">{{ reportData.overallScore }}<span class="score-unit">分</span></div>
        <div class="overall-level" :style="{ color: levelColorMap[reportData.overallLevel] || '#999' }">
          {{ reportData.overallLevel }}
        </div>
      </div>

      <!-- 能力雷达图 -->
      <div class="card">
        <h3>🎯 能力雷达图（{{ reportData.subjectName }}）</h3>
        <div class="radar-wrap" v-if="reportData.radarData">
          <RadarChart :dimensions="reportData.radarData.dimensions" :datasets="radarChartData" height="280" />
        </div>
        <div v-else class="empty-hint">暂无雷达数据</div>
      </div>

      <!-- 薄弱知识点 + 难度分层 -->
      <div class="two-col">
        <div class="card">
          <h3>⚠️ 薄弱知识点</h3>
          <div v-if="reportData.weakPoints.length" class="weak-list">
            <span
              v-for="(w, i) in reportData.weakPoints" :key="w.name"
              class="weak-tag" :style="{ background: weakColors[i % weakColors.length] }"
            >{{ w.name }} {{ w.rate }}%</span>
          </div>
          <div v-else class="empty-hint">无明显薄弱项，继续加油！</div>
        </div>

        <div class="card">
          <h3>📊 难度分层</h3>
          <div v-if="reportData.difficultyBreakdown" class="diff-list">
            <div v-for="(val, key) in reportData.difficultyBreakdown" :key="key" class="diff-row">
              <span class="diff-label">{{ key }}</span>
              <div class="diff-bar-bg"><div class="diff-bar-fill" :style="{ width: val + '%', background: val >= 80 ? '#52C41A' : val >= 60 ? '#1677FF' : '#FF4D4F' }"></div></div>
              <span class="diff-val">{{ val }}%</span>
            </div>
          </div>
          <div v-else class="empty-hint">暂无数据</div>
        </div>
      </div>

      <!-- 能力成长曲线 -->
      <div class="card" v-if="reportData.growthCurve.length">
        <h3>📈 能力成长曲线</h3>
        <div class="growth-table">
          <div class="growth-header">
            <span>日期</span><span>方向</span><span>交通标志</span><span>交通法规</span><span>安全常识</span><span>驾驶理论</span>
          </div>
          <div v-for="row in reportData.growthCurve" :key="row.date" class="growth-row">
            <span>{{ row.date }}</span>
            <span class="grow-subject">{{ row.subject }}</span>
            <span v-for="(s, i) in row.scores" :key="i" :class="{ low: s < 60 }">{{ s }}</span>
          </div>
        </div>
      </div>

      <!-- 历次测评 -->
      <div class="card">
        <h3>📋 历次测评记录</h3>
        <div v-if="reportData.examHistory.length" class="exam-list">
          <div v-for="(exam, idx) in reportData.examHistory" :key="exam.date + '_' + idx" class="exam-row">
            <span class="exam-date">{{ exam.date }}</span>
            <span class="exam-subj">{{ exam.subject }}</span>
            <span class="exam-score" :class="exam.passed ? 'passed' : 'failed'">{{ exam.score }}分</span>
            <span class="exam-tag" :class="exam.passed ? 'tag-green' : 'tag-orange'">
              {{ exam.passed ? '通过' : '未通过' }}
            </span>
          </div>
        </div>
        <div v-else class="empty-hint">暂无记录</div>
      </div>

      <!-- AI建议 -->
      <div class="card">
        <h3>🤖 AI 改进建议</h3>
        <ul class="advice-list">
          <li v-for="(advice, idx) in reportData.aiAdvices" :key="idx">{{ advice }}</li>
        </ul>
      </div>
    </template>

    <!-- 未测评提示 -->
    <div v-else-if="reportData && !reportData.hasEvaluation" class="card no-eval-card">
      <div class="no-eval-icon">📊</div>
      <h3>暂无测评数据</h3>
      <p>请先完成{{ reportData.subjectName }}方向的能力基线测评，测评完成后将在此生成详细的评估报告。</p>
      <router-link to="/student/evaluation" class="btn btn-primary">去测评</router-link>
    </div>
  </div>
</template>

<style scoped>
.report-page { max-width: 960px; margin: 0 auto; padding: 24px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); flex: 1; }
.page-sub { font-size: 13px; color: var(--color-text-tertiary); background: var(--color-bg); padding: 2px 10px; border-radius: 20px; }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }

/* 总评 */
.overall-card { text-align: center; padding: 32px; }
.overall-score { font-size: 56px; font-weight: 800; color: var(--color-primary); }
.score-unit { font-size: 20px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 4px; }
.overall-level { font-size: var(--font-size-xl); font-weight: 600; margin-top: 4px; }

/* 雷达图 */
.radar-wrap { max-width: 400px; margin: 0 auto; }

/* 双栏 */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }

/* 薄弱项 */
.weak-list { display: flex; flex-wrap: wrap; gap: 8px; }
.weak-tag { padding: 4px 12px; border-radius: 20px; color: #fff; font-size: 13px; font-weight: 500; }

/* 难度分层 */
.diff-list { display: flex; flex-direction: column; gap: 14px; }
.diff-row { display: flex; align-items: center; gap: 10px; }
.diff-label { width: 48px; font-size: 14px; font-weight: 500; flex-shrink: 0; }
.diff-bar-bg { flex: 1; height: 10px; background: #F0F0F0; border-radius: 5px; overflow: hidden; }
.diff-bar-fill { height: 100%; border-radius: 5px; transition: width 0.6s ease; }
.diff-val { width: 36px; text-align: right; font-size: 14px; font-weight: 600; }

/* 成长曲线 */
.growth-table { width: 100%; }
.growth-header, .growth-row {
  display: grid; grid-template-columns: 70px 70px repeat(4, 1fr); gap: 6px;
  padding: 8px 0; font-size: var(--font-size-sm);
}
.growth-header { font-weight: 600; border-bottom: 1px solid var(--color-border); margin-bottom: 8px; }
.growth-row { border-bottom: 1px solid var(--color-border-light); }
.growth-row span { text-align: center; }
.grow-subject { color: var(--color-text-tertiary); font-size: 12px; }
.low { color: var(--color-error); font-weight: 600; }

/* 测评记录 */
.exam-list { display: flex; flex-direction: column; gap: 8px; }
.exam-row { display: flex; align-items: center; gap: 16px; font-size: var(--font-size-sm); padding: 8px 0; border-bottom: 1px solid var(--color-border-light); }
.exam-date { width: 60px; }
.exam-subj { color: var(--color-text-tertiary); font-size: 12px; width: 60px; }
.exam-score { font-weight: 700; flex: 1; }
.exam-score.passed { color: var(--color-success); }
.exam-score.failed { color: var(--color-error); }
.exam-tag { font-size: 11px; padding: 1px 8px; border-radius: var(--radius-sm); }

/* 建议 */
.advice-list { padding-left: 20px; }
.advice-list li { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 8px; line-height: 1.6; }

/* 未测评 */
.no-eval-card { text-align: center; padding: 48px 24px; }
.no-eval-icon { font-size: 48px; margin-bottom: 12px; }
.no-eval-card h3 { font-size: 20px; margin-bottom: 8px; }
.no-eval-card p { color: var(--color-text-tertiary); margin-bottom: 20px; }

.empty-hint { text-align: center; color: var(--color-text-tertiary); padding: 20px; font-size: 14px; }
</style>
