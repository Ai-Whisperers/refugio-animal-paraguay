"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  PawPrint,
  ArrowLeft,
  RefreshCw,
  Pencil,
  Calendar,
  Clock,
  Dog,
  Cat,
  CircleDot,
  ArrowRightLeft,
  ChevronRight,
  ImageIcon,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import {
  STATUS_LABELS,
  STATUS_COLORS,
  VALID_TRANSITIONS,
} from "@/lib/animal-status";
import StatusWorkflowModal from "@/components/admin/StatusWorkflowModal";
import type { Animal, AnimalStatus, AnimalPhoto } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Detalle del Animal";
const LABEL_BACK = "Volver a la lista";
const LABEL_LOADING = "Cargando animal...";
const LABEL_ERROR = "Error al cargar el animal";
const LABEL_NOT_FOUND = "Animal no encontrado";
const LABEL_RETRY = "Reintentar";
const LABEL_EDIT = "Editar";
const LABEL_CHANGE_STATUS = "Cambiar Estado";
const LABEL_INFO_SECTION = "Informacion General";
const LABEL_PHOTOS_SECTION = "Galeria de Fotos";
const LABEL_HISTORY_SECTION = "Historial";
const LABEL_NO_DESCRIPTION = "Sin descripcion";
const LABEL_NO_PHOTOS = "No hay fotos registradas";
const LABEL_SPECIES = "Especie";
const LABEL_BREED = "Raza";
const LABEL_SIZE = "Tamano";
const LABEL_GENDER = "Sexo";
const LABEL_BIRTH_DATE = "Fecha de nacimiento";
const LABEL_INTAKE_DATE = "Fecha de ingreso";
const LABEL_LAST_UPDATED = "Ultima actualizacion";
const LABEL_STATUS = "Estado";
const LABEL_UNKNOWN = "Desconocido";
const LABEL_CREATED_EVENT = "Ingresado al sistema";
const LABEL_UPDATED_EVENT = "Ultima modificacion registrada";

const SPECIES_LABELS: Record<string, string> = {
  dog: "Perro",
  cat: "Gato",
  other: "Otro",
};

const SIZE_LABELS: Record<string, string> = {
  small: "Pequeno",
  medium: "Mediano",
  large: "Grande",
  extra_large: "Extra grande",
};

const GENDER_LABELS: Record<string, string> = {
  male: "Macho",
  female: "Hembra",
  unknown: "Desconocido",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return LABEL_UNKNOWN;
  const date = new Date(dateStr);
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function SpeciesIcon({ species }: { species: string }) {
  if (species === "dog") return <Dog className="h-5 w-5" />;
  if (species === "cat") return <Cat className="h-5 w-5" />;
  return <PawPrint className="h-5 w-5" />;
}

interface InfoRowProps {
  label: string;
  value: string | null;
  icon?: React.ReactNode;
}

function InfoRow({ label, value, icon }: InfoRowProps) {
  return (
    <div className="flex items-start gap-3 py-2.5">
      {icon && (
        <span className="mt-0.5 flex-shrink-0 text-warm-text-tertiary">
          {icon}
        </span>
      )}
      <div className="min-w-0">
        <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm text-warm-text-primary">
          {value || LABEL_UNKNOWN}
        </dd>
      </div>
    </div>
  );
}

interface TimelineEvent {
  id: string;
  date: string;
  label: string;
  detail?: string;
  type: "status" | "created" | "updated";
}

function buildTimeline(animal: Animal): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  // Created event
  events.push({
    id: "created",
    date: animal.created_at,
    label: LABEL_CREATED_EVENT,
    detail: `${STATUS_LABELS[animal.status as AnimalStatus] ?? animal.status}`,
    type: "created",
  });

  // If updated_at differs from created_at, add an update event
  if (animal.updated_at !== animal.created_at) {
    events.push({
      id: "updated",
      date: animal.updated_at,
      label: LABEL_UPDATED_EVENT,
      detail: `Estado actual: ${STATUS_LABELS[animal.status as AnimalStatus] ?? animal.status}`,
      type: "updated",
    });
  }

  // Sort newest first
  events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return events;
}

const TIMELINE_DOT_COLORS: Record<string, string> = {
  created: "bg-green-500",
  updated: "bg-blue-500",
  status: "bg-orange-500",
};

