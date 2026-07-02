<template>
  <div class="admin-notifications-page">
    <div class="page-header">
      <h2>通知管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <span style="margin-right:4px">+</span> 发布通知
      </el-button>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar">
      <el-select v-model="filterType" placeholder="通知类型" clearable style="width:140px">
        <el-option label="系统公告" :value="1" />
        <el-option label="培训通知" :value="2" />
        <el-option label="其他" :value="3" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px">
        <el-option label="草稿" :value="1" />
        <el-option label="已发布" :value="2" />
        <el-option label="已撤回" :value="3" />
      </el-select>
      <el-select v-model="filterTargetRole" placeholder="接收角色" clearable style="width:120px">
        <el-option label="教练" :value="1" />
        <el-option label="学员" :value="2" />
        <el-option label="全部" :value="3" />
      </el-select>
      <el-button @click="fetchList">查询</el-button>
    </div>

    <!-- 数据表格 -->
    <el-table :data="list" v-loading="loading" border stripe style="width:100%;margin-top:16px">
      <el-table-column prop="id" label="ID" width="70" align="center" />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="typeTagMap[row.type] || 'info'" size="small">
            {{ NotificationTypeMap[row.type as NotificationType] || '未知' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="接收角色" width="100" align="center">
        <template #default="{ row }">
          {{ TargetRoleMap[row.target_role as TargetRole] || '未知' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagMap[row.status] || 'info'" size="small">
            {{ NotificationStatusMap[row.status as NotificationStatus] || '未知' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" width="170" align="center" />
      <el-table-column prop="publish_time" label="发布时间" width="170" align="center">
        <template #default="{ row }">{{ row.publish_time || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 1" size="small" type="primary" link @click="openEditDialog(row)">
            编辑
          </el-button>
          <el-button
            v-if="row.status === 2"
            size="small"
            type="warning"
            link
            @click="handleRecall(row)"
          >
            撤回
          </el-button>
          <el-button
            v-if="row.status === 1"
            size="small"
            type="danger"
            link
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap" v-if="total > 0">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next, jumper"
        @current-change="fetchList"
      />
    </div>

    <!-- 发布/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑通知' : '发布通知'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="80px" :rules="formRules" ref="formRef">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入通知标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="通知类型" prop="type">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="系统公告" :value="1" />
            <el-option label="培训通知" :value="2" />
            <el-option label="其他" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="接收角色" prop="target_role">
          <el-radio-group v-model="form.target_role">
            <el-radio :value="1">教练</el-radio>
            <el-radio :value="2">学员</el-radio>
            <el-radio :value="3">教练+学员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="请输入通知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button v-if="!isEdit" @click="submitForm(1)">存为草稿</el-button>
        <el-button type="primary" @click="submitForm(2)">
          {{ isEdit ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  adminGetNotifications,
  adminCreateNotification,
  adminUpdateNotification,
  adminDeleteNotification,
  adminRecallNotification,
} from '@/api/modules/notification'
import {
  type NotificationItem,
  type NotificationType,
  type TargetRole,
  type NotificationStatus,
  NotificationTypeMap,
  TargetRoleMap,
  NotificationStatusMap,
} from '@/types/notification'

// ======== 状态 ========
const list = ref<NotificationItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filterType = ref<number | undefined>()
const filterStatus = ref<number | undefined>()
const filterTargetRole = ref<number | undefined>()

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  title: '',
  content: '',
  type: 1 as number,
  target_role: 3 as number,
})

const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

const typeTagMap: Record<number, string> = { 1: '', 2: 'success', 3: 'info' }
const statusTagMap: Record<number, string> = { 1: 'info', 2: 'success', 3: 'warning' }

// ======== 方法 ========
async function fetchList() {
  loading.value = true
  try {
    const res = await adminGetNotifications({
      page: page.value,
      page_size: pageSize.value,
      type: filterType.value,
      status: filterStatus.value,
      target_role: filterTargetRole.value,
    })
    const data = res.data.data!
    list.value = data.list
    total.value = data.total
  } catch {
    // 已在 request 拦截器统一处理
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.title = ''
  form.content = ''
  form.type = 1
  form.target_role = 3
  editingId.value = null
  formRef.value?.resetFields()
}

function openCreateDialog() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: NotificationItem) {
  isEdit.value = true
  editingId.value = row.id
  form.title = row.title
  form.content = row.content
  form.type = row.type
  form.target_role = row.target_role
  dialogVisible.value = true
}

async function submitForm(status: number) {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (isEdit.value && editingId.value) {
      await adminUpdateNotification(editingId.value, {
        title: form.title,
        content: form.content,
        type: form.type as NotificationType,
        target_role: form.target_role as TargetRole,
        status: status as NotificationStatus,
      })
      ElMessage.success(status === 2 ? '通知已更新并发布' : '通知已更新')
    } else {
      await adminCreateNotification({
        title: form.title,
        content: form.content,
        type: form.type as NotificationType,
        target_role: form.target_role as TargetRole,
        status: status as NotificationStatus,
      })
      ElMessage.success(status === 2 ? '通知已发布' : '草稿已保存')
    }

    dialogVisible.value = false
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

async function handleRecall(row: NotificationItem) {
  try {
    await ElMessageBox.confirm('确定要撤回该通知吗？', '确认撤回', {
      type: 'warning',
    })
    await adminRecallNotification(row.id)
    ElMessage.success('通知已撤回')
    fetchList()
  } catch {
    // 取消操作
  }
}

async function handleDelete(row: NotificationItem) {
  try {
    await ElMessageBox.confirm('确定要删除该通知吗？删除后不可恢复。', '确认删除', {
      type: 'warning',
    })
    await adminDeleteNotification(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.admin-notifications-page {
  padding: 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
