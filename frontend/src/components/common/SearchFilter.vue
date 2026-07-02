// src/components/common/SearchFilter.vue
<script setup lang="ts">
const model = defineModel<string>()
defineProps<{ placeholder?: string; manual?: boolean }>()
const emit = defineEmits<{ search: [] }>()

function onSearch() {
  emit('search')
}
</script>

<template>
  <div class="search-filter">
    <input
      v-model="model"
      type="text"
      :placeholder="placeholder || '搜索...'"
      class="search-input"
      :class="{ 'has-btn': manual }"
      @keyup.enter="onSearch"
    />
    <button v-if="manual" class="search-btn" @click="onSearch">搜索</button>
    <span v-else class="search-icon">🔍</span>
  </div>
</template>

<style scoped>
.search-filter { display: inline-flex; align-items: center; gap: 8px; }
.search-input {
  height: 36px; padding: 0 12px; border: 1px solid var(--color-border);
  border-radius: var(--radius-md); font-size: var(--font-size-sm); outline: none;
  min-width: 200px; transition: border-color var(--transition-fast);
}
.search-input.has-btn { padding: 0 12px; }
.search-input:focus { border-color: var(--color-primary); }
.search-btn {
  height: 36px; padding: 0 16px;
  background: var(--color-primary); color: #fff;
  border: none; border-radius: var(--radius-md);
  cursor: pointer; font-size: var(--font-size-sm);
  white-space: nowrap;
}
.search-btn:hover { opacity: 0.9; }
.search-icon { font-size: 14px; color: var(--color-text-tertiary); }
</style>
