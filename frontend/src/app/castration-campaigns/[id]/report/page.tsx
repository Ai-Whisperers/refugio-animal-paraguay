"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getCastrationCampaignReport } from "@/lib/public-api";
import type { ImpactReportResponse } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  title: "Reporte de Impacto",
  subtitle: "Resultados de la campana de castracion",
  back: "Volver a la campana",
  loading: "Cargando reporte...",
  error: "No se pudo cargar el reporte.",
  campaignComplete: "Campana Completada",
  campaignActive: "Campana en Curso",
  campaignPlanned: "Campana Planificada",

  // Stats
  animalsCastrated: "Animales Castrados",
  targetGoal: "Meta",
  progress: "Progreso",
  durationDays: "Dias de Campana",
  partnerClinics: "Clinicas Asociadas",
  totalDrives: "Jornadas Realizadas",
  completedDrives: "Jornadas Completadas",
  registeredAnimals: "Registrados",
  completedAnimals: "Completados en Jornadas",

  // Sections
  byTheNumbers: "En Numeros",
  clinicsSection: "Clinicas Asociadas",
  drivesSection: "Jornadas de Castracion",
  photoSection: "Galeria de Fotos",
  impactStory: "Historia de Impacto",
  areaSection: "Area de Cobertura",

  // Photo types
  beforePhotos: "Antes",
  afterPhotos: "Despues",
  recoveryPhotos: "Recuperacion",
  totalPhotos: "Total de fotos",
  noPhotos: "Aun no hay fotos disponibles.",

  // Clinics
  drivesHosted: "jornadas",
  noClinics: "Sin clinicas asociadas aun.",

  // Share
  shareReport: "Compartir Reporte",
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function statusLabel(status: string, isComplete: boolean): string {
  if (isComplete) return S.campaignComplete;
  if (status === "active") return S.campaignActive;
  return S.campaignPlanned;
}

function statusColor(status: string, isComplete: boolean): string {
  if (isComplete) return "bg-emerald-100 text-emerald-800";
  if (status === "active") return "bg-blue-100 text-blue-800";
  return "bg-gray-100 text-gray-800";
}

// ---------------------------------------------------------------------------
// Stat Card
// ---------------------------------------------------------------------------

