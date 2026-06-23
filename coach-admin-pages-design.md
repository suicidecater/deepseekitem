# 教练端与管理端页面设计文档

> **版本**: V1.0 | **技术栈**: Vue 3 + ECharts 5 + TypeScript

---

## 一、教练端页面

### 1. 教练学情管理页 (CoachStudentsView)

#### 页面布局
```
┌──────────────────────────────────────────────────────┐
│  教练端 · 学情管理                    张教练         │
├──────────────────────────────────────────────────────┤
│  筛选： [按进度▼] [按正确率▼] [搜索学员...] [导出]   │
├──────────┬───────────────────────────────────────────┤
│ 学员列表  │  学员详情卡片                              │
│ ┌──────┐ │  ┌──────────────────────────────┐        │
│ │李同学 │ │  │ 李同学 · C1 · 报名3周         │        │
│ │85% ▲ │ │  │ 学习进度 ████████░░ 80%       │        │
│ ├──────┤ │  │ 总体正确率：85%                │        │
│ │王同学 │ │  │ 练习次数：42次                 │        │
│ │72%   │ │  │ 模拟考最高分：94分             │        │
│ ├──────┤ │  │                              │        │
│ │赵同学 │ │  │ 薄弱知识点：                  │        │
│ │58% ▼ │ │  │ · 交通标志（正确率62%）        │        │
│ └──────┘ │  │ · 扣分罚款（正确率55%）        │        │
│          │  │                              │        │
│          │  │ [查看详情] [AI辅导建议]        │        │
│          │  └──────────────────────────────┘        │
│          │                                          │
│          │  学习趋势图（折线图）                       │
│          │  ┌──────────────────────────────┐        │
│          │  │ 📈 近4周正确率趋势            │        │
│          │  └──────────────────────────────┘        │
└──────────┴───────────────────────────────────────────┘
```

#### 核心实现

