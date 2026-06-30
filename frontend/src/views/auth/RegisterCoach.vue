<script setup lang="ts">
// src/views/auth/RegisterCoach.vue - 教练注册
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import AuthLayout from '@/components/layout/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const passwordVisible = ref(false)
const confirmVisible = ref(false)

const codeSending = ref(false)
const codeCountdown = ref(0)
let codeTimer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  schoolName: '',
  trainType: 1 as number,
  schoolAddress: '',
  schoolPhone: '',
  code: ''
})

const loading = ref(false)
const errors = reactive({
  email: '', password: '', confirmPassword: '',
  schoolName: '', trainType: '', code: ''
})

async function sendCode() {
  if (codeCountdown.value > 0) return
  errors.email = ''
  if (!form.email.trim()) { errors.email = '请输入邮箱'; return }
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    errors.email = '邮箱格式不正确'; return
  }

  codeSending.value = true
  try {
    const res = await fetch('/api/auth/send-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, type: 'register' })
    })
    const json = await res.json()
    if (json.code === 0) {
      appStore.showToast('验证码已发送', 'success')
    } else {
      appStore.showToast(json.message || '发送失败', 'error')
      return
    }
  } catch {
    appStore.showToast('发送失败', 'error')
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

function validate(): boolean {
  Object.keys(errors).forEach(k => (errors as any)[k] = '')
  let valid = true

  if (!form.email.trim()) { errors.email = '请输入邮箱'; valid = false }
  else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(form.email)) {
    errors.email = '邮箱格式不正确'; valid = false
  }
  if (!form.password || form.password.length < 6) {
    errors.password = '密码至少6位'; valid = false
  }
  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次密码不一致'; valid = false
  }
  if (!form.schoolName.trim()) {
    errors.schoolName = '请输入所属驾校名称'; valid = false
  }
  if (![1, 2, 3, 4].includes(form.trainType)) {
    errors.trainType = '请选择培训类型'; valid = false
  }
  if (!form.code.trim()) { errors.code = '请输入验证码'; valid = false }

  return valid
}

async function handleSubmit() {
  if (!validate()) return
  loading.value = true
  try {
    const res = await fetch('/api/auth/coach/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.email,
        password: form.password,
        schoolName: form.schoolName.trim(),
        trainType: form.trainType,
        schoolAddress: form.schoolAddress.trim() || undefined,
        schoolPhone: form.schoolPhone.trim() || undefined,
        code: form.code
      })
    })
    const json = await res.json()
    if (json.code === 0) {
      authStore.setAuth(json.data)
      appStore.showToast('注册成功', 'success')
      router.push('/coach/students')
    } else {
      appStore.showToast(json.message || '注册失败', 'error')
    }
  } catch {
    appStore.showToast('网络错误', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout>
    <div class="auth-form">
      <h2 class="form-title">👨‍🏫 教练注册</h2>

      <form class="form-body" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">邮箱</label>
          <input v-model="form.email" type="email" placeholder="请输入邮箱地址" class="form-input" :class="{ error: errors.email }" />
          <p v-if="errors.email" class="form-error">{{ errors.email }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">密码</label>
          <div class="password-wrapper">
            <input v-model="form.password" :type="passwordVisible ? 'text' : 'password'" placeholder="至少6位，含字母和数字" class="form-input" :class="{ error: errors.password }" />
            <button type="button" class="password-toggle" @click="passwordVisible = !passwordVisible" tabindex="-1">{{ passwordVisible ? '🙈' : '👁' }}</button>
          </div>
          <p v-if="errors.password" class="form-error">{{ errors.password }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">确认密码</label>
          <div class="password-wrapper">
            <input v-model="form.confirmPassword" :type="confirmVisible ? 'text' : 'password'" placeholder="请再次输入密码" class="form-input" :class="{ error: errors.confirmPassword }" />
            <button type="button" class="password-toggle" @click="confirmVisible = !confirmVisible" tabindex="-1">{{ confirmVisible ? '🙈' : '👁' }}</button>
          </div>
          <p v-if="errors.confirmPassword" class="form-error">{{ errors.confirmPassword }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">所属驾校名称</label>
          <input v-model="form.schoolName" type="text" placeholder="请输入驾校名称" class="form-input" :class="{ error: errors.schoolName }" />
          <p v-if="errors.schoolName" class="form-error">{{ errors.schoolName }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">培训类型</label>
          <select v-model.number="form.trainType" class="form-input" :class="{ error: errors.trainType }">
            <option :value="1">🚗 驾考</option>
            <option :value="2">🚌 客运</option>
            <option :value="3">🚛 货运</option>
            <option :value="4">☣️ 危险品</option>
          </select>
          <p v-if="errors.trainType" class="form-error">{{ errors.trainType }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">驾校地址（可选）</label>
          <input v-model="form.schoolAddress" type="text" placeholder="请输入驾校地址" class="form-input" />
        </div>

        <div class="form-group">
          <label class="form-label">驾校联系电话（可选）</label>
          <input v-model="form.schoolPhone" type="text" placeholder="请输入驾校电话" class="form-input" />
        </div>

        <div class="form-group">
          <label class="form-label">验证码</label>
          <div class="code-row">
            <input v-model="form.code" type="text" placeholder="请输入验证码" class="form-input code-input" :class="{ error: errors.code }" maxlength="6" />
            <button type="button" class="btn btn-outline code-btn" :disabled="codeCountdown > 0 || codeSending" @click="sendCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s后重发` : (codeSending ? '发送中...' : '发送验证码') }}
            </button>
          </div>
          <p v-if="errors.code" class="form-error">{{ errors.code }}</p>
        </div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>

        <p class="form-tip">
          已有账号？<a href="#" @click.prevent="router.push('/login')">立即登录</a>
        </p>
      </form>
    </div>
  </AuthLayout>
</template>

<style scoped>
.auth-form { width: 100%; max-width: 380px; }
.form-title { text-align: center; font-size: 22px; font-weight: 600; margin-bottom: 24px; color: var(--color-text-primary); }
.form-body { display: flex; flex-direction: column; gap: 18px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 14px; color: var(--color-text-secondary); }
.form-input { height: 44px; padding: 0 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); font-size: 14px; outline: none; transition: border-color var(--transition-fast); background: #fff; width: 100%; }
.form-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px var(--color-primary-light); }
.form-input.error { border-color: var(--color-error); }
.form-error { font-size: 12px; color: var(--color-error); }
.password-wrapper { position: relative; }
.password-wrapper .form-input { padding-right: 44px; }
.password-toggle { position: absolute; right: 4px; top: 50%; transform: translateY(-50%); background: none; border: none; font-size: 18px; cursor: pointer; padding: 6px 10px; line-height: 1; opacity: 0.6; }
.password-toggle:hover { opacity: 1; }
.code-row { display: flex; gap: 10px; }
.code-input { flex: 1; }
.code-btn { white-space: nowrap; font-size: 12px; padding: 0 14px; height: 44px; min-width: 110px; }
.btn-block { margin-top: 4px; }
select.form-input { cursor: pointer; appearance: auto; }
.form-tip { text-align: center; font-size: 14px; color: var(--color-text-tertiary); }
.form-tip a { color: var(--color-primary); font-weight: 500; }
</style>
