<script setup lang="ts">
// src/views/admin/CMSView.vue - 内容管理系统
import { ref } from 'vue'
import DataTable from '@/components/common/DataTable.vue'

const activeTab = ref<'questions' | 'review' | 'knowledge'>('questions')

const questions = ref([
  { id: 1, content: '在高速公路上遇到紧急情况...', subject: 1, type: 'single', status: 'online', author: '管理员A' },
  { id: 2, content: '这个标志表示什么含义？', subject: 1, type: 'single', status: 'draft', author: '管理员B' },
  { id: 3, content: '夜间会车应当在...', subject: 1, type: 'single', status: 'reviewing', author: '管理员A' },
  { id: 4, content: '以下哪些属于危险驾驶行为？', subject: 1, type: 'multiple', status: 'rejected', author: '管理员C' },
])

const reviewList = ref([
  { id: 1, content: '新增题目：交通标志合集', submitter: '编辑A', time: '2026-06-01', status: 'reviewing' },
  { id: 2, content: '修改知识点：高速限速', submitter: '编辑B', time: '2026-05-30', status: 'reviewing' },
])

const knowledgeList = ref([
  { id: 1, name: '交通标志', questionCount: 120, status: 'online', editor: '管理员A' },
  { id: 2, name: '交通法规', questionCount: 200, status: 'online', editor: '管理员B' },
  { id: 3, name: '安全常识', questionCount: 80, status: 'draft', editor: '管理员A' },
])

const qColumns = [
  { key: 'content', label: '题目内容' },
  { key: 'subject', label: '科目' },
  { key: 'type', label: '题型' },
  { key: 'status', label: '状态' },
  { key: 'author', label: '作者' },
]

const reviewColumns = [
  { key: 'content', label: '变更内容' },
  { key: 'submitter', label: '提交人' },
  { key: 'time', label: '时间' },
  { key: 'status', label: '状态' },
]

const kColumns = [
  { key: 'name', label: '知识点' },
  { key: 'questionCount', label: '题目数' },
  { key: 'status', label: '状态' },
  { key: 'editor', label: '编辑者' },
]

const statusLabels: Record<string, string> = { draft: '草稿', reviewing: '待审核', online: '已上线', rejected: '驳回' }
const statusColors: Record<string, string> = { draft: 'tag-gray', reviewing: 'tag-orange', online: 'tag-green', rejected: 'tag-red' }
</script>

<template>
  <div class="cms-page">
    <div class="page-header"><h2>内容管理系统</h2></div>

    <!-- Tab -->
    <div class="cms-tabs">
      <button :class="{ active: activeTab === 'questions' }" @click="activeTab = 'questions'">题库管理</button>
      <button :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'">审核中心</button>
      <button :class="{ active: activeTab === 'knowledge' }" @click="activeTab = 'knowledge'">知识点管理</button>
    </div>

    <!-- 题库管理 -->
    <div v-if="activeTab === 'questions'" class="card">
      <div class="card-header"><h3>题库管理</h3><button class="btn btn-primary btn-sm">新增题目</button></div>
      <DataTable :columns="qColumns" :rows="questions" :page-size="20">
        <template #cell-subject="{ value }">{{ value === 1 ? '科目一' : '科目四' }}</template>
        <template #cell-type="{ value }">{{ { single: '单选', multiple: '多选', judge: '判断' }[value as string] }}</template>
        <template #cell-status="{ value }">
          <span class="tag" :class="statusColors[value as string]">{{ statusLabels[value as string] }}</span>
        </template>
      </DataTable>
    </div>

    <!-- 审核中心 -->
    <div v-if="activeTab === 'review'" class="card">
      <div class="card-header"><h3>审核中心</h3></div>
      <DataTable :columns="reviewColumns" :rows="reviewList" :page-size="20">
        <template #cell-status="{ value }">
          <span class="tag tag-orange">{{ value === 'reviewing' ? '待审核' : value }}</span>
        </template>
      </DataTable>
    </div>

    <!-- 知识点管理 -->
    <div v-if="activeTab === 'knowledge'" class="card">
      <div class="card-header"><h3>知识点管理</h3><button class="btn btn-primary btn-sm">新增知识点</button></div>
      <DataTable :columns="kColumns" :rows="knowledgeList" :page-size="20">
        <template #cell-status="{ value }">
          <span class="tag" :class="statusColors[value as string]">{{ statusLabels[value as string] }}</span>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.cms-page { max-width: 1100px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.cms-tabs { display: flex; gap: 0; margin-bottom: 20px; border-bottom: 2px solid var(--color-border-light); }
.cms-tabs button {
  padding: 10px 24px; font-size: var(--font-size-sm); color: var(--color-text-tertiary);
  border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all var(--transition-fast);
}
.cms-tabs button.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 500; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.card-header h3 { font-size: var(--font-size-lg); }

.tag { font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm); font-weight: 500; }
.tag-green { background: #F6FFED; color: #52C41A; }
.tag-orange { background: #FFF7E6; color: #FAAD14; }
.tag-gray { background: #F5F5F5; color: #999; }
.tag-red { background: #FFF1F0; color: #FF4D4F; }
.btn-sm { padding: 4px 14px; font-size: var(--font-size-xs); }
</style>
