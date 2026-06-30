<script setup lang="ts">
// src/views/student/HomeView.vue - 学员学习首页仪表盘
// 竞品参考：驾考宝典卡片式布局 + 角色化欢迎 + 科目大卡片入口
import { ref, onMounted, computed } from 'vue'
import { useStudentStore } from '@/stores/student'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'
import { useSWR } from '@/composables/useSWR'
import { get, put } from '@/api/request'
import RadarChart from '@/components/charts/RadarChart.vue'

const studentStore = useStudentStore()
const authStore = useAuthStore()
const appStore = useAppStore()
const router = useRouter()

const loading = ref(true)
const switchingDirection = ref(false)
const showDirectionModal = ref(false) // 新用户方向选择弹窗
const newUserNoEval = computed(() => {
  // 所有方向都没有测评记录 = 全新用户
  const map = authStore.evaluationStatusMap
  return Object.keys(map).length > 0 && Object.values(map).every(v => v === 0)
})

// #4 useSWR 缓存层包裹 dashboard 数据获取
const userId = computed(() => authStore.userInfo?.userId ?? 'guest')
const { data: swrDashboard, loading: swrLoading, error: swrError, fetch: fetchDashboard } = useSWR<any>(
  `dashboard-${userId.value}`,
  async () => {
    const res = await get<any>('/api/student/dashboard')
    return res.data.data
  },
  30_000 // 30秒 TTL
)

// 角色化欢迎信息
const welcomeInfo = computed(() => {
  const user = authStore.userInfo
  const role = authStore.role
  const dashboard = swrDashboard.value || studentStore.dashboard

  if (role === 'coach') return { greeting: `${user?.name}教练`, subtitle: `您有 ${dashboard?.totalStudents ?? 35} 名学员`, tag: '教练端' }
  if (role === 'admin') return { greeting: `${user?.name}管理员`, subtitle: '数据总览', tag: '管理端' }
  return {
    greeting: `${user?.name || '学员'}`,
    subtitle: `今日距考试还有 ${dashboard?.daysUntilExam ?? 14} 天`,
    tag: '学员端'
  }
})

// 当前学习方向
const currentDirection = computed(() => authStore.studySubject)

// 学习方向选择函数
async function selectDirection(subject: 1 | 4 | 5) {
  if (switchingDirection.value || subject === currentDirection.value) return
  switchingDirection.value = true
  try {
    const res = await put('/api/student/study-direction', { study_subject: subject })
    const json = res.data
    if (json.code === 0) {
      // 更新本地 auth store
      if (authStore.userInfo) {
        authStore.userInfo.studySubject = subject
        // 更新该方向的测评状态（后端返回 needsEvaluation）
        if (json.data?.needsEvaluation !== undefined) {
          if (!authStore.userInfo.evaluationStatusMap) {
            authStore.userInfo.evaluationStatusMap = {}
          }
          authStore.userInfo.evaluationStatusMap[String(subject)] = json.data.needsEvaluation ? 0 : 1
        }
      }
      appStore.showToast(json.message || '方向已切换', 'success')
      // 重新拉取仪表盘
      await fetchDashboard()
      // 如果新方向未测评，提示用户
      if (json.data?.needsEvaluation) {
        setTimeout(() => {
          appStore.showToast('该方向尚未测评，请先完成能力基线测评', 'warning')
        }, 500)
      }
    } else {
      appStore.showToast(json.message || '切换失败', 'error')
    }
  } catch {
    appStore.showToast('网络异常，请重试', 'error')
  } finally {
    switchingDirection.value = false
  }
}

