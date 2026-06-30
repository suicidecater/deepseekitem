<script setup lang="ts">
// src/views/auth/LoginView.vue - 三种用户分开登录
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import AuthLayout from '@/components/layout/AuthLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

// 角色类型
const roleType = ref<'student' | 'coach' | 'admin'>('student')
const loginMode = ref<'password' | 'code'>('password')
const passwordVisible = ref(false)

// 验证码
const codeSending = ref(false)
const codeCountdown = ref(0)
let codeTimer: ReturnType<typeof setInterval> | null = null

// 表单
const form = reactive({
  email: '',
  password: '',
  code: ''
})

const loading = ref(false)
const errors = reactive({ email: '', password: '', code: '' })

// 角色配置
const roleConfig = {
  student: { label: '学员', icon: '🎓', color: '#1677ff', desc: '驾考/客运/货运/危险品' },
  coach: { label: '教练', icon: '👨‍🏫', color: '#52c41a', desc: '驾校教练专属入口' },
  admin: { label: '平台管理员', icon: '⚙️', color: '#fa8c16', desc: '后台管理系统' }
}

const currentRole = computed(() => roleConfig[roleType.value])

// 发送验证码
async function sendCode() {
  if (codeCountdown.value > 0) return
  errors.email = ''
  if (!form.email.trim()) {
    errors.email = '请输入邮箱'
    return
  }
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    errors.email = '邮箱格式不正确'
    return
  }

  codeSending.value = true
  try {
    const res = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, type: 'login' })
    })
    const json = await res.json()
    if (json.code === 0) {
      appStore.showToast('验证码已发送', 'success')
    } else {
      appStore.showToast(json.message || '发送失败', 'error')
      return
    }
  } catch {
    appStore.showToast('发送失败，请稍后重试', 'error')
    return
  } finally {
    codeSending.value = false
  }

  codeCountdown.value = 60
  codeTimer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      if (codeTimer) clearInterval(codeTimer)
      codeTimer = null
    }
  }, 1000)
}

// 登录 API 映射
const loginApiMap: Record<string, string> = {
  student: '/api/auth/student/login',
  coach: '/api/auth/coach/login',
  admin: '/api/auth/admin/login'
}

// 注册路由映射
const registerRouteMap: Record<string, string> = {
  student: '/register/student',
  coach: '/register/coach',
  admin: '/register/admin'
}

// 首页映射
const homeRouteMap: Record<string, string> = {
  student: '/student/home',
  coach: '/coach/students',
  admin: '/admin/users'
}

