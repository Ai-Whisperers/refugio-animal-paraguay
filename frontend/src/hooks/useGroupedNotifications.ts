/**
 * useGroupedNotifications — groups a flat notification list by type.
 *
 * Groups are sorted by most-recently-received notification within the group.
 * Each group contains a header label, color, the notifications, and an
 * unread count so the UI can show a badge per group.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationGroup {
  type: string;
  label: string;
  colorClass: string;
  notifications: Notification[];
  unreadCount: number;
  latestAt: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TYPE_META: Record<string, { label: string; colorClass: string }> = {
  adoption_request_created: {
    label: "Solicitudes de adopcion",
    colorClass: "bg-green-100 text-green-800",
  },
  adoption_status_changed: {
    label: "Estado de adopcion",
    colorClass: "bg-blue-100 text-blue-800",
  },
  donation_received: {
    label: "Donaciones recibidas",
    colorClass: "bg-yellow-100 text-yellow-800",
  },
  donation_refunded: {
    label: "Devoluciones",
    colorClass: "bg-orange-100 text-orange-800",
  },
  animal_intake_completed: {
    label: "Ingresos de animales",
    colorClass: "bg-purple-100 text-purple-800",
  },
  animal_status_changed: {
    label: "Cambios en animales",
    colorClass: "bg-indigo-100 text-indigo-800",
  },
  system_alert: {
    label: "Alertas del sistema",
    colorClass: "bg-red-100 text-red-800",
  },
  gdpr_request: {
    label: "Solicitudes GDPR",
    colorClass: "bg-gray-100 text-gray-800",
  },
};

const DEFAULT_META = { label: "Otros avisos", colorClass: "bg-gray-100 text-gray-700" };

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Groups a flat array of notifications by type, sorted by most recent activity.
 *
 * Pure computation — no side effects, no API calls.
 * The caller is responsible for fetching and providing the notification list.
 */
export function useGroupedNotifications(notifications: Notification[]): NotificationGroup[] {
  const groupMap = new Map<string, Notification[]>();

  for (const notification of notifications) {
    const key = notification.notification_type;
    if (!groupMap.has(key)) {
      groupMap.set(key, []);
    }
    groupMap.get(key)!.push(notification);
  }

  const groups: NotificationGroup[] = [];

  for (const [type, items] of groupMap) {
    // Sort items within the group newest-first
    const sorted = [...items].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    const unreadCount = sorted.filter((n) => !n.is_read).length;
    const latestAt = sorted[0]?.created_at ?? "";
    const meta = TYPE_META[type] ?? DEFAULT_META;

    groups.push({
      type,
      label: meta.label,
      colorClass: meta.colorClass,
      notifications: sorted,
      unreadCount,
      latestAt,
    });
  }

  // Sort groups by most recent notification across all types
  groups.sort(
    (a, b) => new Date(b.latestAt).getTime() - new Date(a.latestAt).getTime()
  );

  return groups;
}
