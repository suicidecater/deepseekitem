<script setup lang="ts">
// src/views/student/EvaluationView.vue - 能力基线测评页
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import { useAuthStore } from '@/stores/auth'
import { useTimer } from '@/composables/useTimer'
import QuestionCard from '@/components/business/QuestionCard.vue'
import RadarChart from '@/components/charts/RadarChart.vue'

const router = useRouter()
const route = useRoute()
const examStore = useExamStore()
const authStore = useAuthStore()

type Phase = 'intro' | 'loading' | 'testing' | 'result'
const phase = ref<Phase>('intro')
const evaluationResult = ref<any>(null)
const selectedAnswer = ref('')

// 是否强制测评模式
const isRequired = computed(() => route.query.required === '1')

// 方向名称
const directionNames: Record<number, string> = { 1: '科目一', 4: '科目四', 5: '专业人员' }
const directionName = computed(() => directionNames[authStore.studySubject] || '科目一')

// 倒计时（每题45秒）
const timer = useTimer(45, handleTimeout)

// 能力等级
const abilityLevel = computed(() => {
  if (!evaluationResult.value) return null
  const avg = evaluationResult.value.correctRate
  if (avg >= 95) return { level: '冲刺', color: '#52C41A', desc: '基础扎实，可以直接冲刺考试！' }
  if (avg >= 85) return { level: '进阶', color: '#1677FF', desc: '有一定基础，重点突破薄弱环节' }
  if (avg >= 70) return { level: '基础', color: '#FAAD14', desc: '需要系统学习交通法规知识' }
  return { level: '入门', color: '#FF4D4F', desc: '建议从头系统学习，打好基础' }
})

// 难度拆分数据
const difficultyData = computed(() => evaluationResult.value?.difficultyBreakdown || {})

// 雷达图数据
const radarChartData = computed(() => {
  const rd = evaluationResult.value?.radarData
  if (!rd) return []
  return [
    {
      label: '当前能力',
      data: rd.current || [],
      color: '#1677FF',
    },
    {
      label: '基准线',
      data: rd.baseline || [],
      color: '#999',
      fill: false,
      dashed: true,
    },
  ]
})

onMounted(() => {
  // 等待用户点击"开始测评"
})

async function startEvaluation() {
  phase.value = 'loading'
  try {
    await examStore.loadQuestions({
      mode: 'evaluation',
      subject: 1,
      count: 0,
      difficulty: 0
    })
    phase.value = 'testing'
    timer.start()
  } catch {
    phase.value = 'intro'
    alert('题目加载失败，请重试')
  }
}

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
  // 测评完成，更新当前方向的测评状态
  if (authStore.userInfo) {
    const dir = String(authStore.studySubject)
    if (!authStore.userInfo.evaluationStatusMap) {
      authStore.userInfo.evaluationStatusMap = {}
    }
    authStore.userInfo.evaluationStatusMap[dir] = 1
    authStore.userInfo.evaluationStatus = 1
  }
  phase.value = 'result'
}

function goToStudyPlan() {
  router.push('/student/study-plan?direction=' + authStore.studySubject)
}

function goToReport() {
  router.push('/student/report')
}

function goHome() {
  router.push('/student/home')
}
</script>

