# 业务组件设计文档

> **版本**: V1.0 | **技术栈**: Vue 3 + ECharts 5 + TypeScript

---

## 1. RadarChart - 四维度能力雷达图

基于 ECharts 5.x，展示交通标志/法规/安全常识/驾驶理论四维度。

```vue
<!-- src/components/business/RadarChart.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { RadarChart as EChartsRadar } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([EChartsRadar, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

interface Props {
  data: {
    dimensions: string[]     // ['交通标志', '交通法规', '安全常识', '驾驶理论']
    current: number[]        // [85, 72, 90, 65]  当前得分
    baseline?: number[]      // [60, 60, 60, 60]  基线
    maxValue?: number        // 默认 100
  }
  height?: string            // 默认 '320px'
}

const props = withDefaults(defineProps<Props>(), {
  maxValue: 100,
  height: '320px'
})

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'item' },
    legend: {
      data: ['当前能力', '及格线'],
      bottom: 0
    },
    radar: {
      center: ['50%', '52%'],
      radius: '65%',
      indicator: props.data.dimensions.map(name => ({
        name,
        max: props.maxValue
      })),
      axisName: { color: '#595959', fontSize: 13 }
    },
    series: [
      {
        type: 'radar',
        name: '当前能力',
        data: [{ value: props.data.current, name: '当前能力' }],
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#1677FF', width: 2 },
        areaStyle: { color: 'rgba(22, 119, 255, 0.15)' },
        itemStyle: { color: '#1677FF' }
      }
    ]
  }

  // 添加基线（及格线）
  if (props.data.baseline) {
    option.series!.push({
      type: 'radar',
      name: '及格线',
      data: [{ value: props.data.baseline, name: '及格线' }],
      symbol: 'none',
      lineStyle: { color: '#FF4D4F', type: 'dashed', width: 1.5 },
      areaStyle: { opacity: 0 }
    })
  }

  chart.setOption(option)
}

// 响应式尺寸
function handleResize() {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

watch(() => props.data, () => {
  chart?.setOption({
    series: [
      { data: [{ value: props.data.current, name: '当前能力' }] },
      ...(props.data.baseline ? [{ data: [{ value: props.data.baseline, name: '及格线' }] }] : [])
    ]
  })
}, { deep: true })
</script>

<template>
  <div ref="chartRef" :style="{ height, width: '100%' }" />
</template>
```

### 使用示例

```vue
<RadarChart
  :data="{
    dimensions: ['交通标志', '交通法规', '安全常识', '驾驶理论'],
    current: [85, 72, 90, 65],
    baseline: [60, 60, 60, 60]
  }"
/>
```

---

## 2. QuestionCard - 答题卡片

支持判断/单选/多选，即时正误判断与解析展示。

