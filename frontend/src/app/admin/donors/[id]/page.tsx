"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  User,
  ArrowLeft,
  RefreshCw,
  Mail,
  Globe,
  Shield,
  DollarSign,
  Calendar,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Perfil de Donante";
const LABEL_LOADING = "Cargando perfil...";
const LABEL_ERROR = "Error al cargar perfil";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a donantes";
const LABEL_DONOR_SINCE = "Donante desde";
const LABEL_COUNTRY = "Pais";
const LABEL_CURRENCY_PREF = "Moneda preferida";
const LABEL_GDPR_STATUS = "Estado GDPR";
const LABEL_GDPR_YES = "Consentimiento otorgado";
const LABEL_GDPR_NO = "Sin consentimiento";
const LABEL_LIFETIME_STATS = "Estadisticas de por vida";
const LABEL_TOTAL_DONATED = "Total donado";
const LABEL_TOTAL_DONATIONS = "Total donaciones";
const LABEL_AVG_DONATION = "Donacion promedio";
const LABEL_LAST_DONATION = "Ultima donacion";
const LABEL_DONATION_HISTORY = "Historial de donaciones";
const LABEL_NO_DONATIONS = "Este donante aun no ha realizado donaciones";
const LABEL_DATE = "Fecha";
const LABEL_AMOUNT = "Monto";
const LABEL_METHOD = "Metodo";
const LABEL_STATUS = "Estado";
const LABEL_CATEGORY = "Categoria";
const LABEL_SHOWING = "Mostrando";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_DONOR_NOT_FOUND = "Donante no encontrado";

const PAGE_SIZE = 10;

const COUNTRY_OPTIONS: Record<string, string> = {
  NL: "Paises Bajos",
  DE: "Alemania",
  ES: "Espana",
  FR: "Francia",
  PY: "Paraguay",
  US: "Estados Unidos",
  GB: "Reino Unido",
  IT: "Italia",
  BE: "Belgica",
  AT: "Austria",
};

const STATUS_OPTIONS: Record<string, string> = {
  pending: "Pendiente",
  completed: "Completada",
  failed: "Fallida",
  refunded: "Reembolsada",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  refunded: "bg-blue-100 text-blue-700",
};

const METHOD_OPTIONS: Record<string, string> = {
  stripe: "Stripe",
  cash: "Efectivo",
  transfer: "Transferencia",
  sepa_debit: "SEPA",
  tigo_money: "Tigo Money",
};

const CATEGORY_LABELS: Record<string, string> = {
  medical: "Medico",
  food: "Alimentacion",
  operations: "Operaciones",
  infrastructure: "Infraestructura",
  emergency: "Emergencia",
};

// --- Types ---
interface DonorDetail {
  id: string;
  full_name: string;
  email: string;
  country: string | null;
  currency_preference: string;
  gdpr_consent_at: string | null;
  created_at: string;
  updated_at: string;
}

