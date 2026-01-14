import { useState, useEffect, useRef, useCallback } from 'react';
import type { StateUpdate } from '../types/state';
import { parseStateUpdate } from '../types/state';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketResult {
  state: StateUpdate | null;
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  error: Error | null;
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketResult {
  const { reconnectInterval = 2000, maxReconnectAttempts = 10 } = options;

  const [state, setState] = useState<StateUpdate | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      return;
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current) {
        reconnectAttemptsRef.current += 1;
        // Reconnect will be triggered by connect function
        setConnectionStatus('connecting');
      }
    }, reconnectInterval);
  }, [reconnectInterval, maxReconnectAttempts]);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      setConnectionStatus('connecting');
      setError(null);

      ws.onopen = () => {
        if (mountedRef.current) {
          setConnectionStatus('connected');
          reconnectAttemptsRef.current = 0;
        }
      };

      ws.onmessage = (event: MessageEvent) => {
        if (mountedRef.current) {
          const parsed = parseStateUpdate(event.data as string);
          if (parsed) {
            setState(parsed);
          }
        }
      };

      ws.onclose = () => {
        if (mountedRef.current) {
          setConnectionStatus('disconnected');
          scheduleReconnect();
        }
      };

      ws.onerror = () => {
        if (mountedRef.current) {
          setError(new Error('WebSocket error'));
          setConnectionStatus('error');
        }
      };
    } catch (e) {
      if (mountedRef.current) {
        setError(e instanceof Error ? e : new Error('Connection failed'));
        setConnectionStatus('error');
      }
    }
  }, [url, scheduleReconnect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Handle reconnection when status becomes 'connecting' after disconnect
  useEffect(() => {
    if (connectionStatus === 'connecting' && !wsRef.current) {
      connect();
    }
  }, [connectionStatus, connect]);

  return {
    state,
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    error,
  };
}
