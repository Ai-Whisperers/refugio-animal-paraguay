"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Clock,
  Dog,
  Heart,
  Home,
  RefreshCw,
  Users,
} from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types (matching OperationalMetricsResponse from backend RAP-250)
// ---------------------------------------------------------------------------

interface PopulationBreakdown {
  intake: number;
  quarantine: number;
  available: number;
  foster: number;
  under_treatment: number;
  adopted: number;
  deceased: number;
  total: number;
}

interface OccupancyMetrics {
  current_count: number;
  capacity: number;
  occupancy_rate_pct: number;
}

interface PeriodCounts {
  period_days: number;
  intake_count: number;
  outcome_count: number;
}

interface SpeciesBreakdown {
  dog: number;
  cat: number;
  other: number;
}

interface OperationalMetrics {
  generated_at: string;
  population: PopulationBreakdown;
  occupancy: OccupancyMetrics;
  period: PeriodCounts;
  species: SpeciesBreakdown;
  avg_los_days: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PERIOD_OPTIONS = [
  { label: "7 dias", value: 7 },
  { label: "14 dias", value: 14 },
  { label: "30 dias", value: 30 },
  { label: "90 dias", value: 90 },
];

const OCCUPANCY_THRESHOLDS = {
  safe: 70,
  warning: 85,
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function occupancyColor(rate: number): string {
  if (rate >= OCCUPANCY_THRESHOLDS.warning) return "text-red-600";
  if (rate >= OCCUPANCY_THRESHOLDS.safe) return "text-yellow-600";
  return "text-green-600";
}

function occupancyBg(rate: number): string {
  if (rate >= OCCUPANCY_THRESHOLDS.warning) return "bg-red-50 border-red-200";
  if (rate >= OCCUPANCY_THRESHOLDS.safe) return "bg-yellow-50 border-yellow-200";
  return "bg-green-50 border-green-200";
}

function occupancyBarColor(rate: number): string {
  if (rate >= OCCUPANCY_THRESHOLDS.warning) return "bg-red-500";
  if (rate >= OCCUPANCY_THRESHOLDS.safe) return "bg-yellow-500";
  return "bg-green-500";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("es-PY", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  colorClass?: string;
  borderClass?: string;
  children?: React.ReactNode;
}

function KpiCard({
  title,
  value,
  subtitle,
  icon,
  colorClass = "text-blue-600",
  borderClass = "border-blue-200",
  children,
}: KpiCardProps) {
  return (
    <div className={`bg-white rounded-xl border ${borderClass} p-5 shadow-sm`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-600">{title}</span>
        <span className={`${colorClass}`}>{icon}</span>
      </div>
      <div className={`text-3xl font-bold ${colorClass} mb-1`}>{value}</div>
      {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      {children}
    </div>
  );
}

interface PopulationRowProps {
  label: string;
  count: number;
  total: number;
  color: string;
}

function PopulationRow({ label, count, total, color }: PopulationRowProps) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 py-1">
      <span className="w-32 text-xs text-gray-600 capitalize">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-xs font-medium text-gray-700 text-right">{count}</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-64 mb-2" />
      <div className="h-4 bg-gray-100 rounded w-48 mb-8" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-xl h-32" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="bg-gray-100 rounded-xl h-48" />
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function OperationalDashboardPage() {
  const [metrics, setMetrics] = useState<OperationalMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodDays, setPeriodDays] = useState(30);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<OperationalMetrics>(
        `/api/admin/operational-dashboard/metrics?period_days=${periodDays}`
      );
      setMetrics(data);
      setLastRefreshed(new Date());
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 401) {
        setError("Sesion expirada. Por favor, inicia sesion nuevamente.");
      } else {
        setError("Error al cargar los datos del dashboard. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
          <button
            onClick={fetchMetrics}
            className="ml-auto flex items-center gap-1 text-sm font-medium hover:underline"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const { population, occupancy, period, species, avg_los_days } = metrics;
  const outcomeRate =
    period.intake_count > 0
      ? Math.round((period.outcome_count / period.intake_count) * 100)
      : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-blue-600" aria-hidden="true" />
            Dashboard Operacional
          </h1>
          {lastRefreshed && (
            <p className="text-sm text-gray-500 mt-1">
              Actualizado: {lastRefreshed.toLocaleTimeString("es-PY")}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Period selector */}
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Periodo de analisis"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Refresh button */}
          <button
            onClick={fetchMetrics}
            className="flex items-center gap-1.5 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg px-3 py-2 hover:bg-blue-50 transition-colors"
            aria-label="Actualizar datos"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Top KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Occupancy */}
        <KpiCard
          title="Ocupacion del Refugio"
          value={`${occupancy.occupancy_rate_pct}%`}
          subtitle={`${occupancy.current_count} / ${occupancy.capacity} lugares`}
          icon={<Home className="w-5 h-5" aria-hidden="true" />}
          colorClass={occupancyColor(occupancy.occupancy_rate_pct)}
          borderClass={occupancyBg(occupancy.occupancy_rate_pct).split(" ")[1]}
        >
          <div className="mt-3 bg-gray-100 rounded-full h-2">
            <div
              className={`${occupancyBarColor(occupancy.occupancy_rate_pct)} h-2 rounded-full transition-all`}
              style={{ width: `${Math.min(occupancy.occupancy_rate_pct, 100)}%` }}
              role="progressbar"
              aria-valuenow={occupancy.occupancy_rate_pct}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </KpiCard>

        {/* Intake */}
        <KpiCard
          title={`Ingresos (${period.period_days}d)`}
          value={period.intake_count}
          subtitle="animales ingresados"
          icon={<ArrowUpRight className="w-5 h-5" aria-hidden="true" />}
          colorClass="text-blue-600"
          borderClass="border-blue-200"
        />

        {/* Outcomes */}
        <KpiCard
          title={`Egresos (${period.period_days}d)`}
          value={period.outcome_count}
          subtitle={`${outcomeRate}% tasa de egreso`}
          icon={<ArrowDownRight className="w-5 h-5" aria-hidden="true" />}
          colorClass="text-emerald-600"
          borderClass="border-emerald-200"
        />

        {/* Avg LOS */}
        <KpiCard
          title="Estadia Promedio"
          value={`${avg_los_days}d`}
          subtitle="dias en el refugio"
          icon={<Clock className="w-5 h-5" aria-hidden="true" />}
          colorClass="text-purple-600"
          borderClass="border-purple-200"
        />
      </div>

      {/* Second row — Population breakdown + Species */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {/* Population breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-gray-500" aria-hidden="true" />
            <h2 className="font-semibold text-gray-800">Poblacion por Estado</h2>
            <span className="ml-auto text-sm font-bold text-gray-700">{population.total} total</span>
          </div>
          <div className="space-y-1">
            <PopulationRow
              label="Disponible"
              count={population.available}
              total={population.total}
              color="bg-green-400"
            />
            <PopulationRow
              label="Cuarentena"
              count={population.quarantine}
              total={population.total}
              color="bg-yellow-400"
            />
            <PopulationRow
              label="Ingreso"
              count={population.intake}
              total={population.total}
              color="bg-blue-400"
            />
            <PopulationRow
              label="En tratamiento"
              count={population.under_treatment}
              total={population.total}
              color="bg-orange-400"
            />
            <PopulationRow
              label="En acogida"
              count={population.foster}
              total={population.total}
              color="bg-purple-400"
            />
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100 flex gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Heart className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
              {population.adopted} adoptados
            </span>
            <span className="flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-gray-400" aria-hidden="true" />
              {population.deceased} fallecidos
            </span>
          </div>
        </div>

        {/* Species breakdown */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Dog className="w-5 h-5 text-gray-500" aria-hidden="true" />
            <h2 className="font-semibold text-gray-800">Distribucion por Especie</h2>
            <span className="ml-auto text-sm font-bold text-gray-700">
              {species.dog + species.cat + species.other} en refugio
            </span>
          </div>
          <div className="space-y-4">
            {(
              [
                { label: "Perros", count: species.dog, color: "bg-amber-400", emoji: "Perros" },
                { label: "Gatos", count: species.cat, color: "bg-blue-400", emoji: "Gatos" },
                { label: "Otros", count: species.other, color: "bg-gray-400", emoji: "Otros" },
              ] as const
            ).map((s) => {
              const sheltered = species.dog + species.cat + species.other;
              const pct = sheltered > 0 ? Math.round((s.count / sheltered) * 100) : 0;
              return (
                <div key={s.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{s.label}</span>
                    <span className="font-medium text-gray-800">
                      {s.count} ({pct}%)
                    </span>
                  </div>
                  <div className="bg-gray-100 rounded-full h-3">
                    <div
                      className={`${s.color} h-3 rounded-full transition-all`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
            Periodo de analisis: {period.period_days} dias &bull; Generado:{" "}
            {formatDate(metrics.generated_at)}
          </div>
        </div>
      </div>

      {/* Occupancy alert banner */}
      {occupancy.occupancy_rate_pct >= OCCUPANCY_THRESHOLDS.warning && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          <span className="font-medium">
            Alerta de capacidad: el refugio esta al {occupancy.occupancy_rate_pct}% de ocupacion.
            Considera ampliar la capacidad o acelerar adopciones.
          </span>
        </div>
      )}
      {occupancy.occupancy_rate_pct >= OCCUPANCY_THRESHOLDS.safe &&
        occupancy.occupancy_rate_pct < OCCUPANCY_THRESHOLDS.warning && (
          <div className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-xl text-yellow-700">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
            <span className="font-medium">
              Capacidad moderada: el refugio esta al {occupancy.occupancy_rate_pct}% de ocupacion.
            </span>
          </div>
        )}
    </div>
  );
}
