<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  disabled?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'send', message: string): void
}>()

const inputValue = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const handleSubmit = () => {
  const message = inputValue.value.trim()
  if (message && !props.disabled) {
    emit('send', message)
    inputValue.value = ''
    // Reset textarea height
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  // Shift + Enter = new line
  // Enter = submit (without Shift)
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}

const handleInput = () => {
  // Auto-resize textarea
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 150)}px`
  }
}

// Expose focus method
defineExpose({
  focus: () => textareaRef.value?.focus()
})
</script>

<template>
  <div class="chat-input-wrapper">
    <div class="input-container">
      <textarea
        ref="textareaRef"
        v-model="inputValue"
        class="chat-textarea"
        placeholder="输入消息... (Shift+Enter 换行, Enter 发送)"
        :disabled="disabled"
        rows="1"
        @keydown="handleKeydown"
        @input="handleInput"
      ></textarea>
      <button 
        class="send-button"
        :disabled="disabled || !inputValue.trim()"
        @click="handleSubmit"
      >
        <span class="send-icon">➤</span>
      </button>
    </div>
    <div class="input-hint">
      <span>💡 按 Enter 发送，Shift + Enter 换行</span>
    </div>
  </div>
</template>

<style scoped>
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-width: 800px;
  margin: 0 auto;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-sm);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-sm);
  transition: border-color var(--transition-fast);
}

.input-container:focus-within {
  border-color: var(--accent-blue);
}

.chat-textarea {
  flex: 1;
  min-height: 24px;
  max-height: 150px;
  padding: var(--spacing-sm);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
  resize: none;
}

.chat-textarea::placeholder {
  color: var(--text-muted);
}

.chat-textarea:disabled {
  opacity: 0.5;
}

.send-button {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-blue);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.send-button:hover:not(:disabled) {
  background: #4090e0;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  font-size: 16px;
  color: white;
}

.input-hint {
  display: flex;
  justify-content: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>