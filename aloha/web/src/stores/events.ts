import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ConnectionState = 'connected' | 'reconnecting' | 'disconnected'

export const useEventStore = defineStore('events', () => {
  const connectionState = ref<ConnectionState>('disconnected')
  const sessionId = ref<string>('')
  const eventSource = ref<EventSource | null>(null)
  const reconnectAttempts = ref(0)
  const MAX_RECONNECT = 5
  const eventHandlers = new Map<string, Set<(data: any) => void>>()

  function connect(sid: string) {
    sessionId.value = sid
    reconnectAttempts.value = 0
    _createConnection()
  }

  function _createConnection() {
    if (eventSource.value) {
      eventSource.value.close()
    }

    eventSource.value = new EventSource(`/api/events?session_id=${sessionId.value}`)

    eventSource.value.onopen = () => {
      connectionState.value = 'connected'
      reconnectAttempts.value = 0
    }

    eventSource.value.onerror = () => {
      if (reconnectAttempts.value >= MAX_RECONNECT) {
        connectionState.value = 'disconnected'
        return
      }
      connectionState.value = 'reconnecting'
      reconnectAttempts.value++
      setTimeout(() => _createConnection(), 3000)
    }

    for (const [eventName, handlers] of eventHandlers.entries()) {
      eventSource.value.addEventListener(eventName, (e) => {
        const data = JSON.parse((e as MessageEvent).data)
        handlers.forEach((handler) => handler(data))
      })
    }
  }

  function addEventListener(event: string, handler: (data: any) => void) {
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, new Set())
    }
    eventHandlers.get(event)!.add(handler)

    if (eventSource.value) {
      eventSource.value.addEventListener(event, (e) => {
        const data = JSON.parse((e as MessageEvent).data)
        handler(data)
      })
    }
  }

  function removeEventListener(event: string, handler: (data: any) => void) {
    eventHandlers.get(event)?.delete(handler)
  }

  function disconnect() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    connectionState.value = 'disconnected'
    reconnectAttempts.value = 0
  }

  return {
    connectionState,
    sessionId,
    reconnectAttempts,
    connect,
    disconnect,
    addEventListener,
    removeEventListener,
  }
})
