<script setup lang="ts">
// src/components/business/ContrastCard.vue - 易混淆对比卡片
defineProps<{
  leftTitle: string
  leftContent: string
  rightTitle: string
  rightContent: string
  highlightDiff?: string
  memoryTip?: string
}>()
</script>

<template>
  <div class="contrast-card">
    <div class="contrast-grid">
      <div class="contrast-item left">
        <div class="contrast-label">A</div>
        <h4>{{ leftTitle }}</h4>
        <p>{{ leftContent }}</p>
      </div>
      <div class="contrast-item right">
        <div class="contrast-label">B</div>
        <h4>{{ rightTitle }}</h4>
        <p>{{ rightContent }}</p>
      </div>
    </div>
    <div v-if="highlightDiff" class="contrast-diff">
      <strong>关键差异：</strong>{{ highlightDiff }}
    </div>
    <div v-if="memoryTip" class="contrast-tip">
      💡 <strong>记忆口诀：</strong>{{ memoryTip }}
    </div>
  </div>
</template>

<style scoped>
.contrast-card {
  background: #fff; border-radius: var(--radius-lg); padding: 20px;
  border: 1px solid var(--color-border-light); margin-bottom: 16px;
}
.contrast-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;
}
.contrast-item {
  padding: 16px; border-radius: var(--radius-md); position: relative;
  border: 1px solid var(--color-border);
}
.contrast-item.left { background: #E6F4FF; }
.contrast-item.right { background: #FFF7E6; }
.contrast-label {
  position: absolute; top: -10px; left: 12px;
  background: var(--color-primary); color: #fff; width: 24px; height: 24px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.contrast-item.right .contrast-label { background: var(--color-warning); }
.contrast-item h4 { font-size: var(--font-size-sm); margin-bottom: 6px; }
.contrast-item p { font-size: var(--font-size-xs); color: var(--color-text-secondary); line-height: 1.6; }
.contrast-diff {
  padding: 10px 14px; background: #FFF1F0; border-radius: var(--radius-md);
  font-size: var(--font-size-xs); color: var(--color-error); margin-bottom: 10px;
}
.contrast-tip {
  padding: 10px 14px; background: #F6FFED; border-radius: var(--radius-md);
  font-size: var(--font-size-xs); color: var(--color-success);
}
</style>
