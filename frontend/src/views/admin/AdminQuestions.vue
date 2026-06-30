<script setup lang="ts">
// src/views/admin/AdminQuestions.vue - 题库管理（三表CRUD）
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { useAppStore } from '@/stores/app'
import request from '@/api/request'

const appStore = useAppStore()

const questionSource = ref<'subject1' | 'subject4' | 'professional'>('subject1')
const sourceLabels: Record<string, string> = {
  subject1: '科目一题库', subject4: '科目四题库', professional: '专业人员题库',
}

interface Question {
  id: number; questionNumber: number; questionType: string; questionText: string
  optionA: string; optionB: string; optionC: string; optionD: string
  correctAnswer: string; imageFile: string | null; difficulty: number; source: string
}

const questions = ref<Question[]>([])
const totalQuestions = ref(0)
const currentPage = ref(1)
const pageSize = 20
const keyword = ref('')
const typeFilter = ref('')
const loadingQuestions = ref(false)

// 编辑弹窗
const showEditModal = ref(false)
const editForm = reactive({
  id: 0, questionNumber: 0, questionType: '判断题', questionText: '',
  optionA: '', optionB: '', optionC: '', optionD: '', correctAnswer: '',
  imageFile: '', difficulty: 1,
})
const isNew = ref(false)
const editSaving = ref(false)
const showDetail = ref<Question | null>(null)

async function loadQuestions() {
  loadingQuestions.value = true
  try {
    const qs = new URLSearchParams({
      page: String(currentPage.value),
      page_size: String(pageSize),
    })
    if (keyword.value) qs.set('keyword', keyword.value)
    if (typeFilter.value) qs.set('type', typeFilter.value)
    const res = await request.get(`/api/cms/questions/${questionSource.value}?${qs.toString()}`)
    const d = res.data
    if (d.code === 0 && d.data) {
      questions.value = d.data.list || []
      totalQuestions.value = d.data.pagination?.total || 0
    }
  } catch { appStore.showToast('加载题目失败', 'error') } finally { loadingQuestions.value = false }
}

function onSearch() { currentPage.value = 1; loadQuestions() }
function onPageChange(p: number) { currentPage.value = p; loadQuestions() }
watch(questionSource, () => { currentPage.value = 1; keyword.value = ''; typeFilter.value = ''; loadQuestions() })

function openAdd() {
  isNew.value = true
  Object.assign(editForm, {
    id: 0, questionNumber: 0, questionType: '判断题',
    questionText: '', optionA: '', optionB: '', optionC: '', optionD: '',
    correctAnswer: '', imageFile: '', difficulty: 1,
  })
  showEditModal.value = true
}

function openEdit(q: Question) {
  isNew.value = false
  Object.assign(editForm, {
    id: q.id, questionNumber: q.questionNumber, questionType: q.questionType,
    questionText: q.questionText, optionA: q.optionA || '', optionB: q.optionB || '',
    optionC: q.optionC || '', optionD: q.optionD || '',
    correctAnswer: q.correctAnswer, imageFile: q.imageFile || '', difficulty: q.difficulty,
  })
  showEditModal.value = true
}

async function saveEdit() {
  if (!editForm.questionText.trim() || !editForm.correctAnswer.trim()) {
    appStore.showToast('题干和正确答案不能为空', 'error'); return
  }
  editSaving.value = true
  try {
    const payload = {
      questionType: editForm.questionType, questionText: editForm.questionText.trim(),
      optionA: editForm.optionA, optionB: editForm.optionB, optionC: editForm.optionC, optionD: editForm.optionD,
      correctAnswer: editForm.correctAnswer.trim(), imageFile: editForm.imageFile || null,
      difficulty: editForm.difficulty, questionNumber: editForm.questionNumber,
    }
    if (isNew.value) {
      await request.post(`/api/cms/questions/${questionSource.value}`, payload)
      appStore.showToast('题目创建成功', 'success')
    } else {
      await request.put(`/api/cms/questions/${questionSource.value}/${editForm.id}`, payload)
      appStore.showToast('题目更新成功', 'success')
    }
    showEditModal.value = false
    loadQuestions()
  } catch { appStore.showToast('保存失败', 'error') } finally { editSaving.value = false }
}

async function deleteQuestion(q: Question) {
  if (!confirm(`确定删除题目 #${q.questionNumber}「${q.questionText.slice(0, 30)}...」？此操作不可恢复。`)) return
  try {
    await request.delete(`/api/cms/questions/${questionSource.value}/${q.id}`)
    appStore.showToast('删除成功', 'success')
    loadQuestions()
  } catch { appStore.showToast('删除失败', 'error') }
}

const jumpPage = ref('')
function onJumpPage() {
  const p = parseInt(jumpPage.value)
  if (isNaN(p) || p < 1 || p > totalPages()) {
    appStore.showToast(`请输入 1~${totalPages()} 之间的页码`, 'error')
    return
  }
  onPageChange(p)
}

