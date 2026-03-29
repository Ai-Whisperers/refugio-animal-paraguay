"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  CheckCircle,
  Download,
  DollarSign,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  PieChart,
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
  breakdown_by: string;
  lookback_days: number;
  period_from: string;
  period_to: string;
  total_donations: number;
  currency_totals: CurrencyTotal[];
  rows: SummaryRow[];
}

interface FundDashboard {
  total_donations_cents: number;
  total_allocated_cents: number;
  unallocated_cents: number;
  allocation_rate_pct: number;
  total_donation_count: number;
  pending_allocation_count: number;
  total_expenses_cents: number;
  by_target_type: TargetTypeBreakdown[];
}

interface TargetTypeBreakdown {
  target_type: string;
  count: number;
  total_cents: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const S = {
  title: "Reporte de Asignacion de Fondos",
  subtitle: "Comparativa de donaciones recibidas, asignadas y gastos por categoria",
  loading: "Cargando reporte financiero...",
  error: "Error al cargar los datos. Intente de nuevo.",
  refresh: "Actualizar",
  exportCsv: "Exportar CSV",
  generatedAt: "Generado:",
  period: "Periodo",
  currency: "Moneda",
  donations: "Donaciones",
  allocated: "Asignado",
  unallocated: "Sin Asignar",
  allocationRate: "Tasa de Asignacion",
  expenses: "Gastos",
  totalDonations: "Total Donaciones",
  byTargetType: "Distribucion por Tipo de Fondo",
  currencyBreakdown: "Desglose por Moneda",
  targetTypeLabels: {
    general: "General",
    animal: "Animal especifico",
    rescuer: "Rescatista",
    clinic: "Clinica",
    campaign: "Campana",
    need: "Necesidad",
    emergency: "Emergencia",
  } as Record<string, string>,
  currencyGrouping: "mensual",
} as const;

const GROUPING_OPTIONS = [
  { label: "Ultimos 30 dias", value: "daily", lookback: 30 },
  { label: "Ultimos 3 meses", value: "monthly", lookback: 90 },
  { label: "Ultimo ano", value: "monthly", lookback: 365 },
  { label: "Todos", value: "annual", lookback: 1825 },
] as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatPyg(cents: number): string {
  return new Intl.NumberFormat("es-PY").format(cents) + " Gs.";
}

function formatEur(cents: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(cents / 100);
}

function formatCurrency(cents: number, currency: string): string {
  if (currency === "PYG") return formatPyg(cents);
  if (currency === "EUR") return formatEur(cents);
  return `${(cents / 100).toFixed(2)} ${currency}`;
}

function pct(value: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((value / total) * 100);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 flex items-start gap-4">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-bold text-gray-800 mt-0.5">{value}</p>
      </div>
    </div>
  );
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const width = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="w-full bg-gray-100 rounded-full h-2.5">
      <div
        className={`h-2.5 rounded-full ${color}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function FinancialReportingPage() {
  const [summary, setSummary] = useState<DonationSummary | null>(null);
  const [fundDashboard, setFundDashboard] = useState<FundDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedGroupingIdx, setSelectedGroupingIdx] = useState(2);

  const selectedGrouping = GROUPING_OPTIONS[selectedGroupingIdx];

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, fundData] = await Promise.all([
        api.get<DonationSummary>(
          `/api/admin/financial-reporting/donation-summary?grouping=${selectedGrouping.value}&breakdown_by=currency&lookback_days=${selectedGrouping.lookback}`
        ),
        api.get<FundDashboard>("/admin/funds/dashboard"),
      ]);
      setSummary(summaryData);
      setFundDashboard(fundData);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`Error ${err.statusCode}: ${err.detail}`);
      } else {
        setError(S.error);
      }
    } finally {
      setLoading(false);
    }
  }, [selectedGrouping.value, selectedGrouping.lookback]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin mx-auto mb-3" />
          <p className="text-gray-600">{S.loading}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
          >
            {S.refresh}
          </button>
        </div>
      </div>
    );
  }

  const totalDonationsCents = fundDashboard?.total_donations_cents ?? 0;
  const allocatedCents = fundDashboard?.total_allocated_cents ?? 0;
  const unallocatedCents = fundDashboard?.unallocated_cents ?? 0;
  const expensesCents = fundDashboard?.total_expenses_cents ?? 0;
  const allocationRate = fundDashboard?.allocation_rate_pct ?? 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{S.title}</h1>
            <p className="text-sm text-gray-500 mt-1">{S.subtitle}</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Period selector */}
            <select
              value={selectedGroupingIdx}
              onChange={(e) => setSelectedGroupingIdx(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-indigo-500"
            >
              {GROUPING_OPTIONS.map((opt, idx) => (
                <option key={idx} value={idx}>
                  {opt.label}
                </option>
              ))}
            </select>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              {S.refresh}
            </button>
            <a
              href="/admin/funds/export"
              className="flex items-center gap-2 px-3 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Download className="w-4 h-4" />
              {S.exportCsv}
            </a>
          </div>
        </div>
        {summary && (
          <p className="text-xs text-gray-400 mt-2">
            {S.generatedAt} {new Date(summary.generated_at).toLocaleString("es-PY")} —{" "}
            {summary.period_from} al {summary.period_to}
          </p>
        )}
      </div>

      <div className="px-6 py-6 max-w-7xl mx-auto space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard
            icon={DollarSign}
            label={S.totalDonations}
            value={`${summary?.total_donations ?? 0} donaciones`}
            color="bg-indigo-500"
          />
          <KpiCard
            icon={CheckCircle}
            label={S.allocated}
            value={`${allocationRate.toFixed(1)}%`}
            color="bg-green-500"
          />
          <KpiCard
            icon={TrendingUp}
            label={S.unallocated}
            value={formatPyg(unallocatedCents)}
            color="bg-yellow-500"
          />
          <KpiCard
            icon={BarChart3}
            label={S.expenses}
            value={formatPyg(expensesCents)}
            color="bg-red-500"
          />
        </div>

        {/* Allocation Bar */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-indigo-500" />
            Distribucion de Fondos
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>{S.allocated}</span>
                <span>{formatPyg(allocatedCents)} ({pct(allocatedCents, totalDonationsCents)}%)</span>
              </div>
              <ProgressBar value={allocatedCents} max={totalDonationsCents} color="bg-green-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>{S.expenses}</span>
                <span>{formatPyg(expensesCents)} ({pct(expensesCents, totalDonationsCents)}%)</span>
              </div>
              <ProgressBar value={expensesCents} max={totalDonationsCents} color="bg-red-400" />
            </div>
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>{S.unallocated}</span>
                <span>{formatPyg(unallocatedCents)} ({pct(unallocatedCents, totalDonationsCents)}%)</span>
              </div>
              <ProgressBar value={unallocatedCents} max={totalDonationsCents} color="bg-yellow-400" />
            </div>
          </div>
        </div>

        {/* Currency breakdown + Target type breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Currency breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-indigo-500" />
              {S.currencyBreakdown}
            </h2>
            {summary && summary.currency_totals.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-2 font-medium">{S.currency}</th>
                      <th className="pb-2 font-medium text-right">{S.donations}</th>
                      <th className="pb-2 font-medium text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.currency_totals.map((ct) => (
                      <tr key={ct.currency} className="border-b border-gray-50">
                        <td className="py-2.5 font-medium text-gray-800">{ct.currency}</td>
                        <td className="py-2.5 text-right text-gray-600">{ct.donation_count}</td>
                        <td className="py-2.5 text-right font-semibold text-gray-800">
                          {ct.total_amount_display}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-6">Sin datos para este periodo</p>
            )}
          </div>

          {/* Target type breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-500" />
              {S.byTargetType}
            </h2>
            {fundDashboard && fundDashboard.by_target_type.length > 0 ? (
              <div className="space-y-3">
                {fundDashboard.by_target_type.map((item) => {
                  const widthPct = pct(item.total_cents, totalDonationsCents);
                  return (
                    <div key={item.target_type}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700">
                          {S.targetTypeLabels[item.target_type] ?? item.target_type}
                        </span>
                        <span className="text-gray-500">
                          {item.count} · {formatPyg(item.total_cents)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-indigo-500"
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-6">Sin datos disponibles</p>
            )}
          </div>
        </div>

        {/* Period breakdown table */}
        {summary && summary.rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-500" />
              Detalle por Periodo y Moneda
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 font-medium">{S.period}</th>
                    <th className="pb-2 font-medium">{S.currency}</th>
                    <th className="pb-2 font-medium text-right">{S.donations}</th>
                    <th className="pb-2 font-medium text-right">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.rows.map((row, i) => (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2.5 text-gray-700">{row.period_label}</td>
                      <td className="py-2.5 font-medium text-gray-800">{row.currency}</td>
                      <td className="py-2.5 text-right text-gray-600">{row.donation_count}</td>
                      <td className="py-2.5 text-right font-semibold text-gray-800">
                        {formatCurrency(row.total_amount_cents, row.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
