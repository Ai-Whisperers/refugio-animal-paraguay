"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Stethoscope,
  Syringe,
  Scissors,
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertTriangle,
  PawPrint,
  Activity,
  Calendar,
  BarChart3,
} from "lucide-react";

// --- Constants ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const PERIOD_OPTIONS = [
  { value: 30, label: "30 días" },
  { value: 60, label: "60 días" },
  { value: 90, label: "90 días" },
  { value: 180, label: "6 meses" },
  { value: 365, label: "1 año" },
];

const CHART_COLORS = [
  "#E8622A", "#2A7E62", "#3B82F6", "#8B5CF6",
  "#F59E0B", "#EF4444", "#06B6D4", "#84CC16",
];

// --- Types ---
interface VetSummary {
  total_treatments: number;
  total_vaccinations: number;
  total_sterilizations: number;
  total_animals_treated: number;
  avg_treatments_per_animal: number;
  period_days: number;
}

interface TreatmentCount {
  category: string;
  category_label: string;
  count: number;
  percentage: number;
}

interface SpeciesBreakdown {
  species: string;
  count: number;
  percentage: number;
}

interface CostItem {
  category: string;
  category_label: string;
  total_cost: number;
  avg_cost_per_treatment: number;
  count: number;
}

interface MonthlyTrend {
  month: string;
  month_label: string;
  treatments: number;
  vaccinations: number;
  sterilizations: number;
  cost: number;
}

interface VaccinationStats {
  total_administered: number;
  fully_vaccinated_animals: number;
  vaccination_rate: number;
  overdue_count: number;
  most_common_vaccine: string;
}

interface SterilizationStats {
  total_sterilized: number;
  sterilization_rate: number;
  dogs_sterilized: number;
  cats_sterilized: number;
  pending_count: number;
  monthly_average: number;
}

// --- Components ---

function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  subtitle,
  color = "text-primary-600",
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: "up" | "down" | null;
  subtitle?: string;
  color?: string;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5" role="group" aria-label={title}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg bg-gray-50 ${color}`}>
          <Icon className="w-5 h-5" aria-hidden="true" />
        </div>
      </div>
      {trend && (
        <div className={`flex items-center gap-1 mt-2 text-xs ${trend === "up" ? "text-green-600" : "text-red-600"}`}>
          {trend === "up" ? (
            <TrendingUp className="w-3 h-3" aria-hidden="true" />
          ) : (
            <TrendingDown className="w-3 h-3" aria-hidden="true" />
          )}
          <span>{trend === "up" ? "Tendencia al alza" : "Tendencia a la baja"}</span>
        </div>
      )}
    </div>
  );
}

