"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface RescuerCard {
  id: string;
  name: string;
  location: string;
  specialty: string;
  specialty_label: string;
  mission: string;
  animals_rescued: number;
  supporter_count: number;
  is_verified: boolean;
  last_active: string;
}

interface RescuerListResponse {
  rescuers: RescuerCard[];
  total: number;
  page: number;
  page_size: number;
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function formatNumber(n: number): string {
  return new Intl.NumberFormat("es-PY").format(n);
}

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse" aria-busy="true">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="h-56 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function RescuerCardComponent({ rescuer }: { rescuer: RescuerCard }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="w-12 h-12 bg-[var(--color-primary)] bg-opacity-10 rounded-full flex items-center justify-center">
          <span className="text-lg font-bold text-[var(--color-primary)]">
            {rescuer.name.charAt(0)}
          </span>
        </div>
        {rescuer.is_verified && (
          <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-medium">
            Verificado
          </span>
        )}
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{rescuer.name}</h3>
      <p className="text-sm text-gray-500 mb-2">{rescuer.location} | {rescuer.specialty_label}</p>
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{rescuer.mission}</p>
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <span>{formatNumber(rescuer.animals_rescued)} rescatados</span>
        <span>{formatNumber(rescuer.supporter_count)} apoyos</span>
      </div>
      <div className="flex gap-2">
        <a
          href={`/rescuers/${rescuer.id}`}
          className="flex-1 text-center px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors"
        >
          Ver perfil
        </a>
        <button className="flex-1 px-3 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors">
          Apoyar
        </button>
      </div>
    </div>
  );
}

// -- Main page -----------------------------------------------------------

export default function RescuerDirectoryPage() {
  const [rescuers, setRescuers] = useState<RescuerCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [sortBy, setSortBy] = useState("activity");
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (specialty) params.set("specialty", specialty);
    params.set("sort", sortBy);
    params.set("page", String(page));
    params.set("page_size", "12");

    fetchJSON<RescuerListResponse>(`/api/rescuers?${params.toString()}`)
      .then((data) => {
        setRescuers(data.rescuers);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [search, specialty, sortBy, page]);

  const specialtyOptions = [
    { value: "", label: "Todas las especialidades" },
    { value: "dogs", label: "Perros" },
    { value: "cats", label: "Gatos" },
    { value: "mixed", label: "Mixto" },
    { value: "exotic", label: "Exotico" },
    { value: "farm", label: "Granja" },
    { value: "wildlife", label: "Fauna silvestre" },
  ];

  const sortOptions = [
    { value: "activity", label: "Actividad reciente" },
    { value: "supporters", label: "Mas apoyados" },
    { value: "animals_rescued", label: "Mas rescates" },
    { value: "name", label: "Nombre" },
  ];

  const totalPages = Math.ceil(total / 12);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Directorio de rescatistas</h1>
        <p className="text-gray-500 mt-1">Conoce y apoya a los rescatistas verificados</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <input
          type="text"
          placeholder="Buscar por nombre..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Buscar rescatista"
        />
        <select
          value={specialty}
          onChange={(e) => { setSpecialty(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Filtrar por especialidad"
        >
          {specialtyOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          aria-label="Ordenar por"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <p className="text-sm text-gray-500 mb-4">{total} rescatistas encontrados</p>

      {loading ? (
        <LoadingSkeleton />
      ) : rescuers.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <p className="text-gray-500">No se encontraron rescatistas</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {rescuers.map((r) => (
              <RescuerCardComponent key={r.id} rescuer={r} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`px-3 py-2 rounded-lg text-sm ${
                    page === p
                      ? "bg-[var(--color-primary)] text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
