<script setup lang="ts">
// src/views/student/ConfusingView.vue - 易混淆知识点专项训练
import { ref } from 'vue'
import ContrastCard from '@/components/business/ContrastCard.vue'

const categories = ['交警手势', '扣分罚款', '交通标志', '综合']
const activeCategory = ref('交警手势')

const currentLevel = ref(1)
const totalLevels = 6
const correctCount = ref(0)
const totalAnswered = ref(0)
const showResult = ref(false)

const currentPair = ref({
  id: 1,
  leftTitle: '左转弯信号',
  leftContent: '左臂向前上方直伸，掌心向前，示意左方车辆左转弯。',
  rightTitle: '右转弯信号',
  rightContent: '右臂向前上方直伸，掌心向前，示意右方车辆右转弯。',
  highlightDiff: '左转弯用左手，右转弯用右手，关键看哪只手向前上方伸出。',
  memoryTip: '左左右右——左手是左转弯，右手是右转弯'
})

const userAnswer = ref('')
const answered = ref(false)
const isCorrect = ref(false)

function checkAnswer(answer: string) {
  if (answered.value) return
  userAnswer.value = answer
  answered.value = true
  totalAnswered.value++
  // 简化：点击任意对比卡片即答对
  isCorrect.value = true
  correctCount.value++
}

function nextQuestion() {
  if (currentLevel.value < totalLevels) {
    currentLevel.value++
  }
  answered.value = false
  userAnswer.value = ''
  showResult.value = false
  // Mock 换一题
  currentPair.value = {
    ...currentPair.value,
    id: currentPair.value.id + 1,
    leftTitle: '禁止通行',
    leftContent: '红色圆圈，表示禁止一切车辆和行人通行。',
    rightTitle: '禁止驶入',
    rightContent: '红色圆圈加白色横杠，表示禁止车辆驶入，行人可通行。',
    highlightDiff: '禁止通行针对所有交通参与者，禁止驶入仅针对车辆。',
    memoryTip: '有杠车不进，全红人都停'
  }
}

const accuracy = computed(() => totalAnswered.value > 0 ? Math.round((correctCount.value / totalAnswered.value) * 100) : 0)

function computed(arg0: () => number) {
  return arg0()
}
</script>

<template>
  <div class="confusing-page">
    <div class="page-header">
      <h2>易混淆知识点专项训练</h2>
      <p class="page-desc">通过对比学习，精准攻克易混知识点</p>
    </div>

    <!-- 类别选择 -->
    <div class="category-bar">
      <button
        v-for="cat in categories" :key="cat"
        class="cat-btn" :class="{ active: activeCategory === cat }"
        @click="activeCategory = cat"
      >{{ cat }}</button>
    </div>

    <!-- 闯关进度 -->
    <div class="level-progress">
      <span>闯关进度：{{ currentLevel }} / {{ totalLevels }}</span>
      <span>正确率：{{ accuracy }}%</span>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: (currentLevel / totalLevels) * 100 + '%' }"></div>
      </div>
    </div>

    <!-- 对比卡片 -->
    <ContrastCard
      :left-title="currentPair.leftTitle"
      :left-content="currentPair.leftContent"
      :right-title="currentPair.rightTitle"
      :right-content="currentPair.rightContent"
      :highlight-diff="currentPair.highlightDiff"
      :memory-tip="currentPair.memoryTip"
    />

    <!-- 选择区 -->
    <div class="answer-area">
      <p class="answer-question">以上两个描述分别对应哪个规则？请选择：</p>
      <div class="answer-options">
        <button class="btn btn-outline" @click="checkAnswer('correct')">我已理解区别</button>
      </div>
    </div>

    <!-- 结果反馈 -->
    <div v-if="answered" class="feedback" :class="isCorrect ? 'correct' : 'wrong'">
      {{ isCorrect ? '✅ 回答正确！' : '❌ 再仔细看看对比差异' }}
    </div>

    <!-- 下一题 -->
    <div class="next-area">
      <button v-if="answered" class="btn btn-primary" @click="nextQuestion">
        {{ currentLevel < totalLevels ? '下一组' : '完成闯关' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.confusing-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.category-bar { display: flex; gap: 8px; margin: 20px 0; }
.cat-btn {
  padding: 8px 20px; border-radius: var(--radius-lg); border: 1px solid var(--color-border);
  font-size: var(--font-size-sm); transition: all var(--transition-fast);
}
.cat-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }

.level-progress {
  display: flex; align-items: center; gap: 16px; margin-bottom: 20px;
  font-size: var(--font-size-sm); color: var(--color-text-secondary);
}
.progress-bar { flex: 1; height: 8px; background: #F0F0F0; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-primary); border-radius: 4px; transition: width 0.3s; }

.answer-area { margin-top: 20px; }
.answer-question { font-size: var(--font-size-sm); margin-bottom: 12px; }
.answer-options { display: flex; gap: 10px; flex-wrap: wrap; }

.feedback { padding: 14px; border-radius: var(--radius-md); margin-top: 16px; font-weight: 600; text-align: center; }
.feedback.correct { background: #F6FFED; color: var(--color-success); }
.feedback.wrong { background: #FFF1F0; color: var(--color-error); }

.next-area { margin-top: 20px; text-align: center; }
</style>