// 科目大卡片入口（P0升级 → 方向选择器）
const subjectCards = computed(() => {
  const d = swrDashboard.value || studentStore.dashboard
  const active = currentDirection.value
  return [
    {
      title: '科目一',
      subtitle: '小车理论',
      icon: '🚗',
      value: 1 as const,
      progress: d?.subject1Progress ?? 75,
      color: '#1677FF',
      bg: '#E6F4FF',
      active: active === 1,
      route: '/student/practice?subject=1'
    },
    {
      title: '科目四',
      subtitle: '安全文明',
      icon: '🔒',
      value: 4 as const,
      progress: d?.subject4Progress ?? 40,
      color: '#52C41A',
      bg: '#F6FFED',
      active: active === 4,
      route: '/student/practice?subject=4'
    },
    {
      title: '专业人员',
      subtitle: '客运/货运/危化品',
      icon: '🚛',
      value: 5 as const,
      progress: d?.transportProgress ?? 20,
      color: '#FA8C16',
      bg: '#FFF7E6',
      active: active === 5,
      route: '/student/transport'
    }
  ]
})

// 学车流程步骤（P1）
const studySteps = [
  { label: '能力测评', icon: '📊', status: 'done' },
  { label: 'AI学习路径', icon: '🧭', status: 'done' },
  { label: '题库练习', icon: '📝', status: 'active' },
  { label: '模拟考试', icon: '📋', status: 'pending' },
  { label: '考前冲刺', icon: '🚀', status: 'pending' }
]

// 优势亮点
const advantages = [
  { icon: '🤖', title: 'AI问答', desc: 'DeepSeek大模型驱动' },
  { icon: '🧭', title: '学习路径', desc: '个性化规划' },
  { icon: '📊', title: '能力雷达图', desc: '四维能力可视化' },
  { icon: '🎮', title: '场景模拟', desc: '交通场景实操' },
  { icon: '🔄', title: '易混训练', desc: '精准攻克难点' },
  { icon: '🔥', title: '热力图', desc: '学习轨迹追踪' },
  { icon: '🤖', title: '教练AI建议', desc: '智能辅导' },
  { icon: '🚛', title: '运输培训', desc: '从业资格证备考' }
]

// 快捷入口
const quickActions = [
  { label: '开始练习', icon: '✏️', route: '/student/practice', color: '#1677FF' },
  { label: '模拟考试', icon: '📝', route: '/student/exam', color: '#52C41A' },
  { label: 'AI问答', icon: '🤖', route: '/student/ai-qa', color: '#722ED1' },
  { label: '错题本', icon: '📕', route: '/student/error-book', color: '#FA8C16' },
]

// 今日任务
const todayTasks = ref([
  { id: 1, title: '交通标志专项练习', type: 'practice', completed: false },
  { id: 2, title: 'AI知识点讲解 - 交通法规', type: 'ai_lesson', completed: false },
  { id: 3, title: '模拟考试复盘', type: 'exam_review', completed: true },
  { id: 4, title: '错题回顾 - 易错题集', type: 'error_review', completed: false },
])

// 能力雷达数据（Mock / 测评后来自 dashboard）
const radarData = ref({
  dimensions: ['交通标志', '交通法规', '安全常识', '驾驶理论'],
  current: [82, 65, 78, 55],
  baseline: [90, 90, 90, 90]
})

const radarChartData = computed(() => [
  {
    label: '当前能力',
    data: radarData.value.current,
    color: '#1677FF',
  },
  {
    label: '基准线',
    data: radarData.value.baseline,
    color: '#999',
    fill: false,
    dashed: true,
  },
])

const showSprint = computed(() => {
  const d = swrDashboard.value || studentStore.dashboard
  return (d?.daysUntilExam ?? 14) <= 14
})

// 教练信息（Mock）
const coachInfo = ref({
  name: '李教练',
  phone: '138****5678',
  avatar: '',
  years: 8,
  rate: 4.9
})

// 新用户方向选择弹窗相关
const selectedModalDirection = ref<1 | 4 | 5>(1)

const directionOptions = [
  { title: '科目一', desc: '小车理论驾驶知识', icon: '🚗', value: 1 as const },
  { title: '科目四', desc: '安全文明驾驶常识', icon: '🔒', value: 4 as const },
  { title: '专业人员', desc: '客运/货运/危化品从业资格', icon: '🚛', value: 5 as const },
]

