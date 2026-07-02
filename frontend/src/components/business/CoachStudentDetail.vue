<script setup lang="ts">
// src/components/business/CoachStudentDetail.vue — 学员详情弹窗（雷达图+趋势+错题+考试记录）
import { ref, computed, watch } from 'vue'
import {
  Chart,
  CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import RadarChart from '@/components/charts/RadarChart.vue'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

// ======================== 类型 ========================
interface Dimension { name: string; score: number }
interface TrendItem { date: string; accuracy: number; count: number }
interface ExamRecord { create_time?: string; score?: number; correct_rate?: number }
interface StudentBase { name: string; email: string; carType: string }

const props = defineProps<{
  visible: boolean
  loading?: boolean
  student: StudentBase | null
  dimensions: Dimension[]
  weakPoints: string[]
  examHistory: ExamRecord[]
  trendData: TrendItem[]
  totalPracticeCount?: number
  totalErrorCount?: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'export', id: number): void
}>()

// 当前详情 Tab
type TabKey = 'overview' | 'trend' | 'errors' | 'exams'
const activeTab = ref<TabKey>('overview')

const tabs: { key: TabKey; label: string }[] = [
  { key: 'overview', label: '能力总览' },
  { key: 'trend', label: '学习趋势' },
  { key: 'errors', label: '薄弱点' },
  { key: 'exams', label: '考试记录' },
]

// ======================== 趋势折线图 ========================
const trendLineData = computed(() => ({
  labels: props.trendData.map(d => d.date),
  datasets: [
    {
      label: '正确率(%)',
      data: props.trendData.map(d => d.accuracy),
      borderColor: '#1677FF',
      backgroundColor: 'rgba(22, 119, 255, 0.08)',
      borderWidth: 2,
      pointRadius: 2,
      pointHoverRadius: 5,
      tension: 0.3,
      fill: true,
      yAxisID: 'y',
    },
    {
      label: '做题量',
      data: props.trendData.map(d => d.count),
      borderColor: '#52C41A',
      backgroundColor: 'rgba(82, 196, 26, 0.08)',
      borderWidth: 2,
      pointRadius: 2,
      tension: 0.3,
      fill: true,
      yAxisID: 'y1',
      borderDash: [5, 3],
    },
  ],
}))

const trendOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' as const },
  plugins: {
    legend: {
      position: 'top' as const,
      labels: { usePointStyle: true, padding: 16, font: { size: 12 } },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      beginAtZero: true,
      max: 100,
      grid: { color: '#F0F0F0' },
      ticks: { callback: (v: any) => `${v}%`, font: { size: 10 } },
    },
    y1: {
      type: 'linear' as const,
      display: true,
      position: 'right' as const,
      beginAtZero: true,
      grid: { drawOnChartArea: false },
      ticks: { stepSize: 1, font: { size: 10 } },
    },
  },
}))

// ======================== 辅助方法 ========================
function formatDate(iso?: string): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  } catch { return '' }
}

function getDimensionColor(name: string): string {
  const map: Record<string, string> = {
    '交通标志': '#1677FF',
    '交通法规': '#52C41A',
    '安全常识': '#FAAD14',
    '驾驶理论': '#FF4D4F',
  }
  return map[name] || '#1677FF'
}

// ======================== 雷达图数据 ========================
const radarDatasets = computed(() => {
  if (!props.dimensions.length) return []
  return [{
    label: props.student?.name || '学员',
    data: props.dimensions.map(d => d.score),
    color: '#1677FF',
    fill: true,
  }]
})

// 键盘 ESC 关闭
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