```vue
<!-- src/views/coach/StudentsView.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from '@/components/common/DataTable.vue'
import DashboardChart from '@/components/business/DashboardChart.vue'
import { coachApi } from '@/api/modules/coach'

interface StudentInfo {
  id: number
  name: string
  carType: string
  progress: number
  correctRate: number
  practiceCount: number
  bestExamScore: number
  weakPoints: { name: string; rate: number }[]
  trend: { week: string; rate: number }[]
}

const students = ref<StudentInfo[]>([])
const selectedStudent = ref<StudentInfo | null>(null)
const loading = ref(false)

// 排序/筛选
const sortBy = ref<'progress' | 'correctRate'>('correctRate')
const sortOrder = ref<'asc' | 'desc'>('desc')
const searchKeyword = ref('')

const filteredStudents = computed(() => {
  let list = [...students.value]
  if (searchKeyword.value) {
    list = list.filter(s => s.name.includes(searchKeyword.value))
  }
  list.sort((a, b) => {
    const val = sortOrder.value === 'asc'
      ? a[sortBy.value] - b[sortBy.value]
      : b[sortBy.value] - a[sortBy.value]
    return val
  })
  return list
})

onMounted(async () => {
  loading.value = true
  const res = await coachApi.getMyStudents()
  students.value = res.data
  loading.value = false
})

function selectStudent(student: StudentInfo) {
  selectedStudent.value = student
}

// 导出数据
async function exportData() {
  const res = await coachApi.exportStudentsData()
  const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `学员数据_${new Date().toISOString().slice(0, 10)}.xlsx`
  a.click()
}

const router = useRouter()
function goToAiAdvice(studentId: number) {
  router.push({ name: 'CoachAiAdvice', query: { studentId } })
}

// 趋势图配置
const trendChartOption = computed(() => {
  if (!selectedStudent.value) return {}
  return {
    xAxis: {
      type: 'category',
      data: selectedStudent.value.trend.map(t => t.week)
    },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [{
      type: 'line',
      data: selectedStudent.value.trend.map(t => t.rate),
      smooth: true,
      itemStyle: { color: '#1677FF' },
      areaStyle: { color: 'rgba(22,119,255,0.1)' }
    }]
  }
})
</script>

<template>
  <div class="coach-students-page">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <select v-model="sortBy">
        <option value="correctRate">按正确率</option>
        <option value="progress">按进度</option>
      </select>
      <button @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'">
        {{ sortOrder === 'asc' ? '↑ 升序' : '↓ 降序' }}
      </button>
      <input v-model="searchKeyword" placeholder="搜索学员..." />
      <button class="btn btn-outline" @click="exportData">导出 Excel</button>
    </div>

    <div class="content-layout">
      <!-- 学员列表 -->
      <div class="student-list">
        <div
          v-for="student in filteredStudents"
          :key="student.id"
          class="student-item"
          :class="{ active: selectedStudent?.id === student.id }"
          @click="selectStudent(student)"
        >
          <div class="student-name">{{ student.name }}</div>
          <div class="student-rate" :class="student.correctRate >= 80 ? 'good' : student.correctRate >= 60 ? 'normal' : 'bad'">
            {{ student.correctRate }}%
          </div>
          <ProgressBar :percent="student.progress" :showText="false" height="4" />
        </div>
      </div>

      <!-- 学员详情 -->
      <div class="student-detail" v-if="selectedStudent">
        <div class="detail-card">
          <h3>{{ selectedStudent.name }} · {{ selectedStudent.carType }}</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">学习进度</span>
              <ProgressBar :percent="selectedStudent.progress" />
            </div>
            <div class="stat-item">
              <span class="stat-label">总体正确率</span>
              <span class="stat-value" :class="selectedStudent.correctRate >= 80 ? 'good' : 'normal'">
                {{ selectedStudent.correctRate }}%
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">练习次数</span>
              <span class="stat-value">{{ selectedStudent.practiceCount }}次</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">最高分</span>
              <span class="stat-value">{{ selectedStudent.bestExamScore }}分</span>
            </div>
          </div>

          <!-- 薄弱知识点 -->
          <div class="weak-section">
            <h4>薄弱知识点</h4>
            <div v-for="wp in selectedStudent.weakPoints" :key="wp.name" class="weak-item">
              <span>{{ wp.name }}</span>
              <span class="weak-rate" :class="wp.rate < 60 ? 'bad' : 'normal'">{{ wp.rate }}%</span>
            </div>
          </div>

          <div class="action-buttons">
            <button class="btn btn-primary" @click="goToAiAdvice(selectedStudent.id)">
              AI辅导建议
            </button>
          </div>
        </div>

        <!-- 趋势图 -->
        <div class="detail-card">
          <h4>学习趋势</h4>
          <DashboardChart type="line" :option="trendChartOption" height="260px" />
        </div>
      </div>

      <!-- 空状态 -->
      <EmptyState v-else description="请选择一位学员查看详情" />
    </div>
  </div>
</template>
```

---

### 2. AI教学辅导建议页 (CoachAiAdviceView)

```vue
<!-- src/views/coach/AiAdviceView.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { coachApi } from '@/api/modules/coach'

const route = useRoute()
const studentId = Number(route.query.studentId)

interface AIAdvice {
  studentName: string
  knowledgeGaps: { name: string; analysis: string }[]
  progressTrend: { period: string; description: string }
  suggestions: {
    keyKnowledge: string[]
    teachingMethods: string[]
    trainingPlan: { day: number; task: string }[]
  }
}

const advice = ref<AIAdvice | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  const res = await coachApi.getAIAdvice(studentId)
  advice.value = res.data
  loading.value = false
})
</script>

<template>
  <div class="ai-advice-page">
    <LoadingSpinner v-if="loading" />
    <template v-else-if="advice">
      <h2>{{ advice.studentName }} - AI教学辅导建议</h2>

      <!-- 知识短板分析 -->
      <section class="card">
        <h3>📊 知识短板分析</h3>
        <div v-for="gap in advice.knowledgeGaps" :key="gap.name" class="gap-item">
          <h4>{{ gap.name }}</h4>
          <p>{{ gap.analysis }}</p>
        </div>
      </section>

      <!-- 进步趋势 -->
      <section class="card">
        <h3>📈 进步趋势</h3>
        <p>{{ advice.progressTrend.description }}</p>
      </section>

      <!-- 辅导建议 -->
      <section class="card">
        <h3>💡 辅导建议</h3>
        <div class="suggestion-grid">
          <div>
            <h4>重点知识</h4>
            <ul>
              <li v-for="k in advice.suggestions.keyKnowledge" :key="k">{{ k }}</li>
            </ul>
          </div>
          <div>
            <h4>推荐教学方法</h4>
            <ul>
              <li v-for="m in advice.suggestions.teachingMethods" :key="m">{{ m }}</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- 专项训练方案 -->
      <section class="card">
        <h3>📋 专项训练方案</h3>
        <div v-for="plan in advice.suggestions.trainingPlan" :key="plan.day" class="plan-item">
          <span class="plan-day">第{{ plan.day }}天</span>
          <span>{{ plan.task }}</span>
        </div>
      </section>
    </template>
  </div>
</template>
```

