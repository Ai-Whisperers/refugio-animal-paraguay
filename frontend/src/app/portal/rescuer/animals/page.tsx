"use client";

import { useState, useEffect, useCallback } from "react";

// -- Types ------------------------------------------------------------------

interface RescuerAnimal {
  id: string;
  name: string;
  species: string;
  breed: string;
  age: string;
  description: string;
  medical_needs: string;
  urgency: string;
  status: string;
  photo_urls: string[];
  created_at: string;
  updated_at: string;
  adoption_story: { story_text: string; adopter_name: string | null } | null;
}

// -- API helpers ------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

// -- Sub-components ---------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-32 bg-gray-200 rounded-lg" />
      ))}
    </div>
  );
}

function UrgencyBadge({ urgency }: { urgency: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-600 text-white",
    high: "bg-orange-500 text-white",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-green-100 text-green-800",
  };
  const labels: Record<string, string> = {
    critical: "Critico",
    high: "Alto",
    medium: "Medio",
    low: "Bajo",
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[urgency] ?? "bg-gray-100"}`}>
      {labels[urgency] ?? urgency}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    available: "bg-green-100 text-green-800",
    adopted: "bg-blue-100 text-blue-800",
    in_treatment: "bg-yellow-100 text-yellow-800",
    deceased: "bg-gray-100 text-gray-600",
    archived: "bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    available: "Disponible",
    adopted: "Adoptado",
    in_treatment: "En tratamiento",
    deceased: "Fallecido",
    archived: "Archivado",
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${colors[status] ?? "bg-gray-100"}`}>
      {labels[status] ?? status}
    </span>
  );
}

function AnimalRow({ animal }: { animal: RescuerAnimal }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Photo placeholder */}
        <div className="w-full sm:w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{animal.name}</h3>
            <StatusBadge status={animal.status} />
            <UrgencyBadge urgency={animal.urgency} />
          </div>
          <p className="text-sm text-gray-500 mb-2">
            {animal.species === "dog" ? "Perro" : animal.species === "cat" ? "Gato" : "Otro"} &middot; {animal.breed} &middot; {animal.age}
          </p>
          <p className="text-sm text-gray-700 line-clamp-2 mb-2">{animal.description}</p>
          {animal.medical_needs && (
            <p className="text-xs text-orange-700 bg-orange-50 px-2 py-1 rounded inline-block">
              Necesidades medicas: {animal.medical_needs}
            </p>
          )}
          {animal.adoption_story && (
            <p className="text-xs text-blue-700 bg-blue-50 px-2 py-1 rounded inline-block mt-1">
              Historia de adopcion disponible
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex sm:flex-col gap-2 flex-shrink-0">
          <button className="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors">
            Editar
          </button>
          <button className="px-3 py-1.5 text-xs bg-orange-50 text-orange-700 rounded hover:bg-orange-100 transition-colors">
            Estado
          </button>
          <button className="px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors">
            Archivar
          </button>
        </div>
      </div>
    </div>
  );
}

// -- Main page --------------------------------------------------------------

export default function RescuerAnimalsPage() {
  const [animals, setAnimals] = useState<RescuerAnimal[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [speciesFilter, setSpeciesFilter] = useState("");
  const [total, setTotal] = useState(0);

  const loadAnimals = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status_filter", statusFilter);
      if (speciesFilter) params.set("species_filter", speciesFilter);

      const data = await fetchJSON<{ animals: RescuerAnimal[]; total: number }>(
        `${API}/api/portal/rescuer/animals?${params}`
      );
      setAnimals(data.animals);
      setTotal(data.total);
    } catch {
      /* API not connected */
    } finally {
      setLoading(false);
    }
  }, [statusFilter, speciesFilter]);

  useEffect(() => {
    loadAnimals();
  }, [loadAnimals]);

  const availableCount = animals.filter((a) => a.status === "available").length;
  const treatmentCount = animals.filter((a) => a.status === "in_treatment").length;
  const adoptedCount = animals.filter((a) => a.status === "adopted").length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mis animales</h1>
          <p className="text-gray-600 mt-1">Gestiona los animales bajo tu cuidado</p>
        </div>
        <button className="mt-3 sm:mt-0 px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors">
          + Agregar animal
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-3 text-center">
          <div className="text-xl font-bold text-gray-900">{total}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="bg-green-50 rounded-lg border border-green-200 p-3 text-center">
          <div className="text-xl font-bold text-green-700">{availableCount}</div>
          <div className="text-xs text-green-600">Disponibles</div>
        </div>
        <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-3 text-center">
          <div className="text-xl font-bold text-yellow-700">{treatmentCount}</div>
          <div className="text-xs text-yellow-600">En tratamiento</div>
        </div>
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-3 text-center">
          <div className="text-xl font-bold text-blue-700">{adoptedCount}</div>
          <div className="text-xs text-blue-600">Adoptados</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">Todos los estados</option>
          <option value="available">Disponible</option>
          <option value="in_treatment">En tratamiento</option>
          <option value="adopted">Adoptado</option>
          <option value="deceased">Fallecido</option>
          <option value="archived">Archivado</option>
        </select>
        <select
          value={speciesFilter}
          onChange={(e) => setSpeciesFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">Todas las especies</option>
          <option value="dog">Perro</option>
          <option value="cat">Gato</option>
          <option value="other">Otro</option>
        </select>
      </div>

      {/* Animal list */}
      {loading ? (
        <LoadingSkeleton />
      ) : (
        <div className="space-y-4">
          {animals.map((animal) => (
            <AnimalRow key={animal.id} animal={animal} />
          ))}
          {animals.length === 0 && (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <p className="text-gray-500 mb-4">No tienes animales registrados</p>
              <button className="px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors">
                Agregar tu primer animal
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