async function confirmDirectionSelection() {
  const subject = selectedModalDirection.value
  switchingDirection.value = true
  try {
    const res = await put('/api/student/study-direction', { study_subject: subject })
    const json = res.data
    if (json.code === 0) {
      if (authStore.userInfo) {
        authStore.userInfo.studySubject = subject
      }
      showDirectionModal.value = false
      appStore.showToast('方向已设置，请先完成能力测评', 'success')
      await fetchDashboard()
    } else {
      appStore.showToast(json.message || '设置失败', 'error')
    }
  } catch {
    appStore.showToast('网络异常，请重试', 'error')
  } finally {
    switchingDirection.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await fetchDashboard() // #4 useSWR 缓存层
    // 新用户首次登录（所有方向均未测评），弹出方向选择
    if (newUserNoEval.value) {
      setTimeout(() => { showDirectionModal.value = true }, 800)
    }
  } catch {
    // 失败降级：useSWR 已设置 error，UI 展示降级状态
  }
  loading.value = false
})
</script>

<template>
  <div class="home-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else>
      <!-- 角色化欢迎区 -->
      <section class="welcome-section">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1 class="welcome-greeting">欢迎回来，{{ welcomeInfo.greeting }}</h1>
            <p class="welcome-subtitle">{{ welcomeInfo.subtitle }}</p>
          </div>
          <div class="welcome-stats">
            <div class="stat-item">
              <span class="stat-value">{{ studentStore.dashboard?.streakDays ?? 7 }}</span>
              <span class="stat-label">连续学习(天)</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ studentStore.dashboard?.todayStudyMinutes ?? 45 }}</span>
              <span class="stat-label">今日学习(分钟)</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ studentStore.dashboard?.completedQuestions ?? 320 }}</span>
              <span class="stat-label">已做题数</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 学习方向选择卡片（P0升级） -->
      <section class="subject-cards">
        <div
          v-for="card in subjectCards"
          :key="card.title"
          class="subject-card"
          :class="{ active: card.active, switching: switchingDirection }"
          :style="{ '--card-color': card.color, '--card-bg': card.bg }"
          @click="selectDirection(card.value)"
        >
          <div class="card-header">
            <span class="card-icon">{{ card.icon }}</span>
            <span class="card-title">{{ card.title }}</span>
            <span v-if="card.active" class="card-check">✅ 当前方向</span>
          </div>
          <p class="card-subtitle">{{ card.subtitle }}</p>
          <div class="card-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: card.progress + '%', background: card.color }"></div>
            </div>
            <span class="progress-text">已学 {{ card.progress }}%</span>
          </div>
          <button class="card-btn" :style="{ background: card.color }">
            {{ card.active ? '已选中' : '选择方向' }}
          </button>
        </div>
      </section>

      <!-- 未测评引导条 -->
      <div v-if="authStore.needsEvaluation" class="eval-banner">
        <span class="eval-banner-icon">⚠️</span>
        <span class="eval-banner-text">请先完成能力基线测评，系统将根据测评结果为你定制个性化学习方案</span>
        <button class="btn btn-primary btn-sm" @click="router.push('/student/evaluation')">
          开始测评 →
        </button>
      </div>

      <!-- 主内容区：三栏布局 -->
      <div class="home-grid">
        <!-- 左侧：个人档案 + 教练信息 + 今日任务 -->
        <div class="home-left">
          <!-- 个人档案卡 -->
          <section class="card profile-card">
            <div class="card-title-row">
              <h3>个人档案</h3>
              <span class="tag tag-blue">已认证</span>
            </div>
            <div class="profile-body">
              <div class="profile-avatar">
                <div class="avatar-placeholder">张</div>
              </div>
              <div class="profile-info">
                <p class="profile-name">张三</p>
                <p class="profile-detail">C1 小型汽车</p>
                <p class="profile-detail">安达驾校 · 2026-03-15注册</p>
              </div>
            </div>
            <div class="profile-progress">
              <span class="progress-label">学习总进度</span>
              <div class="progress-bar">
                <div class="progress-fill" style="width: 60%; background: var(--color-primary)"></div>
              </div>
              <span class="progress-percent">60%</span>
            </div>
          </section>

          <!-- 教练信息卡片（P1） -->
          <section class="card coach-card">
            <div class="card-title-row">
              <h3>我的教练</h3>
            </div>
            <div class="coach-body">
              <div class="coach-avatar">李</div>
              <div class="coach-info">
                <p class="coach-name">{{ coachInfo.name }}</p>
                <p class="coach-detail">{{ coachInfo.phone }}</p>
                <p class="coach-detail">{{ coachInfo.years }}年教龄 · 好评率 {{ coachInfo.rate }}</p>
              </div>
              <button class="btn btn-outline btn-sm">联系教练</button>
            </div>
          </section>

          <!-- 今日任务清单 -->
          <section class="card task-card">
            <div class="card-title-row">
              <h3>今日学习任务</h3>
              <span class="task-count">{{ todayTasks.filter(t => !t.completed).length }} 项待完成</span>
            </div>
            <ul class="task-list">
              <li
                v-for="task in todayTasks"
                :key="task.id"
                class="task-item"
                :class="{ completed: task.completed }"
              >
                <span class="task-check">{{ task.completed ? '☑' : '☐' }}</span>
                <span class="task-title">{{ task.title }}</span>
                <span class="task-tag" :class="task.completed ? 'tag-green' : 'tag-orange'">
                  {{ task.completed ? '已完成' : '待完成' }}
                </span>
              </li>
            </ul>
          </section>
        </div>

        <!-- 中间：雷达图 + 学车流程 -->
        <div class="home-center">
          <!-- 四维能力雷达图（Chart.js） -->
          <section class="card radar-card">
            <div class="card-title-row">
              <h3>能力雷达图</h3>
              <span class="text-muted" style="font-size:12px">四维评估</span>
            </div>
            <div class="radar-container">
              <RadarChart
                :dimensions="radarData.dimensions"
                :datasets="radarChartData"
                height="280"
              />
            </div>
          </section>

          <!-- 学车流程进度条（P1） -->
          <section class="card flow-card">
            <div class="card-title-row">
              <h3>学车流程</h3>
            </div>
            <div class="flow-steps">
              <div
                v-for="(step, idx) in studySteps"
                :key="step.label"
                class="flow-step"
                :class="step.status"
              >
                <div class="step-dot">{{ step.icon }}</div>
                <span class="step-label">{{ step.label }}</span>
                <div v-if="idx < studySteps.length - 1" class="step-line" :class="step.status"></div>
              </div>
            </div>
          </section>
        </div>

        <!-- 右侧：快捷入口 + 考前冲刺 + 优势亮点 -->
        <div class="home-right">
          <!-- 快捷入口 -->
          <section class="card quick-card">
            <div class="card-title-row">
              <h3>快捷入口</h3>
            </div>
            <div class="quick-actions">
              <router-link
                v-for="action in quickActions"
                :key="action.label"
                :to="action.route"
                class="quick-btn"
                :style="{ '--btn-color': action.color }"
              >
                <span class="quick-icon">{{ action.icon }}</span>
                <span class="quick-label">{{ action.label }}</span>
              </router-link>
            </div>
          </section>

          <!-- 考前冲刺（条件展示） -->
          <section v-if="showSprint" class="card sprint-card">
            <div class="sprint-badge">🔥 考前冲刺</div>
            <p class="sprint-days">距考试还有 {{ studentStore.dashboard?.daysUntilExam ?? 14 }} 天</p>
            <div class="sprint-timer">
              <span class="timer-icon">⏰</span>
              <span>倒计时：{{ studentStore.dashboard?.daysUntilExam ?? 14 }}天</span>
            </div>
            <router-link to="/student/sprint" class="btn btn-primary btn-block">
              进入冲刺训练
            </router-link>
          </section>

          <!-- AI问答悬浮入口 -->
          <div class="ai-float-btn" @click="router.push('/student/ai-qa')">
            <span class="ai-float-icon">🤖</span>
            <span class="ai-float-text">有疑问？问AI</span>
          </div>
        </div>
      </div>

      <!-- 平台优势亮点 -->
      <section class="advantages-section">
        <h2 class="section-title">为什么选择我们</h2>
        <div class="advantages-grid">
          <div v-for="adv in advantages" :key="adv.title" class="advantage-item">
            <span class="advantage-icon">{{ adv.icon }}</span>
            <div class="advantage-text">
              <p class="advantage-title">{{ adv.title }}</p>
              <p class="advantage-desc">{{ adv.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 底部信息 -->
      <footer class="home-footer">
        <p>交通安全培训平台 · 基于DeepSeek大模型 · AI驱动智能学车</p>
        <p class="footer-links">
          <a href="#">关于我们</a> · <a href="#">用户协议</a> · <a href="#">隐私政策</a> · <a href="#">帮助中心</a>
        </p>
      </footer>
    </template>

    <!-- 新用户方向选择弹窗 -->
    <Teleport to="body">
      <div v-if="showDirectionModal" class="modal-overlay" @click.self="showDirectionModal = false">
        <div class="direction-modal">
          <div class="modal-header">
            <h2>选择学习方向</h2>
            <p>请选择您要学习的方向，系统将为您定制专属学习方案</p>
          </div>
          <div class="modal-body">
            <div
              v-for="card in directionOptions"
              :key="card.value"
              class="direction-option"
              :class="{ selected: selectedModalDirection === card.value }"
              @click="selectedModalDirection = card.value"
            >
              <span class="option-icon">{{ card.icon }}</span>
              <div class="option-info">
                <span class="option-title">{{ card.title }}</span>
                <span class="option-desc">{{ card.desc }}</span>
              </div>
              <span v-if="selectedModalDirection === card.value" class="option-check">✓</span>
            </div>
          </div>
          <div class="modal-footer">
            <button
              class="btn btn-primary modal-confirm-btn"
              :disabled="switchingDirection"
              @click="confirmDirectionSelection"
            >
              {{ switchingDirection ? '设置中...' : '确认选择' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.home-page {
  padding: 24px;
  max-width: var(--content-max-width);
  margin: 0 auto;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 16px;
  color: var(--color-text-tertiary);
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 欢迎区 */
.welcome-section {
  background: linear-gradient(135deg, #E6F4FF, #F0F5FF);
  border-radius: var(--radius-xl);
  padding: 28px 32px;
  margin-bottom: 24px;
}

.welcome-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}

.welcome-greeting {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.welcome-subtitle {
  margin-top: 6px;
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.welcome-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
  padding: 12px 20px;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.stat-value {
  display: block;
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-primary);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

/* 科目大卡片（P0升级） */
.subject-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.subject-card {
  background: #fff;
  border-radius: var(--radius-xl);
  padding: 24px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}
.subject-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--card-color);
}
.subject-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
.subject-card.active {
  border-color: var(--card-color);
  box-shadow: 0 0 0 3px var(--card-bg);
}
.subject-card.switching {
  pointer-events: none;
  opacity: 0.6;
}
.card-check {
  font-size: 12px;
  color: #52C41A;
  font-weight: 600;
}

/* 未测评引导条 */
.eval-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #FFF1F0, #FFF7E6);
  border: 1px solid #FFCCC7;
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
}
.eval-banner-icon { font-size: 20px; flex-shrink: 0; }
.eval-banner-text { flex: 1; font-size: 14px; color: #8C1A1A; }

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.card-icon {
  font-size: 32px;
}

.card-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.card-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-bottom: 16px;
}

.card-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #F0F0F0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.progress-text {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.card-btn {
  width: 100%;
  padding: 10px 0;
  color: #fff;
  font-size: var(--font-size-sm);
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: opacity var(--transition-fast);
}
.card-btn:hover { opacity: 0.9; }

/* 三栏布局 */
.home-grid {
  display: grid;
  grid-template-columns: 300px 1fr 280px;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1400px) {
  .home-grid { grid-template-columns: 1fr 1fr; }
  .home-right { grid-column: 1 / -1; }
  .subject-cards { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
}
@media (max-width: 900px) {
  .home-grid { grid-template-columns: 1fr; }
  .welcome-content { flex-direction: column; align-items: flex-start; }
}

/* 卡片通用 */
.card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--color-border-light);
  margin-bottom: 20px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card-title-row h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

/* 个人档案 */
.profile-body {
  display: flex;
  gap: 14px;
  margin-bottom: 16px;
  align-items: center;
}

.avatar-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary), #4096FF);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 600;
}

.profile-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.profile-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

.profile-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  white-space: nowrap;
}
.progress-percent {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--color-primary);
}