---

## 二、管理端页面

### 3. 驾校管理后台 (AdminSchoolView)

#### 数据仪表盘

```vue
<!-- src/views/admin/SchoolView.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DashboardChart from '@/components/business/DashboardChart.vue'
import DataTable from '@/components/common/DataTable.vue'
import { adminApi } from '@/api/modules/admin'

interface DashboardData {
  overview: {
    totalStudents: number
    activeStudents: number
    avgCorrectRate: number
    passRate: number
  }
  scoreDistribution: { range: string; count: number }[]
  topWeakPoints: { name: string; errorRate: number; count: number }[]
}

const dashboard = ref<DashboardData | null>(null)

onMounted(async () => {
  const res = await adminApi.getSchoolDashboard()
  dashboard.value = res.data
})

// 成绩分布 - 柱状图
const scoreChartOption = computed(() => ({
  xAxis: { type: 'category', data: dashboard.value?.scoreDistribution.map(d => d.range) },
  yAxis: { type: 'value' },
  series: [{
    type: 'bar',
    data: dashboard.value?.scoreDistribution.map(d => d.count),
    itemStyle: {
      color: (params: any) => {
        const colors = ['#FF4D4F', '#FF7A45', '#FAAD14', '#73D13D', '#52C41A']
        return colors[params.dataIndex] || '#1677FF'
      }
    }
  }]
}))

// 批量布置任务
const taskForm = ref({
  studentIds: [] as number[],
  taskType: 'practice',
  count: 20,
  deadline: ''
})

async function assignTask() {
  await adminApi.assignBatchTask(taskForm.value)
  showToast({ message: '任务布置成功', type: 'success' })
}

// 导出报告
async function exportReport() {
  const res = await adminApi.exportReport()
  // 下载 Excel
}
</script>

<template>
  <div class="admin-school-page">
    <h2>驾校管理后台</h2>

    <!-- 核心指标卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">注册人数</span>
        <span class="kpi-value">{{ dashboard?.overview.totalStudents }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">活跃人数</span>
        <span class="kpi-value">{{ dashboard?.overview.activeStudents }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">平均正确率</span>
        <span class="kpi-value">{{ dashboard?.overview.avgCorrectRate }}%</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">通过率</span>
        <span class="kpi-value">{{ dashboard?.overview.passRate }}%</span>
      </div>
    </div>

    <div class="charts-row">
      <!-- 成绩分布 -->
      <div class="card">
        <h3>成绩分布统计</h3>
        <DashboardChart type="bar" :option="scoreChartOption" />
      </div>

      <!-- 薄弱知识点 TOP10 -->
      <div class="card">
        <h3>薄弱知识点 TOP10</h3>
        <DataTable
          :columns="[
            { key: 'name', title: '知识点' },
            { key: 'errorRate', title: '错误率', sortable: true },
            { key: 'count', title: '错误人次' }
          ]"
          :dataSource="dashboard?.topWeakPoints || []"
          rowKey="name"
        />
      </div>
    </div>

    <!-- 批量布置任务 -->
    <div class="card">
      <h3>批量布置学习任务</h3>
      <form @submit.prevent="assignTask">
        <!-- 任务表单 -->
        <button type="submit" class="btn btn-primary">布置任务</button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  margin-bottom: 24px;
}
.kpi-card {
  background: #fff; border-radius: var(--radius-lg);
  padding: 20px; text-align: center;
  border: 1px solid var(--color-border);
}
.kpi-label { font-size: 13px; color: var(--color-text-tertiary); }
.kpi-value { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); margin-top: 8px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
</style>
```

