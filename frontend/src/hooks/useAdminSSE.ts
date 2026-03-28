/**
 * React hook for connecting to the admin SSE activity feed.
 *
 * Opens an EventSource to GET /api/admin/sse, listens for "activity"
 * events, and maintains a bounded list of recent activity items.
 * Automatically reconnects on connection loss with exponential backoff.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { getAccessToken } from "@/lib/auth";

/** Shape of an activity item received via SSE. */
export interface ActivityItem {
  id: string;
  type: string;
  event_type: string;
  category: string;
  icon: string;
  message: string;
  aggregate_id: string | null;
  aggregate_type: string | null;
  actor_id: string | null;
  timestamp: string;
}

/** Maximum number of activity items to keep in state. */
const MAX_ITEMS = 50;

/** Initial reconnect delay in milliseconds. */
const INITIAL_RECONNECT_DELAY_MS = 2000;

/** Maximum reconnect delay in milliseconds. */
const MAX_RECONNECT_DELAY_MS = 30000;

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface UseAdminSSEResult {
  /** List of recent activity items, newest first. */
  activities: ActivityItem[];
  /** Whether the SSE connection is currently open. */
  connected: boolean;
  /** Clear all activity items. */
  clearActivities: () => void;
}

export function useAdminSSE(): UseAdminSSEResult {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY_MS);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearActivities = useCallback(() => {
    setActivities([]);
  }, []);

  useEffect(() => {
    let cancelled = false;

    function connect() {
      if (cancelled) return;

      const token = getAccessToken();
      if (!token) {
        // No auth token — retry later
        reconnectTimerRef.current = setTimeout(connect, INITIAL_RECONNECT_DELAY_MS);
        return;
      }

      // EventSource doesn't support custom headers, so pass token as query param
      const url = `${API_BASE_URL}/api/admin/sse?token=${encodeURIComponent(token)}`;
      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        if (cancelled) return;
        setConnected(true);
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY_MS;
      };

      es.addEventListener("activity", (event: MessageEvent) => {
        if (cancelled) return;
        try {
          const data = JSON.parse(event.data) as Omit<ActivityItem, "id">;
          const item: ActivityItem = {
            ...data,
            id: event.lastEventId || crypto.randomUUID(),
          };
          setActivities((prev) => [item, ...prev].slice(0, MAX_ITEMS));
        } catch {
          // Ignore malformed messages
        }
      });

      es.onerror = () => {
        if (cancelled) return;
        setConnected(false);
        es.close();
        eventSourceRef.current = null;

        // Exponential backoff reconnect
        const delay = reconnectDelayRef.current;
        reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY_MS);
        reconnectTimerRef.current = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return { activities, connected, clearActivities };
}
