<script setup lang="ts">
import { computed } from 'vue'
import type { ToolExecution } from '@/types'

interface Props {
  execution: ToolExecution
}

const props = defineProps<Props>()

const statusColor = computed(() => {
  switch (props.execution.status) {
    case 'completed': return 'success'
    case 'failed': return 'error'
    case 'rejected': return 'rejected'
    default: return 'pending'
  }
})

const statusText = computed(() => {
  switch (props.execution.status) {
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'rejected': return '已拒绝'
    default: return '进行中'
  }
})

const formattedArgs = computed(() => {
  const args = props.execution.arguments
  if (!args) return '无参数'
  
  // Format arguments for display
  if (typeof args === 'string') return args
  
  const entries = Object.entries(args as Record<string, unknown>)
  return entries.map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join('\n')
})
</script>

<template>
  <div class="tool-result-card" :class="[`status-${statusColor}`]">
    <div class="card-header">
      <div class="tool-info">
        <span class="tool-icon">🔧</span>
        <span class="tool-name">{{ execution.tool_name }}</span>
      </div>
      <span class="status-badge" :class="statusColor">{{ statusText }}</span>
    </div>
    
    <div class="card-body">
      <div class="section">
        <div class="section-label">参数</div>
        <pre class="args-content">{{ formattedArgs }}</pre>
      </div>
      
      <div v-if="execution.result" class="section">
        <div class="section-label">结果</div>
        <pre class="result-content">{{ execution.result }}</pre>
      </div>
      
      <div v-if="execution.error" class="section">
        <div class="section-label error-label">错误</div>
        <pre class="error-content">{{ execution.error }}</pre>
      </div>
    </div>
    
    <div class="card-footer">
      <span class="timestamp">
        {{ new Date(execution.timestamp).toLocaleTimeString('zh-CN') }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.tool-result-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.tool-result-card.status-completed {
  border-left: 4px solid var(--success);
}

.tool-result-card.status-failed {
  border-left: 4px solid var(--error);
}

.tool-result-card.status-rejected {
  border-left: 4px solid var(--error);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.tool-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.tool-icon {
  font-size: 16px;
}

.tool-name {
  font-weight: 600;
  color: var(--text-primary);
  font-family: monospace;
}

.status-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.status-badge.success {
  background: rgba(63, 185, 80, 0.15);
  color: var(--success);
}

.status-badge.error {
  background: rgba(248, 81, 73, 0.15);
  color: var(--error);
}

.status-badge.pending {
  background: rgba(210, 153, 34, 0.15);
  color: var(--warning);
}

.status-badge.rejected {
  background: rgba(248, 81, 73, 0.15);
  color: var(--error);
}

.card-body {
  padding: var(--spacing-md);
}

.section {
  margin-bottom: var(--spacing-md);
}

.section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: var(--spacing-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-label.error-label {
  color: var(--error);
}

.args-content,
.result-content,
.error-content {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.error-content {
  color: var(--error);
  border-color: var(--error);
  background: rgba(248, 81, 73, 0.05);
}

.card-footer {
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.timestamp {
  font-size: 11px;
  color: var(--text-muted);
}
</style>