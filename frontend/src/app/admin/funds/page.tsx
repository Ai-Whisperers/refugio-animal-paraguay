"use client";

import { useEffect, useState, useCallback } from "react";
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Download,
  PieChart,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

const S = {
  title: "Panel de Gestion de Fondos",
  subtitle: "Monitoreo de donaciones, asignaciones y salud financiera",
  loading: "Cargando datos del panel...",
  error: "Error al cargar los datos. Intente de nuevo.",
  refresh: "Actualizar",
  exportCsv: "Exportar Reporte CSV",

  // Summary cards
  totalDonations: "Total Donaciones",
  totalAllocated: "Total Asignado",
  unallocated: "Sin Asignar",
  allocationRate: "Tasa de Asignacion",
  totalDonationCount: "Donaciones Recibidas",
  pendingAllocations: "Pendientes de Asignacion",
  expenses: "Gastos Registrados",

  // Sections
  byTargetType: "Donaciones por Tipo",
  fundHealth: "Salud del Fondo",
  trending: "Tendencia de Donaciones",
  trendDaily: "Diario",
  trendWeekly: "Semanal",
  trendMonthly: "Mensual",

  // Target type labels
  targetTypeLabels: {
    general: "General",
    animal: "Animal",
    rescuer: "Rescatista",
    clinic: "Clinica",
    campaign: "Campana",
    need: "Necesidad",
  } as Record<string, string>,

  // Health
  healthIcons: {
    healthy: "check",
    warning: "warn",
    critical: "alert",
  } as Record<string, string>,
} as const;

function formatEur(cents: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(cents / 100);
}

interface TargetTypeBreakdown {
  target_type: string;
  count: number;
  total_cents: number;
}

interface DashboardData {
  total_donations_cents: number;
  total_allocated_cents: number;
  unallocated_cents: number;
  allocation_rate: number;
  unallocated_count: number;
  total_expenses: number;
  by_target_type: TargetTypeBreakdown[];
  health_status: string;
  health_message: string;
  total_donation_count: number;
  pending_allocation_count: number;
}

interface TrendPoint {
  period: string;
  count: number;
  total_cents: number;
}

interface TrendData {
  granularity: string;
  data: TrendPoint[];
}

const TARGET_COLORS: Record<string, string> = {
  general: "bg-blue-500",
  animal: "bg-green-500",
  rescuer: "bg-purple-500",
  clinic: "bg-teal-500",
  campaign: "bg-orange-500",
  need: "bg-pink-500",
};

