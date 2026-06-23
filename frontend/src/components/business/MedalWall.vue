<script setup lang="ts">
// src/components/business/MedalWall.vue - 勋章墙
interface Medal {
  id: number
  name: string
  icon: string
  description: string
  unlocked: boolean
  unlockedDate?: string
}

defineProps<{ medals: Medal[] }>()
</script>

<template>
  <div class="medal-wall">
    <div v-for="m in medals" :key="m.id" class="medal-item" :class="{ unlocked: m.unlocked }">
      <div class="medal-icon">{{ m.icon }}</div>
      <div class="medal-info">
        <p class="medal-name">{{ m.name }}</p>
        <p class="medal-desc">{{ m.unlocked ? (m.unlockedDate || '已解锁') : m.description }}</p>
      </div>
      <div v-if="m.unlocked" class="medal-check">✅</div>
      <div v-else class="medal-lock">🔒</div>
    </div>
  </div>
</template>

<style scoped>
.medal-wall { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.medal-item {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; border-radius: var(--radius-md);
  background: #fff; border: 1px solid var(--color-border-light);
  opacity: 0.5; transition: all var(--transition-fast);
}
.medal-item.unlocked { opacity: 1; border-color: var(--color-warning); background: #FFFBE6; }
.medal-icon { font-size: 36px; flex-shrink: 0; }
.medal-info { flex: 1; }
.medal-name { font-size: var(--font-size-sm); font-weight: 600; }
.medal-desc { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 2px; }
.medal-check, .medal-lock { font-size: 20px; flex-shrink: 0; }
</style>
