<script setup lang="ts">
// src/components/business/KnowledgeTreeMap.vue - 知识树地图
interface TreeNode {
  name: string
  value: number
  completed: number
  color: string
}

defineProps<{ nodes: TreeNode[] }>()
</script>

<template>
  <div class="tree-map">
    <div v-for="node in nodes" :key="node.name" class="tree-node">
      <div class="node-header">
        <span class="node-name">{{ node.name }}</span>
        <span class="node-rate">{{ Math.round((node.completed / node.value) * 100) }}%</span>
      </div>
      <div class="node-bar">
        <div class="node-fill" :style="{ width: Math.round((node.completed / node.value) * 100) + '%', background: node.color }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tree-map { display: flex; flex-direction: column; gap: 16px; }
.tree-node { }
.node-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.node-name { font-size: var(--font-size-sm); font-weight: 500; }
.node-rate { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
.node-bar { height: 10px; background: #F0F0F0; border-radius: 5px; overflow: hidden; }
.node-fill { height: 100%; border-radius: 5px; transition: width 0.6s ease; }
</style>
