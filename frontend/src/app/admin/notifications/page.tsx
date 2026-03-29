"use client";

import { useCallback, useEffect, useState } from "react";
import { Bell, BellOff, CheckCheck, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useGroupedNotifications } from "@/hooks/useGroupedNotifications";
import type { Notification } from "@/hooks/useGroupedNotifications";

/**
 * Grouped notifications page for admin staff.
 *
 * Shows all notifications grouped by type (e.g. "Solicitudes de adopcion",
 * "Donaciones recibidas") with collapsible threads. Each group shows an
 * unread badge. Staff can mark individual groups or all notifications as read.
 */

interface NotificationListResponse {
  items: Notification[];
  total: number;
}

interface MarkAllReadResponse {
  marked_count: number;
}

const PAGE_LIMIT = 100;

export default function AdminNotificationsPage() {
  const [allNotifications, setAllNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [isMarkingAll, setIsMarkingAll] = useState(false);

  const groups = useGroupedNotifications(allNotifications);

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetchAll = useCallback(async () => {
    setError(null);
    try {
      const data = await api.get<NotificationListResponse>(
        `/notifications?limit=${PAGE_LIMIT}&offset=0`,
        { requiresAuth: true }
      );
      setAllNotifications(data.items);
      // Auto-expand groups that have unread notifications
      const unreadTypes = new Set(
        data.items.filter((n) => !n.is_read).map((n) => n.notification_type)
      );
      setExpandedGroups(unreadTypes);
    } catch {
      setError("No se pudieron cargar las notificaciones. Intentalo de nuevo.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  const markRead = useCallback(async (id: string) => {
    try {
      await api.patch(`/notifications/${id}/read`, {}, { requiresAuth: true });
      setAllNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      // Non-critical
    }
  }, []);

  const markGroupRead = useCallback(
    async (notificationIds: string[]) => {
      await Promise.allSettled(notificationIds.map((id) => markRead(id)));
    },
    [markRead]
  );

  const markAllRead = useCallback(async () => {
    setIsMarkingAll(true);
    try {
      await api.post<MarkAllReadResponse>("/notifications/mark-all-read", {}, { requiresAuth: true });
      setAllNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      setError("Error al marcar todas como leidas.");
    } finally {
      setIsMarkingAll(false);
    }
  }, []);

  const toggleGroup = (type: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
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

  const totalUnread = allNotifications.filter((n) => !n.is_read).length;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notificaciones</h1>
          {totalUnread > 0 && (
            <p className="mt-0.5 text-sm text-gray-500">
              {totalUnread} notificacion{totalUnread !== 1 ? "es" : ""} sin leer
            </p>
          )}
        </div>
        {totalUnread > 0 && (
          <button
            type="button"
            onClick={markAllRead}
            disabled={isMarkingAll}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isMarkingAll ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <CheckCheck className="h-4 w-4" aria-hidden="true" />
            )}
            Marcar todo como leido
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : groups.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-200 bg-white py-16">
          <BellOff className="h-10 w-10 text-gray-300" aria-hidden="true" />
          <p className="text-sm text-gray-500">No tienes notificaciones</p>
        </div>
      ) : (
        /* Grouped notification threads */
        <div className="space-y-3" role="list" aria-label="Grupos de notificaciones">
          {groups.map((group) => {
            const isExpanded = expandedGroups.has(group.type);
            const unreadInGroup = group.notifications.filter((n) => !n.is_read);

            return (
              <div
                key={group.type}
                role="listitem"
                className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm"
              >
                {/* Group header */}
                <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.type)}
                    aria-expanded={isExpanded}
                    className="flex flex-1 items-center gap-3 text-left focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 flex-shrink-0 text-gray-400" aria-hidden="true" />
                    ) : (
                      <ChevronRight className="h-4 w-4 flex-shrink-0 text-gray-400" aria-hidden="true" />
                    )}
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${group.colorClass}`}>
                      {group.label}
                    </span>
                    <span className="text-xs text-gray-400">
                      {group.notifications.length} aviso{group.notifications.length !== 1 ? "s" : ""}
                    </span>
                  </button>

                  <div className="flex items-center gap-2">
                    {group.unreadCount > 0 && (
                      <>
                        <span
                          className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white"
                          aria-label={`${group.unreadCount} sin leer`}
                        >
                          {group.unreadCount}
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            markGroupRead(unreadInGroup.map((n) => n.id))
                          }
                          className="text-xs text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
                          aria-label={`Marcar grupo ${group.label} como leido`}
                        >
                          Leer
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Notification thread */}
                {isExpanded && (
                  <ul aria-label={`Notificaciones de ${group.label}`}>
                    {group.notifications.map((notification, index) => (
                      <li
                        key={notification.id}
                        className={`flex items-start gap-3 px-4 py-3 ${
                          index !== group.notifications.length - 1
                            ? "border-b border-gray-50"
                            : ""
                        } ${!notification.is_read ? "bg-primary/5" : ""}`}
                      >
                        {/* Unread dot */}
                        <div className="mt-1.5 flex-shrink-0">
                          {!notification.is_read ? (
                            <button
                              type="button"
                              onClick={() => markRead(notification.id)}
                              className="block h-2 w-2 rounded-full bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
                              aria-label={`Marcar '${notification.title}' como leida`}
                              title="Marcar como leida"
                            />
                          ) : (
                            <span className="block h-2 w-2" aria-hidden="true" />
                          )}
                        </div>

                        {/* Content */}
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 line-clamp-1">
                            {notification.title}
                          </p>
                          <p className="mt-0.5 text-xs text-gray-500 line-clamp-2">
                            {notification.message}
                          </p>
                        </div>

                        {/* Timestamp */}
                        <span className="flex-shrink-0 text-xs text-gray-400">
                          {formatRelativeTime(notification.created_at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Settings link */}
      <div className="text-center">
        <a
          href="/admin/settings/notifications"
          className="text-sm text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <Bell className="mr-1 inline-block h-3.5 w-3.5" aria-hidden="true" />
          Gestionar preferencias de notificaciones
        </a>
      </div>
    </div>
  );
}
