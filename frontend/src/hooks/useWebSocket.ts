import { useState, useEffect, useRef, useCallback } from 'react';

interface UseWebSocketOptions {
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
}

export function useWebSocket<T>(urlPath: string, options: UseWebSocketOptions = {}) {
  const {
    reconnect = true,
    reconnectInterval = 1000,
    maxReconnectInterval = 10000,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const unmounted = useRef(false);

  const connect = useCallback(() => {
    if (unmounted.current) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isDev = Boolean((import.meta as any).env?.DEV);
    const customWs = (import.meta as any).env?.VITE_WS_HOST;
    const wsHost = customWs 
      ? customWs 
      : ((isDev && window.location.port === '3000') ? `${window.location.hostname}:8000` : window.location.host);
    const url = `${protocol}//${wsHost}${urlPath}`;

    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectAttempt.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(parsed);
      } catch (err) {
        // Not JSON or fallback for non-JSON ws
        setData(event.data as any);
      }
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      if (reconnect && !unmounted.current) {
        const timeout = Math.min(
          reconnectInterval * Math.pow(1.5, reconnectAttempt.current),
          maxReconnectInterval
        );
        setTimeout(connect, timeout);
        reconnectAttempt.current += 1;
      }
    };

    wsRef.current.onerror = (err) => {
      setError(err);
    };
  }, [urlPath, reconnect, reconnectInterval, maxReconnectInterval]);

  useEffect(() => {
    unmounted.current = false;
    connect();
    
    return () => {
      unmounted.current = true;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { data, isConnected, error };
}
