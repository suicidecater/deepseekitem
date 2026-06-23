// src/stores/student.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RadarChartData } from '@/types/chart'

interface StudentProfile {
  name: string
  phone: string
  carType: string
  school: string
  registerDate: string
  avatar: string
  progress: number
}

interface StudyTask {
  id: number
  title: string
  description: string
  completed: boolean
  type: 'practice' | 'ai_lesson' | 'exam_review' | 'error_review'
  route?: string
}

interface KnowledgeTreeNode {
  name: string
  value: number
  children?: KnowledgeTreeNode[]
}

interface QuickAction {
  label: string
  icon: string
  route: string
  color: string
}

interface DashboardData {
  profile: StudentProfile
  abilityScores: number[]
  abilityBaseline: number[]
  todayTasks: StudyTask[]
  knowledgeTree: KnowledgeTreeNode
  completedQuestions: number
  totalQuestions: number
  streakDays: number
  todayStudyMinutes: number
  quickActions: QuickAction[]
}

export const useStudentStore = defineStore('student', () => {
  const profile = ref<StudentProfile | null>(null)
  const dashboard = ref<DashboardData | null>(null)
  const loading = ref(false)

  const radarData = computed<RadarChartData | null>(() => {
    if (!dashboard.value) return null
    return {
      dimensions: ['交通标志', '交通法规', '安全常识', '驾驶理论'],
      current: dashboard.value.abilityScores,
      baseline: dashboard.value.abilityBaseline
    }
  })

  const todayTasks = computed(() => dashboard.value?.todayTasks ?? [])
  const quickActions = computed(() => dashboard.value?.quickActions ?? [])
  const completionRate = computed(() => {
    if (!dashboard.value) return 0
    return Math.round((dashboard.value.completedQuestions / dashboard.value.totalQuestions) * 100)
  })

  async function fetchDashboard() {
    loading.value = true
    try {
      const res = await fetch('/api/student/dashboard')
      const json = await res.json()
      if (json.code === 0) {
        dashboard.value = json.data
        profile.value = json.data.profile
      }
    } finally {
      loading.value = false
    }
  }

  return {
    profile,
    dashboard,
    loading,
    radarData,
    todayTasks,
    quickActions,
    completionRate,
    fetchDashboard
  }
})
