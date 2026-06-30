<script setup lang="ts">
// src/components/layout/AuthLayout.vue
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-banner">
        <div class="banner-content">
          <div class="banner-logo">🚦</div>
          <h1 class="banner-title">交通安全培训平台</h1>
          <p class="banner-desc">基于DeepSeek大模型 · AI驱动的智能学车助手</p>
          <div class="banner-features">
            <div class="feature-item">
              <span class="feature-icon">🤖</span>
              <span>AI交规问答</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span>能力雷达图</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🎯</span>
              <span>精准学习路径</span>
            </div>
          </div>
        </div>
      </div>
      <div class="auth-form-wrapper">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #E6F4FF 0%, #F0F5FF 50%, #FFF7E6 100%);
  padding: 40px 20px;
}

.auth-container {
  display: flex;
  width: 960px;
  min-height: 600px;
  background: #fff;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.auth-banner {
  flex: 0 0 440px;
  background: linear-gradient(135deg, var(--color-primary), #4096FF);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.banner-content {
  color: #fff;
  text-align: center;
}

.banner-logo {
  font-size: 64px;
  margin-bottom: 20px;
}

.banner-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.banner-desc {
  font-size: var(--font-size-base);
  opacity: 0.85;
  margin-bottom: 40px;
  line-height: 1.6;
}

.banner-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  backdrop-filter: blur(4px);
}

.feature-icon {
  font-size: 20px;
}

.auth-form-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

@media (max-width: 768px) {
  .auth-container {
    flex-direction: column;
    width: 100%;
    max-width: 420px;
  }
  .auth-banner {
    flex: 0 0 auto;
    padding: 32px 24px;
  }
  .banner-features {
    grid-template-columns: 1fr;
  }
}
</style>
