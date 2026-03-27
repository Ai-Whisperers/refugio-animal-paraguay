"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiClientError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

// -- Types -------------------------------------------------------------------

interface ApplicationItem {
  id: string;
  animal_name: string;
  animal_species: string;
  submitted_at: string;
  status: string;
}

interface DonationStats {
  total_count: number;
  total_amount_cents: number;
  currency: string;
  last_donation_at: string | null;
}

interface SponsoredAnimalItem {
  animal_id: string;
  animal_name: string;
  animal_species: string;
  tier_name: string;
  frequency: string;
  status: string;
}

interface DashboardData {
  user_id: string;
  display_name: string;
  email: string;
  role: string;
  applications: ApplicationItem[];
  donation_summary: DonationStats;
  sponsored_animals: SponsoredAnimalItem[];
  total_applications: number;
  total_sponsored_animals: number;
}

// -- Status badge colors -----------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-600",
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${color}`}
    >
      {status}
    </span>
  );
}

// -- Skeleton loader ---------------------------------------------------------

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-gray-200 bg-white p-6">
      <div className="mb-4 h-4 w-1/3 rounded bg-gray-200" />
      <div className="mb-2 h-3 w-full rounded bg-gray-100" />
      <div className="mb-2 h-3 w-2/3 rounded bg-gray-100" />
      <div className="h-3 w-1/2 rounded bg-gray-100" />
    </div>
  );
}

// -- Format helpers ----------------------------------------------------------

function formatCurrency(cents: number, currency: string): string {
  const amount = cents / 100;
  try {
    return new Intl.NumberFormat("es-PY", {
      style: "currency",
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("es-PY", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

// -- Section components ------------------------------------------------------

function QuickActions() {
  return (
    <div className="flex flex-wrap gap-3">
      <a
        href="/animals"
        className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
      >
        Adoptar un Animal
      </a>
      <a
        href="/donate"
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Hacer una Donacion
      </a>
      <a
        href="/volunteer"
        className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
      >
        Voluntariado
      </a>
      <a
        href="/foster"
        className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700"
      >
        Hogar Temporal
      </a>
    </div>
  );
}

function ApplicationsSection({
  applications,
}: {
  applications: ApplicationItem[];
}) {
  if (applications.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="mb-3 text-base font-semibold text-gray-900">
          Mis Solicitudes de Adopcion
        </h3>
        <p className="text-sm text-gray-500">
          Todavia no tienes solicitudes de adopcion.{" "}
          <a href="/animals" className="text-green-600 hover:underline">
            Buscar animales disponibles
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-base font-semibold text-gray-900">
        Mis Solicitudes de Adopcion
      </h3>
      <div className="space-y-3">
        {applications.map((app) => (
          <div
            key={app.id}
            className="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-gray-900">
                {app.animal_name}
              </p>
              <p className="text-xs text-gray-500">
                {app.animal_species === "dog" ? "Perro" : app.animal_species === "cat" ? "Gato" : app.animal_species}{" "}
                &middot; {formatDate(app.submitted_at)}
              </p>
            </div>
            <StatusBadge status={app.status} />
          </div>
        ))}
      </div>
    </div>
  );
}

function DonationsSection({ stats }: { stats: DonationStats }) {
  if (stats.total_count === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="mb-3 text-base font-semibold text-gray-900">
          Mis Donaciones
        </h3>
        <p className="text-sm text-gray-500">
          Todavia no has hecho donaciones.{" "}
          <a href="/donate" className="text-blue-600 hover:underline">
            Donar ahora
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-base font-semibold text-gray-900">
        Mis Donaciones
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-bold text-green-700">
            {formatCurrency(stats.total_amount_cents, stats.currency)}
          </p>
          <p className="text-xs text-gray-500">Total donado</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">
            {stats.total_count}
          </p>
          <p className="text-xs text-gray-500">Donaciones</p>
        </div>
      </div>
      {stats.last_donation_at && (
        <p className="mt-3 text-xs text-gray-400">
          Ultima donacion: {formatDate(stats.last_donation_at)}
        </p>
      )}
    </div>
  );
}

function SponsoredAnimalsSection({
  animals,
}: {
  animals: SponsoredAnimalItem[];
}) {
  if (animals.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        <h3 className="mb-3 text-base font-semibold text-gray-900">
          Animales Apadrinados
        </h3>
        <p className="text-sm text-gray-500">
          No estas apadrinando ningun animal aun.{" "}
          <a href="/animals" className="text-green-600 hover:underline">
            Ver animales
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-base font-semibold text-gray-900">
        Animales Apadrinados
      </h3>
      <div className="space-y-3">
        {animals.map((animal) => (
          <div
            key={animal.animal_id}
            className="flex items-center justify-between rounded-lg border border-gray-100 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium text-gray-900">
                {animal.animal_name}
              </p>
              <p className="text-xs text-gray-500">
                {animal.tier_name} &middot;{" "}
                {animal.frequency === "monthly" ? "Mensual" : "Anual"}
              </p>
            </div>
            <StatusBadge status={animal.status} />
          </div>
        ))}
      </div>
    </div>
  );
}

// -- Volunteer/Foster placeholders -------------------------------------------

function VolunteerSection() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-3 text-base font-semibold text-gray-900">
        Mis Turnos de Voluntariado
      </h3>
      <p className="text-sm text-gray-500">
        La gestion de turnos estara disponible proximamente.{" "}
        <a href="/volunteer" className="text-purple-600 hover:underline">
          Mas informacion
        </a>
      </p>
    </div>
  );
}

function FosterSection() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-3 text-base font-semibold text-gray-900">
        Animales en Hogar Temporal
      </h3>
      <p className="text-sm text-gray-500">
        La gestion de hogares temporales estara disponible proximamente.{" "}
        <a href="/foster" className="text-orange-600 hover:underline">
          Mas informacion
        </a>
      </p>
    </div>
  );
}

// -- Main page ---------------------------------------------------------------

export default function PortalDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.get<DashboardData>("/portal/dashboard");
      setData(result);
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 401) {
        router.replace("/admin/login");
        return;
      }
      setError("No se pudo cargar el panel. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
      return;
    }
    fetchDashboard();
  }, [fetchDashboard, router]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-1/3 animate-pulse rounded bg-gray-200" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-700">{error ?? "Error desconocido"}</p>
        <button
          onClick={fetchDashboard}
          className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const role = data.role;

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Hola, {data.display_name}!
        </h2>
        <p className="text-sm text-gray-500">
          Bienvenido/a a tu panel personal
        </p>
      </div>

      {/* Quick actions */}
      <QuickActions />

      {/* Dashboard sections — responsive grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Show adoption section for adopter role or anyone with applications */}
        {(role === "adopter" || data.total_applications > 0) && (
          <ApplicationsSection applications={data.applications} />
        )}

        {/* Show donation section for donor role or anyone with donations */}
        {(role === "donor" || data.donation_summary.total_count > 0) && (
          <DonationsSection stats={data.donation_summary} />
        )}

        {/* Sponsored animals for anyone */}
        {(data.total_sponsored_animals > 0 || role === "donor") && (
          <SponsoredAnimalsSection animals={data.sponsored_animals} />
        )}

        {/* Volunteer section for volunteer role */}
        {role === "volunteer" && <VolunteerSection />}

        {/* Foster section for foster role */}
        {role === "foster" && <FosterSection />}
      </div>

      {/* If user has no sections to show, display a welcome message */}
      {role !== "adopter" &&
        role !== "donor" &&
        role !== "volunteer" &&
        role !== "foster" &&
        data.total_applications === 0 &&
        data.donation_summary.total_count === 0 &&
        data.total_sponsored_animals === 0 && (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">
              Tu panel esta vacio por ahora. Explora lo que puedes hacer:
            </p>
            <div className="mt-4">
              <QuickActions />
            </div>
          </div>
        )}
    </div>
  );
}
