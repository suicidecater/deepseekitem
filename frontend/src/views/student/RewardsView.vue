<script setup lang="ts">
// src/views/student/RewardsView.vue - 学习激励系统
import { ref, onMounted } from 'vue'
import MedalWall from '@/components/business/MedalWall.vue'
import Leaderboard from '@/components/business/Leaderboard.vue'

const streakDays = ref(12)

const medals = ref([
  { id: 1, name: '初出茅庐', icon: '🥉', description: '连续学习7天', unlocked: true, unlockedDate: '2026-03-22' },
  { id: 2, name: '持之以恒', icon: '🥈', description: '连续学习30天', unlocked: false },
  { id: 3, name: '学神降临', icon: '🥇', description: '连续学习90天', unlocked: false },
  { id: 4, name: '学霸认证', icon: '🏆', description: '正确率达到90%以上', unlocked: false },
  { id: 5, name: '满分达人', icon: '💯', description: '模拟考试满分', unlocked: false },
  { id: 6, name: '答题狂人', icon: '⚡', description: '累计做题1000道', unlocked: true, unlockedDate: '2026-04-15' },
  { id: 7, name: '速度之星', icon: '🚀', description: '平均答题<15秒/题', unlocked: false },
  { id: 8, name: '全能选手', icon: '🌟', description: '四维度均超80分', unlocked: false },
])

const leaderboardData = ref([
  { rank: 1, name: '王小明', score: 98, accuracy: 96 },
  { rank: 2, name: '李华', score: 96, accuracy: 94 },
  { rank: 3, name: '赵丽', score: 94, accuracy: 92 },
  { rank: 4, name: '张三', score: 88, accuracy: 85, isMe: true },
  { rank: 5, name: '陈强', score: 85, accuracy: 82 },
])

onMounted(() => {})
</script>

<template>
  <div class="rewards-page">
    <div class="page-header">
      <h2>学习激励</h2>
    </div>

    <!-- 连续学习 -->
    <div class="streak-banner">
      <div class="streak-content">
        <span class="streak-fire">🔥</span>
        <div>
          <p class="streak-days">已连续学习 <strong>{{ streakDays }}</strong> 天</p>
          <p class="streak-hint">再坚持18天获得"持之以恒"勋章！</p>
        </div>
      </div>
    </div>

    <!-- 勋章墙 -->
    <div class="card">
      <h3>勋章墙</h3>
      <MedalWall :medals="medals" />
    </div>

    <!-- 排行榜 -->
    <div class="card">
      <h3>同驾校排行榜</h3>
      <Leaderboard :items="leaderboardData" />
    </div>
  </div>
</template>

<style scoped>
.rewards-page { max-width: 800px; margin: 0 auto; padding: 24px; }
.page-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }

.streak-banner {
  background: linear-gradient(135deg, #FFF7E6, #FFF1CC);
  border-radius: var(--radius-xl); padding: 20px 28px; margin-bottom: 24px;
  border: 1px solid #FFD666;
}
.streak-content { display: flex; align-items: center; gap: 16px; }
.streak-fire { font-size: 48px; }
.streak-days { font-size: var(--font-size-lg); }
.streak-days strong { font-size: 32px; color: var(--color-warning); }
.streak-hint { font-size: var(--font-size-xs); color: var(--color-text-tertiary); margin-top: 4px; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.card h3 { font-size: var(--font-size-lg); margin-bottom: 16px; }
</style>
