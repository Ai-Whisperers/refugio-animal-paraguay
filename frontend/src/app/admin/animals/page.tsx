"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  PawPrint,
  Search,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Plus,
  Pencil,
  ArrowRightLeft,
  X,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import { STATUS_LABELS, STATUS_COLORS } from "@/lib/animal-status";
import BatchStatusModal from "@/components/admin/BatchStatusModal";
import type { AnimalStatus, AnimalSpecies } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Gestion de Animales";
const LABEL_SEARCH_PLACEHOLDER = "Buscar por nombre...";
const LABEL_SPECIES_FILTER = "Especie";
const LABEL_STATUS_FILTER = "Estado";
const LABEL_ALL = "Todos";
const LABEL_LOADING = "Cargando animales...";
const LABEL_ERROR = "Error al cargar animales";
const LABEL_EMPTY = "No se encontraron animales";
const LABEL_EMPTY_FILTERED = "No hay animales que coincidan con los filtros";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";
const LABEL_NAME = "Nombre";
const LABEL_SPECIES = "Especie";
const LABEL_STATUS = "Estado";
const LABEL_BREED = "Raza";
const LABEL_INTAKE_DATE = "Fecha de ingreso";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ADD_ANIMAL = "Nuevo Animal";
const LABEL_ACTIONS = "Acciones";
const LABEL_EDIT = "Editar";
const LABEL_BATCH_STATUS = "Cambiar Estado";
const LABEL_SELECTED = "seleccionados";
const LABEL_CLEAR_SELECTION = "Limpiar seleccion";

const PAGE_SIZE = 20;

const SPECIES_LABELS: Record<AnimalSpecies, string> = {
  dog: "Perro",
  cat: "Gato",
  other: "Otro",
};

// --- Types ---
interface AnimalListItem {
  id: string;
  name: string;
  species: AnimalSpecies;
  status: AnimalStatus;
  breed: string | null;
  primary_photo_url: string | null;
  created_at: string;
}

type SortField = "name" | "species" | "status" | "created_at";
type SortDirection = "asc" | "desc";

