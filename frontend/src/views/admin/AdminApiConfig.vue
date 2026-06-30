<script setup lang="ts">
// src/views/admin/AdminApiConfig.vue - DeepSeek API Key 配置
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import request from '@/api/request'

const appStore = useAppStore()

const apiKey = ref('')
const apiKeyMasked = ref('')
const apiKeyLoading = ref(false)
const apiKeySaving = ref(false)
const apiKeyClearing = ref(false)
const isKeyEditing = ref(false)

async function fetchApiConfig() {
  apiKeyLoading.value = true
  try {
    const res = await request.get('/api/cms/api-config')
    const json = res.data
    if (json.code === 0 && json.data && json.data.configs) {
      const dsk = json.data.configs.deepseek_api_key
      if (dsk && dsk.has_value) {
        apiKeyMasked.value = dsk.value || '已配置'
        apiKey.value = ''
      } else {
        apiKey.value = ''
        apiKeyMasked.value = ''
      }
    }
  } catch { /* 静默 */ } finally { apiKeyLoading.value = false }
}

async function saveApiKey() {
  if (!apiKey.value.trim()) { appStore.showToast('请输入 API Key', 'error'); return }
  apiKeySaving.value = true
  try {
    const res = await request.post('/api/cms/api-config', { deepseek_api_key: apiKey.value.trim() })
    if (res.data.code === 0) {
      appStore.showToast('API Key 保存成功', 'success')
      isKeyEditing.value = false
      const v = apiKey.value.trim()
      apiKeyMasked.value = v.length > 8 ? v.slice(0, 4) + '*'.repeat(v.length - 8) + v.slice(-4) : '*'.repeat(v.length)
    }
  } catch { appStore.showToast('网络错误', 'error') } finally { apiKeySaving.value = false }
}

async function clearApiKey() {
  if (!confirm('确定要清空 API Key 吗？AI 功能将无法使用。')) return
  apiKeyClearing.value = true
  try {
    const res = await request.post('/api/cms/api-config', { deepseek_api_key: '' })
    if (res.data.code === 0) { apiKey.value = ''; apiKeyMasked.value = ''; appStore.showToast('API Key 已清空', 'success') }
  } catch { appStore.showToast('网络错误', 'error') } finally { apiKeyClearing.value = false }
}

onMounted(() => fetchApiConfig())
</script>

<template>
  <div class="api-config-page">
    <div class="card">
      <div class="card-header">
        <h3>DeepSeek API Key 配置</h3>
        <span v-if="apiKeyMasked" class="status-badge status-set">已配置</span>
        <span v-else class="status-badge status-empty">未配置</span>
      </div>

      <div v-if="apiKeyLoading" class="loading-hint">加载中...</div>

      <template v-else>
        <div v-if="!isKeyEditing" class="api-config-view">
          <div class="api-key-display">
            <label class="config-label">API Key</label>
            <div class="key-field">
              <span v-if="apiKeyMasked" class="key-masked">{{ apiKeyMasked }}</span>
              <span v-else class="key-empty">尚未配置 API Key</span>
            </div>
          </div>
          <div class="api-config-info">
            <p class="info-title">说明</p>
            <ul>
              <li>API Key 用于调用 DeepSeek AI 服务，包括 AI 问答功能</li>
              <li>请前往 <a href="https://platform.deepseek.com/api_keys" target="_blank" rel="noopener">DeepSeek 开放平台</a> 获取</li>
              <li>API Key 将加密存储于服务器</li>
            </ul>
          </div>
          <div class="api-config-actions">
            <button class="btn btn-primary" @click="isKeyEditing = true">{{ apiKeyMasked ? '修改' : '配置 API Key' }}</button>
            <button v-if="apiKeyMasked" class="btn btn-danger" :disabled="apiKeyClearing" @click="clearApiKey">{{ apiKeyClearing ? '清空中...' : '清空' }}</button>
          </div>
        </div>
        <div v-else class="api-config-edit">
          <div class="form-group">
            <label class="config-label" for="apiKeyInput">API Key</label>
            <input id="apiKeyInput" v-model="apiKey" type="text" class="form-input api-key-input" placeholder="请输入 DeepSeek API Key" autocomplete="off" />
            <p class="form-hint">API Key 将以加密方式存储在服务器</p>
          </div>
          <div class="api-config-actions">
            <button class="btn btn-primary" :disabled="apiKeySaving" @click="saveApiKey">{{ apiKeySaving ? '保存中...' : '保存' }}</button>
            <button class="btn btn-outline" @click="isKeyEditing = false; fetchApiConfig()">取消</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.api-config-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.card-header h3 { font-size: var(--font-size-lg); }
.status-badge { font-size: var(--font-size-xs); padding: 2px 10px; border-radius: var(--radius-sm); font-weight: 500; }
.status-set { background: #F6FFED; color: #52C41A; }
.status-empty { background: #FFF1F0; color: #FF4D4F; }
.loading-hint { text-align: center; padding: 40px; color: var(--color-text-tertiary); }
.api-config-view, .api-config-edit { margin-top: 8px; }
.api-key-display { margin-bottom: 20px; }
.config-label { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 8px; display: block; }
.key-field { padding: 14px 16px; background: var(--color-bg); border-radius: var(--radius-md); border: 1px solid var(--color-border-light); min-height: 44px; display: flex; align-items: center; }
.key-masked { font-family: 'Courier New', Courier, monospace; font-size: var(--font-size-base); color: var(--color-text); letter-spacing: 1px; }
.key-empty { color: var(--color-text-tertiary); font-size: var(--font-size-sm); }
.api-config-info { background: #F0F5FF; border: 1px solid #D6E4FF; border-radius: var(--radius-md); padding: 16px; margin-bottom: 20px; }
.info-title { font-size: var(--font-size-sm); font-weight: 500; color: var(--color-primary); margin-bottom: 8px; }
.api-config-info ul { padding-left: 18px; margin: 0; }
.api-config-info li { font-size: var(--font-size-xs); color: var(--color-text-secondary); line-height: 1.8; }
.api-config-info a { color: var(--color-primary); text-decoration: underline; }
.api-config-actions { display: flex; gap: 10px; margin-top: 8px; }
.api-key-input { width: 100%; max-width: 520px; font-family: 'Courier New', Courier, monospace; font-size: var(--font-size-sm); }
.form-hint { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 6px; }
.form-group { margin-bottom: 20px; }
.btn-danger { background: var(--color-error); color: #fff; border: none; border-radius: var(--radius-md); padding: 8px 20px; font-size: var(--font-size-sm); cursor: pointer; }
.btn-danger:hover { opacity: 0.85; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { background: transparent; color: var(--color-text); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 8px 20px; font-size: var(--font-size-sm); cursor: pointer; }
.btn-outline:hover { border-color: var(--color-primary); color: var(--color-primary); }
</style>
