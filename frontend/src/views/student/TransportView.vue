<script setup lang="ts">
// src/views/student/TransportView.vue - 运输从业人员培训
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const activeType = ref<'passenger' | 'freight' | 'dangerous'>('passenger')

const typeOptions = [
  { key: 'passenger' as const, label: '客运', icon: '🚌', color: '#1677FF' },
  { key: 'freight' as const, label: '货运', icon: '🚛', color: '#FA8C16' },
  { key: 'dangerous' as const, label: '危化品', icon: '⚠️', color: '#FF4D4F' },
]

const courses = ref([
  { id: 1, title: '客运驾驶员从业资格基础', progress: 80, total: 10, completed: 8 },
  { id: 2, title: '旅客运输安全规范', progress: 45, total: 8, completed: 3 },
  { id: 3, title: '应急处置与急救知识', progress: 0, total: 6, completed: 0 },
])

function goToPractice() {
  router.push('/student/practice?subject=transport')
}
</script>

<template>
  <div class="transport-page">
    <div class="page-header">
      <h2>运输从业人员培训</h2>
      <p class="page-desc">客运、货运、危化品运输从业资格培训</p>
    </div>

    <!-- 类型选择 -->
    <div class="type-cards">
      <div v-for="t in typeOptions" :key="t.key" class="type-card" :class="{ active: activeType === t.key }" :style="{ '--type-color': t.color }" @click="activeType = t.key">
        <span class="type-icon">{{ t.icon }}</span>
        <span class="type-label">{{ t.label }}</span>
      </div>
    </div>

    <!-- 课程列表 -->
    <div class="card">
      <h3>培训课程</h3>
      <div class="course-list">
        <div v-for="c in courses" :key="c.id" class="course-item">
          <div class="course-info">
            <p class="course-title">{{ c.title }}</p>
            <div class="course-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: c.progress + '%' }"></div>
              </div>
              <span>{{ c.completed }}/{{ c.total }} 课时</span>
            </div>
          </div>
          <button class="btn btn-outline btn-sm" @click="goToPractice">继续学习</button>
        </div>
      </div>
    </div>

    <!-- 资格练习 -->
    <div class="card">
      <h3>资格练习题库</h3>
      <p class="card-desc">包含客运/货运/危化品运输从业资格考试真题</p>
      <button class="btn btn-primary" @click="goToPractice">进入题库练习</button>
    </div>
  </div>
</template>

<style scoped>
.transport-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.page-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }

.type-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }
.type-card {
  padding: 20px; border-radius: var(--radius-lg); border: 2px solid var(--color-border);
  text-align: center; cursor: pointer; transition: all var(--transition-fast);
}
.type-card.active { border-color: var(--type-color); background: #fff; box-shadow: 0 0 0 3px rgba(0,0,0,0.04); }
.type-icon { display: block; font-size: 40px; margin-bottom: 8px; }
.type-label { font-size: var(--font-size-lg); font-weight: 600; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }
.card-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); margin-bottom: 12px; }

.course-list { display: flex; flex-direction: column; gap: 14px; }
.course-item { display: flex; align-items: center; gap: 16px; padding: 14px; border-radius: var(--radius-md); background: #FAFAFA; }
.course-info { flex: 1; }
.course-title { font-size: var(--font-size-sm); font-weight: 500; margin-bottom: 8px; }
.course-progress { display: flex; align-items: center; gap: 10px; }
.progress-bar { flex: 1; height: 6px; background: #F0F0F0; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-primary); border-radius: 3px; }
.course-progress span { font-size: var(--font-size-xs); color: var(--color-text-tertiary); white-space: nowrap; }
.btn-sm { padding: 4px 12px; font-size: var(--font-size-xs); }
</style>
