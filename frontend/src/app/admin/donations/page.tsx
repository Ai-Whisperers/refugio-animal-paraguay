"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  DollarSign,
  Search,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Download,
  Filter,
  Calendar,
} from "lucide-react";
import { isAuthenticated, getAccessToken } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Historial de Donaciones";
const LABEL_SEARCH_PLACEHOLDER = "Buscar por ID de donante...";
const LABEL_CURRENCY_FILTER = "Moneda";
const LABEL_STATUS_FILTER = "Estado";
const LABEL_METHOD_FILTER = "Metodo";
const LABEL_DATE_FROM = "Desde";
const LABEL_DATE_TO = "Hasta";
const LABEL_ALL = "Todos";
const LABEL_LOADING = "Cargando donaciones...";
const LABEL_ERROR = "Error al cargar donaciones";
const LABEL_EMPTY = "No se encontraron donaciones";
const LABEL_EMPTY_FILTERED = "No hay donaciones que coincidan con los filtros";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_SHOWING = "Mostrando";
const LABEL_DONOR = "Donante";
const LABEL_AMOUNT = "Monto";
const LABEL_CURRENCY = "Moneda";
const LABEL_METHOD = "Metodo de Pago";
const LABEL_STATUS = "Estado";
const LABEL_CATEGORY = "Categoria";
const LABEL_DATE = "Fecha";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_EXPORT = "Exportar CSV";
const LABEL_CLEAR_FILTERS = "Limpiar filtros";
const LABEL_FILTERED_TOTAL = "Total filtrado";

const PAGE_SIZE = 20;

