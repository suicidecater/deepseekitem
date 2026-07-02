// src/components/common/DataTable.vue
<script setup lang="ts" generic="T extends Record<string, any>">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  columns: { key: string; label: string; sortable?: boolean; width?: string }[]
  rows: T[]
  pageSize?: number
  loading?: boolean
}>(), { pageSize: 20, loading: false })

const emit = defineEmits<{ (e: 'sort', key: string, dir: 'asc' | 'desc'): void }>()

const currentPage = ref(1)
const sortKey = ref('')
const sortDir = ref<'asc' | 'desc'>('asc')

const totalPages = computed(() => Math.ceil(props.rows.length / props.pageSize))
const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  return props.rows.slice(start, start + props.pageSize)
})

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  emit('sort', sortKey.value, sortDir.value)
}

function goPage(p: number) {
  if (p >= 1 && p <= totalPages.value) currentPage.value = p
}
</script>

<template>
  <div class="data-table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key" :style="{ width: col.width }" @click="col.sortable ? toggleSort(col.key) : undefined" :class="{ sortable: col.sortable }">
            {{ col.label }}
            <span v-if="col.sortable && sortKey === col.key" class="sort-icon">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading"><td :colspan="columns.length" class="loading-cell">加载中...</td></tr>
        <tr v-else-if="rows.length === 0"><td :colspan="columns.length" class="empty-cell">暂无数据</td></tr>
        <tr v-for="(row, idx) in pagedRows" :key="idx">
          <td v-for="col in columns" :key="col.key">
            <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">{{ row[col.key] }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="currentPage === 1" @click="goPage(currentPage - 1)">上一页</button>
      <span v-for="p in totalPages" :key="p" class="page-num" :class="{ active: p === currentPage }" @click="goPage(p)">{{ p }}</span>
      <button :disabled="currentPage === totalPages" @click="goPage(currentPage + 1)">下一页</button>
      <span class="page-info">共 {{ rows.length }} 条</span>
    </div>
  </div>
</template>

<style scoped>
.data-table-wrapper { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.data-table th {
  background: #FAFAFA; padding: 12px 16px; text-align: left; font-weight: 600;
  border-bottom: 1px solid var(--color-border-light); user-select: none;
}
.data-table th.sortable { cursor: pointer; }
.data-table td { padding: 12px 16px; border-bottom: 1px solid var(--color-border-light); }
.sort-icon { font-size: 10px; margin-left: 4px; }
.loading-cell, .empty-cell { text-align: center; padding: 40px; color: var(--color-text-tertiary); }
.pagination { display: flex; align-items: center; justify-content: center; gap: 4px; padding: 12px; }
.pagination button { padding: 4px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); font-size: var(--font-size-xs); background: #fff; }
.pagination button:disabled { opacity: 0.4; }
.page-num { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-xs); }
.page-num.active { background: var(--color-primary); color: #fff; }
.page-info { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-left: 8px; }
</style>
