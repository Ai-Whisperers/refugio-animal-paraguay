"use client";

import { useAdminSSE, type ActivityItem } from "@/hooks/useAdminSSE";
import {
  DollarSign,
  Heart,
  PawPrint,
  AlertTriangle,
  FilePlus,
  Calendar,
  XCircle,
  AlertCircle,
  CheckCircle,
  RotateCcw,
  PieChart,
  RefreshCw,
  Activity,
  Wifi,
  WifiOff,
  Trash2,
} from "lucide-react";

/** Spanish strings for the activity feed. */
const S = {
  title: "Actividad en Tiempo Real",
  connected: "Conectado",
  disconnected: "Desconectado",
  noActivity: "Sin actividad reciente",
  noActivityHint: "Las nuevas actividades apareceran aqui automaticamente.",
  clear: "Limpiar",
  justNow: "Ahora",
  minutesAgo: (n: number) => `hace ${n} min`,
  hoursAgo: (n: number) => `hace ${n}h`,
} as const;

/** Map icon hint strings to Lucide icon components. */
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  "dollar-sign": DollarSign,
  "rotate-ccw": RotateCcw,
  "pie-chart": PieChart,
  heart: Heart,
  "check-circle": CheckCircle,
  "paw-print": PawPrint,
  "refresh-cw": RefreshCw,
  "alert-triangle": AlertTriangle,
  "file-plus": FilePlus,
  "calendar-plus": Calendar,
  "calendar-check": Calendar,
  "alert-circle": AlertCircle,
  "x-circle": XCircle,
  activity: Activity,
};

/** Map category to background color for the icon badge. */
const CATEGORY_COLORS: Record<string, string> = {
  donation: "bg-green-100 text-green-600",
  adoption: "bg-pink-100 text-pink-600",
  animal: "bg-blue-100 text-blue-600",
  medical: "bg-amber-100 text-amber-600",
  volunteer: "bg-purple-100 text-purple-600",
  subscription: "bg-red-100 text-red-600",
  system: "bg-gray-100 text-gray-600",
};

function formatRelativeTime(timestamp: string): string {
  const now = Date.now();
  const eventTime = new Date(timestamp).getTime();
  const diffMs = now - eventTime;
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return S.justNow;
  if (diffMin < 60) return S.minutesAgo(diffMin);
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return S.hoursAgo(diffHours);
  return new Date(timestamp).toLocaleDateString("es-PY", {
    day: "numeric",
    month: "short",
  });
}

function ActivityItemRow({ item }: { item: ActivityItem }) {
  const IconComponent = ICON_MAP[item.icon] ?? Activity;
  const colorClass = CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.system;

  return (
    <div className="flex items-start gap-3 py-3 px-1 border-b border-gray-50 last:border-0 animate-fadeIn">
      <div className={`rounded-lg p-2 flex-shrink-0 ${colorClass}`}>
        <IconComponent className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-warm-text-primary leading-snug">
          {item.message}
        </p>
        <p className="text-xs text-warm-text-tertiary mt-0.5">
          {formatRelativeTime(item.timestamp)}
        </p>
      </div>
    </div>
  );
}

export default function ActivityFeed() {
  const { activities, connected, clearActivities } = useAdminSSE();

  return (
    <div className="rounded-xl border border-warm-border bg-warm-surface">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-warm-border">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-warm-text-secondary" />
          <h2 className="text-base font-semibold text-warm-text-primary">
            {S.title}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {activities.length > 0 && (
            <button
              onClick={clearActivities}
              className="text-xs text-warm-text-tertiary hover:text-warm-text-secondary transition-colors flex items-center gap-1"
              title={S.clear}
            >
              <Trash2 className="h-3.5 w-3.5" />
              {S.clear}
            </button>
          )}
          <span
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${
              connected
                ? "bg-green-50 text-green-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {connected ? (
              <Wifi className="h-3 w-3" />
            ) : (
              <WifiOff className="h-3 w-3" />
            )}
            {connected ? S.connected : S.disconnected}
          </span>
        </div>
      </div>

      {/* Feed */}
      <div className="px-4 py-2 max-h-96 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="py-8 text-center">
            <Activity className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-warm-text-tertiary">{S.noActivity}</p>
            <p className="text-xs text-warm-text-tertiary mt-1">
              {S.noActivityHint}
            </p>
          </div>
        ) : (
          activities.map((item) => (
            <ActivityItemRow key={item.id} item={item} />
          ))
        )}
      </div>
    </div>
  );
}
