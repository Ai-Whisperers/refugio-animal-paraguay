"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  DollarSign,
  Download,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  UserCheck,
  UserX,
  Users,
} from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CurrencyTotal {
  currency: string;
  donation_count: number;
  total_amount_cents: number;
  total_amount_display: string;
}

interface SummaryRow {
  period_label: string;
  period_start: string;
  dimension_value: string;
  currency: string;
  donation_count: number;
  total_amount_cents: number;
}

interface DonationSummary {
  generated_at: string;
  grouping: string;
  total_donations: number;
  currency_totals: CurrencyTotal[];
  rows: SummaryRow[];
}

interface DonorSegments {
  new: number;
  active: number;
  at_risk: number;
  lapsed: number;
  churned: number;
  total: number;
}

interface RetentionMetrics {
  generated_at: string;
  period_days: number;
  retained_donors: number;
  churned_donors: number;
  new_donors: number;
  retention_rate_pct: number;
  churn_rate_pct: number;
  segments: DonorSegments;
}

interface CohortRow {
  cohort_month: string;
  cohort_size: number;
  retained_month_1: number;
  retained_month_3: number;
  retained_month_6: number;
  retention_pct_1: number;
  retention_pct_3: number;
  retention_pct_6: number;
}

interface CohortData {
  generated_at: string;
  lookback_months: number;
  cohorts: CohortRow[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PERIOD_OPTIONS = [
  { label: "30 dias", days: 30 },
  { label: "90 dias", days: 90 },
  { label: "1 ano", days: 365 },
];

const GROUPING_OPTIONS: Array<{
  label: string;
  value: "daily" | "weekly" | "monthly";
}> = [
  { label: "Diario", value: "daily" },
  { label: "Semanal", value: "weekly" },
  { label: "Mensual", value: "monthly" },
];

const CURRENCY_COLORS: Record<string, string> = {
  EUR: "bg-blue-500",
  PYG: "bg-green-500",
  USD: "bg-yellow-500",
};

const SEGMENT_COLORS: Record<string, string> = {
  new: "bg-emerald-500",
  active: "bg-blue-500",
  at_risk: "bg-yellow-400",
  lapsed: "bg-orange-400",
  churned: "bg-red-400",
};

const SEGMENT_LABELS: Record<string, string> = {
  new: "Nuevos",
  active: "Activos",
  at_risk: "En riesgo",
  lapsed: "Dormidos",
  churned: "Perdidos",
};

const RETENTION_HEAT_COLORS = [
  "bg-red-100 text-red-700",
  "bg-orange-100 text-orange-700",
  "bg-yellow-100 text-yellow-700",
  "bg-green-100 text-green-700",
  "bg-emerald-100 text-emerald-700",
];

function retentionHeatClass(pct: number): string {
  if (pct >= 70) return RETENTION_HEAT_COLORS[4];
  if (pct >= 50) return RETENTION_HEAT_COLORS[3];
  if (pct >= 30) return RETENTION_HEAT_COLORS[2];
  if (pct >= 10) return RETENTION_HEAT_COLORS[1];
  return RETENTION_HEAT_COLORS[0];
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiCard({
  label,
  value,
  subtext,
  icon,
  trend,
}: {
  label: string;
  value: string;
  subtext?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}) {
  const trendIcon =
    trend === "up" ? (
      <TrendingUp className="w-4 h-4 text-green-500" />
    ) : trend === "down" ? (
      <TrendingDown className="w-4 h-4 text-red-500" />
    ) : null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <span className="text-gray-400">{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {trendIcon}
      </div>
      {subtext && <span className="text-xs text-gray-400">{subtext}</span>}
    </div>
  );
}

function DonationTrendChart({
  rows,
  grouping,
}: {
  rows: SummaryRow[];
  grouping: string;
}) {
  // Aggregate rows by period_label (sum all currencies / dimensions)
  const byPeriod: Record<string, number> = {};
  for (const row of rows) {
    byPeriod[row.period_label] = (byPeriod[row.period_label] ?? 0) + row.donation_count;
  }
  const periods = Object.keys(byPeriod).slice(-24);
  const maxVal = Math.max(...periods.map((p) => byPeriod[p]), 1);

  if (periods.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">Sin datos para el periodo</div>
    );
  }

  return (
    <div>
      <div
        className="flex items-end gap-1 mt-4"
        style={{ height: 140 }}
        role="img"
        aria-label={`Donaciones por ${grouping}`}
      >
        {periods.map((label) => {
          const count = byPeriod[label];
          const heightPct = (count / maxVal) * 100;
          return (
            <div
              key={label}
              className="flex-1 flex flex-col items-center gap-1"
              title={`${label}: ${count} donaciones`}
            >
              <span className="text-xs text-gray-500 font-medium">{count}</span>
              <div
                className="w-full bg-blue-500 rounded-t-sm min-h-[2px] transition-all"
                style={{ height: `${Math.max(heightPct, 2)}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex items-end gap-1 mt-1">
        {periods.map((label) => (
          <div key={label} className="flex-1 text-center">
            <span className="text-xs text-gray-400 truncate block">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CurrencyBreakdown({ totals }: { totals: CurrencyTotal[] }) {
  const grandTotal = totals.reduce((s, t) => s + t.donation_count, 0);

  if (totals.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">Sin datos de moneda</div>
    );
  }

  return (
    <div className="space-y-3" role="list" aria-label="Distribucion por moneda">
      {totals.map((t) => {
        const pct = grandTotal > 0 ? (t.donation_count / grandTotal) * 100 : 0;
        return (
          <div key={t.currency} className="flex items-center gap-3" role="listitem">
            <span className="w-10 text-xs font-semibold text-gray-700">{t.currency}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${CURRENCY_COLORS[t.currency] ?? "bg-gray-400"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-24 text-right text-xs text-gray-500">{t.total_amount_display}</span>
            <span className="w-10 text-right text-xs font-medium text-gray-700">
              {pct.toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SegmentChart({ segments }: { segments: DonorSegments }) {
  const total = segments.total || 1;
  const keys = ["new", "active", "at_risk", "lapsed", "churned"] as const;

  return (
    <div className="space-y-3" role="list" aria-label="Segmentos de donantes">
      {keys.map((key) => {
        const count = segments[key];
        const pct = (count / total) * 100;
        return (
          <div key={key} className="flex items-center gap-3" role="listitem">
            <span className="w-20 text-xs font-medium text-gray-700">
              {SEGMENT_LABELS[key]}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${SEGMENT_COLORS[key]}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-8 text-right text-xs font-semibold text-gray-800">{count}</span>
            <span className="w-10 text-right text-xs text-gray-500">{pct.toFixed(0)}%</span>
          </div>
        );
      })}
    </div>
  );
}

function CohortTable({ cohorts }: { cohorts: CohortRow[] }) {
  if (cohorts.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8 text-sm">Sin datos de cohortes</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm" aria-label="Tabla de retencion por cohorte">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 pr-4 text-xs font-semibold text-gray-600">Cohorte</th>
            <th className="text-right py-2 px-2 text-xs font-semibold text-gray-600">Tamano</th>
            <th className="text-center py-2 px-2 text-xs font-semibold text-gray-600">+1 mes</th>
            <th className="text-center py-2 px-2 text-xs font-semibold text-gray-600">+3 meses</th>
            <th className="text-center py-2 px-2 text-xs font-semibold text-gray-600">+6 meses</th>
          </tr>
        </thead>
        <tbody>
          {cohorts.map((row) => (
            <tr key={row.cohort_month} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2 pr-4 text-xs font-medium text-gray-700">{row.cohort_month}</td>
              <td className="py-2 px-2 text-right text-xs text-gray-600">{row.cohort_size}</td>
              <td className="py-2 px-2 text-center">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${retentionHeatClass(row.retention_pct_1)}`}
                >
                  {row.retention_pct_1}%
                </span>
              </td>
              <td className="py-2 px-2 text-center">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${retentionHeatClass(row.retention_pct_3)}`}
                >
                  {row.retention_pct_3}%
                </span>
              </td>
              <td className="py-2 px-2 text-center">
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${retentionHeatClass(row.retention_pct_6)}`}
                >
                  {row.retention_pct_6}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function FinancialDashboardPage() {
  const [periodDays, setPeriodDays] = useState(30);
  const [grouping, setGrouping] = useState<"daily" | "weekly" | "monthly">("monthly");

  const [summary, setSummary] = useState<DonationSummary | null>(null);
  const [retention, setRetention] = useState<RetentionMetrics | null>(null);
  const [cohorts, setCohorts] = useState<CohortData | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const currentYear = new Date().getFullYear();

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, retentionData, cohortData] = await Promise.all([
        api.get<DonationSummary>(
          `/api/admin/financial-reporting/donation-summary?grouping=${grouping}&lookback_days=${periodDays}`
        ),
        api.get<RetentionMetrics>(
          `/api/admin/financial-reporting/donor-retention?period_days=${periodDays}`
        ),
        api.get<CohortData>(`/api/admin/financial-reporting/donor-cohorts?lookback_months=12`),
      ]);
      setSummary(summaryData);
      setRetention(retentionData);
      setCohorts(cohortData);
      setLastRefresh(new Date());
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`Error ${err.statusCode}: ${err.detail}`);
      } else {
        setError("No se pudo cargar el dashboard financiero");
      }
    } finally {
      setLoading(false);
    }
  }, [periodDays, grouping]);

  useEffect(() => {
    void fetchAll();
  }, [fetchAll]);

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" aria-hidden="true" />
            Dashboard Financiero
          </h1>
          {lastRefresh && (
            <p className="text-xs text-gray-400 mt-1">
              Actualizado: {lastRefresh.toLocaleTimeString()}
            </p>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Period selector */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.days}
                onClick={() => setPeriodDays(opt.days)}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  periodDays === opt.days
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
                aria-pressed={periodDays === opt.days}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Grouping selector */}
          <select
            value={grouping}
            onChange={(e) =>
              setGrouping(e.target.value as "daily" | "weekly" | "monthly")
            }
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Agrupacion de periodos"
          >
            {GROUPING_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Refresh */}
          <button
            onClick={() => void fetchAll()}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            aria-label="Actualizar datos"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Cargando..." : "Actualizar"}
          </button>

          {/* EU Tax export */}
          <a
            href={`/api/admin/financial-reporting/eu-tax-export/${currentYear}`}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            download
            aria-label={`Exportar CSV de donantes EU para ${currentYear}`}
          >
            <Download className="w-4 h-4" />
            EU Tax {currentYear}
          </a>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {/* KPI row */}
      <section aria-labelledby="kpis-heading">
        <h2 id="kpis-heading" className="sr-only">
          Indicadores clave
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard
            label="Total donaciones"
            value={summary?.total_donations?.toLocaleString() ?? "—"}
            subtext={`Ultimos ${periodDays} dias`}
            icon={<DollarSign className="w-5 h-5" />}
          />
          <KpiCard
            label="Tasa de retencion"
            value={retention ? `${retention.retention_rate_pct}%` : "—"}
            subtext={`Periodo ${periodDays}d`}
            icon={<UserCheck className="w-5 h-5 text-green-500" />}
            trend={
              retention
                ? retention.retention_rate_pct >= 50
                  ? "up"
                  : "down"
                : "neutral"
            }
          />
          <KpiCard
            label="Tasa de abandono"
            value={retention ? `${retention.churn_rate_pct}%` : "—"}
            subtext={`${retention?.churned_donors ?? "—"} donantes perdidos`}
            icon={<UserX className="w-5 h-5 text-red-500" />}
            trend={
              retention
                ? retention.churn_rate_pct <= 30
                  ? "up"
                  : "down"
                : "neutral"
            }
          />
          <KpiCard
            label="Donantes activos"
            value={
              retention
                ? (retention.segments.new + retention.segments.active).toLocaleString()
                : "—"
            }
            subtext={`${retention?.new_donors ?? "—"} nuevos este periodo`}
            icon={<Users className="w-5 h-5 text-blue-500" />}
            trend="up"
          />
        </div>
      </section>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Donation trend */}
        <section
          className="bg-white rounded-xl border border-gray-200 p-5"
          aria-labelledby="trend-heading"
        >
          <h2 id="trend-heading" className="text-lg font-semibold text-gray-900 mb-1">
            <TrendingUp className="w-5 h-5 inline-block mr-2 text-blue-500" aria-hidden="true" />
            Tendencia de Donaciones
          </h2>
          <p className="text-xs text-gray-500 mb-2">Cantidad de donaciones por periodo</p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
              Cargando...
            </div>
          ) : (
            <DonationTrendChart rows={summary?.rows ?? []} grouping={grouping} />
          )}
        </section>

        {/* Currency breakdown */}
        <section
          className="bg-white rounded-xl border border-gray-200 p-5"
          aria-labelledby="currency-heading"
        >
          <h2 id="currency-heading" className="text-lg font-semibold text-gray-900 mb-1">
            <DollarSign className="w-5 h-5 inline-block mr-2 text-green-500" aria-hidden="true" />
            Distribucion por Moneda
          </h2>
          <p className="text-xs text-gray-500 mb-4">Totales por moneda en el periodo</p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
              Cargando...
            </div>
          ) : (
            <CurrencyBreakdown totals={summary?.currency_totals ?? []} />
          )}
        </section>
      </div>

      {/* Retention row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Donor segments */}
        <section
          className="bg-white rounded-xl border border-gray-200 p-5"
          aria-labelledby="segments-heading"
        >
          <h2 id="segments-heading" className="text-lg font-semibold text-gray-900 mb-1">
            <Users className="w-5 h-5 inline-block mr-2 text-indigo-500" aria-hidden="true" />
            Segmentacion de Donantes
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            Total: {retention?.segments.total ?? "—"} donantes con historial
          </p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
              Cargando...
            </div>
          ) : retention ? (
            <SegmentChart segments={retention.segments} />
          ) : (
            <div className="text-center text-gray-400 py-8 text-sm">Sin datos</div>
          )}
        </section>

        {/* Retention rate card */}
        <section
          className="bg-white rounded-xl border border-gray-200 p-5"
          aria-labelledby="retrates-heading"
        >
          <h2 id="retrates-heading" className="text-lg font-semibold text-gray-900 mb-4">
            <UserCheck className="w-5 h-5 inline-block mr-2 text-green-500" aria-hidden="true" />
            Retencion vs Abandono
          </h2>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-gray-400 text-sm">
              Cargando...
            </div>
          ) : retention ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-3xl font-bold text-green-700">
                    {retention.retention_rate_pct}%
                  </p>
                  <p className="text-sm text-green-600 mt-1">Retencion</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {retention.retained_donors} donantes retenidos
                  </p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-3xl font-bold text-red-700">
                    {retention.churn_rate_pct}%
                  </p>
                  <p className="text-sm text-red-600 mt-1">Abandono</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {retention.churned_donors} donantes perdidos
                  </p>
                </div>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-sm text-blue-700">
                  <span className="font-semibold">{retention.new_donors}</span> donantes nuevos
                  en los ultimos {retention.period_days} dias
                </p>
              </div>
              {/* Visual retention bar */}
              <div>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Retenidos</span>
                  <span>Perdidos</span>
                </div>
                <div className="flex h-4 rounded-full overflow-hidden">
                  <div
                    className="bg-green-500 transition-all"
                    style={{ width: `${retention.retention_rate_pct}%` }}
                    role="presentation"
                  />
                  <div
                    className="bg-red-400 transition-all"
                    style={{ width: `${retention.churn_rate_pct}%` }}
                    role="presentation"
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8 text-sm">Sin datos</div>
          )}
        </section>
      </div>

      {/* Cohort retention table */}
      <section
        className="bg-white rounded-xl border border-gray-200 p-5"
        aria-labelledby="cohort-heading"
      >
        <h2 id="cohort-heading" className="text-lg font-semibold text-gray-900 mb-1">
          <BarChart3 className="w-5 h-5 inline-block mr-2 text-purple-500" aria-hidden="true" />
          Retencion por Cohorte Mensual
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          % de donantes que volvieron a donar 1, 3 y 6 meses despues de su primera donacion
        </p>
        {loading ? (
          <div className="h-24 flex items-center justify-center text-gray-400 text-sm">
            Cargando...
          </div>
        ) : (
          <CohortTable cohorts={cohorts?.cohorts ?? []} />
        )}
      </section>
    </main>
  );
}
