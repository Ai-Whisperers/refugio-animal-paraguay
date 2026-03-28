"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface Need {
  id: string;
  rescuer_name: string;
  title: string;
  description: string;
  need_type: string;
  need_type_label: string;
  urgency: string;
  urgency_label: string;
  location: string;
  contact_method: string;
  contact_info: string;
  target_date: string | null;
  estimated_cost_pyg: number | null;
  status: string;
  status_label: string;
  responses_count: number;
  created_at: string;
}

interface NeedListResponse {
  needs: Need[];
  total: number;
  page: number;
  page_size: number;
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function urgencyColor(urgency: string): string {
  switch (urgency) {
    case "critical": return "bg-red-100 text-red-800 border-red-200";
    case "high": return "bg-orange-100 text-orange-800 border-orange-200";
    case "medium": return "bg-yellow-100 text-yellow-800 border-yellow-200";
    default: return "bg-green-100 text-green-800 border-green-200";
  }
}

function typeIcon(type: string): string {
  switch (type) {
    case "food": return "\uD83C\uDF5E";
    case "transport": return "\uD83D\uDE97";
    case "foster": return "\uD83C\uDFE0";
    case "medical": return "\uD83C\uDFE5";
    case "supplies": return "\uD83D\uDCE6";
    default: return "\u2753";
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PY", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse" aria-busy="true" aria-label="Cargando necesidades">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-36 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function NeedCard({ need }: { need: Need }) {
  const isCriticalOrHigh = need.urgency === "critical" || need.urgency === "high";

  return (
    <div
      className={`bg-white rounded-xl border p-4 ${
        isCriticalOrHigh ? "border-red-300 ring-1 ring-red-100" : "border-gray-200"
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{typeIcon(need.need_type)}</span>
          <div>
            <h3 className="font-semibold text-gray-900">{need.title}</h3>
            <p className="text-sm text-gray-500">
              {need.rescuer_name} | {need.location}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium border ${urgencyColor(need.urgency)}`}>
          {need.urgency_label}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{need.description}</p>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="text-gray-400">{formatDate(need.created_at)}</span>
        <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
          {need.need_type_label}
        </span>
        {need.estimated_cost_pyg && (
          <span className="text-gray-500">
            ~{new Intl.NumberFormat("es-PY").format(need.estimated_cost_pyg)} PYG
          </span>
        )}
        {need.target_date && (
          <span className="text-gray-500">Necesario: {need.target_date}</span>
        )}
        <span className="text-gray-400">{need.responses_count} respuestas</span>
      </div>
      <div className="mt-3 flex gap-2">
        <a
          href={`/community/needs/${need.id}`}
          className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors"
        >
          Ayudar con esto
        </a>
        <a
          href={`/community/needs/${need.id}`}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors"
        >
          Ver detalles
        </a>
      </div>
    </div>
  );
}

// -- Main page -----------------------------------------------------------

export default function CommunityNeedsPage() {
  const [needs, setNeeds] = useState<Need[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [urgencyFilter, setUrgencyFilter] = useState<string>("");
  const [locationSearch, setLocationSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (typeFilter) params.set("type", typeFilter);
    if (urgencyFilter) params.set("urgency", urgencyFilter);
    if (locationSearch) params.set("location", locationSearch);

    const qs = params.toString() ? `?${params.toString()}` : "";
    fetchJSON<NeedListResponse>(`/api/community/needs${qs}`)
      .then((data) => {
        setNeeds(data.needs);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [typeFilter, urgencyFilter, locationSearch]);

  const typeOptions = [
    { value: "", label: "Todos los tipos" },
    { value: "food", label: "Alimento" },
    { value: "transport", label: "Transporte" },
    { value: "foster", label: "Acogida" },
    { value: "medical", label: "Medico" },
    { value: "supplies", label: "Suministros" },
    { value: "other", label: "Otro" },
  ];

  const urgencyOptions = [
    { value: "", label: "Toda urgencia" },
    { value: "critical", label: "Critico" },
    { value: "high", label: "Alta" },
    { value: "medium", label: "Media" },
    { value: "low", label: "Baja" },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Necesidades de la comunidad</h1>
        <p className="text-gray-500 mt-1">
          Ayuda a los rescatistas con sus necesidades urgentes
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Filtrar por tipo"
        >
          {typeOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <select
          value={urgencyFilter}
          onChange={(e) => setUrgencyFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Filtrar por urgencia"
        >
          {urgencyOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Buscar por ubicacion..."
          value={locationSearch}
          onChange={(e) => setLocationSearch(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Buscar por ubicacion"
        />
      </div>

      <p className="text-sm text-gray-500 mb-4">{total} necesidades encontradas</p>

      {loading ? (
        <LoadingSkeleton />
      ) : needs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <p className="text-gray-500">No hay necesidades abiertas en este momento</p>
        </div>
      ) : (
        <div className="space-y-4">
          {needs.map((need) => (
            <NeedCard key={need.id} need={need} />
          ))}
        </div>
      )}
    </div>
  );
}
