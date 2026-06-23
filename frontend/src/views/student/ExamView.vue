<script setup lang="ts">
// src/views/student/ExamView.vue - 全真模拟考试页
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import { useTimer } from '@/composables/useTimer'
import { useFullscreen } from '@/composables/useFullscreen'
import { useAppStore } from '@/stores/app'
import QuestionCard from '@/components/business/QuestionCard.vue'
import ExamNavigator from '@/components/business/ExamNavigator.vue'

const router = useRouter()
const examStore = useExamStore()
const appStore = useAppStore()

type Phase = 'config' | 'exam' | 'result'
const phase = ref<Phase>('config')
const selectedSubject = ref<1 | 4>(1)
const showWarning = ref(false)

const subjectOptions = [
  { label: '科目一', value: 1 as const, count: 100, time: 45 * 60 },
  { label: '科目四', value: 4 as const, count: 50, time: 45 * 60 }
]

const currentSubject = computed(() => subjectOptions.find(s => s.value === selectedSubject.value))

// 防切窗
const fullscreen = useFullscreen(handleForceSubmit)

// 倒计时
const timer = useTimer(currentSubject.value?.time || 45 * 60, handleTimeout)

const selectedAnswer = ref('')

async function startExam() {
  const subject = currentSubject.value!
  await examStore.loadQuestions({
    mode: 'exam',
    subject: subject.value,
    count: subject.count
  })
  phase.value = 'exam'
  timer.reset(subject.time)
  timer.start()
  await fullscreen.enterFullscreen()
}

function handleAnswer(questionId: number, answer: string) {
  selectedAnswer.value = answer
  examStore.recordAnswer(questionId, answer)
}

function jumpToQuestion(index: number) {
  examStore.jumpTo(index)
  const q = examStore.questions[index]
  selectedAnswer.value = examStore.answers.get(q?.id || 0) || ''
}

function toggleMark() {
  const q = examStore.currentQuestion
  if (q) examStore.toggleMark(q.id)
}

function handleTimeout() {
  appStore.showToast('考试时间到，自动交卷！', 'error')
  handleSubmit()
}

function handleForceSubmit() {
  appStore.showToast('切屏超过3次，强制交卷！', 'error')
  handleSubmit()
}

async function handleSubmit() {
  timer.stop()
  fullscreen.exitFullscreen()
  const records = Array.from(examStore.answers.entries()).map(([questionId, answer]) => {
    const q = examStore.questions.find(x => x.id === questionId)
    return {
      questionId,
      answer,
      correct: q?.answer === answer,
      timeSpent: 0
    }
  })
  await examStore.submit(records)
  phase.value = 'result'
}

function restart() {
  examStore.reset()
  phase.value = 'config'
  selectedAnswer.value = ''
}

onMounted(() => {
  // 自动全屏（已在路由守卫中触发 requestFullscreen）
})

onUnmounted(() => {
  timer.stop()
  fullscreen.exitFullscreen()
})
</script>