/* 教练信息 */
.coach-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.coach-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--color-primary-light);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.coach-info { flex: 1; }
.coach-name { font-size: var(--font-size-base); font-weight: 600; }
.coach-detail { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.btn-sm { padding: 4px 12px; font-size: var(--font-size-xs); }

/* 今日任务 */
.task-count {
  font-size: var(--font-size-xs);
  color: var(--color-warning);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: #FAFAFA;
  transition: all var(--transition-fast);
}

.task-item.completed {
  opacity: 0.6;
}

.task-check {
  font-size: 18px;
}

.task-title {
  flex: 1;
  font-size: var(--font-size-sm);
}

.task-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

/* 雷达图容器 */
.radar-container {
  padding: 8px 0;
}

/* 学车流程 */
.flow-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}

.step-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: #F0F0F0;
  border: 2px solid var(--color-border);
}

.flow-step.done .step-dot {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}
.flow-step.active .step-dot {
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-light);
}

.step-label {
  font-size: 11px;
  color: var(--color-text-tertiary);
}
.flow-step.active .step-label {
  color: var(--color-primary);
  font-weight: 600;
}

.step-line {
  position: absolute;
  top: 20px;
  left: calc(50% + 20px);
  width: calc(100% - 40px);
  height: 2px;
  background: var(--color-border);
}
.step-line.done {
  background: var(--color-primary);
}

