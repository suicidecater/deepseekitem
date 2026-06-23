<script setup lang="ts">
// src/components/business/HeatmapCalendar.vue - GitHub风格热力图
interface DayCell {
  date: string
  minutes: number
  level: 0 | 1 | 2 | 3 | 4
}

defineProps<{ cells: DayCell[]; year?: number }>()

function getColor(level: number): string {
  const colors = ['#EBEDF0', '#C6E48B', '#7BC96F', '#239A3B', '#196127']
  return colors[level] || colors[0]
}
</script>

<template>
  <div class="heatmap">
    <div class="heatmap-grid">
      <div
        v-for="cell in cells" :key="cell.date"
        class="heatmap-cell"
        :style="{ background: getColor(cell.level) }"
        :title="`${cell.date}: ${cell.minutes}分钟`"
      ></div>
    </div>
    <div class="heatmap-legend">
      <span>少</span>
      <span class="legend-block" style="background:#EBEDF0"></span>
      <span class="legend-block" style="background:#C6E48B"></span>
      <span class="legend-block" style="background:#7BC96F"></span>
      <span class="legend-block" style="background:#239A3B"></span>
      <span class="legend-block" style="background:#196127"></span>
      <span>多</span>
    </div>
  </div>
</template>

<style scoped>
.heatmap { overflow-x: auto; }
.heatmap-grid {
  display: grid; grid-template-columns: repeat(52, 1fr);
  gap: 3px; margin-bottom: 8px;
}
.heatmap-cell {
  aspect-ratio: 1; border-radius: 2px; min-width: 12px;
}
.heatmap-legend {
  display: flex; align-items: center; gap: 4px; justify-content: flex-end;
  font-size: 11px; color: var(--color-text-tertiary);
}
.legend-block { width: 12px; height: 12px; border-radius: 2px; }
</style>
