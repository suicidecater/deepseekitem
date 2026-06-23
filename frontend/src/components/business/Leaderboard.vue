<script setup lang="ts">
// src/components/business/Leaderboard.vue - 排行榜
interface RankItem {
  rank: number
  name: string
  score: number
  accuracy: number
  isMe?: boolean
}

defineProps<{ items: RankItem[] }>()
</script>

<template>
  <div class="leaderboard">
    <div v-for="item in items" :key="item.rank" class="rank-item" :class="{ me: item.isMe }">
      <span class="rank-num" :class="'rank-' + item.rank">{{ item.rank <= 3 ? ['🥇','🥈','🥉'][item.rank-1] : item.rank }}</span>
      <span class="rank-name">{{ item.name }}{{ item.isMe ? ' (我)' : '' }}</span>
      <span class="rank-score">{{ item.score }}分</span>
      <span class="rank-accuracy">{{ item.accuracy }}%</span>
    </div>
  </div>
</template>

<style scoped>
.leaderboard { display: flex; flex-direction: column; gap: 6px; }
.rank-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  border-radius: var(--radius-md); background: #FAFAFA; font-size: var(--font-size-sm);
}
.rank-item.me { background: var(--color-primary-light); font-weight: 600; }
.rank-num { width: 30px; text-align: center; font-weight: 700; }
.rank-name { flex: 1; }
.rank-score, .rank-accuracy { width: 48px; text-align: right; color: var(--color-text-secondary); }
</style>