async function handleLogin() {
  errors.email = ''
  errors.password = ''
  errors.code = ''

  let valid = true
  if (!form.email.trim()) {
    errors.email = '请输入邮箱'
    valid = false
  } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    errors.email = '邮箱格式不正确'
    valid = false
  }

  if (loginMode.value === 'password') {
    if (!form.password) {
      errors.password = '请输入密码'
      valid = false
    } else if (form.password.length < 6) {
      errors.password = '密码至少6位'
      valid = false
    }
  } else {
    if (!form.code.trim()) {
      errors.code = '请输入验证码'
      valid = false
    } else if (form.code.length < 4) {
      errors.code = '验证码至少4位'
      valid = false
    }
  }

  if (!valid) return

  loading.value = true
  try {
    const res = await fetch(loginApiMap[roleType.value], {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.email,
        password: loginMode.value === 'password' ? form.password : undefined,
        code: loginMode.value === 'code' ? form.code : undefined
      })
    })
    const json = await res.json()

    if (json.code === 0) {
      authStore.setAuth(json.data)
      appStore.showToast('登录成功', 'success')
      const redirect = (route.query.redirect as string) || homeRouteMap[roleType.value]
      router.push(redirect)
    } else {
      appStore.showToast(json.message || '登录失败', 'error')
    }
  } catch {
    appStore.showToast('网络错误，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <div class="auth-form">
      <h2 class="form-title">用户登录</h2>

      <!-- 角色选择卡片 -->
      <div class="role-cards">
        <button
          v-for="(cfg, key) in roleConfig"
          :key="key"
          :class="['role-card', { active: roleType === key }]"
          @click="roleType = key as 'student' | 'coach' | 'admin'"
        >
          <span class="role-icon">{{ cfg.icon }}</span>
          <span class="role-name">{{ cfg.label }}</span>
        </button>
      </div>

      <!-- 登录模式切换 -->
      <div class="login-mode-tabs">
        <button
          :class="{ active: loginMode === 'password' }"
          class="mode-btn"
          @click="loginMode = 'password'"
        >密码登录</button>
        <button
          :class="{ active: loginMode === 'code' }"
          class="mode-btn"
          @click="loginMode = 'code'"
        >验证码登录</button>
      </div>

      <!-- 表单 -->
      <form class="form-body" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input
            v-model="form.email"
            type="email"
            placeholder="请输入邮箱地址"
            class="form-input"
            :class="{ error: errors.email }"
          />
          <p v-if="errors.email" class="form-error">{{ errors.email }}</p>
        </div>

        <!-- 密码模式 -->
        <div v-if="loginMode === 'password'" class="form-group">
          <label class="form-label">密码</label>
          <div class="password-wrapper">
            <input
              v-model="form.password"
              :type="passwordVisible ? 'text' : 'password'"
              placeholder="请输入密码"
              class="form-input"
              :class="{ error: errors.password }"
            />
            <button type="button" class="password-toggle" @click="passwordVisible = !passwordVisible" tabindex="-1">
              {{ passwordVisible ? '🙈' : '👁' }}
            </button>
          </div>
          <p v-if="errors.password" class="form-error">{{ errors.password }}</p>
        </div>

        <!-- 验证码模式 -->
        <div v-else class="form-group">
          <label class="form-label">验证码</label>
          <div class="code-row">
            <input
              v-model="form.code"
              type="text"
              placeholder="请输入验证码"
              class="form-input code-input"
              :class="{ error: errors.code }"
              maxlength="6"
            />
            <button
              type="button"
              class="btn btn-outline code-btn"
              :disabled="codeCountdown > 0 || codeSending"
              @click="sendCode"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}s后重发` : (codeSending ? '发送中...' : '发送验证码') }}
            </button>
          </div>
          <p v-if="errors.code" class="form-error">{{ errors.code }}</p>
        </div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '登录中...' : `登 录（${currentRole.label}）` }}
        </button>

        <p class="form-tip">
          还没有{{ currentRole.label }}账号？
          <a href="#" @click.prevent="router.push(registerRouteMap[roleType])">立即注册</a>
        </p>
      </form>
    </div>
  </AuthLayout>
</template>

<style scoped>
.auth-form {
  width: 100%;
  max-width: 380px;
}

.form-title {
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 24px;
}

/* 角色卡片 */
.role-cards {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
}

.role-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: #fff;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.role-card:hover {
  border-color: var(--color-primary-light);
}

.role-card.active {
  border-color: var(--color-primary);
  background: var(--color-primary-lighter);
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.role-icon {
  font-size: 22px;
}

.role-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.role-card.active .role-name {
  color: var(--color-primary);
}

/* 登录模式 */
.login-mode-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--color-border-light);
}

.mode-btn {
  flex: 1;
  padding: 8px 0;
  font-size: 14px;
  color: var(--color-text-tertiary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all var(--transition-fast);
}

.mode-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 500;
}

/* 表单 */
.form-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.form-input {
  height: 44px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.form-input.error {
  border-color: var(--color-error);
}

.form-error {
  font-size: 12px;
  color: var(--color-error);
}

.password-wrapper {
  position: relative;
}

.password-wrapper .form-input {
  padding-right: 44px;
  width: 100%;
}

.password-toggle {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 6px 10px;
  line-height: 1;
  opacity: 0.6;
  transition: opacity var(--transition-fast);
}

.password-toggle:hover { opacity: 1; }

.code-row {
  display: flex;
  gap: 10px;
}

.code-input { flex: 1; }

.code-btn {
  white-space: nowrap;
  font-size: 12px;
  padding: 0 14px;
  height: 44px;
  min-width: 110px;
}

.btn-block { margin-top: 4px; }

.form-tip {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.form-tip a {
  color: var(--color-primary);
  font-weight: 500;
}
</style>
