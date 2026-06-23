<script setup lang="ts">
// src/views/admin/OperationView.vue - 运营管理平台
import { ref } from 'vue'
import DataTable from '@/components/common/DataTable.vue'

const stats = ref({ totalUsers: 2560, dau: 420, mau: 1850, retention: 68 })

const dauTrend = ref([32,38,45,40,48,42,35,52,58,55,60,65,70,68])
const trendMax = Math.max(...dauTrend.value)

const schoolData = ref([
  { name: '安达驾校', students: 320, passRate: 82, activeRate: 75 },
  { name: '通达驾校', students: 280, passRate: 78, activeRate: 72 },
  { name: '平安驾校', students: 250, passRate: 85, activeRate: 80 },
  { name: '顺达驾校', students: 200, passRate: 76, activeRate: 68 },
  { name: '飞驰驾校', students: 180, passRate: 80, activeRate: 73 },
])

const schoolColumns = [
  { key: 'name', label: '驾校名称' },
  { key: 'students', label: '学员数', sortable: true },
  { key: 'passRate', label: '通过率', sortable: true },
  { key: 'activeRate', label: '活跃率', sortable: true },
]

const passRates = ref({ subject1: 88, subject4: 82 })
</script>

<template>
  <div class="operation-page">
    <div class="page-header"><h2>运营管理平台</h2></div>

    <!-- 核心指标 -->
    <div class="stats-row">
      <div class="stat-card"><span class="stat-num">{{ stats.totalUsers }}</span><span class="stat-label">总用户</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.dau }}</span><span class="stat-label">DAU</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.mau }}</span><span class="stat-label">MAU</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.retention }}%</span><span class="stat-label">留存率</span></div>
    </div>

    <div class="dashboard-grid">
      <!-- DAU趋势 -->
      <div class="card">
        <h3>DAU趋势（近14天）</h3>
        <div class="trend-chart">
          <div v-for="(v, idx) in dauTrend" :key="idx" class="trend-bar" :style="{ height: (v / trendMax) * 100 + '%' }">
            <span class="trend-val">{{ v }}</span>
          </div>
        </div>
      </div>

      <!-- 通过率 -->
      <div class="card">
        <h3>考试通过率</h3>
        <div class="pass-rates">
          <div class="pass-item">
            <span>科目一</span>
            <div class="pass-bar"><div class="pass-fill" :style="{ width: passRates.subject1 + '%', background: '#1677FF' }"></div></div>
            <span class="pass-val">{{ passRates.subject1 }}%</span>
          </div>
          <div class="pass-item">
            <span>科目四</span>
            <div class="pass-bar"><div class="pass-fill" :style="{ width: passRates.subject4 + '%', background: '#52C41A' }"></div></div>
            <span class="pass-val">{{ passRates.subject4 }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 驾校分布 -->
    <div class="card">
      <h3>驾校分布</h3>
      <DataTable :columns="schoolColumns" :rows="schoolData" :page-size="10" />
    </div>
  </div>
</template>

<style scoped>
.operation-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 14px; }

.trend-chart { display: flex; align-items: flex-end; gap: 6px; height: 120px; padding-top: 20px; }
.trend-bar { flex: 1; background: var(--color-primary); border-radius: 4px 4px 0 0; position: relative; transition: height 0.4s; min-width: 12px; }
.trend-val { position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--color-text-secondary); }

.pass-rates { display: flex; flex-direction: column; gap: 16px; }
.pass-item { display: flex; align-items: center; gap: 10px; font-size: var(--font-size-sm); }
.pass-bar { flex: 1; height: 24px; background: #F0F0F0; border-radius: 12px; overflow: hidden; }
.pass-fill { height: 100%; border-radius: 12px; transition: width 0.6s; display: flex; align-items: center; justify-content: center; color: #fff; font-size: var(--font-size-xs); }
.pass-val { width: 40px; font-weight: 600; }
</style>
