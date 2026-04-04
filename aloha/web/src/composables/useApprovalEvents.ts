import { useEventStore } from '@/stores/events'
import { useChatStore } from '@/stores/chat'

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

export function useApprovalEvents() {
  const eventStore = useEventStore()
  const chatStore = useChatStore()

  function showToast(message: string, type: 'success' | 'warning' | 'error' = 'success') {
    console.log(`[${type.toUpperCase()}] ${message}`)
  }

  function setup() {
    eventStore.addEventListener('approval_required', (data) => {
      const approval = data.approval as PendingApproval
      approval.queue_position = data.queue_position
      approval.queue_total = data.queue_total
      approval.status = 'pending'
      chatStore.pushApprovalQueue(approval)
    })

    eventStore.addEventListener('approval_completed', (data) => {
      chatStore.resolveApproval(data.approval_id, data.decision, data.approved_at)
      if (data.decision === 'approved') {
        showToast(`已批准`, 'success')
      } else {
        showToast(`已拒绝${data.reason ? `: ${data.reason}` : ''}`, 'warning')
      }
    })

    eventStore.addEventListener('approval_timeout', (data) => {
      chatStore.resolveApproval(data.approval_id, 'timeout', null)
      showToast('审批超时，已自动拒绝', 'warning')
    })

    eventStore.addEventListener('tool_result', (data) => {
      chatStore.updateToolResult(data.tool_call_id, data.success, data.content)
    })

    eventStore.addEventListener('thinking', (data) => {
      chatStore.setThinking(data.content)
    })

    eventStore.addEventListener('message', (data) => {
      chatStore.addMessageFromSSE(data.message)
      chatStore.setLoading(false)
    })

    eventStore.addEventListener('error', (data) => {
      chatStore.setError(data.message)
    })

    eventStore.addEventListener('heartbeat', () => {
      // heartbeat - no action needed
    })
  }

  return { setup }
}
