<script setup lang="ts">
// src/views/student/SceneSimView.vue - 交通场景模拟
import { ref } from 'vue'

const sceneTypes = ['城市道路', '高速公路', '夜间驾驶', '恶劣天气']
const activeScene = ref('城市道路')
const loadingScene = ref(false)

const currentScene = ref({
  title: '城市道路 - 十字路口',
  description: '你正驾驶车辆接近一个交通信号灯控制的十字路口，前方是红灯，右侧有行人准备过马路...',
  image: ''
})

const currentQuestion = ref({
  content: '此时你应该怎么做？',
  options: ['A. 减速慢行，观察信号灯变化', 'B. 加速通过路口', 'C. 鸣笛提醒行人', 'D. 直接右转'],
  answer: 'A'
})

const answered = ref(false)
const showResult = ref(false)
const selectedAnswer = ref('')
const isCorrect = ref(false)

function selectScene(type: string) {
  activeScene.value = type
  loadingScene.value = true
  answered.value = false
  showResult.value = false
  setTimeout(() => { loadingScene.value = false }, 800)
}

function checkAnswer(opt: string) {
  if (answered.value) return
  selectedAnswer.value = opt
  answered.value = true
  isCorrect.value = opt === currentQuestion.value.answer
  showResult.value = true
}

function nextScene() {
  answered.value = false
  showResult.value = false
  selectedAnswer.value = ''
  currentScene.value.title = '高速公路 - 匝道入口'
  currentScene.value.description = '你正在高速公路匝道上加速，准备并入主路，左侧车道有车辆快速驶来...'
  currentQuestion.value = { content: '并线时应注意什么？', options: ['A. 加速直接并入', 'B. 观察后视镜，打转向灯，确认安全后并入', 'C. 减速等待', 'D. 鸣笛提醒'], answer: 'B' }
}
</script>

<template>
  <div class="scene-sim-page">
    <div class="page-header">
      <h2>交通场景模拟</h2>
      <p class="page-desc">AI生成真实交通场景，提升实战应对能力</p>
    </div>

    <!-- 场景类型 -->
    <div class="scene-types">
      <button v-for="type in sceneTypes" :key="type" class="scene-btn" :class="{ active: activeScene === type }" @click="selectScene(type)">{{ type }}</button>
    </div>

    <!-- 场景展示 -->
    <div class="scene-card card">
      <div v-if="loadingScene" class="scene-loading">
        <div class="spinner"></div>
        <p>AI正在生成场景...</p>
      </div>
      <template v-else>
        <div class="scene-image">
          <div class="scene-placeholder">🚗 {{ activeScene }}场景模拟</div>
        </div>
        <h3>{{ currentScene.title }}</h3>
        <p class="scene-desc">{{ currentScene.description }}</p>
      </template>
    </div>

    <!-- 判断题 -->
    <div v-if="!loadingScene" class="scene-question card">
      <p class="question-text">{{ currentQuestion.content }}</p>
      <div class="question-options">
        <button
          v-for="(opt, idx) in currentQuestion.options" :key="idx"
          class="option-btn"
          :class="{
            selected: selectedAnswer === opt[0],
            correct: showResult && opt[0] === currentQuestion.answer,
            wrong: showResult && selectedAnswer === opt[0] && opt[0] !== currentQuestion.answer
          }"
          @click="checkAnswer(opt[0])"
          :disabled="answered"
        >{{ opt }}</button>
      </div>

      <div v-if="showResult" class="result-feedback" :class="isCorrect ? 'correct' : 'wrong'">
        {{ isCorrect ? '✅ 正确！你做出了安全的选择。' : '❌ 错误。注意观察路况，确保安全第一。' }}
      </div>

      <button v-if="showResult" class="btn btn-primary mt-4" @click="nextScene">下一场景</button>
    </div>
  </div>
</template>

<style scoped>
.scene-sim-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.scene-types { display: flex; gap: 8px; margin: 20px 0; flex-wrap: wrap; }
.scene-btn {
  padding: 8px 20px; border-radius: var(--radius-lg); border: 1px solid var(--color-border);
  font-size: var(--font-size-sm); transition: all var(--transition-fast);
}
.scene-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }

.scene-loading { display: flex; flex-direction: column; align-items: center; padding: 40px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 12px; }
@keyframes spin { to { transform: rotate(360deg); } }

.scene-card { padding: 24px; }
.scene-image { margin-bottom: 16px; }
.scene-placeholder {
  height: 200px; background: linear-gradient(135deg, #E6F4FF, #F0F5FF);
  border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center;
  font-size: var(--font-size-xl); color: var(--color-primary);
}
.scene-card h3 { font-size: var(--font-size-lg); margin-bottom: 8px; }
.scene-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); line-height: 1.8; }

.scene-question { padding: 24px; }
.question-text { font-size: var(--font-size-base); font-weight: 500; margin-bottom: 16px; }
.question-options { display: flex; flex-direction: column; gap: 8px; }
.option-btn {
  text-align: left; padding: 12px 16px; border-radius: var(--radius-md); border: 1px solid var(--color-border);
  font-size: var(--font-size-sm); transition: all var(--transition-fast);
}
.option-btn:hover:not(:disabled) { border-color: var(--color-primary); background: var(--color-primary-light); }
.option-btn.selected { border-color: var(--color-primary); background: var(--color-primary-light); }
.option-btn.correct { border-color: var(--color-success); background: #F6FFED; }
.option-btn.wrong { border-color: var(--color-error); background: #FFF1F0; }
.option-btn:disabled { cursor: not-allowed; }

.result-feedback { padding: 14px; border-radius: var(--radius-md); margin-top: 16px; font-weight: 600; text-align: center; }
.result-feedback.correct { background: #F6FFED; color: var(--color-success); }
.result-feedback.wrong { background: #FFF1F0; color: var(--color-error); }

.card { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.mt-4 { margin-top: 16px; }
</style>
