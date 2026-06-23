<script setup lang="ts">
// src/views/auth/LoginView.vue
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import AuthLayout from '@/components/layout/AuthLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

// Tab 切换
const activeTab = ref<'login' | 'register'>('login')
const loginType = ref<'email' | 'phone'>('email')
const loginMode = ref<'password' | 'code'>('password') // #2 新增：密码/验证码模式

// 密码可见切换（#3）
const passwordVisible = ref(false)
const regPasswordVisible = ref(false)
const regConfirmVisible = ref(false)

// 验证码相关（#2）
const codeSending = ref(false)
const codeCountdown = ref(0)
let codeTimer: ReturnType<typeof setInterval> | null = null

// 表单
const loginForm = reactive({
  account: '',
  password: '',
  code: '' // #2 新增
})

const registerForm = reactive({
  name: '',
  account: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false
})

const loading = ref(false)
const loginErrors = reactive({ account: '', password: '', code: '' })
const registerErrors = reactive({ name: '', account: '', password: '', confirmPassword: '', agreeTerms: '' })

// 登录类型 label
const accountLabel = computed(() => loginType.value === 'email' ? '邮箱' : '手机号')
const accountPlaceholder = computed(() => loginType.value === 'email' ? '请输入邮箱地址' : '请输入手机号')

// #2 发送验证码
async function sendCode() {
  if (codeCountdown.value > 0) return

  // 校验账号
  loginErrors.account = ''
  if (!loginForm.account.trim()) {
    loginErrors.account = `请输入${accountLabel.value}`
    return
  }
  if (loginType.value === 'phone' && !/^1[3-9]\d{9}$/.test(loginForm.account)) {
    loginErrors.account = '手机号格式不正确'
    return
  }
  if (loginType.value === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(loginForm.account)) {
    loginErrors.account = '邮箱格式不正确'
    return
  }

  codeSending.value = true
  try {
    await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account: loginForm.account, loginType: loginType.value })
    })
    appStore.showToast('验证码已发送', 'success')

    // 60秒倒计时
    codeCountdown.value = 60
    codeTimer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        if (codeTimer) clearInterval(codeTimer)
        codeTimer = null
      }
    }, 1000)
  } catch {
    appStore.showToast('发送失败，请稍后重试', 'error')
  } finally {
    codeSending.value = false
  }
}

