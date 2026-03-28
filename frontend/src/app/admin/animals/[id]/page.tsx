"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  PawPrint,
  ArrowLeft,
  Pencil,
  RefreshCw,
  ArrowRightLeft,
  Calendar,
  Info,
  Stethoscope,
  Settings2,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import { STATUS_LABELS, STATUS_COLORS, VALID_TRANSITIONS } from "@/lib/animal-status";
import StatusWorkflowModal from "@/components/admin/StatusWorkflowModal";
import AnimalHistoryTimeline from "@/components/admin/AnimalHistoryTimeline";
import MedicalTimeline from "@/components/admin/MedicalTimeline";
import VetVisitForm from "@/components/admin/VetVisitForm";
import type { Animal, AnimalStatus } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_LOADING = "Cargando animal...";
const LABEL_ERROR = "Error al cargar el animal";
const LABEL_NOT_FOUND = "Animal no encontrado";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a la lista";
const LABEL_EDIT = "Editar";
const LABEL_VET_NOTES = "Notas Veterinarias";
const LABEL_REQUIREMENTS = "Requisitos";
const LABEL_CHANGE_STATUS = "Cambiar Estado";
const LABEL_TAB_INFO = "Informacion";
const LABEL_TAB_MEDICAL = "Historial Medico";
const LABEL_TAB_HISTORY = "Historial";
const LABEL_SPECIES = "Especie";
const LABEL_BREED = "Raza";
const LABEL_SIZE = "Tamano";
const LABEL_GENDER = "Genero";
const LABEL_BIRTH_DATE = "Fecha de nacimiento";
const LABEL_INTAKE_DATE = "Fecha de ingreso";
const LABEL_UPDATED = "Ultima actualizacion";
const LABEL_DESCRIPTION = "Descripcion";
const LABEL_NO_DESCRIPTION = "Sin descripcion";
const LABEL_PHOTOS = "Fotos";
const LABEL_NO_PHOTOS = "Sin fotos";
const LABEL_NO_TRANSITIONS = "Estado final";

const SPECIES_LABELS: Record<string, string> = {
  dog: "Perro",
  cat: "Gato",
  other: "Otro",
};

const SIZE_LABELS: Record<string, string> = {
  small: "Pequeno",
  medium: "Mediano",
  large: "Grande",
};

