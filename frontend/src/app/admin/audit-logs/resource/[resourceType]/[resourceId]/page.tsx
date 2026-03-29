"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  History,
  Clock,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  User,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { AuditLogEntry, AuditLogListResponse } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Historial de Cambios";
const LABEL_BACK = "Volver a Auditoria";
const LABEL_LOADING = "Cargando historial...";
const LABEL_ERROR = "Error al cargar historial";
const LABEL_EMPTY = "Sin cambios registrados para este recurso";
const LABEL_RETRY = "Reintentar";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";
const LABEL_OLD_VALUES = "Antes";
const LABEL_NEW_VALUES = "Despues";

const ACTION_LABELS: Record<string, string> = {
  create: "Creado",
  read: "Leido",
  update: "Actualizado",
  delete: "Eliminado",
  approve: "Aprobado",
  reject: "Rechazado",
  assign: "Asignado",
  export: "Exportado",
  generate_report: "Reporte generado",
  login: "Login",
  logout: "Logout",
  gdpr_erasure: "Borrado GDPR",
};

const ACTION_COLORS: Record<string, string> = {
  create: "bg-green-100 text-green-700",
  update: "bg-yellow-100 text-yellow-800",
  delete: "bg-red-100 text-red-700",
  approve: "bg-emerald-100 text-emerald-700",
  reject: "bg-red-100 text-red-700",
  assign: "bg-purple-100 text-purple-700",
  read: "bg-blue-100 text-blue-700",
  export: "bg-indigo-100 text-indigo-700",
};

const PAGE_SIZE = 20;

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

function DiffViewer({
  oldValues,
  newValues,
}: {
  oldValues: Record<string, unknown> | null;
  newValues: Record<string, unknown> | null;
}) {
  if (!oldValues && !newValues) return null;

  const allKeys = new Set([
    ...Object.keys(oldValues ?? {}),
    ...Object.keys(newValues ?? {}),
  ]);

  if (allKeys.size === 0) return null;

  const changedKeys = Array.from(allKeys).filter((key) => {
    const oldVal = oldValues?.[key];
    const newVal = newValues?.[key];
    return JSON.stringify(oldVal) !== JSON.stringify(newVal);
  });

  if (changedKeys.length === 0) return null;

  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-warm-border text-xs">
      <div className="grid grid-cols-2 divide-x divide-warm-border">
        <div className="bg-red-50 p-2">
          <p className="mb-1 font-medium text-red-700">{LABEL_OLD_VALUES}</p>
          {changedKeys.map((key) => (
            <div key={key} className="mb-0.5 font-mono text-red-600">
              <span className="font-medium text-warm-text-secondary">{key}:</span>{" "}
              {JSON.stringify(oldValues?.[key] ?? null)}
            </div>
          ))}
        </div>
        <div className="bg-green-50 p-2">
          <p className="mb-1 font-medium text-green-700">{LABEL_NEW_VALUES}</p>
          {changedKeys.map((key) => (
            <div key={key} className="mb-0.5 font-mono text-green-700">
              <span className="font-medium text-warm-text-secondary">{key}:</span>{" "}
              {JSON.stringify(newValues?.[key] ?? null)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ChangeEntry({
  entry,
  isLast,
}: {
  entry: AuditLogEntry;
  isLast: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasDiff = !!(entry.old_values || entry.new_values);

  return (
    <div className="relative flex gap-4 pb-6">
      {!isLast && (
        <div className="absolute left-[11px] top-6 h-full w-px bg-warm-border" />
      )}

      <div
        className={`relative z-10 mt-1 h-5 w-5 flex-shrink-0 rounded-full ring-2 ring-white ${
          entry.action === "delete"
            ? "bg-red-500"
            : entry.action === "create"
              ? "bg-green-500"
              : entry.action === "update"
                ? "bg-yellow-500"
                : "bg-gray-400"
        }`}
      />

      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              ACTION_COLORS[entry.action] ?? "bg-gray-100 text-gray-700"
            }`}
          >
            {ACTION_LABELS[entry.action] ?? entry.action}
          </span>
          <span className="flex items-center gap-1 text-xs text-warm-text-tertiary">
            <User className="h-3 w-3" />
            <span className="font-mono">{entry.user_id.slice(0, 8)}...</span>
          </span>
          {hasDiff && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-xs text-primary-600 hover:underline"
            >
              {expanded ? "Ocultar cambios" : "Ver cambios"}
            </button>
          )}
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
          {entry.request_id && (
            <>
              <span>·</span>
              <span className="font-mono text-[10px]">{entry.request_id}</span>
            </>
          )}
        </div>
        {expanded && hasDiff && (
          <DiffViewer
            oldValues={entry.old_values as Record<string, unknown> | null}
            newValues={entry.new_values as Record<string, unknown> | null}
          />
        )}
      </div>
    </div>
  );
}

export default function DataChangeHistoryPage() {
  const router = useRouter();
  const params = useParams();
  const resourceType = params.resourceType as string;
  const resourceId = params.resourceId as string;

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
    if (!resourceType || !resourceId) return;
    setLoading(true);
    setError(null);

    const queryParams = new URLSearchParams();
    queryParams.set("resource_type", resourceType);
    queryParams.set("resource_id", resourceId);
    queryParams.set("page", String(page));
    queryParams.set("page_size", String(PAGE_SIZE));

    try {
      const data = await api.get<AuditLogListResponse>(
        `/api/v1/admin/audit-logs?${queryParams.toString()}`
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
  }, [resourceType, resourceId, page]);

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
          <History className="h-6 w-6 text-primary-600" />
          <div>
            <h1 className="text-xl font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            <p className="text-xs text-warm-text-tertiary">
              <span className="font-medium">{resourceType}</span>
              <span className="mx-1">·</span>
              <span className="font-mono">{resourceId}</span>
            </p>
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
          <History className="h-10 w-10 text-red-400" />
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
          <History className="h-10 w-10 text-warm-text-tertiary" />
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
              <ChangeEntry
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