<template>
  <div class="evaluation-page">
    <!-- 介绍页 -->
    <div v-if="phase === 'intro'" class="eval-intro">
      <h2>{{ directionName }} · 能力基线测评</h2>
      <div class="intro-cards">
        <div class="intro-card">
          <span class="intro-icon">📐</span>
          <strong>四维度评估</strong>
          <p>交通标志 / 交通法规 / 安全常识 / 驾驶理论</p>
        </div>
        <div class="intro-card">
          <span class="intro-icon">⭐</span>
          <strong>两难度分层</strong>
          <p>简单题 + 中等题，精准定位薄弱环节</p>
        </div>
        <div class="intro-card">
          <span class="intro-icon">📝</span>
          <strong>共80道精选题目</strong>
          <p>每题45秒，选择后自动跳转，不可回退</p>
        </div>
      </div>
      <div class="intro-tips">
        <p>💡 测评完成后，系统将根据你的薄弱点生成 <strong>AI个性化学习路径</strong></p>
        <p>💡 测评结果将展示四级 <strong>能力雷达图</strong>，明确优势与短板</p>
        <p v-if="authStore.evaluationStatus" class="intro-tips-warn">⚠️ 该方向已有测评记录，重新测评将覆盖之前的数据</p>
      </div>
      <button class="btn btn-primary btn-lg" @click="startEvaluation">
        开始测评 →
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="phase === 'loading'" class="loading-state">
      <div class="spinner"></div>
      <p>正在准备测评题目...</p>
    </div>

    <!-- 测评阶段 -->
    <template v-if="phase === 'testing' && examStore.currentQuestion">
      <div class="eval-header">
        <h2>{{ directionName }} · 能力基线测评</h2>
        <p class="eval-desc">共{{ examStore.totalCount }}题，四维度（交通标志/交通法规/安全常识/驾驶理论）× 两难度评估</p>
        <div class="eval-progress-bar">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{ width: ((examStore.currentIndex) / Math.max(examStore.totalCount, 1)) * 100 + '%' }"
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

        <!-- 能力雷达图（Chart.js） -->
        <div class="result-radar card">
          <h3>四维能力分析</h3>
          <RadarChart
            :dimensions="evaluationResult.radarData?.dimensions || []"
            :datasets="radarChartData"
            height="340"
          />
        </div>

        <!-- 难度分解柱状图 -->
        <div v-if="Object.keys(difficultyData).length" class="result-difficulty card">
          <h3>难度维度分解</h3>
          <div class="diff-grid">
            <div v-for="(info, dimName) in difficultyData" :key="dimName" class="diff-dim">
              <span class="diff-dim-name">{{ dimName }}</span>
              <div class="diff-bars">
                <div class="diff-row">
                  <span class="diff-label">⭐ 简单</span>
                  <div class="diff-bar-bg">
                    <div
                      class="diff-bar-fill easy"
                      :style="{ width: (info.diff1Rate || 0) + '%' }"
                    ></div>
                  </div>
                  <span class="diff-value">{{ info.diff1Correct || 0 }}/{{ info.diff1Total || 0 }} ({{ info.diff1Rate || 0 }}%)</span>
                </div>
                <div class="diff-row">
                  <span class="diff-label">⭐⭐ 中等</span>
                  <div class="diff-bar-bg">
                    <div
                      class="diff-bar-fill hard"
                      :style="{ width: (info.diff2Rate || 0) + '%' }"
                      :class="{ bad: (info.diff2Rate || 0) < 60 }"
                    ></div>
                  </div>
                  <span class="diff-value">{{ info.diff2Correct || 0 }}/{{ info.diff2Total || 0 }} ({{ info.diff2Rate || 0 }}%)</span>
                </div>
              </div>
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
          <button class="btn btn-primary btn-lg" @click="goToReport">
            查看完整报告 →
          </button>
          <button v-if="!isRequired" class="btn btn-outline btn-lg" @click="goHome">
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

/* ========== 介绍页 ========== */
.eval-intro {
  text-align: center;
  padding: 48px 24px;
}
.eval-intro h2 {
  font-size: var(--font-size-2xl);
  margin-bottom: 32px;
}
.intro-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
}
.intro-card {
  flex: 1;
  min-width: 160px;
  max-width: 200px;
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 20px 16px;
  border: 1px solid var(--color-border-light);
  text-align: center;
}
.intro-icon {
  display: block;
  font-size: 32px;
  margin-bottom: 8px;
}
.intro-card strong {
  display: block;
  font-size: var(--font-size-base);
  margin-bottom: 4px;
}
.intro-card p {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin: 0;
}
.intro-tips {
  background: #F6F8FA;
  border-radius: var(--radius-md);
  padding: 16px 24px;
  margin-bottom: 32px;
  display: inline-block;
  text-align: left;
}
.intro-tips p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 8px 0;
}
.intro-tips-warn {
  color: var(--color-warning) !important;
}
.btn-lg {
  padding: 14px 48px;
  font-size: var(--font-size-lg);
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

.weak-list { display: flex; flex-direction: column; gap: 10px; }
.weak-item { display: flex; align-items: center; gap: 12px; }
.weak-name { width: 72px; font-size: var(--font-size-sm); }
.weak-rate { width: 40px; font-size: var(--font-size-sm); font-weight: 600; color: var(--color-error); }
.weak-bar { flex: 1; height: 6px; background: #F0F0F0; border-radius: 3px; overflow: hidden; }
.weak-bar-fill { height: 100%; border-radius: 3px; }

.result-advice ul { padding-left: 20px; }
.result-advice li { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 6px; }

.result-actions { display: flex; gap: 12px; justify-content: center; margin-top: 12px; }

/* 难度分解柱状图 */
.result-difficulty h3 { margin-bottom: 14px; }
.diff-grid { display: flex; flex-direction: column; gap: 16px; }
.diff-dim { display: flex; align-items: flex-start; gap: 12px; }
.diff-dim-name { width: 72px; font-size: var(--font-size-sm); font-weight: 600; text-align: right; flex-shrink: 0; padding-top: 2px; }
.diff-bars { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.diff-row { display: flex; align-items: center; gap: 10px; }
.diff-label { width: 52px; font-size: 12px; color: var(--color-text-tertiary); flex-shrink: 0; text-align: right; }
.diff-bar-bg { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.diff-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s; }
.diff-bar-fill.easy { background: #52C41A; }
.diff-bar-fill.hard { background: #1677FF; }
.diff-bar-fill.bad { background: #FF4D4F; }
.diff-value { width: 120px; font-size: 11px; color: var(--color-text-secondary); flex-shrink: 0; }
</style>
