"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  Search,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Download,
  Globe,
  Shield,
} from "lucide-react";
import { isAuthenticated, getAccessToken } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Gestion de Donantes";
const LABEL_SEARCH_PLACEHOLDER = "Buscar por nombre o email...";
const LABEL_COUNTRY_FILTER = "Pais";
const LABEL_GDPR_FILTER = "GDPR";
const LABEL_ALL = "Todos";
const LABEL_GDPR_YES = "Con consentimiento";
const LABEL_GDPR_NO = "Sin consentimiento";
const LABEL_LOADING = "Cargando donantes...";
const LABEL_ERROR = "Error al cargar donantes";
const LABEL_EMPTY = "No se encontraron donantes";
const LABEL_EMPTY_FILTERED = "No hay donantes que coincidan con los filtros";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";
const LABEL_NAME = "Nombre";
const LABEL_EMAIL = "Email";
const LABEL_COUNTRY = "Pais";
const LABEL_TOTAL_DONATED = "Total Donado";
const LABEL_DONATIONS = "Donaciones";
const LABEL_REGISTERED = "Registrado";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_EXPORT = "Exportar CSV";
const LABEL_GDPR = "GDPR";

const PAGE_SIZE = 20;

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

// --- Types ---
interface DonorListItem {
  id: string;
  full_name: string;
  email: string;
  country: string | null;
  currency_preference: string;
  gdpr_consent_at: string | null;
  total_donations: number;
  total_donated_cents: number;
  created_at: string;
  updated_at: string;
}

type SortField = "full_name" | "email" | "created_at";
type SortDirection = "asc" | "desc";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
    month: "short",
    day: "numeric",
  });
}

