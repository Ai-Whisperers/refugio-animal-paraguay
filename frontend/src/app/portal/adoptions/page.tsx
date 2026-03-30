"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiClientError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

// -- Types -------------------------------------------------------------------

interface ApplicationDetail {
  id: string;
  animal_id: string;
  animal_name: string;
  animal_species: string;
  submitted_at: string;
  decided_at: string | null;
  status: string;
  notes: string | null;
}

interface AdopterApplicationsResponse {
  applications: ApplicationDetail[];
  total: number;
}

// -- Constants ---------------------------------------------------------------

const STATUS_LABELS: Record<string, string> = {
  pending: "En Revision",
  approved: "Aprobada",
  rejected: "Rechazada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  cancelled: "bg-gray-100 text-gray-600 border-gray-200",
};

const SPECIES_LABELS: Record<string, string> = {
  dog: "Perro",
  cat: "Gato",
  bird: "Ave",
  rabbit: "Conejo",
  other: "Otro",
};

const STATUS_NEXT_STEPS: Record<string, string> = {
  pending:
    "Tu solicitud esta siendo revisada por nuestro equipo. Te contactaremos pronto.",
  approved:
    "Felicitaciones! Tu solicitud fue aprobada. Contacta al refugio para coordinar la entrega.",
  rejected:
    "Tu solicitud no fue aprobada en esta oportunidad. Puedes explorar otros animales disponibles.",
  cancelled: "Esta solicitud fue cancelada.",
};

// -- Helpers -----------------------------------------------------------------

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("es-PY", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// -- Components --------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const color =
    STATUS_COLORS[status] ?? "bg-gray-100 text-gray-600 border-gray-200";
  const label = STATUS_LABELS[status] ?? status;
  return (
    <span
      className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold ${color}`}
    >
      {label}
    </span>
  );
}

function ProgressDots({ status }: { status: string }) {
  const steps = ["pending", "approved"];
  const isCancelled = status === "cancelled";
  const isRejected = status === "rejected";

  if (isCancelled || isRejected) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-gray-300" />
        <div className="h-px w-8 bg-gray-200" />
        <div
          className={`h-2 w-2 rounded-full ${isRejected ? "bg-red-400" : "bg-gray-300"}`}
        />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {steps.map((step, i) => {
        const isActive = step === status;
        const isPast =
          status === "approved" && step === "pending";
        return (
          <div key={step} className="flex items-center gap-2">
            {i > 0 && (
              <div
                className={`h-px w-8 ${isPast ? "bg-green-400" : "bg-gray-200"}`}
              />
            )}
            <div
              className={`h-3 w-3 rounded-full border-2 ${
                isActive
                  ? "border-green-600 bg-green-600"
                  : isPast
                    ? "border-green-400 bg-green-400"
                    : "border-gray-300 bg-white"
              }`}
            />
          </div>
        );
      })}
    </div>
  );
}

function ApplicationCard({ app }: { app: ApplicationDetail }) {
  const speciesLabel =
    SPECIES_LABELS[app.animal_species] ?? app.animal_species;
  const nextStep = STATUS_NEXT_STEPS[app.status];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900">
            {app.animal_name}
          </h3>
          <p className="text-sm text-gray-500">{speciesLabel}</p>
        </div>
        <StatusBadge status={app.status} />
      </div>

      {/* Progress indicator */}
      <div className="mb-4">
        <ProgressDots status={app.status} />
      </div>

      {/* Dates */}
      <div className="mb-3 grid grid-cols-2 gap-3 text-xs text-gray-500">
        <div>
          <span className="font-medium text-gray-700">Enviada:</span>{" "}
          {formatDate(app.submitted_at)}
        </div>
        {app.decided_at && (
          <div>
            <span className="font-medium text-gray-700">Decidida:</span>{" "}
            {formatDate(app.decided_at)}
          </div>
        )}
      </div>

      {/* Next steps */}
      {nextStep && (
        <p className="text-xs text-gray-500 italic">{nextStep}</p>
      )}

      {/* Staff notes (only when decision was made) */}
      {app.notes && app.status !== "pending" && (
        <div className="mt-3 rounded-lg bg-gray-50 px-3 py-2">
          <p className="text-xs font-medium text-gray-600">
            Comentario del equipo:
          </p>
          <p className="mt-1 text-xs text-gray-700">{app.notes}</p>
        </div>
      )}

      {/* View animal link */}
      <div className="mt-4 flex justify-end">
        <a
          href={`/animals/${app.animal_id}`}
          className="text-xs font-medium text-green-600 hover:underline"
        >
          Ver perfil del animal
        </a>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-4 flex items-start justify-between">
        <div className="space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-3 w-20 rounded bg-gray-100" />
        </div>
        <div className="h-6 w-20 rounded-full bg-gray-200" />
      </div>
      <div className="mb-3 flex gap-2">
        <div className="h-3 w-3 rounded-full bg-gray-200" />
        <div className="h-px w-8 self-center bg-gray-200" />
        <div className="h-3 w-3 rounded-full bg-gray-200" />
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-gray-100" />
        <div className="h-3 w-3/4 rounded bg-gray-100" />
      </div>
    </div>
  );
}

// -- Main page ---------------------------------------------------------------

export default function PortalAdoptionsPage() {
  const router = useRouter();
  const [data, setData] = useState<AdopterApplicationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAdoptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result =
        await api.get<AdopterApplicationsResponse>("/portal/adoptions");
      setData(result);
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 401) {
        router.replace("/admin/login");
        return;
      }
      setError("No se pudieron cargar tus solicitudes. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
      return;
    }
    fetchAdoptions();
  }, [fetchAdoptions, router]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-2/5 animate-pulse rounded bg-gray-200" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-700">{error}</p>
        <button
          onClick={fetchAdoptions}
          className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const applications = data?.applications ?? [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Mis Solicitudes de Adopcion
          </h2>
          <p className="text-sm text-gray-500">
            {applications.length === 0
              ? "Todavia no tienes solicitudes"
              : `${applications.length} solicitud${applications.length !== 1 ? "es" : ""} registrada${applications.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <a
          href="/animals"
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
        >
          Buscar animales
        </a>
      </div>

      {/* Status legend */}
      {applications.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(STATUS_LABELS).map(([key, label]) => (
            <span
              key={key}
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs ${STATUS_COLORS[key]}`}
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* Application grid */}
      {applications.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-10 text-center">
          <p className="text-gray-500">
            No tienes solicitudes de adopcion todavia.
          </p>
          <a
            href="/animals"
            className="mt-4 inline-block rounded-lg bg-green-600 px-5 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            Explorar animales disponibles
          </a>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {applications.map((app) => (
            <ApplicationCard key={app.id} app={app} />
          ))}
        </div>
      )}

      {/* Back link */}
      <div>
        <a
          href="/portal/dashboard"
          className="text-sm text-gray-500 hover:text-gray-700 hover:underline"
        >
          Volver al panel principal
        </a>
      </div>
    </div>
  );
}
