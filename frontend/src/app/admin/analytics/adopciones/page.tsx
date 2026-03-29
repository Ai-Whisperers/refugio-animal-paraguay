"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Heart,
  TrendingUp,
  TrendingDown,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Star,
  Users,
  RefreshCw,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OutcomeStats {
  total_completed_adoptions: number;
  total_returned: number;
  success_rate_pct: number;
  return_rate_by_species: Record<string, number>;
  average_welfare_score: number | null;
  average_satisfaction_score: number | null;
}

interface ReturnAnalytics {
  total_returns: number;
  by_condition: Record<string, number>;
  emergency_count: number;
  emergency_pct: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SPECIES_LABELS: Record<string, string> = {
  dog: "Perro",
  cat: "Gato",
  rabbit: "Conejo",
  bird: "Ave",
  other: "Otro",
};

const CONDITION_LABELS: Record<string, string> = {
  healthy: "Saludable",
  injured: "Lesionado",
  sick: "Enfermo",
  deceased: "Fallecido",
};

const CONDITION_COLORS: Record<string, string> = {
  healthy: "bg-green-500",
  injured: "bg-yellow-500",
  sick: "bg-orange-500",
  deceased: "bg-red-500",
};

function scoreColor(score: number): string {
  if (score >= 4) return "text-green-600";
  if (score >= 3) return "text-yellow-600";
  return "text-red-600";
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  iconColor,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  iconColor: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5" role="region" aria-label={label}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{label}</span>
        <Icon className={`w-5 h-5 ${iconColor}`} aria-hidden="true" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-sm text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function ScoreCard({
  label,
  score,
  description,
}: {
  label: string;
  score: number | null;
  description: string;
}) {
  const display = score !== null ? score.toFixed(1) : "—";
  const color = score !== null ? scoreColor(score) : "text-gray-400";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5" role="region" aria-label={label}>
      <div className="flex items-center gap-2 mb-2">
        <Star className="w-5 h-5 text-yellow-500" aria-hidden="true" />
        <span className="text-sm text-gray-500">{label}</span>
      </div>
      <p className={`text-3xl font-bold ${color}`}>{display}</p>
      <p className="text-xs text-gray-400 mt-1">{description}</p>
    </div>
  );
}

function SuccessRateGauge({ rate }: { rate: number }) {
  const returnRate = Math.round(100 - rate);
  const successRate = Math.round(rate);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <Heart className="w-5 h-5 inline-block mr-2 text-rose-500" aria-hidden="true" />
        Tasa de Exito de Adopciones
      </h2>
      <div
        className="flex rounded-full overflow-hidden h-8 mb-4"
        role="img"
        aria-label={`${successRate}% adopciones exitosas, ${returnRate}% devueltas`}
      >
        <div
          className="bg-green-500 flex items-center justify-center text-white text-xs font-bold transition-all"
          style={{ width: `${successRate}%` }}
        >
          {successRate >= 15 ? `${successRate}%` : ""}
        </div>
        <div
          className="bg-red-400 flex items-center justify-center text-white text-xs font-bold transition-all"
          style={{ width: `${returnRate}%` }}
        >
          {returnRate >= 10 ? `${returnRate}%` : ""}
        </div>
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" aria-hidden="true" />
          <span className="text-sm text-gray-700">Exitosas: <span className="font-bold text-green-700">{successRate}%</span></span>
        </div>
        <div className="flex items-center gap-2">
          <XCircle className="w-5 h-5 text-red-400" aria-hidden="true" />
          <span className="text-sm text-gray-700">Devueltas: <span className="font-bold text-red-600">{returnRate}%</span></span>
        </div>
      </div>
    </div>
  );
}

