<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useThemeStore } from '@/stores/theme'
import { useEventStore } from '@/stores/events'
import { useApprovalEvents } from '@/composables/useApprovalEvents'
import MessageBubble from '@/components/MessageBubble.vue'
import ToolApprovalCard from '@/components/ToolApprovalCard.vue'
import ToolResultCard from '@/components/ToolResultCard.vue'
import ChatInput from '@/components/ChatInput.vue'
import ThinkingPanel from '@/components/ThinkingPanel.vue'

const chatStore = useChatStore()
const themeStore = useThemeStore()
const eventStore = useEventStore()
const { setup: setupApprovalEvents } = useApprovalEvents()
const messagesContainer = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)

const handleSend = async (message: string) => {
  await chatStore.sendMessage(message)
  scrollToBottom()
}

const handleApprove = async (id: string) => {
  await chatStore.submitApproval(id, 'approved')
}

const handleReject = async (id: string) => {
  await chatStore.submitApproval(id, 'rejected')
}

onMounted(() => {
  chatStore.init()
  setupApprovalEvents()
  const sessionId = chatStore.currentConversationId || `session-${Date.now()}`
  eventStore.connect(sessionId)
})
</script>

<template>
  <div class="chat-view">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-left">
        <h1 class="app-title">Aloha AI Assistant</h1>
        <span v-if="chatStore.isSecurityEnabled" class="security-badge">
          安全模式
        </span>
      </div>
      <div class="header-right">
        <span class="model-name">{{ chatStore.currentModel }}</span>
        <button 
          class="theme-toggle-btn"
          @click="themeStore.toggleTheme"
          :title="themeStore.currentTheme === 'dark' ? '切换到亮色模式' : '切换到深色模式'"
        >
          {{ themeStore.currentTheme === 'dark' ? '◐' : '◑' }}
        </button>
      </div>
    </header>

    <!-- Messages Area -->
    <main class="chat-messages" ref="messagesContainer">
      <div class="messages-list">
        <!-- Welcome message -->
        <MessageBubble
          v-if="chatStore.messages.length === 0"
          message-type="welcome"
          content="你好！我是 Aloha AI 助手。有什么我可以帮助你的吗？"
        />

        <!-- Chat messages -->
        <template v-for="msg in chatStore.messages" :key="msg.id">
          <MessageBubble
            :message="msg"
            :show-thinking="true"
          />
        </template>

        <!-- Tool Approval Cards -->
        <ToolApprovalCard
          v-for="execution in chatStore.pendingApprovals"
          :key="execution.id"
          :execution="execution"
          @approve="handleApprove"
          @reject="handleReject"
        />

        <!-- Tool Results -->
        <ToolResultCard
          v-for="execution in chatStore.toolExecutions.filter(e => e.status !== 'pending')"
          :key="execution.id"
          :execution="execution"
        />

        <!-- Loading indicator -->
        <div v-if="chatStore.isLoading" class="loading-indicator">
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
        </div>
      </div>
    </main>

    <!-- Thinking Panel (expandable) -->
    <ThinkingPanel
      v-if="chatStore.currentThinking"
      :thinking="chatStore.currentThinking"
    />

    <!-- Input Area -->
    <footer class="chat-input-area">
      <ChatInput
        :disabled="chatStore.isLoading"
        @send="handleSend"
      />
    </footer>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.security-badge {
  padding: 2px 8px;
  font-size: 12px;
  background: rgba(210, 153, 34, 0.15);
  color: var(--accent-orange);
  border-radius: var(--radius-sm);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.model-name {
  font-size: 12px;
  color: var(--text-secondary);
}

.theme-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent-blue);
  font-size: 18px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-toggle-btn:hover {
  background: rgba(88, 166, 255, 0.25);
  transform: scale(1.1);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.loading-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  padding: var(--spacing-md);
}

.loading-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-blue);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input-area {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}
</style>