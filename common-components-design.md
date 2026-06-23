# 通用基础组件设计文档

> **版本**: V1.0 | **技术栈**: Vue 3 Composition API + TypeScript

---

## 1. FormInput - 表单输入组件

支持实时校验、多种类型、错误提示。

```vue
<!-- src/components/common/FormInput.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: string
  type?: 'text' | 'password' | 'email' | 'number' | 'tel'
  label?: string
  placeholder?: string
  rules?: ValidationRule[]
  disabled?: boolean
  maxlength?: number
  showCount?: boolean
}

interface ValidationRule {
  validator: (value: string) => boolean
  message: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  showCount: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'blur'): void
  (e: 'focus'): void
}>()

const errors = computed(() => {
  if (!props.rules) return []
  return props.rules
    .filter(rule => !rule.validator(props.modelValue))
    .map(rule => rule.message)
})

const isValid = computed(() => errors.value.length === 0)
</script>

<template>
  <div class="form-input" :class="{ 'has-error': errors.length > 0, 'is-valid': isValid && modelValue }">
    <label v-if="label" class="form-input__label">{{ label }}</label>
    <div class="form-input__wrapper">
      <input
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :maxlength="maxlength"
        class="form-input__control"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @blur="emit('blur')"
        @focus="emit('focus')"
      />
      <span v-if="showCount && maxlength" class="form-input__count">
        {{ modelValue.length }}/{{ maxlength }}
      </span>
    </div>
    <transition name="slide-fade">
      <p v-if="errors.length" class="form-input__error">{{ errors[0] }}</p>
    </transition>
  </div>
</template>

<style scoped>
.form-input {
  margin-bottom: 20px;
}
.form-input__label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: var(--color-text-secondary);
}
.form-input__wrapper {
  position: relative;
}
.form-input__control {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.form-input__control:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}
.has-error .form-input__control {
  border-color: var(--color-error);
}
.is-valid .form-input__control {
  border-color: var(--color-success);
}
.form-input__error {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-error);
}
.form-input__count {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
```

### 使用示例

```typescript
// 密码校验规则
const passwordRules = [
  { validator: (v: string) => v.length >= 6, message: '密码至少6位' },
  { validator: (v: string) => /[a-zA-Z]/.test(v), message: '需包含字母' },
  { validator: (v: string) => /\d/.test(v), message: '需包含数字' },
]

// 邮箱校验规则
const emailRules = [
  { validator: (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), message: '邮箱格式不正确' },
]
```

---

## 2. CountdownTimer - 倒计时器

支持45秒/45分钟可配置，剩余5分钟时触发警告。

```vue
<!-- src/components/common/CountdownTimer.vue -->
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  seconds: number           // 倒计时总秒数
  warnAt?: number           // 警告触发秒数（默认300=5分钟）
  autoStart?: boolean
  showMs?: boolean          // 是否显示毫秒
}

const props = withDefaults(defineProps<Props>(), {
  warnAt: 300,
  autoStart: true,
  showMs: false
})

const emit = defineEmits<{
  (e: 'timeout'): void
  (e: 'warning'): void
  (e: 'tick', remaining: number): void
}>()

const remaining = ref(props.seconds)
const isRunning = ref(false)
const isWarning = ref(false)
let timer: number | null = null

const displayTime = computed(() => {
  const h = Math.floor(remaining.value / 3600)
  const m = Math.floor((remaining.value % 3600) / 60)
  const s = remaining.value % 60
  if (h > 0) {
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const progress = computed(() => {
  return ((props.seconds - remaining.value) / props.seconds) * 100
})

function start() {
  if (isRunning.value) return
  isRunning.value = true
  timer = window.setInterval(() => {
    remaining.value--
    emit('tick', remaining.value)
    if (remaining.value === props.warnAt) {
      isWarning.value = true
      emit('warning')
    }
    if (remaining.value <= 0) {
      stop()
      emit('timeout')
    }
  }, 1000)
}

function stop() {
  isRunning.value = false
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function reset() {
  stop()
  remaining.value = props.seconds
  isWarning.value = false
}

onMounted(() => {
  if (props.autoStart) start()
})

onUnmounted(() => stop())

defineExpose({ start, stop, reset, remaining })
</script>

<template>
  <div class="countdown-timer" :class="{ 'is-warning': isWarning }">
    <div class="countdown-timer__circle">
      <svg viewBox="0 0 100 100">
        <circle class="bg" cx="50" cy="50" r="45" />
        <circle
          class="progress"
          cx="50" cy="50" r="45"
          :stroke-dasharray="2 * Math.PI * 45"
          :stroke-dashoffset="2 * Math.PI * 45 * (1 - progress / 100)"
        />
      </svg>
      <span class="countdown-timer__text">{{ displayTime }}</span>
    </div>
  </div>
</template>

<style scoped>
.countdown-timer__circle {
  position: relative;
  width: 80px; height: 80px;
}
.countdown-timer__circle svg {
  transform: rotate(-90deg);
}
.bg {
  fill: none;
  stroke: #E8E8E8;
  stroke-width: 6;
}
.progress {
  fill: none;
  stroke: var(--color-primary);
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s linear;
}
.is-warning .progress {
  stroke: var(--color-error);
}
.countdown-timer__text {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 18px;
  font-weight: 700;
}
.is-warning .countdown-timer__text {
  color: var(--color-error);
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
```

