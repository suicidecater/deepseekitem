<script setup lang="ts">
// src/components/business/PendingCoachingPanel.vue — 待辅导学员快捷面板（右侧悬浮）
import { computed } from 'vue'

export interface PendingStudent {
  id: number
  name: string
  email: string
  carType: string
  weakDimension: string
  accuracy: number
  lastActive: string
  daysSinceActive: number
  reason: string
}

const props = defineProps<{
  students: PendingStudent[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-detail', id: number): void
  (e: 'send-message', id: number): void
  (e: 'toggle', visible: boolean): void
}>()

const collapsed = defineModel<boolean>('collapsed', { default: false })

const hasStudents = computed(() => props.students.length > 0)

function togglePanel() {
  collapsed.value = !collapsed.value
}

function formatTime(iso: string): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffHours = Math.round((now.getTime() - d.getTime()) / (1000 * 60 * 60))
    if (diffHours < 1) return '刚刚'
    if (diffHours < 24) return `${diffHours}小时前`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 30) return `${diffDays}天前`
    return d.toLocaleDateString('zh-CN')
  } catch {
    return ''
  }
}
</script>

<template>
  <div v-if="hasStudents">
    <Transition name="panel-slide">
      <!-- 展开面板 -->
      <div v-if="!collapsed" key="panel" class="pending-panel card">
        <div class="panel-header">
          <div class="panel-title">
            <span class="dot"></span>
            <span>待辅导学员</span>
            <span class="badge">{{ students.length }}</span>
          </div>
          <button class="panel-close" @click="collapsed = true" title="收起面板">✕</button>
        </div>

        <div v-if="loading" class="panel-loading">加载中...</div>
        <div v-else class="panel-list">
          <div
            v-for="s in students"
            :key="s.id"
            class="pending-item"
          >
            <div class="item-header">
              <span class="item-name">{{ s.name }}</span>
              <span class="item-car">{{ s.carType }}</span>
            </div>
            <div class="item-info">
              <span class="item-weak">薄弱：{{ s.weakDimension || '暂无' }}</span>
            </div>
            <div class="item-meta">
              <span class="item-accuracy" :class="{ danger: s.accuracy < 60 }">
                正确率 {{ s.accuracy }}%
              </span>
              <span class="item-time" v-if="s.daysSinceActive > 0">
                {{ s.daysSinceActive }}天未刷题
              </span>
            </div>
            <div class="item-reason">{{ s.reason }}</div>
            <div class="item-actions">
              <button class="action-btn primary" @click="emit('view-detail', s.id)">查看详情</button>
              <button class="action-btn" @click="emit('send-message', s.id)">发消息</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 收起状态的小标签 -->
      <div v-else key="toggle" class="pending-toggle" @click="collapsed = false">
        <span class="dot"></span>
        <span>待辅导 {{ students.length }}</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.pending-panel {
  position: fixed;
  right: 24px;
  top: 100px;
  width: 320px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  z-index: 100;
  background: var(--color-bg-white);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 0;
  background: var(--color-bg-white);
  z-index: 1;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-error);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.badge {
  background: var(--color-error);
  color: #fff;
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 500;
}

.panel-close {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--color-text-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
}

.panel-close:hover {
  background: #f0f0f0;
  color: var(--color-text-primary);
}

.panel-loading {
  text-align: center;
  padding: 20px;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-xs);
}

.panel-list {
  padding: 8px;
}

.pending-item {
  padding: 12px;
  border-radius: var(--radius-md);
  background: #FFFBEB;
  margin-bottom: 8px;
  border: 1px solid #FFE7BA;
  transition: background var(--transition-fast);
}

.pending-item:hover {
  background: #FFF7E6;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.item-name {
  font-weight: 600;
  font-size: var(--font-size-sm);
}

.item-car {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  background: #fff;
  padding: 1px 6px;
  border-radius: 3px;
}

.item-info {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: 2px;
}

.item-weak {
  color: var(--color-warning);
  font-weight: 500;
}

.item-meta {
  display: flex;
  gap: 12px;
  font-size: var(--font-size-xs);
  margin-bottom: 4px;
}

.item-accuracy {
  font-weight: 600;
  color: var(--color-text-secondary);
}

.item-accuracy.danger {
  color: var(--color-error);
}

.item-time {
  color: var(--color-text-tertiary);
}

.item-reason {
  font-size: 11px;
  color: var(--color-error);
  margin-bottom: 8px;
}

.item-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  flex: 1;
  padding: 5px 0;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.action-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.action-btn.primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.action-btn.primary:hover {
  background: var(--color-primary-dark);
}

/* 收起状态触发按钮 */
.pending-toggle {
  position: fixed;
  right: 24px;
  top: 100px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  background: var(--color-bg-white);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--color-error);
  z-index: 100;
  border: 1px solid var(--color-border-light);
}

.pending-toggle:hover {
  box-shadow: var(--shadow-lg);
}

/* 过渡动画 */
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: all 0.3s ease;
}

.panel-slide-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.panel-slide-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
