<script setup lang="ts">
// src/views/coach/StudentsView.vue - 学情管理（全面升级版）
import { ref, onMounted, computed, nextTick } from 'vue'
import { get } from '@/api/request'
import request from '@/api/request'
import DataTable from '@/components/common/DataTable.vue'
import SearchFilter from '@/components/common/SearchFilter.vue'
import AnalyticsCharts from '@/components/business/AnalyticsCharts.vue'
import PendingCoachingPanel from '@/components/business/PendingCoachingPanel.vue'
import CoachStudentDetail from '@/components/business/CoachStudentDetail.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ======================== 状态 ========================
const searchQuery = ref('')
const loading = ref(false)
const analyticsLoading = ref(false)
const pendingLoading = ref(false)
const autoRefreshTimer = ref<ReturnType<typeof setInterval> | null>(null)
const lastUpdateTime = ref('')

// 筛选
const carTypeFilter = ref('')
const accuracyRangeFilter = ref('')
const activeDaysFilter = ref<number>(0)
const pendingOnly = ref(false)

// ======================== 统计卡片（8个） ========================
const stats = ref({
  total: 0, active: 0, avgScore: 0, avgAccuracy: 0,
  pendingTutorCount: 0, unfinishedExamCount: 0, totalErrors: 0, topWeakDimension: '暂无',
})

async function fetchStats() {
  try {
    const res = await get('/api/coach/student-stat')
    if (res.data?.code === 0) {
      stats.value = { ...stats.value, ...res.data.data }
    }
  } catch { /* 保持默认值 */ }
}

// ======================== 全局分析图表 ========================
const analyticsData = ref({
  activeTrend: [] as { date: string; count: number }[],
  dimensionAvg: [] as { name: string; score: number }[],
  accuracyDistribution: [] as { range: string; count: number }[],
})

async function fetchAnalytics() {
  analyticsLoading.value = true
  try {
    const res = await get('/api/coach/student-analytics')
    if (res.data?.code === 0) {
      analyticsData.value = res.data.data
    }
  } catch { /* 保持默认 */ }
  finally { analyticsLoading.value = false }
}

// ======================== 待辅导学员 ========================
const pendingStudents = ref<any[]>([])
const pendingPanelCollapsed = ref(false)

async function fetchPendingStudents() {
  pendingLoading.value = true
  try {
    const res = await get('/api/coach/pending-coaching')
    if (res.data?.code === 0) {
      pendingStudents.value = res.data.data || []
    }
  } catch {
    pendingStudents.value = []
  }
  finally { pendingLoading.value = false }
}

// ======================== 学员表格 ========================
interface StudentRow {
  id: number
  name: string
  email: string
  carType: string
  score: number
  accuracy: number
  studyDays: number
  lastActive: string
  weakDimension: string
  weakDimensionScore: number
  pendingTags: string[]
}

const students = ref<StudentRow[]>([])
const selectedIds = ref<Set<number>>(new Set())

const columns = computed(() => [
  { key: 'name', label: '姓名', sortable: true },
  { key: 'email', label: '注册邮箱' },
  { key: 'carType', label: '车型', sortable: true },
  { key: 'score', label: '综合得分', sortable: true },
  { key: 'accuracy', label: '正确率', sortable: true },
  { key: 'studyDays', label: '学习天数', sortable: true },
  { key: 'weakDimension', label: '薄弱维度' },
  { key: 'pendingTags', label: '待处理提醒' },
  { key: 'actions', label: '操作' },
])

async function fetchStudents() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: 1,
      page_size: 999,
      keyword: searchQuery.value,
    }
    if (carTypeFilter.value) params.car_type = carTypeFilter.value
    if (accuracyRangeFilter.value) params.accuracy_range = accuracyRangeFilter.value
    if (activeDaysFilter.value > 0) params.active_days = activeDaysFilter.value
    if (pendingOnly.value) params.pending_only = '1'

    const res = await get('/api/coach/student-list', params)
    if (res.data?.code === 0) {
      students.value = res.data.data.list
    }
  } catch {
    students.value = []
  } finally {
    loading.value = false
  }
}

