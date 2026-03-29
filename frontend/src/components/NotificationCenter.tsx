"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, BellOff, Check, CheckCheck, Loader2, Trash2, X } from "lucide-react";
import { api } from "@/lib/api";

/**
 * NotificationCenter — bell icon with dropdown showing recent in-app notifications.
 *
 * Features:
 * - Unread count badge on the bell icon
 * - Dropdown panel with recent notifications
 * - Mark individual or all notifications as read
 * - Delete individual notifications
 * - Auto-refreshes every 30 seconds
 * - Click outside to close
 * - Accessible: ARIA expanded, roles, keyboard navigation
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface NotificationListResponse {
  items: Notification[];
  total: number;
}

interface UnreadCountResponse {
  unread_count: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 30_000;
const MAX_DISPLAY = 20;

const TYPE_LABELS: Record<string, string> = {
  adoption_request_created: "Adopcion",
  adoption_status_changed: "Adopcion",
  donation_received: "Donacion",
  donation_refunded: "Devolucion",
  animal_intake_completed: "Animal",
  animal_status_changed: "Animal",
  system_alert: "Sistema",
  gdpr_request: "GDPR",
};

const TYPE_COLORS: Record<string, string> = {
  adoption_request_created: "bg-green-100 text-green-700",
  adoption_status_changed: "bg-blue-100 text-blue-700",
  donation_received: "bg-yellow-100 text-yellow-700",
  donation_refunded: "bg-orange-100 text-orange-700",
  animal_intake_completed: "bg-purple-100 text-purple-700",
  animal_status_changed: "bg-purple-100 text-purple-700",
  system_alert: "bg-red-100 text-red-700",
  gdpr_request: "bg-gray-100 text-gray-700",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRelativeTime(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Ahora mismo";
  if (minutes < 60) return `Hace ${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  return `Hace ${days}d`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.get<NotificationListResponse>(
        `/notifications?limit=${MAX_DISPLAY}&offset=0`,
        { requiresAuth: true }
      );
      setNotifications(data.items);
      setError(null);
    } catch {
      setError("No se pudieron cargar las notificaciones.");
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await api.get<UnreadCountResponse>("/notifications/unread-count", {
        requiresAuth: true,
      });
      setUnreadCount(data.unread_count);
    } catch {
      // Silently fail for the badge count
    }
  }, []);

  // Fetch unread count on mount and poll every 30s
  useEffect(() => {
    fetchUnreadCount();
    const timer = setInterval(fetchUnreadCount, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchUnreadCount]);

  // Fetch full list when panel opens
  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    fetchNotifications().finally(() => setIsLoading(false));
  }, [isOpen, fetchNotifications]);

  // ---------------------------------------------------------------------------
  // Click outside to close
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  // Close on ESC
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
        buttonRef.current?.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  const markRead = useCallback(async (id: string) => {
    try {
      await api.patch(`/notifications/${id}/read`, {}, { requiresAuth: true });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // Non-critical — ignore
    }
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await api.post("/notifications/mark-all-read", {}, { requiresAuth: true });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      setError("Error al marcar todas como leidas.");
    }
  }, []);

  const deleteNotification = useCallback(async (id: string) => {
    try {
      await api.delete(`/notifications/${id}`, { requiresAuth: true });
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // Non-critical — ignore
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  const hasUnread = unreadCount > 0;

  return (
    <div className="relative">
      {/* Bell button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        aria-label={
          hasUnread
            ? `${unreadCount} notificacion${unreadCount !== 1 ? "es" : ""} sin leer`
            : "Notificaciones"
        }
        aria-expanded={isOpen}
        aria-haspopup="true"
        className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        {hasUnread && (
          <span
            aria-hidden="true"
            className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div
          ref={panelRef}
          role="dialog"
          aria-label="Centro de notificaciones"
          className="absolute right-0 top-full z-40 mt-2 w-96 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xl"
        >
          {/* Panel header */}
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-900">Notificaciones</h2>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={markAllRead}
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-primary hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-primary"
                  title="Marcar todas como leidas"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  Leer todo
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Cerrar notificaciones"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="max-h-[420px] overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="px-4 py-8 text-center text-sm text-red-500">{error}</div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center">
                <BellOff className="h-8 w-8 text-gray-300" aria-hidden="true" />
                <p className="text-sm text-gray-500">No tienes notificaciones</p>
              </div>
            ) : (
              <ul role="list" aria-label="Lista de notificaciones">
                {notifications.map((notification) => (
                  <li
                    key={notification.id}
                    className={`group relative border-b border-gray-50 px-4 py-3 transition-colors hover:bg-gray-50 ${
                      !notification.is_read ? "bg-primary/5" : ""
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Unread indicator dot */}
                      <div className="mt-1.5 flex-shrink-0">
                        {!notification.is_read ? (
                          <span className="block h-2 w-2 rounded-full bg-primary" aria-label="Sin leer" />
                        ) : (
                          <span className="block h-2 w-2" aria-hidden="true" />
                        )}
                      </div>

                      {/* Notification content */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                              TYPE_COLORS[notification.notification_type] ??
                              "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {TYPE_LABELS[notification.notification_type] ?? "Aviso"}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(notification.created_at)}
                          </span>
                        </div>
                        <p className="mt-0.5 text-sm font-medium text-gray-900 line-clamp-1">
                          {notification.title}
                        </p>
                        <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">
                          {notification.message}
                        </p>
                      </div>

                      {/* Action buttons (visible on hover) */}
                      <div className="flex flex-shrink-0 flex-col gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        {!notification.is_read && (
                          <button
                            type="button"
                            onClick={() => markRead(notification.id)}
                            className="rounded p-1 text-gray-400 hover:bg-primary/10 hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary"
                            aria-label={`Marcar '${notification.title}' como leida`}
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => deleteNotification(notification.id)}
                          className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-400"
                          aria-label={`Eliminar '${notification.title}'`}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="border-t border-gray-100 px-4 py-2.5 text-center">
              <a
                href="/admin/settings/notifications"
                className="text-xs text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
              >
                Gestionar preferencias de notificaciones
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
