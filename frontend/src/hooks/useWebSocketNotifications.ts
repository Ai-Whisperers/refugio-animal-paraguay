/**
 * useWebSocketNotifications — React hook for real-time in-app notifications
 * via a WebSocket connection to the backend.
 *
 * Usage:
 *   const { latestNotification, isConnected } = useWebSocketNotifications(token);
 *
 * The hook:
 * - Opens a WebSocket connection to /ws/notifications?token=<jwt>
 * - Parses incoming "notification" events and surfaces them via latestNotification
 * - Responds to server "ping" events with "pong"
 * - Reconnects with exponential back-off on disconnect
 * - Cleans up on unmount
 *
 * The caller should merge latestNotification into their local notification state.
 */

import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RealtimeNotification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface WSMessage {
  event: "notification" | "ping";
  data?: RealtimeNotification;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const WS_BASE_URL =
  (process.env.NEXT_PUBLIC_WS_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace(/^http/, "ws")
    .replace(/\/$/, "");

const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;
const RECONNECT_FACTOR = 2;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useWebSocketNotifications(token: string | null): {
  latestNotification: RealtimeNotification | null;
  isConnected: boolean;
} {
  const [latestNotification, setLatestNotification] =
    useState<RealtimeNotification | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(RECONNECT_BASE_MS);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMounted = useRef(true);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimer.current !== null) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!token || !isMounted.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = `${WS_BASE_URL}/ws/notifications?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMounted.current) return;
      setIsConnected(true);
      reconnectDelay.current = RECONNECT_BASE_MS;
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      if (!isMounted.current) return;
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        if (msg.event === "ping") {
          // Respond with pong to maintain connection
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("pong");
          }
        } else if (msg.event === "notification" && msg.data) {
          setLatestNotification(msg.data);
        }
      } catch {
        // Malformed message — ignore
      }
    };

    ws.onclose = () => {
      if (!isMounted.current) return;
      setIsConnected(false);
      wsRef.current = null;

      // Reconnect with exponential back-off
      const delay = reconnectDelay.current;
      reconnectDelay.current = Math.min(delay * RECONNECT_FACTOR, RECONNECT_MAX_MS);

      reconnectTimer.current = setTimeout(() => {
        if (isMounted.current) connect();
      }, delay);
    };

    ws.onerror = () => {
      // onclose fires after onerror, so reconnect logic is there
      ws.close();
    };
  }, [token]);

  useEffect(() => {
    isMounted.current = true;
    connect();

    return () => {
      isMounted.current = false;
      clearReconnectTimer();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, clearReconnectTimer]);

  return { latestNotification, isConnected };
}
