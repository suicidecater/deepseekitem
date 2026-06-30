<script setup lang="ts">
// src/components/charts/RadarChart.vue — Chart.js 雷达图组件（支持非线性刻度）
import { computed } from 'vue'
import {
  Chart,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Radar } from 'vue-chartjs'

// 按需注册 Chart.js 模块（Tree-shake 友好）
Chart.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
)

// === 非线性刻度映射 ===
// 6 个分段，真实分数范围不同，但在视觉上各占 1/6 等宽
const NONLINEAR_SEGMENTS = [
  { realMin: 0,  realMax: 50,   visualStart: 0 },
  { realMin: 50, realMax: 70,   visualStart: 100 / 6 },
  { realMin: 70, realMax: 80,   visualStart: 200 / 6 },
  { realMin: 80, realMax: 90,   visualStart: 300 / 6 },
  { realMin: 90, realMax: 95,   visualStart: 400 / 6 },
  { realMin: 95, realMax: 100,  visualStart: 500 / 6 },
] as const

const SEGMENT_VISUAL_WIDTH = 100 / 6 // 每段视觉宽度 ≈ 16.67

/** 真实分数 → 视觉位置（用于数据绘制和半径计算） */
function mapScore(real: number): number {
  if (real <= 0) return 0
  for (const seg of NONLINEAR_SEGMENTS) {
    if (real >= seg.realMin && real <= seg.realMax) {
      const ratio = (real - seg.realMin) / (seg.realMax - seg.realMin)
      return seg.visualStart + ratio * SEGMENT_VISUAL_WIDTH
    }
  }
  return 100
}

// === 自定刻度值（非等比例标签） ===
const CUSTOM_TICKS = [
  { value: 0,             label: '0' },
  { value: SEGMENT_VISUAL_WIDTH * 1, label: '50' },
  { value: SEGMENT_VISUAL_WIDTH * 2, label: '70' },
  { value: SEGMENT_VISUAL_WIDTH * 3, label: '80' },
  { value: SEGMENT_VISUAL_WIDTH * 4, label: '90' },
  { value: SEGMENT_VISUAL_WIDTH * 5, label: '95' },
  { value: 100,           label: '100' },
]

// === Props ===
interface RadarDataset {
  label: string
  data: number[]
  color?: string
  fill?: boolean
  dashed?: boolean
}

const props = withDefaults(defineProps<{
  dimensions: string[]
  datasets: RadarDataset[]
  height?: string | number
  maxValue?: number
  showLegend?: boolean
}>(), {
  height: 320,
  maxValue: 100,
  showLegend: true,
})

// === 配色 ===
const defaultColors = [
  { bg: 'rgba(22,119,255,0.15)', border: '#1677FF' },
  { bg: 'rgba(255,77,79,0.15)',  border: '#FF4D4F' },
  { bg: 'rgba(82,196,26,0.15)',  border: '#52C41A' },
  { bg: 'rgba(250,140,22,0.15)', border: '#FA8C16' },
]

// === Chart.js 数据（含非线性映射） ===
const chartData = computed(() => ({
  labels: props.dimensions,
  datasets: props.datasets.map((ds, i) => {
    const c = ds.color
      ? { border: ds.color, bg: `${ds.color}22` }
      : defaultColors[i % defaultColors.length]
    return {
      label: ds.label,
      data: ds.data.map(mapScore), // ← 非线性映射
      backgroundColor: ds.fill !== false ? c.bg : 'transparent',
      borderColor: c.border,
      borderWidth: 2.5,
      borderDash: ds.dashed ? [5, 5] : [],
      pointBackgroundColor: c.border,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 8,
      tension: 0.1,
      fill: ds.fill !== false,
    }
  }),
}))

// === Chart.js 配置 ===
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.showLegend && props.datasets.length > 1,
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: { size: 13 },
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx: { dataset: { label?: string }; datasetIndex: number; dataIndex: number }) => {
          // 显示真实分数（不做映射）
          const realVal = props.datasets[ctx.datasetIndex]?.data?.[ctx.dataIndex]
          return `${ctx.dataset.label}: ${realVal ?? '?'}分`
        },
      },
    },
  },
  scales: {
    r: {
      beginAtZero: true,
      max: props.maxValue,
      min: 0,
      ticks: {
        showLabelBackdrop: false,
        font: { size: 11 },
        stepSize: SEGMENT_VISUAL_WIDTH,
        callback: function (this: { getLabelForValue?: (v: number) => string }, value: number) {
          const threshold = 0.1
          for (const t of CUSTOM_TICKS) {
            if (Math.abs(value - t.value) < threshold) {
              return t.label
            }
          }
          return ''
        },
      } as Record<string, unknown>,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      afterBuildTicks(axis: any) {
        axis.ticks = CUSTOM_TICKS.map(t => ({
          value: t.value,
          label: t.label,
          major: true,
        }))
      },
      pointLabels: {
        font: { size: 13, weight: '600' as const },
        color: '#333',
      },
      grid: {
        color: '#E0E0E0',
        circular: false,
      },
      angleLines: {
        color: '#E8E8E8',
      },
    },
  },
}))
</script>

<template>
  <div class="radar-chart-wrapper">
    <div
      class="chart-container"
      :style="{ height: typeof height === 'number' ? height + 'px' : height }"
    >
      <Radar :data="chartData" :options="(chartOptions as any)" />
    </div>
  </div>
</template>

<style scoped>
.radar-chart-wrapper {
  width: 100%;
}

.chart-container {
  position: relative;
  width: 100%;
  min-height: 280px;
}
</style>
