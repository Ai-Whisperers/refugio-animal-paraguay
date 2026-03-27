"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  Heart,
  User,
  PawPrint,
  Clock,
  CheckCircle,
  XCircle,
  Ban,
  Mail,
  Phone,
  MapPin,
  Calendar,
  FileText,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { AdoptionRequestStatus, AdoptionRequestResponse } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Detalle de Solicitud";
const LABEL_LOADING = "Cargando solicitud...";
const LABEL_ERROR = "Error al cargar la solicitud";
const LABEL_NOT_FOUND = "Solicitud no encontrada";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a solicitudes";
const LABEL_ADOPTER_SECTION = "Informacion del Adoptante";
const LABEL_ANIMAL_SECTION = "Animal Solicitado";
const LABEL_REQUEST_SECTION = "Detalles de la Solicitud";
const LABEL_STATUS = "Estado";
const LABEL_SUBMITTED = "Fecha de solicitud";
const LABEL_DECIDED = "Fecha de decision";
const LABEL_NOTES = "Notas";
const LABEL_NO_NOTES = "Sin notas";
const LABEL_CONTRACT = "Contrato";
const LABEL_CONTRACT_GENERATED = "Contrato generado";
const LABEL_NO_CONTRACT = "Sin contrato";
const LABEL_ADOPTER_DELETED = "Adoptante eliminado (datos eliminados por GDPR)";
const LABEL_ANIMAL_DELETED = "Animal eliminado del sistema";

// --- Status config ---
const STATUS_LABELS: Record<AdoptionRequestStatus, string> = {
  pending: "Pendiente",
  approved: "Aprobada",
  rejected: "Rechazada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<AdoptionRequestStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  cancelled: "bg-gray-100 text-gray-800 border-gray-200",
};

const STATUS_ICONS: Record<AdoptionRequestStatus, typeof Clock> = {
  pending: Clock,
  approved: CheckCircle,
  rejected: XCircle,
  cancelled: Ban,
};

// --- Types ---
interface AdopterDetail {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  gdpr_consent_at: string | null;
  created_at: string;
}

interface AnimalDetail {
  id: string;
  name: string;
  species: string;
  breed: string | null;
  size: string | null;
  gender: string | null;
  birth_date: string | null;
  description: string | null;
  primary_photo_url: string | null;
  status: string;
}