const GENDER_LABELS: Record<string, string> = {
  male: "Macho",
  female: "Hembra",
  unknown: "Desconocido",
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
  const [showVetVisitForm, setShowVetVisitForm] = useState(false);
  const [activeTab, setActiveTab] = useState<"info" | "medical" | "history">("info");
  const [medicalRefreshKey, setMedicalRefreshKey] = useState(0);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchAnimal = useCallback(async () => {
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
    if (!isChecking) {
      fetchAnimal();
    }
  }, [isChecking, fetchAnimal]);

  function handleStatusChanged(newStatus: AnimalStatus) {
    setAnimal((prev) => (prev ? { ...prev, status: newStatus } : prev));
    setShowStatusModal(false);
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-800">{error}</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <button
              onClick={fetchAnimal}
              className="text-sm font-medium text-red-700 underline hover:text-red-900"
            >
              {LABEL_RETRY}
            </button>
            <button
              onClick={() => router.push("/admin/animals")}
              className="text-sm font-medium text-warm-text-secondary underline hover:text-warm-text-primary"
            >
              {LABEL_BACK}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!animal) return null;

  const validTransitions = VALID_TRANSITIONS[animal.status] ?? [];
  const hasTransitions = validTransitions.length > 0;

  return (
    <div className="mx-auto max-w-4xl">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/animals")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          {animal.primary_photo_url ? (
            <img
              src={animal.primary_photo_url}
              alt={animal.name}
              className="h-12 w-12 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
              <PawPrint className="h-6 w-6 text-primary-500" />
            </div>
          )}
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {animal.name}
            </h1>
            <span
              className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[animal.status]}`}
            >
              {STATUS_LABELS[animal.status]}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowStatusModal(true)}
            disabled={!hasTransitions}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary disabled:cursor-not-allowed disabled:opacity-50"
            title={hasTransitions ? LABEL_CHANGE_STATUS : LABEL_NO_TRANSITIONS}
          >
            <ArrowRightLeft className="h-4 w-4" />
            {LABEL_CHANGE_STATUS}
          </button>
          <button
            onClick={() => router.push(`/admin/animals/${animalId}/vet-notes`)}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border bg-white px-3 py-1.5 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
          >
            <Stethoscope className="h-4 w-4" />
            {LABEL_VET_NOTES}
          </button>
          <button
            onClick={() => router.push(`/admin/animals/${animalId}/requirements`)}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border bg-white px-3 py-1.5 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
          >
            <Settings2 className="h-4 w-4" />
            {LABEL_REQUIREMENTS}
          </button>
          <button
            onClick={() => router.push(`/admin/animals/${animalId}/edit`)}
            className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          >
            <Pencil className="h-4 w-4" />
            {LABEL_EDIT}
          </button>
        </div>
      </div>

      {/* Tabbed section: Info / Medical / History */}
      <div className="mt-6">
        {/* Tab navigation */}
        <div className="mb-4 flex gap-1 border-b border-warm-border">
          {(
            [
              { key: "info", label: LABEL_TAB_INFO },
              { key: "medical", label: LABEL_TAB_MEDICAL },
              { key: "history", label: LABEL_TAB_HISTORY },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-b-2 border-primary-500 text-primary-600"
                  : "text-warm-text-secondary hover:text-warm-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "info" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
                <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_SPECIES}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {SPECIES_LABELS[animal.species] ?? animal.species}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_BREED}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {animal.breed ?? "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_SIZE}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {animal.size ? (SIZE_LABELS[animal.size] ?? animal.size) : "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_GENDER}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {animal.gender
                        ? (GENDER_LABELS[animal.gender] ?? animal.gender)
                        : "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_BIRTH_DATE}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {animal.birth_date ? formatDate(animal.birth_date) : "-"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                      {LABEL_INTAKE_DATE}
                    </dt>
                    <dd className="mt-1 text-sm text-warm-text-primary">
                      {formatDate(animal.created_at)}
                    </dd>
                  </div>
                </dl>
                <div className="mt-6 border-t border-warm-border pt-4">
                  <dt className="text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                    {LABEL_DESCRIPTION}
                  </dt>
                  <dd className="mt-2 text-sm leading-relaxed text-warm-text-secondary">
                    {animal.description ?? LABEL_NO_DESCRIPTION}
                  </dd>
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
                <h2 className="mb-3 text-base font-semibold text-warm-text-primary">
                  {LABEL_PHOTOS}
                </h2>
                {animal.photos && animal.photos.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2">
                    {animal.photos.map((photo) => (
                      <img
                        key={photo.id}
                        src={photo.url}
                        alt={photo.caption ?? animal.name}
                        className="aspect-square rounded-lg object-cover"
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center rounded-lg bg-warm-bg py-6">
                    <PawPrint className="h-8 w-8 text-primary-200" />
                    <p className="mt-2 text-xs text-warm-text-tertiary">
                      {LABEL_NO_PHOTOS}
                    </p>
                  </div>
                )}
              </div>
              <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs text-warm-text-tertiary">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{LABEL_INTAKE_DATE}:</span>
                    <span className="text-warm-text-secondary">
                      {formatDate(animal.created_at)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-warm-text-tertiary">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{LABEL_UPDATED}:</span>
                    <span className="text-warm-text-secondary">
                      {formatDate(animal.updated_at)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "medical" && (
          <MedicalTimeline
            key={medicalRefreshKey}
            animalId={animal.id}
            onAddVisit={() => setShowVetVisitForm(true)}
          />
        )}

        {activeTab === "history" && (
          <AnimalHistoryTimeline animalId={animal.id} />
        )}
      </div>

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

      {/* Vet visit form modal */}
      {showVetVisitForm && (
        <VetVisitForm
          animalId={animal.id}
          animalName={animal.name}
          onClose={() => setShowVetVisitForm(false)}
          onSaved={() => {
            setShowVetVisitForm(false);
            setMedicalRefreshKey((k) => k + 1);
          }}
        />
      )}
    </div>
  );
}
