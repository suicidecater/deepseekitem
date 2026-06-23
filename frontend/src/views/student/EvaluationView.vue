<script setup lang="ts">
// src/views/student/EvaluationView.vue - 能力基线测评页
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import { useTimer } from '@/composables/useTimer'
import QuestionCard from '@/components/business/QuestionCard.vue'

const router = useRouter()
const examStore = useExamStore()

type Phase = 'loading' | 'testing' | 'result'
const phase = ref<Phase>('loading')
const evaluationResult = ref<any>(null)
const selectedAnswer = ref('')

// 倒计时（每题45秒）
const timer = useTimer(45, handleTimeout)

// 能力等级
const abilityLevel = computed(() => {
  if (!evaluationResult.value) return null
  const avg = evaluationResult.value.correctRate
  if (avg >= 90) return { level: '冲刺', color: '#52C41A', desc: '基础扎实，可以直接冲刺考试！' }
  if (avg >= 75) return { level: '进阶', color: '#1677FF', desc: '有一定基础，重点突破薄弱环节' }
  if (avg >= 60) return { level: '基础', color: '#FAAD14', desc: '需要系统学习交通法规知识' }
  return { level: '入门', color: '#FF4D4F', desc: '建议从头系统学习，打好基础' }
})

onMounted(async () => {
  await examStore.loadQuestions({
    mode: 'evaluation',
    subject: 1,
    count: 40,
    difficulty: 0
  })
  phase.value = 'testing'
  timer.start()
})

function handleAnswer(questionId: number, answer: string) {
  selectedAnswer.value = answer
  examStore.recordAnswer(questionId, answer)

  // 自动跳下一题
  setTimeout(() => {
    if (examStore.currentIndex < examStore.totalCount - 1) {
      examStore.nextQuestion()
      selectedAnswer.value = ''
      timer.reset(45)
      timer.start()
    } else {
      handleSubmit()
    }
  }, 400)
}

function handleTimeout() {
  if (examStore.currentIndex < examStore.totalCount - 1) {
    examStore.nextQuestion()
    selectedAnswer.value = ''
    timer.reset(45)
    timer.start()
  } else {
    handleSubmit()
  }
}

async function handleSubmit() {
  timer.stop()
  const records = Array.from(examStore.answers.entries()).map(([questionId, answer]) => {
    const q = examStore.questions.find(x => x.id === questionId)
    return {
      questionId,
      answer,
      correct: q?.answer === answer,
      timeSpent: 45
    }
  })
  const result = await examStore.submit(records)
  evaluationResult.value = result
  phase.value = 'result'
}

function goToStudyPlan() {
  router.push('/student/study-plan')
}
</script>