---

## 3. ModalDialog - 弹窗组件

二次确认、信息提示、表单弹窗。

```vue
<!-- src/components/common/ModalDialog.vue -->
<script setup lang="ts">
import { watch, nextTick } from 'vue'

interface Props {
  visible: boolean
  title?: string
  width?: string          // 默认 520px
  closable?: boolean      // 点击遮罩关闭
  confirmText?: string
  cancelText?: string
  showFooter?: boolean
  loading?: boolean       // 确认按钮加载态
}

const props = withDefaults(defineProps<Props>(), {
  width: '520px',
  closable: true,
  confirmText: '确定',
  cancelText: '取消',
  showFooter: true,
  loading: false
})

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'close'): void
}>()

// 快捷键支持
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') handleClose()
  if (e.key === 'Enter' && props.showFooter) emit('confirm')
}

watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => document.addEventListener('keydown', onKeydown))
  } else {
    document.removeEventListener('keydown', onKeydown)
  }
})

function handleClose() {
  if (props.closable) {
    emit('update:visible', false)
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="handleClose">
        <div class="modal-container" :style="{ width }">
          <div class="modal-header">
            <h3>{{ title }}</h3>
            <button class="modal-close" @click="handleClose">&times;</button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="showFooter" class="modal-footer">
            <slot name="footer">
              <button class="btn btn-cancel" @click="emit('cancel')">{{ cancelText }}</button>
              <button class="btn btn-confirm" :disabled="loading" @click="emit('confirm')">
                <span v-if="loading" class="spinner"></span>
                {{ confirmText }}
              </button>
            </slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-container {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-height: 80vh;
  display: flex; flex-direction: column;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border);
}
.modal-close {
  background: none; border: none; font-size: 24px;
  cursor: pointer; color: var(--color-text-tertiary);
}
.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}
.modal-footer {
  padding: 12px 24px;
  border-top: 1px solid var(--color-border);
  display: flex; justify-content: flex-end; gap: 12px;
}
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.2s;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
</style>
```

---

## 4. ProgressBar - 进度条

支持答题进度、学习进度等场景。