const CURRENCY_OPTIONS: Record<string, string> = {
  EUR: "Euro (EUR)",
  PYG: "Guarani (PYG)",
  USD: "Dolar (USD)",
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
interface DonationListItem {
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

type SortField = "created_at" | "amount_cents";
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
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDateForInput(dateString: string): string {
  return new Date(dateString).toISOString().split("T")[0];
}

export default function AdminDonationsPage() {
  const router = useRouter();

  // --- Auth check ---
  const [isChecking, setIsChecking] = useState(true);

  // --- Data state ---
  const [donations, setDonations] = useState<DonationListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  // --- Filter state ---
  const [currencyFilter, setCurrencyFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [methodFilter, setMethodFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // --- Sort state ---
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // --- Pagination state ---
  const [currentPage, setCurrentPage] = useState(1);

  // --- Auth check ---
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [currencyFilter, statusFilter, methodFilter, dateFrom, dateTo, sortField, sortDirection]);

  // --- Build query params ---
  const buildParams = useCallback(
    (includePagination: boolean = true) => {
      const params = new URLSearchParams();
      if (currencyFilter) params.set("currency", currencyFilter);
      if (statusFilter) params.set("status", statusFilter);
      if (methodFilter) params.set("payment_method", methodFilter);
      if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString());
      if (dateTo) {
        const endDate = new Date(dateTo);
        endDate.setHours(23, 59, 59, 999);
        params.set("date_to", endDate.toISOString());
      }
      if (includePagination) {
        params.set("limit", String(PAGE_SIZE));
        params.set("offset", String((currentPage - 1) * PAGE_SIZE));
      }
      return params;
    },
    [currencyFilter, statusFilter, methodFilter, dateFrom, dateTo, currentPage]
  );

  // --- Fetch donations ---
  const fetchDonations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = buildParams();
      const endpoint = `/donations?${params.toString()}`;
      const data = await api.get<DonationListItem[]>(endpoint);
      setDonations(data);
      // Estimate total count for pagination
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
  }, [buildParams, currentPage]);

  useEffect(() => {
    if (!isChecking) {
      fetchDonations();
    }
  }, [isChecking, fetchDonations]);

  // --- Export handler ---
  async function handleExport() {
    try {
      const params = buildParams(false);
      const token = getAccessToken();
      const response = await fetch(
        `${API_BASE_URL}/donations/export?${params.toString()}`,
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
      a.download = `donations-export-${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("Error al exportar donaciones");
    }
  }

  // --- Clear all filters ---
  function handleClearFilters() {
    setCurrencyFilter("");
    setStatusFilter("");
    setMethodFilter("");
    setDateFrom("");
    setDateTo("");
  }

  const hasActiveFilters = currencyFilter || statusFilter || methodFilter || dateFrom || dateTo;

  // --- Sort handler ---
  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection(field === "created_at" ? "desc" : "asc");
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

  // --- Compute filtered totals per currency ---
  const filteredTotals = donations.reduce<Record<string, number>>(
    (acc, donation) => {
      const key = donation.currency;
      acc[key] = (acc[key] ?? 0) + donation.amount_cents;
      return acc;
    },
    {}
  );

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
              onClick={() => router.push("/admin/dashboard")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <DollarSign className="h-6 w-6 text-primary-600" aria-hidden="true" />
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
              onClick={fetchDonations}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="mb-6 space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            {/* Currency filter */}
            <div className="flex items-center gap-2">
              <label
                htmlFor="currency-filter"
                className="text-sm font-medium text-warm-text-secondary"
              >
                {LABEL_CURRENCY_FILTER}:
              </label>
              <select
                id="currency-filter"
                value={currencyFilter}
                onChange={(e) => setCurrencyFilter(e.target.value)}
                className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">{LABEL_ALL}</option>
                {Object.entries(CURRENCY_OPTIONS).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            {/* Status filter */}
            <div className="flex items-center gap-2">
              <label
                htmlFor="status-filter"
                className="text-sm font-medium text-warm-text-secondary"
              >
                {LABEL_STATUS_FILTER}:
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
            </div>

            {/* Payment method filter */}
            <div className="flex items-center gap-2">
              <label
                htmlFor="method-filter"
                className="text-sm font-medium text-warm-text-secondary"
              >
                {LABEL_METHOD_FILTER}:
              </label>
              <select
                id="method-filter"
                value={methodFilter}
                onChange={(e) => setMethodFilter(e.target.value)}
                className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">{LABEL_ALL}</option>
                {Object.entries(METHOD_OPTIONS).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Date range filters */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-warm-text-tertiary" />
              <label
                htmlFor="date-from"
                className="text-sm font-medium text-warm-text-secondary"
              >
                {LABEL_DATE_FROM}:
              </label>
              <input
                id="date-from"
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <label
                htmlFor="date-to"
                className="text-sm font-medium text-warm-text-secondary"
              >
                {LABEL_DATE_TO}:
              </label>
              <input
                id="date-to"
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
              >
                <Filter className="h-3.5 w-3.5" />
                {LABEL_CLEAR_FILTERS}
              </button>
            )}
          </div>
        </div>

        {/* Filtered totals */}
        {!isLoading && !error && donations.length > 0 && Object.keys(filteredTotals).length > 0 && (
          <div className="mb-4 flex flex-wrap gap-3">
            {Object.entries(filteredTotals).map(([currency, totalCents]) => (
              <div
                key={currency}
                className="rounded-lg border border-warm-border bg-warm-surface px-4 py-2"
              >
                <span className="text-xs font-medium text-warm-text-tertiary">
                  {LABEL_FILTERED_TOTAL} ({currency})
                </span>
                <p className="text-sm font-semibold text-warm-text-primary">
                  {formatCurrency(totalCents, currency)}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={fetchDonations}
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
        {!isLoading && !error && donations.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
            <DollarSign
              className="mx-auto h-12 w-12 text-primary-300"
              aria-hidden="true"
            />
            <p className="mt-4 text-warm-text-secondary">
              {hasActiveFilters ? LABEL_EMPTY_FILTERED : LABEL_EMPTY}
            </p>
          </div>
        )}

        {/* Donations table */}
        {!isLoading && !error && donations.length > 0 && (
          <>
            <div className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-warm-border bg-warm-bg">
                      <th
                        className="group cursor-pointer px-4 py-3 text-left font-medium text-warm-text-secondary"
                        onClick={() => handleSort("created_at")}
                      >
                        {LABEL_DATE}
                        {renderSortIcon("created_at")}
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-warm-text-secondary">
                        {LABEL_DONOR}
                      </th>
                      <th
                        className="group cursor-pointer px-4 py-3 text-right font-medium text-warm-text-secondary"
                        onClick={() => handleSort("amount_cents")}
                      >
                        {LABEL_AMOUNT}
                        {renderSortIcon("amount_cents")}
                      </th>
                      <th className="px-4 py-3 text-center font-medium text-warm-text-secondary">
                        {LABEL_CURRENCY}
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
                          {formatDate(donation.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          {donation.donor_id ? (
                            <button
                              onClick={() =>
                                router.push(`/admin/donors/${donation.donor_id}`)
                              }
                              className="font-medium text-primary-600 hover:text-primary-700 hover:underline"
                            >
                              {donation.donor_id.slice(0, 8)}...
                            </button>
                          ) : (
                            <span className="text-warm-text-tertiary italic">
                              Anonimo
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-warm-text-primary">
                          {formatCurrency(
                            donation.amount_cents,
                            donation.currency
                          )}
                        </td>
                        <td className="px-4 py-3 text-center text-warm-text-secondary">
                          {donation.currency}
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
      </div>
    </div>
  );
}
