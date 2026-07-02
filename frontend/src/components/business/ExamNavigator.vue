<script setup lang="ts">
// src/components/business/ExamNavigator.vue - 题号导航面板
import { computed } from 'vue'

const props = defineProps<{
  totalCount: number
  answers: Map<number, string>
  markedQuestions: Set<number>
  currentIndex: number
}>()

const emit = defineEmits<{
  (e: 'jump', index: number): void
  (e: 'submit'): void
}>()

const questionStatuses = computed(() => {
  return Array.from({ length: props.totalCount }, (_, i) => {
    const qId = i + 1
    const answered = props.answers.has(qId)
    const marked = props.markedQuestions.has(qId)
    return { index: i, qId, answered, marked, current: i === props.currentIndex }
  })
})

const answeredCount = computed(() => props.answers.size)
const unansweredCount = computed(() => props.totalCount - props.answers.size)
const markedCount = computed(() => props.markedQuestions.size)
</script>

<template>
  <div class="exam-navigator">
    <div class="nav-stats">
      <div class="stat-row"><span class="stat-dot answered"></span> 已答 {{ answeredCount }}</div>
      <div class="stat-row"><span class="stat-dot unanswered"></span> 未答 {{ unansweredCount }}</div>
      <div class="stat-row"><span class="stat-dot marked"></span> 标记 {{ markedCount }}</div>
    </div>

    <div class="nav-grid">
      <button
        v-for="s in questionStatuses"
        :key="s.index"
        class="nav-btn"
        :class="{
          current: s.current,
          answered: s.answered,
          marked: s.marked
        }"
        @click="emit('jump', s.index)"
      >
        {{ s.qId }}
      </button>
    </div>

    <button class="btn btn-primary btn-block nav-submit" @click="emit('submit')">
      交卷
    </button>
  </div>
</template>

<style scoped>
.exam-navigator {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 16px;
  border: 1px solid var(--color-border-light);
}

.nav-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.stat-dot.answered { background: var(--color-primary); }
.stat-dot.unanswered { background: var(--color-border); }
.stat-dot.marked { background: var(--color-warning); }

.nav-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  margin-bottom: 16px;
}

.nav-btn {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: #fff;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.nav-btn.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}
.nav-btn.answered {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.nav-btn.marked {
  border-color: var(--color-warning);
  background: #FFFBE6;
}
.nav-btn:hover {
  transform: scale(1.05);
}

.nav-submit {
  padding: 10px 0;
}
</style>