/* 快捷入口 */
.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  border-radius: var(--radius-md);
  background: #FAFAFA;
  text-decoration: none;
  color: var(--color-text-primary);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}
.quick-btn:hover {
  background: #fff;
  border-color: var(--btn-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.quick-icon {
  font-size: 26px;
}
.quick-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
}

/* 考前冲刺 */
.sprint-card {
  background: linear-gradient(135deg, #FFF7E6, #FFF1CC);
  border-color: #FFD666;
  text-align: center;
}

.sprint-badge {
  font-size: var(--font-size-xl);
  font-weight: 700;
  margin-bottom: 8px;
}

.sprint-days {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.sprint-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: #fff;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  font-size: var(--font-size-sm);
}

.timer-icon { font-size: 18px; }

/* AI悬浮按钮 */
.ai-float-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #722ED1, #9254DE);
  color: #fff;
  border-radius: var(--radius-xl);
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(114, 46, 209, 0.3);
  transition: all var(--transition-fast);
  justify-content: center;
}
.ai-float-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(114, 46, 209, 0.4);
}

.ai-float-icon { font-size: 22px; }
.ai-float-text { font-size: var(--font-size-sm); font-weight: 500; }

/* 平台优势 */
.advantages-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  margin-bottom: 20px;
  text-align: center;
}

.advantages-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .advantages-grid { grid-template-columns: 1fr 1fr; }
}

.advantage-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
}

.advantage-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.advantage-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.advantage-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* 底部 */
.home-footer {
  text-align: center;
  padding: 32px 0;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

.footer-links {
  margin-top: 8px;
}
.footer-links a {
  color: var(--color-text-secondary);
}
.footer-links a:hover {
  color: var(--color-primary);
}

/* ==================== 新用户方向选择弹窗 ==================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.direction-modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  text-align: center;
  margin-bottom: 24px;
}

.modal-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.modal-header p {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.direction-option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  border: 1.5px solid var(--color-border-light);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: #FAFAFA;
}

.direction-option:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.direction-option.selected {
  border-color: var(--color-primary);
  background: #E6F4FF;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.option-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.option-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.option-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.option-check {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.modal-footer {
  text-align: center;
}

.modal-confirm-btn {
  min-width: 180px;
  padding: 12px 40px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
}
</style>
