<script setup lang="ts">
// src/views/student/ErrorBookView.vue - 错题本（重做做对自动删除）
import { ref, computed, onMounted } from 'vue'
import { getErrorBook, reviewError, type ErrorBookItem } from '@/api/modules/question'

const list = ref<ErrorBookItem[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterSubject = ref<number>(0)

const stats = ref({ total: 0, toReview: 0, reviewed: 0 })

// ===== 展开/答题 =====
const expandedId = ref<number | null>(null) // 展开的错误记录 errorId
const selectedAnswer = ref<Record<number, string>>({}) // errorId → answer
const submitting = ref<Record<number, boolean>>({})
const resultMap = ref<Record<number, { correct: boolean; correctAnswer: string }>>({})

const totalPages = computed(() => Math.ceil(total.value / pageSize))

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    const res: any = await getErrorBook({
      page: page.value,
      pageSize,
      subject: filterSubject.value || undefined,
    })
    const data = res.data?.data || res.data
    list.value = data?.list || []
    total.value = data?.total || 0
    stats.value = {
      total: data?.total || 0,
      toReview: data?.toReview || (data?.total || 0),
      reviewed: data?.reviewed || 0,
    }
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

// ===== 展开/折叠 =====
function toggleExpand(errId: number) {
  if (expandedId.value === errId) {
    expandedId.value = null
  } else {
    expandedId.value = errId
    resultMap.value[errId] = undefined as any
  }
}

// ===== 选择答案 =====
function selectAns(errId: number, ans: string) {
  selectedAnswer.value[errId] = ans
}

// ===== 提交重做 =====
async function submitReview(errId: number) {
  const ans = selectedAnswer.value[errId]
  if (!ans) return
  submitting.value[errId] = true
  try {
    const res: any = await reviewError({ errorId: errId, answer: ans })
    const data = res.data?.data || res.data
    if (data?.correct) {
      // 做对：前端立即移除
      list.value = list.value.filter(e => e.id !== errId)
      stats.value.total = Math.max(0, stats.value.total - 1)
      stats.value.toReview = Math.max(0, stats.value.toReview - 1)
    } else {
      // 做错：显示正确答案
      resultMap.value[errId] = { correct: false, correctAnswer: data?.correctAnswer || '' }
    }
  } catch {
    // ignore
  } finally {
    submitting.value[errId] = false
  }
}

// ===== 分页 =====
function goPage(p: number) {
  page.value = p
  expandedId.value = null
  loadData()
}
function changeSubject(sub: number) {
  filterSubject.value = sub
  page.value = 1
  expandedId.value = null
  loadData()
}

// 选项标签
const optionLabels = ['A', 'B', 'C', 'D']
function isExpanded(errId: number) { return expandedId.value === errId }
function isSelected(errId: number, label: string) { return selectedAnswer.value[errId] === label }
function getResult(errId: number) { return resultMap.value[errId] }

onMounted(loadData)
</script>

<template>
  <div class="error-book-page">
    <div class="page-header">
      <h2>错题本</h2>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-num">{{ stats.total }}</span>
        <span class="stat-label">总错题</span>
      </div>
      <div class="stat-card warn">
        <span class="stat-num">{{ stats.toReview }}</span>
        <span class="stat-label">待复习</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ stats.reviewed }}</span>
        <span class="stat-label">已复习</span>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <select class="filter-select" :value="filterSubject" @change="changeSubject(Number(($event.target as HTMLSelectElement).value))">
        <option :value="0">全部科目</option>
        <option :value="1">科目一</option>
        <option :value="4">科目四</option>
        <option :value="5">专业人员</option>
      </select>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="list.length === 0" class="empty-state">
      <p>暂无错题记录</p>
      <p class="empty-hint">完成练习、考试或专项训练后，错题会自动收集到这里</p>
    </div>

    <!-- 错题列表 -->
    <div v-else class="error-list">
      <div v-for="item in list" :key="item.id" class="error-item card">
        <div class="error-main">
          <div class="error-header">
            <span class="tag tag-blue">科目{{ item.source === 'subject1' ? '一' : item.source === 'subject4' ? '四' : '专' }}</span>
            <span class="tag tag-orange">{{ item.errorType }}</span>
          </div>
          <p class="error-question">{{ item.content }}</p>
          <div class="error-meta">
            <span>最近：{{ item.updateTime }}</span>
            <button class="btn-link" @click="toggleExpand(item.id)">
              {{ isExpanded(item.id) ? '收起' : '展开答题' }}
            </button>
          </div>

          <!-- 展开答题区 -->
          <div v-if="isExpanded(item.id)" class="expand-area">
            <div v-if="item.image" class="expand-image">
              <img :src="`/images/${item.image}`" alt="题目图片" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
            </div>
            <div class="expand-options">
              <label
                v-for="(opt, oi) in item.options" :key="oi"
                class="opt-label"
                :class="{
                  selected: isSelected(item.id, optionLabels[oi]),
                  correct: getResult(item.id) && optionLabels[oi] === getResult(item.id)?.correctAnswer,
                  wrong: getResult(item.id) && isSelected(item.id, optionLabels[oi]) && !getResult(item.id)?.correct,
                }"
              >
                <input
                  type="radio"
                  :name="'err-' + item.id"
                  :value="optionLabels[oi]"
                  :checked="isSelected(item.id, optionLabels[oi])"
                  :disabled="!!getResult(item.id)"
                  @change="selectAns(item.id, optionLabels[oi])"
                />
                <span>{{ opt }}</span>
              </label>
            </div>

            <div v-if="getResult(item.id) && !getResult(item.id)?.correct" class="review-result wrong-msg">
              回答错误，正确答案是 <strong>{{ getResult(item.id)?.correctAnswer }}</strong>，请继续加油！
            </div>

            <div class="expand-actions">
              <button
                class="btn btn-primary btn-sm"
                :disabled="!selectedAnswer[item.id] || submitting[item.id] || !!getResult(item.id)"
                @click="submitReview(item.id)"
              >
                {{ submitting[item.id] ? '提交中...' : '提交答案' }}
              </button>
              <button class="btn btn-outline btn-sm" @click="toggleExpand(item.id)">收起</button>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.error-book-page { max-width: 900px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

/* 统计 */
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: var(--radius-lg); padding: 20px; text-align: center; border: 1px solid var(--color-border-light); }
.stat-card.warn { border-color: var(--color-warning); background: #FFFBE6; }
.stat-card.success { border-color: var(--color-success); background: #F6FFED; }
.stat-num { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); }
.stat-card.warn .stat-num { color: var(--color-warning); }
.stat-card.success .stat-num { color: var(--color-success); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

/* 筛选 */
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.filter-select { padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: var(--font-size-sm); background: #fff; }

.loading, .empty-state { text-align: center; padding: 60px 0; color: var(--color-text-tertiary); }
.empty-hint { font-size: var(--font-size-xs); margin-top: 8px; }

/* 列表 */
.error-list { display: flex; flex-direction: column; gap: 12px; }
.error-item { display: flex; align-items: flex-start; gap: 16px; }
.error-main { flex: 1; min-width: 0; }
.error-header { display: flex; gap: 8px; margin-bottom: 8px; }
.error-question { font-size: var(--font-size-sm); margin-bottom: 6px; line-height: 1.6; }
.error-meta { display: flex; gap: 16px; font-size: var(--font-size-xs); color: var(--color-text-tertiary); align-items: center; }

/* 展开答题区 */
.expand-area { margin-top: 12px; padding: 16px; background: #FAFAFA; border-radius: var(--radius-md); border: 1px solid var(--color-border-light); }
.expand-image { text-align: center; margin-bottom: 12px; }
.expand-image img { max-width: 100%; max-height: 260px; border-radius: var(--radius-md); border: 1px solid var(--color-border-light); }
.expand-options { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.opt-label {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  border: 1px solid var(--color-border); border-radius: var(--radius-md);
  cursor: pointer; transition: all 0.15s; font-size: var(--font-size-sm);
}
.opt-label:hover { border-color: var(--color-primary); background: var(--color-primary-light); }
.opt-label.selected { border-color: var(--color-primary); background: #E6F4FF; }
.opt-label.correct { border-color: #52C41A; background: #F6FFED; }
.opt-label.wrong { border-color: #FF4D4F; background: #FFF1F0; }
.opt-label input { display: none; }

.review-result { padding: 8px 12px; border-radius: var(--radius-md); font-size: var(--font-size-sm); margin-bottom: 8px; }
.wrong-msg { background: #FFF1F0; color: #CF1322; }

.expand-actions { display: flex; gap: 8px; }

/* 分页 */
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 24px; }
.pagination button { padding: 6px 16px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: #fff; cursor: pointer; }
.pagination button:disabled { opacity: 0.4; cursor: not-allowed; }

/* 标签 */
.tag { font-size: var(--font-size-xs); padding: 2px 8px; border-radius: var(--radius-sm); }
.tag-blue { background: #E6F4FF; color: #1677FF; }
.tag-orange { background: #FFF7E6; color: #FA8C16; }
.tag-green { background: #F6FFED; color: #52C41A; }
.tag-gray { background: #F0F0F0; color: #666; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 16px 20px; border: 1px solid var(--color-border-light); }
.btn-sm { padding: 4px 12px; font-size: var(--font-size-xs); }
.btn-link { background: none; border: none; color: var(--color-primary); cursor: pointer; font-size: var(--font-size-xs); padding: 0; }
.btn-link:hover { text-decoration: underline; }
</style>
