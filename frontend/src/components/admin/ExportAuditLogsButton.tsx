"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

// --- Labels (Spanish) ---
const LABEL_EXPORT_CSV = "Exportar CSV";
const LABEL_EXPORT_JSON = "Exportar JSON";
const LABEL_EXPORTING = "Exportando...";
const LABEL_ERROR = "Error al exportar";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ExportAuditLogsFilters {
  user_id?: string;
  action?: string;
  resource_type?: string;
  resource_id?: string;
  start_date?: string;
  end_date?: string;
}

interface ExportAuditLogsButtonProps {
  filters?: ExportAuditLogsFilters;
  format?: "csv" | "json";
  /** Optional label override */
  label?: string;
  className?: string;
}

/**
 * Button that triggers an authenticated download of audit logs in CSV or JSON.
 *
 * Uses the existing GET /admin/audit-logs/export?format=... endpoint.
 * Passes the current filters as query params so the export matches what is on screen.
 */
export default function ExportAuditLogsButton({
  filters = {},
  format = "csv",
  label,
  className = "",
}: ExportAuditLogsButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("format", format);
    if (filters.user_id) params.set("user_id", filters.user_id);
    if (filters.action) params.set("action", filters.action);
    if (filters.resource_type) params.set("resource_type", filters.resource_type);
    if (filters.resource_id) params.set("resource_id", filters.resource_id);
    if (filters.start_date)
      params.set("start_date", new Date(filters.start_date).toISOString());
    if (filters.end_date)
      params.set("end_date", new Date(filters.end_date).toISOString());

    try {
      const token = getAccessToken();
      const response = await fetch(
        `${API_BASE_URL}/api/v1/admin/audit-logs/export?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (!response.ok) {
        setError(LABEL_ERROR);
        return;
      }

      const blob = await response.blob();
      const filename =
        format === "json" ? "audit-logs.json" : "audit-logs.csv";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError(LABEL_ERROR);
    } finally {
      setLoading(false);
    }
  }

  const defaultLabel = format === "json" ? LABEL_EXPORT_JSON : LABEL_EXPORT_CSV;

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        onClick={handleExport}
        disabled={loading}
        className={`flex items-center gap-2 rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
        aria-label={label ?? defaultLabel}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        {loading ? LABEL_EXPORTING : (label ?? defaultLabel)}
      </button>
      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}
