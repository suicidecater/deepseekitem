// src/types/chart.ts
export interface RadarDataItem {
  name: string
  value: number
  max?: number
}

export interface RadarChartData {
  dimensions: string[]
  current: number[]
  baseline: number[]
}
