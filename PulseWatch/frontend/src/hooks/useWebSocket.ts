import { useEffect, useRef, useCallback, useState } from 'react'

export interface WebSocketMessage {
  event: string
  [key: string]: any
}

export const useWebSocket = (url: string) => {
  const ws = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const messageHandlers = useRef<Map<string, (data: any) => void>>(new Map())

  useEffect(() => {
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        setLastMessage(message)

        const handler = messageHandlers.current.get(message.type)
        if (handler) {
          handler(message)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [url])

  const subscribe = useCallback((metric_name: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'subscribe',
        metric_name,
      }))
    }
  }, [])

  const unsubscribe = useCallback((metric_name: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'unsubscribe',
        metric_name,
      }))
    }
  }, [])

  const onMessage = useCallback((type: string, handler: (data: any) => void) => {
    messageHandlers.current.set(type, handler)

    return () => {
      messageHandlers.current.delete(type)
    }
  }, [])

  return {
    connected,
    lastMessage,
    subscribe,
    unsubscribe,
    onMessage,
  }
}
