"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Shield,
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Filter,
  Calendar,
  X,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Registros de Auditoria";
const LABEL_FILTER_ACTION = "Accion";
const LABEL_FILTER_RESOURCE_TYPE = "Tipo de Recurso";
const LABEL_FILTER_DATE_FROM = "Desde";
const LABEL_FILTER_DATE_TO = "Hasta";
const LABEL_ALL = "Todos";
const LABEL_LOADING = "Cargando registros...";
const LABEL_ERROR = "Error al cargar registros de auditoria";
const LABEL_EMPTY = "No se encontraron registros de auditoria";
const LABEL_EMPTY_FILTERED = "No hay registros que coincidan con los filtros";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_CLEAR_FILTERS = "Limpiar filtros";
const LABEL_COL_TIMESTAMP = "Fecha/Hora";
const LABEL_COL_ACTION = "Accion";
const LABEL_COL_RESOURCE = "Recurso";
const LABEL_COL_RESOURCE_ID = "ID Recurso";
const LABEL_COL_USER = "Usuario";
const LABEL_COL_IP = "IP";
const LABEL_FILTER_TITLE = "Filtros";

const PAGE_SIZE = 50;

const ACTION_OPTIONS: Record<string, string> = {
  create: "Crear",
  read: "Leer",
  update: "Actualizar",
  delete: "Eliminar",
  approve: "Aprobar",
  reject: "Rechazar",
  assign: "Asignar",
  export: "Exportar",
  generate_report: "Generar Reporte",
  login: "Inicio de Sesion",
  logout: "Cierre de Sesion",
  gdpr_erasure: "Borrado GDPR",
};

const ACTION_COLORS: Record<string, string> = {
  create: "bg-green-100 text-green-700",
  read: "bg-blue-100 text-blue-700",
  update: "bg-yellow-100 text-yellow-800",
  delete: "bg-red-100 text-red-700",
  approve: "bg-emerald-100 text-emerald-700",
  reject: "bg-red-100 text-red-700",
  assign: "bg-purple-100 text-purple-700",
  export: "bg-indigo-100 text-indigo-700",
  generate_report: "bg-indigo-100 text-indigo-700",
  login: "bg-teal-100 text-teal-700",
  logout: "bg-gray-100 text-gray-700",
  gdpr_erasure: "bg-orange-100 text-orange-700",
};

// --- Types ---
interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  request_id: string | null;
}

interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
}

interface Filters {
  action: string;
  resource_type: string;
  start_date: string;
  end_date: string;
}