export default function AdminDonorsPage() {
  const router = useRouter();

  // --- Auth check ---
  const [isChecking, setIsChecking] = useState(true);

  // --- Data state ---
  const [donors, setDonors] = useState<DonorListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  // --- Filter/search state ---
  const [searchQuery, setSearchQuery] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [gdprFilter, setGdprFilter] = useState<"" | "true" | "false">("");

  // --- Sort state ---
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // --- Pagination state ---
  const [currentPage, setCurrentPage] = useState(1);

  // --- Debounced search ---
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // --- Auth check ---
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch, countryFilter, gdprFilter, sortField, sortDirection]);

  // --- Fetch donors ---
  const fetchDonors = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (debouncedSearch) {
        params.set("search", debouncedSearch);
      }
      if (countryFilter) {
        params.set("country", countryFilter);
      }
      if (gdprFilter) {
        params.set("has_gdpr_consent", gdprFilter);
      }
      params.set("sort_by", sortField);
      params.set("sort_order", sortDirection);
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((currentPage - 1) * PAGE_SIZE));

      const endpoint = `/donors?${params.toString()}`;
      const data = await api.get<DonorListItem[]>(endpoint);
      setDonors(data);
      // If we got a full page, there might be more
      setTotalCount(
        data.length < PAGE_SIZE
          ? (currentPage - 1) * PAGE_SIZE + data.length
          : (currentPage + 1) * PAGE_SIZE
      );
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, countryFilter, gdprFilter, sortField, sortDirection, currentPage]);

  useEffect(() => {
    if (!isChecking) {
      fetchDonors();
    }
  }, [isChecking, fetchDonors]);

  // --- Export handler ---
  async function handleExport() {
    try {
      const params = new URLSearchParams();
      if (debouncedSearch) {
        params.set("search", debouncedSearch);
      }
      if (countryFilter) {
        params.set("country", countryFilter);
      }
      if (gdprFilter) {
        params.set("has_gdpr_consent", gdprFilter);
      }
      params.set("sort_by", sortField);
      params.set("sort_order", sortDirection);

      const token = getAccessToken();
      const response = await fetch(
        `${API_BASE_URL}/donors/export?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Export failed");
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "donors-export.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("Error al exportar donantes");
    }
  }

  // --- Sort handler ---
  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  }

  function renderSortIcon(field: SortField) {
    if (sortField !== field) {
      return (
        <ChevronUp className="ml-1 inline h-3 w-3 text-warm-text-tertiary opacity-0 group-hover:opacity-50" />
      );
    }
    return sortDirection === "asc" ? (
      <ChevronUp className="ml-1 inline h-3 w-3 text-primary-600" />
    ) : (
      <ChevronDown className="ml-1 inline h-3 w-3 text-primary-600" />
    );
  }

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const hasMore = donors.length === PAGE_SIZE;

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
              onClick={() => router.push("/admin/dashboard")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <Users className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 rounded-lg border border-warm-border bg-warm-surface px-3 py-1.5 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg"
            >
              <Download className="h-4 w-4" />
              {LABEL_EXPORT}
            </button>
            <button
              onClick={fetchDonors}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Search and Filters */}
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-warm-text-tertiary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={LABEL_SEARCH_PLACEHOLDER}
              className="w-full rounded-lg border border-warm-border bg-warm-surface py-2 pl-10 pr-4 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>

          {/* Country filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="country-filter"
              className="text-sm font-medium text-warm-text-secondary"
            >
              <Globe className="mr-1 inline h-3.5 w-3.5" />
              {LABEL_COUNTRY_FILTER}:
            </label>
            <select
              id="country-filter"
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
              className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">{LABEL_ALL}</option>
              {Object.entries(COUNTRY_OPTIONS).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          {/* GDPR filter */}
          <div className="flex items-center gap-2">
            <label
              htmlFor="gdpr-filter"
              className="text-sm font-medium text-warm-text-secondary"
            >
              <Shield className="mr-1 inline h-3.5 w-3.5" />
              {LABEL_GDPR_FILTER}:
            </label>
            <select
              id="gdpr-filter"
              value={gdprFilter}
              onChange={(e) =>
                setGdprFilter(e.target.value as "" | "true" | "false")
              }
              className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">{LABEL_ALL}</option>
              <option value="true">{LABEL_GDPR_YES}</option>
              <option value="false">{LABEL_GDPR_NO}</option>
            </select>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={fetchDonors}
              className="mt-2 text-sm font-medium text-red-700 underline hover:text-red-900"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
            <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && donors.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
            <Users
              className="mx-auto h-12 w-12 text-primary-300"
              aria-hidden="true"
            />
            <p className="mt-4 text-warm-text-secondary">
              {debouncedSearch || countryFilter || gdprFilter
                ? LABEL_EMPTY_FILTERED
                : LABEL_EMPTY}
            </p>
          </div>
        )}

        {/* Donors table */}
        {!isLoading && !error && donors.length > 0 && (
          <>
            <div className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-warm-border bg-warm-bg">
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("full_name")}
                      >
                        {LABEL_NAME}
                        {renderSortIcon("full_name")}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("email")}
                      >
                        {LABEL_EMAIL}
                        {renderSortIcon("email")}
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                        {LABEL_COUNTRY}
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-warm-text-secondary">
                        {LABEL_DONATIONS}
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-warm-text-secondary">
                        {LABEL_TOTAL_DONATED}
                      </th>
                      <th className="px-4 py-3 text-center font-medium text-warm-text-secondary">
                        {LABEL_GDPR}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("created_at")}
                      >
                        {LABEL_REGISTERED}
                        {renderSortIcon("created_at")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {donors.map((donor) => (
                      <tr
                        key={donor.id}
                        className="border-b border-warm-border last:border-b-0 transition-colors hover:bg-warm-bg cursor-pointer"
                        onClick={() =>
                          router.push(`/admin/donors/${donor.id}`)
                        }
                      >
                        <td className="px-4 py-3">
                          <span className="font-medium text-warm-text-primary">
                            {donor.full_name}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {donor.email}
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {donor.country
                            ? COUNTRY_OPTIONS[donor.country] ?? donor.country
                            : "-"}
                        </td>
                        <td className="px-4 py-3 text-right text-warm-text-secondary">
                          {donor.total_donations}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-warm-text-primary">
                          {donor.total_donated_cents > 0
                            ? formatCurrency(
                                donor.total_donated_cents,
                                donor.currency_preference
                              )
                            : "-"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {donor.gdpr_consent_at ? (
                            <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                              Si
                            </span>
                          ) : (
                            <span className="inline-flex rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                              No
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-warm-text-secondary">
                          {formatDate(donor.created_at)}
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
                {(currentPage - 1) * PAGE_SIZE + donors.length}{" "}
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
                  onClick={() =>
                    setCurrentPage((prev) => prev + 1)
                  }
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
      </div>
    </div>
  );
}