const typeOptions = computed(() => {
  // 科目一只有判断题和单选题，科目四和专业人员有全部三种题型
  if (questionSource.value === 'subject1') return ['判断题', '单选题']
  return ['判断题', '单选题', '多选题']
})
const difficultyOptions = [1, 2, 3, 4, 5]
const totalPages = () => Math.ceil(totalQuestions.value / pageSize) || 1

onMounted(() => loadQuestions())
</script>

<template>
  <div class="questions-page">
    <div class="card">
      <div class="card-header">
        <h3>题库管理</h3>
      </div>

      <!-- 科目子标签 -->
      <div class="source-tabs">
        <button v-for="(label, key) in sourceLabels" :key="key"
          :class="{ active: questionSource === key }"
          @click="questionSource = key as any">{{ label }}</button>
      </div>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <input v-model="keyword" type="text" class="search-keyword" placeholder="输入题干关键词搜索..."
            @keyup.enter="onSearch" />
          <select v-model="typeFilter" class="search-type" @change="onSearch">
            <option value="">全部题型</option>
            <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
          </select>
          <button type="button" class="btn btn-primary btn-sm search-btn" @click="onSearch">搜索</button>
        </div>
        <div class="search-right">
          <button class="btn btn-primary btn-sm" @click="openAdd">+ 新增题目</button>
        </div>
      </div>

      <!-- 加载/空态 -->
      <div v-if="loadingQuestions" class="loading-hint">加载中...</div>
      <div v-else-if="questions.length === 0" class="empty-hint">暂无题目，点击"新增题目"添加</div>

      <!-- 表格 -->
      <table v-else class="question-table">
        <thead>
          <tr>
            <th style="width:60px">题号</th>
            <th>题干</th>
            <th style="width:80px">题型</th>
            <th style="width:70px">答案</th>
            <th style="width:60px">难度</th>
            <th style="width:130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in questions" :key="q.id">
            <td class="cell-center">{{ q.questionNumber }}</td>
            <td class="cell-text" @click="showDetail = q" title="点击查看详情">{{ q.questionText }}</td>
            <td class="cell-center">
              <span class="type-tag" :class="{
                'type-judge': q.questionType === '判断题',
                'type-single': q.questionType === '单选题',
                'type-multi': q.questionType === '多选题',
              }">{{ q.questionType }}</span>
            </td>
            <td class="cell-center answer-cell">{{ q.correctAnswer }}</td>
            <td class="cell-center"><span class="diff-tag" :class="'diff-' + q.difficulty">{{ '★'.repeat(q.difficulty) }}</span></td>
            <td class="cell-center">
              <button class="btn-action btn-edit" @click="openEdit(q)">编辑</button>
              <button class="btn-action btn-del" @click="deleteQuestion(q)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="totalQuestions > pageSize" class="pagination">
        <button :disabled="currentPage <= 1" @click="onPageChange(currentPage - 1)">上一页</button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages() }} 页（共 {{ totalQuestions }} 题）</span>
        <button :disabled="currentPage >= totalPages()" @click="onPageChange(currentPage + 1)">下一页</button>
        <span class="jump-input-wrap">
          跳至
          <input v-model="jumpPage" type="number" class="jump-input" :min="1" :max="totalPages()"
            placeholder="" @keyup.enter="onJumpPage" />
          页
        </span>
        <button class="btn-jump" @click="onJumpPage">跳转</button>
      </div>
    </div>

    <!-- ===== 编辑弹窗 ===== -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ isNew ? '新增题目 - ' + sourceLabels[questionSource] : '编辑题目 #' + editForm.questionNumber }}</h3>
          <button class="modal-close" @click="showEditModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group form-group-half">
              <label>题号</label>
              <input v-model.number="editForm.questionNumber" type="number" class="form-input" />
            </div>
            <div class="form-group form-group-half">
              <label>题型</label>
              <select v-model="editForm.questionType" class="form-input">
                <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>题干 <span class="required">*</span></label>
            <textarea v-model="editForm.questionText" class="form-input form-textarea" rows="3" placeholder="请输入题目内容"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group form-group-half"><label>选项 A</label><input v-model="editForm.optionA" class="form-input" /></div>
            <div class="form-group form-group-half"><label>选项 B</label><input v-model="editForm.optionB" class="form-input" /></div>
          </div>
          <div class="form-row">
            <div class="form-group form-group-half"><label>选项 C</label><input v-model="editForm.optionC" class="form-input" placeholder="判断题可留空" /></div>
            <div class="form-group form-group-half"><label>选项 D</label><input v-model="editForm.optionD" class="form-input" placeholder="判断题可留空" /></div>
          </div>
          <div class="form-row">
            <div class="form-group form-group-half">
              <label>正确答案 <span class="required">*</span></label>
              <input v-model="editForm.correctAnswer" class="form-input"
                :placeholder="editForm.questionType === '判断题' ? '对 / 错' : 'A/B/C/D 或多选如 AB'" />
            </div>
            <div class="form-group form-group-half">
              <label>难度</label>
              <select v-model.number="editForm.difficulty" class="form-input">
                <option v-for="d in difficultyOptions" :key="d" :value="d">{{ '★'.repeat(d) }} ({{ d }})</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>附图文件名</label>
            <input v-model="editForm.imageFile" class="form-input" placeholder="例如：T1-001.jpg（可选）" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showEditModal = false">取消</button>
          <button class="btn btn-primary" :disabled="editSaving" @click="saveEdit">{{ editSaving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- ===== 详情弹窗 ===== -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = null">
      <div class="modal-box modal-detail">
        <div class="modal-header">
          <h3>题目详情 #{{ showDetail.questionNumber }}</h3>
          <button class="modal-close" @click="showDetail = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="detail-field"><span class="detail-label">题型</span><span>{{ showDetail.questionType }}</span></div>
          <div class="detail-field"><span class="detail-label">难度</span><span>{{ '★'.repeat(showDetail.difficulty) }}</span></div>
          <div class="detail-field detail-block"><span class="detail-label">题干</span><span>{{ showDetail.questionText }}</span></div>
          <div class="detail-field" v-if="showDetail.optionA"><span class="detail-label">A</span><span>{{ showDetail.optionA }}</span></div>
          <div class="detail-field" v-if="showDetail.optionB"><span class="detail-label">B</span><span>{{ showDetail.optionB }}</span></div>
          <div class="detail-field" v-if="showDetail.optionC"><span class="detail-label">C</span><span>{{ showDetail.optionC }}</span></div>
          <div class="detail-field" v-if="showDetail.optionD"><span class="detail-label">D</span><span>{{ showDetail.optionD }}</span></div>
          <div class="detail-field detail-answer"><span class="detail-label">正确答案</span><span class="answer-text">{{ showDetail.correctAnswer }}</span></div>
          <div class="detail-field" v-if="showDetail.imageFile"><span class="detail-label">附图</span><span>{{ showDetail.imageFile }}</span></div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showDetail = null">关闭</button>
          <button class="btn btn-primary btn-sm" @click="showDetail = null; openEdit(showDetail!)">编辑</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.questions-page { max-width: 1100px; margin: 0 auto; padding: 24px; }
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

.question-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.question-table th { background: var(--color-bg); padding: 10px 8px; text-align: left; font-weight: 500; color: var(--color-text-secondary); border-bottom: 1px solid var(--color-border-light); }
.question-table td { padding: 10px 8px; border-bottom: 1px solid var(--color-border-light); }
.cell-center { text-align: center; vertical-align: middle; }
.cell-text { cursor: pointer; color: var(--color-primary); max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-text:hover { text-decoration: underline; }
.answer-cell { font-weight: 600; color: var(--color-success); font-family: 'Courier New', monospace; }

.type-tag { font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm); font-weight: 500; }
.type-judge { background: #FFF7E6; color: #FA8C16; }
.type-single { background: #E6F7FF; color: #1890FF; }
.type-multi { background: #F6FFED; color: #52C41A; }
.diff-tag { font-size: 14px; letter-spacing: 2px; }
.diff-1, .diff-2 { color: #52C41A; } .diff-3 { color: #FAAD14; } .diff-4, .diff-5 { color: #FF4D4F; }

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

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 1000; display: flex; justify-content: center; align-items: center; }
.modal-box { background: #fff; border-radius: var(--radius-lg); width: 640px; max-height: 85vh; overflow-y: auto; box-shadow: 0 8px 40px rgba(0,0,0,0.15); }
.modal-detail { width: 540px; }
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
.form-input { width: 100%; padding: 8px 12px; font-size: var(--font-size-sm); border: 1px solid var(--color-border); border-radius: var(--radius-md); box-sizing: border-box; }
.form-input:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 2px rgba(24,144,255,0.1); }
.form-textarea { resize: vertical; min-height: 60px; }
.detail-field { display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--color-border-light); font-size: var(--font-size-sm); }
.detail-label { min-width: 60px; color: var(--color-text-tertiary); font-weight: 500; flex-shrink: 0; }
.detail-block { flex-direction: column; gap: 4px; }
.detail-answer { background: #F6FFED; padding: 12px; border-radius: var(--radius-sm); border: none; }
.answer-text { font-weight: 700; color: var(--color-success); font-size: var(--font-size-base); }
.btn-sm { padding: 4px 14px; font-size: var(--font-size-xs); }
.btn-outline { background: transparent; color: var(--color-text); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 8px 20px; font-size: var(--font-size-sm); cursor: pointer; }
.btn-outline:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