<template>
  <div class="evaluation-page">
    <!-- 加载中 -->
    <div v-if="phase === 'loading'" class="loading-state">
      <div class="spinner"></div>
      <p>正在准备测评题目...</p>
    </div>

    <!-- 测评阶段 -->
    <template v-if="phase === 'testing' && examStore.currentQuestion">
      <div class="eval-header">
        <h2>能力基线测评</h2>
        <p class="eval-desc">共40题，四维度评估你的交规知识水平</p>
        <div class="eval-progress-bar">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{ width: ((examStore.currentIndex) / examStore.totalCount) * 100 + '%' }"
            ></div>
          </div>
          <span class="progress-text">{{ examStore.currentIndex + 1 }} / {{ examStore.totalCount }}</span>
        </div>
      </div>

      <div class="eval-body">
        <div class="eval-timer">
          <span :class="{ warning: timer.remaining <= 10 }">⏱ {{ timer.displayTime }}</span>
        </div>

        <QuestionCard
          :question="examStore.currentQuestion"
          :selected-answer="selectedAnswer"
          :show-result="false"
          @answer="handleAnswer"
        />

        <div class="eval-footer">
          <p class="eval-hint">选择答案后将自动进入下一题（不可回退）</p>
          <button class="btn btn-primary" @click="handleSubmit">立即提交</button>
        </div>
      </div>
    </template>

    <!-- 结果阶段 -->
    <template v-if="phase === 'result' && evaluationResult">
      <div class="eval-result">
        <div class="result-header">
          <h2>测评结果</h2>
          <div class="level-badge" :style="{ background: abilityLevel?.color }">
            {{ abilityLevel?.level }}
          </div>
          <p class="level-desc">{{ abilityLevel?.desc }}</p>
        </div>

        <!-- 能力雷达图（CSS简化版） -->
        <div class="result-radar card">
          <h3>四维能力分析</h3>
          <div class="simple-radar">
            <div v-for="(dim, idx) in evaluationResult.radarData?.dimensions || []" :key="dim" class="radar-dim">
              <span class="dim-label">{{ dim }}</span>
              <div class="dim-bar-bg">
                <div
                  class="dim-bar-fill"
                  :style="{ width: (evaluationResult.radarData?.current?.[idx] || 0) + '%' }"
                  :class="{ low: (evaluationResult.radarData?.current?.[idx] || 0) < 60 }"
                ></div>
              </div>
              <span class="dim-score">{{ evaluationResult.radarData?.current?.[idx] || 0 }}分</span>
            </div>
          </div>
        </div>

        <!-- 薄弱点清单 -->
        <div v-if="evaluationResult.weakPoints?.length" class="result-weak card">
          <h3>薄弱知识点（正确率 < 60%）</h3>
          <ul class="weak-list">
            <li v-for="item in evaluationResult.weakPoints" :key="item.name" class="weak-item">
              <span class="weak-name">{{ item.name }}</span>
              <span class="weak-rate">{{ item.rate }}%</span>
              <div class="weak-bar">
                <div class="weak-bar-fill" :style="{ width: item.rate + '%', background: '#FF4D4F' }"></div>
              </div>
            </li>
          </ul>
        </div>

        <!-- 学习建议 -->
        <div class="result-advice card">
          <h3>学习建议</h3>
          <ul>
            <li v-for="(advice, idx) in (evaluationResult.advices || ['请查看AI学习路径获取个性化建议'])" :key="idx">
              {{ advice }}
            </li>
          </ul>
        </div>

        <div class="result-actions">
          <button class="btn btn-primary btn-lg" @click="goToStudyPlan">
            查看AI学习计划 →
          </button>
          <button class="btn btn-outline btn-lg" @click="router.push('/student/home')">
            返回首页
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.evaluation-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 60vh; gap: 16px; color: var(--color-text-tertiary);
}
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.eval-header { margin-bottom: 24px; }
.eval-header h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.eval-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.eval-progress-bar {
  display: flex; align-items: center; gap: 12px; margin-top: 16px;
}
.progress-track { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-primary); border-radius: 4px; transition: width 0.3s ease; }
.progress-text { font-size: var(--font-size-sm); font-weight: 600; color: var(--color-primary); white-space: nowrap; }

.eval-timer {
  text-align: right; margin-bottom: 12px; font-size: var(--font-size-xl); font-weight: 700;
}
.eval-timer .warning { color: var(--color-error); animation: pulse 0.5s infinite; }
@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.5 } }

.eval-footer {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--color-border-light);
}
.eval-hint { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

/* 结果页 */
.eval-result { display: flex; flex-direction: column; gap: 20px; }
.result-header { text-align: center; margin-bottom: 8px; }
.result-header h2 { font-size: var(--font-size-2xl); margin-bottom: 12px; }
.level-badge { display: inline-block; padding: 8px 32px; border-radius: var(--radius-xl); color: #fff; font-size: var(--font-size-xl); font-weight: 700; margin-bottom: 8px; }
.level-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); }

.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }

.simple-radar { display: flex; flex-direction: column; gap: 14px; }
.radar-dim { display: flex; align-items: center; gap: 12px; }
.dim-label { width: 72px; font-size: var(--font-size-sm); text-align: right; }
.dim-bar-bg { flex: 1; height: 10px; background: #F0F0F0; border-radius: 5px; overflow: hidden; }
.dim-bar-fill { height: 100%; background: var(--color-primary); border-radius: 5px; transition: width 0.8s; }
.dim-bar-fill.low { background: var(--color-warning); }
.dim-score { width: 40px; font-size: var(--font-size-sm); font-weight: 600; }

.weak-list { display: flex; flex-direction: column; gap: 10px; }
.weak-item { display: flex; align-items: center; gap: 12px; }
.weak-name { width: 72px; font-size: var(--font-size-sm); }
.weak-rate { width: 40px; font-size: var(--font-size-sm); font-weight: 600; color: var(--color-error); }
.weak-bar { flex: 1; height: 6px; background: #F0F0F0; border-radius: 3px; overflow: hidden; }
.weak-bar-fill { height: 100%; border-radius: 3px; }

.result-advice ul { padding-left: 20px; }
.result-advice li { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 6px; }

.result-actions { display: flex; gap: 12px; justify-content: center; margin-top: 12px; }
</style>
