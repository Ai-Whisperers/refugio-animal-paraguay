"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Heart, PawPrint, Scissors, DollarSign, ArrowLeft, AlertCircle } from "lucide-react";
import type { ImpactResponse, MonthlyImpactItem } from "@/types/api";
import { getImpactStatistics } from "@/lib/public-api";
import ShareWidget from "@/components/ShareWidget";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  title: "Nuestro Impacto",
  subtitle:
    "Mira como tu apoyo transforma vidas. Estos datos muestran nuestro progreso durante los ultimos 12 meses.",
  totalRescued: "Animales Rescatados",
  totalAdopted: "Adopciones Completadas",
  totalCastrated: "Castraciones Realizadas",
  totalDonated: "Total Donado",
  chartRescued: "Animales rescatados por mes",
  chartDonations: "Donaciones por mes",
  chartAdoptions: "Adopciones por mes",
  chartCastrations: "Castraciones acumuladas",
  loading: "Cargando estadisticas...",
  errorTitle: "No se pudieron cargar las estadisticas",
  errorSubtitle: "Intenta nuevamente en unos minutos.",
  retry: "Reintentar",
  back: "Volver al inicio",
  shareTitle: "Mira el impacto del Refugio Animal Paraguay!",
  lastUpdated: "Ultima actualizacion",
  allTime: "historico",
} as const;

// ---------------------------------------------------------------------------
// Month label helpers
// ---------------------------------------------------------------------------

const MONTH_LABELS = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun",
  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
];

function monthLabel(item: MonthlyImpactItem): string {
  return `${MONTH_LABELS[item.month - 1]} ${String(item.year).slice(2)}`;
}

function formatCurrency(cents: number): string {
  const amount = cents / 100;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K`;
  return amount.toLocaleString("es-PY");
}

// ---------------------------------------------------------------------------
// Stat card component
// ---------------------------------------------------------------------------

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  return (
    <div className={`bg-white rounded-xl p-6 shadow-sm border border-gray-100`}>
      <div className={`inline-flex items-center justify-center h-12 w-12 rounded-lg mb-3 ${color}`}>
        {icon}
      </div>
      <p className="text-2xl sm:text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart components
// ---------------------------------------------------------------------------

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
}

function ChartCard({ title, children }: ChartCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-base font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="h-64">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom tooltip
// ---------------------------------------------------------------------------

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-md text-sm">
      <p className="font-medium text-gray-900 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }}>
          {entry.name}: {entry.value.toLocaleString("es-PY")}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function ImpactPage() {
  const [data, setData] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getImpactStatistics();
      setData(result);
    } catch {
      setError(S.errorTitle);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-r-transparent" />
        <p className="mt-3 text-gray-500">{S.loading}</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-4">
          <AlertCircle className="h-8 w-8 text-red-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{S.errorTitle}</h2>
        <p className="text-gray-500 mb-6">{S.errorSubtitle}</p>
        <button
          onClick={fetchData}
          className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
        >
          {S.retry}
        </button>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.months.map((m) => ({
    name: monthLabel(m),
    rescued: m.animals_rescued,
    adoptions: m.adoptions_completed,
    castrations: m.castrations_performed,
    donations: m.donations_total_cents / 100,
  }));

  // Cumulative castrations
  let cumulative = 0;
  const cumulativeData = data.months.map((m) => {
    cumulative += m.castrations_performed;
    return {
      name: monthLabel(m),
      total: cumulative,
    };
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
          {S.title}
        </h1>
        <p className="text-gray-500 max-w-2xl mx-auto mb-4">
          {S.subtitle}
        </p>
        <div className="flex items-center justify-center gap-3">
          <ShareWidget title={S.shareTitle} variant="inline" />
        </div>
      </div>

      {/* All-time summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <StatCard
          icon={<PawPrint className="h-6 w-6 text-blue-600" />}
          label={`${S.totalRescued} (${S.allTime})`}
          value={data.total_animals_rescued.toLocaleString("es-PY")}
          color="bg-blue-50"
        />
        <StatCard
          icon={<Heart className="h-6 w-6 text-orange-600" />}
          label={`${S.totalAdopted} (${S.allTime})`}
          value={data.total_adopted.toLocaleString("es-PY")}
          color="bg-orange-50"
        />
        <StatCard
          icon={<Scissors className="h-6 w-6 text-purple-600" />}
          label={`${S.totalCastrated} (${S.allTime})`}
          value={data.total_castrated.toLocaleString("es-PY")}
          color="bg-purple-50"
        />
        <StatCard
          icon={<DollarSign className="h-6 w-6 text-green-600" />}
          label={`${S.totalDonated} (${S.allTime})`}
          value={`Gs. ${formatCurrency(data.total_donations_cents)}`}
          color="bg-green-50"
        />
      </div>

      {/* Charts — 2x2 grid on desktop, stacked on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        {/* Animals rescued by month */}
        <ChartCard title={S.chartRescued}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="rescued"
                name="Rescatados"
                fill="#3B82F6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Donations by month */}
        <ChartCard title={S.chartDonations}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${formatCurrency(v * 100)}`} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="donations"
                name="Donaciones (Gs.)"
                stroke="#22C55E"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Adoptions by month */}
        <ChartCard title={S.chartAdoptions}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="adoptions"
                name="Adopciones"
                fill="#F97316"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Castrations cumulative */}
        <ChartCard title={S.chartCastrations}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cumulativeData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="total"
                name="Castraciones (acumulado)"
                stroke="#8B5CF6"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-400">
        <p>
          {S.lastUpdated}:{" "}
          {new Date(data.last_updated).toLocaleDateString("es-PY", {
            day: "numeric",
            month: "long",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>

      {/* Back link */}
      <div className="text-center mt-6">
        <Link
          href="/"
          className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          {S.back}
        </Link>
      </div>
    </div>
  );
}
