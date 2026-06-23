<script setup lang="ts">
// src/views/student/ProgressView.vue - 学习进度可视化
import { ref, onMounted } from 'vue'
import { useSWR } from '@/composables/useSWR'
import KnowledgeTreeMap from '@/components/business/KnowledgeTreeMap.vue'
import HeatmapCalendar from '@/components/business/HeatmapCalendar.vue'

const activeTab = ref<'tree' | 'radar' | 'heatmap'>('tree')

interface ProgressData {
  stats: { totalDays: number; totalHours: number; totalQuestions: number; accuracy: number }
  knowledgeTree: { name: string; value: number; completed: number; color: string }[]
  radarData: { dimensions: string[]; current: number[]; baseline: number[] }
  heatmapCells: { date: string; minutes: number; level: 0|1|2|3|4 }[]
}

const { data: progressData, loading, fetch: fetchProgress } = useSWR<ProgressData>(
  'student-progress',
  async () => {
    const res = await fetch('/api/student/progress')
    const json = await res.json()
    if (json.code !== 0) throw new Error(json.message)
    return json.data
  },
  60_000
)

onMounted(() => fetchProgress())
</script>

<template>
  <div class="progress-page">
    <div class="page-header">
      <h2>学习进度可视化</h2>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><p>加载中...</p></div>

    <template v-else-if="progressData">
      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.totalDays }}</span><span class="stat-label">学习天数</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.totalHours }}</span><span class="stat-label">总时长(h)</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.totalQuestions }}</span><span class="stat-label">做题数</span></div>
        <div class="stat-card"><span class="stat-num">{{ progressData.stats.accuracy }}%</span><span class="stat-label">正确率</span></div>
      </div>

      <!-- 图表切换 -->
      <div class="tab-bar">
        <button :class="{ active: activeTab === 'tree' }" @click="activeTab = 'tree'">知识树</button>
        <button :class="{ active: activeTab === 'radar' }" @click="activeTab = 'radar'">能力雷达</button>
        <button :class="{ active: activeTab === 'heatmap' }" @click="activeTab = 'heatmap'">学习热力图</button>
      </div>

      <!-- 知识树 -->
      <div v-if="activeTab === 'tree'" class="card">
        <h3>知识树掌握度</h3>
        <KnowledgeTreeMap :nodes="progressData.knowledgeTree" />
      </div>

      <!-- 能力雷达图 -->
      <div v-if="activeTab === 'radar'" class="card">
        <h3>四维能力对比</h3>
        <div class="simple-radar">
          <div v-for="(dim, idx) in progressData.radarData.dimensions" :key="dim" class="radar-dim">
            <span class="dim-label">{{ dim }}</span>
            <div class="dim-bar-bg">
              <div class="dim-bar-current" :style="{ width: progressData.radarData.current[idx] + '%' }"></div>
            </div>
            <span class="dim-score">{{ progressData.radarData.current[idx] }}</span>
            <div class="dim-bar-bg dim-bar-baseline">
              <div class="dim-bar-baseline-fill" :style="{ width: progressData.radarData.baseline[idx] + '%' }"></div>
            </div>
          </div>
        </div>
        <div class="radar-legend">
          <span class="legend-dot" style="background:var(--color-primary)"></span> 当前
          <span class="legend-dot" style="background:var(--color-border)"></span> 基线(60)
        </div>
      </div>

      <!-- 热力图 -->
      <div v-if="activeTab === 'heatmap'" class="card">
        <h3>学习热力图（近一年）</h3>
        <HeatmapCalendar :cells="progressData.heatmapCells" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.progress-page { max-width: 1000px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }
.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.tab-bar { display: flex; gap: 0; margin-bottom: 20px; border-bottom: 2px solid var(--color-border-light); }
.tab-bar button {
  padding: 10px 24px; font-size: var(--font-size-sm); color: var(--color-text-tertiary);
  border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all var(--transition-fast);
}
.tab-bar button.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 500; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 20px; }

.simple-radar { display: flex; flex-direction: column; gap: 14px; }
.radar-dim { display: flex; align-items: center; gap: 12px; }
.dim-label { width: 72px; font-size: var(--font-size-sm); text-align: right; }
.dim-bar-bg { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.dim-bar-baseline { height: 4px; margin-top: 2px; }
.dim-bar-current { height: 100%; background: var(--color-primary); border-radius: 4px; }
.dim-bar-baseline-fill { height: 100%; background: var(--color-border); border-radius: 2px; }
.dim-score { width: 36px; font-size: var(--font-size-sm); font-weight: 600; }
.radar-legend { display: flex; gap: 16px; font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 8px; }
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
</style>
