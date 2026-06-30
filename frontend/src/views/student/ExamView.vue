<script setup lang="ts">
// src/views/student/ExamView.vue - 全真模拟考试页
import { ref, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import { useTimer } from '@/composables/useTimer'
import { useAppStore } from '@/stores/app'
import QuestionCard from '@/components/business/QuestionCard.vue'


const router = useRouter()
const examStore = useExamStore()
const appStore = useAppStore()

type Phase = 'config' | 'exam' | 'result'
const phase = ref<Phase>('config')
const selectedSubject = ref<1 | 4 | 5>(1)

const subjectOptions = [
  { label: '科目一', value: 1 as const, count: 100, time: 45 * 60, desc: '道路交通安全法律、法规和相关知识' },
  { label: '科目四', value: 4 as const, count: 50, time: 30 * 60, desc: '安全文明驾驶常识' },
  { label: '专业人员', value: 5 as const, count: 50, time: 30 * 60, desc: '客货运/危险品从业资格培训' },
]

const currentSubject = computed(() => subjectOptions.find(s => s.value === selectedSubject.value))

// 倒计时
const timer = useTimer(currentSubject.value?.time || 45 * 60, handleTimeout)

const selectedAnswer = ref('')

// 交卷确认弹窗
const showConfirmModal = ref(false)
const submitting = ref(false)

// 结果页查看题目模式
const showReview = ref(false)
const reviewIndex = ref(0)

// 导航面板
const navItems = computed(() => {
  return examStore.questions.map((q, i) => ({
    index: i,
    id: q.id,
    label: i + 1,
    answered: examStore.answers.has(q.id),
    current: i === examStore.currentIndex,
  }))
})
const answeredCount = computed(() => examStore.answers.size)

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

function handleTimeout() {
  appStore.showToast('考试时间到，自动交卷！', 'error')
  showConfirmModal.value = false
  doSubmit()
}

function handleSubmit() {
  showConfirmModal.value = true
}

async function doSubmit() {
  showConfirmModal.value = false
  submitting.value = true
  try {
    timer.stop()
    const result = await examStore.submit((currentSubject.value?.time || 0) - timer.remaining)
    if (!result) {
      throw new Error('提交失败，未获取到考试结果')
    }
    phase.value = 'result'
  } catch (e: any) {
    const msg = e?.message || e?.response?.data?.message || '交卷失败，请重试'
    appStore.showToast(msg, 'error')
    // 恢复计时器，让用户可以继续答题
    timer.start()
    // 重新打开确认弹窗让用户决定
    showConfirmModal.value = true
  } finally {
    submitting.value = false
  }
}

function confirmSubmit() {
  doSubmit()
}

function cancelSubmit() {
  showConfirmModal.value = false
}

function openReview() {
  reviewIndex.value = 0
  showReview.value = true
}

function closeReview() {
  showReview.value = false
}

function reviewPrev() {
  if (reviewIndex.value > 0) reviewIndex.value--
}

function reviewNext() {
  if (reviewIndex.value < examStore.reviewQuestions.length - 1) reviewIndex.value++
}

function restart() {
  showReview.value = false
  reviewIndex.value = 0
  examStore.reset()
  phase.value = 'config'
  selectedAnswer.value = ''
}

onUnmounted(() => {
  timer.stop()
})
</script>

<template>
  <div class="exam-page">
    <!-- 配置页 -->
    <template v-if="phase === 'config'">
      <div class="exam-config card">
        <h2>全真模拟考试</h2>
        <p class="config-desc">请选择考试科目，开始模拟考试</p>

        <div class="subject-options">
          <button
            v-for="opt in subjectOptions" :key="opt.value"
            class="subject-btn"
            :class="{ active: selectedSubject === opt.value }"
            @click="selectedSubject = opt.value"
          >
            <span class="subject-name">{{ opt.label }}</span>
            <span class="subject-info">{{ opt.count }}题 · {{ opt.time / 60 }}分钟</span>
            <span class="subject-pass">合格线：90分</span>
          </button>
        </div>

        <div class="exam-rules">
          <h4>考试规则</h4>
          <ul>
            <li>科目一：100题（判断40+单选60），45分钟，90分合格</li>
            <li>科目四：50题（判断20+单选20+多选10），30分钟，90分合格</li>
            <li>专业人员：50题（判断20+单选20+多选10），30分钟，90分合格</li>
            <li>到时间将自动交卷并评分</li>
          </ul>
        </div>

        <button class="btn btn-primary btn-lg btn-block" @click="startExam">开始考试</button>
      </div>
    </template>

    <!-- 考试中 -->
    <template v-if="phase === 'exam'">
      <!-- 交卷确认弹窗 -->
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="cancelSubmit">
        <div class="confirm-modal card">
          <div class="confirm-icon">⚠️</div>
          <h3>确认交卷</h3>
          <p class="confirm-desc">
            您已完成 <strong>{{ answeredCount }}</strong> / {{ examStore.totalCount }} 题，<br/>
            未作答的题目将计为错误，确定要交卷吗？
          </p>
          <div class="confirm-actions">
            <button class="btn btn-outline" @click="cancelSubmit">继续答题</button>
            <button class="btn btn-primary" @click="confirmSubmit">确认交卷</button>
          </div>
        </div>
      </div>

      <!-- 提交中全屏锁定遮罩（不可关闭、不可打断） -->
      <div v-if="submitting" class="submitting-overlay">
        <div class="submitting-box">
          <div class="submitting-spinner"></div>
          <p class="submitting-text">正在提交试卷...</p>
          <p class="submitting-hint">请勿关闭页面或刷新</p>
        </div>
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

      <!-- 居中题目区域 -->
      <div class="exam-center">
        <QuestionCard
          v-if="examStore.currentQuestion"
          :question="examStore.currentQuestion"
          :question-index="examStore.currentIndex + 1"
          :selected-answer="selectedAnswer"
          :show-result="false"
          @answer="handleAnswer"
        />

        <div class="exam-actions">
          <button class="btn btn-outline" :disabled="examStore.currentIndex === 0" @click="jumpToQuestion(examStore.currentIndex - 1)">
            上一题
          </button>
          <button class="btn btn-outline" :disabled="examStore.currentIndex >= examStore.totalCount - 1" @click="jumpToQuestion(examStore.currentIndex + 1)">
            下一题
          </button>
          <button class="btn btn-primary" @click="handleSubmit">交卷</button>
        </div>
      </div>

      <!-- 右上角悬浮导航面板 -->
      <div class="nav-panel">
        <div class="nav-panel-inner">
          <div class="nav-title">答题卡 {{ answeredCount }}/{{ examStore.totalCount }}</div>
          <div class="nav-grid">
            <button
              v-for="item in navItems" :key="item.index"
              class="nav-dot"
              :class="{ answered: item.answered, current: item.current }"
              :title="`第${item.label}题`"
              @click="jumpToQuestion(item.index)"
            >
              {{ item.label }}
            </button>
          </div>
          <button class="nav-submit-btn" @click="handleSubmit">交 卷</button>
        </div>
      </div>
    </template>

    <!-- 结果 - 查看题目 -->
    <template v-if="phase === 'result' && showReview && examStore.reviewQuestions.length">
      <div class="exam-header">
        <div class="exam-title">
          <h2>答卷回顾</h2>
          <span class="exam-progress">{{ reviewIndex + 1 }}/{{ examStore.reviewQuestions.length }}</span>
        </div>
        <button class="btn btn-outline" @click="closeReview">返回成绩</button>
      </div>
      <div class="exam-center">
        <div class="review-question-card">
          <QuestionCard
            :question="{
              id: examStore.reviewQuestions[reviewIndex].id,
              type: examStore.reviewQuestions[reviewIndex].type as any,
              content: examStore.reviewQuestions[reviewIndex].content,
              options: examStore.reviewQuestions[reviewIndex].options,
              image: examStore.reviewQuestions[reviewIndex].image,
              answer: examStore.reviewQuestions[reviewIndex].answer,
            }"
            :question-index="reviewIndex + 1"
            :selected-answer="examStore.reviewQuestions[reviewIndex].userAnswer"
            :show-result="true"
            :disabled="true"
          />
        </div>
        <div class="exam-actions">
          <button class="btn btn-outline" :disabled="reviewIndex === 0" @click="reviewPrev">上一题</button>
          <button class="btn btn-outline" :disabled="reviewIndex >= examStore.reviewQuestions.length - 1" @click="reviewNext">下一题</button>
        </div>
      </div>
    </template>

    <!-- 结果 - 成绩单 -->
    <template v-if="phase === 'result' && examStore.examResult && !showReview">
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
          <button class="btn btn-primary" @click="openReview">查看答卷</button>
          <button class="btn btn-outline" @click="router.push('/student/home')">返回首页</button>
          <button class="btn btn-outline" @click="restart">重新考试</button>
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
/* 交卷确认弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.confirm-modal {
  width: 380px;
  padding: 32px;
  text-align: center;
  background: #fff;
  border-radius: var(--radius-xl);
}
.confirm-icon { font-size: 48px; margin-bottom: 12px; }
.confirm-modal h3 { font-size: var(--font-size-xl); margin-bottom: 12px; }
.confirm-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 24px; line-height: 1.8; }
.confirm-actions { display: flex; gap: 12px; justify-content: center; }

/* 提交中全屏锁定 */
.submitting-overlay {
  position: fixed;
  inset: 0;
  z-index: 10001;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: all;
}
.submitting-box {
  text-align: center;
  padding: 40px 48px;
  background: #fff;
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.submitting-spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 20px;
  border: 4px solid #E8E8E8;
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.submitting-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}
.submitting-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
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

