<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  thinking: string
}

defineProps<Props>()

const isExpanded = ref(true)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="thinking-panel" :class="{ collapsed: !isExpanded }">
    <div class="panel-header" @click="toggleExpand">
      <div class="header-left">
        <span class="thinking-badge">💭</span>
        <span class="header-title">思考中...</span>
      </div>
      <button class="toggle-btn">
        {{ isExpanded ? '▼' : '▲' }}
      </button>
    </div>
    <div v-if="isExpanded" class="panel-content">
      <pre class="thinking-text">{{ thinking }}</pre>
    </div>
  </div>
</template>

<style scoped>
.thinking-panel {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.thinking-panel.collapsed {
  padding: var(--spacing-sm) var(--spacing-md);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  user-select: none;
}

.panel-header:hover {
  background: var(--bg-tertiary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.thinking-badge {
  font-size: 16px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.toggle-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  font-size: 12px;
}

.panel-content {
  padding: 0 var(--spacing-md) var(--spacing-md);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.thinking-text {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--spacing-md);
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}
</style>