export default function AnimalDetailPage() {
  const router = useRouter();
  const params = useParams();
  const animalId = params.id as string;

  const [isChecking, setIsChecking] = useState(true);
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedPhoto, setSelectedPhoto] = useState<AnimalPhoto | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchAnimal = useCallback(async () => {
    if (!animalId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<Animal>(`/animals/${animalId}`);
      setAnimal(data);
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 404) {
        setError(LABEL_NOT_FOUND);
      } else if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [animalId]);

  useEffect(() => {
    if (isChecking) return;
    fetchAnimal();
  }, [isChecking, fetchAnimal]);

  function handleStatusChanged(newStatus: AnimalStatus) {
    setShowStatusModal(false);
    // Refresh animal data to reflect new status
    fetchAnimal();
  }

  if (isChecking || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-warm-text-secondary">{error}</p>
        <button
          onClick={() => fetchAnimal()}
          className="text-sm font-medium text-primary-600 underline hover:text-primary-700"
        >
          {LABEL_RETRY}
        </button>
      </div>
    );
  }

  if (!animal) return null;

  const timeline = buildTimeline(animal);
  const hasValidTransitions = (VALID_TRANSITIONS[animal.status as AnimalStatus] ?? []).length > 0;

  return (
    <div className="min-h-screen bg-warm-bg">
      {/* Header */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/animals")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <SpeciesIcon species={animal.species} />
            <div>
              <h1 className="text-lg font-semibold text-warm-text-primary">
                {animal.name}
              </h1>
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[animal.status as AnimalStatus]}`}
              >
                {STATUS_LABELS[animal.status as AnimalStatus]}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasValidTransitions && (
              <button
                onClick={() => setShowStatusModal(true)}
                className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
              >
                <ArrowRightLeft className="h-4 w-4" />
                {LABEL_CHANGE_STATUS}
              </button>
            )}
            <button
              onClick={() => router.push(`/admin/animals/${animalId}/edit`)}
              className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              <Pencil className="h-4 w-4" />
              {LABEL_EDIT}
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main content — left 2 cols */}
          <div className="space-y-6 lg:col-span-2">
            {/* Primary photo + description */}
            <section className="rounded-xl border border-warm-border bg-warm-surface p-5">
              {animal.primary_photo_url && (
                <div className="mb-4 overflow-hidden rounded-lg">
                  <img
                    src={animal.primary_photo_url}
                    alt={animal.name}
                    className="h-64 w-full object-cover"
                  />
                </div>
              )}
              <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-warm-text-tertiary">
                Descripcion
              </h2>
              <p className="text-sm leading-relaxed text-warm-text-secondary">
                {animal.description || LABEL_NO_DESCRIPTION}
              </p>
            </section>

            {/* Photo gallery */}
            <section className="rounded-xl border border-warm-border bg-warm-surface p-5">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-warm-text-tertiary">
                {LABEL_PHOTOS_SECTION}
              </h2>
              {animal.photos && animal.photos.length > 0 ? (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {animal.photos
                    .sort((a, b) => a.display_order - b.display_order)
                    .map((photo) => (
                      <button
                        key={photo.id}
                        onClick={() => setSelectedPhoto(photo)}
                        className="group relative overflow-hidden rounded-lg border border-warm-border"
                      >
                        <img
                          src={photo.url}
                          alt={photo.caption || animal.name}
                          className="h-32 w-full object-cover transition-transform group-hover:scale-105"
                        />
                        {photo.caption && (
                          <div className="absolute inset-x-0 bottom-0 bg-black/50 px-2 py-1">
                            <p className="truncate text-xs text-white">
                              {photo.caption}
                            </p>
                          </div>
                        )}
                      </button>
                    ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-warm-text-tertiary">
                  <ImageIcon className="mb-2 h-8 w-8" />
                  <p className="text-sm">{LABEL_NO_PHOTOS}</p>
                </div>
              )}
            </section>

            {/* History timeline */}
            <section className="rounded-xl border border-warm-border bg-warm-surface p-5">
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-warm-text-tertiary">
                {LABEL_HISTORY_SECTION}
              </h2>
              <div className="space-y-0">
                {timeline.map((event, idx) => (
                  <div key={event.id} className="flex gap-3">
                    {/* Timeline line + dot */}
                    <div className="flex flex-col items-center">
                      <div
                        className={`h-3 w-3 rounded-full ${TIMELINE_DOT_COLORS[event.type]}`}
                      />
                      {idx < timeline.length - 1 && (
                        <div className="w-px flex-1 bg-warm-border" />
                      )}
                    </div>
                    {/* Event content */}
                    <div className="pb-5">
                      <p className="text-sm font-medium text-warm-text-primary">
                        {event.label}
                      </p>
                      {event.detail && (
                        <p className="mt-0.5 text-xs text-warm-text-secondary">
                          {event.detail}
                        </p>
                      )}
                      <p className="mt-1 text-xs text-warm-text-tertiary">
                        {formatDateTime(event.date)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Sidebar — right col */}
          <div className="space-y-6">
            {/* Info card */}
            <section className="rounded-xl border border-warm-border bg-warm-surface p-5">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-warm-text-tertiary">
                {LABEL_INFO_SECTION}
              </h2>
              <dl className="divide-y divide-warm-border">
                <InfoRow
                  label={LABEL_STATUS}
                  value={STATUS_LABELS[animal.status as AnimalStatus]}
                  icon={<CircleDot className="h-4 w-4" />}
                />
                <InfoRow
                  label={LABEL_SPECIES}
                  value={SPECIES_LABELS[animal.species] ?? animal.species}
                  icon={<SpeciesIcon species={animal.species} />}
                />
                <InfoRow
                  label={LABEL_BREED}
                  value={animal.breed}
                  icon={<PawPrint className="h-4 w-4" />}
                />
                <InfoRow
                  label={LABEL_SIZE}
                  value={animal.size ? (SIZE_LABELS[animal.size] ?? animal.size) : null}
                />
                <InfoRow
                  label={LABEL_GENDER}
                  value={animal.gender ? (GENDER_LABELS[animal.gender] ?? animal.gender) : null}
                />
                <InfoRow
                  label={LABEL_BIRTH_DATE}
                  value={formatDate(animal.birth_date)}
                  icon={<Calendar className="h-4 w-4" />}
                />
                <InfoRow
                  label={LABEL_INTAKE_DATE}
                  value={formatDate(animal.created_at)}
                  icon={<Clock className="h-4 w-4" />}
                />
                <InfoRow
                  label={LABEL_LAST_UPDATED}
                  value={formatDateTime(animal.updated_at)}
                />
              </dl>
            </section>

            {/* Quick actions */}
            <section className="rounded-xl border border-warm-border bg-warm-surface p-5">
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-warm-text-tertiary">
                Acciones
              </h2>
              <div className="space-y-2">
                <button
                  onClick={() => router.push(`/admin/animals/${animalId}/edit`)}
                  className="flex w-full items-center justify-between rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
                >
                  <span className="flex items-center gap-2">
                    <Pencil className="h-4 w-4" />
                    {LABEL_EDIT}
                  </span>
                  <ChevronRight className="h-4 w-4" />
                </button>
                {hasValidTransitions && (
                  <button
                    onClick={() => setShowStatusModal(true)}
                    className="flex w-full items-center justify-between rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
                  >
                    <span className="flex items-center gap-2">
                      <ArrowRightLeft className="h-4 w-4" />
                      {LABEL_CHANGE_STATUS}
                    </span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>

      {/* Photo lightbox */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setSelectedPhoto(null)}
          role="dialog"
          aria-modal="true"
          aria-label={selectedPhoto.caption || animal.name}
        >
          <div className="max-h-[90vh] max-w-4xl">
            <img
              src={selectedPhoto.url}
              alt={selectedPhoto.caption || animal.name}
              className="max-h-[85vh] rounded-lg object-contain"
            />
            {selectedPhoto.caption && (
              <p className="mt-2 text-center text-sm text-white">
                {selectedPhoto.caption}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Status workflow modal */}
      {showStatusModal && (
        <StatusWorkflowModal
          animalId={animal.id}
          animalName={animal.name}
          currentStatus={animal.status}
          onClose={() => setShowStatusModal(false)}
          onStatusChanged={handleStatusChanged}
        />
      )}
    </div>
  );
}
