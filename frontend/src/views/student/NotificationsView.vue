<template>
  <div class="notifications-page">
    <div class="page-header">
      <h2>通知中心</h2>
      <el-button v-if="list.length > 0" type="primary" plain @click="handleReadAll">
        全部标记已读
      </el-button>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && list.length === 0" description="暂无通知" />

    <!-- 通知列表 -->
    <div v-loading="loading" class="notification-list">
      <div
        v-for="(item, index) in list"
        :key="item.id"
        class="notification-card"
        :class="{
          'card-even': index % 2 === 0,
          'card-odd': index % 2 === 1,
          unread: item.is_read === 0,
        }"
        @click="handleClick(item)"
      >
        <div class="card-left">
          <div class="icon-wrap">
            <component :is="getIconByType(item.type)" class="type-icon" />
          </div>
          <div class="card-content">
            <div class="card-title">{{ item.title }}</div>
            <div class="card-desc">{{ item.content }}</div>
          </div>
        </div>
        <div class="card-right">
          <span class="card-time">{{ item.publish_time || item.create_time }}</span>
          <span v-if="item.is_read === 0" class="unread-dot"></span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrap" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
    </div>

    <!-- 通知详情弹窗 -->
    <el-dialog v-model="detailVisible" title="通知详情" width="560px" :close-on-click-modal="false">
      <div class="detail-content">
        <div class="detail-meta">
          <el-tag size="small">{{ NotificationTypeMap[detailItem.type as NotificationType] }}</el-tag>
          <span class="detail-time">{{ detailItem.publish_time || detailItem.create_time }}</span>
        </div>
        <h3 class="detail-title">{{ detailItem.title }}</h3>
        <div class="detail-body">{{ detailItem.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, shallowRef, type Component } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, Document, InfoFilled } from '@element-plus/icons-vue'
import {
  studentGetNotifications,
  studentReadNotification,
  studentReadAllNotifications,
} from '@/api/modules/notification'
import { useNotificationStore } from '@/stores/notification'
import type { NotificationItem, NotificationType } from '@/types/notification'
import { NotificationTypeMap } from '@/types/notification'

// ======== 根据通知类型返回对应图标 ========
function getIconByType(type: number): Component {
  switch (type) {
    case 1:
      return Bell // 系统公告 → 喇叭图标
    case 2:
      return Document // 培训通知 → 文档图标
    case 3:
      return InfoFilled // 其他 → 提示图标
    default:
      return InfoFilled
  }
}

// ======== 状态 ========
const list = ref<NotificationItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const detailItem = ref<NotificationItem>({} as NotificationItem)

const notifyStore = useNotificationStore()

// ======== 方法 ========
async function fetchList() {
  loading.value = true
  try {
    const res = await studentGetNotifications({
      page: page.value,
      page_size: pageSize.value,
    })
    const data = res.data.data!
    list.value = data.list
    total.value = data.total
  } catch {
    // 静默
  } finally {
    loading.value = false
  }
}

async function handleClick(item: NotificationItem) {
  detailItem.value = item
  detailVisible.value = true

  // 未读 → 标记已读
  if (item.is_read === 0) {
    try {
      await studentReadNotification(item.id)
      item.is_read = 1
      notifyStore.decrementUnread(1)
    } catch {
      // 静默
    }
  }
}

async function handleReadAll() {
  try {
    await studentReadAllNotifications()
    list.value.forEach((item) => {
      item.is_read = 1
    })
    notifyStore.clearUnread()
    ElMessage.success('已全部标记为已读')
  } catch (err: any) {
    console.error('[学生端-全部标记已读] 失败:', err)
    ElMessage.error(err?.message || '操作失败，请稍后重试')
  }
}

onMounted(() => {
  fetchList()
  notifyStore.startPolling()
})
</script>

<style scoped>
.notifications-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 12px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  line-height: 1;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.notification-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 20px;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 12px;
}
.notification-card:hover {
  background: #e8f4fd !important;
}
/* 奇偶行背景色 */
.notification-card.card-even {
  background: #ffffff;
}
.notification-card.card-odd {
  background: #f5f9ff;
}
/* 未读卡片背景色 */
.notification-card.unread.card-even {
  background: #e8f4fd;
}
.notification-card.unread.card-odd {
  background: #e0eefa;
}

/* 左侧：图标 + 内容 */
.card-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.type-icon {
  font-size: 20px;
  color: #409eff;
}
.card-content {
  flex: 1;
  min-width: 0;
}
.card-title {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}
.card-desc {
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧：时间 + 未读圆点 */
.card-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 16px;
}
.card-time {
  font-size: 12px;
  color: #c0c4cc;
  white-space: nowrap;
}
.unread-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
  flex-shrink: 0;
}

.pagination-wrap {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.detail-content {
  padding: 4px 0;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.detail-time {
  font-size: 13px;
  color: #909399;
}
.detail-title {
  font-size: 18px;
  color: #303133;
  margin: 0 0 16px;
}
.detail-body {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