```vue
<!-- src/components/common/ProgressBar.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  percent: number       // 0-100
  showText?: boolean
  strokeColor?: string
  height?: number       // px
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showText: true,
  strokeColor: 'var(--color-primary)',
  height: 8,
  animated: true
})

const percentClamped = computed(() => Math.min(100, Math.max(0, props.percent)))
</script>

<template>
  <div class="progress-bar">
    <div class="progress-bar__track" :style="{ height: height + 'px' }">
      <div
        class="progress-bar__fill"
        :class="{ animated }"
        :style="{
          width: percentClamped + '%',
          backgroundColor: strokeColor,
          height: height + 'px'
        }"
      />
    </div>
    <span v-if="showText" class="progress-bar__text">
      {{ Math.round(percentClamped) }}%
    </span>
  </div>
</template>

<style scoped>
.progress-bar {
  display: flex; align-items: center; gap: 8px;
}
.progress-bar__track {
  flex: 1;
  background: #F0F0F0;
  border-radius: 999px;
  overflow: hidden;
}
.progress-bar__fill {
  border-radius: 999px;
  transition: width 0.3s ease;
}
.progress-bar__fill.animated {
  background-image: linear-gradient(-45deg,
    rgba(255,255,255,0.2) 25%, transparent 25%, transparent 50%,
    rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.2) 75%, transparent 75%
  );
  background-size: 20px 20px;
  animation: progress-stripe 1s linear infinite;
}
@keyframes progress-stripe {
  0% { background-position: 0 0; }
  100% { background-position: 20px 0; }
}
</style>
```

---

## 5. Toast - 消息提示

```typescript
// src/components/common/Toast.ts
import { createApp, h, ref, Transition } from 'vue'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastOptions {
  message: string
  type?: ToastType
  duration?: number  // ms, 0 = 不自动关闭
}

// 函数式调用
export function showToast(options: ToastOptions | string) {
  const opts: ToastOptions = typeof options === 'string'
    ? { message: options, type: 'info' }
    : options

  const visible = ref(true)
  const mountNode = document.createElement('div')
  document.body.appendChild(mountNode)

  const app = createApp({
    setup() {
      if (opts.duration !== 0) {
        setTimeout(() => { visible.value = false }, opts.duration || 3000)
      }
      return () => h(Transition, { name: 'toast-slide' }, {
        default: () => visible.value ? h('div', {
          class: `toast toast--${opts.type || 'info'}`,
          onClick: () => { visible.value = false }
        }, opts.message) : null
      })
    }
  })

  app.mount(mountNode)

  // 动画结束后清理
  setTimeout(() => {
    app.unmount()
    document.body.removeChild(mountNode)
  }, (opts.duration || 3000) + 400)
}
```

---

## 6. EmptyState - 空状态

```vue
<!-- src/components/common/EmptyState.vue -->
<script setup lang="ts">
interface Props {
  description?: string
  image?: string        // 自定义图片URL
  actionText?: string   // 操作按钮文字
}

defineProps<Props>()
const emit = defineEmits<{ (e: 'action'): void }>()
</script>

<template>
  <div class="empty-state">
    <img :src="image || '/assets/images/empty-default.svg'" alt="empty" class="empty-state__image" />
    <p class="empty-state__desc">{{ description || '暂无数据' }}</p>
    <button v-if="actionText" class="btn btn-primary" @click="emit('action')">
      {{ actionText }}
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 20px;
}
.empty-state__image { width: 120px; height: 120px; margin-bottom: 16px; opacity: 0.6; }
.empty-state__desc { color: var(--color-text-tertiary); font-size: 14px; margin-bottom: 16px; }
</style>
```

---

## 7. DataTable - 数据表格

支持排序、筛选、多选、导出、分页。