const DEFAULT_FILTERS: Filters = {
  action: "",
  resource_type: "",
  start_date: "",
  end_date: "",
};

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString("es-PY", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function shortUserId(id: string): string {
  return id.slice(0, 8) + "...";
}

function hasActiveFilters(filters: Filters): boolean {
  return Object.values(filters).some((v) => v !== "");
}

export default function AuditLogsPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [pendingFilters, setPendingFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
    if (filters.action) params.set("action", filters.action);
    if (filters.resource_type) params.set("resource_type", filters.resource_type);
    if (filters.start_date) params.set("start_date", new Date(filters.start_date).toISOString());
    if (filters.end_date) params.set("end_date", new Date(filters.end_date).toISOString());

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
  }, [page, filters]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  function applyFilters() {
    setFilters({ ...pendingFilters });
    setPage(1);
    setShowFilters(false);
  }

  function clearFilters() {
    const reset = { ...DEFAULT_FILTERS };
    setPendingFilters(reset);
    setFilters(reset);
    setPage(1);
    setShowFilters(false);
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const startItem = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const endItem = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="rounded-lg p-2 text-warm-text-secondary hover:bg-warm-bg"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary-600" />
            <h1 className="text-xl font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
              hasActiveFilters(filters)
                ? "border-primary-300 bg-primary-50 text-primary-700"
                : "border-warm-border bg-warm-surface text-warm-text-secondary hover:bg-warm-bg"
            }`}
          >
            <Filter className="h-4 w-4" />
            {LABEL_FILTER_TITLE}
            {hasActiveFilters(filters) && (
              <span className="ml-1 rounded-full bg-primary-600 px-1.5 py-0.5 text-xs text-white">
                {Object.values(filters).filter((v) => v !== "").length}
              </span>
            )}
          </button>
          <button
            onClick={fetchEntries}
            className="rounded-lg border border-warm-border bg-warm-surface p-2 text-warm-text-secondary hover:bg-warm-bg"
            aria-label="Actualizar"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="rounded-xl border border-warm-border bg-warm-surface p-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Action filter */}
            <div>
              <label className="mb-1 block text-xs font-medium text-warm-text-secondary">
                {LABEL_FILTER_ACTION}
              </label>
              <select
                value={pendingFilters.action}
                onChange={(e) =>
                  setPendingFilters((f) => ({ ...f, action: e.target.value }))
                }
                className="w-full rounded-lg border border-warm-border bg-white px-3 py-2 text-sm text-warm-text-primary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
              >
                <option value="">{LABEL_ALL}</option>
                {Object.entries(ACTION_OPTIONS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Resource type filter */}
            <div>
              <label className="mb-1 block text-xs font-medium text-warm-text-secondary">
                {LABEL_FILTER_RESOURCE_TYPE}
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-text-tertiary" />
                <input
                  type="text"
                  value={pendingFilters.resource_type}
                  onChange={(e) =>
                    setPendingFilters((f) => ({
                      ...f,
                      resource_type: e.target.value,
                    }))
                  }
                  placeholder="ej. animal, donor"
                  className="w-full rounded-lg border border-warm-border bg-white py-2 pl-9 pr-3 text-sm text-warm-text-primary placeholder-warm-text-tertiary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                />
              </div>
            </div>

            {/* Start date */}
            <div>
              <label className="mb-1 block text-xs font-medium text-warm-text-secondary">
                {LABEL_FILTER_DATE_FROM}
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-text-tertiary" />
                <input
                  type="date"
                  value={pendingFilters.start_date}
                  onChange={(e) =>
                    setPendingFilters((f) => ({
                      ...f,
                      start_date: e.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-warm-border bg-white py-2 pl-9 pr-3 text-sm text-warm-text-primary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                />
              </div>
            </div>

            {/* End date */}
            <div>
              <label className="mb-1 block text-xs font-medium text-warm-text-secondary">
                {LABEL_FILTER_DATE_TO}
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-text-tertiary" />
                <input
                  type="date"
                  value={pendingFilters.end_date}
                  onChange={(e) =>
                    setPendingFilters((f) => ({
                      ...f,
                      end_date: e.target.value,
                    }))
                  }
                  className="w-full rounded-lg border border-warm-border bg-white py-2 pl-9 pr-3 text-sm text-warm-text-primary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
                />
              </div>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-end gap-2">
            {hasActiveFilters(filters) && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 rounded-lg px-3 py-2 text-sm text-warm-text-secondary hover:bg-warm-bg"
              >
                <X className="h-4 w-4" />
                {LABEL_CLEAR_FILTERS}
              </button>
            )}
            <button
              onClick={applyFilters}
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            >
              Aplicar filtros
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
            <p className="text-sm text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50 py-12">
          <Shield className="h-10 w-10 text-red-400" />
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

      {/* Empty state */}
      {!loading && !error && entries.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-warm-border bg-warm-surface py-16">
          <Shield className="h-10 w-10 text-warm-text-tertiary" />
          <p className="text-sm text-warm-text-secondary">
            {hasActiveFilters(filters) ? LABEL_EMPTY_FILTERED : LABEL_EMPTY}
          </p>
          {hasActiveFilters(filters) && (
            <button
              onClick={clearFilters}
              className="text-sm font-medium text-primary-600 hover:underline"
            >
              {LABEL_CLEAR_FILTERS}
            </button>
          )}
        </div>
      )}

      {/* Table */}
      {!loading && !error && entries.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-warm-border bg-warm-surface">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-warm-border bg-warm-bg">
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_TIMESTAMP}
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_ACTION}
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_RESOURCE}
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_RESOURCE_ID}
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_USER}
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                    {LABEL_COL_IP}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-warm-border">
                {entries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="hover:bg-warm-bg/50 transition-colors"
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-warm-text-secondary font-mono text-xs">
                      {formatTimestamp(entry.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                          ACTION_COLORS[entry.action] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {ACTION_OPTIONS[entry.action] ?? entry.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-warm-text-primary">
                      {entry.resource_type}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-warm-text-secondary">
                      {entry.resource_id
                        ? entry.resource_id.length > 16
                          ? entry.resource_id.slice(0, 12) + "..."
                          : entry.resource_id
                        : "—"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-warm-text-secondary">
                      {shortUserId(entry.user_id)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-warm-text-secondary">
                      {entry.ip_address ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-warm-border px-4 py-3">
            <p className="text-sm text-warm-text-secondary">
              {LABEL_SHOWING} {startItem}–{endItem} {LABEL_OF} {total}
            </p>
            <div className="flex items-center gap-2">
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
          </div>
        </div>
      )}
    </div>
  );
}