```vue
<!-- src/components/business/QuestionCard.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Question, QuestionOption } from '@/types/exam'

interface Props {
  question: Question
  userAnswer?: string         // 用户已选答案
  showResult?: boolean        // 是否展示对错结果
  showAnalysis?: boolean      // 是否展示解析
  disabled?: boolean          // 禁止作答
}

const props = withDefaults(defineProps<Props>(), {
  showResult: false,
  showAnalysis: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'answer', questionId: number, answer: string): void
}>()

const selectedAnswer = ref<string[]>(props.userAnswer ? props.userAnswer.split(',') : [])

const isCorrect = computed(() => {
  if (!props.showResult || !selectedAnswer.value.length) return null
  const correct = props.question.answer.split(',').sort().join(',')
  const user = selectedAnswer.value.sort().join(',')
  return correct === user
})

const questionTypeLabel = computed(() => {
  const map = { 1: '单选题', 2: '多选题', 3: '判断题', 4: '图片题', 5: '情景题' }
  return map[props.question.type]
})

function handleSelect(optionKey: string) {
  if (props.disabled) return
  if (props.question.type === 2) {
    // 多选题：toggle
    const idx = selectedAnswer.value.indexOf(optionKey)
    if (idx > -1) {
      selectedAnswer.value.splice(idx, 1)
    } else {
      selectedAnswer.value.push(optionKey)
    }
  } else {
    // 单选/判断：直接替换
    selectedAnswer.value = [optionKey]
  }
  emit('answer', props.question.id, selectedAnswer.value.sort().join(','))
}

function isSelected(key: string) {
  return selectedAnswer.value.includes(key)
}

function isCorrectOption(key: string) {
  return props.question.answer.split(',').includes(key)
}
</script>

<template>
  <div class="question-card" :class="{ 'is-correct': isCorrect === true, 'is-wrong': isCorrect === false }">
    <!-- 题号与类型 -->
    <div class="question-card__header">
      <span class="question-card__type">{{ questionTypeLabel }}</span>
      <span class="question-card__difficulty" v-if="question.difficulty">
        {{ '★'.repeat(question.difficulty) }}
      </span>
    </div>

    <!-- 题干 -->
    <div class="question-card__content">
      <p>{{ question.content }}</p>
      <img v-if="question.image" :src="question.image" class="question-card__image" alt="题目图片" />
    </div>

    <!-- 选项 -->
    <div class="question-card__options">
      <div
        v-for="opt in question.options"
        :key="opt.key"
        class="option-item"
        :class="{
          'is-selected': isSelected(opt.key),
          'is-correct-option': showResult && isCorrectOption(opt.key),
          'is-wrong-option': showResult && isSelected(opt.key) && !isCorrectOption(opt.key)
        }"
        @click="handleSelect(opt.key)"
      >
        <span class="option-key">{{ opt.key }}</span>
        <span class="option-text">{{ opt.content }}</span>
        <span v-if="showResult && isCorrectOption(opt.key)" class="option-mark">✓</span>
        <span v-else-if="showResult && isSelected(opt.key) && !isCorrectOption(opt.key)" class="option-mark">✗</span>
      </div>
    </div>

    <!-- 结果反馈 -->
    <div v-if="showResult" class="question-card__result" :class="isCorrect ? 'correct' : 'wrong'">
      {{ isCorrect ? '✓ 回答正确' : '✗ 回答错误' }}
    </div>

    <!-- 解析 -->
    <div v-if="showAnalysis && question.analysis" class="question-card__analysis">
      <h4>题目解析</h4>
      <p>{{ question.analysis }}</p>
      <blockquote v-if="question.law">
        <strong>法规原文：</strong>{{ question.law }}
      </blockquote>
    </div>
  </div>
</template>

<style scoped>
.question-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--color-border);
  transition: border-color 0.3s;
}
.question-card.is-correct { border-color: var(--color-success); }
.question-card.is-wrong { border-color: var(--color-error); }

.question-card__header {
  display: flex; justify-content: space-between;
  margin-bottom: 16px;
}
.question-card__type {
  padding: 2px 8px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 4px; font-size: 12px; font-weight: 600;
}
.question-card__difficulty { color: #FAAD14; font-size: 14px; }

.question-card__content { margin-bottom: 20px; font-size: 16px; line-height: 1.6; }
.question-card__image { max-width: 100%; margin-top: 12px; border-radius: var(--radius-md); }

.question-card__options { display: flex; flex-direction: column; gap: 10px; }

.option-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.option-item:hover:not(.is-correct-option):not(.is-wrong-option) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.option-item.is-selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.option-item.is-correct-option {
  border-color: var(--color-success);
  background: #F6FFED;
}
.option-item.is-wrong-option {
  border-color: var(--color-error);
  background: #FFF2F0;
}
.option-key {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  background: #F0F0F0;
  font-weight: 600; font-size: 14px; flex-shrink: 0;
}
.is-selected .option-key { background: var(--color-primary); color: #fff; }
.option-text { flex: 1; font-size: 14px; }
.option-mark { font-size: 18px; font-weight: 700; }

.question-card__result {
  margin-top: 16px; padding: 12px;
  border-radius: var(--radius-md);
  font-weight: 600; font-size: 15px;
}
.question-card__result.correct { background: #F6FFED; color: var(--color-success); }
.question-card__result.wrong { background: #FFF2F0; color: var(--color-error); }

.question-card__analysis {
  margin-top: 16px; padding: 16px;
  background: #FAFAFA;
  border-radius: var(--radius-md);
}
.question-card__analysis h4 { margin-bottom: 8px; font-size: 14px; }
.question-card__analysis p { font-size: 14px; color: var(--color-text-secondary); line-height: 1.6; }
.question-card__analysis blockquote {
  margin-top: 12px; padding: 10px 14px;
  border-left: 3px solid var(--color-primary);
  background: #fff;
  font-size: 13px; color: var(--color-text-tertiary);
}
</style>
```

---

## 3. ChatBubble - AI 对话气泡

支持用户/AI角色区分、流式输出动画、结构化回答。