export default function FundDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [trending, setTrending] = useState<TrendData | null>(null);
  const [trendGranularity, setTrendGranularity] = useState<string>("daily");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashData, trendData] = await Promise.all([
        api.get<DashboardData>("/admin/funds/dashboard"),
        api.get<TrendData>(`/admin/funds/trending?granularity=${trendGranularity}&days=90`),
      ]);
      setDashboard(dashData);
      setTrending(trendData);
    } catch {
      setError(S.error);
    } finally {
      setLoading(false);
    }
  }, [trendGranularity]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleExport = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/admin/funds/export`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
          },
        }
      );
      if (!response.ok) return;
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "fund_report.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Silently fail — user can retry
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">{S.loading}</div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600 mb-4">{error ?? S.error}</p>
        <button
          onClick={fetchDashboard}
          className="text-teal-600 hover:underline"
        >
          {S.refresh}
        </button>
      </div>
    );
  }

  const maxTrendCents = trending
    ? Math.max(...trending.data.map((d) => d.total_cents), 1)
    : 1;
  const totalTargetCents = dashboard.by_target_type.reduce(
    (sum, t) => sum + t.total_cents,
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{S.title}</h1>
          <p className="text-sm text-gray-500 mt-1">{S.subtitle}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchDashboard}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4" />
            {S.refresh}
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700"
          >
            <Download className="h-4 w-4" />
            {S.exportCsv}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard
          label={S.totalDonations}
          value={formatEur(dashboard.total_donations_cents)}
          icon={<DollarSign className="h-5 w-5 text-green-500" />}
        />
        <SummaryCard
          label={S.totalAllocated}
          value={formatEur(dashboard.total_allocated_cents)}
          icon={<CheckCircle className="h-5 w-5 text-blue-500" />}
        />
        <SummaryCard
          label={S.unallocated}
          value={formatEur(dashboard.unallocated_cents)}
          icon={<AlertTriangle className="h-5 w-5 text-amber-500" />}
        />
        <SummaryCard
          label={S.allocationRate}
          value={`${dashboard.allocation_rate.toFixed(1)}%`}
          icon={<TrendingUp className="h-5 w-5 text-teal-500" />}
          highlight={dashboard.allocation_rate >= 80}
        />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label={S.totalDonationCount} value={dashboard.total_donation_count} />
        <StatCard label={S.pendingAllocations} value={dashboard.pending_allocation_count} />
        <StatCard label={S.expenses} value={dashboard.total_expenses} />
      </div>

      {/* Fund Health */}
      <div
        className={`rounded-xl border p-5 ${
          dashboard.health_status === "healthy"
            ? "bg-green-50 border-green-200"
            : dashboard.health_status === "warning"
            ? "bg-amber-50 border-amber-200"
            : "bg-red-50 border-red-200"
        }`}
      >
        <div className="flex items-start gap-3">
          {dashboard.health_status === "healthy" ? (
            <CheckCircle className="h-6 w-6 text-green-500 mt-0.5" />
          ) : dashboard.health_status === "warning" ? (
            <AlertTriangle className="h-6 w-6 text-amber-500 mt-0.5" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-red-500 mt-0.5" />
          )}
          <div>
            <h3 className="font-semibold text-gray-900">{S.fundHealth}</h3>
            <p className="text-sm text-gray-700 mt-1">{dashboard.health_message}</p>
          </div>
        </div>
      </div>

      {/* Target Type Breakdown */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center gap-2 mb-4">
          <PieChart className="h-5 w-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900">{S.byTargetType}</h2>
        </div>
        <div className="space-y-3">
          {dashboard.by_target_type.map((item) => {
            const pct = totalTargetCents > 0 ? (item.total_cents / totalTargetCents) * 100 : 0;
            return (
              <div key={item.target_type}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">
                    {S.targetTypeLabels[item.target_type] ?? item.target_type}
                  </span>
                  <span className="text-gray-500">
                    {formatEur(item.total_cents)} ({item.count})
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${TARGET_COLORS[item.target_type] ?? "bg-gray-400"}`}
                    style={{ width: `${Math.max(pct, 1)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Donation Trending */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900">{S.trending}</h2>
          </div>
          <div className="flex gap-1">
            {(["daily", "weekly", "monthly"] as const).map((g) => (
              <button
                key={g}
                onClick={() => setTrendGranularity(g)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                  trendGranularity === g
                    ? "bg-teal-100 text-teal-700"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                {g === "daily" ? S.trendDaily : g === "weekly" ? S.trendWeekly : S.trendMonthly}
              </button>
            ))}
          </div>
        </div>

        {trending && trending.data.length > 0 ? (
          <div className="space-y-2">
            {trending.data.slice(-20).map((point) => {
              const pct = (point.total_cents / maxTrendCents) * 100;
              return (
                <div key={point.period} className="flex items-center gap-3">
                  <span className="text-xs text-gray-500 w-24 text-right font-mono">
                    {point.period}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 relative">
                    <div
                      className="bg-teal-500 h-4 rounded-full"
                      style={{ width: `${Math.max(pct, 1)}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-600 w-24 font-mono">
                    {formatEur(point.total_cents)}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-sm text-center py-8">
            No hay datos de tendencia disponibles.
          </p>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon,
  highlight = false,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border p-5 ${
        highlight ? "ring-2 ring-teal-200" : ""
      }`}
    >
      <div className="flex items-center gap-3 mb-2">{icon}</div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
      <p className="text-xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}
