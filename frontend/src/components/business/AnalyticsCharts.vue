<script setup lang="ts">
// src/components/business/AnalyticsCharts.vue — 全局学情分析图表（折线图+柱状图+饼图）
import { computed } from 'vue'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line, Bar, Pie } from 'vue-chartjs'

Chart.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Filler, Tooltip, Legend,
)

// ======================== Props ========================
interface ActiveTrendItem { date: string; count: number }
interface DimensionAvgItem { name: string; score: number }
interface AccuracyDistItem { range: string; count: number }

const props = withDefaults(defineProps<{
  activeTrend: ActiveTrendItem[]
  dimensionAvg: DimensionAvgItem[]
  accuracyDistribution: AccuracyDistItem[]
  loading?: boolean
}>(), { loading: false })

// ======================== 折线图：近30天活跃趋势 ========================
const lineData = computed(() => ({
  labels: props.activeTrend.map(d => d.date),
  datasets: [{
    label: '刷题人数',
    data: props.activeTrend.map(d => d.count),
    borderColor: '#1677FF',
    backgroundColor: 'rgba(22, 119, 255, 0.08)',
    borderWidth: 2.5,
    pointRadius: 3,
    pointHoverRadius: 6,
    pointBackgroundColor: '#1677FF',
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    tension: 0.3,
    fill: true,
  }],
}))

const lineOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' as const },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(0,0,0,0.75)',
      padding: 10,
      titleFont: { size: 12 },
      bodyFont: { size: 12 },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 11 } } },
    y: { beginAtZero: true, grid: { color: '#F0F0F0' }, ticks: { stepSize: 1, font: { size: 11 } } },
  },
}))

// ======================== 柱状图：四维能力平均得分 ========================
const barData = computed(() => ({
  labels: props.dimensionAvg.map(d => d.name),
  datasets: [{
    label: '平均得分',
    data: props.dimensionAvg.map(d => d.score),
    backgroundColor: ['#1677FF', '#52C41A', '#FAAD14', '#FF4D4F'],
    borderRadius: 6,
    borderSkipped: false,
    barPercentage: 0.6,
  }],
}))

const barOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${ctx.parsed.y} 分`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 } } },
    y: {
      beginAtZero: true,
      max: 100,
      grid: { color: '#F0F0F0' },
      ticks: { stepSize: 20, font: { size: 11 }, callback: (v: any) => `${v}分` },
    },
  },
}))

// ======================== 饼图：正确率分层分布 ========================
const pieData = computed(() => ({
  labels: props.accuracyDistribution.map(d => d.range),
  datasets: [{
    data: props.accuracyDistribution.map(d => d.count),
    backgroundColor: ['#FF4D4F', '#FAAD14', '#52C41A'],
    borderColor: '#fff',
    borderWidth: 2,
  }],
}))

const pieOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: { padding: 20, usePointStyle: true, font: { size: 12 } },
    },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0
          return `${ctx.label}: ${ctx.parsed} 人 (${pct}%)`
        },
      },
    },
  },
}))
</script>

<template>
  <div class="analytics-charts">
    <!-- 折线图：活跃趋势 -->
    <div class="chart-card card">
      <div class="chart-header">
        <h4>近30天学员刷题活跃趋势</h4>
      </div>
      <div v-if="activeTrend.length === 0 && !loading" class="chart-empty">暂无活跃数据</div>
      <div v-else class="chart-body">
        <Line :data="lineData" :options="lineOptions" />
      </div>
    </div>

    <!-- 柱状图：四维能力 -->
    <div class="chart-card card">
      <div class="chart-header">
        <h4>四大能力维度平均得分对比</h4>
      </div>
      <div v-if="dimensionAvg.length === 0 && !loading" class="chart-empty">暂无测评数据</div>
      <div v-else class="chart-body">
        <Bar :data="barData" :options="barOptions" />
      </div>
    </div>

    <!-- 饼图：正确率分层 -->
    <div class="chart-card card">
      <div class="chart-header">
        <h4>学员正确率分层分布</h4>
      </div>
      <div v-if="accuracyDistribution.every(d => d.count === 0) && !loading" class="chart-empty">暂无学员数据</div>
      <div v-else class="chart-body pie-body">
        <Pie :data="pieData" :options="pieOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-charts {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  padding: 20px;
  overflow: hidden;
}

.chart-header {
  margin-bottom: 12px;
}

.chart-header h4 {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.chart-body {
  height: 280px;
  position: relative;
}

.pie-body {
  height: 300px;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

@media (max-width: 1200px) {
  .analytics-charts {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .analytics-charts {
    grid-template-columns: 1fr;
  }
}
</style>
