"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface KPIMetric {
  id: string;
  name: string;
  category: string;
  value: number;
  unit: string;
  target: number | null;
  previous_value: number | null;
  trend: string;
  trend_pct: number;
  status: string;
}

interface KPIDashboard {
  period_days: number;
  generated_at: string;
  kpis: KPIMetric[];
  summary: {
    total_kpis: number;
    on_track: number;
    approaching: number;
    at_risk: number;
    health_score: number;
  };
}

interface DashboardAlert {
  id: string;
  severity: string;
  title: string;
  message: string;
  category: string;
  action_url: string | null;
}

interface AlertsResponse {
  alerts: DashboardAlert[];
  total: number;
  critical_count: number;
  warning_count: number;
}

interface PerformanceScore {
  metric: string;
  actual: number;
  target: number;
  score: number;
  grade: string;
}

interface PerformanceScorecard {
  scores: PerformanceScore[];
  overall_score: number;
  overall_grade: string;
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function formatValue(value: number, unit: string): string {
  if (unit === "PYG") return new Intl.NumberFormat("es-PY").format(value) + " PYG";
  if (unit === "EUR") return new Intl.NumberFormat("de-DE").format(value) + " EUR";
  if (unit === "%") return value + "%";
  return new Intl.NumberFormat("es-PY").format(value) + " " + unit;
}

function statusColor(status: string): string {
  switch (status) {
    case "on_track": return "bg-green-100 text-green-800";
    case "approaching": return "bg-yellow-100 text-yellow-800";
    case "at_risk": return "bg-red-100 text-red-800";
    default: return "bg-gray-100 text-gray-600";
  }
}

function trendIcon(trend: string, pct: number): string {
  if (trend === "up") return pct >= 0 ? "\u2191" : "\u2193";
  if (trend === "down") return pct <= 0 ? "\u2193" : "\u2191";
  return "\u2194";
}

function severityColor(severity: string): string {
  switch (severity) {
    case "critical": return "border-red-500 bg-red-50";
    case "warning": return "border-yellow-500 bg-yellow-50";
    default: return "border-blue-500 bg-blue-50";
  }
}

function gradeColor(grade: string): string {
  if (grade.startsWith("A")) return "text-green-600";
  if (grade === "B") return "text-yellow-600";
  return "text-red-600";
}

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Cargando dashboard">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-gray-200 rounded-xl" />
        ))}
      </div>
      {[1, 2].map((i) => (
        <div key={i} className="h-48 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function HealthSummary({ summary }: { summary: KPIDashboard["summary"] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
        <p className="text-3xl font-bold text-[var(--color-primary)]">{summary.health_score}%</p>
        <p className="text-sm text-gray-500">Salud general</p>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
        <p className="text-3xl font-bold text-green-600">{summary.on_track}</p>
        <p className="text-sm text-gray-500">En meta</p>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
        <p className="text-3xl font-bold text-yellow-600">{summary.approaching}</p>
        <p className="text-sm text-gray-500">Acercandose</p>
      </div>
      <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
        <p className="text-3xl font-bold text-red-600">{summary.at_risk}</p>
        <p className="text-sm text-gray-500">En riesgo</p>
      </div>
    </div>
  );
}

function KPICard({ kpi }: { kpi: KPIMetric }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm font-medium text-gray-600">{kpi.name}</p>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(kpi.status)}`}>
          {kpi.status === "on_track" ? "En meta" : kpi.status === "approaching" ? "Acercandose" : "En riesgo"}
        </span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{formatValue(kpi.value, kpi.unit)}</p>
      <div className="flex items-center justify-between mt-2">
        <span className={`text-sm ${kpi.trend_pct >= 0 ? "text-green-600" : "text-red-600"}`}>
          {trendIcon(kpi.trend, kpi.trend_pct)} {Math.abs(kpi.trend_pct)}%
        </span>
        {kpi.target && (
          <span className="text-xs text-gray-400">Meta: {formatValue(kpi.target, kpi.unit)}</span>
        )}
      </div>
    </div>
  );
}

function AlertsList({ alerts }: { alerts: AlertsResponse }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Alertas activas</h2>
        <div className="flex gap-2 text-sm">
          {alerts.critical_count > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full font-medium">
              {alerts.critical_count} criticas
            </span>
          )}
          {alerts.warning_count > 0 && (
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full font-medium">
              {alerts.warning_count} advertencias
            </span>
          )}
        </div>
      </div>
      <div className="space-y-3">
        {alerts.alerts.map((alert) => (
          <div key={alert.id} className={`border-l-4 rounded-r-lg p-3 ${severityColor(alert.severity)}`}>
            <p className="font-medium text-gray-900 text-sm">{alert.title}</p>
            <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ScorecardSection({ scorecard }: { scorecard: PerformanceScorecard }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Scorecard de rendimiento</h2>
        <div className="text-center">
          <span className={`text-2xl font-bold ${gradeColor(scorecard.overall_grade)}`}>
            {scorecard.overall_grade}
          </span>
          <p className="text-xs text-gray-500">{scorecard.overall_score}%</p>
        </div>
      </div>
      <div className="space-y-3">
        {scorecard.scores.map((s) => (
          <div key={s.metric} className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-700">{s.metric}</span>
                <span className={`font-medium ${gradeColor(s.grade)}`}>{s.grade}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--color-primary)] rounded-full transition-all"
                  style={{ width: `${Math.min(s.score, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Actual: {s.actual}</span>
                <span>Meta: {s.target}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// -- Main page -----------------------------------------------------------

export default function ExecutiveDashboardPage() {
  const [period, setPeriod] = useState(30);
  const [dashboard, setDashboard] = useState<KPIDashboard | null>(null);
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [scorecard, setScorecard] = useState<PerformanceScorecard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const q = `?period_days=${period}`;
    Promise.all([
      fetchJSON<KPIDashboard>(`/api/admin/dashboard/kpis${q}`),
      fetchJSON<AlertsResponse>("/api/admin/dashboard/alerts"),
      fetchJSON<PerformanceScorecard>(`/api/admin/dashboard/performance${q}`),
    ])
      .then(([d, a, s]) => {
        setDashboard(d);
        setAlerts(a);
        setScorecard(s);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [period]);

  const periodOptions = [
    { label: "30 dias", value: 30 },
    { label: "90 dias", value: 90 },
    { label: "1 ano", value: 365 },
  ];

  const categories = ["animals", "financial", "community", "operations"];
  const categoryLabels: Record<string, string> = {
    animals: "Animales",
    financial: "Financiero",
    community: "Comunidad",
    operations: "Operaciones",
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard ejecutivo</h1>
          <p className="text-gray-500 mt-1">Indicadores clave de rendimiento del refugio</p>
        </div>
        <div className="flex gap-2">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === opt.value
                  ? "bg-[var(--color-primary)] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton />
      ) : (
        <div className="space-y-6">
          {dashboard && <HealthSummary summary={dashboard.summary} />}

          {dashboard &&
            categories.map((cat) => {
              const catKpis = dashboard.kpis.filter((k) => k.category === cat);
              if (catKpis.length === 0) return null;
              return (
                <div key={cat}>
                  <h2 className="text-lg font-semibold text-gray-900 mb-3">
                    {categoryLabels[cat]}
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {catKpis.map((kpi) => (
                      <KPICard key={kpi.id} kpi={kpi} />
                    ))}
                  </div>
                </div>
              );
            })}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {alerts && <AlertsList alerts={alerts} />}
            {scorecard && <ScorecardSection scorecard={scorecard} />}
          </div>
        </div>
      )}
    </div>
  );
}
