<script setup lang="ts">
// src/views/admin/StudentCoachAssignment.vue - 学员教练分配管理
import { ref, reactive, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import request from '@/api/request'

const appStore = useAppStore()

// 教练列表
interface Coach {
  id: number; name: string; phone: string; status: number; studentsCount?: number
}
const coaches = ref<Coach[]>([])

// 学员列表
interface Student {
  id: number; email: string; name: string; status: number; trainType: number
  carType: string; coach_id: number | null; coach_name: string; coach_phone: string
}
const students = ref<Student[]>([])
const totalStudents = ref(0)
const currentPage = ref(1)
const pageSize = 20
const keyword = ref('')
const statusFilter = ref<number | null>(null)
const coachFilter = ref<number | null>(null) // 按教练筛选
const loading = ref(false)

// 分配弹窗
const showAssignModal = ref(false)
const targetStudent = ref<Student | null>(null)
const selectedCoachId = ref<number | null>(null)
const assignSaving = ref(false)

// 批量分配
const selectedStudentIds = ref<Set<number>>(new Set())
const selectAll = ref(false)

const trainTypeLabels: Record<number, string> = { 1: '驾考', 2: '客运', 3: '货运', 4: '危险品' }
const statusLabels: Record<number, string> = { 1: '正常', 2: '结业', 3: '弃学', 4: '禁用' }

// 可用教练（状态正常）
const availableCoaches = computed(() => coaches.value.filter(c => c.status === 1))

// 加载教练列表
async function loadCoaches() {
  try {
    const res = await request.get('/api/admin/users/coach?page=1&page_size=200')
    const d = res.data
    if (d.code === 0 && d.data) {
      coaches.value = (d.data.list || []).map((c: any) => ({
        id: c.id,
        name: c.name || '',
        phone: c.phone || '',
        status: c.status,
        studentsCount: 0,
      }))
    }
  } catch { /* 忽略 */ }
}

// 加载学员列表
async function loadStudents() {
  loading.value = true
  try {
    const qs = new URLSearchParams({ page: String(currentPage.value), page_size: String(pageSize) })
    if (keyword.value) qs.set('keyword', keyword.value)
    if (statusFilter.value !== null) qs.set('status', String(statusFilter.value))
    const res = await request.get(`/api/admin/users/student?${qs.toString()}`)
    const d = res.data
    if (d.code === 0 && d.data) {
      let list: Student[] = (d.data.list || []).map((s: any) => ({
        id: s.id,
        email: s.email || '',
        name: s.name || '',
        status: s.status,
        trainType: s.trainType,
        carType: s.carType || '',
        coach_id: s.coach_id ?? null,
        coach_name: s.coach_name || '未分配',
        coach_phone: s.coach_phone || '',
      }))
      // 按教练筛选
      if (coachFilter.value !== null) {
        list = list.filter(s => s.coach_id === coachFilter.value)
      }
      students.value = list
      totalStudents.value = d.data.pagination?.total || 0
      // 重置全选
      selectedStudentIds.value = new Set()
      selectAll.value = false
    }
  } catch { appStore.showToast('加载学员失败', 'error') } finally { loading.value = false }
}

function onSearch() { currentPage.value = 1; loadStudents() }
function onPageChange(p: number) { currentPage.value = p; loadStudents() }

// 打开分配弹窗
function openAssign(student: Student) {
  targetStudent.value = student
  selectedCoachId.value = student.coach_id
  showAssignModal.value = true
}

// 确认分配
async function confirmAssign() {
  if (!targetStudent.value || selectedCoachId.value === null && selectedCoachId.value !== targetStudent.value.coach_id === false) return
  
  // 检查是否有变化
  if (selectedCoachId.value === targetStudent.value.coach_id) {
    appStore.showToast('未修改教练', 'warning')
    showAssignModal.value = false
    return
  }

  assignSaving.value = true
  try {
    const res = await request.put(`/api/admin/users/student/${targetStudent.value.id}`, {
      coach_id: selectedCoachId.value,
    })
    const d = res.data
    if (d.code === 0) {
      appStore.showToast(
        selectedCoachId.value
          ? '教练分配成功'
          : '已取消教练分配',
        'success'
      )
      showAssignModal.value = false
      loadStudents()
    } else {
      appStore.showToast(d.message || '操作失败', 'error')
    }
  } catch {
    appStore.showToast('网络异常', 'error')
  } finally {
    assignSaving.value = false
  }
}

// 批量分配
const batchCoachId = ref<number | null>(null)
const showBatchModal = ref(false)
const batchSaving = ref(false)

function openBatchAssign() {
  if (selectedStudentIds.value.size === 0) {
    appStore.showToast('请先选择学员', 'warning')
    return
  }
  batchCoachId.value = availableCoaches.value[0]?.id || null
  showBatchModal.value = true
}

async function confirmBatchAssign() {
  if (selectedStudentIds.value.size === 0 || batchCoachId.value === null) return
  
  batchSaving.value = true
  let successCount = 0
  let failCount = 0

  try {
    const ids = Array.from(selectedStudentIds.value)
    for (const id of ids) {
      try {
        const res = await request.put(`/api/admin/users/student/${id}`, {
          coach_id: batchCoachId.value,
        })
        if (res.data?.code === 0) {
          successCount++
        } else {
          failCount++
        }
      } catch {
        failCount++
      }
    }
    appStore.showToast(`分配完成: 成功 ${successCount} 人${failCount > 0 ? `，失败 ${failCount} 人` : ''}`, failCount > 0 ? 'warning' : 'success')
    showBatchModal.value = false
    loadStudents()
  } catch {
    appStore.showToast('批量操作异常', 'error')
  } finally {
    batchSaving.value = false
  }
}

// 全选/取消全选
function toggleSelectAll() {
  selectAll.value = !selectAll.value
  if (selectAll.value) {
    selectedStudentIds.value = new Set(students.value.map(s => s.id))
  } else {
    selectedStudentIds.value = new Set()
  }
}

function toggleSelectStudent(id: number) {
  const newSet = new Set(selectedStudentIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  selectedStudentIds.value = newSet
  selectAll.value = newSet.size === students.value.length && students.value.length > 0
}

// 获取教练名称
function getCoachName(coachId: number | null) {
  if (!coachId) return '未分配'
  const coach = coaches.value.find(c => c.id === coachId)
  return coach?.name || `教练 #${coachId}`
}

// 初始化
onMounted(async () => {
  await loadCoaches()
  loadStudents()
})
</script>

<template>
  <div class="coach-assign-page">
    <div class="page-header">
      <h2>学员教练分配</h2>
      <p class="page-desc">管理学员与教练的分配关系</p>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索学员邮箱/姓名..."
          class="search-input"
          @keyup.enter="onSearch"
        />
        <select v-model="statusFilter" class="filter-select" @change="onSearch">
          <option :value="null">全部状态</option>
          <option :value="1">正常</option>
          <option :value="2">结业</option>
          <option :value="3">弃学</option>
          <option :value="4">禁用</option>
        </select>
        <select v-model="coachFilter" class="filter-select" @change="onSearch">
          <option :value="null">全部教练</option>
          <option :value="0">未分配</option>
          <option v-for="coach in availableCoaches" :key="coach.id" :value="coach.id">
            {{ coach.name }}
          </option>
        </select>
        <button class="btn btn-primary" @click="onSearch">搜索</button>
      </div>
      <div class="toolbar-right">
        <button
          class="btn btn-primary"
          :disabled="selectedStudentIds.size === 0"
          @click="openBatchAssign"
        >
          批量分配 ({{ selectedStudentIds.size }})
        </button>
      </div>
    </div>

    <!-- 学员列表表格 -->
    <div class="table-wrap">
      <table class="data-table" v-if="!loading">
        <thead>
          <tr>
            <th class="col-check">
              <input type="checkbox" :checked="selectAll" @change="toggleSelectAll" />
            </th>
            <th>ID</th>
            <th>姓名</th>
            <th>邮箱</th>
            <th>车型</th>
            <th>培训类型</th>
            <th>状态</th>
            <th>当前教练</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.id" :class="{ 'row-inactive': student.status !== 1 }">
            <td>
              <input
                type="checkbox"
                :checked="selectedStudentIds.has(student.id)"
                @change="toggleSelectStudent(student.id)"
              />
            </td>
            <td>{{ student.id }}</td>
            <td>{{ student.name || '-' }}</td>
            <td>{{ student.email }}</td>
            <td>{{ student.carType || '-' }}</td>
            <td>{{ trainTypeLabels[student.trainType] || '-' }}</td>
            <td>
              <span class="status-tag" :class="'status-' + student.status">
                {{ statusLabels[student.status] || '未知' }}
              </span>
            </td>
            <td>
              <span v-if="student.coach_id" class="coach-info">
                {{ student.coach_name }}
                <span class="coach-phone" v-if="student.coach_phone">{{ student.coach_phone }}</span>
              </span>
              <span v-else class="text-muted">未分配</span>
            </td>
            <td>
              <button class="btn btn-sm btn-outline" @click="openAssign(student)">
                {{ student.coach_id ? '更换教练' : '分配教练' }}
              </button>
            </td>
          </tr>
          <tr v-if="students.length === 0">
            <td colspan="9" class="empty-row">暂无数据</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalStudents > pageSize">
      <button
        :disabled="currentPage <= 1"
        @click="onPageChange(currentPage - 1)"
        class="btn btn-sm"
      >上一页</button>
      <span class="page-info">{{ currentPage }} / {{ Math.ceil(totalStudents / pageSize) }}</span>
      <button
        :disabled="currentPage >= Math.ceil(totalStudents / pageSize)"
        @click="onPageChange(currentPage + 1)"
        class="btn btn-sm"
      >下一页</button>
      <span class="total-info">共 {{ totalStudents }} 名学员</span>
    </div>

    <!-- 教练统计面板 -->
    <div class="coach-stats-panel">
      <h3>教练统计</h3>
      <div class="coach-stats-grid">
        <div
          v-for="coach in availableCoaches"
          :key="coach.id"
          class="coach-stat-card"
        >
          <div class="coach-stat-name">{{ coach.name }}</div>
          <div class="coach-stat-detail">{{ coach.phone || '暂无电话' }}</div>
          <div class="coach-stat-count">
            {{ students.filter(s => s.coach_id === coach.id).length }} 名在册学员
          </div>
        </div>
        <div v-if="availableCoaches.length === 0" class="empty-stats">暂无在职教练</div>
      </div>
    </div>

    <!-- 分配弹窗 -->
    <Teleport to="body">
      <div v-if="showAssignModal" class="modal-overlay" @click.self="showAssignModal = false">
        <div class="assign-modal">
          <div class="modal-header">
            <h3>{{ targetStudent?.coach_id ? '更换教练' : '分配教练' }}</h3>
            <p>
              学员：{{ targetStudent?.name || targetStudent?.email }}
              <span v-if="targetStudent?.coach_id">
                · 当前教练：{{ targetStudent?.coach_name }}
              </span>
            </p>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>选择教练</label>
              <select v-model="selectedCoachId" class="form-select">
                <option :value="null">取消分配（不指定教练）</option>
                <option
                  v-for="coach in availableCoaches"
                  :key="coach.id"
                  :value="coach.id"
                >
                  {{ coach.name }} {{ coach.phone ? '(' + coach.phone + ')' : '' }}
                </option>
              </select>
            </div>
            <div v-if="selectedCoachId" class="assign-preview">
              <span class="preview-label">将分配至：</span>
              <strong>{{ getCoachName(selectedCoachId) }}</strong>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn" @click="showAssignModal = false">取消</button>
            <button
              class="btn btn-primary"
              :disabled="assignSaving || selectedCoachId === targetStudent?.coach_id"
              @click="confirmAssign"
            >
              {{ assignSaving ? '保存中...' : '确认分配' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 批量分配弹窗 -->
    <Teleport to="body">
      <div v-if="showBatchModal" class="modal-overlay" @click.self="showBatchModal = false">
        <div class="assign-modal">
          <div class="modal-header">
            <h3>批量分配教练</h3>
            <p>已选择 {{ selectedStudentIds.size }} 名学员</p>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>统一分配至教练</label>
              <select v-model="batchCoachId" class="form-select">
                <option
                  v-for="coach in availableCoaches"
                  :key="coach.id"
                  :value="coach.id"
                >
                  {{ coach.name }} {{ coach.phone ? '(' + coach.phone + ')' : '' }}
                </option>
              </select>
            </div>
            <div class="batch-warning" v-if="selectedStudentIds.size > 5">
              ⚠️ 将一次性分配 {{ selectedStudentIds.size }} 名学员
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn" @click="showBatchModal = false">取消</button>
            <button
              class="btn btn-primary"
              :disabled="batchSaving || !batchCoachId"
              @click="confirmBatchAssign"
            >
              {{ batchSaving ? '分配中...' : '确认批量分配' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.coach-assign-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.page-desc {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.search-input {
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  width: 220px;
  outline: none;
  transition: border-color var(--transition-fast);
}
.search-input:focus { border-color: var(--color-primary); }
.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: #fff;
  outline: none;
}

/* 表格 */
.table-wrap {
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-align: left;
  background: #FAFAFA;
  border-bottom: 1px solid var(--color-border-light);
  white-space: nowrap;
}
.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  border-bottom: 1px solid #F5F5F5;
  color: var(--color-text-primary);
}
.data-table tbody tr.row-inactive {
  opacity: 0.55;
}
.data-table tbody tr:hover {
  background: #F9FBFF;
}
.col-check { width: 40px; }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.status-1 { background: #E6F7FF; color: #1677FF; }
.status-2 { background: #F6FFED; color: #52C41A; }
.status-3 { background: #FFF7E6; color: #FA8C16; }
.status-4 { background: #FFF1F0; color: #FF4D4F; }

.coach-info { color: var(--color-primary); font-weight: 500; }
.coach-phone { color: var(--color-text-tertiary); margin-left: 6px; font-weight: 400; font-size: 12px; }
.text-muted { color: var(--color-text-tertiary); }

.empty-row {
  text-align: center;
  padding: 40px !important;
  color: var(--color-text-tertiary);
}

/* 加载 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  gap: 12px;
  color: var(--color-text-tertiary);
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  justify-content: center;
}
.page-info {
  font-size: 14px;
  color: var(--color-text-secondary);
}
.total-info {
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-left: 8px;
}

/* 教练统计面板 */
.coach-stats-panel {
  margin-top: 32px;
  padding: 20px;
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}
.coach-stats-panel h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text-primary);
}
.coach-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.coach-stat-card {
  padding: 14px;
  border-radius: var(--radius-md);
  background: #F9FBFF;
  border: 1px solid var(--color-border-light);
}
.coach-stat-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.coach-stat-detail {
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}
.coach-stat-count {
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 500;
  margin-top: 6px;
}
.empty-stats {
  padding: 20px;
  text-align: center;
  color: var(--color-text-tertiary);
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.assign-modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  width: 460px;
  max-width: 90vw;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.25s ease;
}
@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.modal-header {
  margin-bottom: 20px;
}
.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.modal-header p {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-top: 6px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}
.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: #fff;
  outline: none;
}
.form-select:focus { border-color: var(--color-primary); }
.assign-preview {
  padding: 12px;
  background: #E6F4FF;
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--color-primary);
}
.preview-label { color: var(--color-text-secondary); }
.batch-warning {
  padding: 10px 14px;
  background: #FFF7E6;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: #AD6800;
  margin-top: 8px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}

/* 通用按钮 */
.btn {
  padding: 8px 18px;
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  border: 1px solid var(--color-border);
  background: #fff;
  color: var(--color-text-primary);
  transition: all var(--transition-fast);
}
.btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.btn-primary:hover { opacity: 0.9; color: #fff; }
.btn-outline {
  background: #fff;
  color: var(--color-primary);
  border-color: var(--color-primary);
}
.btn-outline:hover { background: var(--color-primary-light); }
.btn-sm { padding: 4px 12px; font-size: 13px; }
</style>