```vue
<!-- src/components/business/ChatBubble.vue -->
<script setup lang="ts">
import type { ChatMessage } from '@/types/ai'
import { computed } from 'vue'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

const isUser = computed(() => props.message.role === 'user')
const isStreaming = computed(() => props.message.isStreaming === true)
</script>

<template>
  <div class="chat-bubble" :class="{ 'chat-bubble--user': isUser, 'chat-bubble--ai': !isUser }">
    <!-- 头像 -->
    <div class="chat-bubble__avatar">
      <img v-if="isUser" src="/assets/images/avatar-user.svg" alt="user" />
      <img v-else src="/assets/images/avatar-ai.svg" alt="AI" />
    </div>

    <!-- 内容区 -->
    <div class="chat-bubble__body">
      <div class="chat-bubble__name">{{ isUser ? '我' : 'DeepSeek AI' }}</div>
      <div class="chat-bubble__content">
        <!-- 结构化 AI 回答 -->
        <template v-if="!isUser && message.structured">
          <div v-if="message.structured.knowledge" class="ai-section">
            <h4>📖 知识点解析</h4>
            <p>{{ message.structured.knowledge }}</p>
          </div>
          <div v-if="message.structured.lawText" class="ai-section">
            <h4>📜 法规原文</h4>
            <blockquote>{{ message.structured.lawText }}</blockquote>
          </div>
          <div v-if="message.structured.caseAnalysis" class="ai-section">
            <h4>🚗 案例分析</h4>
            <p>{{ message.structured.caseAnalysis }}</p>
          </div>
        </template>

        <!-- 普通文本 / 流式输出 -->
        <template v-else>
          <p>{{ message.content }}</p>
          <span v-if="isStreaming" class="typing-cursor">|</span>
        </template>
      </div>
      <div class="chat-bubble__time">{{ message.timestamp }}</div>
    </div>
  </div>
</template>

<style scoped>
.chat-bubble {
  display: flex; gap: 12px;
  padding: 12px 16px;
  max-width: 80%;
}
.chat-bubble--user { flex-direction: row-reverse; align-self: flex-end; }
.chat-bubble--ai { align-self: flex-start; }

.chat-bubble__avatar img {
  width: 36px; height: 36px; border-radius: 50%;
}
.chat-bubble__body {
  max-width: calc(100% - 48px);
}
.chat-bubble__name { font-size: 12px; color: var(--color-text-tertiary); margin-bottom: 4px; }

.chat-bubble__content {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px; line-height: 1.6;
  word-break: break-word;
}
.chat-bubble--user .chat-bubble__content {
  background: var(--color-primary); color: #fff;
  border-radius: var(--radius-md) 0 var(--radius-md) var(--radius-md);
}
.chat-bubble--ai .chat-bubble__content {
  background: #F5F5F5; color: var(--color-text-primary);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
}

.chat-bubble__time { font-size: 11px; color: var(--color-text-tertiary); margin-top: 4px; }

.ai-section { margin-bottom: 12px; }
.ai-section:last-child { margin-bottom: 0; }
.ai-section h4 { font-size: 13px; margin-bottom: 6px; color: var(--color-primary); }
.ai-section blockquote {
  padding: 8px 12px; border-left: 3px solid var(--color-warning);
  background: #FFFBE6; font-size: 13px; color: var(--color-text-secondary);
}

.typing-cursor {
  display: inline-block; animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
</style>
```

---

## 4. ExamNavigator - 题号导航面板

模拟考试左侧题号导航，显示已答/未答/标记状态。

```vue
<!-- src/components/business/ExamNavigator.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  totalCount: number          // 总题数
  currentIndex: number        // 当前题号(0-based)
  answeredMap: Set<number>    // 已答题号 Set
  markedMap?: Set<number>     // 标记题号 Set
}

const props = withDefaults(defineProps<Props>(), {
  markedMap: () => new Set()
})

const emit = defineEmits<{
  (e: 'jump', index: number): void
}>()

const questionNumbers = computed(() =>
  Array.from({ length: props.totalCount }, (_, i) => i)
)
</script>

<template>
  <div class="exam-navigator">
    <h4 class="exam-navigator__title">答题卡</h4>
    <div class="exam-navigator__stats">
      <span class="stat answered">已答 {{ answeredMap.size }}</span>
      <span class="stat unanswered">未答 {{ totalCount - answeredMap.size }}</span>
      <span v-if="markedMap.size" class="stat marked">标记 {{ markedMap.size }}</span>
    </div>
    <div class="exam-navigator__grid">
      <button
        v-for="i in questionNumbers"
        :key="i"
        class="nav-btn"
        :class="{
          'is-current': i === currentIndex,
          'is-answered': answeredMap.has(i),
          'is-marked': markedMap.has(i)
        }"
        @click="emit('jump', i)"
      >
        {{ i + 1 }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.exam-navigator {
  width: 220px; padding: 16px;
  background: #fff; border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
.exam-navigator__title { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
.exam-navigator__stats {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 12px; font-size: 12px;
}
.stat.answered { color: var(--color-primary); }
.stat.unanswered { color: var(--color-text-tertiary); }
.stat.marked { color: var(--color-warning); }

.exam-navigator__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}
.nav-btn {
  width: 32px; height: 32px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.nav-btn:hover { border-color: var(--color-primary); }
.nav-btn.is-current { border-color: var(--color-primary); background: var(--color-primary); color: #fff; }
.nav-btn.is-answered { background: #E6F4FF; border-color: #91CAFF; }
.nav-btn.is-marked { border-color: var(--color-warning); box-shadow: 0 0 0 1px var(--color-warning); }
.nav-btn.is-current.is-answered { background: var(--color-primary); color: #fff; }
</style>
```

