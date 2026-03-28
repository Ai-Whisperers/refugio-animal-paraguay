"use client";

import { useEffect, useState, useCallback } from "react";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Users,
  BarChart3,
  Globe,
  Repeat,
  Award,
  Target,
  ArrowRight,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DonationKPI {
  label: string;
  value: number;
  unit: string;
  change_percent: number | null;
  trend: string;
}

interface DonationSummary {
  total_amount_pyg: number;
  total_amount_eur: number;
  donation_count: number;
  unique_donors: number;
  average_donation_pyg: number;
  average_donation_eur: number;
  recurring_percentage: number;
  period_days: number;
  kpis: DonationKPI[];
}

interface MonthlyTrend {
  month: string;
  year: number;
  total_pyg: number;
  total_eur: number;
  count: number;
  average_pyg: number;
}

interface SourceBreakdown {
  source: string;
  label: string;
  amount_pyg: number;
  count: number;
  percentage: number;
}

interface CurrencyDistribution {
  currency: string;
  total_amount: number;
  count: number;
  percentage: number;
  average_amount: number;
}

interface TopDonor {
  rank: number;
  donor_name: string;
  total_donated_pyg: number;
  donation_count: number;
  last_donation_date: string;
  is_recurring: boolean;
}

interface CampaignPerformance {
  campaign_name: string;
  goal_pyg: number;
  raised_pyg: number;
  progress_percent: number;
  donor_count: number;
  status: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const formatPYG = (amount: number): string => {
  if (amount >= 1_000_000) {
    return `${(amount / 1_000_000).toFixed(1)}M`;
  }
  if (amount >= 1_000) {
    return `${(amount / 1_000).toFixed(0)}K`;
  }
  return amount.toLocaleString("es-PY");
};

const formatEUR = (amount: number): string =>
  new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(amount);

const PERIOD_OPTIONS = [
  { label: "30 dias", value: 30 },
  { label: "90 dias", value: 90 },
  { label: "180 dias", value: 180 },
  { label: "1 ano", value: 365 },
];

const SOURCE_COLORS: Record<string, string> = {
  online: "bg-blue-500",
  bank_transfer: "bg-green-500",
  sepa: "bg-purple-500",
  tigo_money: "bg-yellow-500",
  cash: "bg-orange-500",
  in_kind: "bg-pink-500",
};

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function KPICard({ kpi }: { kpi: DonationKPI }) {
  const TrendIcon = kpi.trend === "up" ? TrendingUp : kpi.trend === "down" ? TrendingDown : BarChart3;
  const trendColor = kpi.trend === "up" ? "text-green-600" : kpi.trend === "down" ? "text-red-600" : "text-gray-500";
  const displayValue = kpi.unit === "PYG" ? formatPYG(kpi.value) : kpi.unit === "EUR" ? formatEUR(kpi.value) : kpi.value.toLocaleString("es-PY");

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5" role="region" aria-label={kpi.label}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{kpi.label}</span>
        <TrendIcon className={`w-5 h-5 ${trendColor}`} aria-hidden="true" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{displayValue}</p>
      {kpi.change_percent !== null && (
        <p className={`text-sm mt-1 ${trendColor}`}>
          {kpi.change_percent > 0 ? "+" : ""}{kpi.change_percent}% vs periodo anterior
        </p>
      )}
    </div>
  );
}

