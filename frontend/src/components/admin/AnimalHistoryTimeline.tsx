"use client";

import { useEffect, useState, useCallback } from "react";
import { Clock, RefreshCw, AlertCircle } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import { STATUS_LABELS, STATUS_COLORS } from "@/lib/animal-status";
import type { AuditLogEntry, AuditLogListResponse, AnimalStatus } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_TITLE = "Historial";
const LABEL_LOADING = "Cargando historial...";
const LABEL_ERROR = "Error al cargar historial";
const LABEL_RETRY = "Reintentar";
const LABEL_EMPTY = "Sin eventos registrados";

// Action label map for common audit actions
const ACTION_LABELS: Record<string, string> = {
  create: "Creado",
  update: "Actualizado",
  delete: "Eliminado",
  status_change: "Cambio de estado",
  photo_add: "Foto agregada",
  photo_delete: "Foto eliminada",
};

interface AnimalHistoryTimelineProps {
  animalId: string;
}

function formatTimestamp(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getActionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function renderStatusChange(
  oldValues: Record<string, unknown> | null,
  newValues: Record<string, unknown> | null
): React.ReactNode {
  const oldStatus = oldValues?.status as AnimalStatus | undefined;
  const newStatus = newValues?.status as AnimalStatus | undefined;

  if (!oldStatus && !newStatus) return null;

  return (
    <div className="mt-1 flex items-center gap-2 text-xs">
      {oldStatus && (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 font-medium ${STATUS_COLORS[oldStatus] ?? "bg-gray-100 text-gray-600"}`}
        >
          {STATUS_LABELS[oldStatus] ?? oldStatus}
        </span>
      )}
      {oldStatus && newStatus && (
        <span className="text-warm-text-tertiary">&rarr;</span>
      )}
      {newStatus && (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 font-medium ${STATUS_COLORS[newStatus] ?? "bg-gray-100 text-gray-600"}`}
        >
          {STATUS_LABELS[newStatus] ?? newStatus}
        </span>
      )}
    </div>
  );
}

function renderChangeSummary(entry: AuditLogEntry): React.ReactNode {
  // Special handling for status changes
  if (
    entry.action === "update" &&
    entry.new_values &&
    "status" in entry.new_values
  ) {
    return renderStatusChange(entry.old_values, entry.new_values);
  }

  // For other updates, show changed fields
  if (entry.action === "update" && entry.new_values) {
    const changedFields = Object.keys(entry.new_values).filter(
      (key) => key !== "updated_at"
    );
    if (changedFields.length > 0) {
      return (
        <p className="mt-1 text-xs text-warm-text-tertiary">
          Campos: {changedFields.join(", ")}
        </p>
      );
    }
  }

  return null;
}

export default function AnimalHistoryTimeline({
  animalId,
}: AnimalHistoryTimelineProps) {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        resource_type: "animal",
        resource_id: animalId,
        page_size: "50",
      });
      const data = await api.get<AuditLogListResponse>(
        `/admin/audit-logs?${params.toString()}`
      );
      setEntries(data.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [animalId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
          <Clock className="h-5 w-5 text-primary-500" />
          {LABEL_TITLE}
        </h2>
        <div className="flex items-center justify-center py-6">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin text-primary-400" />
          <p className="text-sm text-warm-text-tertiary">{LABEL_LOADING}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
          <Clock className="h-5 w-5 text-primary-500" />
          {LABEL_TITLE}
        </h2>
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchHistory}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
      <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
        <Clock className="h-5 w-5 text-primary-500" />
        {LABEL_TITLE}
      </h2>

      {entries.length === 0 ? (
        <p className="text-center text-sm text-warm-text-tertiary py-4">
          {LABEL_EMPTY}
        </p>
      ) : (
        <div className="relative space-y-0">
          {/* Timeline line */}
          <div className="absolute left-3 top-2 bottom-2 w-px bg-warm-border" />

          {entries.map((entry, index) => (
            <div
              key={entry.id}
              className="relative flex gap-4 pb-4 last:pb-0"
            >
              {/* Timeline dot */}
              <div
                className={`relative z-10 mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full border-2 ${
                  index === 0
                    ? "border-primary-500 bg-primary-500"
                    : "border-warm-border bg-warm-surface"
                }`}
                style={{ marginLeft: "5px" }}
              />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-sm font-medium text-warm-text-primary">
                    {getActionLabel(entry.action)}
                  </p>
                  <time className="flex-shrink-0 text-xs text-warm-text-tertiary">
                    {formatTimestamp(entry.timestamp)}
                  </time>
                </div>
                {renderChangeSummary(entry)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