export default function AdminAnimalsPage() {
  const router = useRouter();

  // --- Auth check ---
  const [isChecking, setIsChecking] = useState(true);

  // --- Data state ---
  const [animals, setAnimals] = useState<AnimalListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- Filter/search state ---
  const [searchQuery, setSearchQuery] = useState("");
  const [speciesFilter, setSpeciesFilter] = useState<AnimalSpecies | "">("");
  const [statusFilter, setStatusFilter] = useState<AnimalStatus | "">("");

  // --- Sort state ---
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // --- Pagination state ---
  const [currentPage, setCurrentPage] = useState(1);

  // --- Selection state ---
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showBatchModal, setShowBatchModal] = useState(false);

  // --- Auth check ---
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  // --- Fetch animals ---
  const fetchAnimals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (speciesFilter) {
        params.set("species", speciesFilter);
      }
      if (statusFilter) {
        params.set("status", statusFilter);
      }
      params.set("limit", "100");
      params.set("offset", "0");

      const endpoint = `/animals?${params.toString()}`;
      const data = await api.get<AnimalListItem[]>(endpoint);
      setAnimals(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [speciesFilter, statusFilter]);

  useEffect(() => {
    if (!isChecking) {
      fetchAnimals();
    }
  }, [isChecking, fetchAnimals]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, speciesFilter, statusFilter, sortField, sortDirection]);

  // --- Derived data: search, sort, paginate ---
  const filteredAndSorted = useMemo(() => {
    let result = [...animals];

    // Client-side search by name
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter((animal) =>
        animal.name.toLowerCase().includes(query)
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;
        case "species":
          comparison = a.species.localeCompare(b.species);
          break;
        case "status":
          comparison = a.status.localeCompare(b.status);
          break;
        case "created_at":
          comparison =
            new Date(a.created_at).getTime() -
            new Date(b.created_at).getTime();
          break;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });

    return result;
  }, [animals, searchQuery, sortField, sortDirection]);

  const totalPages = Math.max(1, Math.ceil(filteredAndSorted.length / PAGE_SIZE));
  const paginatedAnimals = filteredAndSorted.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  // --- Selection handlers ---
  const allPageSelected = paginatedAnimals.length > 0 && paginatedAnimals.every((a) => selectedIds.has(a.id));
  const somePageSelected = paginatedAnimals.some((a) => selectedIds.has(a.id));

  function handleToggleAll() {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allPageSelected) {
        paginatedAnimals.forEach((a) => next.delete(a.id));
      } else {
        paginatedAnimals.forEach((a) => next.add(a.id));
      }
      return next;
    });
  }

  function handleToggleOne(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function handleClearSelection() {
    setSelectedIds(new Set());
  }

  const selectedAnimals = animals.filter((a) => selectedIds.has(a.id));

  // --- Sort handler ---
  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  }

  function renderSortIcon(field: SortField) {
    if (sortField !== field) {
      return (
        <ChevronUp className="ml-1 inline h-3 w-3 text-warm-text-tertiary opacity-0 group-hover:opacity-50" />
      );
    }
    return sortDirection === "asc" ? (
      <ChevronUp className="ml-1 inline h-3 w-3 text-primary-600" />
    ) : (
      <ChevronDown className="ml-1 inline h-3 w-3 text-primary-600" />
    );
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  // --- Loading state ---
  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/dashboard")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <PawPrint className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/admin/animals/new")}
              className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              {LABEL_ADD_ANIMAL}
            </button>
            <button
              onClick={fetchAnimals}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Search and Filters */}
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-text-tertiary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={LABEL_SEARCH_PLACEHOLDER}
              className="w-full rounded-lg border border-warm-border bg-warm-surface py-2 pl-10 pr-4 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          {/* Species filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="species-filter"
              className="text-sm font-medium text-warm-text-secondary"
            >
              {LABEL_SPECIES_FILTER}:
            </label>
            <select
              id="species-filter"
              value={speciesFilter}
              onChange={(e) =>
                setSpeciesFilter(e.target.value as AnimalSpecies | "")
              }
              className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">{LABEL_ALL}</option>
              {Object.entries(SPECIES_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="status-filter"
              className="text-sm font-medium text-warm-text-secondary"
            >
              {LABEL_STATUS_FILTER}:
            </label>
            <select
              id="status-filter"
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as AnimalStatus | "")
              }
              className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">{LABEL_ALL}</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={fetchAnimals}
              className="mt-2 text-sm font-medium text-red-700 underline hover:text-red-900"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
            <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && filteredAndSorted.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
            <PawPrint
              className="mx-auto h-12 w-12 text-primary-300"
              aria-hidden="true"
            />
            <p className="mt-4 text-warm-text-secondary">
              {searchQuery || speciesFilter || statusFilter
                ? LABEL_EMPTY_FILTERED
                : LABEL_EMPTY}
            </p>
          </div>
        )}

        {/* Batch action toolbar */}
        {selectedIds.size > 0 && (
          <div className="mb-4 flex items-center gap-3 rounded-lg border border-primary-200 bg-primary-50 px-4 py-2.5">
            <span className="text-sm font-medium text-primary-800">
              {selectedIds.size} {LABEL_SELECTED}
            </span>
            <button
              onClick={() => setShowBatchModal(true)}
              className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              <ArrowRightLeft className="h-3.5 w-3.5" />
              {LABEL_BATCH_STATUS}
            </button>
            <button
              onClick={handleClearSelection}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-primary-700 transition-colors hover:bg-primary-100"
            >
              <X className="h-3.5 w-3.5" />
              {LABEL_CLEAR_SELECTION}
            </button>
          </div>
        )}

        {/* Animals table */}
        {!isLoading && !error && filteredAndSorted.length > 0 && (
          <>
            <div className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-warm-border bg-warm-bg">
                      <th className="w-10 px-3 py-3">
                        <input
                          type="checkbox"
                          checked={allPageSelected}
                          ref={(el) => {
                            if (el) el.indeterminate = somePageSelected && !allPageSelected;
                          }}
                          onChange={handleToggleAll}
                          className="h-4 w-4 rounded border-warm-border text-primary-600 focus:ring-primary-500"
                          aria-label="Seleccionar todos"
                        />
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("name")}
                      >
                        {LABEL_NAME}
                        {renderSortIcon("name")}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("species")}
                      >
                        {LABEL_SPECIES}
                        {renderSortIcon("species")}
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                        {LABEL_BREED}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("status")}
                      >
                        {LABEL_STATUS}
                        {renderSortIcon("status")}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("created_at")}
                      >
                        {LABEL_INTAKE_DATE}
                        {renderSortIcon("created_at")}
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-warm-text-secondary">
                        {LABEL_ACTIONS}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedAnimals.map((animal) => (
                      <tr
                        key={animal.id}
                        className={`border-b border-warm-border last:border-b-0 transition-colors hover:bg-warm-bg ${selectedIds.has(animal.id) ? "bg-primary-50/50" : ""}`}
                      >
                        <td className="w-10 px-3 py-3">
                          <input
                            type="checkbox"
                            checked={selectedIds.has(animal.id)}
                            onChange={() => handleToggleOne(animal.id)}
                            className="h-4 w-4 rounded border-warm-border text-primary-600 focus:ring-primary-500"
                            aria-label={`Seleccionar ${animal.name}`}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            {animal.primary_photo_url ? (
                              <img
                                src={animal.primary_photo_url}
                                alt={animal.name}
                                className="h-8 w-8 rounded-full object-cover"
                              />
                            ) : (
                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100">
                                <PawPrint className="h-4 w-4 text-primary-500" />
                              </div>
                            )}
                            <span className="font-medium text-warm-text-primary">
                              {animal.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {SPECIES_LABELS[animal.species] ?? animal.species}
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {animal.breed ?? "-"}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[animal.status] ?? "bg-gray-100 text-gray-700"}`}
                          >
                            {STATUS_LABELS[animal.status] ?? animal.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {formatDate(animal.created_at)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() =>
                              router.push(`/admin/animals/${animal.id}/edit`)
                            }
                            className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-primary-600 transition-colors hover:bg-primary-50"
                          >
                            <Pencil className="h-3 w-3" />
                            {LABEL_EDIT}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-warm-text-secondary">
                {LABEL_SHOWING}{" "}
                {(currentPage - 1) * PAGE_SIZE + 1}-
                {Math.min(currentPage * PAGE_SIZE, filteredAndSorted.length)}{" "}
                {LABEL_OF} {filteredAndSorted.length}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={currentPage <= 1}
                  className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                  {LABEL_PREVIOUS}
                </button>
                <span className="px-2 text-sm text-warm-text-secondary">
                  {currentPage} / {totalPages}
                </span>
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                  }
                  disabled={currentPage >= totalPages}
                  className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {LABEL_NEXT}
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Batch status modal */}
      {showBatchModal && selectedAnimals.length > 0 && (
        <BatchStatusModal
          animals={selectedAnimals.map((a) => ({
            id: a.id,
            name: a.name,
            status: a.status,
          }))}
          onClose={() => setShowBatchModal(false)}
          onBatchCompleted={(updatedIds, newStatus) => {
            setAnimals((prev) =>
              prev.map((a) =>
                updatedIds.includes(a.id)
                  ? { ...a, status: newStatus }
                  : a
              )
            );
            setSelectedIds(new Set());
          }}
        />
      )}
    </div>
  );
}
