"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Users,
  TrendingUp,
  TrendingDown,
  Heart,
  AlertTriangle,
  UserCheck,
  UserX,
  UserPlus,
  Repeat,
  Star,
  BarChart3,
  RefreshCw,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RetentionMetric {
  label: string;
  value: number;
  unit: string;
  change_percent: number | null;
  trend: string;
}

interface RetentionSummary {
  retention_rate: number;
  churn_rate: number;
  average_donor_lifetime_months: number;
  average_ltv_pyg: number;
  total_active_donors: number;
  total_donors: number;
  period_days: number;
  metrics: RetentionMetric[];
}

interface SegmentData {
  segment: string;
  label: string;
  count: number;
  percentage: number;
  average_donation_pyg: number;
  total_donated_pyg: number;
}

interface AcquisitionTrend {
  month: string;
  year: number;
  new_donors: number;
  returning_donors: number;
  churned_donors: number;
  net_growth: number;
}

interface RecurringAnalysis {
  recurring_donors: number;
  one_time_donors: number;
  recurring_percentage: number;
  recurring_total_pyg: number;
  one_time_total_pyg: number;
  recurring_avg_pyg: number;
  one_time_avg_pyg: number;
  conversion_rate: number;
}

interface EngagementScore {
  level: string;
  label: string;
  count: number;
  percentage: number;
  avg_donations_per_year: number;
  avg_amount_pyg: number;
}

