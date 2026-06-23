<script setup lang="ts">
// src/views/coach/AiAdviceView.vue - AI教学辅导建议
import { ref } from 'vue'

const selectedStudent = ref('')
const loading = ref(false)
const advice = ref<any>(null)

const studentOptions = [
  { id: 1, name: '张三', score: 88 },
  { id: 2, name: '李四', score: 72 },
  { id: 3, name: '王五', score: 95 },
  { id: 4, name: '赵六', score: 65 },
]

async function generateAdvice() {
  if (!selectedStudent.value) return
  loading.value = true
  await new Promise(r => setTimeout(r, 1200))
  advice.value = {
    weaknesses: ['驾驶理论知识薄弱，得分仅55分', '交通法规中扣分标准混淆', '高速限速规定记忆不牢'],
    aiSuggestions: [
      { type: '重点', content: '本周重点攻克驾驶理论章节，每天完成30道相关题目' },
      { type: '方法', content: '建议使用对比记忆法学习扣分罚款标准，配合易混淆训练' },
      { type: '方案', content: '制定5天专项辅导计划：第1-2天理论精讲，第3天法规串讲，第4天模拟测试，第5天错题复盘' },
    ],
    plan: [
      { day: '第1天', task: '驾驶理论精讲（交通信号、安全行车）', duration: '45分钟' },
      { day: '第2天', task: '驾驶理论精讲（恶劣天气、紧急情况）', duration: '45分钟' },
      { day: '第3天', task: '扣分罚款标准专项训练', duration: '30分钟' },
      { day: '第4天', task: '科目一全真模拟考试', duration: '45分钟' },
      { day: '第5天', task: '错题复盘 + 薄弱点巩固', duration: '30分钟' },
    ]
  }
  loading.value = false
}
</script>

<template>
  <div class="ai-advice-page">
    <div class="page-header"><h2>AI教学辅导建议</h2></div>

    <!-- 学员选择 -->
    <div class="card select-card">
      <label>选择学员：</label>
      <select v-model="selectedStudent" class="student-select">
        <option value="">请选择</option>
        <option v-for="s in studentOptions" :key="s.id" :value="s.id">{{ s.name }} ({{ s.score }}分)</option>
      </select>
      <button class="btn btn-primary" :disabled="!selectedStudent || loading" @click="generateAdvice">
        {{ loading ? 'AI分析中...' : '生成辅导建议' }}
      </button>
    </div>

    <!-- 结果 -->
    <div v-if="advice" class="advice-result">
      <!-- 知识短板 -->
      <div class="card">
        <h3>知识短板分析</h3>
        <ul class="weak-list">
          <li v-for="w in advice.weaknesses" :key="w">⚠️ {{ w }}</li>
        </ul>
      </div>

      <!-- AI建议 -->
      <div class="card">
        <h3>AI辅导建议</h3>
        <div v-for="(s, idx) in advice.aiSuggestions" :key="idx" class="suggestion-item" :class="'sug-' + s.type">
          <span class="sug-badge">{{ s.type === '重点' ? '🎯' : s.type === '方法' ? '💡' : '📋' }}</span>
          <p>{{ s.content }}</p>
        </div>
      </div>

      <!-- 5天计划 -->
      <div class="card">
        <h3>5天辅导计划</h3>
        <div class="plan-list">
          <div v-for="p in advice.plan" :key="p.day" class="plan-item">
            <span class="plan-day">{{ p.day }}</span>
            <span class="plan-task">{{ p.task }}</span>
            <span class="plan-duration">{{ p.duration }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-advice-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.select-card { padding: 20px; display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.select-card label { font-size: var(--font-size-sm); }
.student-select { padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: var(--font-size-sm); min-width: 180px; }

.advice-result { display: flex; flex-direction: column; gap: 20px; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 14px; }

.weak-list { padding-left: 20px; }
.weak-list li { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 6px; }

.suggestion-item {
  display: flex; gap: 12px; padding: 14px; border-radius: var(--radius-md); margin-bottom: 10px;
  font-size: var(--font-size-sm); line-height: 1.6;
}
.sug-重点 { background: #FFF1F0; }
.sug-方法 { background: #E6F4FF; }
.sug-方案 { background: #F6FFED; }
.sug-badge { font-size: 20px; flex-shrink: 0; }

.plan-list { display: flex; flex-direction: column; gap: 8px; }
.plan-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: var(--radius-md); background: #FAFAFA; font-size: var(--font-size-sm); }
.plan-day { width: 48px; font-weight: 600; color: var(--color-primary); }
.plan-task { flex: 1; }
.plan-duration { color: var(--color-text-tertiary); font-size: var(--font-size-xs); }
</style>
