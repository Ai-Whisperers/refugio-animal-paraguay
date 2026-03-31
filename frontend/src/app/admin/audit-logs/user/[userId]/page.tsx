"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  User,
  Clock,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { AuditLogEntry, AuditLogListResponse } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Actividad del Usuario";
const LABEL_BACK = "Volver a Auditoria";
const LABEL_LOADING = "Cargando actividad...";
const LABEL_ERROR = "Error al cargar actividad del usuario";
const LABEL_EMPTY = "Sin actividad registrada para este usuario";
const LABEL_RETRY = "Reintentar";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";

const ACTION_LABELS: Record<string, string> = {
  create: "Creo",
  read: "Leyo",
  update: "Actualizo",
  delete: "Elimino",
  approve: "Aprobo",
  reject: "Rechazo",
  assign: "Asigno",
  export: "Exporto",
  generate_report: "Genero reporte",
  login: "Inicio sesion",
  logout: "Cerro sesion",
  gdpr_erasure: "Ejecuto borrado GDPR",
};

const ACTION_ICONS: Record<string, string> = {
  create: "bg-green-500",
  read: "bg-blue-400",
  update: "bg-yellow-500",
  delete: "bg-red-500",
  approve: "bg-emerald-500",
  reject: "bg-red-500",
  assign: "bg-purple-500",
  export: "bg-indigo-500",
  generate_report: "bg-indigo-500",
  login: "bg-teal-500",
  logout: "bg-gray-400",
  gdpr_erasure: "bg-orange-500",
};

const PAGE_SIZE = 30;

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString("es-PY", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

function getActionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function getActionDotColor(action: string): string {
  return ACTION_ICONS[action] ?? "bg-gray-400";
}

interface TimelineEntryProps {
  entry: AuditLogEntry;
  isLast: boolean;
}

function TimelineEntry({ entry, isLast }: TimelineEntryProps) {
  return (
    <div className="relative flex gap-4 pb-6">
      {/* Vertical line */}
      {!isLast && (
        <div className="absolute left-[11px] top-6 h-full w-px bg-warm-border" />
      )}

      {/* Dot */}
      <div
        className={`relative z-10 mt-1 h-5 w-5 flex-shrink-0 rounded-full ${getActionDotColor(entry.action)} ring-2 ring-white`}
      />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="text-sm font-medium text-warm-text-primary">
            {getActionLabel(entry.action)}
          </span>
          <span className="text-sm text-warm-text-secondary">
            {entry.resource_type}
            {entry.resource_id && (
              <span className="ml-1 font-mono text-xs text-warm-text-tertiary">
                #{entry.resource_id.slice(0, 12)}
              </span>
            )}
          </span>
        </div>
        <div className="mt-1 flex items-center gap-2 text-xs text-warm-text-tertiary">
          <Clock className="h-3 w-3" />
          <span>{formatTimestamp(entry.timestamp)}</span>
          {entry.ip_address && (
            <>
              <span>·</span>
              <span className="font-mono">{entry.ip_address}</span>
            </>
          )}
        </div>
        {(entry.old_values || entry.new_values) && (
          <div className="mt-2 rounded-md border border-warm-border bg-warm-bg p-2 text-xs font-mono text-warm-text-secondary">
            {entry.new_values && (
              <div className="truncate text-green-700">
                + {JSON.stringify(entry.new_values).slice(0, 120)}
              </div>
            )}
            {entry.old_values && (
              <div className="truncate text-red-600">
                - {JSON.stringify(entry.old_values).slice(0, 120)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function UserActivityTimelinePage() {
  const router = useRouter();
  const params = useParams();
  const userId = params.userId as string;

  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  const fetchEntries = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("user_id", userId);
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));

    try {
      const data = await api.get<AuditLogListResponse>(
        `/api/v1/admin/audit-logs?${params.toString()}`
      );
      setEntries(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [userId, page]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const startItem = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const endItem = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.push("/admin/audit-logs")}
          className="rounded-lg p-2 text-warm-text-secondary hover:bg-warm-bg"
          aria-label={LABEL_BACK}
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-2">
          <User className="h-6 w-6 text-primary-600" />
          <div>
            <h1 className="text-xl font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            <p className="font-mono text-xs text-warm-text-tertiary">{userId}</p>
          </div>
        </div>
        <button
          onClick={fetchEntries}
          className="ml-auto rounded-lg border border-warm-border bg-warm-surface p-2 text-warm-text-secondary hover:bg-warm-bg"
          aria-label="Actualizar"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
            <p className="text-sm text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50 py-12">
          <User className="h-10 w-10 text-red-400" />
          <p className="text-sm font-medium text-red-700">{error}</p>
          <button
            onClick={fetchEntries}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            <RefreshCw className="h-4 w-4" />
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && entries.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-warm-border bg-warm-surface py-16">
          <Clock className="h-10 w-10 text-warm-text-tertiary" />
          <p className="text-sm text-warm-text-secondary">{LABEL_EMPTY}</p>
        </div>
      )}

      {/* Timeline */}
      {!loading && !error && entries.length > 0 && (
        <div className="rounded-xl border border-warm-border bg-warm-surface p-6">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-warm-text-secondary">
              {LABEL_SHOWING} {startItem}–{endItem} {LABEL_OF} {total}
            </p>
          </div>

          <div>
            {entries.map((entry, idx) => (
              <TimelineEntry
                key={entry.id}
                entry={entry}
                isLast={idx === entries.length - 1}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between border-t border-warm-border pt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
                {LABEL_PREVIOUS}
              </button>
              <span className="text-sm text-warm-text-secondary">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-40"
              >
                {LABEL_NEXT}
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