interface ReactivationOpportunity {
  donor_name: string;
  last_donation_date: string;
  days_since_last: number;
  total_historical_pyg: number;
  donation_count: number;
  segment: string;
  reactivation_priority: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const formatPYG = (amount: number): string => {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K`;
  return amount.toLocaleString("es-PY");
};

const SEGMENT_COLORS: Record<string, string> = {
  new: "bg-blue-500",
  active: "bg-green-500",
  at_risk: "bg-yellow-500",
  lapsed: "bg-orange-500",
  churned: "bg-red-500",
};

const SEGMENT_ICONS: Record<string, typeof UserPlus> = {
  new: UserPlus,
  active: UserCheck,
  at_risk: AlertTriangle,
  lapsed: UserX,
  churned: UserX,
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-gray-100 text-gray-700",
};

const ENGAGEMENT_COLORS: Record<string, string> = {
  high: "bg-green-500",
  medium: "bg-blue-500",
  low: "bg-yellow-500",
  inactive: "bg-gray-400",
};

const PERIOD_OPTIONS = [
  { label: "30 dias", value: 30 },
  { label: "90 dias", value: 90 },
  { label: "180 dias", value: 180 },
  { label: "1 ano", value: 365 },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function RetentionCard({ metric }: { metric: RetentionMetric }) {
  const TrendIcon = metric.trend === "up" ? TrendingUp : metric.trend === "down" ? TrendingDown : BarChart3;
  const trendColor = metric.trend === "up" ? "text-green-600" : metric.trend === "down" ? "text-red-600" : "text-gray-500";
  const displayValue = metric.unit === "PYG" ? formatPYG(metric.value) : metric.unit === "%" ? `${metric.value}%` : metric.value.toFixed(1);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5" role="region" aria-label={metric.label}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{metric.label}</span>
        <TrendIcon className={`w-5 h-5 ${trendColor}`} aria-hidden="true" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{displayValue}</p>
      {metric.change_percent !== null && (
        <p className={`text-sm mt-1 ${trendColor}`}>
          {metric.change_percent > 0 ? "+" : ""}{metric.change_percent}%
        </p>
      )}
    </div>
  );
}

function SegmentChart({ segments }: { segments: SegmentData[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Segmentacion de Donantes</h2>
      <div className="space-y-3" role="list" aria-label="Segmentos de donantes">
        {segments.map((s) => {
          const Icon = SEGMENT_ICONS[s.segment] ?? Users;
          return (
            <div key={s.segment} className="flex items-center gap-3" role="listitem">
              <Icon className="w-5 h-5 text-gray-400 shrink-0" aria-hidden="true" />
              <div className="w-20 text-sm text-gray-700">{s.label}</div>
              <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
                <div
                  className={`h-full rounded-full ${SEGMENT_COLORS[s.segment] ?? "bg-gray-400"} transition-all`}
                  style={{ width: `${s.percentage}%` }}
                />
              </div>
              <div className="w-12 text-right text-sm font-medium text-gray-900">{s.count}</div>
              <div className="w-12 text-right text-xs text-gray-500">{s.percentage}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AcquisitionChart({ trends }: { trends: AcquisitionTrend[] }) {
  const maxVal = Math.max(...trends.map((t) => Math.max(t.new_donors, t.returning_donors)));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Adquisicion de Donantes</h2>
      <div className="flex items-end gap-2 h-48" role="img" aria-label="Tendencia de adquisicion de donantes">
        {trends.map((t) => (
          <div key={`${t.month}-${t.year}`} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs text-gray-500">+{t.net_growth}</span>
            <div className="w-full flex gap-0.5 items-end" style={{ height: "80%" }}>
              <div
                className="flex-1 bg-green-400 rounded-t-sm min-h-[2px]"
                style={{ height: `${maxVal > 0 ? (t.new_donors / maxVal) * 100 : 0}%` }}
                aria-label={`${t.month}: ${t.new_donors} nuevos`}
              />
              <div
                className="flex-1 bg-blue-400 rounded-t-sm min-h-[2px]"
                style={{ height: `${maxVal > 0 ? (t.returning_donors / maxVal) * 100 : 0}%` }}
                aria-label={`${t.month}: ${t.returning_donors} recurrentes`}
              />
            </div>
            <span className="text-xs text-gray-600 font-medium">{t.month}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-3 justify-center text-xs">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-400" /> Nuevos</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-400" /> Recurrentes</span>
      </div>
    </div>
  );
}

function RecurringCard({ data }: { data: RecurringAnalysis }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <Repeat className="w-5 h-5 inline-block mr-2 text-green-500" aria-hidden="true" />
        Donantes Recurrentes vs Unicos
      </h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-green-50 rounded-lg" role="region" aria-label="Donantes recurrentes">
          <p className="text-2xl font-bold text-green-700">{data.recurring_donors}</p>
          <p className="text-sm text-green-600">Recurrentes ({data.recurring_percentage}%)</p>
          <p className="text-xs text-gray-500 mt-1">Prom: {formatPYG(data.recurring_avg_pyg)}</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg" role="region" aria-label="Donantes unicos">
          <p className="text-2xl font-bold text-gray-700">{data.one_time_donors}</p>
          <p className="text-sm text-gray-600">Unicos</p>
          <p className="text-xs text-gray-500 mt-1">Prom: {formatPYG(data.one_time_avg_pyg)}</p>
        </div>
      </div>
      <div className="bg-blue-50 rounded-lg p-3" role="region" aria-label="Tasa de conversion a recurrente">
        <div className="flex items-center justify-between">
          <span className="text-sm text-blue-700">Tasa de conversion a recurrente</span>
          <span className="text-lg font-bold text-blue-700">{data.conversion_rate}%</span>
        </div>
      </div>
    </div>
  );
}

function EngagementChart({ scores }: { scores: EngagementScore[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <Star className="w-5 h-5 inline-block mr-2 text-yellow-500" aria-hidden="true" />
        Nivel de Compromiso
      </h2>
      <div className="space-y-3" role="list" aria-label="Niveles de compromiso de donantes">
        {scores.map((s) => (
          <div key={s.level} className="flex items-center gap-3" role="listitem">
            <div className="w-16 text-sm font-medium text-gray-700">{s.label}</div>
            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
              <div
                className={`h-full rounded-full ${ENGAGEMENT_COLORS[s.level] ?? "bg-gray-400"}`}
                style={{ width: `${s.percentage}%` }}
              />
            </div>
            <div className="w-10 text-right text-sm font-medium">{s.count}</div>
            <div className="w-24 text-right text-xs text-gray-500">
              {s.avg_donations_per_year}/ano | {formatPYG(s.avg_amount_pyg)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReactivationTable({ opportunities }: { opportunities: ReactivationOpportunity[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <RefreshCw className="w-5 h-5 inline-block mr-2 text-orange-500" aria-hidden="true" />
        Oportunidades de Reactivacion
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" aria-label="Donantes para reactivacion">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Donante</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Dias inactivo</th>
              <th className="text-right py-2 px-2 text-gray-500 font-medium">Total historico</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Donaciones</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Prioridad</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((o) => (
              <tr key={o.donor_name} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-2 font-medium text-gray-900">{o.donor_name}</td>
                <td className="py-2 px-2 text-center text-gray-600">{o.days_since_last}d</td>
                <td className="py-2 px-2 text-right font-medium text-gray-900">{formatPYG(o.total_historical_pyg)}</td>
                <td className="py-2 px-2 text-center text-gray-600">{o.donation_count}</td>
                <td className="py-2 px-2 text-center">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${PRIORITY_COLORS[o.reactivation_priority] ?? "bg-gray-100 text-gray-700"}`}>
                    {o.reactivation_priority === "critical" ? "Critico" : o.reactivation_priority === "high" ? "Alto" : o.reactivation_priority === "medium" ? "Medio" : "Bajo"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Cargando analiticas de donantes">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-200 rounded-xl h-28" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-200 rounded-xl h-64" />
        <div className="bg-gray-200 rounded-xl h-64" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DonorAnalyticsPage() {
  const [retention, setRetention] = useState<RetentionSummary | null>(null);
  const [segments, setSegments] = useState<SegmentData[]>([]);
  const [acquisition, setAcquisition] = useState<AcquisitionTrend[]>([]);
  const [recurring, setRecurring] = useState<RecurringAnalysis | null>(null);
  const [engagement, setEngagement] = useState<EngagementScore[]>([]);
  const [reactivation, setReactivation] = useState<ReactivationOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodDays, setPeriodDays] = useState(30);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [retRes, segRes, acqRes, recRes, engRes, reactRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/analytics/donors/retention?period_days=${periodDays}`),
        fetch(`${API_BASE}/api/admin/analytics/donors/segments?period_days=${periodDays}`),
        fetch(`${API_BASE}/api/admin/analytics/donors/acquisition?months=6`),
        fetch(`${API_BASE}/api/admin/analytics/donors/recurring?period_days=${periodDays}`),
        fetch(`${API_BASE}/api/admin/analytics/donors/engagement?period_days=${periodDays}`),
        fetch(`${API_BASE}/api/admin/analytics/donors/reactivation`),
      ]);

      if (retRes.ok) setRetention(await retRes.json());
      if (segRes.ok) setSegments(await segRes.json());
      if (acqRes.ok) setAcquisition(await acqRes.json());
      if (recRes.ok) setRecurring(await recRes.json());
      if (engRes.ok) setEngagement(await engRes.json());
      if (reactRes.ok) setReactivation(await reactRes.json());
    } catch {
      setError("Error al cargar los datos de donantes");
    } finally {
      setLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <LoadingSkeleton />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            <Users className="w-7 h-7 inline-block mr-2 text-orange-500" aria-hidden="true" />
            Analiticas de Donantes
          </h1>
          <p className="text-gray-500 mt-1">Retencion, segmentacion y oportunidades de reactivacion</p>
        </div>
        <div className="flex gap-2" role="group" aria-label="Seleccionar periodo">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriodDays(opt.value)}
              className={`px-3 py-2 text-sm rounded-lg min-h-[44px] transition-colors ${
                periodDays === opt.value
                  ? "bg-orange-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
              aria-pressed={periodDays === opt.value}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6" role="alert">
          {error}
        </div>
      )}

      {/* Retention KPIs */}
      {retention && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {retention.metrics.map((m) => (
            <RetentionCard key={m.label} metric={m} />
          ))}
        </div>
      )}

      {/* Active donors summary */}
      {retention && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex items-center justify-between" role="region" aria-label="Resumen de donantes activos">
          <div className="flex items-center gap-3">
            <Heart className="w-6 h-6 text-red-500" aria-hidden="true" />
            <div>
              <p className="text-lg font-bold text-gray-900">{retention.total_active_donors} donantes activos</p>
              <p className="text-sm text-gray-500">de {retention.total_donors} donantes totales</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-green-600">{retention.retention_rate}%</p>
            <p className="text-sm text-gray-500">retencion</p>
          </div>
        </div>
      )}

      {/* Segments & Acquisition */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {segments.length > 0 && <SegmentChart segments={segments} />}
        {acquisition.length > 0 && <AcquisitionChart trends={acquisition} />}
      </div>

      {/* Recurring & Engagement */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {recurring && <RecurringCard data={recurring} />}
        {engagement.length > 0 && <EngagementChart scores={engagement} />}
      </div>

      {/* Reactivation */}
      {reactivation.length > 0 && <ReactivationTable opportunities={reactivation} />}
    </div>
  );
}