function StatCard({
  value,
  label,
  accent = false,
}: {
  value: string | number;
  label: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-5 text-center ${
        accent
          ? "bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg"
          : "bg-white border border-gray-200 shadow-sm"
      }`}
    >
      <p
        className={`text-3xl font-bold ${accent ? "text-white" : "text-gray-900"}`}
      >
        {value}
      </p>
      <p
        className={`mt-1 text-sm font-medium ${accent ? "text-emerald-100" : "text-gray-500"}`}
      >
        {label}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Progress Ring
// ---------------------------------------------------------------------------

function ProgressRing({ percent }: { percent: number }) {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative mx-auto h-32 w-32">
      <svg className="h-32 w-32 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={percent >= 100 ? "#10b981" : "#3b82f6"}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-gray-900">{percent}%</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CastrationImpactReportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [report, setReport] = useState<ImpactReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const campaignId = params.id;

  useEffect(() => {
    async function load() {
      try {
        const data = await getCastrationCampaignReport(campaignId);
        setReport(data);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [campaignId]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div
            className="mx-auto h-10 w-10 animate-spin rounded-full border-4
                        border-emerald-200 border-t-emerald-600"
          />
          <p className="mt-4 text-gray-500">{S.loading}</p>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-red-600">{S.error}</p>
          <button
            type="button"
            onClick={() => router.back()}
            className="mt-4 text-sm text-emerald-600 hover:text-emerald-700"
          >
            {S.back}
          </button>
        </div>
      </main>
    );
  }

  const badge = statusLabel(report.status, report.is_complete);
  const badgeColor = statusColor(report.status, report.is_complete);

  return (
    <main className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Back button */}
      <button
        type="button"
        onClick={() => router.back()}
        className="mb-6 inline-flex items-center gap-1 text-sm text-emerald-600
                   hover:text-emerald-700"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        {S.back}
      </button>

      {/* Hero */}
      <div className="mb-10 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 p-8 text-white shadow-xl sm:p-12">
        <div className="flex items-start justify-between gap-4">
          <div>
            <span
              className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${badgeColor}`}
            >
              {badge}
            </span>
            <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
              {report.title}
            </h1>
            <p className="mt-2 text-emerald-100">{S.subtitle}</p>
          </div>
          <ProgressRing percent={report.progress_percent} />
        </div>
        <p className="mt-4 text-sm text-emerald-100">
          {formatDate(report.start_date)} — {formatDate(report.end_date)} (
          {report.campaign_duration_days} {S.durationDays.toLowerCase()})
        </p>
        <p className="mt-2 text-emerald-50">{report.description}</p>
      </div>

      {/* By The Numbers */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          {S.byTheNumbers}
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            value={report.completed_count}
            label={S.animalsCastrated}
            accent
          />
          <StatCard value={report.target_count} label={S.targetGoal} />
          <StatCard value={report.total_clinics} label={S.partnerClinics} />
          <StatCard
            value={report.campaign_duration_days}
            label={S.durationDays}
          />
        </div>
      </section>

      {/* Partner Clinics */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          {S.clinicsSection}
        </h2>
        {report.clinics.length === 0 ? (
          <p className="text-gray-500">{S.noClinics}</p>
        ) : (
          <div className="space-y-3">
            {report.clinics.map((clinic) => (
              <div
                key={clinic.clinic_id}
                className="flex items-center justify-between rounded-lg border
                           border-gray-200 bg-white px-5 py-3 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-full
                                bg-emerald-100 text-emerald-700"
                  >
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14
                           0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1
                           4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                      />
                    </svg>
                  </div>
                  <span className="font-medium text-gray-900">
                    {clinic.clinic_name}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {clinic.drives_hosted} {S.drivesHosted}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Drives Summary */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          {S.drivesSection}
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            value={report.drives.total_drives}
            label={S.totalDrives}
          />
          <StatCard
            value={report.drives.completed_drives}
            label={S.completedDrives}
          />
          <StatCard
            value={report.drives.total_registered}
            label={S.registeredAnimals}
          />
          <StatCard
            value={report.drives.total_completed}
            label={S.completedAnimals}
          />
        </div>
      </section>

      {/* Photo Gallery */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          {S.photoSection}
        </h2>
        {report.photos.total_photos === 0 ? (
          <div className="rounded-xl bg-gray-50 py-12 text-center">
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
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2
                   2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2
                   2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="mt-4 text-gray-500">{S.noPhotos}</p>
          </div>
        ) : (
          <>
            <div className="mb-4 flex gap-4 text-sm">
              <span className="rounded-full bg-blue-100 px-3 py-1 text-blue-800">
                {report.photos.before_count} {S.beforePhotos}
              </span>
              <span className="rounded-full bg-green-100 px-3 py-1 text-green-800">
                {report.photos.after_count} {S.afterPhotos}
              </span>
              <span className="rounded-full bg-purple-100 px-3 py-1 text-purple-800">
                {report.photos.recovery_count} {S.recoveryPhotos}
              </span>
              <span className="text-gray-500">
                {report.photos.total_photos} {S.totalPhotos.toLowerCase()}
              </span>
            </div>
            {report.photos.featured_urls.length > 0 && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {report.photos.featured_urls.map((url, idx) => (
                  <div
                    key={url}
                    className="aspect-square overflow-hidden rounded-lg"
                  >
                    <img
                      src={url}
                      alt={`${S.photoSection} ${idx + 1}`}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      {/* Coverage Area */}
      <section className="mb-10">
        <h2 className="mb-4 text-xl font-bold text-gray-900">
          {S.areaSection}
        </h2>
        <div
          className="flex items-center gap-3 rounded-lg border border-gray-200
                     bg-white px-5 py-4 shadow-sm"
        >
          <svg
            className="h-6 w-6 text-emerald-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827
                 0l-4.244-4.243a8 8 0 1111.314 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span className="text-lg font-medium text-gray-900">
            {report.target_area}
          </span>
        </div>
      </section>
    </main>
  );
}