watch(() => props.visible, (v) => {
  if (v) document.addEventListener('keydown', onKeydown)
  else document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Transition name="modal-fade">
    <div v-if="visible" class="detail-overlay" @click.self="emit('close')">
      <div class="detail-modal card">
        <!-- 头部 -->
        <div class="modal-header">
          <div>
            <h3>{{ student?.name || '学员' }} - 学情详情</h3>
            <span class="modal-sub">{{ student?.email }} · {{ student?.carType }}</span>
          </div>
          <div class="modal-header-actions">
            <button class="btn btn-sm btn-outline" @click="emit('export', (student as any)?.id || 0)">导出学情</button>
            <button class="btn-close" @click="emit('close')">✕</button>
          </div>
        </div>

        <div v-if="loading" class="modal-loading">加载中...</div>
        <template v-else>
          <!-- 统计概览条 -->
          <div class="stat-strip">
            <div class="strip-item">
              <span class="strip-num">{{ totalPracticeCount ?? 0 }}</span>
              <span class="strip-label">专项训练次数</span>
            </div>
            <div class="strip-item">
              <span class="strip-num">{{ totalErrorCount ?? 0 }}</span>
              <span class="strip-label">错题总数</span>
            </div>
            <div class="strip-item">
              <span class="strip-num">{{ examHistory.length }}</span>
              <span class="strip-label">考试记录</span>
            </div>
            <div class="strip-item">
              <span class="strip-num">{{ weakPoints.length }}</span>
              <span class="strip-label">薄弱知识点</span>
            </div>
          </div>

          <!-- Tab 切换 -->
          <div class="modal-tabs">
            <button
              v-for="tab in tabs" :key="tab.key"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >{{ tab.label }}</button>
          </div>

          <!-- Tab: 能力总览 -->
          <div v-if="activeTab === 'overview'" class="tab-content">
            <div class="overview-grid">
              <div class="overview-chart">
                <h4>四维能力雷达图</h4>
                <RadarChart
                  v-if="dimensions.length"
                  :dimensions="dimensions.map(d => d.name)"
                  :datasets="radarDatasets"
                  :height="320"
                  :show-legend="false"
                />
                <div v-else class="hint-text">暂无测评数据，学员需先完成能力测评</div>
              </div>
              <div class="overview-list">
                <h4>各维度得分详情</h4>
                <div v-if="dimensions.length">
                  <div v-for="d in dimensions" :key="d.name" class="dim-row">
                    <div class="dim-name-col">
                      <span class="dim-dot" :style="{ background: getDimensionColor(d.name) }"></span>
                      <span>{{ d.name }}</span>
                    </div>
                    <div class="dim-bar-col">
                      <div class="dim-bar-bg">
                        <div
                          class="dim-bar-fill"
                          :style="{ width: d.score + '%', background: d.score < 60 ? '#FF4D4F' : getDimensionColor(d.name) }"
                        ></div>
                      </div>
                    </div>
                    <span class="dim-score" :class="{ low: d.score < 60 }">{{ d.score }}</span>
                  </div>
                </div>
                <div v-else class="hint-text">暂无测评数据</div>
              </div>
            </div>
          </div>

          <!-- Tab: 学习趋势 -->
          <div v-if="activeTab === 'trend'" class="tab-content">
            <div class="trend-section">
              <h4>近30天正确率 & 做题量趋势</h4>
              <div v-if="trendData.length" class="trend-chart-wrapper">
                <Line :data="trendLineData" :options="trendOptions" />
              </div>
              <div v-else class="hint-text">暂无学习趋势数据</div>
            </div>
          </div>

          <!-- Tab: 薄弱点 -->
          <div v-if="activeTab === 'errors'" class="tab-content">
            <div class="weak-section">
              <h4>薄弱知识点 Top {{ weakPoints.length || '--' }}</h4>
              <div v-if="weakPoints.length" class="weak-grid">
                <div
                  v-for="(w, idx) in weakPoints.slice(0, 10)"
                  :key="idx"
                  class="weak-card"
                >
                  <span class="weak-rank">{{ idx + 1 }}</span>
                  <span class="weak-name">{{ typeof w === 'string' ? w : (w as any).name || (w as any).know || String(w) }}</span>
                </div>
              </div>
              <div v-else class="hint-text">该学员暂无薄弱知识点，表现良好 🎉</div>
            </div>
          </div>

          <!-- Tab: 考试记录 -->
          <div v-if="activeTab === 'exams'" class="tab-content">
            <div class="exam-section">
              <h4>历次考试记录（最近10条）</h4>
              <div v-if="examHistory.length">
                <div class="exam-table">
                  <div class="exam-th">
                    <span>时间</span><span>得分</span><span>正确率</span><span>结果</span>
                  </div>
                  <div v-for="(e, idx) in examHistory" :key="idx" class="exam-tr">
                    <span>{{ formatDate(e.create_time) }}</span>
                    <span class="exam-score">{{ e.score ?? '--' }}</span>
                    <span>{{ e.correct_rate != null ? e.correct_rate + '%' : '--' }}</span>
                    <span>
                      <span class="tag" :class="(e.score ?? 0) >= 90 ? 'tag-green' : 'tag-orange'">
                        {{ (e.score ?? 0) >= 90 ? '通过' : '未通过' }}
                      </span>
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="hint-text">暂无考试记录</div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* 遮罩 */
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 24px;
  overflow-y: auto;
}

.detail-modal {
  width: 100%;
  max-width: 900px;
  background: var(--color-bg-white);
  padding: 0;
  max-height: none;
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-xl);
}

