// src/components/common/SearchFilter.vue
<script setup lang="ts">
const model = defineModel<string>()
defineProps<{ placeholder?: string }>()
</script>

<template>
  <div class="search-filter">
    <input v-model="model" type="text" :placeholder="placeholder || '搜索...'" class="search-input" />
    <span class="search-icon">🔍</span>
  </div>
</template>

<style scoped>
.search-filter { position: relative; display: inline-block; }
.search-input {
  height: 36px; padding: 0 36px 0 12px; border: 1px solid var(--color-border);
  border-radius: var(--radius-md); font-size: var(--font-size-sm); outline: none;
  min-width: 200px; transition: border-color var(--transition-fast);
}
.search-input:focus { border-color: var(--color-primary); }
.search-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-size: 14px; }
</style>
