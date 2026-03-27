"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Scissors,
  RefreshCw,
  AlertCircle,
  ArrowLeft,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  BarChart3,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { SurgeryScheduleListResponse, SurgeryWithAnimal } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Estadisticas de Cirugias";
const LABEL_LOADING = "Cargando estadisticas...";
const LABEL_ERROR = "Error al cargar datos";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a cirugias";
const LABEL_REFRESH = "Actualizar";
const LABEL_TOTAL = "Total cirugias";
const LABEL_SUCCESS_RATE = "Tasa de exito";
const LABEL_COMPLICATIONS = "Con complicaciones";
const LABEL_BY_STATUS = "Por estado";
const LABEL_BY_TYPE = "Por tipo";
const LABEL_BY_OUTCOME = "Por resultado";
const LABEL_EMPTY = "Sin datos";
const LABEL_EMPTY_SUB = "No hay cirugias registradas aun";
const LABEL_COUNT = "Cantidad";
const LABEL_PCT = "Porcentaje";

const SURGERY_TYPE_LABELS: Record<string, string> = {
  spay: "Castracion (hembra)",
  neuter: "Castracion (macho)",
  mass_removal: "Extirpacion de masa",
  orthopedic: "Ortopedica",
  dental: "Dental",
  emergency: "Emergencia",
  biopsy: "Biopsia",
  eye: "Ocular",
  other: "Otra",
};

const STATUS_LABELS: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  complications: "Complicaciones",
};

const OUTCOME_LABELS: Record<string, string> = {
  successful: "Exitosa",
  complications: "Con complicaciones",
  incomplete: "Incompleta",
  failed: "Fallida",
};

const STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-400",
  in_progress: "bg-orange-400",
  completed: "bg-green-500",
  cancelled: "bg-gray-400",
  complications: "bg-red-500",
};

const OUTCOME_COLORS: Record<string, string> = {
  successful: "bg-green-500",
  complications: "bg-orange-400",
  incomplete: "bg-yellow-400",
  failed: "bg-red-500",
};

// --- Types ---
interface CountMap {
  [key: string]: number;
}

interface SurgeryStats {
  total: number;
  byStatus: CountMap;
  byType: CountMap;
  byOutcome: CountMap;
  completedCount: number;
  successfulCount: number;
  complicationsCount: number;
}

function computeStats(surgeries: SurgeryWithAnimal[]): SurgeryStats {
  const byStatus: CountMap = {};
  const byType: CountMap = {};
  const byOutcome: CountMap = {};
  let completedCount = 0;
  let successfulCount = 0;
  let complicationsCount = 0;

  for (const s of surgeries) {
    byStatus[s.surgery_status] = (byStatus[s.surgery_status] ?? 0) + 1;
    byType[s.surgery_type] = (byType[s.surgery_type] ?? 0) + 1;

    if (s.surgery_status === "completed" || s.surgery_status === "complications") {
      completedCount += 1;
    }
    if (s.surgery_status === "complications") {
      complicationsCount += 1;
    }
    if (s.outcome) {
      byOutcome[s.outcome] = (byOutcome[s.outcome] ?? 0) + 1;
      if (s.outcome === "successful") {
        successfulCount += 1;
      }
    }
  }

  return {
    total: surgeries.length,
    byStatus,
    byType,
    byOutcome,
    completedCount,
    successfulCount,
    complicationsCount,
  };
}

// --- Bar chart component ---
interface BarChartProps {
  data: CountMap;
  labels: Record<string, string>;
  colors: Record<string, string>;
  total: number;
}

