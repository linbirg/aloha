<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()

const editingId = ref<string | null>(null)
const editingTitle = ref('')

const formattedConversations = computed(() => {
  const convs = chatStore.conversations || []
  return convs.map(conv => ({
    ...conv,
    formattedDate: formatDate(conv.updatedAt)
  }))
})

function formatDate(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function handleNewChat() {
  chatStore.createConversation()
}

function handleSelectConversation(id: string) {
  if (editingId.value !== id) {
    chatStore.switchConversation(id)
  }
}

function handleDeleteConversation(id: string, event: Event) {
  event.stopPropagation()
  if (confirm('确定要删除这个对话吗？')) {
    chatStore.deleteConversation(id)
  }
}

function startEdit(id: string, currentTitle: string, event: Event) {
  event.stopPropagation()
  editingId.value = id
  editingTitle.value = currentTitle
}

function cancelEdit() {
  editingId.value = null
  editingTitle.value = ''
}

function saveEdit(id: string) {
  if (editingTitle.value.trim()) {
    chatStore.renameConversation(id, editingTitle.value.trim())
  }
  cancelEdit()
}

function handleEditKeydown(id: string, event: KeyboardEvent) {
  if (event.key === 'Enter') {
    saveEdit(id)
  } else if (event.key === 'Escape') {
    cancelEdit()
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">ALOHA</h1>
      <button class="new-chat-btn" @click="handleNewChat">
        <span class="btn-icon">+</span>
        新建对话
      </button>
    </div>
    
    <div class="conversations-list">
      <div 
        v-for="conv in formattedConversations" 
        :key="conv.id"
        class="conversation-item"
        :class="{ active: conv.id === chatStore.currentConversationId }"
        @click="handleSelectConversation(conv.id)"
      >
        <div class="conv-content">
          <template v-if="editingId === conv.id">
            <input 
              v-model="editingTitle"
              class="edit-input"
              @blur="saveEdit(conv.id)"
              @keydown="handleEditKeydown(conv.id, $event)"
              @click.stop
              ref="editInput"
              autofocus
            />
          </template>
          <template v-else>
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-meta">{{ conv.formattedDate }}</div>
          </template>
        </div>
        <div class="conv-actions">
          <button 
            v-if="editingId !== conv.id"
            class="action-btn edit-btn"
            @click="startEdit(conv.id, conv.title, $event)"
            title="重命名"
          >
            ✎
          </button>
          <button 
            class="action-btn delete-btn"
            @click="handleDeleteConversation(conv.id, $event)"
            title="删除对话"
          >
            ×
          </button>
        </div>
      </div>
      
      <div v-if="chatStore.conversations.length === 0" class="empty-state">
        <p>暂无对话记录</p>
        <p class="hint">点击上方按钮开始新对话</p>
      </div>
    </div>
    
    <div class="sidebar-footer">
      <div class="model-info">
        <span class="model-label">模型:</span>
        <span class="model-name">{{ chatStore.currentModel }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 280px;
  height: 100vh;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-blue);
  margin-bottom: var(--spacing-md);
  letter-spacing: 2px;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--accent-blue);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: var(--accent-blue-hover);
}

.btn-icon {
  font-size: 18px;
  font-weight: 600;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm);
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.conversation-item:hover {
  background: var(--bg-tertiary);
}

.conversation-item.active {
  background: var(--bg-tertiary);
  border: 1px solid var(--accent-blue);
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.edit-input {
  width: 100%;
  padding: 2px 4px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-primary);
  border: 1px solid var(--accent-blue);
  border-radius: var(--radius-sm);
  outline: none;
}

.conv-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conv-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px 6px;
  background: transparent;
  color: var(--text-muted);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s, color 0.2s;
}

.action-btn:hover {
  background: var(--bg-tertiary);
}

.delete-btn:hover {
  background: var(--accent-red);
  color: white;
}

.edit-btn:hover {
  background: var(--accent-blue);
  color: white;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-muted);
}

.empty-state .hint {
  font-size: 12px;
  margin-top: var(--spacing-sm);
}

.sidebar-footer {
  padding: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.model-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 12px;
}

.model-label {
  color: var(--text-muted);
}

.model-name {
  color: var(--text-secondary);
}
</style>