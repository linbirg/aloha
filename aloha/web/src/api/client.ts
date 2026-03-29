const API_BASE_URL = '/api'

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

interface ChatResponse {
  content: string
  model?: string
}

interface ToolExecuteResponse {
  status: string
  result?: string
}

interface StatusResponse {
  connected: boolean
  model: string
  security_enabled: boolean
}

interface HistoryResponse {
  messages: unknown[]
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    const response = await fetch(url, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async chat(request: { message: string; stream?: boolean }): Promise<ChatResponse> {
    // Non-streaming chat request, returns JSON directly
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: request
    })
  }

  async executeTool(request: { tool_call_id: string; approved: boolean }): Promise<ToolExecuteResponse> {
    return this.request<ToolExecuteResponse>('/tool/execute', {
      method: 'POST',
      body: request
    })
  }

  async getStatus(): Promise<StatusResponse> {
    return this.request<StatusResponse>('/status')
  }

  async getHistory(): Promise<HistoryResponse> {
    return this.request<HistoryResponse>('/history')
  }
}

export const apiClient = new ApiClient()