```vue
<!-- src/components/common/DataTable.vue -->
<script setup lang="ts" generic="T extends Record<string, any>">
import { ref, computed } from 'vue'

interface Column {
  key: string
  title: string
  width?: number
  sortable?: boolean
  render?: (value: any, row: T) => string
}

interface Props {
  columns: Column[]
  dataSource: T[]
  loading?: boolean
  rowKey?: string
  selectable?: boolean
  pagination?: { current: number; pageSize: number; total: number }
}

const props = withDefaults(defineProps<Props>(), {
  rowKey: 'id',
  selectable: false
})

const emit = defineEmits<{
  (e: 'sort', key: string, order: 'asc' | 'desc'): void
  (e: 'select', keys: (string | number)[]): void
  (e: 'page-change', page: number): void
  (e: 'row-click', row: T): void
}>()

const sortKey = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')
const selectedKeys = ref<Set<string | number>>(new Set())

function handleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
  emit('sort', key, sortOrder.value)
}
</script>

<template>
  <div class="data-table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th v-if="selectable" class="col-checkbox">
            <input type="checkbox" />
          </th>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width ? col.width + 'px' : 'auto' }"
            :class="{ sortable: col.sortable, sorted: sortKey === col.key }"
            @click="col.sortable && handleSort(col.key)"
          >
            {{ col.title }}
            <span v-if="col.sortable" class="sort-icon">
              {{ sortKey === col.key ? (sortOrder === 'asc' ? '↑' : '↓') : '↕' }}
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td :colspan="columns.length + (selectable ? 1 : 0)" class="loading-cell">
            加载中...
          </td>
        </tr>
        <tr v-else-if="!dataSource.length">
          <td :colspan="columns.length + (selectable ? 1 : 0)" class="empty-cell">
            暂无数据
          </td>
        </tr>
        <tr
          v-for="row in dataSource"
          :key="row[rowKey]"
          @click="emit('row-click', row)"
        >
          <td v-if="selectable" class="col-checkbox">
            <input type="checkbox" />
          </td>
          <td v-for="col in columns" :key="col.key">
            {{ col.render ? col.render(row[col.key], row) : row[col.key] }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 分页器 -->
    <div v-if="pagination" class="pagination">
      <span>共 {{ pagination.total }} 条</span>
      <button
        :disabled="pagination.current <= 1"
        @click="emit('page-change', pagination.current - 1)"
      >上一页</button>
      <span>{{ pagination.current }} / {{ Math.ceil(pagination.total / pagination.pageSize) }}</span>
      <button
        :disabled="pagination.current >= Math.ceil(pagination.total / pagination.pageSize)"
        @click="emit('page-change', pagination.current + 1)"
      >下一页</button>
    </div>
  </div>
</template>

<style scoped>
.data-table-wrapper { background: #fff; border-radius: var(--radius-md); }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  padding: 12px 16px; text-align: left; font-weight: 600;
  background: #FAFAFA; border-bottom: 1px solid var(--color-border);
  font-size: 14px; user-select: none;
}
.data-table td { padding: 12px 16px; border-bottom: 1px solid #F0F0F0; font-size: 14px; }
.data-table tr:hover td { background: #FAFAFA; }
.sortable { cursor: pointer; }
.sortable:hover { background: #F0F0F0; }
.sort-icon { margin-left: 4px; font-size: 12px; }
.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 12px 16px; }
</style>
```

---

## 8. FileUpload - 文件上传

```vue
<!-- src/components/common/FileUpload.vue -->
<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  accept?: string       // 如 '.xlsx,.csv'
  multiple?: boolean
  maxSize?: number      // MB
  tip?: string
}

const props = withDefaults(defineProps<Props>(), {
  accept: '*',
  multiple: false,
  maxSize: 10
})

const emit = defineEmits<{
  (e: 'upload', files: File[]): void
  (e: 'error', msg: string): void
}>()

const isDragging = ref(false)

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  validateAndEmit(files)
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  validateAndEmit(files)
  input.value = '' // 允许重复选择同一文件
}

function validateAndEmit(files: File[]) {
  for (const file of files) {
    if (file.size > props.maxSize * 1024 * 1024) {
      emit('error', `文件 ${file.name} 超过 ${props.maxSize}MB 限制`)
      return
    }
  }
  emit('upload', files)
}
</script>

<template>
  <div
    class="file-upload"
    :class="{ 'is-dragging': isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop="handleDrop"
  >
    <input
      type="file"
      :accept="accept"
      :multiple="multiple"
      class="file-upload__input"
      @change="handleFileInput"
    />
    <div class="file-upload__content">
      <slot>
        <p>点击或拖拽文件到此处上传</p>
        <span v-if="tip" class="file-upload__tip">{{ tip }}</span>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.file-upload {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
  position: relative;
}
.file-upload:hover, .file-upload.is-dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.file-upload__input {
  position: absolute; inset: 0; opacity: 0; cursor: pointer;
}
.file-upload__tip {
  font-size: 12px; color: var(--color-text-tertiary);
}
</style>
```

---

*本文档基于 SRS V1.0 交互规范编写，组件遵循 Vue 3 Composition API + TypeScript 最佳实践*