.exam-center { max-width: 760px; margin: 0 auto; }

.exam-actions {
  display: flex; gap: 12px; margin-top: 20px; padding-top: 16px;
  justify-content: center;
}

/* 右上角悬浮导航面板 */
.nav-panel {
  position: fixed;
  right: 0; top: 0;
  width: 260px;
  height: 100vh;
  z-index: 1000;
  transform: translateX(calc(100% - 14px));
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.nav-panel:hover {
  transform: translateX(0);
}
.nav-panel::before {
  content: '';
  position: absolute;
  left: -8px; top: 0; bottom: 0;
  width: 8px;
}
.nav-panel-inner {
  height: 100%;
  padding: 24px 16px;
  background: #fff;
  border-left: 1px solid var(--color-border-light);
  box-shadow: -4px 0 20px rgba(0,0,0,0.08);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.nav-panel::after {
  content: '';
  position: absolute;
  left: 4px; top: 50%;
  transform: translateY(-50%);
  width: 5px; height: 56px;
  border-radius: 5px;
  background: rgba(22, 119, 255, 0.3);
  transition: opacity 0.2s;
}
.nav-panel:hover::after {
  opacity: 0;
}
.nav-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 16px;
}
.nav-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  flex: 1;
  align-content: start;
}
.nav-dot {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 2px solid #d9d9d9;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  padding: 0;
  margin: 0 auto;
}
.nav-dot:hover {
  transform: scale(1.12);
  border-color: var(--color-primary);
}
.nav-dot.answered {
  background: #434343;
  color: #fff;
  border-color: #434343;
}
.nav-dot.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.2);
  color: var(--color-primary);
  font-weight: 700;
}
.nav-dot.current.answered {
  color: #fff;
}
.nav-submit-btn {
  margin-top: 16px;
  padding: 12px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-error);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.nav-submit-btn:hover {
  opacity: 0.9;
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

.result-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }



</style>
