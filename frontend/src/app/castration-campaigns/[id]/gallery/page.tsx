"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { getCastrationCampaignGallery } from "@/lib/public-api";
import type { CastrationPhotoPublic, CastrationPhotoType } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  title: "Galeria de Castraciones",
  subtitle: "Fotos de los animales atendidos en esta campana",
  filterAll: "Todas",
  filterBefore: "Antes",
  filterAfter: "Despues",
  filterRecovery: "Recuperacion",
  featured: "Destacada",
  noPhotos: "Aun no hay fotos publicadas para esta campana.",
  loadMore: "Cargar mas",
  loading: "Cargando...",
  back: "Volver a la campana",
  species: "Especie",
  closeModal: "Cerrar",
} as const;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type FilterType = "all" | CastrationPhotoType;

const FILTERS: { key: FilterType; label: string }[] = [
  { key: "all", label: S.filterAll },
  { key: "before", label: S.filterBefore },
  { key: "after", label: S.filterAfter },
  { key: "recovery", label: S.filterRecovery },
];

const PAGE_SIZE = 12;

// ---------------------------------------------------------------------------
// Photo card
// ---------------------------------------------------------------------------

function PhotoCard({
  photo,
  onSelect,
}: {
  photo: CastrationPhotoPublic;
  onSelect: (p: CastrationPhotoPublic) => void;
}) {
  const typeBadgeColor: Record<CastrationPhotoType, string> = {
    before: "bg-amber-100 text-amber-800",
    after: "bg-green-100 text-green-800",
    recovery: "bg-blue-100 text-blue-800",
  };

  return (
    <button
      type="button"
      onClick={() => onSelect(photo)}
      className="group relative overflow-hidden rounded-xl bg-white shadow-md
                 transition-all hover:shadow-lg hover:-translate-y-0.5
                 focus:outline-none focus:ring-2 focus:ring-emerald-500"
    >
      {/* Photo */}
      <div className="aspect-square overflow-hidden">
        <img
          src={photo.photo_url}
          alt={photo.animal_name}
          className="h-full w-full object-cover transition-transform
                     group-hover:scale-105"
          loading="lazy"
        />
      </div>

      {/* Info overlay */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70
                      to-transparent p-4 text-left">
        <p className="text-sm font-semibold text-white">{photo.animal_name}</p>
        {photo.animal_species && (
          <p className="text-xs text-white/80">{photo.animal_species}</p>
        )}
      </div>

      {/* Type badge */}
      <span
        className={`absolute top-3 left-3 rounded-full px-2.5 py-0.5 text-xs
                    font-medium ${typeBadgeColor[photo.photo_type]}`}
      >
        {photo.photo_type === "before"
          ? S.filterBefore
          : photo.photo_type === "after"
            ? S.filterAfter
            : S.filterRecovery}
      </span>

      {/* Featured badge */}
      {photo.is_featured && (
        <span
          className="absolute top-3 right-3 rounded-full bg-yellow-400 px-2.5
                     py-0.5 text-xs font-medium text-yellow-900"
        >
          {S.featured}
        </span>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Lightbox modal
// ---------------------------------------------------------------------------

function Lightbox({
  photo,
  onClose,
}: {
  photo: CastrationPhotoPublic;
  onClose: () => void;
}) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center
                 bg-black/80 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={photo.animal_name}
    >
      <div
        className="relative max-h-[90vh] max-w-4xl overflow-hidden rounded-2xl
                   bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-3 right-3 z-10 rounded-full bg-black/50 p-2
                     text-white transition-colors hover:bg-black/70"
          aria-label={S.closeModal}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <img
          src={photo.photo_url}
          alt={photo.animal_name}
          className="max-h-[75vh] w-full object-contain"
        />
        <div className="p-4">
          <h3 className="text-lg font-bold text-gray-900">{photo.animal_name}</h3>
          {photo.animal_species && (
            <p className="text-sm text-gray-500">
              {S.species}: {photo.animal_species}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-400">
            {new Date(photo.uploaded_at).toLocaleDateString("es-PY")}
          </p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Gallery page
// ---------------------------------------------------------------------------

export default function CastrationGalleryPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [photos, setPhotos] = useState<CastrationPhotoPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterType>("all");
  const [selected, setSelected] = useState<CastrationPhotoPublic | null>(null);

  const campaignId = params.id;

  const fetchPhotos = useCallback(
    async (pageNum: number, activeFilter: FilterType, append: boolean) => {
      setLoading(true);
      try {
        const typeParam = activeFilter === "all" ? undefined : activeFilter;
        const data = await getCastrationCampaignGallery(
          campaignId,
          pageNum,
          PAGE_SIZE,
          typeParam
        );
        setPhotos((prev) => (append ? [...prev, ...data.items] : data.items));
        setTotal(data.total);
      } catch {
        // Network error — keep existing photos
      } finally {
        setLoading(false);
      }
    },
    [campaignId]
  );

  // Initial load and filter changes
  useEffect(() => {
    setPage(1);
    fetchPhotos(1, filter, false);
  }, [filter, fetchPhotos]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchPhotos(nextPage, filter, true);
  };

  const hasMore = photos.length < total;

  return (
    <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <button
          type="button"
          onClick={() => router.back()}
          className="mb-4 inline-flex items-center gap-1 text-sm text-emerald-600
                     hover:text-emerald-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 19l-7-7 7-7" />
          </svg>
          {S.back}
        </button>
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">{S.title}</h1>
        <p className="mt-2 text-lg text-gray-600">{S.subtitle}</p>
      </div>

      {/* Filter tabs */}
      <div className="mb-8 flex flex-wrap gap-2">
        {FILTERS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilter(key)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors
              ${
                filter === key
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto self-center text-sm text-gray-500">
          {total} {total === 1 ? "foto" : "fotos"}
        </span>
      </div>

      {/* Grid */}
      {!loading && photos.length === 0 ? (
        <div className="rounded-xl bg-gray-50 py-16 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159
                 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909
                 2.909M3.75 21h16.5a1.5 1.5 0 001.5-1.5V5.25a1.5 1.5 0
                 00-1.5-1.5H3.75a1.5 1.5 0 00-1.5 1.5v14.25a1.5 1.5 0
                 001.5 1.5z"
            />
          </svg>
          <p className="mt-4 text-gray-500">{S.noPhotos}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {photos.map((photo) => (
            <PhotoCard key={photo.id} photo={photo} onSelect={setSelected} />
          ))}
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="mt-8 text-center">
          <button
            type="button"
            onClick={handleLoadMore}
            disabled={loading}
            className="rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-medium
                       text-white shadow-sm transition-colors hover:bg-emerald-700
                       disabled:opacity-50"
          >
            {loading ? S.loading : S.loadMore}
          </button>
        </div>
      )}

      {/* Loading spinner */}
      {loading && photos.length === 0 && (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-4
                          border-emerald-200 border-t-emerald-600" />
        </div>
      )}

      {/* Lightbox */}
      {selected && <Lightbox photo={selected} onClose={() => setSelected(null)} />}
    </main>
  );
}