function HorizontalBar({
  items,
  maxValue,
}: {
  items: { label: string; value: number; percentage: number; color: string }[];
  maxValue: number;
}) {
  return (
    <div className="space-y-3" role="list" aria-label="Distribución de tratamientos">
      {items.map((item) => (
        <div key={item.label} role="listitem">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-700">{item.label}</span>
            <span className="font-medium text-gray-900">
              {item.value} ({item.percentage}%)
            </span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2.5">
            <div
              className="h-2.5 rounded-full transition-all duration-500"
              style={{
                width: `${Math.min((item.value / maxValue) * 100, 100)}%`,
                backgroundColor: item.color,
              }}
              role="img"
              aria-label={`${item.label}: ${item.percentage}%`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function TrendChart({ data }: { data: MonthlyTrend[] }) {
  if (data.length === 0) return null;
  const maxTreatments = Math.max(...data.map((d) => d.treatments), 1);

  return (
    <div className="space-y-4" role="img" aria-label="Tendencias mensuales de atención veterinaria">
      <div className="flex items-end gap-2 h-40">
        {data.map((month) => (
          <div key={month.month} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-xs text-gray-600 font-medium">{month.treatments}</span>
            <div
              className="w-full bg-primary-500 rounded-t transition-all duration-300"
              style={{
                height: `${(month.treatments / maxTreatments) * 100}%`,
                minHeight: "4px",
              }}
            />
            <span className="text-xs text-gray-500 truncate w-full text-center">
              {month.month_label.split(" ")[0]}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-6 text-xs text-gray-500 justify-center">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-primary-500 rounded" aria-hidden="true" />
          Tratamientos
        </span>
      </div>
    </div>
  );
}

function CostTable({ costs }: { costs: CostItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" aria-label="Desglose de costos veterinarios">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 text-gray-600 font-medium">Categoría</th>
            <th className="text-right py-2 text-gray-600 font-medium">Total</th>
            <th className="text-right py-2 text-gray-600 font-medium">Promedio</th>
            <th className="text-right py-2 text-gray-600 font-medium">Cantidad</th>
          </tr>
        </thead>
        <tbody>
          {costs.map((cost) => (
            <tr key={cost.category} className="border-b border-gray-100">
              <td className="py-2 text-gray-900">{cost.category_label}</td>
              <td className="py-2 text-right text-gray-900 font-medium">
                {(cost.total_cost / 1_000_000).toFixed(1)}M Gs.
              </td>
              <td className="py-2 text-right text-gray-600">
                {(cost.avg_cost_per_treatment / 1000).toFixed(0)}k Gs.
              </td>
              <td className="py-2 text-right text-gray-600">{cost.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8" aria-busy="true" aria-label="Cargando analíticas">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6 animate-pulse" />
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border rounded-xl p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Page ---
export default function VetAnalyticsPage() {
  const [summary, setSummary] = useState<VetSummary | null>(null);
  const [treatments, setTreatments] = useState<TreatmentCount[]>([]);
  const [species, setSpecies] = useState<SpeciesBreakdown[]>([]);
  const [vaccinations, setVaccinations] = useState<VaccinationStats | null>(null);
  const [sterilizations, setSterilizations] = useState<SterilizationStats | null>(null);
  const [costs, setCosts] = useState<CostItem[]>([]);
  const [trends, setTrends] = useState<MonthlyTrend[]>([]);
  const [periodDays, setPeriodDays] = useState(30);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const base = `${API_BASE}/api/admin/analytics/veterinary`;
      const [sumRes, treatRes, vaccRes, sterRes, costRes, trendRes] = await Promise.all([
        fetch(`${base}/summary?period_days=${periodDays}`),
        fetch(`${base}/treatments?period_days=${periodDays}`),
        fetch(`${base}/vaccinations?period_days=${periodDays}`),
        fetch(`${base}/sterilizations?period_days=${periodDays}`),
        fetch(`${base}/costs?period_days=${periodDays}`),
        fetch(`${base}/trends?months=6`),
      ]);

      if (sumRes.ok) setSummary(await sumRes.json());
      if (treatRes.ok) {
        const data = await treatRes.json();
        setTreatments(data.treatments ?? []);
        setSpecies(data.by_species ?? []);
      }
      if (vaccRes.ok) setVaccinations(await vaccRes.json());
      if (sterRes.ok) setSterilizations(await sterRes.json());
      if (costRes.ok) {
        const data = await costRes.json();
        setCosts(data.by_category ?? []);
      }
      if (trendRes.ok) {
        const data = await trendRes.json();
        setTrends(data.monthly ?? []);
      }
    } catch {
      setError("No se pudieron cargar las analíticas veterinarias.");
    } finally {
      setIsLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) return <LoadingSkeleton />;

  const maxTreatment = Math.max(...treatments.map((t) => t.count), 1);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Analíticas veterinarias
          </h1>
          <p className="text-gray-600 mt-1">
            Resumen de atención veterinaria y tendencias
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-500" aria-hidden="true" />
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[44px]"
            aria-label="Período de análisis"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6" role="alert">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      {summary && (
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4 mb-8">
          <MetricCard
            title="Total tratamientos"
            value={summary.total_treatments}
            icon={Stethoscope}
            trend="up"
            color="text-blue-600"
          />
          <MetricCard
            title="Vacunaciones"
            value={summary.total_vaccinations}
            icon={Syringe}
            trend="up"
            color="text-green-600"
          />
          <MetricCard
            title="Esterilizaciones"
            value={summary.total_sterilizations}
            icon={Scissors}
            color="text-purple-600"
          />
          <MetricCard
            title="Animales atendidos"
            value={summary.total_animals_treated}
            icon={PawPrint}
            subtitle={`${summary.avg_treatments_per_animal} trat./animal`}
            color="text-primary-600"
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2 mb-8">
        {/* Treatment Breakdown */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-500" aria-hidden="true" />
            Distribución de tratamientos
          </h2>
          <HorizontalBar
            items={treatments.map((t, i) => ({
              label: t.category_label,
              value: t.count,
              percentage: t.percentage,
              color: CHART_COLORS[i % CHART_COLORS.length],
            }))}
            maxValue={maxTreatment}
          />
        </div>

        {/* Monthly Trends */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-gray-500" aria-hidden="true" />
            Tendencias mensuales
          </h2>
          <TrendChart data={trends} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 mb-8">
        {/* Vaccination Stats */}
        {vaccinations && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Syringe className="w-5 h-5 text-green-600" aria-hidden="true" />
              Vacunaciones
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Tasa de vacunación</span>
                <span className="font-semibold text-gray-900">{vaccinations.vaccination_rate}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className="h-3 bg-green-500 rounded-full transition-all"
                  style={{ width: `${vaccinations.vaccination_rate}%` }}
                  role="img"
                  aria-label={`Tasa de vacunación: ${vaccinations.vaccination_rate}%`}
                />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completamente vacunados</span>
                <span className="text-gray-900">{vaccinations.fully_vaccinated_animals}</span>
              </div>
              {vaccinations.overdue_count > 0 && (
                <div className="flex items-center gap-2 p-2 bg-amber-50 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
                  <span className="text-sm text-amber-800">
                    {vaccinations.overdue_count} vacunaciones vencidas
                  </span>
                </div>
              )}
              <div className="text-sm text-gray-600">
                Vacuna más común: <span className="font-medium">{vaccinations.most_common_vaccine}</span>
              </div>
            </div>
          </div>
        )}

        {/* Sterilization Stats */}
        {sterilizations && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Scissors className="w-5 h-5 text-purple-600" aria-hidden="true" />
              Esterilizaciones
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Tasa de esterilización</span>
                <span className="font-semibold text-gray-900">{sterilizations.sterilization_rate}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className="h-3 bg-purple-500 rounded-full transition-all"
                  style={{ width: `${sterilizations.sterilization_rate}%` }}
                  role="img"
                  aria-label={`Tasa de esterilización: ${sterilizations.sterilization_rate}%`}
                />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Perros</span>
                  <p className="font-semibold text-gray-900">{sterilizations.dogs_sterilized}</p>
                </div>
                <div>
                  <span className="text-gray-600">Gatos</span>
                  <p className="font-semibold text-gray-900">{sterilizations.cats_sterilized}</p>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Promedio mensual: <span className="font-medium">{sterilizations.monthly_average}</span>
              </div>
              <div className="text-sm text-gray-600">
                Pendientes: <span className="font-medium text-amber-600">{sterilizations.pending_count}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Cost Analysis */}
      {costs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-amber-600" aria-hidden="true" />
            Análisis de costos
          </h2>
          <CostTable costs={costs} />
        </div>
      )}
    </div>
  );
}
