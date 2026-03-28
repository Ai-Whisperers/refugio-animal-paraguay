"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface ForecastPoint {
  month: string;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

interface IntakeForecast {
  forecast_months: number;
  total_predicted: number;
  by_category: {
    dogs: ForecastPoint[];
    cats: ForecastPoint[];
    other: ForecastPoint[];
  };
  seasonal_notes: string[];
}

interface AdoptionForecast {
  forecast_months: number;
  monthly: ForecastPoint[];
  projected_total: number;
  bottlenecks: string[];
}

interface DonationForecast {
  forecast_months: number;
  monthly_pyg: ForecastPoint[];
  monthly_eur: ForecastPoint[];
  projected_total_pyg: number;
  projected_total_eur: number;
  seasonal_factors: string[];
}

interface CapacityForecast {
  forecast_months: number;
  occupancy: ForecastPoint[];
  current_capacity: number;
  peak_month: string;
  peak_occupancy: number;
  recommendations: string[];
}

interface PredictionSummary {
  generated_at: string;
  forecast_months: number;
  highlights: string[];
  risks: string[];
  opportunities: string[];
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function confidenceColor(c: number): string {
  if (c >= 0.85) return "text-green-700 bg-green-50";
  if (c >= 0.70) return "text-yellow-700 bg-yellow-50";
  return "text-red-700 bg-red-50";
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat("es-PY").format(Math.round(n));
}

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Cargando predicciones">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-48 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function SummaryCard({ summary }: { summary: PredictionSummary }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Resumen de predicciones</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <h3 className="text-sm font-medium text-green-700 mb-2">Aspectos destacados</h3>
          <ul className="space-y-1">
            {summary.highlights.map((h, i) => (
              <li key={i} className="text-sm text-gray-700">{h}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-medium text-red-700 mb-2">Riesgos</h3>
          <ul className="space-y-1">
            {summary.risks.map((r, i) => (
              <li key={i} className="text-sm text-gray-700">{r}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-medium text-blue-700 mb-2">Oportunidades</h3>
          <ul className="space-y-1">
            {summary.opportunities.map((o, i) => (
              <li key={i} className="text-sm text-gray-700">{o}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function ForecastTable({ title, points }: { title: string; points: ForecastPoint[] }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 pr-4 font-medium text-gray-600">Mes</th>
              <th className="text-right py-2 px-4 font-medium text-gray-600">Prediccion</th>
              <th className="text-right py-2 px-4 font-medium text-gray-600">Rango</th>
              <th className="text-right py-2 pl-4 font-medium text-gray-600">Confianza</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p) => (
              <tr key={p.month} className="border-b border-gray-100">
                <td className="py-2 pr-4 text-gray-900">{p.month}</td>
                <td className="py-2 px-4 text-right font-medium text-gray-900">
                  {formatNumber(p.predicted)}
                </td>
                <td className="py-2 px-4 text-right text-gray-500">
                  {formatNumber(p.lower_bound)} - {formatNumber(p.upper_bound)}
                </td>
                <td className="py-2 pl-4 text-right">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${confidenceColor(p.confidence)}`}>
                    {Math.round(p.confidence * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function IntakeSection({ data }: { data: IntakeForecast }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Prediccion de ingresos</h2>
      <p className="text-sm text-gray-500 mb-4">
        Total estimado: {formatNumber(data.total_predicted)} animales en {data.forecast_months} meses
      </p>
      <div className="space-y-6">
        <ForecastTable title="Perros" points={data.by_category.dogs} />
        <ForecastTable title="Gatos" points={data.by_category.cats} />
        <ForecastTable title="Otros" points={data.by_category.other} />
      </div>
      {data.seasonal_notes.length > 0 && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm font-medium text-blue-800 mb-1">Notas estacionales</p>
          {data.seasonal_notes.map((n, i) => (
            <p key={i} className="text-sm text-blue-700">{n}</p>
          ))}
        </div>
      )}
    </section>
  );
}

function AdoptionSection({ data }: { data: AdoptionForecast }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Prediccion de adopciones</h2>
      <p className="text-sm text-gray-500 mb-4">
        Total proyectado: {formatNumber(data.projected_total)} adopciones
      </p>
      <ForecastTable title="Adopciones mensuales" points={data.monthly} />
      {data.bottlenecks.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
          <p className="text-sm font-medium text-yellow-800 mb-1">Cuellos de botella</p>
          {data.bottlenecks.map((b, i) => (
            <p key={i} className="text-sm text-yellow-700">{b}</p>
          ))}
        </div>
      )}
    </section>
  );
}

function DonationSection({ data }: { data: DonationForecast }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Prediccion de donaciones</h2>
      <p className="text-sm text-gray-500 mb-4">
        Proyectado: {formatNumber(data.projected_total_pyg)} PYG / {formatNumber(data.projected_total_eur)} EUR
      </p>
      <div className="space-y-6">
        <ForecastTable title="Donaciones en PYG" points={data.monthly_pyg} />
        <ForecastTable title="Donaciones en EUR" points={data.monthly_eur} />
      </div>
      {data.seasonal_factors.length > 0 && (
        <div className="mt-4 p-3 bg-green-50 rounded-lg">
          <p className="text-sm font-medium text-green-800 mb-1">Factores estacionales</p>
          {data.seasonal_factors.map((f, i) => (
            <p key={i} className="text-sm text-green-700">{f}</p>
          ))}
        </div>
      )}
    </section>
  );
}

function CapacitySection({ data }: { data: CapacityForecast }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Prediccion de capacidad</h2>
      <p className="text-sm text-gray-500 mb-4">
        Capacidad actual: {data.current_capacity} | Pico: {data.peak_month} ({Math.round(data.peak_occupancy)}%)
      </p>
      <ForecastTable title="Ocupacion mensual (%)" points={data.occupancy} />
      {data.recommendations.length > 0 && (
        <div className="mt-4 p-3 bg-purple-50 rounded-lg">
          <p className="text-sm font-medium text-purple-800 mb-1">Recomendaciones</p>
          {data.recommendations.map((r, i) => (
            <p key={i} className="text-sm text-purple-700">{r}</p>
          ))}
        </div>
      )}
    </section>
  );
}

// -- Main page -----------------------------------------------------------

export default function PrediccionesPage() {
  const [months, setMonths] = useState(3);
  const [summary, setSummary] = useState<PredictionSummary | null>(null);
  const [intake, setIntake] = useState<IntakeForecast | null>(null);
  const [adoptions, setAdoptions] = useState<AdoptionForecast | null>(null);
  const [donations, setDonations] = useState<DonationForecast | null>(null);
  const [capacity, setCapacity] = useState<CapacityForecast | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const q = `?months=${months}`;
    Promise.all([
      fetchJSON<PredictionSummary>(`/api/admin/analytics/predictions/summary${q}`),
      fetchJSON<IntakeForecast>(`/api/admin/analytics/predictions/intake${q}`),
      fetchJSON<AdoptionForecast>(`/api/admin/analytics/predictions/adoptions${q}`),
      fetchJSON<DonationForecast>(`/api/admin/analytics/predictions/donations${q}`),
      fetchJSON<CapacityForecast>(`/api/admin/analytics/predictions/capacity${q}`),
    ])
      .then(([s, i, a, d, c]) => {
        setSummary(s);
        setIntake(i);
        setAdoptions(a);
        setDonations(d);
        setCapacity(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [months]);

  const periodOptions = [
    { label: "3 meses", value: 3 },
    { label: "6 meses", value: 6 },
    { label: "12 meses", value: 12 },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analisis predictivo</h1>
          <p className="text-gray-500 mt-1">Proyecciones y tendencias del refugio</p>
        </div>
        <div className="flex gap-2">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setMonths(opt.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                months === opt.value
                  ? "bg-[var(--color-primary)] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton />
      ) : (
        <div className="space-y-6">
          {summary && <SummaryCard summary={summary} />}
          {intake && <IntakeSection data={intake} />}
          {adoptions && <AdoptionSection data={adoptions} />}
          {donations && <DonationSection data={donations} />}
          {capacity && <CapacitySection data={capacity} />}
        </div>
      )}
    </div>
  );
}
