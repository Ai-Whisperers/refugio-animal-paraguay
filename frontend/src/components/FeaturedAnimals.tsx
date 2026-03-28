"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, PawPrint } from "lucide-react";
import { listAnimalsPublic } from "@/lib/public-api";
import { PublicAnimalListItem } from "@/types/api";
import { HOME } from "@/lib/strings";

const FEATURED_PAGE_SIZE = 6;
const AUTO_ROTATE_MS = 5000;

/** Species label in Spanish. */
function speciesLabel(species: string): string {
  const labels: Record<string, string> = {
    dog: "Perro",
    cat: "Gato",
    other: "Otro",
  };
  return labels[species] ?? species;
}

/** Age string from birth_date ISO string. */
function ageLabel(birthDate: string | null): string {
  if (!birthDate) return "";
  const birth = new Date(birthDate);
  const now = new Date();
  const months =
    (now.getFullYear() - birth.getFullYear()) * 12 +
    (now.getMonth() - birth.getMonth());
  if (months < 1) return "< 1 mes";
  if (months < 12) return `${months} ${months === 1 ? "mes" : "meses"}`;
  const years = Math.floor(months / 12);
  const rem = months % 12;
  if (rem === 0) return `${years} ${years === 1 ? "ano" : "anos"}`;
  return `${years} ${years === 1 ? "ano" : "anos"}, ${rem} ${rem === 1 ? "mes" : "meses"}`;
}

export default function FeaturedAnimals() {
  const [animals, setAnimals] = useState<PublicAnimalListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listAnimalsPublic({ featured: true, page_size: FEATURED_PAGE_SIZE })
      .then((res) => {
        if (!cancelled) setAnimals(res.items);
      })
      .catch(() => {
        // Silently fail — carousel simply won't render
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const visibleCount = Math.min(animals.length, 3);

  const next = useCallback(() => {
    if (animals.length <= visibleCount) return;
    setCurrentIndex((prev) => (prev + 1) % animals.length);
  }, [animals.length, visibleCount]);

  const prev = useCallback(() => {
    if (animals.length <= visibleCount) return;
    setCurrentIndex((prev) => (prev - 1 + animals.length) % animals.length);
  }, [animals.length, visibleCount]);

  // Auto-rotate
  useEffect(() => {
    if (isPaused || animals.length <= visibleCount) return;
    const timer = setInterval(next, AUTO_ROTATE_MS);
    return () => clearInterval(timer);
  }, [isPaused, next, animals.length, visibleCount]);

  // Don't render section if no featured animals or still loading
  if (loading || animals.length === 0) return null;

  /** Get the visible slice wrapping around the array. */
  const visibleAnimals: PublicAnimalListItem[] = [];
  for (let i = 0; i < visibleCount; i++) {
    visibleAnimals.push(animals[(currentIndex + i) % animals.length]);
  }

  return (
    <section
      className="py-10 sm:py-16 px-4 bg-white"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8 sm:mb-10">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-2">
            {HOME.featuredTitle}
          </h2>
          <p className="text-gray-600">{HOME.featuredSubtitle}</p>
        </div>

        <div className="relative">
          {/* Navigation arrows */}
          {animals.length > visibleCount && (
            <>
              <button
                onClick={prev}
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3 sm:-translate-x-5 z-10 w-10 h-10 bg-white rounded-full shadow-md border border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
                aria-label="Anterior"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600" />
              </button>
              <button
                onClick={next}
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3 sm:translate-x-5 z-10 w-10 h-10 bg-white rounded-full shadow-md border border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
                aria-label="Siguiente"
              >
                <ChevronRight className="w-5 h-5 text-gray-600" />
              </button>
            </>
          )}

          {/* Cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {visibleAnimals.map((animal) => (
              <Link
                key={animal.id}
                href={`/animals/${animal.id}`}
                className="group bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-md hover:border-primary-200 transition-all"
              >
                {/* Photo */}
                <div className="aspect-[4/3] bg-gray-100 relative overflow-hidden">
                  {animal.primary_photo_url ? (
                    <img
                      src={animal.primary_photo_url}
                      alt={animal.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <PawPrint className="w-12 h-12 text-gray-300" />
                    </div>
                  )}
                  {/* Featured badge */}
                  <span className="absolute top-3 left-3 bg-orange-500 text-white text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm">
                    Destacado
                  </span>
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                    {animal.name}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                    <span>{speciesLabel(animal.species)}</span>
                    {animal.breed && (
                      <>
                        <span aria-hidden="true">&middot;</span>
                        <span>{animal.breed}</span>
                      </>
                    )}
                    {animal.birth_date && (
                      <>
                        <span aria-hidden="true">&middot;</span>
                        <span>{ageLabel(animal.birth_date)}</span>
                      </>
                    )}
                  </div>
                  {animal.description && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {animal.description}
                    </p>
                  )}
                  <span className="inline-block mt-3 text-sm font-medium text-primary-600 group-hover:text-primary-700">
                    {HOME.featuredAdopt} &rarr;
                  </span>
                </div>
              </Link>
            ))}
          </div>

          {/* Dot indicators */}
          {animals.length > visibleCount && (
            <div className="flex justify-center gap-2 mt-6">
              {animals.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentIndex(idx)}
                  className={`w-2.5 h-2.5 rounded-full transition-colors ${
                    idx === currentIndex
                      ? "bg-primary-600"
                      : "bg-gray-300 hover:bg-gray-400"
                  }`}
                  aria-label={`Ir al animal ${idx + 1}`}
                />
              ))}
            </div>
          )}
        </div>

        {/* View all link */}
        <div className="text-center mt-8">
          <Link
            href="/animals"
            className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium transition-colors"
          >
            {HOME.featuredViewAll} &rarr;
          </Link>
        </div>
      </div>
    </section>
  );
}
