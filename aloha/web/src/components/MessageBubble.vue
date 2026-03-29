j<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/types'

interface Props {
  message?: Message
  messageType?: 'welcome' | 'user' | 'assistant' | 'tool'
  content?: string
  showThinking?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  messageType: 'assistant',
  showThinking: false
})

// 统一消息对象，确保包含所有可选字段
const message = computed<Message>(() => {
  console.log('MessageBubble props:', props)
  console.log('MessageBubble message:', props.message)
  console.log('MessageBubble content:', props.content)
  
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
  console.log('isUser check:', message.value.role, props.messageType)
  return message.value.role === 'user' || props.messageType === 'user'
})

const isTool = computed(() => {
  console.log('isTool check:', message.value.role, props.messageType)
  return message.value.role === 'tool' || props.messageType === 'tool'
})

const formattedTime = computed(() => {
  const date = new Date(message.value.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})
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
      <!-- Thinking (collapsible) -->
      <div v-if="showThinking && message.thinking" class="thinking-section">
        <details>
          <summary class="thinking-toggle">
            <span class="thinking-icon">💭</span>
            思考过程
          </summary>
          <pre class="thinking-content">{{ message.thinking }}</pre>
        </details>
      </div>

      <!-- Main content -->
      <div class="content-text">{{ message.content || content }}</div>
      
      <!-- Debug info (hidden by default) -->
      <pre style="display:none">DEBUG: role={{message.role}}, content={{message.content?.substring(0,50)}}, type={{props.messageType}}</pre>

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
}

.thinking-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  width: fit-content;
}

.thinking-toggle:hover {
  color: var(--accent-blue);
}

.thinking-content {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: monospace;
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