function TrendChart({ trends }: { trends: MonthlyTrend[] }) {
  const maxAmount = Math.max(...trends.map((t) => t.total_pyg));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Tendencia de Donaciones</h2>
      <div className="flex items-end gap-3 h-48" role="img" aria-label="Grafico de tendencia de donaciones mensuales">
        {trends.map((t) => {
          const height = maxAmount > 0 ? (t.total_pyg / maxAmount) * 100 : 0;
          return (
            <div key={`${t.month}-${t.year}`} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-xs text-gray-500">{formatPYG(t.total_pyg)}</span>
              <div
                className="w-full bg-orange-500 rounded-t-md transition-all min-h-[4px]"
                style={{ height: `${height}%` }}
                aria-label={`${t.month} ${t.year}: ${formatPYG(t.total_pyg)} PYG`}
              />
              <span className="text-xs text-gray-600 font-medium">{t.month}</span>
              <span className="text-xs text-gray-400">{t.count} don.</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SourceChart({ sources }: { sources: SourceBreakdown[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Donaciones por Canal</h2>
      <div className="space-y-3" role="list" aria-label="Distribucion de donaciones por canal">
        {sources.map((s) => (
          <div key={s.source} className="flex items-center gap-3" role="listitem">
            <div className="w-28 text-sm text-gray-700 truncate">{s.label}</div>
            <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
              <div
                className={`h-full rounded-full ${SOURCE_COLORS[s.source] ?? "bg-gray-400"} transition-all`}
                style={{ width: `${s.percentage}%` }}
              />
            </div>
            <div className="w-20 text-right text-sm font-medium text-gray-900">
              {formatPYG(s.amount_pyg)}
            </div>
            <div className="w-12 text-right text-xs text-gray-500">{s.percentage}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CurrencyCards({ currencies }: { currencies: CurrencyDistribution[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Distribucion por Moneda</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4" role="list" aria-label="Distribucion por moneda">
        {currencies.map((c) => (
          <div key={c.currency} className="border border-gray-200 rounded-lg p-4" role="listitem">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-5 h-5 text-gray-400" aria-hidden="true" />
              <span className="font-semibold text-gray-900">{c.currency}</span>
              <span className="ml-auto text-sm text-gray-500">{c.percentage}%</span>
            </div>
            <p className="text-xl font-bold text-gray-900">
              {c.currency === "EUR" ? formatEUR(c.total_amount) : formatPYG(c.total_amount)}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {c.count} donaciones - Promedio: {c.currency === "EUR" ? formatEUR(c.average_amount) : formatPYG(c.average_amount)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopDonorsTable({ donors }: { donors: TopDonor[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <Award className="w-5 h-5 inline-block mr-2 text-orange-500" aria-hidden="true" />
        Top Donantes
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" aria-label="Ranking de principales donantes">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-2 text-gray-500 font-medium">#</th>
              <th className="text-left py-2 px-2 text-gray-500 font-medium">Donante</th>
              <th className="text-right py-2 px-2 text-gray-500 font-medium">Total (PYG)</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Donaciones</th>
              <th className="text-center py-2 px-2 text-gray-500 font-medium">Recurrente</th>
            </tr>
          </thead>
          <tbody>
            {donors.map((d) => (
              <tr key={d.rank} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-2 text-gray-400 font-medium">{d.rank}</td>
                <td className="py-2 px-2 text-gray-900 font-medium">{d.donor_name}</td>
                <td className="py-2 px-2 text-right font-medium text-gray-900">{formatPYG(d.total_donated_pyg)}</td>
                <td className="py-2 px-2 text-center text-gray-600">{d.donation_count}</td>
                <td className="py-2 px-2 text-center">
                  {d.is_recurring ? (
                    <span className="inline-flex items-center gap-1 text-green-600">
                      <Repeat className="w-4 h-4" aria-hidden="true" /> Si
                    </span>
                  ) : (
                    <span className="text-gray-400">No</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CampaignCards({ campaigns }: { campaigns: CampaignPerformance[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        <Target className="w-5 h-5 inline-block mr-2 text-orange-500" aria-hidden="true" />
        Rendimiento de Campanas
      </h2>
      <div className="space-y-4" role="list" aria-label="Rendimiento de campanas de donacion">
        {campaigns.map((c) => (
          <div key={c.campaign_name} className="border border-gray-200 rounded-lg p-4" role="listitem">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">{c.campaign_name}</h3>
              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${
                  c.status === "completed"
                    ? "bg-green-100 text-green-700"
                    : c.status === "active"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-700"
                }`}
              >
                {c.status === "completed" ? "Completada" : c.status === "active" ? "Activa" : c.status}
              </span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    c.progress_percent >= 100 ? "bg-green-500" : c.progress_percent >= 50 ? "bg-orange-500" : "bg-red-400"
                  }`}
                  style={{ width: `${Math.min(c.progress_percent, 100)}%` }}
                  role="progressbar"
                  aria-valuenow={c.progress_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${c.progress_percent}% del objetivo alcanzado`}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">{c.progress_percent}%</span>
            </div>
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>{formatPYG(c.raised_pyg)} / {formatPYG(c.goal_pyg)} PYG</span>
              <span>{c.donor_count} donantes</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Cargando analiticas de donaciones">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-200 rounded-xl h-28" />
        ))}
      </div>
      <div className="bg-gray-200 rounded-xl h-64" />
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

export default function DonationAnalyticsPage() {
  const [summary, setSummary] = useState<DonationSummary | null>(null);
  const [trends, setTrends] = useState<MonthlyTrend[]>([]);
  const [sources, setSources] = useState<SourceBreakdown[]>([]);
  const [currencies, setCurrencies] = useState<CurrencyDistribution[]>([]);
  const [topDonors, setTopDonors] = useState<TopDonor[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodDays, setPeriodDays] = useState(30);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, trendsRes, sourcesRes, currencyRes, donorsRes, campaignsRes] =
        await Promise.all([
          fetch(`${API_BASE}/api/admin/analytics/donations/summary?period_days=${periodDays}`),
          fetch(`${API_BASE}/api/admin/analytics/donations/trends?months=6`),
          fetch(`${API_BASE}/api/admin/analytics/donations/by-source?period_days=${periodDays}`),
          fetch(`${API_BASE}/api/admin/analytics/donations/by-currency?period_days=${periodDays}`),
          fetch(`${API_BASE}/api/admin/analytics/donations/top-donors?period_days=${periodDays}`),
          fetch(`${API_BASE}/api/admin/analytics/donations/campaigns`),
        ]);

      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (trendsRes.ok) {
        const tData = await trendsRes.json();
        setTrends(tData.months ?? []);
      }
      if (sourcesRes.ok) setSources(await sourcesRes.json());
      if (currencyRes.ok) setCurrencies(await currencyRes.json());
      if (donorsRes.ok) setTopDonors(await donorsRes.json());
      if (campaignsRes.ok) setCampaigns(await campaignsRes.json());
    } catch (err) {
      setError("Error al cargar los datos de donaciones");
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
            <DollarSign className="w-7 h-7 inline-block mr-2 text-orange-500" aria-hidden="true" />
            Analiticas de Donaciones
          </h1>
          <p className="text-gray-500 mt-1">Resumen y tendencias de donaciones recibidas</p>
        </div>
        <div className="flex gap-2" role="group" aria-label="Seleccionar periodo de tiempo">
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

      {/* KPI Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {summary.kpis.map((kpi) => (
            <KPICard key={kpi.label} kpi={kpi} />
          ))}
        </div>
      )}

      {/* Recurring & Average Stats */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4" role="region" aria-label="Porcentaje de donaciones recurrentes">
            <div className="flex items-center gap-2 mb-1">
              <Repeat className="w-5 h-5 text-green-500" aria-hidden="true" />
              <span className="text-sm text-gray-500">Recurrentes</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{summary.recurring_percentage}%</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4" role="region" aria-label="Promedio por donacion en guaranies">
            <div className="flex items-center gap-2 mb-1">
              <ArrowRight className="w-5 h-5 text-blue-500" aria-hidden="true" />
              <span className="text-sm text-gray-500">Promedio (PYG)</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{formatPYG(summary.average_donation_pyg)}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4" role="region" aria-label="Promedio por donacion en euros">
            <div className="flex items-center gap-2 mb-1">
              <ArrowRight className="w-5 h-5 text-purple-500" aria-hidden="true" />
              <span className="text-sm text-gray-500">Promedio (EUR)</span>
            </div>
            <p className="text-xl font-bold text-gray-900">{formatEUR(summary.average_donation_eur)}</p>
          </div>
        </div>
      )}

      {/* Trend Chart */}
      {trends.length > 0 && <div className="mb-6"><TrendChart trends={trends} /></div>}

      {/* Source & Currency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {sources.length > 0 && <SourceChart sources={sources} />}
        {currencies.length > 0 && <CurrencyCards currencies={currencies} />}
      </div>

      {/* Top Donors */}
      {topDonors.length > 0 && <div className="mb-6"><TopDonorsTable donors={topDonors} /></div>}

      {/* Campaign Performance */}
      {campaigns.length > 0 && <CampaignCards campaigns={campaigns} />}
    </div>
  );
}
