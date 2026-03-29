"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, ArrowLeft, FileText } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import ExportAuditLogsButton from "@/components/admin/ExportAuditLogsButton";
import type { ExportAuditLogsFilters } from "@/components/admin/ExportAuditLogsButton";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Exportar Registros de Auditoria";
const LABEL_BACK = "Volver a Auditoria";
const LABEL_FORMAT_TITLE = "Formato de Exportacion";
const LABEL_FILTERS_TITLE = "Filtros Opcionales";
const LABEL_ACTION = "Accion";
const LABEL_RESOURCE_TYPE = "Tipo de Recurso";
const LABEL_DATE_FROM = "Desde";
const LABEL_DATE_TO = "Hasta";
const LABEL_ALL = "Todos";
const LABEL_FORMAT_CSV_DESC = "Compatible con Excel y Google Sheets";
const LABEL_FORMAT_JSON_DESC = "Para procesamiento programatico";

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

export default function ExportAuditLogsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<ExportAuditLogsFilters>({});

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  function updateFilter<K extends keyof ExportAuditLogsFilters>(
    key: K,
    value: ExportAuditLogsFilters[K]
  ) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
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
          <Shield className="h-6 w-6 text-primary-600" />
          <h1 className="text-xl font-semibold text-warm-text-primary">
            {LABEL_PAGE_TITLE}
          </h1>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-warm-border bg-warm-surface p-6 space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-warm-text-tertiary" />
          <h2 className="text-sm font-medium text-warm-text-primary">
            {LABEL_FILTERS_TITLE}
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Action filter */}
          <div>
            <label
              htmlFor="export-action"
              className="mb-1 block text-xs font-medium text-warm-text-secondary"
            >
              {LABEL_ACTION}
            </label>
            <select
              id="export-action"
              value={filters.action ?? ""}
              onChange={(e) => updateFilter("action", e.target.value)}
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
            <label
              htmlFor="export-resource-type"
              className="mb-1 block text-xs font-medium text-warm-text-secondary"
            >
              {LABEL_RESOURCE_TYPE}
            </label>
            <input
              id="export-resource-type"
              type="text"
              value={filters.resource_type ?? ""}
              onChange={(e) => updateFilter("resource_type", e.target.value)}
              placeholder="ej. animal, donor"
              className="w-full rounded-lg border border-warm-border bg-white px-3 py-2 text-sm text-warm-text-primary placeholder-warm-text-tertiary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
            />
          </div>

          {/* Start date */}
          <div>
            <label
              htmlFor="export-start-date"
              className="mb-1 block text-xs font-medium text-warm-text-secondary"
            >
              {LABEL_DATE_FROM}
            </label>
            <input
              id="export-start-date"
              type="date"
              value={filters.start_date ?? ""}
              onChange={(e) => updateFilter("start_date", e.target.value)}
              className="w-full rounded-lg border border-warm-border bg-white px-3 py-2 text-sm text-warm-text-primary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
            />
          </div>

          {/* End date */}
          <div>
            <label
              htmlFor="export-end-date"
              className="mb-1 block text-xs font-medium text-warm-text-secondary"
            >
              {LABEL_DATE_TO}
            </label>
            <input
              id="export-end-date"
              type="date"
              value={filters.end_date ?? ""}
              onChange={(e) => updateFilter("end_date", e.target.value)}
              className="w-full rounded-lg border border-warm-border bg-white px-3 py-2 text-sm text-warm-text-primary focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
            />
          </div>
        </div>
      </div>

      {/* Export format cards */}
      <div className="rounded-xl border border-warm-border bg-warm-surface p-6 space-y-4">
        <h2 className="text-sm font-medium text-warm-text-primary">
          {LABEL_FORMAT_TITLE}
        </h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* CSV */}
          <div className="rounded-lg border border-warm-border p-4 space-y-3">
            <div>
              <p className="text-sm font-medium text-warm-text-primary">CSV</p>
              <p className="text-xs text-warm-text-secondary">
                {LABEL_FORMAT_CSV_DESC}
              </p>
            </div>
            <ExportAuditLogsButton filters={filters} format="csv" />
          </div>

          {/* JSON */}
          <div className="rounded-lg border border-warm-border p-4 space-y-3">
            <div>
              <p className="text-sm font-medium text-warm-text-primary">JSON</p>
              <p className="text-xs text-warm-text-secondary">
                {LABEL_FORMAT_JSON_DESC}
              </p>
            </div>
            <ExportAuditLogsButton filters={filters} format="json" />
          </div>
        </div>
      </div>
    </div>
  );
}
