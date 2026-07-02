<script setup lang="ts">
// src/components/business/QuestionCard.vue
import { computed, ref, watch } from 'vue'
import type { ExamQuestion } from '@/types/exam'

const props = defineProps<{
  question: ExamQuestion
  questionIndex?: number
  selectedAnswer?: string
  showResult?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'answer', questionId: number, answer: string): void
}>()

// 多选题临时选择集合
const multiSelected = ref<Set<string>>(new Set())

const isJudge = computed(() => props.question.type === 'judge')
const isMulti = computed(() => props.question.type === 'multiple')
const isSingle = computed(() => props.question.type === 'single')

const typeLabel = computed(() => {
  const map: Record<string, string> = { single: '单选题', multiple: '多选题', judge: '判断题' }
  return map[props.question.type] || '未知'
})

const optionLabels = ['A', 'B', 'C', 'D', 'E', 'F']
const correctAnswer = computed(() => props.question.answer || '')

function isSelected(letter: string) {
  if (isMulti.value) return multiSelected.value.has(letter)
  return props.selectedAnswer === letter
}

function getOptionClass(_opt: string, idx: number) {
  const letter = optionLabels[idx]
  const selected = isSelected(letter)
  if (!props.showResult) return { selected }
  const correct = correctAnswer.value.includes(letter)
  return { correct, wrong: selected && !correct, selected: selected && correct }
}

function selectOption(idx: number) {
  if (props.disabled || props.showResult) return
  const letter = optionLabels[idx]

  if (isMulti.value) {
    if (multiSelected.value.has(letter)) multiSelected.value.delete(letter)
    else multiSelected.value.add(letter)
    return
  }
  emit('answer', props.question.id, letter)
}

function isCorrectMulti() {
  if (!isMulti.value) return false
  const sorted = (props.selectedAnswer || '').split('').sort().join('')
  return sorted === correctAnswer.value
}

function confirmMulti() {
  if (!isMulti.value) return
  const sorted = Array.from(multiSelected.value).sort().join('')
  if (sorted) emit('answer', props.question.id, sorted)
  multiSelected.value = new Set()
}

// 判断题快捷选项
function answerJudge(value: string) {
  if (props.disabled || props.showResult) return
  emit('answer', props.question.id, value)
}

// ===== 图片兜底 =====
const hideImage = ref(false)
const imageRetried = ref(false)

function onImageError(e: Event) {
  const img = e.target as HTMLImageElement
  if (imageRetried.value) {
    hideImage.value = true
    return
  }
  if (/\.jpg$/i.test(img.src) && !/\.png$/i.test(img.src)) {
    imageRetried.value = true
    img.src = img.src.replace(/\.jpg$/i, '.png')
  } else {
    hideImage.value = true
  }
}

// 切换题目时重置状态
watch(() => props.question?.id, () => {
  hideImage.value = false
  imageRetried.value = false
  multiSelected.value = new Set()
})
</script>

<template>
  <div class="question-card">
    <div class="question-header">
      <span class="question-type" :class="'type-' + question.type">{{ typeLabel }}</span>
      <span v-if="question.difficulty" class="question-difficulty" :title="question.difficulty === 1 ? '简单' : '中等'">
        {{ question.difficulty === 1 ? '⭐' : '⭐⭐' }}
      </span>
      <span v-if="isMulti" class="multi-hint">可多选，选完后点击确认</span>
      <span class="question-index">第 {{ questionIndex }} 题</span>
    </div>

    <div class="question-body">
      <p class="question-content">{{ question.content }}</p>
      <div v-if="question.image && !hideImage" class="question-image-area">
        <img :src="`/images/${question.image}`" class="question-image" alt="题目配图"
          @error="onImageError" />
      </div>
    </div>

    <!-- 判断题：对/错按钮 -->
    <div v-if="isJudge" class="judge-options">
      <button class="judge-btn correct-btn"
        :class="{
          selected: selectedAnswer === '√' || selectedAnswer === '对',
          correct: showResult && correctAnswer === '√',
          wrong: showResult && (selectedAnswer === '√' || selectedAnswer === '对') && correctAnswer !== '√'
        }"
        :disabled="disabled || showResult" @click="answerJudge('√')">
        <span class="judge-icon">✅</span> 正确
      </button>
      <button class="judge-btn wrong-btn"
        :class="{
          selected: selectedAnswer === '×' || selectedAnswer === '错',
          correct: showResult && correctAnswer === '×',
          wrong: showResult && (selectedAnswer === '×' || selectedAnswer === '错') && correctAnswer !== '×'
        }"
        :disabled="disabled || showResult" @click="answerJudge('×')">
        <span class="judge-icon">❌</span> 错误
      </button>
    </div>

    <!-- 单选/多选：选项列表 -->
    <div v-else class="question-options">
      <div v-for="(opt, idx) in question.options" :key="idx" class="option-item"
        :class="getOptionClass(opt, idx)" @click="selectOption(idx)">
        <span class="option-check">{{ isMulti ? (multiSelected.has(optionLabels[idx]) ? '☑' : '☐') : (isSelected(optionLabels[idx]) ? '●' : '○') }}</span>
        <span class="option-letter">{{ optionLabels[idx] }}</span>
        <span class="option-text">{{ opt }}</span>
      </div>
      <!-- 多选题确认按钮 -->
      <button v-if="isMulti && !showResult && multiSelected.size > 0" class="confirm-multi-btn" @click="confirmMulti">
        确认选择（已选 {{ multiSelected.size }} 项）
      </button>
    </div>

    <!-- 答案解析 -->
    <div v-if="showResult" class="question-explanation">
      <div class="explanation-header">
        <span v-if="selectedAnswer === correctAnswer || (isMulti && isCorrectMulti())" class="result-tag correct">回答正确</span>
        <span v-else class="result-tag wrong">回答错误，正确答案是 {{ correctAnswer }}</span>
      </div>
      <p v-if="question.explanation" class="explanation-text"><strong>解析：</strong>{{ question.explanation }}</p>
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

.question-difficulty {
  font-size: 14px;
  cursor: default;
  flex-shrink: 0;
}

.question-index {
  font-size: 14px;
  color: var(--color-text-secondary);
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

.multi-hint {
  font-size: 12px; color: #FA8C16; margin-left: 8px;
}

/* 判断题 */
.judge-options { display: flex; gap: 16px; }
.judge-btn {
  flex: 1; padding: 20px; border: 2px solid var(--color-border); border-radius: var(--radius-lg);
  font-size: 18px; font-weight: 600; cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.judge-btn:hover:not(:disabled) { border-color: var(--color-primary); }
.judge-btn.selected { border-color: var(--color-primary); background: var(--color-primary-light); }
.judge-btn:disabled { cursor: default; opacity: .7; }
.correct-btn.selected { border-color: #52C41A; background: #F6FFED; }
.wrong-btn.selected { border-color: #FF4D4F; background: #FFF1F0; }
.judge-btn.correct { border-color: #52C41A; background: #F6FFED; }
.judge-btn.wrong { border-color: #FF4D4F; background: #FFF1F0; }
.judge-icon { font-size: 24px; }

.option-check { font-size: 14px; margin-right: 4px; width: 18px; text-align: center; }

.confirm-multi-btn {
  margin-top: 8px; padding: 12px; background: var(--color-primary); color: #fff;
  border: none; border-radius: var(--radius-md); font-size: 15px; cursor: pointer; font-weight: 500;
}
.question-image-area {
  display: flex;
  justify-content: center;
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
