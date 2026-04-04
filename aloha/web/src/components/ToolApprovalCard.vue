<script setup lang="ts">
import { computed } from 'vue'
import type { ToolExecution, PendingApproval } from '@/types'

type ApprovalItem = ToolExecution | PendingApproval

interface Props {
  execution: ApprovalItem
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'approve', id: string): void
  (e: 'reject', id: string): void
}>()

const formattedArgs = computed(() => {
  const args = props.execution.arguments
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
})

const riskLevel = computed(() => {
  const lvl = (props.execution as PendingApproval).risk_level
  if (lvl) return lvl
  const toolRiskMap: Record<string, string> = {
    'shell': 'high',
    'bash': 'high',
    'exec': 'high',
    'read_file': 'medium',
    'write_file': 'high',
    'web': 'medium',
    'search': 'low'
  }
  return toolRiskMap[props.execution.tool_name] || 'medium'
})

const riskColor = computed(() => {
  const colors: Record<string, string> = {
    'low': 'var(--accent-green)',
    'medium': 'var(--accent-orange)',
    'high': 'var(--accent-red)'
  }
  return colors[riskLevel.value] || colors.medium
})

const riskColorFromProp = computed(() => {
  return (props.execution as PendingApproval).risk_color || riskColor.value
})

const statusText = computed(() => {
  const status = (props.execution as PendingApproval).status
  if (status === 'pending') return '⏳ 待确认'
  if (status === 'approved') return '✅ 已批准'
  if (status === 'rejected') return '✕ 已拒绝'
  if (status === 'timeout') return '⏱️ 已超时'
  return '⏳ 待确认'
})

const resource = computed(() => {
  return (props.execution as PendingApproval).resource || ''
})

const queueInfo = computed(() => {
  const approval = props.execution as PendingApproval
  if (approval.queue_total > 1) {
    return `(${approval.queue_position}/${approval.queue_total})`
  }
  return ''
})

const handleApprove = () => emit('approve', props.execution.id)
const handleReject = () => emit('reject', props.execution.id)
</script>

<template>
  <div class="tool-approval-card">
    <!-- Header -->
    <div class="card-header">
      <div class="tool-icon">🔧</div>
      <div class="tool-info">
        <span class="tool-name">{{ execution.tool_name }}</span>
        <span 
          class="risk-badge" 
          :style="{ color: riskColorFromProp, borderColor: riskColorFromProp }"
        >
          {{ riskLevel.toUpperCase() }} 风险
        </span>
        <span v-if="queueInfo" class="queue-badge">{{ queueInfo }}</span>
      </div>
      <div class="pending-indicator">{{ statusText }}</div>
    </div>

    <!-- Resource -->
    <div v-if="resource" class="resource-info">
      <span class="label">资源:</span>
      <code class="value">{{ resource }}</code>
    </div>

    <!-- Arguments -->
    <div class="arguments-section">
      <div class="section-label">参数:</div>
      <pre class="arguments-json">{{ formattedArgs }}</pre>
    </div>

    <!-- Warning Message -->
    <div class="warning-message">
      <span class="warning-icon">⚠️</span>
      执行此操作需要您的确认
    </div>

    <!-- Action Buttons -->
    <div class="action-buttons" v-if="(execution as PendingApproval).status === 'pending'">
      <button 
        class="btn btn-danger reject-btn"
        @click="handleReject"
      >
        <span class="btn-icon">✕</span>
        拒绝
      </button>
      <button 
        class="btn btn-success approve-btn"
        @click="handleApprove"
      >
        <span class="btn-icon">✓</span>
        确认执行
      </button>
    </div>
  </div>
</template>

<style scoped>
.tool-approval-card {
  background: var(--bg-secondary);
  border: 2px solid var(--accent-orange);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin: var(--spacing-md) 0;
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0%, 100% {
    border-color: var(--accent-orange);
  }
  50% {
    border-color: rgba(210, 153, 34, 0.5);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.tool-icon {
  font-size: 24px;
}

.tool-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.tool-name {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}

.risk-badge {
  font-size: 11px;
  padding: 2px 6px;
  border: 1px solid;
  border-radius: var(--radius-sm);
  width: fit-content;
}

.queue-badge {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent-blue);
  border-radius: var(--radius-sm);
  width: fit-content;
}

.pending-indicator {
  font-size: 14px;
  color: var(--accent-orange);
}

.tool-id {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  font-size: 12px;
}

.tool-id .label {
  color: var(--text-secondary);
}

.tool-id .value {
  font-family: monospace;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.resource-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  font-size: 12px;
}

.resource-info .label {
  color: var(--text-secondary);
}

.resource-info .value {
  font-family: monospace;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.arguments-section {
  margin-bottom: var(--spacing-md);
}

.section-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.arguments-json {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  font-family: monospace;
  font-size: 12px;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre;
}

.warning-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: rgba(210, 153, 34, 0.1);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-md);
  font-size: 13px;
  color: var(--accent-orange);
}

.warning-icon {
  font-size: 16px;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.btn-icon {
  font-size: 14px;
}

.reject-btn,
.approve-btn {
  min-width: 100px;
}
</style>