<script setup lang="ts">
// src/views/admin/AdminUsers.vue - 人员管理（学员/教练/管理员 CRUD）
import { ref, reactive, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import request from '@/api/request'

const appStore = useAppStore()

const userRole = ref<'student' | 'coach' | 'admin'>('student')
const roleLabels: Record<string, string> = {
  student: '学员', coach: '教练', admin: '管理员',
}

interface User {
  id: number; role: string; email: string; name: string; status: number
  trainType?: number; carType?: string; phone?: string; adminType?: number
}

const users = ref<User[]>([])
const totalUsers = ref(0)
const currentPage = ref(1)
const pageSize = 20
const keyword = ref('')
const statusFilter = ref<number | null>(null)
const loading = ref(false)

// 编辑弹窗
const showEditModal = ref(false)
const editForm = reactive({
  id: 0, email: '', password: '', name: '', status: 1,
  trainType: 1, carType: '', phone: '', adminType: 2,
})
const isNew = ref(false)
const editSaving = ref(false)

const trainTypeLabels: Record<number, string> = { 1: '驾考', 2: '客运', 3: '货运', 4: '危险品' }
const statusLabels: Record<number, string> = { 1: '正常', 2: '禁用' }
const studentStatusLabels: Record<number, string> = { 1: '正常', 2: '结业', 3: '弃学', 4: '禁用' }
const coachStatusLabels: Record<number, string> = { 1: '正常', 2: '离职', 3: '禁用' }
const adminTypeLabels: Record<number, string> = { 1: '超级管理员', 2: '内容管理员', 3: '运营管理员' }

function getStatusLabel(user: User) {
  if (user.role === 'student') return studentStatusLabels[user.status] || '未知'
  if (user.role === 'coach') return coachStatusLabels[user.status] || '未知'
  return statusLabels[user.status] || '未知'
}

async function loadUsers() {
  loading.value = true
  try {
    const qs = new URLSearchParams({ page: String(currentPage.value), page_size: String(pageSize) })
    if (keyword.value) qs.set('keyword', keyword.value)
    if (statusFilter.value !== null) qs.set('status', String(statusFilter.value))
    const res = await request.get(`/api/admin/users/${userRole.value}?${qs.toString()}`)
    const d = res.data
    if (d.code === 0 && d.data) {
      users.value = d.data.list || []
      totalUsers.value = d.data.pagination?.total || 0
    }
  } catch { appStore.showToast('加载失败', 'error') } finally { loading.value = false }
}

function onSearch() { currentPage.value = 1; loadUsers() }
function onPageChange(p: number) { currentPage.value = p; loadUsers() }
watch(userRole, () => { currentPage.value = 1; keyword.value = ''; statusFilter.value = null; loadUsers() })

function openAdd() {
  isNew.value = true
  Object.assign(editForm, {
    id: 0, email: '', password: '', name: '', status: 1,
    trainType: 1, carType: '', phone: '', adminType: 2,
  })
  showEditModal.value = true
}

function openEdit(u: User) {
  isNew.value = false
  Object.assign(editForm, {
    id: u.id, email: u.email, password: '', name: u.name || '',
    status: u.status, trainType: u.trainType || 1,
    carType: u.carType || '', phone: u.phone || '', adminType: u.adminType || 2,
  })
  showEditModal.value = true
}

async function saveEdit() {
  if (!editForm.email.trim()) { appStore.showToast('邮箱不能为空', 'error'); return }
  if (isNew.value && !editForm.password) { appStore.showToast('密码不能为空', 'error'); return }
  editSaving.value = true
  try {
    const payload: Record<string, any> = {
      email: editForm.email.trim(), status: editForm.status,
    }
    if (editForm.password) payload.password = editForm.password
    if (userRole.value === 'student') {
      payload.name = editForm.name; payload.trainType = editForm.trainType; payload.carType = editForm.carType
    } else if (userRole.value === 'coach') {
      payload.name = editForm.name; payload.trainType = editForm.trainType; payload.phone = editForm.phone
    } else {
      payload.adminType = editForm.adminType
    }
    if (isNew.value) {
      await request.post(`/api/admin/users/${userRole.value}`, payload)
      appStore.showToast('创建成功', 'success')
    } else {
      await request.put(`/api/admin/users/${userRole.value}/${editForm.id}`, payload)
      appStore.showToast('更新成功', 'success')
    }
    showEditModal.value = false
    loadUsers()
  } catch { appStore.showToast('保存失败', 'error') } finally { editSaving.value = false }
}

async function deleteUser(u: User) {
  if (!confirm(`确定删除 ${u.email} 吗？此操作不可恢复。`)) return
  try {
    await request.delete(`/api/admin/users/${userRole.value}/${u.id}`)
    appStore.showToast('删除成功', 'success')
    loadUsers()
  } catch { appStore.showToast('删除失败', 'error') }
}

const jumpPage = ref('')
function onJumpPage() {
  const p = parseInt(jumpPage.value)
  if (isNaN(p) || p < 1 || p > totalPages()) { appStore.showToast(`请输入 1~${totalPages()} 之间的页码`, 'error'); return }
  onPageChange(p)
}
const totalPages = () => Math.ceil(totalUsers.value / pageSize) || 1

onMounted(() => loadUsers())
</script>

<template>
  <div class="users-page">
    <div class="card">
      <div class="card-header"><h3>人员管理</h3></div>

      <!-- 角色子标签 -->
      <div class="source-tabs">
        <button v-for="(label, key) in roleLabels" :key="key"
          :class="{ active: userRole === key }"
          @click="userRole = key as any">{{ label }}</button>
      </div>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <input v-model="keyword" type="text" class="search-keyword" placeholder="搜索邮箱或姓名..."
            @keyup.enter="onSearch" />
          <select v-model="statusFilter" class="search-type" @change="onSearch">
            <option :value="null">全部状态</option>
            <option v-if="userRole==='student'" :value="1">正常</option>
            <option v-if="userRole==='student'" :value="4">禁用</option>
            <option v-if="userRole==='coach'" :value="1">正常</option>
            <option v-if="userRole==='admin'" :value="1">正常</option>
            <option :value="2">禁用/离职</option>
          </select>
          <button type="button" class="btn btn-primary btn-sm search-btn" @click="onSearch">搜索</button>
        </div>
        <div class="search-right">
          <button class="btn btn-primary btn-sm" @click="openAdd">+ 新增</button>
        </div>
      </div>

      <!-- 表格 -->
      <div v-if="loading" class="loading-hint">加载中...</div>
      <div v-else-if="users.length === 0" class="empty-hint">暂无数据</div>
      <table v-else class="user-table">
        <thead>
          <tr>
            <th style="width:60px">ID</th>
            <th>邮箱</th>
            <th v-if="userRole==='student'||userRole==='coach'" style="width:100px">名称</th>
            <th v-if="userRole==='student'">车型</th>
            <th v-if="userRole==='coach'">电话</th>
            <th v-if="userRole==='admin'">管理员类型</th>
            <th style="width:70px">状态</th>
            <th style="width:130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td class="cell-center">{{ u.id }}</td>
            <td>{{ u.email }}</td>
            <td v-if="userRole==='student'||userRole==='coach'" class="cell-center">
              {{ u.name || '-' }}
            </td>
            <td v-if="userRole==='student'" class="cell-center">{{ u.carType || '-' }}</td>
            <td v-if="userRole==='coach'" class="cell-center">{{ u.phone || '-' }}</td>
            <td v-if="userRole==='admin'" class="cell-center">{{ adminTypeLabels[u.adminType || 2] }}</td>
            <td class="cell-center">
              <span class="status-tag" :class="u.status === 1 ? 'status-normal' : 'status-off'">
                {{ getStatusLabel(u) }}
              </span>
            </td>
            <td class="cell-center">
              <button class="btn-action btn-edit" @click="openEdit(u)">编辑</button>
              <button class="btn-action btn-del" @click="deleteUser(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="totalUsers > pageSize" class="pagination">
        <button :disabled="currentPage <= 1" @click="onPageChange(currentPage - 1)">上一页</button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages() }} 页（共 {{ totalUsers }} 人）</span>
        <button :disabled="currentPage >= totalPages()" @click="onPageChange(currentPage + 1)">下一页</button>
        <span class="jump-input-wrap">
          跳至 <input v-model="jumpPage" type="number" class="jump-input" :min="1" :max="totalPages()"
            placeholder="" @keyup.enter="onJumpPage" /> 页
        </span>
        <button class="btn-jump" @click="onJumpPage">跳转</button>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ isNew ? '新增' + roleLabels[userRole] : '编辑 ' + editForm.email }}</h3>
          <button class="modal-close" @click="showEditModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>邮箱 <span class="required">*</span></label>
            <input v-model="editForm.email" class="form-input" placeholder="请输入邮箱" />
          </div>
          <div class="form-group">
            <label>密码 <span v-if="isNew" class="required">*</span><span v-else class="hint">（留空则不修改）</span></label>
            <input v-model="editForm.password" type="text" class="form-input" placeholder="请输入密码" />
          </div>
          <div class="form-group" v-if="userRole==='student'||userRole==='coach'">
            <label>{{ userRole === 'student' ? '姓名' : '驾校名称' }}</label>
            <input v-model="editForm.name" class="form-input" placeholder="请输入" />
          </div>
          <div class="form-row" v-if="userRole==='student'||userRole==='coach'">
            <div class="form-group form-group-half">
              <label>培训类型</label>
              <select v-model.number="editForm.trainType" class="form-input">
                <option v-for="(label, val) in trainTypeLabels" :key="val" :value="Number(val)">{{ label }}</option>
              </select>
            </div>
            <div class="form-group form-group-half" v-if="userRole==='student'">
              <label>车型</label>
              <template v-if="userRole==='student'">
                <input v-model="editForm.carType" class="form-input" placeholder="C1/C2/A1" />
              </template>
              <template v-if="userRole==='coach'">
                <input v-model="editForm.phone" class="form-input" placeholder="联系电话" />
              </template>
            </div>
          </div>
          <div class="form-row" v-if="userRole==='coach'&&!isNew">
            <div class="form-group form-group-half">
              <label>联系电话</label>
              <input v-model="editForm.phone" class="form-input" placeholder="驾校电话" />
            </div>
          </div>
          <div class="form-group" v-if="userRole==='admin'">
            <label>管理员类型</label>
            <select v-model.number="editForm.adminType" class="form-input">
              <option v-for="(label, val) in adminTypeLabels" :key="val" :value="Number(val)">{{ label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model.number="editForm.status" class="form-input">
              <template v-if="userRole==='student'">
                <option :value="1">正常</option>
                <option :value="4">禁用</option>
              </template>
              <template v-if="userRole==='coach'">
                <option :value="1">正常</option>
                <option :value="2">离职</option>
                <option :value="3">禁用</option>
              </template>
              <template v-if="userRole==='admin'">
                <option :value="1">正常</option>
                <option :value="2">禁用</option>
              </template>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" :disabled="editSaving" @click="saveEdit">{{ editSaving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.users-page { max-width: 1100px; margin: 0 auto; padding: 24px; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.card-header h3 { font-size: var(--font-size-lg); }

.source-tabs { display: flex; gap: 6px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-light); }
.source-tabs button { padding: 6px 18px; font-size: var(--font-size-sm); border-radius: var(--radius-md); background: var(--color-bg); color: var(--color-text-secondary); cursor: pointer; transition: all var(--transition-fast); }
.source-tabs button.active { background: var(--color-primary); color: #fff; font-weight: 500; }

.search-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 10px; }
.search-left { display: flex; align-items: center; gap: 8px; flex: 1; }
.search-keyword { width: 360px; padding: 8px 12px; font-size: var(--font-size-sm); border: 1px solid var(--color-border); border-radius: var(--radius-md); outline: none; }
.search-keyword:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(24,144,255,0.1); }
.search-type { width: 110px; padding: 8px 8px; font-size: var(--font-size-sm); border: 1px solid var(--color-border); border-radius: var(--radius-md); outline: none; background: #fff; cursor: pointer; }
.search-type:focus { border-color: var(--color-primary); }
.search-btn { height: 34px; white-space: nowrap; }
.search-right { flex-shrink: 0; }

.loading-hint { text-align: center; padding: 60px; color: var(--color-text-tertiary); }
.empty-hint { text-align: center; padding: 60px 20px; color: var(--color-text-tertiary); font-size: var(--font-size-sm); }

.user-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.user-table th { background: var(--color-bg); padding: 10px 8px; text-align: left; font-weight: 500; color: var(--color-text-secondary); border-bottom: 1px solid var(--color-border-light); }
.user-table td { padding: 10px 8px; border-bottom: 1px solid var(--color-border-light); }
.cell-center { text-align: center; vertical-align: middle; }

.status-tag { font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm); font-weight: 500; }
.status-normal { background: #F6FFED; color: #52C41A; }
.status-off { background: #FFF1F0; color: #FF4D4F; }

.btn-action { padding: 3px 10px; font-size: 12px; border-radius: var(--radius-sm); cursor: pointer; transition: all var(--transition-fast); }
.btn-edit { background: #E6F7FF; color: #1890FF; }
.btn-edit:hover { background: #BAE7FF; }
.btn-del { background: #FFF1F0; color: #FF4D4F; margin-left: 6px; }
.btn-del:hover { background: #FFCCC7; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 20px; }
.pagination button { padding: 6px 16px; font-size: var(--font-size-xs); border-radius: var(--radius-md); cursor: pointer; border: 1px solid var(--color-border); background: #fff; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.jump-input-wrap { font-size: var(--font-size-xs); color: var(--color-text-tertiary); display: flex; align-items: center; gap: 4px; white-space: nowrap; }
.jump-input { width: 50px; padding: 4px 8px; font-size: var(--font-size-xs); border: 1px solid var(--color-border); border-radius: var(--radius-sm); text-align: center; }
.jump-input:focus { border-color: var(--color-primary); outline: none; }
.btn-jump { padding: 6px 14px; font-size: var(--font-size-xs); border-radius: var(--radius-md); cursor: pointer; border: 1px solid var(--color-border); background: #fff; color: var(--color-text); }
.btn-jump:hover { border-color: var(--color-primary); color: var(--color-primary); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 1000; display: flex; justify-content: center; align-items: center; }
.modal-box { background: #fff; border-radius: var(--radius-lg); width: 520px; max-height: 85vh; overflow-y: auto; box-shadow: 0 8px 40px rgba(0,0,0,0.15); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--color-border-light); }
.modal-header h3 { font-size: var(--font-size-base); }
.modal-close { font-size: 18px; color: var(--color-text-tertiary); cursor: pointer; padding: 4px; border-radius: var(--radius-sm); }
.modal-close:hover { background: var(--color-bg); color: var(--color-text); }
.modal-body { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 12px 20px; border-top: 1px solid var(--color-border-light); }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 4px; }
.form-row { display: flex; gap: 16px; }
.form-group-half { flex: 1; }
.required { color: var(--color-error); }
.hint { font-weight: 400; color: var(--color-text-tertiary); font-size: 12px; }
.form-input { width: 100%; padding: 8px 12px; font-size: var(--font-size-sm); border: 1px solid var(--color-border); border-radius: var(--radius-md); box-sizing: border-box; }
.form-input:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 2px rgba(24,144,255,0.1); }
.btn-sm { padding: 4px 14px; font-size: var(--font-size-xs); }
.btn-outline { background: transparent; color: var(--color-text); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 8px 20px; font-size: var(--font-size-sm); cursor: pointer; }
.btn-outline:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
