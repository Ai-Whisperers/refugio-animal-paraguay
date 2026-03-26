"use client";

import { Suspense, useCallback, useEffect, useState, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Search, X, SlidersHorizontal, AlertCircle, Heart } from "lucide-react";
import type { Animal, AnimalSpecies } from "@/types/api";
import { listAnimalsPublic } from "@/lib/public-api";
import { STATUS_LABELS, statusBadgeClass, calculateAge } from "@/lib/animal-utils";
import { ANIMALS_LIST, SPECIES_LABELS } from "@/lib/strings";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";
import AnimalCardSkeleton from "@/components/AnimalCardSkeleton";

// --- Filter option types ---

interface FilterOption<T extends string> {
  value: T;
  label: string;
}

const SPECIES_OPTIONS: FilterOption<AnimalSpecies | "">[] = [
  { value: "", label: ANIMALS_LIST.allSpecies },
  { value: "dog", label: ANIMALS_LIST.dogs },
  { value: "cat", label: ANIMALS_LIST.cats },
  { value: "other", label: ANIMALS_LIST.other },
];

const SIZE_OPTIONS: FilterOption<string>[] = [
  { value: "", label: ANIMALS_LIST.sizeAll },
  { value: "small", label: ANIMALS_LIST.sizeSmall },
  { value: "medium", label: ANIMALS_LIST.sizeMedium },
  { value: "large", label: ANIMALS_LIST.sizeLarge },
];

interface AgeRange {
  value: string;
  label: string;
  min?: number;
  max?: number;
}

const AGE_OPTIONS: AgeRange[] = [
  { value: "", label: ANIMALS_LIST.ageAll },
  { value: "puppy", label: ANIMALS_LIST.agePuppy, min: 0, max: 12 },
  { value: "young", label: ANIMALS_LIST.ageYoung, min: 12, max: 36 },
  { value: "adult", label: ANIMALS_LIST.ageAdult, min: 36, max: 96 },
  { value: "senior", label: ANIMALS_LIST.ageSenior, min: 96 },
];

const PAGE_SIZE = 12;
const SKELETON_COUNT = 8;

export default function AnimalsPage() {
  return (
    <Suspense fallback={<AnimalsPageSkeleton />}>
      <AnimalsPageContent />
    </Suspense>
  );
}

function AnimalsPageSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="text-center mb-10">
        <div className="h-10 w-64 bg-gray-200 rounded-lg animate-pulse mx-auto mb-3" />
        <div className="h-5 w-96 bg-gray-100 rounded animate-pulse mx-auto" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <AnimalCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

function AnimalsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Read filters from URL search params
  const speciesFilter = (searchParams.get("species") ?? "") as AnimalSpecies | "";
  const sizeFilter = searchParams.get("size") ?? "";
  const ageFilter = searchParams.get("age") ?? "";
  const searchQuery = searchParams.get("search") ?? "";
  const currentOffset = Number(searchParams.get("offset") ?? "0");

  const [animals, setAnimals] = useState<Animal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [searchInput, setSearchInput] = useState(searchQuery);

  // Count active filters for the indicator
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (speciesFilter) count++;
    if (sizeFilter) count++;
    if (ageFilter) count++;
    if (searchQuery) count++;
    return count;
  }, [speciesFilter, sizeFilter, ageFilter, searchQuery]);

  // Build URL with updated params
  const buildUrl = useCallback(
    (updates: Record<string, string>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value) {
          params.set(key, value);
        } else {
          params.delete(key);
        }
      }
      // Reset offset when filters change (unless explicitly setting offset)
      if (!("offset" in updates)) {
        params.delete("offset");
      }
      const query = params.toString();
      return `/animals${query ? `?${query}` : ""}`;
    },
    [searchParams]
  );

  const setFilter = useCallback(
    (key: string, value: string) => {
      router.push(buildUrl({ [key]: value }));
    },
    [router, buildUrl]
  );

  const clearAllFilters = useCallback(() => {
    setSearchInput("");
    router.push("/animals");
  }, [router]);

  // Resolve age filter to min/max months
  const ageRange = useMemo(() => {
    const match = AGE_OPTIONS.find((o) => o.value === ageFilter);
    return match ?? AGE_OPTIONS[0];
  }, [ageFilter]);

  const fetchAnimals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listAnimalsPublic({
        species: speciesFilter || undefined,
        status: "available",
        size: sizeFilter || undefined,
        age_min: ageRange.min,
        age_max: ageRange.max,
        search: searchQuery || undefined,
        offset: currentOffset,
        limit: PAGE_SIZE + 1,
      });
      setHasMore(result.length > PAGE_SIZE);
      setAnimals(result.slice(0, PAGE_SIZE));
    } catch (err) {
      setError(err instanceof Error ? err.message : ANIMALS_LIST.errorTitle);
    } finally {
      setIsLoading(false);
    }
  }, [speciesFilter, sizeFilter, ageRange, searchQuery, currentOffset]);

  useEffect(() => {
    fetchAnimals();
  }, [fetchAnimals]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== searchQuery) {
        setFilter("search", searchInput);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]); // eslint-disable-line react-hooks/exhaustive-deps

  const hasFilters = activeFilterCount > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Page Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
          {ANIMALS_LIST.title}
        </h1>
        <p className="text-gray-500 max-w-2xl mx-auto">
          {ANIMALS_LIST.subtitle}
        </p>
      </div>

      {/* Filter Bar */}
      <div className="sticky top-0 z-10 bg-white/95 backdrop-blur-sm border-b border-gray-100 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-4 mb-8">
        <div className="flex flex-col gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={ANIMALS_LIST.filterSearch}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] transition-colors"
              inputMode="search"
            />
            {searchInput && (
              <button
                onClick={() => { setSearchInput(""); setFilter("search", ""); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Limpiar busqueda"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Filter Pills Row */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 text-sm text-gray-500">
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{ANIMALS_LIST.filterSpecies}:</span>
            </div>

            {/* Species */}
            <div className="flex flex-wrap gap-2">
              {SPECIES_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setFilter("species", opt.value)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    speciesFilter === opt.value
                      ? "bg-[#E8622A] text-white shadow-sm"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <span className="hidden sm:inline text-gray-300">|</span>

            {/* Size */}
            <select
              value={sizeFilter}
              onChange={(e) => setFilter("size", e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A]"
              aria-label={ANIMALS_LIST.filterSize}
            >
              {SIZE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {ANIMALS_LIST.filterSize}: {opt.label}
                </option>
              ))}
            </select>

            {/* Age */}
            <select
              value={ageFilter}
              onChange={(e) => setFilter("age", e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A]"
              aria-label={ANIMALS_LIST.filterAge}
            >
              {AGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {ANIMALS_LIST.filterAge}: {opt.label}
                </option>
              ))}
            </select>

            {/* Active filter count + clear */}
            {hasFilters && (
              <button
                onClick={clearAllFilters}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                {ANIMALS_LIST.filterActiveCount(activeFilterCount)}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Loading State: Skeleton Grid */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <AnimalCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-4">
            <AlertCircle className="h-8 w-8 text-red-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {ANIMALS_LIST.errorTitle}
          </h2>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            {ANIMALS_LIST.errorSubtitle}
          </p>
          <button
            onClick={fetchAnimals}
            className="px-6 py-2.5 bg-[#E8622A] text-white rounded-lg hover:bg-[#d4571f] transition-colors font-medium"
          >
            {ANIMALS_LIST.errorRetry}
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && animals.length === 0 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-50 mb-4">
            <Heart className="h-8 w-8 text-[#E8622A]" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {hasFilters ? ANIMALS_LIST.emptyTitle : ANIMALS_LIST.emptyNoAnimals}
          </h2>
          {hasFilters && (
            <>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                {ANIMALS_LIST.emptySubtitle}
              </p>
              <button
                onClick={clearAllFilters}
                className="px-6 py-2.5 bg-[#E8622A] text-white rounded-lg hover:bg-[#d4571f] transition-colors font-medium"
              >
                {ANIMALS_LIST.emptyClearFilters}
              </button>
            </>
          )}
        </div>
      )}

      {/* Animal Grid */}
      {!isLoading && !error && animals.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {animals.map((animal) => (
              <Link
                key={animal.id}
                href={`/animals/${animal.id}`}
                className="group bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                {/* Photo with overlay badge */}
                <div className="relative aspect-[4/3] overflow-hidden">
                  {animal.primary_photo_url ? (
                    <Image
                      src={animal.primary_photo_url}
                      alt={animal.name}
                      fill
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                      className="object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <AnimalPlaceholder species={animal.species} />
                  )}
                  {/* Status badge overlay */}
                  <span
                    className={`absolute top-3 right-3 text-xs px-2.5 py-1 rounded-full font-medium shadow-sm ${statusBadgeClass(animal.status)}`}
                  >
                    {STATUS_LABELS[animal.status]}
                  </span>
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-[#E8622A] transition-colors mb-1">
                    {animal.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {SPECIES_LABELS[animal.species] ?? animal.species}
                    {animal.birth_date && (
                      <span className="ml-2 text-gray-400">
                        {calculateAge(animal.birth_date)}
                      </span>
                    )}
                  </p>
                  {animal.description && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">
                      {animal.description}
                    </p>
                  )}
                  <p className="text-sm font-medium text-[#E8622A] mt-3 group-hover:underline">
                    {ANIMALS_LIST.meetAnimal(animal.name)}
                  </p>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center gap-4 mt-10">
            <button
              onClick={() => router.push(buildUrl({ offset: String(Math.max(0, currentOffset - PAGE_SIZE)) }))}
              disabled={currentOffset === 0}
              className="px-5 py-2.5 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {ANIMALS_LIST.previous}
            </button>
            <button
              onClick={() => router.push(buildUrl({ offset: String(currentOffset + PAGE_SIZE) }))}
              disabled={!hasMore}
              className="px-5 py-2.5 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {ANIMALS_LIST.next}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
