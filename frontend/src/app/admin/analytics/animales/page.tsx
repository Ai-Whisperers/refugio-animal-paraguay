"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface Overview {
  period_days: number;
  total_intake: number;
  total_outcomes: number;
  current_population: number;
  net_change: number;
  intake_rate_per_day: number;
  outcome_rate_per_day: number;
  live_release_rate_pct: number;
  average_length_of_stay_days: number;
}

interface BreakdownItem {
  [key: string]: string | number;
}

interface IntakeBreakdown {
  period_days: number;
  total: number;
  by_source: BreakdownItem[];
  by_species: BreakdownItem[];
}

interface OutcomeBreakdown {
  period_days: number;
  total: number;
  by_type: BreakdownItem[];
  by_species: BreakdownItem[];
  live_release_rate_pct: number;
}

interface Demographics {
  total_population: number;
  by_species: BreakdownItem[];
  by_age_group: BreakdownItem[];
  by_sex: BreakdownItem[];
  sterilization_rate_pct: number;
}

interface LengthOfStay {
  average_days: number;
  median_days: number;
  min_days: number;
  max_days: number;
  by_species: BreakdownItem[];
  distribution: BreakdownItem[];
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat("es-PY").format(Math.round(n));
}

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Cargando analytics">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-40 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function KPIGrid({ overview }: { overview: Overview }) {
  const kpis = [
    { label: "Poblacion actual", value: formatNumber(overview.current_population), color: "text-blue-600" },
    { label: "Ingresos (periodo)", value: formatNumber(overview.total_intake), color: "text-green-600" },
    { label: "Egresos (periodo)", value: formatNumber(overview.total_outcomes), color: "text-orange-600" },
    { label: "Cambio neto", value: (overview.net_change >= 0 ? "+" : "") + overview.net_change, color: overview.net_change >= 0 ? "text-red-600" : "text-green-600" },
    { label: "Tasa liberacion viva", value: `${overview.live_release_rate_pct}%`, color: "text-green-600" },
    { label: "Estancia promedio", value: `${overview.average_length_of_stay_days} dias`, color: "text-purple-600" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
          <p className="text-xs text-gray-500 mt-1">{kpi.label}</p>
        </div>
      ))}
    </div>
  );
}

function BreakdownSection({
  title,
  items,
  labelKey,
  countKey,
  pctKey,
}: {
  title: string;
  items: BreakdownItem[];
  labelKey: string;
  countKey: string;
  pctKey: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-3">{title}</h3>
      <div className="space-y-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-700">{String(item[labelKey])}</span>
                <span className="text-gray-500">
                  {formatNumber(Number(item[countKey]))} ({item[pctKey]}%)
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--color-primary)] rounded-full transition-all"
                  style={{ width: `${Number(item[pctKey])}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function IntakeSection({ data }: { data: IntakeBreakdown }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Ingresos ({formatNumber(data.total)} total)
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BreakdownSection
          title="Por fuente"
          items={data.by_source}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
        <BreakdownSection
          title="Por especie"
          items={data.by_species}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
      </div>
    </section>
  );
}

function OutcomeSection({ data }: { data: OutcomeBreakdown }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">
        Egresos ({formatNumber(data.total)} total)
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Tasa de liberacion viva: {data.live_release_rate_pct}%
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <BreakdownSection
          title="Por tipo"
          items={data.by_type}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
        <BreakdownSection
          title="Por especie"
          items={data.by_species}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
      </div>
    </section>
  );
}

function DemographicsSection({ data }: { data: Demographics }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">
        Demografia ({formatNumber(data.total_population)} animales)
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Tasa de esterilizacion: {data.sterilization_rate_pct}%
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <BreakdownSection
          title="Por especie"
          items={data.by_species}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
        <BreakdownSection
          title="Por grupo de edad"
          items={data.by_age_group}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
        <BreakdownSection
          title="Por sexo"
          items={data.by_sex}
          labelKey="label"
          countKey="count"
          pctKey="pct"
        />
      </div>
    </section>
  );
}

function LOSSection({ data }: { data: LengthOfStay }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Tiempo de estancia</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <p className="text-xl font-bold text-gray-900">{data.average_days}</p>
          <p className="text-xs text-gray-500">Promedio (dias)</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold text-gray-900">{data.median_days}</p>
          <p className="text-xs text-gray-500">Mediana (dias)</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold text-gray-900">{data.min_days}</p>
          <p className="text-xs text-gray-500">Minimo (dias)</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold text-gray-900">{data.max_days}</p>
          <p className="text-xs text-gray-500">Maximo (dias)</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Por especie</h3>
          {data.by_species.map((s, i) => (
            <div key={i} className="flex justify-between text-sm py-1.5 border-b border-gray-100">
              <span className="text-gray-600">{String(s.label)}</span>
              <span className="font-medium text-gray-900">{String(s.avg_days)} dias</span>
            </div>
          ))}
        </div>
        <BreakdownSection
          title="Distribucion"
          items={data.distribution}
          labelKey="range"
          countKey="count"
          pctKey="pct"
        />
      </div>
    </section>
  );
}

// -- Main page -----------------------------------------------------------

export default function AnimalAnalyticsPage() {
  const [period, setPeriod] = useState(30);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [intake, setIntake] = useState<IntakeBreakdown | null>(null);
  const [outcomes, setOutcomes] = useState<OutcomeBreakdown | null>(null);
  const [demographics, setDemographics] = useState<Demographics | null>(null);
  const [los, setLos] = useState<LengthOfStay | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const q = `?period_days=${period}`;
    Promise.all([
      fetchJSON<Overview>(`/api/admin/analytics/animals/overview${q}`),
      fetchJSON<IntakeBreakdown>(`/api/admin/analytics/animals/intake${q}`),
      fetchJSON<OutcomeBreakdown>(`/api/admin/analytics/animals/outcomes${q}`),
      fetchJSON<Demographics>("/api/admin/analytics/animals/demographics"),
      fetchJSON<LengthOfStay>("/api/admin/analytics/animals/length-of-stay"),
    ])
      .then(([o, i, out, d, l]) => {
        setOverview(o);
        setIntake(i);
        setOutcomes(out);
        setDemographics(d);
        setLos(l);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [period]);

  const periodOptions = [
    { label: "30 dias", value: 30 },
    { label: "90 dias", value: 90 },
    { label: "180 dias", value: 180 },
    { label: "1 ano", value: 365 },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics de animales</h1>
          <p className="text-gray-500 mt-1">Ingresos, egresos y demografia del refugio</p>
        </div>
        <div className="flex gap-2">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === opt.value
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
          {overview && <KPIGrid overview={overview} />}
          {intake && <IntakeSection data={intake} />}
          {outcomes && <OutcomeSection data={outcomes} />}
          {demographics && <DemographicsSection data={demographics} />}
          {los && <LOSSection data={los} />}
        </div>
      )}
    </div>
  );
}