<template>
  <div class="exam-page">
    <!-- 配置页 -->
    <template v-if="phase === 'config'">
      <div class="exam-config card">
        <h2>全真模拟考试</h2>
        <p class="config-desc">请选择考试科目，考试期间将进入全屏模式</p>

        <div class="subject-options">
          <button
            v-for="opt in subjectOptions" :key="opt.value"
            class="subject-btn"
            :class="{ active: selectedSubject === opt.value }"
            @click="selectedSubject = opt.value"
          >
            <span class="subject-name">{{ opt.label }}</span>
            <span class="subject-info">{{ opt.count }}题 · {{ opt.time / 60 }}分钟</span>
            <span class="subject-pass">合格线：{{ opt.value === 1 ? 90 : 90 }}分</span>
          </button>
        </div>

        <div class="exam-rules">
          <h4>考试规则</h4>
          <ul>
            <li>科目一：100题，45分钟，90分合格</li>
            <li>科目四：50题，45分钟，90分合格</li>
            <li>考试期间请勿切屏，超过3次将自动交卷</li>
            <li>到时间将自动交卷并评分</li>
          </ul>
        </div>

        <button class="btn btn-primary btn-lg btn-block" @click="startExam">开始考试</button>
      </div>
    </template>

    <!-- 考试中 -->
    <template v-if="phase === 'exam'">
      <!-- 切屏警告 -->
      <div v-if="fullscreen.showWarning" class="cheat-warning">
        {{ fullscreen.warningMessage }}
      </div>

      <div class="exam-header">
        <div class="exam-title">
          <h2>{{ currentSubject?.label }} · 全真模拟考试</h2>
          <span class="exam-progress">{{ examStore.currentIndex + 1 }}/{{ examStore.totalCount }}</span>
        </div>
        <div class="exam-timer" :class="{ warning: timer.remaining <= 300 }">
          ⏱ {{ timer.displayTime }}
        </div>
      </div>

      <div class="exam-body">
        <div class="exam-sidebar">
          <ExamNavigator
            :total-count="examStore.totalCount"
            :answers="examStore.answers"
            :marked-questions="examStore.markedQuestions"
            :current-index="examStore.currentIndex"
            @jump="jumpToQuestion"
            @submit="handleSubmit"
          />
        </div>

        <div class="exam-main">
          <QuestionCard
            v-if="examStore.currentQuestion"
            :question="examStore.currentQuestion"
            :selected-answer="selectedAnswer"
            :show-result="false"
            @answer="handleAnswer"
          />

          <div class="exam-actions">
            <button class="btn btn-outline" :disabled="examStore.currentIndex === 0" @click="jumpToQuestion(examStore.currentIndex - 1)">
              上一题
            </button>
            <button class="btn btn-outline" @click="toggleMark">
              {{ examStore.markedQuestions.has(examStore.currentQuestion?.id || 0) ? '取消标记' : '标记' }}
            </button>
            <button class="btn btn-outline" :disabled="examStore.currentIndex >= examStore.totalCount - 1" @click="jumpToQuestion(examStore.currentIndex + 1)">
              下一题
            </button>
            <button class="btn btn-primary" @click="handleSubmit">交卷</button>
          </div>
        </div>
      </div>
    </template>

    <!-- 结果 -->
    <template v-if="phase === 'result' && examStore.examResult">
      <div class="exam-result card">
        <h2 :class="examStore.examResult.passed ? 'passed' : 'failed'">
          {{ examStore.examResult.passed ? '恭喜通过！' : '未通过' }}
        </h2>

        <div class="result-stats">
          <div class="result-stat">
            <span class="stat-num" :class="examStore.examResult.passed ? 'correct' : 'wrong'">
              {{ examStore.examResult.score }}
            </span>
            <span class="stat-label">得分</span>
          </div>
          <div class="result-stat">
            <span class="stat-num">{{ examStore.examResult.correctRate }}%</span>
            <span class="stat-label">正确率</span>
          </div>
          <div class="result-stat">
            <span class="stat-num">{{ examStore.examResult.correctCount }}</span>
            <span class="stat-label">正确</span>
          </div>
          <div class="result-stat">
            <span class="stat-num wrong">{{ examStore.examResult.wrongCount }}</span>
            <span class="stat-label">错误</span>
          </div>
        </div>

        <p class="result-time">总用时：{{ Math.floor(timer.remaining / 60) ? (currentSubject!.time / 60 - Math.floor(timer.remaining / 60)) : currentSubject!.time / 60 }}分</p>

        <!-- 知识点正确率 -->
        <div v-if="examStore.examResult.categoryStats?.length" class="category-stats">
          <h4>知识点统计</h4>
          <div v-for="cat in examStore.examResult.categoryStats" :key="cat.name" class="cat-row">
            <span class="cat-name">{{ cat.name }}</span>
            <div class="cat-bar">
              <div class="cat-fill" :style="{ width: cat.rate + '%', background: cat.rate >= 80 ? '#52C41A' : '#FF4D4F' }"></div>
            </div>
            <span class="cat-rate">{{ cat.rate }}%</span>
          </div>
        </div>

        <div class="result-actions">
          <button class="btn btn-outline" @click="restart">重新考试</button>
          <button class="btn btn-primary" @click="router.push('/student/error-book')">查看错题</button>
          <button class="btn btn-outline" @click="router.push('/student/home')">返回首页</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.exam-page { min-height: 100vh; background: var(--color-bg); padding: 16px; }

