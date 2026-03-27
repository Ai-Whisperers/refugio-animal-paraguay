"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  HandHeart,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  PawPrint,
  DollarSign,
  TrendingUp,
  Users,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Panel de Padrinos";
const LABEL_LOADING = "Cargando padrinos...";
const LABEL_ERROR = "Error al cargar padrinos";
const LABEL_EMPTY = "No hay padrinazgos registrados";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ALL = "Todos";
const LABEL_SHOWING = "Mostrando";
const LABEL_ACTIVE_SPONSORS = "Padrinos activos";
const LABEL_MONTHLY_REVENUE = "Ingreso mensual";
const LABEL_TOTAL_CONTRIBUTED = "Total contribuido";
const LABEL_ANIMALS_SPONSORED = "Animales apadrinados";

const PAGE_SIZE = 20;

const STATUS_OPTIONS: Record<string, string> = {
  active: "Activo",
  paused: "Pausado",
  cancelled: "Cancelado",
  expired: "Expirado",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  cancelled: "bg-red-100 text-red-700",
  expired: "bg-gray-100 text-gray-600",
};

const TIER_COLORS: Record<string, string> = {
  bronze: "bg-orange-100 text-orange-700",
  silver: "bg-gray-200 text-gray-700",
  gold: "bg-yellow-100 text-yellow-700",
};

const TIER_LABELS: Record<string, string> = {
  bronze: "Bronce",
  silver: "Plata",
  gold: "Oro",
};

const FREQUENCY_LABELS: Record<string, string> = {
  monthly: "Mensual",
  annual: "Anual",
};

interface SponsorshipTier {
  id: string;
  level: string;
  name: string;
  amount_cents: number;
  currency: string;
}

interface SponsorshipItem {
  id: string;
  donor_id: string;
  animal_id: string;
  tier_id: string;
  frequency: string;
  status: string;
  stripe_subscription_id: string | null;
  total_contributed_cents: number;
  started_at: string;
  ended_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  tier: SponsorshipTier | null;
}

interface SponsorshipListResponse {
  items: SponsorshipItem[];
  total: number;
  page: number;
  page_size: number;
}

function formatCurrency(cents: number, currency: string = "EUR"): string {
  const amount = cents / 100;
  return new Intl.NumberFormat("es-PY", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: currency === "PYG" ? 0 : 0,
    maximumFractionDigits: currency === "PYG" ? 0 : 0,
  }).format(amount);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function AdminSponsorsPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [sponsorships, setSponsorships] = useState<SponsorshipItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter]);

  const fetchSponsorships = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      params.set("page", String(currentPage));
      params.set("page_size", String(PAGE_SIZE));

      const data = await api.get<SponsorshipListResponse>(
        `/sponsorships?${params.toString()}`
      );
      setSponsorships(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, currentPage]);

  useEffect(() => {
    if (!isChecking) {
      fetchSponsorships();
    }
  }, [isChecking, fetchSponsorships]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Compute summary stats from current data
  const activeCount = sponsorships.filter((s) => s.status === "active").length;
  const totalContributed = sponsorships.reduce(
    (sum, s) => sum + s.total_contributed_cents,
    0
  );
  const uniqueAnimals = new Set(sponsorships.map((s) => s.animal_id)).size;
  const monthlyRevenue = sponsorships
    .filter((s) => s.status === "active" && s.tier)
    .reduce((sum, s) => sum + (s.tier?.amount_cents ?? 0), 0);

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
              onClick={() => router.push("/admin/dashboard")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <HandHeart className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <button
            onClick={fetchSponsorships}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_RETRY}
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <SummaryCard
            icon={<Users className="h-5 w-5 text-green-600" />}
            label={LABEL_ACTIVE_SPONSORS}
            value={String(activeCount)}
            bgColor="bg-green-50"
          />
          <SummaryCard
            icon={<DollarSign className="h-5 w-5 text-blue-600" />}
            label={LABEL_MONTHLY_REVENUE}
            value={formatCurrency(monthlyRevenue)}
            bgColor="bg-blue-50"
          />
          <SummaryCard
            icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
            label={LABEL_TOTAL_CONTRIBUTED}
            value={formatCurrency(totalContributed)}
            bgColor="bg-purple-50"
          />
          <SummaryCard
            icon={<PawPrint className="h-5 w-5 text-orange-600" />}
            label={LABEL_ANIMALS_SPONSORED}
            value={String(uniqueAnimals)}
            bgColor="bg-orange-50"
          />
        </div>

        {/* Filters */}
        <div className="mb-6 flex items-center gap-4">
          <label
            htmlFor="status-filter"
            className="text-sm font-medium text-warm-text-secondary"
          >
            Estado:
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option value="">{LABEL_ALL}</option>
            {Object.entries(STATUS_OPTIONS).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
          <span className="text-sm text-warm-text-tertiary">
            {total} padrinazgos
          </span>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={fetchSponsorships}
              className="mt-2 text-sm font-medium text-red-700 underline hover:text-red-900"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
            <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && sponsorships.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
            <HandHeart className="mx-auto h-12 w-12 text-primary-300" aria-hidden="true" />
            <p className="mt-4 text-warm-text-secondary">{LABEL_EMPTY}</p>
          </div>
        )}

        {/* Table */}
        {!isLoading && !error && sponsorships.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-lg border border-warm-border">
              <table className="min-w-full divide-y divide-warm-border">
                <thead className="bg-warm-bg">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Nivel
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Estado
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Frecuencia
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Monto
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Contribuido
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Inicio
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Animal
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-warm-text-tertiary uppercase">
                      Notas
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border bg-warm-surface">
                  {sponsorships.map((s) => (
                    <tr key={s.id} className="hover:bg-warm-bg transition-colors">
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            TIER_COLORS[s.tier?.level ?? ""] ?? "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {TIER_LABELS[s.tier?.level ?? ""] ?? s.tier?.name ?? "-"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            STATUS_COLORS[s.status] ?? "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {STATUS_OPTIONS[s.status] ?? s.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-warm-text-secondary">
                        {FREQUENCY_LABELS[s.frequency] ?? s.frequency}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-warm-text-primary">
                        {s.tier
                          ? formatCurrency(s.tier.amount_cents, s.tier.currency)
                          : "-"}
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-warm-text-primary">
                        {formatCurrency(s.total_contributed_cents)}
                      </td>
                      <td className="px-4 py-3 text-sm text-warm-text-secondary">
                        {formatDate(s.started_at)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => router.push(`/admin/animals/${s.animal_id}`)}
                          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                        >
                          Ver animal
                        </button>
                      </td>
                      <td className="px-4 py-3 text-sm text-warm-text-tertiary max-w-[200px] truncate">
                        {s.notes ?? "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-warm-text-secondary">
                {LABEL_SHOWING}{" "}
                {(currentPage - 1) * PAGE_SIZE + 1}-
                {Math.min(currentPage * PAGE_SIZE, total)} de {total}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                  {LABEL_PREVIOUS}
                </button>
                <span className="px-2 text-sm text-warm-text-secondary">
                  Pagina {currentPage} de {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages}
                  className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {LABEL_NEXT}
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/** Summary stat card for the dashboard header. */
function SummaryCard({
  icon,
  label,
  value,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  bgColor: string;
}) {
  return (
    <div className={`${bgColor} rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