interface DonationItem {
  id: string;
  donor_id: string | null;
  amount_cents: number;
  currency: string;
  payment_method: string;
  status: string;
  fund_category: string | null;
  is_recurring: boolean;
  recurring_interval: string | null;
  receipt_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface CurrencyTotal {
  currency: string;
  totalCents: number;
  count: number;
}

function formatCurrency(cents: number, currency: string = "EUR"): string {
  const amount = cents / 100;
  const currencyMap: Record<string, string> = {
    EUR: "es-ES",
    USD: "en-US",
    PYG: "es-PY",
  };
  const locale = currencyMap[currency] ?? "es-PY";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
    minimumFractionDigits: currency === "PYG" ? 0 : 2,
  }).format(amount);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatShortDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DonorProfilePage() {
  const router = useRouter();
  const params = useParams();
  const donorId = params.id as string;

  // --- Auth check ---
  const [isChecking, setIsChecking] = useState(true);

  // --- Donor data ---
  const [donor, setDonor] = useState<DonorDetail | null>(null);
  const [isLoadingDonor, setIsLoadingDonor] = useState(true);
  const [donorError, setDonorError] = useState<string | null>(null);

  // --- Donations data ---
  const [donations, setDonations] = useState<DonationItem[]>([]);
  const [isLoadingDonations, setIsLoadingDonations] = useState(true);
  const [donationsError, setDonationsError] = useState<string | null>(null);

  // --- All donations for stats (unpaginated) ---
  const [allDonations, setAllDonations] = useState<DonationItem[]>([]);

  // --- Pagination ---
  const [currentPage, setCurrentPage] = useState(1);

  // --- Auth check ---
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  // --- Fetch donor profile ---
  const fetchDonor = useCallback(async () => {
    setIsLoadingDonor(true);
    setDonorError(null);
    try {
      const data = await api.get<DonorDetail>(`/donors/${donorId}`);
      setDonor(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.statusCode === 404) {
          setDonorError(LABEL_DONOR_NOT_FOUND);
        } else {
          setDonorError(`${LABEL_ERROR}: ${err.detail}`);
        }
      } else {
        setDonorError(LABEL_ERROR);
      }
    } finally {
      setIsLoadingDonor(false);
    }
  }, [donorId]);

  // --- Fetch all donations for stats ---
  const fetchAllDonations = useCallback(async () => {
    try {
      const data = await api.get<DonationItem[]>(
        `/donations?donor_id=${donorId}&limit=100&offset=0`
      );
      setAllDonations(data);
    } catch {
      // Stats will show as empty if this fails
    }
  }, [donorId]);

  // --- Fetch paginated donations ---
  const fetchDonations = useCallback(async () => {
    setIsLoadingDonations(true);
    setDonationsError(null);
    try {
      const offset = (currentPage - 1) * PAGE_SIZE;
      const data = await api.get<DonationItem[]>(
        `/donations?donor_id=${donorId}&limit=${PAGE_SIZE}&offset=${offset}`
      );
      setDonations(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setDonationsError(`Error: ${err.detail}`);
      } else {
        setDonationsError("Error al cargar donaciones");
      }
    } finally {
      setIsLoadingDonations(false);
    }
  }, [donorId, currentPage]);

  useEffect(() => {
    if (!isChecking) {
      fetchDonor();
      fetchAllDonations();
    }
  }, [isChecking, fetchDonor, fetchAllDonations]);

  useEffect(() => {
    if (!isChecking) {
      fetchDonations();
    }
  }, [isChecking, fetchDonations]);

  // --- Compute lifetime stats ---
  const lifetimeStats = useMemo(() => {
    const completedDonations = allDonations.filter(
      (d) => d.status === "completed"
    );

    const byCurrency: Record<string, CurrencyTotal> = {};
    for (const d of completedDonations) {
      if (!byCurrency[d.currency]) {
        byCurrency[d.currency] = {
          currency: d.currency,
          totalCents: 0,
          count: 0,
        };
      }
      byCurrency[d.currency].totalCents += d.amount_cents;
      byCurrency[d.currency].count += 1;
    }

    const totalDonations = completedDonations.length;
    const lastDonation =
      completedDonations.length > 0
        ? completedDonations.sort(
            (a, b) =>
              new Date(b.created_at).getTime() -
              new Date(a.created_at).getTime()
          )[0]
        : null;

    return {
      byCurrency: Object.values(byCurrency),
      totalDonations,
      lastDonation,
    };
  }, [allDonations]);

  const hasMore = donations.length === PAGE_SIZE;

  // --- Loading state ---
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
              onClick={() => router.push("/admin/donors")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <User className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <button
            onClick={() => {
              fetchDonor();
              fetchAllDonations();
              fetchDonations();
            }}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_RETRY}
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Donor error state */}
        {donorError && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{donorError}</p>
            <button
              onClick={fetchDonor}
              className="mt-2 text-sm font-medium text-red-700 underline hover:text-red-900"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Loading donor */}
        {isLoadingDonor && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
            <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        )}

        {/* Donor profile */}
        {!isLoadingDonor && !donorError && donor && (
          <>
            {/* Donor info card */}
            <div className="mb-6 rounded-lg border border-warm-border bg-warm-surface p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-xl font-bold text-warm-text-primary">
                    {donor.full_name}
                  </h2>
                  <div className="mt-2 flex flex-col gap-1.5">
                    <div className="flex items-center gap-2 text-sm text-warm-text-secondary">
                      <Mail className="h-4 w-4" />
                      {donor.email}
                    </div>
                    {donor.country && (
                      <div className="flex items-center gap-2 text-sm text-warm-text-secondary">
                        <Globe className="h-4 w-4" />
                        {LABEL_COUNTRY}:{" "}
                        {COUNTRY_OPTIONS[donor.country] ?? donor.country}
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-warm-text-secondary">
                      <DollarSign className="h-4 w-4" />
                      {LABEL_CURRENCY_PREF}: {donor.currency_preference}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-warm-text-secondary">
                      <Calendar className="h-4 w-4" />
                      {LABEL_DONOR_SINCE}: {formatDate(donor.created_at)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-warm-text-tertiary" />
                  <span className="text-sm font-medium text-warm-text-secondary">
                    {LABEL_GDPR_STATUS}:
                  </span>
                  {donor.gdpr_consent_at ? (
                    <span className="inline-flex rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                      {LABEL_GDPR_YES}
                    </span>
                  ) : (
                    <span className="inline-flex rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-700">
                      {LABEL_GDPR_NO}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Lifetime stats */}
            <div className="mb-6">
              <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
                <TrendingUp className="h-5 w-5 text-primary-600" />
                {LABEL_LIFETIME_STATS}
              </h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {/* Total per currency */}
                {lifetimeStats.byCurrency.map((ct) => (
                  <div
                    key={ct.currency}
                    className="rounded-lg border border-warm-border bg-warm-surface p-4"
                  >
                    <p className="text-xs font-medium text-warm-text-tertiary">
                      {LABEL_TOTAL_DONATED} ({ct.currency})
                    </p>
                    <p className="mt-1 text-lg font-bold text-warm-text-primary">
                      {formatCurrency(ct.totalCents, ct.currency)}
                    </p>
                    <p className="text-xs text-warm-text-tertiary">
                      {ct.count} {ct.count === 1 ? "donacion" : "donaciones"}
                    </p>
                  </div>
                ))}

                {/* Total donation count */}
                <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
                  <p className="text-xs font-medium text-warm-text-tertiary">
                    {LABEL_TOTAL_DONATIONS}
                  </p>
                  <p className="mt-1 text-lg font-bold text-warm-text-primary">
                    {lifetimeStats.totalDonations}
                  </p>
                </div>

                {/* Last donation */}
                {lifetimeStats.lastDonation && (
                  <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
                    <p className="text-xs font-medium text-warm-text-tertiary">
                      {LABEL_LAST_DONATION}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-warm-text-primary">
                      {formatCurrency(
                        lifetimeStats.lastDonation.amount_cents,
                        lifetimeStats.lastDonation.currency
                      )}
                    </p>
                    <p className="text-xs text-warm-text-tertiary">
                      {formatDate(lifetimeStats.lastDonation.created_at)}
                    </p>
                  </div>
                )}

                {/* Average per currency */}
                {lifetimeStats.byCurrency.map((ct) => (
                  <div
                    key={`avg-${ct.currency}`}
                    className="rounded-lg border border-warm-border bg-warm-surface p-4"
                  >
                    <p className="text-xs font-medium text-warm-text-tertiary">
                      {LABEL_AVG_DONATION} ({ct.currency})
                    </p>
                    <p className="mt-1 text-lg font-bold text-warm-text-primary">
                      {ct.count > 0
                        ? formatCurrency(
                            Math.round(ct.totalCents / ct.count),
                            ct.currency
                          )
                        : "-"}
                    </p>
                  </div>
                ))}
              </div>

              {lifetimeStats.totalDonations === 0 && (
                <div className="mt-4 rounded-lg border border-warm-border bg-warm-surface p-6 text-center">
                  <DollarSign
                    className="mx-auto h-8 w-8 text-primary-300"
                    aria-hidden="true"
                  />
                  <p className="mt-2 text-sm text-warm-text-secondary">
                    {LABEL_NO_DONATIONS}
                  </p>
                </div>
              )}
            </div>

            {/* Donation history */}
            <div>
              <h3 className="mb-3 text-base font-semibold text-warm-text-primary">
                {LABEL_DONATION_HISTORY}
              </h3>

              {/* Donations error */}
              {donationsError && (
                <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-sm text-red-800">{donationsError}</p>
                </div>
              )}

              {/* Donations loading */}
              {isLoadingDonations && (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
                </div>
              )}

              {/* Donations table */}
              {!isLoadingDonations && !donationsError && donations.length > 0 && (
                <>
                  <div className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-warm-border bg-warm-bg">
                            <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                              {LABEL_DATE}
                            </th>
                            <th className="px-4 py-3 text-right font-medium text-warm-text-secondary">
                              {LABEL_AMOUNT}
                            </th>
                            <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                              {LABEL_METHOD}
                            </th>
                            <th className="px-4 py-3 text-center font-medium text-warm-text-secondary">
                              {LABEL_STATUS}
                            </th>
                            <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                              {LABEL_CATEGORY}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {donations.map((donation) => (
                            <tr
                              key={donation.id}
                              className="border-b border-warm-border last:border-b-0 transition-colors hover:bg-warm-bg"
                            >
                              <td className="px-4 py-3 text-warm-text-secondary">
                                {formatShortDate(donation.created_at)}
                              </td>
                              <td className="px-4 py-3 text-right font-medium text-warm-text-primary">
                                {formatCurrency(
                                  donation.amount_cents,
                                  donation.currency
                                )}
                              </td>
                              <td className="px-4 py-3 text-warm-text-secondary">
                                {METHOD_OPTIONS[donation.payment_method] ??
                                  donation.payment_method}
                                {donation.is_recurring && (
                                  <span className="ml-1 inline-flex rounded-full bg-purple-100 px-1.5 py-0.5 text-xs font-medium text-purple-700">
                                    Recurrente
                                  </span>
                                )}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <span
                                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                                    STATUS_COLORS[donation.status] ??
                                    "bg-gray-100 text-gray-700"
                                  }`}
                                >
                                  {STATUS_OPTIONS[donation.status] ??
                                    donation.status}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-warm-text-secondary">
                                {donation.fund_category
                                  ? CATEGORY_LABELS[donation.fund_category] ??
                                    donation.fund_category
                                  : "-"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Pagination */}
                  <div className="mt-4 flex items-center justify-between">
                    <p className="text-sm text-warm-text-secondary">
                      {LABEL_SHOWING}{" "}
                      {(currentPage - 1) * PAGE_SIZE + 1}-
                      {(currentPage - 1) * PAGE_SIZE + donations.length}
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          setCurrentPage((prev) => Math.max(1, prev - 1))
                        }
                        disabled={currentPage <= 1}
                        className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        {LABEL_PREVIOUS}
                      </button>
                      <span className="px-2 text-sm text-warm-text-secondary">
                        Pagina {currentPage}
                      </span>
                      <button
                        onClick={() => setCurrentPage((prev) => prev + 1)}
                        disabled={!hasMore}
                        className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {LABEL_NEXT}
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </>
              )}

              {/* Empty donations */}
              {!isLoadingDonations &&
                !donationsError &&
                donations.length === 0 && (
                  <div className="rounded-lg border border-warm-border bg-warm-surface p-6 text-center">
                    <p className="text-sm text-warm-text-secondary">
                      {LABEL_NO_DONATIONS}
                    </p>
                  </div>
                )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