// Mock 登录
async function handleLogin() {
  // 校验
  loginErrors.account = ''
  loginErrors.password = ''
  loginErrors.code = ''

  let valid = true
  if (!loginForm.account.trim()) {
    loginErrors.account = `请输入${accountLabel.value}`
    valid = false
  } else if (loginType.value === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(loginForm.account)) {
    loginErrors.account = '邮箱格式不正确'
    valid = false
  } else if (loginType.value === 'phone' && !/^1[3-9]\d{9}$/.test(loginForm.account)) {
    loginErrors.account = '手机号格式不正确'
    valid = false
  }

  if (loginMode.value === 'code') {
    if (!loginForm.code.trim()) {
      loginErrors.code = '请输入验证码'
      valid = false
    } else if (loginForm.code.length < 4) {
      loginErrors.code = '验证码至少4位'
      valid = false
    }
  } else {
    if (!loginForm.password) {
      loginErrors.password = '请输入密码'
      valid = false
    } else if (loginForm.password.length < 6) {
      loginErrors.password = '密码至少6位'
      valid = false
    }
  }

  if (!valid) return

  loading.value = true

  try {
    // Mock API
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account: loginForm.account,
        password: loginMode.value === 'password' ? loginForm.password : undefined,
        code: loginMode.value === 'code' ? loginForm.code : undefined,
        loginType: loginType.value,
        loginMode: loginMode.value
      })
    })
    const json = await res.json()

    if (json.code === 0) {
      authStore.setAuth(json.data)
      appStore.showToast('登录成功', 'success')

      const redirect = (route.query.redirect as string) || '/student/home'
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

// Mock 注册
async function handleRegister() {
  // 校验
  registerErrors.name = ''
  registerErrors.account = ''
  registerErrors.password = ''
  registerErrors.confirmPassword = ''
  registerErrors.agreeTerms = ''

  let valid = true
  if (registerForm.name.trim().length < 2) {
    registerErrors.name = '姓名至少2个字符'
    valid = false
  }
  if (!registerForm.account.trim()) {
    registerErrors.account = '请输入邮箱或手机号'
    valid = false
  }
  if (!registerForm.password || registerForm.password.length < 6) {
    registerErrors.password = '密码至少6位'
    valid = false
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    registerErrors.confirmPassword = '两次密码不一致'
    valid = false
  }
  if (!registerForm.agreeTerms) {
    registerErrors.agreeTerms = '请同意用户协议'
    valid = false
  }

  if (!valid) return

  loading.value = true

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: registerForm.name,
        account: registerForm.account,
        password: registerForm.password,
        registerType: loginType.value
      })
    })
    const json = await res.json()

    if (json.code === 0) {
      authStore.setAuth(json.data)
      appStore.showToast('注册成功', 'success')
      router.push('/student/home')
    } else {
      appStore.showToast(json.message || '注册失败', 'error')
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
      <!-- Tab 切换 -->
      <div class="auth-tabs">
        <button
          :class="{ active: activeTab === 'login' }"
          class="tab-btn"
          @click="activeTab = 'login'"
        >登录</button>
        <button
          :class="{ active: activeTab === 'register' }"
          class="tab-btn"
          @click="activeTab = 'register'"
        >注册</button>
      </div>

      <!-- 登录类型切换 -->
      <div class="login-type-tabs">
        <button
          :class="{ active: loginType === 'email' }"
          class="type-btn"
          @click="loginType = 'email'"
        >邮箱登录</button>
        <button
          :class="{ active: loginType === 'phone' }"
          class="type-btn"
          @click="loginType = 'phone'"
        >手机号登录</button>
      </div>

      <!-- 登录模式切换（密码/验证码）（#2） -->
      <div v-if="activeTab === 'login'" class="login-mode-tabs">
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

      <!-- 登录表单 -->
      <form v-if="activeTab === 'login'" class="form-body" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">{{ accountLabel }}</label>
          <input
            v-model="loginForm.account"
            :type="loginType === 'email' ? 'email' : 'tel'"
            :placeholder="accountPlaceholder"
            class="form-input"
            :class="{ error: loginErrors.account }"
          />
          <p v-if="loginErrors.account" class="form-error">{{ loginErrors.account }}</p>
        </div>

        <!-- 密码登录模式 -->
        <template v-if="loginMode === 'password'">
          <div class="form-group">
            <label class="form-label">密码</label>
            <div class="password-wrapper">
              <input
                v-model="loginForm.password"
                :type="passwordVisible ? 'text' : 'password'"
                placeholder="请输入密码"
                class="form-input"
                :class="{ error: loginErrors.password }"
              />
              <button type="button" class="password-toggle" @click="passwordVisible = !passwordVisible" tabindex="-1">
                {{ passwordVisible ? '🙈' : '👁' }}
              </button>
            </div>
            <p v-if="loginErrors.password" class="form-error">{{ loginErrors.password }}</p>
          </div>
        </template>

        <!-- 验证码登录模式（#2） -->
        <template v-else>
          <div class="form-group">
            <label class="form-label">验证码</label>
            <div class="code-row">
              <input
                v-model="loginForm.code"
                type="text"
                placeholder="请输入验证码"
                class="form-input code-input"
                :class="{ error: loginErrors.code }"
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
            <p v-if="loginErrors.code" class="form-error">{{ loginErrors.code }}</p>
          </div>
        </template>

        <div class="form-extra">
          <label class="remember-me">
            <input type="checkbox" /> 记住我
          </label>
          <a href="#" class="forgot-link">忘记密码？</a>
        </div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>

        <p class="form-tip">
          还没有账号？<a href="#" @click.prevent="activeTab = 'register'">立即注册</a>
        </p>
      </form>

      <!-- 注册表单 -->
      <form v-else class="form-body" @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label">姓名</label>
          <input
            v-model="registerForm.name"
            type="text"
            placeholder="请输入真实姓名"
            class="form-input"
            :class="{ error: registerErrors.name }"
          />
          <p v-if="registerErrors.name" class="form-error">{{ registerErrors.name }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">{{ accountLabel }}</label>
          <input
            v-model="registerForm.account"
            :type="loginType === 'email' ? 'email' : 'tel'"
            :placeholder="accountPlaceholder"
            class="form-input"
            :class="{ error: registerErrors.account }"
          />
          <p v-if="registerErrors.account" class="form-error">{{ registerErrors.account }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <div class="password-wrapper">
            <input
              v-model="registerForm.password"
              :type="regPasswordVisible ? 'text' : 'password'"
              placeholder="请设置密码（至少6位）"
              class="form-input"
              :class="{ error: registerErrors.password }"
            />
            <button type="button" class="password-toggle" @click="regPasswordVisible = !regPasswordVisible" tabindex="-1">
              {{ regPasswordVisible ? '🙈' : '👁' }}
            </button>
          </div>
          <p v-if="registerErrors.password" class="form-error">{{ registerErrors.password }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">确认密码</label>
          <div class="password-wrapper">
            <input
              v-model="registerForm.confirmPassword"
              :type="regConfirmVisible ? 'text' : 'password'"
              placeholder="请再次输入密码"
              class="form-input"
              :class="{ error: registerErrors.confirmPassword }"
            />
            <button type="button" class="password-toggle" @click="regConfirmVisible = !regConfirmVisible" tabindex="-1">
              {{ regConfirmVisible ? '🙈' : '👁' }}
            </button>
          </div>
          <p v-if="registerErrors.confirmPassword" class="form-error">{{ registerErrors.confirmPassword }}</p>
        </div>

        <div class="form-group">
          <label class="agree-terms">
            <input v-model="registerForm.agreeTerms" type="checkbox" />
            <span>我已阅读并同意 <a href="#">《用户服务协议》</a> 和 <a href="#">《隐私政策》</a></span>
          </label>
          <p v-if="registerErrors.agreeTerms" class="form-error">{{ registerErrors.agreeTerms }}</p>
        </div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>

        <p class="form-tip">
          已有账号？<a href="#" @click.prevent="activeTab = 'login'">立即登录</a>
        </p>
      </form>
    </div>
  </AuthLayout>
</template>

<style scoped>
.auth-form {
  width: 100%;
  max-width: 360px;
}

.auth-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--color-border-light);
}

.tab-btn {
  flex: 1;
  padding: 12px 0;
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--color-text-tertiary);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all var(--transition-fast);
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.login-type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 28px;
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: 4px;
}

.type-btn {
  flex: 1;
  padding: 8px 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.type-btn.active {
  background: #fff;
  color: var(--color-primary);
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

/* 登录模式切换（密码/验证码） */
.login-mode-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--color-border-light);
}

.mode-btn {
  flex: 1;
  padding: 8px 0;
  font-size: var(--font-size-sm);
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

/* 密码可见切换（#3） */
.password-wrapper {
  position: relative;
}
.password-wrapper .form-input {
  padding-right: 44px;
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
.password-toggle:hover {
  opacity: 1;
}

/* 验证码行（#2） */
.code-row {
  display: flex;
  gap: 10px;
}
.code-input {
  flex: 1;
}
.code-btn {
  white-space: nowrap;
  font-size: var(--font-size-xs);
  padding: 0 14px;
  height: 44px;
  min-width: 110px;
}

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
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.form-input {
  height: 44px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
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
  font-size: var(--font-size-xs);
  color: var(--color-error);
}

.form-extra {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.forgot-link {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
}

.agree-terms {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  cursor: pointer;
  line-height: 1.6;
}
.agree-terms a {
  color: var(--color-primary);
}

.form-tip {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}
.form-tip a {
  color: var(--color-primary);
  font-weight: 500;
}

.btn-block {
  margin-top: 4px;
}
</style>
