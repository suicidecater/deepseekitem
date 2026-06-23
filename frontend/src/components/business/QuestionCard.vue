<script setup lang="ts">
// src/components/business/QuestionCard.vue
import { computed } from 'vue'
import type { ExamQuestion } from '@/types/exam'

const props = defineProps<{
  question: ExamQuestion
  selectedAnswer?: string
  showResult?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'answer', questionId: number, answer: string): void
}>()

const typeLabel = computed(() => {
  const map: Record<string, string> = { single: '单选题', multiple: '多选题', judge: '判断题' }
  return map[props.question.type] || '未知'
})

const optionLabels = ['A', 'B', 'C', 'D', 'E', 'F']

function getOptionClass(opt: string, idx: number) {
  if (!props.showResult) {
    return { selected: props.selectedAnswer === optionLabels[idx] }
  }
  const letter = optionLabels[idx]
  return {
    correct: letter === props.question.answer,
    wrong: props.selectedAnswer === letter && letter !== props.question.answer,
    selected: props.selectedAnswer === letter
  }
}

function selectOption(idx: number) {
  if (props.disabled) return
  emit('answer', props.question.id, optionLabels[idx])
}
</script>

<template>
  <div class="question-card">
    <div class="question-header">
      <span class="question-type" :class="'type-' + question.type">{{ typeLabel }}</span>
      <span class="question-category">{{ question.category }}</span>
      <span v-if="question.difficulty > 0" class="question-difficulty">
        {{ '⭐'.repeat(question.difficulty) }}
      </span>
    </div>

    <div class="question-body">
      <p class="question-content">{{ question.content }}</p>
      <img v-if="question.image" :src="question.image" class="question-image" alt="题目配图" />
    </div>

    <div class="question-options">
      <div
        v-for="(opt, idx) in question.options"
        :key="idx"
        class="option-item"
        :class="getOptionClass(opt, idx)"
        @click="selectOption(idx)"
      >
        <span class="option-letter">{{ optionLabels[idx] }}</span>
        <span class="option-text">{{ opt }}</span>
        <span v-if="showResult && optionLabels[idx] === question.answer" class="option-icon">✅</span>
        <span v-else-if="showResult && props.selectedAnswer === optionLabels[idx] && optionLabels[idx] !== question.answer" class="option-icon">❌</span>
      </div>
    </div>

    <!-- 答案解析 -->
    <div v-if="showResult" class="question-explanation">
      <div class="explanation-header">
        <span v-if="props.selectedAnswer === question.answer" class="result-tag correct">回答正确</span>
        <span v-else class="result-tag wrong">
          回答错误，正确答案是 {{ question.answer }}
        </span>
      </div>
      <p class="explanation-text">
        <strong>解析：</strong>{{ question.explanation }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.question-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--color-border-light);
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.question-type {
  font-size: var(--font-size-xs);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}
.type-single { background: #E6F4FF; color: #1677FF; }
.type-multiple { background: #F6FFED; color: #52C41A; }
.type-judge { background: #FFF7E6; color: #FA8C16; }

.question-category {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.question-difficulty {
  font-size: 11px;
  margin-left: auto;
}

.question-body {
  margin-bottom: 24px;
}

.question-content {
  font-size: var(--font-size-lg);
  line-height: 1.8;
  color: var(--color-text-primary);
}

.question-image {
  margin-top: 16px;
  max-width: 100%;
  border-radius: var(--radius-md);
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.option-item:hover:not(.correct):not(.wrong) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.option-item.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.option-item.correct {
  border-color: var(--color-success);
  background: #F6FFED;
}
.option-item.wrong {
  border-color: var(--color-error);
  background: #FFF1F0;
}

.option-letter {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #F5F5F5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: 600;
  flex-shrink: 0;
}
.option-item.selected .option-letter { background: var(--color-primary); color: #fff; }
.option-item.correct .option-letter { background: var(--color-success); color: #fff; }
.option-item.wrong .option-letter { background: var(--color-error); color: #fff; }

.option-text { flex: 1; font-size: var(--font-size-base); }
.option-icon { font-size: 18px; }

.question-explanation {
  margin-top: 20px;
  padding: 16px;
  background: #FAFAFA;
  border-radius: var(--radius-md);
}

.explanation-header {
  margin-bottom: 8px;
}

.result-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
}
.result-tag.correct { background: #F6FFED; color: var(--color-success); }
.result-tag.wrong { background: #FFF1F0; color: var(--color-error); }

.explanation-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.8;
}
</style>
