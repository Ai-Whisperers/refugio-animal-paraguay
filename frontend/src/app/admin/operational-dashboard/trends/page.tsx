"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  AlertTriangle,
  BarChart3,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Minus,
} from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types (matching TrendsResponse from backend RAP-252)
// ---------------------------------------------------------------------------

interface TrendDataPoint {
  period_label: string;
  intake_count: number;
  outcome_count: number;
}

interface TrendsResponse {
  interval: string;
  lookback_days: number;
  generated_at: string;
  data_points: TrendDataPoint[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type Interval = "daily" | "weekly" | "monthly";

const INTERVAL_OPTIONS: { label: string; value: Interval; lookback_days: number }[] = [
  { label: "Diario (30 dias)", value: "daily", lookback_days: 30 },
  { label: "Semanal (90 dias)", value: "weekly", lookback_days: 90 },
  { label: "Mensual (365 dias)", value: "monthly", lookback_days: 365 },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function computeTrend(data: TrendDataPoint[], field: "intake_count" | "outcome_count"): string {
  if (data.length < 2) return "stable";
  const first = data[0][field];
  const last = data[data.length - 1][field];
  const change = last - first;
  const pct = first > 0 ? Math.abs(change / first) * 100 : 0;
  if (pct < 5) return "stable";
  return change > 0 ? "up" : "down";
}

function TrendBadge({ trend, label }: { trend: string; label: string }) {
  if (trend === "up") {
    return (
      <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
        <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
        {label} creciendo
      </span>
    );
  }
  if (trend === "down") {
    return (
      <span className="flex items-center gap-1 text-red-600 text-xs font-medium">
        <TrendingDown className="w-3.5 h-3.5" aria-hidden="true" />
        {label} bajando
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-gray-500 text-xs font-medium">
      <Minus className="w-3.5 h-3.5" aria-hidden="true" />
      {label} estable
    </span>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-72 mb-2" />
      <div className="h-4 bg-gray-100 rounded w-48 mb-8" />
      <div className="bg-gray-100 rounded-xl h-96 mb-4" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function OperationalTrendsPage() {
  const [data, setData] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOption, setActiveOption] = useState(INTERVAL_OPTIONS[2]); // Monthly default

  const fetchTrends = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<TrendsResponse>(
        `/api/admin/operational-dashboard/trends?interval=${activeOption.value}&lookback_days=${activeOption.lookback_days}`
      );
      setData(result);
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 401) {
        setError("Sesion expirada. Por favor, inicia sesion nuevamente.");
      } else {
        setError("Error al cargar los datos de tendencias. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }, [activeOption]);

  useEffect(() => {
    fetchTrends();
  }, [fetchTrends]);

  if (loading) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
          <button
            onClick={fetchTrends}
            className="ml-auto flex items-center gap-1 text-sm font-medium hover:underline"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const points = data?.data_points ?? [];
  const intakeTrend = computeTrend(points, "intake_count");
  const outcomeTrend = computeTrend(points, "outcome_count");
  const totalIntake = points.reduce((sum, p) => sum + p.intake_count, 0);
  const totalOutcome = points.reduce((sum, p) => sum + p.outcome_count, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-blue-600" aria-hidden="true" />
            Tendencias de Ingresos y Egresos
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {data ? `${data.data_points.length} periodos — ${data.lookback_days} dias de historial` : ""}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Interval selector */}
          <div className="flex rounded-lg border border-gray-300 overflow-hidden" role="group" aria-label="Intervalo de tiempo">
            {INTERVAL_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setActiveOption(opt)}
                className={`px-3 py-2 text-sm font-medium transition-colors ${
                  activeOption.value === opt.value
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
                aria-pressed={activeOption.value === opt.value}
              >
                {opt.label.split(" ")[0]}
              </button>
            ))}
          </div>

          <button
            onClick={fetchTrends}
            className="flex items-center gap-1.5 text-sm font-medium text-blue-600 border border-blue-300 rounded-lg px-3 py-2 hover:bg-blue-50 transition-colors"
            aria-label="Actualizar datos"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-blue-200 p-4 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-sm text-gray-500 mb-1">Ingresos totales</div>
              <div className="text-2xl font-bold text-blue-600">{totalIntake}</div>
            </div>
            <TrendBadge trend={intakeTrend} label="Ingresos" />
          </div>
        </div>
        <div className="bg-white rounded-xl border border-emerald-200 p-4 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-sm text-gray-500 mb-1">Egresos totales</div>
              <div className="text-2xl font-bold text-emerald-600">{totalOutcome}</div>
            </div>
            <TrendBadge trend={outcomeTrend} label="Egresos" />
          </div>
        </div>
      </div>

      {/* Main chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h2 className="font-semibold text-gray-800 mb-4">
          Tendencia {activeOption.label}
        </h2>

        {points.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
            No hay datos para el periodo seleccionado
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={points} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="intakeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
                <linearGradient id="outcomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="period_label"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  fontSize: "13px",
                }}
                labelStyle={{ fontWeight: 600 }}
                formatter={(value: number, name: string) => [
                  value,
                  name === "intake_count" ? "Ingresos" : "Egresos",
                ]}
              />
              <Legend
                formatter={(value: string) =>
                  value === "intake_count" ? "Ingresos" : "Egresos"
                }
              />
              <Area
                type="monotone"
                dataKey="intake_count"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#intakeGrad)"
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Area
                type="monotone"
                dataKey="outcome_count"
                stroke="#10b981"
                strokeWidth={2}
                fill="url(#outcomeGrad)"
                dot={false}
                activeDot={{ r: 4 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer note */}
      <p className="mt-4 text-xs text-gray-400">
        Los egresos se calculan a partir de adopciones registradas en el periodo. Los datos de
        tendencia usan la fecha de creacion del registro como punto de ingreso.
      </p>
    </div>
  );
}
