import { useEffect, useRef, useCallback, useState } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  path: string;
  onMessage?: (data: unknown) => void;
  enabled?: boolean;
  reconnectInterval?: number;
}

export function useWebSocket({ path, onMessage, enabled = true, reconnectInterval = 3000 }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (!enabled) return;

    const token = localStorage.getItem('access_token');
    const url = `${WS_URL}${path}${token ? `?token=${token}` : ''}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      reconnectTimer.current = setTimeout(connect, reconnectInterval);
    };

    ws.onerror = () => ws.close();
  }, [path, onMessage, enabled, reconnectInterval]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, send };
}