// ======================== 筛选 ========================
function onFilterChange() {
  fetchStudents()
}

function togglePendingOnly() {
  pendingOnly.value = !pendingOnly.value
  fetchStudents()
}

// ======================== 学员详情弹窗 ========================
const detailVisible = ref(false)
const detailLoading = ref(false)
const currentDetailStudent = ref<any>(null)
const detailData = ref({
  name: '', email: '', carType: '',
  dimensions: [] as { name: string; score: number }[],
  weakPoints: [] as string[],
  examHistory: [] as any[],
  trendData: [] as { date: string; accuracy: number; count: number }[],
  totalPracticeCount: 0,
  totalErrorCount: 0,
})

async function openStudentDetail(row: StudentRow) {
  detailVisible.value = true
  detailLoading.value = true
  currentDetailStudent.value = { id: row.id, name: row.name, email: row.email, carType: row.carType }

  try {
    const res = await get(`/api/coach/students/${row.id}`)
    if (res.data?.code === 0) {
      const d = res.data.data
      detailData.value = {
        name: row.name,
        email: row.email,
        carType: row.carType,
        dimensions: d.dimensions || [],
        weakPoints: d.weakPoints || [],
        examHistory: d.examHistory || [],
        trendData: d.trendData || [],
        totalPracticeCount: d.totalPracticeCount ?? 0,
        totalErrorCount: d.totalErrorCount ?? 0,
      }
    }
  } catch {
    detailData.value = {
      name: row.name, email: row.email, carType: row.carType,
      dimensions: [], weakPoints: [], examHistory: [], trendData: [],
      totalPracticeCount: 0, totalErrorCount: 0,
    }
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detailVisible.value = false
  detailData.value = {
    name: '', email: '', carType: '',
    dimensions: [], weakPoints: [], examHistory: [], trendData: [],
    totalPracticeCount: 0, totalErrorCount: 0,
  }
}

// ======================== 发起对话 ========================
function startChat(studentId: number) {
  router.push(`/coach/chat?student=${studentId}`)
}

// ======================== 待辅导面板操作 ========================
function onPendingViewDetail(id: number) {
  const s = students.value.find(st => st.id === id)
  if (s) openStudentDetail(s)
}

function onPendingSendMessage(id: number) {
  startChat(id)
}

// ======================== 导出功能 ========================
const showExportMenu = ref(false)
const exportType = ref<'all' | 'filtered'>('all')
const exportFields = ref(['basic', 'practice', 'exam', 'errors'])

function toggleExportMenu() {
  showExportMenu.value = !showExportMenu.value
}

async function doExport() {
  try {
    const params: Record<string, any> = {}
    if (exportType.value === 'filtered') {
      if (searchQuery.value) params.keyword = searchQuery.value
      if (carTypeFilter.value) params.car_type = carTypeFilter.value
      if (accuracyRangeFilter.value) params.accuracy_range = accuracyRangeFilter.value
    }
    if (exportFields.value.length > 0 && exportFields.value.length < 4) {
      params.export_fields = exportFields.value.join(',')
    }
    params.export_type = exportType.value

    const res = await request.get('/api/coach/export-student', {
      params,
      responseType: 'blob',
    })

    const disposition = res.headers['content-disposition'] || ''
    let filename = `学情管理_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`
    const match = disposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
    if (match) filename = decodeURIComponent(match[1].replace(/["\n]/g, ''))

    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    showExportMenu.value = false
  } catch (err: any) {
    const msg = err.response?.data?.message || err.message || '导出失败'
    alert(msg)
  }
}

// 导出单个学员
async function exportSingleStudent(id: number) {
  try {
    const res = await request.get(`/api/coach/export-student/${id}`, {
      responseType: 'blob',
    })
    const disposition = res.headers['content-disposition'] || ''
    let filename = `学员学情报告_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`
    const match = disposition.match(/filename\*?=(?:UTF-8'')?(.+)/i)
    if (match) filename = decodeURIComponent(match[1].replace(/["\n]/g, ''))
    const blob = new Blob([res.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = filename
    document.body.appendChild(a); a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    alert(err.message || '导出失败')
  }
}

// ======================== 数据刷新 ========================
function refreshAll() {
  fetchStats()
  fetchAnalytics()
  fetchStudents()
  fetchPendingStudents()
  lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN')
}

// 自动刷新（30秒）
function startAutoRefresh() {
  autoRefreshTimer.value = setInterval(refreshAll, 30000)
}

// ======================== 辅助 ========================
function getAccuracyColor(acc: number): string {
  if (acc >= 80) return 'var(--color-success)'
  if (acc >= 60) return 'var(--color-warning)'
  return 'var(--color-error)'
}

function formatAccuracy(val: any): string {
  const n = Number(val)
  return isNaN(n) ? '--' : n.toFixed(1) + '%'
}

// ======================== 生命周期 ========================
onMounted(() => {
  refreshAll()
  startAutoRefresh()
})

// 组件卸载时清除定时器（vue 3.5+ 可以用 onUnmounted）
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (autoRefreshTimer.value) clearInterval(autoRefreshTimer.value)
})
</script>

<template>
  <div class="students-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>学情管理</h2>
      <div class="header-right">
        <span v-if="lastUpdateTime" class="update-time">上次更新 {{ lastUpdateTime }}</span>
        <button class="btn btn-sm btn-outline" @click="refreshAll" title="刷新数据">
          🔄 刷新
        </button>
      </div>
    </div>

    <!-- ==================== 模块1：统计卡片（8个，两行） ==================== -->
    <div class="stats-section">
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ stats.total }}</span>
          <span class="stat-label">总学员</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.active }}</span>
          <span class="stat-label">近7天活跃</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.avgScore }}</span>
          <span class="stat-label">综合平均分</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ formatAccuracy(stats.avgAccuracy) }}</span>
          <span class="stat-label">平均正确率</span>
        </div>
        <div class="stat-card highlight-red" @click="togglePendingOnly" title="点击筛选待辅导学员">
          <span class="stat-num danger">{{ stats.pendingTutorCount }}</span>
          <span class="stat-label">⚠ 待辅导学员</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.unfinishedExamCount }}</span>
          <span class="stat-label">未完成考试</span>
        </div>
        <div class="stat-card">
          <span class="stat-num">{{ stats.totalErrors }}</span>
          <span class="stat-label">错题总量</span>
        </div>
        <div class="stat-card">
          <span class="stat-num weak">{{ stats.topWeakDimension }}</span>
          <span class="stat-label">薄弱题型 TOP1</span>
        </div>
      </div>
    </div>

    <!-- ==================== 模块2：全局分析图表 ==================== -->
    <AnalyticsCharts
      :active-trend="analyticsData.activeTrend"
      :dimension-avg="analyticsData.dimensionAvg"
      :accuracy-distribution="analyticsData.accuracyDistribution"
      :loading="analyticsLoading"
    />

    <!-- ==================== 模块3：筛选 + 搜索 + 导出 ==================== -->
    <div class="toolbar">
      <div class="toolbar-filters">
        <!-- 车型筛选 -->
        <select v-model="carTypeFilter" class="filter-select" @change="onFilterChange">
          <option value="">全部车型</option>
          <option value="C1">C1 小型汽车</option>
          <option value="C2">C2 小型自动挡</option>
          <option value="A1">A1 大型客车</option>
          <option value="A2">A2 牵引车</option>
          <option value="B1">B1 中型客车</option>
          <option value="B2">B2 大型货车</option>
        </select>

        <!-- 正确率区间 -->
        <select v-model="accuracyRangeFilter" class="filter-select" @change="onFilterChange">
          <option value="">全部正确率</option>
          <option value="0-60">0-60%（需关注）</option>
          <option value="60-80">60-80%（中等）</option>
          <option value="80-100">80-100%（优秀）</option>
        </select>

        <!-- 活跃时间 -->
        <select v-model="activeDaysFilter" class="filter-select" @change="onFilterChange">
          <option :value="0">全部活跃时间</option>
          <option :value="3">近3天</option>
          <option :value="7">近7天</option>
          <option :value="30">近30天</option>
        </select>

        <!-- 待辅导快捷筛选 -->
        <button
          class="filter-btn"
          :class="{ active: pendingOnly }"
          @click="togglePendingOnly"
        >
          {{ pendingOnly ? '✓ 仅待辅导' : '仅待辅导' }}
        </button>
      </div>

      <SearchFilter v-model="searchQuery" placeholder="搜索学员姓名/邮箱..." manual @search="fetchStudents" />

      <!-- 导出按钮（带菜单） -->
      <div class="export-wrapper">
        <button class="btn btn-outline" @click="toggleExportMenu">📥 导出Excel</button>
        <Transition name="fade">
          <div v-if="showExportMenu" class="export-menu card" @click.stop>
            <div class="export-menu-title">导出选项</div>
            <div class="export-option">
              <label>
                <input type="radio" v-model="exportType" value="all" /> 导出全部学员
              </label>
            </div>
            <div class="export-option">
              <label>
                <input type="radio" v-model="exportType" value="filtered" /> 仅导出筛选结果
              </label>
            </div>
            <div class="export-option-title">导出字段：</div>
            <div class="export-option">
              <label><input type="checkbox" v-model="exportFields" value="basic" /> 基础信息</label>
            </div>
            <div class="export-option">
              <label><input type="checkbox" v-model="exportFields" value="practice" /> 刷题记录</label>
            </div>
            <div class="export-option">
              <label><input type="checkbox" v-model="exportFields" value="exam" /> 考试记录</label>
            </div>
            <div class="export-option">
              <label><input type="checkbox" v-model="exportFields" value="errors" /> 错题明细</label>
            </div>
            <button class="btn btn-primary btn-block btn-sm" @click="doExport">确认导出</button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ==================== 模块4：学员表格 ==================== -->
    <div class="table-section">
      <DataTable :columns="columns" :rows="students" :loading="loading">
        <!-- 姓名列：可点击 -->
        <template #cell-name="{ row }">
          <span class="name-link" @click="openStudentDetail(row)">{{ row.name }}</span>
        </template>

        <!-- 正确率：带颜色 -->
        <template #cell-accuracy="{ row }">
          <span :style="{ color: getAccuracyColor(row.accuracy), fontWeight: 600 }">
            {{ formatAccuracy(row.accuracy) }}
          </span>
        </template>

        <!-- 薄弱维度 -->
        <template #cell-weakDimension="{ row }">
          <span v-if="row.weakDimension" class="weak-dim-tag">
            {{ row.weakDimension }} ({{ row.weakDimensionScore }}分)
          </span>
          <span v-else class="text-muted">--</span>
        </template>

        <!-- 待处理提醒 -->
        <template #cell-pendingTags="{ row }">
          <span v-if="row.pendingTags && row.pendingTags.length" class="tags-wrap">
            <span
              v-for="tag in row.pendingTags"
              :key="tag"
              class="tag"
              :class="tag === '待辅导' ? 'tag-red' : 'tag-orange'"
            >{{ tag }}</span>
          </span>
          <span v-else class="text-muted">正常</span>
        </template>

        <!-- 操作按钮 -->
        <template #cell-actions="{ row }">
          <div class="action-btns">
            <button class="action-link" @click="openStudentDetail(row)">查看详情</button>
            <button class="action-link" @click="startChat(row.id)">发起对话</button>
            <button class="action-link" @click="exportSingleStudent(row.id)">导出</button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- ==================== 模块5：待辅导快捷面板（右侧悬浮） ==================== -->
    <PendingCoachingPanel
      :students="pendingStudents"
      :loading="pendingLoading"
      v-model:collapsed="pendingPanelCollapsed"
      @view-detail="onPendingViewDetail"
      @send-message="onPendingSendMessage"
    />

    <!-- ==================== 学员详情弹窗 ==================== -->
    <CoachStudentDetail
      :visible="detailVisible"
      :loading="detailLoading"
      :student="currentDetailStudent"
      :dimensions="detailData.dimensions"
      :weak-points="detailData.weakPoints"
      :exam-history="detailData.examHistory"
      :trend-data="detailData.trendData"
      :total-practice-count="detailData.totalPracticeCount"
      :total-error-count="detailData.totalErrorCount"
      @close="closeDetail"
      @export="exportSingleStudent"
    />
  </div>
