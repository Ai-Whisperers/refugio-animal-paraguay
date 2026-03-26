"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import type { Animal, AnimalSpecies } from "@/types/api";
import { listAnimalsPublic } from "@/lib/public-api";
import { STATUS_LABELS, statusBadgeClass, calculateAge } from "@/lib/animal-utils";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";

const SPECIES_OPTIONS: { value: AnimalSpecies | ""; label: string }[] = [
  { value: "", label: "All Species" },
  { value: "dog", label: "Dogs" },
  { value: "cat", label: "Cats" },
  { value: "other", label: "Other" },
];

const PAGE_SIZE = 12;

export default function AnimalsPage() {
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [speciesFilter, setSpeciesFilter] = useState<AnimalSpecies | "">("");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const fetchAnimals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listAnimalsPublic({
        species: speciesFilter || undefined,
        status: "available",
        offset,
        limit: PAGE_SIZE + 1,
      });
      // Fetch PAGE_SIZE + 1 to detect if there are more pages
      setHasMore(result.length > PAGE_SIZE);
      setAnimals(result.slice(0, PAGE_SIZE));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load animals");
    } finally {
      setIsLoading(false);
    }
  }, [speciesFilter, offset]);

  useEffect(() => {
    fetchAnimals();
  }, [fetchAnimals]);

  function handleSpeciesChange(value: string) {
    setSpeciesFilter(value as AnimalSpecies | "");
    setOffset(0);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Page Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-heading font-bold text-gray-900 mb-3">
          Animals Available for Adoption
        </h1>
        <p className="text-gray-500 max-w-2xl mx-auto">
          Meet our furry friends who are looking for their forever home.
          Click on any animal to learn more and start the adoption process.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-8 justify-center">
        {SPECIES_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleSpeciesChange(opt.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              speciesFilter === opt.value
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-r-transparent" />
          <p className="mt-3 text-gray-500">Loading animals...</p>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchAnimals}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && animals.length === 0 && (
        <div className="text-center py-12">
          <p className="text-5xl mb-4">🐾</p>
          <p className="text-gray-500 text-lg">
            No animals available right now. Check back soon!
          </p>
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
                className="group bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Photo */}
                {animal.primary_photo_url ? (
                  <Image
                    src={animal.primary_photo_url}
                    alt={animal.name}
                    width={400}
                    height={192}
                    className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                    unoptimized
                  />
                ) : (
                  <AnimalPlaceholder species={animal.species} />
                )}

                {/* Info */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {animal.name}
                    </h3>
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${statusBadgeClass(animal.status)}`}
                    >
                      {STATUS_LABELS[animal.status]}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 capitalize">
                    {animal.species}
                    {animal.birth_date && (
                      <span className="ml-2">
                        {calculateAge(animal.birth_date)}
                      </span>
                    )}
                  </p>
                  {animal.description && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">
                      {animal.description}
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center gap-4 mt-10">
            <button
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={offset === 0}
              className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + PAGE_SIZE)}
              disabled={!hasMore}
              className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