function ReturnBySpecies({ speciesData }: { speciesData: Record<string, number> }) {
  const entries = Object.entries(speciesData).sort(([, a], [, b]) => b - a);

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Tasa de Devolucion por Especie</h2>
        <p className="text-sm text-gray-400 text-center py-4">Sin datos disponibles</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <BarChart3 className="w-5 h-5 inline-block mr-2 text-orange-500" aria-hidden="true" />
        Tasa de Devolucion por Especie
      </h2>
      <div className="space-y-3" role="list" aria-label="Tasas de devolucion por especie animal">
        {entries.map(([species, rate]) => (
          <div key={species} className="flex items-center gap-3" role="listitem">
            <div className="w-20 text-sm text-gray-700 capitalize">
              {SPECIES_LABELS[species] ?? species}
            </div>
            <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  rate >= 20 ? "bg-red-500" : rate >= 10 ? "bg-yellow-500" : "bg-green-500"
                }`}
                style={{ width: `${Math.min(rate, 100)}%` }}
                role="progressbar"
                aria-valuenow={rate}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${SPECIES_LABELS[species] ?? species}: ${rate}%`}
              />
            </div>
            <div className="w-12 text-right text-sm font-medium text-gray-900">{rate}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReturnConditionBreakdown({ analytics }: { analytics: ReturnAnalytics }) {
  const total = analytics.total_returns;
  const entries = Object.entries(analytics.by_condition).sort(([, a], [, b]) => b - a);

  if (total === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Estado de Animales Devueltos</h2>
        <p className="text-sm text-gray-400 text-center py-4">Sin devoluciones registradas</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Estado de Animales Devueltos
        {analytics.emergency_count > 0 && (
          <span className="ml-2 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
            <AlertTriangle className="w-3 h-3" aria-hidden="true" />
            {analytics.emergency_count} emergencia{analytics.emergency_count > 1 ? "s" : ""}
          </span>
        )}
      </h2>
      <div className="space-y-3" role="list" aria-label="Estado de los animales devueltos">
        {entries.map(([condition, count]) => {
          const pct = total > 0 ? Math.round((count / total) * 100) : 0;
          return (
            <div key={condition} className="flex items-center gap-3" role="listitem">
              <div className="w-24 text-sm text-gray-700">
                {CONDITION_LABELS[condition] ?? condition}
              </div>
              <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${CONDITION_COLORS[condition] ?? "bg-gray-400"}`}
                  style={{ width: `${pct}%` }}
                  role="progressbar"
                  aria-valuenow={pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${CONDITION_LABELS[condition] ?? condition}: ${count} (${pct}%)`}
                />
              </div>
              <div className="w-10 text-right text-sm text-gray-500">{count}</div>
              <div className="w-10 text-right text-xs text-gray-400">{pct}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Cargando analiticas de adopciones">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-200 rounded-xl h-28" />
        ))}
      </div>
      <div className="bg-gray-200 rounded-xl h-24" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-200 rounded-xl h-56" />
        <div className="bg-gray-200 rounded-xl h-56" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AdoptionAnalyticsPage() {
  const [outcomeStats, setOutcomeStats] = useState<OutcomeStats | null>(null);
  const [returnAnalytics, setReturnAnalytics] = useState<ReturnAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [outcomesRes, returnsRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/follow-ups/analytics/outcomes`),
        fetch(`${API_BASE}/api/admin/returns/analytics`),
      ]);

      if (outcomesRes.ok) {
        setOutcomeStats(await outcomesRes.json());
      }
      if (returnsRes.ok) {
        setReturnAnalytics(await returnsRes.json());
      }
    } catch {
      setError("Error al cargar los datos de adopciones");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <LoadingSkeleton />;

  const successfulCount = outcomeStats
    ? outcomeStats.total_completed_adoptions - outcomeStats.total_returned
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            <Heart className="w-7 h-7 inline-block mr-2 text-rose-500" aria-hidden="true" />
            Analiticas de Adopciones
          </h1>
          <p className="text-gray-500 mt-1">Tasas de exito, devoluciones y bienestar animal</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 min-h-[44px] transition-colors"
          aria-label="Actualizar datos"
        >
          <RefreshCw className="w-4 h-4" aria-hidden="true" />
          Actualizar
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6" role="alert">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      {outcomeStats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            label="Adopciones con Seguimiento"
            value={outcomeStats.total_completed_adoptions.toLocaleString("es-PY")}
            sub="Total con follow-ups"
            icon={Users}
            iconColor="text-blue-500"
          />
          <StatCard
            label="Adopciones Exitosas"
            value={successfulCount.toLocaleString("es-PY")}
            sub={`${Math.round(outcomeStats.success_rate_pct)}% del total`}
            icon={CheckCircle}
            iconColor="text-green-500"
          />
          <StatCard
            label="Devoluciones"
            value={outcomeStats.total_returned.toLocaleString("es-PY")}
            sub={`${Math.round(100 - outcomeStats.success_rate_pct)}% del total`}
            icon={TrendingDown}
            iconColor="text-red-500"
          />
          <StatCard
            label="Tasa de Exito"
            value={`${outcomeStats.success_rate_pct.toFixed(1)}%`}
            sub={returnAnalytics ? `${returnAnalytics.emergency_count} emergencias` : undefined}
            icon={outcomeStats.success_rate_pct >= 80 ? TrendingUp : TrendingDown}
            iconColor={outcomeStats.success_rate_pct >= 80 ? "text-green-500" : "text-yellow-500"}
          />
        </div>
      )}

      {/* Success Rate Gauge */}
      {outcomeStats && (
        <div className="mb-6">
          <SuccessRateGauge rate={outcomeStats.success_rate_pct} />
        </div>
      )}

      {/* Score Cards */}
      {outcomeStats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <ScoreCard
            label="Puntuacion de Bienestar Animal"
            score={outcomeStats.average_welfare_score}
            description="Promedio de encuestas completadas (1–5)"
          />
          <ScoreCard
            label="Satisfaccion del Adoptante"
            score={outcomeStats.average_satisfaction_score}
            description="Promedio de encuestas completadas (1–5)"
          />
        </div>
      )}

      {/* Species breakdown + Return conditions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {outcomeStats && (
          <ReturnBySpecies speciesData={outcomeStats.return_rate_by_species} />
        )}
        {returnAnalytics && (
          <ReturnConditionBreakdown analytics={returnAnalytics} />
        )}
      </div>
    </div>
  );
}
