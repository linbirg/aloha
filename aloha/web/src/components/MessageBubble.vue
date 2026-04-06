j<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Message } from '@/types'

interface Props {
  message?: Message
  messageType?: 'welcome' | 'user' | 'assistant' | 'tool'
  content?: string
  showThinking?: boolean
  liveThinking?: string
}

const props = withDefaults(defineProps<Props>(), {
  messageType: 'assistant',
  showThinking: false,
  liveThinking: ''
})

const message = computed<Message>(() => {
  if (props.message) {
    return props.message
  }
  return {
    id: '',
    role: props.messageType as 'user' | 'assistant' | 'tool',
    content: props.content || '',
    timestamp: Date.now(),
    thinking: undefined,
    tool_call_id: undefined,
    tool_calls: undefined
  }
})

const isUser = computed(() => {
  return message.value.role === 'user' || props.messageType === 'user'
})

const isTool = computed(() => {
  return message.value.role === 'tool' || props.messageType === 'tool'
})

const formattedTime = computed(() => {
  const date = new Date(message.value.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const displayThinking = computed(() => {
  return props.liveThinking || message.value.thinking || ''
})

const hasThinking = computed(() => {
  return !!displayThinking.value
})

const isStreaming = computed(() => {
  return !!props.liveThinking
})

const isThinkingCollapsed = ref(false)

const toggleThinking = () => {
  isThinkingCollapsed.value = !isThinkingCollapsed.value
}
</script>

<template>
  <div :class="['message-bubble', {
    'message-user': isUser,
    'message-assistant': !isUser && !isTool,
    'message-tool': isTool,
    'message-welcome': messageType === 'welcome'
  }]">
    <!-- Avatar -->
    <div class="message-avatar">
      <span v-if="isUser" class="avatar-icon">👤</span>
      <span v-else-if="isTool" class="avatar-icon">🔧</span>
      <span v-else class="avatar-icon">🤖</span>
    </div>

    <!-- Content -->
    <div class="message-content">
      <!-- Thinking (collapsible toggle) -->
      <div v-if="hasThinking && (showThinking || liveThinking)" class="thinking-section">
        <div class="thinking-header" @click="toggleThinking">
          <div class="thinking-header-left">
            <span class="thinking-icon" :class="{ streaming: isStreaming }">💭</span>
            <span class="thinking-label">{{ isStreaming ? '思考中...' : '思考' }}</span>
          </div>
          <button class="thinking-toggle-btn" :title="isThinkingCollapsed ? '展开' : '折叠'">
            {{ isThinkingCollapsed ? '▶' : '▼' }}
          </button>
        </div>
        <pre v-show="!isThinkingCollapsed" class="thinking-content">{{ displayThinking }}</pre>
      </div>

      <!-- Main content -->
      <div class="content-text">{{ message.content || content }}</div>

      <!-- Tool result indicator -->
      <div v-if="isTool && message.tool_call_id" class="tool-indicator">
        <span class="tool-badge">🔧 工具结果</span>
      </div>

      <!-- Timestamp -->
      <div class="message-time">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<style scoped>
.message-bubble {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
}

.message-user {
  flex-direction: row-reverse;
}

.message-welcome {
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.message-tool {
  background: var(--bg-tertiary);
  border-left: 3px solid var(--accent-purple);
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: 50%;
}

.avatar-icon {
  font-size: 18px;
}

.message-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.message-user .message-content {
  align-items: flex-end;
}

.thinking-section {
  margin-bottom: var(--spacing-sm);
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

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xs);
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
}

.thinking-header:hover {
  opacity: 0.8;
}

.thinking-header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.thinking-toggle-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 10px;
  padding: 2px 4px;
}

.thinking-icon {
  font-size: 14px;
}

.thinking-icon.streaming {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.thinking-label {
  font-weight: 500;
}

.thinking-content {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', Consolas, monospace;
  line-height: 1.6;
}

.content-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-indicator {
  margin-top: var(--spacing-xs);
}

.tool-badge {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(163, 113, 247, 0.15);
  color: var(--accent-purple);
  border-radius: var(--radius-sm);
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: var(--spacing-xs);
}
</style>