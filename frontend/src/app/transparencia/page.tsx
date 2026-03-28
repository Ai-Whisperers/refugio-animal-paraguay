"use client";

import { useState, useEffect, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REFRESH_INTERVAL_MS = 3_600_000; // 1 hour

const CATEGORY_COLORS: Record<string, string> = {
  medical: "#E74C3C",
  food: "#F39C12",
  shelter: "#3498DB",
  rescue: "#2ECC71",
  operations: "#9B59B6",
  transport: "#1ABC9C",
  administration: "#95A5A6",
};

const INCOME_COLOR = "#3B82F6";
const EXPENSE_COLOR = "#EF4444";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CurrencyAmount {
  pyg: number;
  usd: number;
}

interface MetricCard {
  label_es: string;
  label_en: string;
  amount: CurrencyAmount;
}

interface CategoryBreakdown {
  category: string;
  label_es: string;
  amount_pyg: number;
  percentage: number;
}

interface MonthlyComparison {
  month: number;
  month_label: string;
  income_pyg: number;
  expenses_pyg: number;
  net_pyg: number;
}

interface FinancialStats {
  generated_at: string;
  cache_ttl_seconds: number;
  year: number;
  disclaimer_es: string;
  metrics: MetricCard[];
  expense_categories: CategoryBreakdown[];
  monthly_comparison: MonthlyComparison[];
  last_updated: string;
}

// ---------------------------------------------------------------------------
// Formatting helpers
// ---------------------------------------------------------------------------

function formatPYG(amount: number): string {
  return new Intl.NumberFormat("es-PY", {
    style: "currency",
    currency: "PYG",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatUSD(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(amount);
}

// ---------------------------------------------------------------------------
// MetricCards component
// ---------------------------------------------------------------------------

function MetricCards({ metrics }: { metrics: MetricCard[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label_es}
          className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
        >
          <p className="text-sm text-gray-500 font-medium">{metric.label_es}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {formatPYG(metric.amount.pyg)}
          </p>
          <p className="text-sm text-gray-400 mt-0.5">
            {formatUSD(metric.amount.usd)}
          </p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CategoryPieChart — CSS-based pie visualization
// ---------------------------------------------------------------------------

function CategoryPieChart({ categories }: { categories: CategoryBreakdown[] }) {
  // Build conic-gradient segments
  let cumulativePercent = 0;
  const gradientSegments = categories.map((cat) => {
    const start = cumulativePercent;
    cumulativePercent += cat.percentage;
    const color = CATEGORY_COLORS[cat.category] ?? "#CBD5E1";
    return `${color} ${start}% ${cumulativePercent}%`;
  });
  const gradient = `conic-gradient(${gradientSegments.join(", ")})`;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Gastos por Categoria
      </h2>
      <div className="flex flex-col md:flex-row items-center gap-6">
        <div
          className="w-48 h-48 rounded-full flex-shrink-0"
          style={{ background: gradient }}
          role="img"
          aria-label="Grafico circular de gastos por categoria"
        />
        <ul className="space-y-2 w-full" role="list">
          {categories.map((cat) => (
            <li key={cat.category} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full inline-block flex-shrink-0"
                  style={{
                    backgroundColor: CATEGORY_COLORS[cat.category] ?? "#CBD5E1",
                  }}
                  aria-hidden="true"
                />
                <span className="text-sm text-gray-700">{cat.label_es}</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-medium text-gray-900">
                  {cat.percentage.toFixed(1)}%
                </span>
                <span className="text-xs text-gray-400 ml-2">
                  {formatPYG(cat.amount_pyg)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MonthlyBarChart — CSS-based bar chart
// ---------------------------------------------------------------------------

function MonthlyBarChart({ months }: { months: MonthlyComparison[] }) {
  const maxAmount = Math.max(
    ...months.map((m) => Math.max(m.income_pyg, m.expenses_pyg)),
    1
  );

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Ingresos vs Gastos Mensuales
      </h2>
      <div className="flex items-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-1.5">
          <span
            className="w-3 h-3 rounded-sm inline-block"
            style={{ backgroundColor: INCOME_COLOR }}
            aria-hidden="true"
          />
          <span className="text-gray-600">Ingresos</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className="w-3 h-3 rounded-sm inline-block"
            style={{ backgroundColor: EXPENSE_COLOR }}
            aria-hidden="true"
          />
          <span className="text-gray-600">Gastos</span>
        </div>
      </div>
      <div
        className="flex items-end gap-1 sm:gap-2 h-48 overflow-x-auto"
        role="img"
        aria-label="Grafico de barras de ingresos vs gastos mensuales"
      >
        {months.map((m) => {
          const incomeHeight = (m.income_pyg / maxAmount) * 100;
          const expenseHeight = (m.expenses_pyg / maxAmount) * 100;
          return (
            <div
              key={m.month}
              className="flex flex-col items-center flex-1 min-w-[2rem]"
            >
              <div className="flex items-end gap-0.5 h-40 w-full">
                <div
                  className="flex-1 rounded-t-sm transition-all"
                  style={{
                    height: `${incomeHeight}%`,
                    backgroundColor: INCOME_COLOR,
                    minHeight: m.income_pyg > 0 ? "2px" : "0",
                  }}
                  title={`${m.month_label} Ingresos: ${formatPYG(m.income_pyg)}`}
                />
                <div
                  className="flex-1 rounded-t-sm transition-all"
                  style={{
                    height: `${expenseHeight}%`,
                    backgroundColor: EXPENSE_COLOR,
                    minHeight: m.expenses_pyg > 0 ? "2px" : "0",
                  }}
                  title={`${m.month_label} Gastos: ${formatPYG(m.expenses_pyg)}`}
                />
              </div>
              <span className="text-xs text-gray-500 mt-1">{m.month_label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-label="Cargando datos financieros">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-200 rounded-xl h-28" />
        ))}
      </div>
      <div className="bg-gray-200 rounded-xl h-64" />
      <div className="bg-gray-200 rounded-xl h-64" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error state
// ---------------------------------------------------------------------------

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      className="bg-red-50 border border-red-200 rounded-xl p-6 text-center"
      role="alert"
    >
      <p className="text-red-700 font-medium">Error al cargar datos financieros</p>
      <p className="text-red-500 text-sm mt-1">{message}</p>
      <button
        onClick={onRetry}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors min-h-[44px] min-w-[44px]"
      >
        Reintentar
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TransparenciaPage() {
  const [stats, setStats] = useState<FinancialStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/stats/financial`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data: FinancialStats = await response.json();
      setStats(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStats]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:py-12">
      {/* Page header */}
      <header className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          Transparencia Financiera
        </h1>
        <p className="text-gray-500 mt-2 text-lg">
          Conoce como utilizamos cada donacion para ayudar a los animales.
        </p>
      </header>

      {/* Content */}
      {isLoading && !stats ? (
        <LoadingSkeleton />
      ) : error && !stats ? (
        <ErrorState message={error} onRetry={fetchStats} />
      ) : stats ? (
        <div className="space-y-6">
          {/* Key metrics */}
          <section aria-label="Metricas principales">
            <MetricCards metrics={stats.metrics} />
          </section>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <section aria-label="Gastos por categoria">
              <CategoryPieChart categories={stats.expense_categories} />
            </section>
            <section aria-label="Comparacion mensual">
              <MonthlyBarChart months={stats.monthly_comparison} />
            </section>
          </div>

          {/* Current month breakdown */}
          <section
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
            aria-label="Desglose del mes actual"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Desglose del Mes Actual
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {stats.metrics.slice(0, 3).map((metric) => (
                <div key={metric.label_es} className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">{metric.label_es}</p>
                  <p className="text-xl font-bold text-gray-900 mt-1">
                    {formatPYG(metric.amount.pyg)}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Disclaimer and last updated */}
          <footer className="text-center text-sm text-gray-400 space-y-1 pt-4 border-t border-gray-100">
            <p>{stats.disclaimer_es}</p>
            <p>
              Ultima actualizacion: {stats.last_updated}
            </p>
          </footer>
        </div>
      ) : null}
    </div>
  );
}
