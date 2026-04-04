// Type definitions for Aloha Web UI

// Message types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: number
  thinking?: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
}

// Tool execution
export interface ToolExecution {
  id: string
  tool_call_id: string
  tool_name: string
  arguments: Record<string, unknown>
  status: 'pending' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed'
  result?: string
  error?: string
  timestamp: number
  user_decision?: 'approve' | 'reject'
}

// API types
export interface ChatRequest {
  message: string
  stream?: boolean
}

export interface ChatResponse {
  content: string
  thinking?: string
  tool_calls?: ToolCall[]
  model?: string
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
}

export interface StreamChunk {
  type: 'content' | 'thinking' | 'tool_call' | 'done'
  delta: string
  tool_call?: ToolCall
}

// Permission types
export interface Permission {
  tool_name: string
  action: string
  risk_level: 'low' | 'medium' | 'high'
  details: {
    command?: string
    path?: string
    url?: string
    args?: Record<string, unknown>
  }
}

// Conversation types
export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

// Store types
export interface ChatState {
  messages: Message[]
  isLoading: boolean
  toolExecutions: ToolExecution[]
  error: string | null
}

export interface AppState {
  connected: boolean
  securityEnabled: boolean
  currentModel: string
}

export interface PendingApproval {
  id: string
  tool_name: string
  action: string
  arguments: Record<string, unknown>
  risk_level: string
  risk_color: string
  description: string
  resource: string
  timeout: number
  queue_position: number
  queue_total: number
  status: 'pending' | 'approved' | 'rejected' | 'timeout'
  approved_at?: number
  reason?: string
}