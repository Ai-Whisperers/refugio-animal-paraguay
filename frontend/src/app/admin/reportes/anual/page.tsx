"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  BarChart3,
  Calendar,
  Download,
  DollarSign,
  Heart,
  Loader2,
  PawPrint,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Users,
} from "lucide-react";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MonthlyEntry {
  month: number;
  month_name: string;
  income_cents: number;
  expenses_cents: number;
  net_cents: number;
}

interface CategoryEntry {
  category: string;
  amount_cents: number;
  percentage: number;
}

interface DonorMetrics {
  total_donors: number;
  new_donors: number;
  recurring_donors: number;
  average_donation_cents: number;
}

interface AnimalOutcomes {
  rescued: number;
  adopted: number;
  castrated: number;
  treated: number;
}

interface Efficiency {
  direct_care_percentage: number;
  admin_percentage: number;
  direct_care_cents: number;
  admin_cents: number;
}

interface AnnualReport {
  year: number;
  generated_at: string;
  generated_by: string;
  total_income_cents: number;
  total_expenses_cents: number;
  net_result_cents: number;
  currency: string;
  income_by_source: Record<string, number>;
  expense_categories: CategoryEntry[];
  monthly_breakdown: MonthlyEntry[];
  donor_metrics: DonorMetrics;
  animal_outcomes: AnimalOutcomes;
  efficiency: Efficiency;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function formatPYG(cents: number): string {
  return new Intl.NumberFormat("es-PY", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents) + " PYG";
}

function currentYear(): number {
  return new Date().getFullYear();
}

// ---------------------------------------------------------------------------
// Canvas bar chart helper
// ---------------------------------------------------------------------------

function drawBarChart(
  canvas: HTMLCanvasElement,
  labels: string[],
  incomeData: number[],
  expenseData: number[],
): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;
  const padLeft = 80;
  const padBottom = 40;
  const padTop = 20;
  const padRight = 20;
  const chartW = w - padLeft - padRight;
  const chartH = h - padBottom - padTop;

  ctx.clearRect(0, 0, w, h);

  const maxVal = Math.max(...incomeData, ...expenseData, 1);
  const barGroupW = chartW / labels.length;
  const barW = Math.max(4, barGroupW * 0.35);

  // Y-axis grid lines
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padTop + chartH - (i / 4) * chartH;
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(padLeft + chartW, y);
    ctx.stroke();

    const label = formatPYG(Math.round((maxVal * i) / 4));
    ctx.fillStyle = "#6b7280";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(label, padLeft - 6, y + 4);
  }

  // Bars
  labels.forEach((label, idx) => {
    const groupX = padLeft + idx * barGroupW + barGroupW * 0.1;

    const incomeH = (incomeData[idx] / maxVal) * chartH;
    ctx.fillStyle = "#10b981";
    ctx.fillRect(groupX, padTop + chartH - incomeH, barW, incomeH);

    const expenseH = (expenseData[idx] / maxVal) * chartH;
    ctx.fillStyle = "#ef4444";
    ctx.fillRect(groupX + barW + 2, padTop + chartH - expenseH, barW, expenseH);

    // X label
    ctx.fillStyle = "#6b7280";
    ctx.font = "9px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label.substring(0, 3), groupX + barW, padTop + chartH + 16);
  });

  // Legend
  ctx.fillStyle = "#10b981";
  ctx.fillRect(padLeft, h - 14, 12, 10);
  ctx.fillStyle = "#374151";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("Ingresos", padLeft + 16, h - 5);

  ctx.fillStyle = "#ef4444";
  ctx.fillRect(padLeft + 90, h - 14, 12, 10);
  ctx.fillStyle = "#374151";
  ctx.fillText("Gastos", padLeft + 106, h - 5);
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  color: string;
}

