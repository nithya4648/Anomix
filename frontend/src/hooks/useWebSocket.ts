import { useEffect, useRef, useCallback, useState } from 'react'

export interface WebSocketMessage {
  event: string
  [key: string]: any
}

export const useWebSocket = (url: string) => {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttempt = useRef(0)
  const disposed = useRef(false)
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const messageHandlers = useRef<Map<string, (data: any) => void>>(new Map())

  useEffect(() => {
    disposed.current = false
    reconnectAttempt.current = 0

    const clearReconnectTimer = () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    const closeSocket = () => {
      if (!ws.current) return
      ws.current.onclose = null
      ws.current.onerror = null
      ws.current.close()
      ws.current = null
    }

    const connect = (resetBackoff = false) => {
      if (disposed.current) return
      if (resetBackoff) reconnectAttempt.current = 0
      clearReconnectTimer()

      if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
        closeSocket()
      }

      const socket = new WebSocket(url)
      ws.current = socket

      socket.onopen = () => {
        if (socket !== ws.current) return
        reconnectAttempt.current = 0
        console.log('WebSocket connected')
        setConnected(true)
      }

      socket.onmessage = (event) => {
        if (socket !== ws.current) return
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

      socket.onerror = (error) => {
        if (socket !== ws.current) return
        console.error('WebSocket error:', error)
        setConnected(false)
      }

      socket.onclose = () => {
        if (socket !== ws.current || disposed.current) return
        setConnected(false)
        const delay = Math.min(1000 * 2 ** reconnectAttempt.current, 30000)
        reconnectAttempt.current += 1
        reconnectTimer.current = setTimeout(() => connect(), delay)
        console.log(`WebSocket disconnected; reconnecting in ${delay}ms`)
      }
    }

    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) connect(true)
    }

    window.addEventListener('pageshow', handlePageShow)
    connect()

    return () => {
      disposed.current = true
      clearReconnectTimer()
      window.removeEventListener('pageshow', handlePageShow)
      closeSocket()
      setConnected(false)
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
