<script setup lang="ts">
// src/views/coach/StudentsView.vue - 学情管理
import { ref, onMounted } from 'vue'
import DataTable from '@/components/common/DataTable.vue'
import SearchFilter from '@/components/common/SearchFilter.vue'

const searchQuery = ref('')
const selectedStudent = ref<any>(null)
const loading = ref(false)

const stats = ref({ total: 35, active: 28, avgScore: 82, avgAccuracy: 78 })

interface StudentRow {
  id: number; name: string; phone: string; carType: string; score: number; accuracy: number; studyDays: number; lastActive: string
}

const students = ref<StudentRow[]>([
  { id: 1, name: '张三', phone: '138****5678', carType: 'C1', score: 88, accuracy: 85, studyDays: 45, lastActive: '2026-06-01' },
  { id: 2, name: '李四', phone: '139****1234', carType: 'C2', score: 72, accuracy: 68, studyDays: 30, lastActive: '2026-05-30' },
  { id: 3, name: '王五', phone: '137****9876', carType: 'C1', score: 95, accuracy: 92, studyDays: 60, lastActive: '2026-06-01' },
  { id: 4, name: '赵六', phone: '136****3456', carType: 'C1', score: 65, accuracy: 58, studyDays: 20, lastActive: '2026-05-25' },
  { id: 5, name: '陈七', phone: '135****7890', carType: 'C2', score: 80, accuracy: 76, studyDays: 38, lastActive: '2026-05-31' },
])

const columns = [
  { key: 'name', label: '姓名', sortable: true },
  { key: 'phone', label: '手机号' },
  { key: 'carType', label: '车型' },
  { key: 'score', label: '得分', sortable: true },
  { key: 'accuracy', label: '正确率', sortable: true },
  { key: 'studyDays', label: '学习天数', sortable: true },
  { key: 'lastActive', label: '最近活跃' },
]

const filteredStudents = ref(students.value)

function onSearch() {
  const q = searchQuery.value.toLowerCase()
  filteredStudents.value = students.value.filter(s => s.name.includes(q) || s.phone.includes(q))
}

function selectStudent(row: StudentRow) {
  selectedStudent.value = {
    ...row,
    dimensions: [
      { name: '交通标志', score: Math.floor(Math.random() * 40 + 50) },
      { name: '交通法规', score: Math.floor(Math.random() * 40 + 50) },
      { name: '安全常识', score: Math.floor(Math.random() * 40 + 50) },
      { name: '驾驶理论', score: Math.floor(Math.random() * 40 + 50) },
    ],
    weakTop5: ['高速限速', '交警手势', '扣分标准', '灯光使用', '优先通行'],
    examHistory: [
      { date: '05-01', score: 62 },
      { date: '05-15', score: 75 },
      { date: '05-28', score: 88 },
    ]
  }
}

function exportExcel() {
  alert('导出Excel功能（Mock）')
}

onMounted(() => {})
</script>

<template>
  <div class="students-page">
    <div class="page-header"><h2>学情管理</h2></div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card"><span class="stat-num">{{ stats.total }}</span><span class="stat-label">总学员</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.active }}</span><span class="stat-label">活跃学员</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.avgScore }}</span><span class="stat-label">平均得分</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.avgAccuracy }}%</span><span class="stat-label">平均正确率</span></div>
    </div>

    <!-- 搜索+导出 -->
    <div class="toolbar">
      <SearchFilter v-model="searchQuery" placeholder="搜索学员姓名/手机号..." @input="onSearch" />
      <button class="btn btn-outline" @click="exportExcel">导出Excel</button>
    </div>

    <!-- 表格 -->
    <DataTable :columns="columns" :rows="filteredStudents" :page-size="20" @row-click="selectStudent" />

    <!-- 学情详情面板 -->
    <div v-if="selectedStudent" class="detail-panel card">
      <h3>{{ selectedStudent.name }} - 学情详情</h3>
      <div class="detail-grid">
        <div class="detail-section">
          <h4>四维能力得分</h4>
          <div v-for="d in selectedStudent.dimensions" :key="d.name" class="dim-row">
            <span class="dim-name">{{ d.name }}</span>
            <div class="dim-bar"><div class="dim-fill" :style="{ width: d.score + '%', background: d.score < 60 ? '#FF4D4F' : '#1677FF' }"></div></div>
            <span class="dim-val">{{ d.score }}</span>
          </div>
        </div>
        <div class="detail-section">
          <h4>薄弱知识点 Top5</h4>
          <ol class="weak-list"><li v-for="w in selectedStudent.weakTop5" :key="w">{{ w }}</li></ol>
        </div>
        <div class="detail-section">
          <h4>模考记录</h4>
          <div v-for="e in selectedStudent.examHistory" :key="e.date" class="exam-row">
            <span>{{ e.date }}</span><span :class="e.score >= 90 ? 'pass' : 'fail'">{{ e.score }}分</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.students-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }

.detail-panel { margin-top: 20px; padding: 24px; }
.detail-panel h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }
.detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.detail-section h4 { font-size: var(--font-size-sm); margin-bottom: 10px; }
.dim-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: var(--font-size-xs); }
.dim-name { width: 64px; }
.dim-bar { flex: 1; height: 6px; background: #F0F0F0; border-radius: 3px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 3px; }
.dim-val { width: 28px; font-weight: 600; }
.weak-list { padding-left: 18px; font-size: var(--font-size-xs); }
.weak-list li { margin-bottom: 4px; }
.exam-row { display: flex; gap: 12px; font-size: var(--font-size-xs); margin-bottom: 4px; }
.pass { color: var(--color-success); font-weight: 600; }
.fail { color: var(--color-error); }
.card { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); }
</style>