</template>

<style scoped>
/* ======================== 基础布局 ======================== */
.students-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  position: relative;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: var(--font-size-2xl);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.btn-sm {
  padding: 5px 12px;
  font-size: var(--font-size-xs);
}

/* ======================== 统计卡片 ======================== */
.stats-section {
  margin-bottom: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  padding: 18px 16px;
  text-align: center;
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-fast);
  cursor: default;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary-light);
}

.stat-card.highlight-red {
  cursor: pointer;
  border-color: #FFE7BA;
  background: #FFFBEB;
}

.stat-card.highlight-red:hover {
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.15);
  border-color: var(--color-error);
}

.stat-num {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1.3;
}

.stat-num.danger {
  color: var(--color-error);
}

.stat-num.weak {
  font-size: 16px;
  color: var(--color-warning);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
  display: block;
}

/* ======================== 工具栏 ======================== */
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.toolbar-filters {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select {
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  outline: none;
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  cursor: pointer;
  min-width: 120px;
}

.filter-select:focus {
  border-color: var(--color-primary);
}

.filter-btn {
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  background: var(--color-bg-white);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.filter-btn:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.filter-btn.active {
  background: var(--color-error);
  color: #fff;
  border-color: var(--color-error);
}

/* ======================== 导出菜单 ======================== */
.export-wrapper {
  position: relative;
  margin-left: auto;
}

.export-menu {
  position: absolute;
  right: 0;
  top: 42px;
  width: 240px;
  padding: 16px;
  background: var(--color-bg-white);
  box-shadow: var(--shadow-lg);
  z-index: 50;
}

.export-menu-title {
  font-weight: 600;
  font-size: var(--font-size-sm);
  margin-bottom: 10px;
}

.export-option,
.export-option-title {
  margin-bottom: 6px;
  font-size: var(--font-size-xs);
}

.export-option-title {
  color: var(--color-text-tertiary);
  margin-top: 10px;
}

.export-option label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.btn-sm {
  padding: 6px 14px;
  font-size: var(--font-size-xs);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ======================== 表格区域 ======================== */
.table-section {
  margin-bottom: 20px;
}

.name-link {
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 500;
}

.name-link:hover {
  text-decoration: underline;
}

.weak-dim-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #FFF7E6;
  color: var(--color-warning);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.tags-wrap {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

:deep(.tag-red) {
  background: #FFF2F0 !important;
  color: #FF4D4F !important;
  border: 1px solid #FFCCC7 !important;
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.action-btns {
  display: flex;
  gap: 8px;
}

.action-link {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 2px;
  transition: background var(--transition-fast);
}

.action-link:hover {
  background: var(--color-primary-light);
}

/* ======================== 响应式 ======================== */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .export-wrapper {
    margin-left: 0;
  }
}

@media (max-width: 600px) {
  .students-page {
    padding: 12px;
  }
  .stats-row {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }
  .stat-num {
    font-size: 20px;
  }
}
</style>
