import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, ToolExecution, Conversation, PendingApproval } from '@/types'
import { apiClient } from '@/api/client'

const STORAGE_KEY = 'aloha_conversations'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const toolExecutions = ref<ToolExecution[]>([])
  const currentThinking = ref<string>('')
  const error = ref<string | null>(null)
  const currentModel = ref('MiniMax-M2')
  const isSecurityEnabled = ref(true)
  const ssePendingApprovals = ref<PendingApproval[]>([])
  
  // Conversation management
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)

  // Computed
  const pendingApprovals = computed(() => 
    toolExecutions.value.filter(e => e.status === 'pending')
  )

  const recentMessages = computed(() => 
    messages.value.slice(-50)
  )

  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value)
  )

  // Load conversations from localStorage
  function loadConversations() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        conversations.value = parsed.conversations || []
        currentConversationId.value = parsed.currentId || null
        
        // Load messages for current conversation
        if (currentConversationId.value) {
          const conv = conversations.value.find(c => c.id === currentConversationId.value)
          if (conv) {
            messages.value = conv.messages
          }
        }
      }
    } catch (e) {
      // Ignore localStorage errors silently
    }
  }

  // Save conversations to localStorage
  function saveConversations() {
    try {
      // Update current conversation with messages
      if (currentConversationId.value) {
        const idx = conversations.value.findIndex(c => c.id === currentConversationId.value)
        if (idx >= 0) {
          conversations.value[idx].messages = messages.value
          conversations.value[idx].updatedAt = Date.now()
        }
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        conversations: conversations.value,
        currentId: currentConversationId.value
      }))
    } catch (e) {
      // Ignore localStorage errors silently
    }
  }

  // Initialize store
  function init() {
    loadConversations()
  }

  // Create new conversation
  function createConversation(title?: string) {
    const id = generateId()
    const conv: Conversation = {
      id,
      title: title || `对话 ${conversations.value.length + 1}`,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    conversations.value.unshift(conv)
    currentConversationId.value = id
    messages.value = []
    saveConversations()
    return id
  }

  // Switch conversation
  function switchConversation(id: string) {
    // Save current conversation first
    saveConversations()
    
    currentConversationId.value = id
    const conv = conversations.value.find(c => c.id === id)
    if (conv) {
      messages.value = conv.messages || []
    }
    saveConversations()
  }

  // Delete conversation
  function deleteConversation(id: string) {
    const idx = conversations.value.findIndex(c => c.id === id)
    if (idx >= 0) {
      conversations.value.splice(idx, 1)
      if (currentConversationId.value === id) {
        currentConversationId.value = conversations.value[0]?.id || null
        messages.value = conversations.value[0]?.messages || []
      }
      saveConversations()
    }
  }

  // Rename conversation
  function renameConversation(id: string, newTitle: string) {
    const conv = conversations.value.find(c => c.id === id)
    if (conv && newTitle.trim()) {
      conv.title = newTitle.trim()
      conv.updatedAt = Date.now()
      saveConversations()
    }
  }

  async function sendMessage(content: string) {
    if (!content.trim() || isLoading.value) return

    // Auto-create conversation if none exists
    if (!currentConversationId.value) {
      createConversation()
    }

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: Date.now()
    }

    messages.value.push(userMessage)
    isLoading.value = true
    error.value = null
    currentThinking.value = ''

    try {
      const response = await apiClient.chat({
        message: content.trim(),
        stream: false
      })

      // Create assistant message with response
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.content || 'No response',
        timestamp: Date.now(),
        thinking: response.thinking || undefined
      }
      messages.value.push(assistantMessage)

      // Update currentModel from API response
      if (response.model) {
        currentModel.value = response.model
      }
      
      // Update conversation title from first exchange
      if (currentConversationId.value && messages.value.length === 2) {
        const conv = conversations.value.find(c => c.id === currentConversationId.value)
        if (conv && conv.title.startsWith('对话')) {
          const firstUserMsg = messages.value[0]?.content || ''
          conv.title = firstUserMsg.substring(0, 30) + (firstUserMsg.length > 30 ? '...' : '')
        }
      }
      
      saveConversations()
    } catch (err) {
      // Silent error handling for better UX
    } finally {
      isLoading.value = false
    }
  }

  async function approveTool(executionId: string) {
    const execution = toolExecutions.value.find(e => e.id === executionId)
    if (!execution) return

    execution.status = 'approved'
    execution.user_decision = 'approve'

    try {
      const result = await apiClient.executeTool({
        tool_call_id: execution.tool_call_id,
        approved: true
      })

      execution.status = 'completed'
      execution.result = result?.result || result?.status || 'OK'

      // Add result as tool message
      const toolMessage: Message = {
        id: generateId(),
        role: 'tool',
        content: execution.result,
        tool_call_id: execution.tool_call_id,
        timestamp: Date.now()
      }
      messages.value.push(toolMessage)
      saveConversations()
    } catch (err) {
      execution.status = 'failed'
      execution.error = err instanceof Error ? err.message : '执行失败'
    }
  }

  async function rejectTool(executionId: string) {
    const execution = toolExecutions.value.find(e => e.id === executionId)
    if (!execution) return

    execution.status = 'rejected'
    execution.user_decision = 'reject'

    // Notify backend
    await apiClient.executeTool({
      tool_call_id: execution.tool_call_id,
      approved: false
    })
    saveConversations()
  }

  function clearMessages() {
    messages.value = []
    toolExecutions.value = []
    currentThinking.value = ''
    error.value = null
    saveConversations()
  }

  function pushApprovalQueue(approval: PendingApproval, position: number, total: number) {
    approval.queue_position = position
    approval.queue_total = total
    approval.status = 'pending'
    ssePendingApprovals.value.push(approval)
  }

  function resolveApproval(id: string, decision: string, approvedAt: number | null) {
    const idx = ssePendingApprovals.value.findIndex((a) => a.id === id)
    if (idx !== -1) {
      ssePendingApprovals.value[idx].status = decision as PendingApproval['status']
      ssePendingApprovals.value[idx].approved_at = approvedAt ?? undefined
      ssePendingApprovals.value.splice(idx, 1)
    }
  }

  function updateToolResult(toolCallId: string, success: boolean, content: string) {
    const execution = toolExecutions.value.find((e) => e.tool_call_id === toolCallId)
    if (execution) {
      execution.status = success ? 'completed' : 'failed'
      execution.result = content
    }
  }

  function addMessageFromSSE(message: Message) {
    messages.value.push(message)
    saveConversations()
  }

  async function submitApproval(id: string, decision: 'approved' | 'rejected', reason?: string) {
    try {
      await fetch(`/api/approvals/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason }),
      })
    } catch (err) {
      console.error('Failed to submit approval:', err)
    }
  }

  return {
    // State
    messages,
    isLoading,
    toolExecutions,
    currentThinking,
    error,
    currentModel,
    isSecurityEnabled,
    conversations,
    currentConversationId,
    // Computed
    pendingApprovals,
    ssePendingApprovals,
    recentMessages,
    currentConversation,
    // Actions
    init,
    createConversation,
    switchConversation,
    deleteConversation,
    renameConversation,
    sendMessage,
    approveTool,
    rejectTool,
    clearMessages,
    loadConversations,
    saveConversations,
    pushApprovalQueue,
    resolveApproval,
    updateToolResult,
    addMessageFromSSE,
    submitApproval
  }
})

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}