function StatCard({ icon, label, value, sub, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-start gap-3">
      <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-semibold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function AnualReportPage() {
  const [year, setYear] = useState<number>(currentYear());
  const [report, setReport] = useState<AnnualReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const loadReport = useCallback(async (targetYear: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<AnnualReport>("/api/admin/reports/annual", {
        year: targetYear,
        admin_name: "Staff",
      });
      setReport(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`Error ${err.statusCode}: ${err.detail}`);
      } else {
        setError("No se pudo cargar el reporte anual.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReport(year);
  }, [year, loadReport]);

  useEffect(() => {
    if (!report || !canvasRef.current) return;
    const labels = report.monthly_breakdown.map((m) => m.month_name);
    const income = report.monthly_breakdown.map((m) => m.income_cents);
    const expenses = report.monthly_breakdown.map((m) => m.expenses_cents);
    drawBarChart(canvasRef.current, labels, income, expenses);
  }, [report]);

  const availableYears = Array.from({ length: 6 }, (_, i) => currentYear() - i);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reporte Anual de Impacto</h1>
          <p className="text-sm text-gray-500 mt-1">
            Resumen financiero, donantes y resultados del año seleccionado
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            aria-label="Seleccionar año"
          >
            {availableYears.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
          <button
            onClick={() => loadReport(year)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Actualizar
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !report && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {report && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<DollarSign className="h-5 w-5 text-green-600" />}
              label="Total ingresos"
              value={formatPYG(report.total_income_cents)}
              sub={`${report.currency}`}
              color="bg-green-50"
            />
            <StatCard
              icon={<TrendingDown className="h-5 w-5 text-red-500" />}
              label="Total gastos"
              value={formatPYG(report.total_expenses_cents)}
              color="bg-red-50"
            />
            <StatCard
              icon={
                report.net_result_cents >= 0 ? (
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-orange-500" />
                )
              }
              label="Resultado neto"
              value={formatPYG(report.net_result_cents)}
              color={report.net_result_cents >= 0 ? "bg-blue-50" : "bg-orange-50"}
            />
            <StatCard
              icon={<Users className="h-5 w-5 text-purple-600" />}
              label="Total donantes"
              value={String(report.donor_metrics.total_donors)}
              sub={`${report.donor_metrics.new_donors} nuevos este año`}
              color="bg-purple-50"
            />
          </div>

          {/* Animal outcomes */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={<PawPrint className="h-5 w-5 text-amber-600" />}
              label="Animales rescatados"
              value={String(report.animal_outcomes.rescued)}
              color="bg-amber-50"
            />
            <StatCard
              icon={<Heart className="h-5 w-5 text-pink-600" />}
              label="Adopciones"
              value={String(report.animal_outcomes.adopted)}
              color="bg-pink-50"
            />
            <StatCard
              icon={<Users className="h-5 w-5 text-teal-600" />}
              label="Donantes recurrentes"
              value={String(report.donor_metrics.recurring_donors)}
              color="bg-teal-50"
            />
            <StatCard
              icon={<BarChart3 className="h-5 w-5 text-indigo-600" />}
              label="Donación promedio"
              value={formatPYG(report.donor_metrics.average_donation_cents)}
              color="bg-indigo-50"
            />
          </div>

          {/* Monthly chart */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              Ingresos vs Gastos por Mes — {year}
            </h2>
            <canvas
              ref={canvasRef}
              width={800}
              height={260}
              className="w-full h-auto"
              aria-label="Gráfico de ingresos y gastos mensuales"
            />
          </div>

          {/* Expense categories + income by source */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="text-base font-semibold text-gray-900 mb-3">
                Gastos por Categoría
              </h2>
              {report.expense_categories.length === 0 ? (
                <p className="text-sm text-gray-400">Sin datos para este período</p>
              ) : (
                <ul className="space-y-2">
                  {report.expense_categories.map((cat) => (
                    <li key={cat.category} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-gray-700">{cat.category}</span>
                      <span className="font-medium text-gray-900">
                        {formatPYG(cat.amount_cents)}{" "}
                        <span className="text-gray-400 text-xs">({cat.percentage.toFixed(1)}%)</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="text-base font-semibold text-gray-900 mb-3">
                Ingresos por Fuente
              </h2>
              {Object.keys(report.income_by_source).length === 0 ? (
                <p className="text-sm text-gray-400">Sin datos para este período</p>
              ) : (
                <ul className="space-y-2">
                  {Object.entries(report.income_by_source).map(([source, cents]) => (
                    <li key={source} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-gray-700">{source}</span>
                      <span className="font-medium text-gray-900">{formatPYG(cents)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Efficiency */}
          {(report.efficiency.direct_care_percentage > 0 ||
            report.efficiency.admin_percentage > 0) && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="text-base font-semibold text-gray-900 mb-3">
                Eficiencia Financiera
              </h2>
              <div className="flex gap-8">
                <div>
                  <p className="text-xs text-gray-500">Atención directa</p>
                  <p className="text-2xl font-bold text-green-600">
                    {report.efficiency.direct_care_percentage.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Administración</p>
                  <p className="text-2xl font-bold text-gray-600">
                    {report.efficiency.admin_percentage.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* CSV Downloads */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Download className="h-4 w-4 text-gray-500" />
              Exportar CSV
            </h2>
            <div className="flex flex-wrap gap-3">
              {[
                { label: "Resumen", path: "summary" },
                { label: "Gastos", path: "expenses" },
                { label: "Mensual", path: "monthly" },
                { label: "Campañas", path: "campaigns" },
              ].map(({ label, path }) => (
                <a
                  key={path}
                  href={`${API_BASE}/api/admin/reports/annual/${year}/csv/${path}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
                  download
                >
                  <Download className="h-3 w-3" />
                  {label}
                </a>
              ))}
            </div>
          </div>

          <p className="text-xs text-gray-400">
            Generado: {new Date(report.generated_at).toLocaleString("es-PY")} · {report.generated_by}
          </p>
        </>
      )}
    </div>
  );
}
