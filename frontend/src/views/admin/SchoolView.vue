<script setup lang="ts">
// src/views/admin/SchoolView.vue - 驾校管理后台
import { ref } from 'vue'
import DataTable from '@/components/common/DataTable.vue'

const stats = ref({ totalStudents: 128, avgScore: 82, passRate: 78, activeRate: 85 })

const scoreDistribution = ref([
  { range: '0-60', count: 15, color: '#FF4D4F' },
  { range: '60-75', count: 28, color: '#FAAD14' },
  { range: '75-90', count: 45, color: '#1677FF' },
  { range: '90-100', count: 40, color: '#52C41A' },
])

const weakTop10 = ref([
  { name: '高速限速规定', errorRate: 72 },
  { name: '交警手势信号', errorRate: 68 },
  { name: '扣分罚款标准', errorRate: 65 },
  { name: '灯光使用规范', errorRate: 58 },
  { name: '优先通行规则', errorRate: 55 },
  { name: '安全距离判断', errorRate: 52 },
  { name: '恶劣天气驾驶', errorRate: 48 },
  { name: '紧急情况处理', errorRate: 45 },
  { name: '交通标志识别', errorRate: 42 },
  { name: '超车变道规则', errorRate: 38 },
])

const tasks = ref([
  { id: 1, title: '新增科目一题库200题', assignee: '管理员A', status: '进行中', dueDate: '2026-06-15' },
  { id: 2, title: '审核学员注册信息', assignee: '管理员B', status: '待处理', dueDate: '2026-06-10' },
  { id: 3, title: '更新交通法规知识点', assignee: '管理员A', status: '已完成', dueDate: '2026-06-05' },
])

const taskColumns = [
  { key: 'title', label: '任务名称' },
  { key: 'assignee', label: '负责人' },
  { key: 'status', label: '状态' },
  { key: 'dueDate', label: '截止日期' },
]

function exportReport() { alert('导出报告（Mock）') }
</script>

<template>
  <div class="school-page">
    <div class="page-header"><h2>驾校管理后台</h2></div>

    <!-- 仪表盘 -->
    <div class="stats-row">
      <div class="stat-card" v-for="(v,k) in { '总学员': stats.totalStudents, '平均得分': stats.avgScore, '通过率': stats.passRate + '%', '活跃率': stats.activeRate + '%' }" :key="k">
        <span class="stat-num">{{ v }}</span><span class="stat-label">{{ k }}</span>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- 成绩分布 -->
      <div class="card">
        <h3>成绩分布</h3>
        <div class="bar-chart">
          <div v-for="item in scoreDistribution" :key="item.range" class="bar-item">
            <span class="bar-label">{{ item.range }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: (item.count / 45) * 100 + '%', background: item.color }"></div></div>
            <span class="bar-count">{{ item.count }}人</span>
          </div>
        </div>
      </div>

      <!-- 薄弱Top10 -->
      <div class="card">
        <h3>薄弱知识点 Top10</h3>
        <div class="weak-list">
          <div v-for="(w, idx) in weakTop10" :key="w.name" class="weak-row">
            <span class="weak-rank">{{ idx + 1 }}</span>
            <span class="weak-name">{{ w.name }}</span>
            <span class="weak-rate">{{ w.errorRate }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量任务 -->
    <div class="card">
      <div class="card-header"><h3>批量任务列表</h3><button class="btn btn-primary btn-sm">新建任务</button></div>
      <DataTable :columns="taskColumns" :rows="tasks" :page-size="10" />
    </div>

    <div class="actions"><button class="btn btn-primary" @click="exportReport">导出驾校报告</button></div>
  </div>
</template>

<style scoped>
.school-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 14px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-header h3 { margin-bottom: 0; }

.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-item { display: flex; align-items: center; gap: 8px; font-size: var(--font-size-xs); }
.bar-label { width: 48px; }
.bar-track { flex: 1; height: 16px; background: #F0F0F0; border-radius: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 8px; transition: width 0.6s; }
.bar-count { width: 36px; text-align: right; color: var(--color-text-secondary); }

.weak-list { display: flex; flex-direction: column; gap: 6px; }
.weak-row { display: flex; align-items: center; gap: 8px; font-size: var(--font-size-xs); }
.weak-rank { width: 20px; text-align: center; font-weight: 700; color: var(--color-primary); }
.weak-name { flex: 1; }
.weak-rate { width: 36px; text-align: right; color: var(--color-error); font-weight: 600; }

.actions { margin-top: 20px; text-align: right; }
.btn-sm { padding: 4px 14px; font-size: var(--font-size-xs); }
</style>