export default function AdoptionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const requestId = params.id as string;

  const [isChecking, setIsChecking] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [request, setRequest] = useState<AdoptionRequestResponse | null>(null);
  const [adopter, setAdopter] = useState<AdopterDetail | null>(null);
  const [animal, setAnimal] = useState<AnimalDetail | null>(null);
  const [adopterError, setAdopterError] = useState(false);
  const [animalError, setAnimalError] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchData = useCallback(async () => {
    if (!requestId) return;

    setIsLoading(true);
    setError(null);
    setAdopterError(false);
    setAnimalError(false);

    try {
      const reqData = await api.get<AdoptionRequestResponse>(`/adoption-requests/${requestId}`);
      setRequest(reqData);

      // Fetch adopter
      try {
        const adopterData = await api.get<AdopterDetail>(`/adopters/${reqData.adopter_id}`);
        setAdopter(adopterData);
      } catch {
        setAdopterError(true);
      }

      // Fetch animal
      try {
        const animalData = await api.get<AnimalDetail>(`/animals/${reqData.animal_id}`);
        setAnimal(animalData);
      } catch {
        setAnimalError(true);
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 404) {
        setError(LABEL_NOT_FOUND);
      } else if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [requestId]);

  useEffect(() => {
    if (!isChecking) {
      fetchData();
    }
  }, [isChecking, fetchData]);

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatShortDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  const SPECIES_LABELS: Record<string, string> = {
    dog: "Perro",
    cat: "Gato",
    other: "Otro",
  };

  const GENDER_LABELS: Record<string, string> = {
    male: "Macho",
    female: "Hembra",
    unknown: "Desconocido",
  };

  const SIZE_LABELS: Record<string, string> = {
    small: "Pequeno",
    medium: "Mediano",
    large: "Grande",
    extra_large: "Extra grande",
  };

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
              onClick={() => router.push("/admin/adoptions")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <Heart className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary disabled:opacity-50"
            aria-label={LABEL_RETRY}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-warm-text-secondary">
              <RefreshCw className="h-5 w-5 animate-spin" />
              <span>{LABEL_LOADING}</span>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={fetchData}
              className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Main content */}
        {!isLoading && !error && request && (
          <div className="space-y-6">
            {/* Status banner */}
            {(() => {
              const StatusIcon = STATUS_ICONS[request.status];
              return (
                <div className={`flex items-center gap-3 rounded-lg border p-4 ${STATUS_COLORS[request.status]}`}>
                  <StatusIcon className="h-6 w-6" />
                  <div>
                    <p className="font-semibold text-lg">
                      {STATUS_LABELS[request.status]}
                    </p>
                    <p className="text-sm opacity-80">
                      {LABEL_SUBMITTED}: {formatDate(request.submitted_at)}
                      {request.decided_at && (
                        <> &middot; {LABEL_DECIDED}: {formatDate(request.decided_at)}</>
                      )}
                    </p>
                  </div>
                </div>
              );
            })()}

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Adopter section */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
                <div className="flex items-center gap-2 mb-4">
                  <User className="h-5 w-5 text-primary-600" />
                  <h2 className="text-lg font-semibold text-warm-text-primary">
                    {LABEL_ADOPTER_SECTION}
                  </h2>
                </div>

                {adopterError ? (
                  <p className="text-sm text-warm-text-secondary italic">
                    {LABEL_ADOPTER_DELETED}
                  </p>
                ) : adopter ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-warm-text-secondary" />
                      <span className="text-sm font-medium text-warm-text-primary">
                        {adopter.full_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-warm-text-secondary" />
                      <a
                        href={`mailto:${adopter.email}`}
                        className="text-sm text-primary-600 hover:text-primary-800"
                      >
                        {adopter.email}
                      </a>
                    </div>
                    {adopter.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-warm-text-secondary" />
                        <a
                          href={`tel:${adopter.phone}`}
                          className="text-sm text-primary-600 hover:text-primary-800"
                        >
                          {adopter.phone}
                        </a>
                      </div>
                    )}
                    {adopter.address && (
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-warm-text-secondary mt-0.5" />
                        <span className="text-sm text-warm-text-primary">
                          {adopter.address}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-warm-text-secondary" />
                      <span className="text-sm text-warm-text-secondary">
                        Registrado: {formatShortDate(adopter.created_at)}
                      </span>
                    </div>
                    {adopter.gdpr_consent_at && (
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm text-warm-text-secondary">
                          Consentimiento GDPR: {formatShortDate(adopter.gdpr_consent_at)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>

              {/* Animal section */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
                <div className="flex items-center gap-2 mb-4">
                  <PawPrint className="h-5 w-5 text-primary-600" />
                  <h2 className="text-lg font-semibold text-warm-text-primary">
                    {LABEL_ANIMAL_SECTION}
                  </h2>
                </div>

                {animalError ? (
                  <p className="text-sm text-warm-text-secondary italic">
                    {LABEL_ANIMAL_DELETED}
                  </p>
                ) : animal ? (
                  <div className="space-y-3">
                    {animal.primary_photo_url && (
                      <img
                        src={animal.primary_photo_url}
                        alt={animal.name}
                        className="h-32 w-32 rounded-lg object-cover"
                      />
                    )}
                    <div>
                      <p className="text-lg font-semibold text-warm-text-primary">
                        {animal.name}
                      </p>
                      <p className="text-sm text-warm-text-secondary capitalize">
                        {SPECIES_LABELS[animal.species] ?? animal.species}
                        {animal.breed ? ` - ${animal.breed}` : ""}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {animal.gender && (
                        <div>
                          <span className="text-warm-text-secondary">Sexo: </span>
                          <span className="text-warm-text-primary">
                            {GENDER_LABELS[animal.gender] ?? animal.gender}
                          </span>
                        </div>
                      )}
                      {animal.size && (
                        <div>
                          <span className="text-warm-text-secondary">Tamano: </span>
                          <span className="text-warm-text-primary">
                            {SIZE_LABELS[animal.size] ?? animal.size}
                          </span>
                        </div>
                      )}
                      {animal.birth_date && (
                        <div>
                          <span className="text-warm-text-secondary">Nacimiento: </span>
                          <span className="text-warm-text-primary">
                            {formatShortDate(animal.birth_date)}
                          </span>
                        </div>
                      )}
                    </div>
                    {animal.description && (
                      <p className="text-sm text-warm-text-secondary mt-2">
                        {animal.description}
                      </p>
                    )}
                  </div>
                ) : null}
              </div>
            </div>

            {/* Request details section */}
            <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-warm-text-primary">
                  {LABEL_REQUEST_SECTION}
                </h2>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-warm-text-secondary mb-1">
                    {LABEL_NOTES}
                  </h3>
                  <p className="text-sm text-warm-text-primary">
                    {request.notes ?? LABEL_NO_NOTES}
                  </p>
                </div>

                {request.contract_pdf_path && (
                  <div>
                    <h3 className="text-sm font-medium text-warm-text-secondary mb-1">
                      {LABEL_CONTRACT}
                    </h3>
                    <p className="text-sm text-warm-text-primary">
                      {LABEL_CONTRACT_GENERATED}
                      {request.contract_generated_at && (
                        <> ({formatDate(request.contract_generated_at)})</>
                      )}
                    </p>
                  </div>
                )}

                <div className="border-t border-warm-border pt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-warm-text-secondary">ID: </span>
                    <span className="text-warm-text-primary font-mono text-xs">
                      {request.id}
                    </span>
                  </div>
                  <div>
                    <span className="text-warm-text-secondary">Creado: </span>
                    <span className="text-warm-text-primary">
                      {formatDate(request.created_at)}
                    </span>
                  </div>
                  <div>
                    <span className="text-warm-text-secondary">Actualizado: </span>
                    <span className="text-warm-text-primary">
                      {formatDate(request.updated_at)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