/* 配置 */
.exam-config { max-width: 640px; margin: 40px auto; padding: 32px; background: #fff; border-radius: var(--radius-xl); border: 1px solid var(--color-border-light); }
.exam-config h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.config-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); margin-bottom: 24px; }

.subject-options { display: flex; gap: 16px; margin-bottom: 24px; }
.subject-btn {
  flex: 1; padding: 24px 16px; border-radius: var(--radius-lg); border: 2px solid var(--color-border);
  text-align: center; transition: all var(--transition-fast);
}
.subject-btn.active { border-color: var(--color-primary); background: var(--color-primary-light); }
.subject-name { display: block; font-size: var(--font-size-xl); font-weight: 700; margin-bottom: 6px; }
.subject-info { display: block; font-size: var(--font-size-xs); color: var(--color-text-secondary); }
.subject-pass { display: block; font-size: 11px; color: var(--color-success); margin-top: 4px; }

.exam-rules { background: #FAFAFA; border-radius: var(--radius-md); padding: 16px; margin-bottom: 24px; }
.exam-rules h4 { font-size: var(--font-size-sm); margin-bottom: 8px; }
.exam-rules ul { padding-left: 20px; }
.exam-rules li { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin-bottom: 4px; }

/* 考试中 */
.cheat-warning {
  position: fixed; top: 0; left: 0; right: 0; z-index: 10000;
  background: var(--color-error); color: #fff; text-align: center; padding: 12px; font-weight: 600;
}

.exam-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: #fff; border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light); margin-bottom: 12px;
}
.exam-title { display: flex; align-items: center; gap: 16px; }
.exam-title h2 { font-size: var(--font-size-lg); }
.exam-progress { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
.exam-timer { font-size: var(--font-size-xl); font-weight: 700; }
.exam-timer.warning { color: var(--color-error); animation: pulse 0.5s infinite; }
@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.5 } }

.exam-body { display: flex; gap: 16px; }
.exam-sidebar { width: 200px; flex-shrink: 0; }
.exam-main { flex: 1; min-width: 0; }

.exam-actions {
  display: flex; gap: 12px; margin-top: 20px; padding-top: 16px;
  border-top: 1px solid var(--color-border-light); justify-content: center;
}

/* 结果 */
.exam-result { max-width: 700px; margin: 40px auto; padding: 40px; text-align: center; background: #fff; border-radius: var(--radius-xl); border: 1px solid var(--color-border-light); }
.exam-result h2 { font-size: var(--font-size-2xl); margin-bottom: 24px; }
.exam-result h2.passed { color: var(--color-success); }
.exam-result h2.failed { color: var(--color-error); }

.result-stats { display: flex; justify-content: center; gap: 40px; margin-bottom: 16px; }
.result-stat { text-align: center; }
.stat-num { display: block; font-size: 40px; font-weight: 700; color: var(--color-primary); }
.stat-num.correct { color: var(--color-success); }
.stat-num.wrong { color: var(--color-error); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.result-time { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 24px; }

.category-stats { text-align: left; margin-bottom: 24px; padding: 16px; background: #FAFAFA; border-radius: var(--radius-md); }
.category-stats h4 { font-size: var(--font-size-sm); margin-bottom: 12px; }
.cat-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.cat-name { width: 80px; font-size: var(--font-size-xs); }
.cat-bar { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.cat-fill { height: 100%; border-radius: 4px; }
.cat-rate { width: 40px; font-size: var(--font-size-xs); font-weight: 600; }

.result-actions { display: flex; gap: 12px; justify-content: center; }
</style>