/* 头部 */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 24px 28px 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h3 {
  font-size: var(--font-size-xl);
  margin: 0 0 4px;
}

.modal-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.modal-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-sm {
  padding: 5px 14px;
  font-size: var(--font-size-xs);
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  padding: 4px 8px;
  border-radius: 4px;
  line-height: 1;
}

.btn-close:hover {
  background: #f0f0f0;
  color: var(--color-text-primary);
}

.modal-loading {
  text-align: center;
  padding: 60px;
  color: var(--color-text-tertiary);
}

/* 统计条 */
.stat-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-bottom: 1px solid var(--color-border-light);
}

.strip-item {
  text-align: center;
  padding: 16px 8px;
}

.strip-item:not(:last-child) {
  border-right: 1px solid var(--color-border-light);
}

.strip-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-primary);
}

.strip-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* Tabs */
.modal-tabs {
  display: flex;
  gap: 0;
  padding: 0 28px;
  border-bottom: 1px solid var(--color-border-light);
}

.modal-tabs button {
  padding: 12px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-tabs button:hover {
  color: var(--color-primary);
}

.modal-tabs button.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

/* Tab 内容 */
.tab-content {
  padding: 24px 28px 28px;
}

.tab-content h4 {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--color-text-primary);
}

/* 能力总览 */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.overview-chart h4,
.overview-list h4 {
  margin-bottom: 12px;
}

.dim-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.dim-name-col {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 72px;
  font-size: var(--font-size-xs);
}

.dim-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dim-bar-col {
  flex: 1;
}

.dim-bar-bg {
  height: 8px;
  background: #F0F0F0;
  border-radius: 4px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.dim-score {
  width: 30px;
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-align: right;
}

.dim-score.low {
  color: var(--color-error);
}

/* 趋势图 */
.trend-chart-wrapper {
  height: 320px;
}

/* 薄弱点 */
.weak-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.weak-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #FFF7E6;
  border-radius: var(--radius-md);
  border: 1px solid #FFE7BA;
}

.weak-rank {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-warning);
  color: #fff;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.weak-name {
  font-size: var(--font-size-xs);
  color: var(--color-text-primary);
}

/* 考试记录表 */
.exam-table {
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.exam-th {
  display: grid;
  grid-template-columns: 1fr 80px 80px 80px;
  padding: 10px 16px;
  background: #FAFAFA;
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
}

.exam-tr {
  display: grid;
  grid-template-columns: 1fr 80px 80px 80px;
  padding: 10px 16px;
  font-size: var(--font-size-xs);
  border-top: 1px solid var(--color-border-light);
}

.exam-tr:hover {
  background: #FAFAFA;
}

.exam-score {
  font-weight: 600;
  color: var(--color-primary);
}

/* 空状态 */
.hint-text {
  text-align: center;
  padding: 24px;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

/* 过渡动画 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .detail-modal,
.modal-fade-leave-to .detail-modal {
  transform: scale(0.95) translateY(10px);
}

.modal-fade-enter-active .detail-modal,
.modal-fade-leave-active .detail-modal {
  transition: transform 0.25s ease;
}

@media (max-width: 768px) {
  .detail-overlay {
    padding: 0;
    align-items: stretch;
  }
  .detail-modal {
    border-radius: 0;
    max-width: 100%;
  }
  .overview-grid {
    grid-template-columns: 1fr;
  }
  .weak-grid {
    grid-template-columns: 1fr;
  }
  .stat-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