---

### 4. 运营管理平台 (AdminOperationView)

```vue
<script setup lang="ts">
import DashboardChart from '@/components/business/DashboardChart.vue'
import DataTable from '@/components/common/DataTable.vue'

// 运营数据看板
const dauTrendOption = {
  xAxis: { type: 'category', data: ['周一','周二','周三','周四','周五','周六','周日'] },
  yAxis: { type: 'value' },
  series: [
    { name: 'DAU', type: 'line', data: [120, 145, 132, 168, 175, 210, 195], smooth: true },
    { name: 'MAU', type: 'line', data: [850, 860, 875, 890, 905, 920, 935], smooth: true }
  ]
}

const passRatePieOption = {
  series: [{
    type: 'pie',
    radius: ['50%', '70%'],
    data: [
      { value: 82, name: '通过', itemStyle: { color: '#52C41A' } },
      { value: 18, name: '未通过', itemStyle: { color: '#FF4D4F' } }
    ]
  }]
}

// 账号管理
const accounts = ref([])

async function disableAccount(id: number) {
  // 二次确认
  const confirmed = await showConfirm('确定禁用该账号吗？')
  if (confirmed) {
    await adminApi.disableAccount(id)
    showToast({ message: '账号已禁用', type: 'success' })
  }
}
</script>
```

---

### 5. 内容管理系统 (AdminCMSView)

#### 多级审核流程
```
编辑提交 → 初审（教研组长） → 终审（内容总监） → 正式上线发布
```

```vue
<script setup lang="ts">
import { ref } from 'vue'
import DataTable from '@/components/common/DataTable.vue'
import FileUpload from '@/components/common/FileUpload.vue'
import ModalDialog from '@/components/common/ModalDialog.vue'

// 题库管理
const questionList = ref([])
const showUploadModal = ref(false)
const showEditModal = ref(false)

// 批量导入题目
async function handleBatchImport(files: File[]) {
  const formData = new FormData()
  formData.append('file', files[0])
  await adminApi.batchImportQuestions(formData)
  showToast({ message: '导入成功', type: 'success' })
}

// 审核流程
const reviewFlow = [
  { step: 1, name: '编辑', status: 'done' },
  { step: 2, name: '初审', status: 'pending' },
  { step: 3, name: '终审', status: 'pending' },
  { step: 4, name: '发布', status: 'pending' }
]

// 版本回滚
async function rollback(questionId: number, version: number) {
  await adminApi.rollbackQuestion(questionId, version)
  showToast({ message: '已回滚', type: 'success' })
}
</script>
```

---

## 三、API 接口示例

```typescript
// src/api/modules/coach.ts
export const coachApi = {
  getMyStudents: () =>
    http.get('/api/coach/students'),

  getStudentDetail: (id: number) =>
    http.get(`/api/coach/students/${id}`),

  exportStudentsData: () =>
    http.get('/api/coach/students/export', { responseType: 'blob' }),

  getAIAdvice: (studentId: number) =>
    http.post('/api/coach/ai-advice', { student_id: studentId })
}

// src/api/modules/admin.ts
export const adminApi = {
  getSchoolDashboard: () =>
    http.get('/api/admin/school/dashboard'),

  assignBatchTask: (params: any) =>
    http.post('/api/admin/school/tasks/batch', params),

  exportReport: () =>
    http.get('/api/admin/school/report/export', { responseType: 'blob' }),

  // 运营管理
  getOperationDashboard: () =>
    http.get('/api/admin/operation/dashboard'),

  createAccount: (params: any) =>
    http.post('/api/admin/accounts', params),

  disableAccount: (id: number) =>
    http.put(`/api/admin/accounts/${id}/disable`),

  // 内容管理
  batchImportQuestions: (formData: FormData) =>
    http.post('/api/admin/cms/questions/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  submitReview: (id: number, action: 'approve' | 'reject') =>
    http.post(`/api/admin/cms/review/${id}`, { action }),

  rollbackQuestion: (id: number, version: number) =>
    http.post(`/api/admin/cms/questions/${id}/rollback`, { version })
}
```

---

*本文档基于 SRS V1.0 教练端 2 项功能 + 管理端 3 项功能需求编写*
