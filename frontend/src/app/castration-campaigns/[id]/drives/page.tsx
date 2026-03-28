"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { getCastrationCampaignDrives } from "@/lib/public-api";
import type { CastrationDrivePublic } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  title: "Jornadas de Castracion",
  subtitle: "Proximas jornadas programadas para esta campana",
  back: "Volver a la campana",
  noDrives: "No hay jornadas programadas por el momento.",
  spotsAvailable: "lugares disponibles",
  spotAvailable: "lugar disponible",
  full: "Cupo completo",
  registered: "registrados",
  completed: "completados",
  scheduled: "Programada",
  inProgress: "En curso",
  completedStatus: "Completada",
  cancelled: "Cancelada",
  showPast: "Mostrar jornadas pasadas",
  hidePast: "Ocultar jornadas pasadas",
  loadMore: "Ver mas jornadas",
  loading: "Cargando...",
  contact: "Contacto",
  location: "Ubicacion",
  time: "Horario",
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("es-PY", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatTime(timeStr: string | null): string {
  if (!timeStr) return "";
  return timeStr.slice(0, 5);
}

function statusBadge(status: string): { label: string; color: string } {
  switch (status) {
    case "scheduled":
      return { label: S.scheduled, color: "bg-blue-100 text-blue-800" };
    case "in_progress":
      return { label: S.inProgress, color: "bg-yellow-100 text-yellow-800" };
    case "completed":
      return { label: S.completedStatus, color: "bg-green-100 text-green-800" };
    case "cancelled":
      return { label: S.cancelled, color: "bg-red-100 text-red-800" };
    default:
      return { label: status, color: "bg-gray-100 text-gray-800" };
  }
}

// ---------------------------------------------------------------------------
// Drive card
// ---------------------------------------------------------------------------

function DriveCard({ drive }: { drive: CastrationDrivePublic }) {
  const badge = statusBadge(drive.status);
  const spotsText =
    drive.spots_available === 1
      ? `1 ${S.spotAvailable}`
      : `${drive.spots_available} ${S.spotsAvailable}`;

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm
                    transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="border-b border-gray-100 bg-gradient-to-r from-emerald-50 to-teal-50 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-gray-900">{drive.title}</h3>
            <p className="mt-1 text-sm font-medium text-emerald-700">
              {formatDate(drive.drive_date)}
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${badge.color}`}>
            {badge.label}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="space-y-3 p-5">
        {drive.description && (
          <p className="text-sm text-gray-600">{drive.description}</p>
        )}

        {/* Location */}
        <div className="flex items-start gap-2">
          <svg className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" fill="none"
               viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827
                     0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-gray-900">{drive.location_name}</p>
            {drive.location_address && (
              <p className="text-xs text-gray-500">{drive.location_address}</p>
            )}
          </div>
        </div>

        {/* Time */}
        {(drive.start_time || drive.end_time) && (
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-gray-600">
              {formatTime(drive.start_time)}
              {drive.end_time && ` - ${formatTime(drive.end_time)}`}
            </p>
          </div>
        )}

        {/* Contact */}
        {(drive.contact_name || drive.contact_phone) && (
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24"
                 stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498
                       4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042
                       0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493
                       1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716
                       21 3 14.284 3 6V5z" />
            </svg>
            <p className="text-sm text-gray-600">
              {drive.contact_name}
              {drive.contact_name && drive.contact_phone && " - "}
              {drive.contact_phone}
            </p>
          </div>
        )}
      </div>

      {/* Footer: capacity bar */}
      <div className="border-t border-gray-100 bg-gray-50 px-5 py-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">
            {drive.registered_count} {S.registered}
          </span>
          {drive.is_full ? (
            <span className="font-semibold text-red-600">{S.full}</span>
          ) : (
            <span className="font-semibold text-emerald-600">{spotsText}</span>
          )}
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-gray-200">
          <div
            className={`h-full rounded-full transition-all ${
              drive.is_full ? "bg-red-400" : "bg-emerald-500"
            }`}
            style={{
              width: `${Math.min(100, (drive.registered_count / drive.max_capacity) * 100)}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const PAGE_SIZE = 10;

export default function CastrationDrivesPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [drives, setDrives] = useState<CastrationDrivePublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showPast, setShowPast] = useState(false);

  const campaignId = params.id;

  const fetchDrives = useCallback(
    async (pageNum: number, includePast: boolean, append: boolean) => {
      setLoading(true);
      try {
        const data = await getCastrationCampaignDrives(
          campaignId,
          pageNum,
          PAGE_SIZE,
          includePast
        );
        setDrives((prev) => (append ? [...prev, ...data.items] : data.items));
        setTotal(data.total);
      } catch {
        // Keep existing data
      } finally {
        setLoading(false);
      }
    },
    [campaignId]
  );

  useEffect(() => {
    setPage(1);
    fetchDrives(1, showPast, false);
  }, [showPast, fetchDrives]);

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchDrives(nextPage, showPast, true);
  };

  const hasMore = drives.length < total;

  return (
    <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
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

      {/* Toggle past drives */}
      <div className="mb-6 flex items-center justify-between">
        <span className="text-sm text-gray-500">
          {total} {total === 1 ? "jornada" : "jornadas"}
        </span>
        <button
          type="button"
          onClick={() => setShowPast(!showPast)}
          className="text-sm font-medium text-emerald-600 hover:text-emerald-700"
        >
          {showPast ? S.hidePast : S.showPast}
        </button>
      </div>

      {/* Drive list */}
      {!loading && drives.length === 0 ? (
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
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0
                 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2
                 2 0 002 2z"
            />
          </svg>
          <p className="mt-4 text-gray-500">{S.noDrives}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {drives.map((drive) => (
            <DriveCard key={drive.id} drive={drive} />
          ))}
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="mt-6 text-center">
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
      {loading && drives.length === 0 && (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-4
                          border-emerald-200 border-t-emerald-600" />
        </div>
      )}
    </main>
  );
}