---

## 5. HeatmapCalendar - 学习热力图

类似 GitHub 贡献图的日历热力图。

```vue
<!-- src/components/business/HeatmapCalendar.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { CalendarComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([HeatmapChart, CalendarComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

interface Props {
  data: { date: string; hours: number }[]  // [{ date: '2026-05-01', hours: 2.5 }, ...]
  year?: number                             // 默认当前年
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  year: new Date().getFullYear(),
  height: '200px'
})

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const maxHours = computed(() => Math.max(...props.data.map(d => d.hours), 1))

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  chart.setOption({
    tooltip: {
      formatter: (params: any) =>
        `${params.value[0]}<br/>学习时长: ${params.value[1]} 小时`
    },
    visualMap: {
      min: 0, max: maxHours.value,
      orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#EBEDF0', '#C6E48B', '#7BC96F', '#239A3B', '#196127'] },
      text: ['长', '短'],
    },
    calendar: {
      top: 20, left: 30, right: 30,
      range: props.year,
      cellSize: ['auto', 15],
      yearLabel: { show: true },
      dayLabel: { firstDay: 1 },
      monthLabel: { show: true }
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: props.data.map(d => [d.date, d.hours])
    }]
  })
}

onMounted(initChart)
onUnmounted(() => chart?.dispose())
</script>

<template>
  <div ref="chartRef" :style="{ height, width: '100%' }" />
</template>
```

---

## 6. MedalWall - 勋章墙

展示连续学习勋章（铜/银/金）。

```vue
<!-- src/components/business/MedalWall.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Medal {
  name: string           // '铜牌勋章'
  type: 'bronze' | 'silver' | 'gold' | 'scholar'
  rule: string           // '连续学习7天'
  earned: boolean
  earnedDate?: string
}

interface Props {
  medals: Medal[]
}

const props = defineProps<Props>()

const medalConfig = {
  bronze: { icon: '🥉', color: '#CD7F32', bg: '#FFF8F0' },
  silver: { icon: '🥈', color: '#C0C0C0', bg: '#F8F8F8' },
  gold:   { icon: '🥇', color: '#FFD700', bg: '#FFFDE6' },
  scholar:{ icon: '🎓', color: '#1677FF', bg: '#E6F4FF' },
}

const earnedCount = computed(() => props.medals.filter(m => m.earned).length)
</script>

<template>
  <div class="medal-wall">
    <div class="medal-wall__header">
      <h3>我的勋章</h3>
      <span>{{ earnedCount }} / {{ medals.length }}</span>
    </div>
    <div class="medal-wall__grid">
      <div
        v-for="medal in medals" :key="medal.name"
        class="medal-item"
        :class="{ earned: medal.earned }"
        :style="{ background: medal.earned ? medalConfig[medal.type].bg : '#F5F5F5' }"
      >
        <span class="medal-icon">{{ medalConfig[medal.type].icon }}</span>
        <span class="medal-name">{{ medal.name }}</span>
        <span class="medal-rule">{{ medal.rule }}</span>
        <span v-if="medal.earned && medal.earnedDate" class="medal-date">
          {{ medal.earnedDate }}
        </span>
        <span v-else class="medal-locked">🔒</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.medal-wall { padding: 20px; }
.medal-wall__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.medal-wall__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; }
.medal-item {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 20px 16px; border-radius: var(--radius-md);
  text-align: center; transition: transform 0.2s;
}
.medal-item.earned { cursor: default; }
.medal-item.earned:hover { transform: translateY(-2px); }
.medal-item:not(.earned) { opacity: 0.6; }
.medal-icon { font-size: 36px; }
.medal-name { font-size: 14px; font-weight: 600; }
.medal-rule { font-size: 12px; color: var(--color-text-tertiary); }
.medal-date { font-size: 11px; color: var(--color-text-secondary); }
.medal-locked { font-size: 18px; margin-top: 4px; }
</style>
```