function BarChartSection({ data, labels, colors, total }: BarChartProps) {
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (sorted.length === 0) {
    return (
      <p className="text-sm text-warm-text-tertiary">{LABEL_EMPTY}</p>
    );
  }
  const maxVal = sorted[0][1];

  return (
    <div className="space-y-3">
      {sorted.map(([key, count]) => {
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        const barPct = maxVal > 0 ? Math.round((count / maxVal) * 100) : 0;
        const color = colors[key] ?? "bg-primary-400";
        const label = labels[key] ?? key;

        return (
          <div key={key}>
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className="text-sm text-warm-text-secondary">{label}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-warm-text-tertiary">{pct}%</span>
                <span className="w-8 text-right text-sm font-semibold text-warm-text-primary">
                  {count}
                </span>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-warm-bg">
              <div
                className={`h-2 rounded-full transition-all ${color}`}
                style={{ width: `${barPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// --- Stat card component ---
interface StatCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  sub?: string;
}

function StatCard({ label, value, icon: Icon, iconBg, iconColor, sub }: StatCardProps) {
  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-warm-text-tertiary">{label}</p>
          <p className="mt-1 text-2xl font-bold text-warm-text-primary">{value}</p>
          {sub && <p className="mt-0.5 text-xs text-warm-text-secondary">{sub}</p>}
        </div>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
      </div>
    </div>
  );
}

// --- Main page ---

export default function SurgicalStatsDashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [surgeries, setSurgeries] = useState<SurgeryWithAnimal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchSurgeries = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<SurgeryScheduleListResponse>(
        "/surgeries?size=500"
      );
      setSurgeries(data.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isChecking) {
      fetchSurgeries();
    }
  }, [isChecking, fetchSurgeries]);

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  const stats = computeStats(surgeries);
  const successRate =
    stats.completedCount > 0
      ? Math.round((stats.successfulCount / stats.completedCount) * 100)
      : null;
  const complicationRate =
    stats.total > 0
      ? Math.round((stats.complicationsCount / stats.total) * 100)
      : null;

  return (
    <div className="mx-auto max-w-4xl">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/surgeries")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
            <BarChart3 className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            {!isLoading && (
              <p className="text-xs text-warm-text-tertiary">
                {stats.total} cirugias en total
              </p>
            )}
          </div>
        </div>

        <button
          onClick={fetchSurgeries}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          {LABEL_REFRESH}
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
          <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchSurgeries}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && stats.total === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-warm-border bg-warm-surface py-16">
          <Scissors className="h-10 w-10 text-warm-text-tertiary" />
          <p className="mt-3 text-sm font-medium text-warm-text-secondary">{LABEL_EMPTY}</p>
          <p className="mt-1 text-xs text-warm-text-tertiary">{LABEL_EMPTY_SUB}</p>
        </div>
      )}

      {/* Stats content */}
      {!isLoading && !error && stats.total > 0 && (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatCard
              label={LABEL_TOTAL}
              value={String(stats.total)}
              icon={Scissors}
              iconBg="bg-purple-100"
              iconColor="text-purple-600"
            />
            <StatCard
              label={LABEL_SUCCESS_RATE}
              value={successRate !== null ? `${successRate}%` : "N/A"}
              icon={CheckCircle2}
              iconBg="bg-green-100"
              iconColor="text-green-600"
              sub={
                stats.completedCount > 0
                  ? `${stats.successfulCount} de ${stats.completedCount} completadas`
                  : undefined
              }
            />
            <StatCard
              label={LABEL_COMPLICATIONS}
              value={complicationRate !== null ? `${complicationRate}%` : "N/A"}
              icon={stats.complicationsCount > 0 ? AlertTriangle : TrendingUp}
              iconBg={
                stats.complicationsCount > 0 ? "bg-red-100" : "bg-green-100"
              }
              iconColor={
                stats.complicationsCount > 0 ? "text-red-600" : "text-green-600"
              }
              sub={`${stats.complicationsCount} cirugias`}
            />
          </div>

          {/* By status and by type in 2 columns on larger screens */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* By status */}
            <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
              <div className="mb-4 flex items-center gap-2">
                <XCircle className="h-4 w-4 text-warm-text-tertiary" />
                <h2 className="text-sm font-semibold text-warm-text-primary">
                  {LABEL_BY_STATUS}
                </h2>
              </div>
              <BarChartSection
                data={stats.byStatus}
                labels={STATUS_LABELS}
                colors={STATUS_COLORS}
                total={stats.total}
              />
            </div>

            {/* By type */}
            <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
              <div className="mb-4 flex items-center gap-2">
                <Scissors className="h-4 w-4 text-warm-text-tertiary" />
                <h2 className="text-sm font-semibold text-warm-text-primary">
                  {LABEL_BY_TYPE}
                </h2>
              </div>
              <BarChartSection
                data={stats.byType}
                labels={SURGERY_TYPE_LABELS}
                colors={Object.fromEntries(
                  Object.keys(SURGERY_TYPE_LABELS).map((k, i) => {
                    const palette = [
                      "bg-primary-400",
                      "bg-primary-500",
                      "bg-primary-600",
                      "bg-indigo-400",
                      "bg-indigo-500",
                      "bg-violet-400",
                      "bg-violet-500",
                      "bg-purple-400",
                      "bg-purple-500",
                    ];
                    return [k, palette[i % palette.length]];
                  })
                )}
                total={stats.total}
              />
            </div>
          </div>

          {/* By outcome */}
          {Object.keys(stats.byOutcome).length > 0 && (
            <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
              <div className="mb-4 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-warm-text-tertiary" />
                <h2 className="text-sm font-semibold text-warm-text-primary">
                  {LABEL_BY_OUTCOME}
                </h2>
                <span className="text-xs text-warm-text-tertiary">
                  (cirugias con resultado registrado)
                </span>
              </div>
              <div className="grid grid-cols-1 gap-0 sm:grid-cols-2">
                <div className="sm:pr-4">
                  <BarChartSection
                    data={stats.byOutcome}
                    labels={OUTCOME_LABELS}
                    colors={OUTCOME_COLORS}
                    total={Object.values(stats.byOutcome).reduce(
                      (s, v) => s + v,
                      0
                    )}
                  />
                </div>
                {/* Outcome legend table */}
                <div className="mt-4 sm:mt-0 sm:border-l sm:border-warm-border sm:pl-4">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-warm-text-tertiary">
                        <th className="pb-1 text-left font-medium">{LABEL_BY_OUTCOME}</th>
                        <th className="pb-1 text-right font-medium">{LABEL_COUNT}</th>
                        <th className="pb-1 text-right font-medium">{LABEL_PCT}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(stats.byOutcome)
                        .sort((a, b) => b[1] - a[1])
                        .map(([key, count]) => {
                          const outcomeTotal = Object.values(
                            stats.byOutcome
                          ).reduce((s, v) => s + v, 0);
                          const pct =
                            outcomeTotal > 0
                              ? Math.round((count / outcomeTotal) * 100)
                              : 0;
                          return (
                            <tr key={key} className="border-t border-warm-border">
                              <td className="py-1.5 text-warm-text-secondary">
                                {OUTCOME_LABELS[key] ?? key}
                              </td>
                              <td className="py-1.5 text-right font-semibold text-warm-text-primary">
                                {count}
                              </td>
                              <td className="py-1.5 text-right text-warm-text-tertiary">
                                {pct}%
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