---

## 7. ContrastCard - 易混淆对比卡片

展示两种易混淆知识点的图文对比。

```vue
<!-- src/components/business/ContrastCard.vue -->
<script setup lang="ts">
interface ContrastItem {
  title: string
  image?: string
  description: string
  keyPoints: string[]
}

interface Props {
  itemA: ContrastItem
  itemB: ContrastItem
  highlightDiff?: boolean        // 是否高亮差异点
  mnemonic?: string              // 记忆口诀
}

defineProps<Props>()
</script>

<template>
  <div class="contrast-card">
    <!-- 对比区 -->
    <div class="contrast-card__compare">
      <div class="contrast-column">
        <h4>{{ itemA.title }}</h4>
        <img v-if="itemA.image" :src="itemA.image" :alt="itemA.title" class="contrast-image" />
        <p>{{ itemA.description }}</p>
        <ul>
          <li v-for="point in itemA.keyPoints" :key="point">{{ point }}</li>
        </ul>
      </div>
      <div class="contrast-divider">
        <span>VS</span>
      </div>
      <div class="contrast-column">
        <h4>{{ itemB.title }}</h4>
        <img v-if="itemB.image" :src="itemB.image" :alt="itemB.title" class="contrast-image" />
        <p>{{ itemB.description }}</p>
        <ul>
          <li v-for="point in itemB.keyPoints" :key="point">{{ point }}</li>
        </ul>
      </div>
    </div>

    <!-- 记忆口诀 -->
    <div v-if="mnemonic" class="contrast-card__mnemonic">
      💡 记忆口诀：{{ mnemonic }}
    </div>
  </div>
</template>

<style scoped>
.contrast-card { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border); overflow: hidden; }
.contrast-card__compare { display: flex; }
.contrast-column {
  flex: 1; padding: 20px;
  border-right: 1px solid var(--color-border);
}
.contrast-column:last-child { border-right: none; }
.contrast-column h4 { font-size: 16px; margin-bottom: 12px; text-align: center; }
.contrast-image { width: 100%; border-radius: var(--radius-md); margin-bottom: 12px; }
.contrast-column p { font-size: 13px; color: var(--color-text-secondary); margin-bottom: 8px; }
.contrast-column li { font-size: 13px; color: var(--color-text-primary); margin-bottom: 4px; }

.contrast-divider {
  display: flex; align-items: center; justify-content: center;
  width: 48px; background: #FAFAFA;
}
.contrast-divider span {
  font-weight: 800; color: var(--color-primary); font-size: 16px;
}

.contrast-card__mnemonic {
  padding: 14px 20px; background: #FFFBE6;
  border-top: 1px solid #FFE58F;
  font-size: 14px; color: #D48806;
}
</style>
```

---

## 8. DashboardChart - 数据看板图表

封装折线/柱状/饼图的通用图表组件。

```vue
<!-- src/components/business/DashboardChart.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

type ChartType = 'line' | 'bar' | 'pie'

interface Props {
  type: ChartType
  option: echarts.EChartsOption
  height?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false
})

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption(props.option)
}

onMounted(initChart)
onUnmounted(() => chart?.dispose())

watch(() => props.option, (val) => chart?.setOption(val, true), { deep: true })
watch(() => props.loading, (val) => {
  val ? chart?.showLoading() : chart?.hideLoading()
})
</script>

<template>
  <div ref="chartRef" :style="{ height, width: '100%' }" />
</template>
```

### 使用示例

```vue
<!-- 柱状图：成绩分布 -->
<DashboardChart
  type="bar"
  :option="{
    xAxis: { data: ['<60', '60-69', '70-79', '80-89', '90-100'] },
    yAxis: {},
    series: [{ type: 'bar', data: [5, 12, 25, 40, 18], itemStyle: { color: '#1677FF' } }]
  }"
/>

<!-- 饼图：通过率 -->
<DashboardChart
  type="pie"
  :option="{
    series: [{
      type: 'pie', radius: ['50%', '70%'],
      data: [
        { value: 85, name: '通过', itemStyle: { color: '#52C41A' } },
        { value: 15, name: '未通过', itemStyle: { color: '#FF4D4F' } }
      ]
    }]
  }"
/>
```

---

*本文档基于 SRS V1.0 业务需求编写，所有组件遵循 Vue 3 + TypeScript 规范*
