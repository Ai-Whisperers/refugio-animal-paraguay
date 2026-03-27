"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Megaphone,
  Plus,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Star,
  Edit,
  BarChart3,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Gestion de Campanas";
const LABEL_LOADING = "Cargando campanas...";
const LABEL_ERROR = "Error al cargar campanas";
const LABEL_EMPTY = "No hay campanas creadas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_NEW_CAMPAIGN = "Nueva Campana";
const LABEL_SHOWING = "Mostrando";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ALL = "Todos";
const LABEL_STATUS_FILTER = "Estado";

const PAGE_SIZE = 20;

const STATUS_OPTIONS: Record<string, string> = {
  draft: "Borrador",
  active: "Activa",
  paused: "Pausada",
  completed: "Completada",
  archived: "Archivada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  completed: "bg-blue-100 text-blue-700",
  archived: "bg-gray-100 text-gray-500",
  cancelled: "bg-red-100 text-red-700",
};

const CATEGORY_LABELS: Record<string, string> = {
  medical: "Medico",
  food: "Alimentacion",
  operations: "Operaciones",
  rescue: "Rescate",
  infrastructure: "Infraestructura",
  general: "General",
};

interface CampaignListItem {
  id: string;
  title: string;
  description: string;
  target_amount_cents: number;
  currency: string;
  fund_category: string;
  status: string;
  featured: boolean;
  image_url: string | null;
  deadline: string | null;
  created_at: string;
  updated_at: string;
}

function formatCurrency(cents: number, currency: string = "EUR"): string {
  const amount = cents / 100;
  const localeMap: Record<string, string> = {
    EUR: "es-ES",
    USD: "en-US",
    PYG: "es-PY",
  };
  const locale = localeMap[currency] ?? "es-PY";
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

export default function AdminCampaignsPage() {
  const router = useRouter();

  const [isChecking, setIsChecking] = useState(true);
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [featuredFilter, setFeaturedFilter] = useState<string>("");
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
  }, [statusFilter, featuredFilter]);

  const fetchCampaigns = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (featuredFilter) params.set("featured", featuredFilter);
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((currentPage - 1) * PAGE_SIZE));

      const data = await api.get<CampaignListItem[]>(
        `/admin/campaigns?${params.toString()}`
      );
      setCampaigns(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, featuredFilter, currentPage]);

  useEffect(() => {
    if (!isChecking) {
      fetchCampaigns();
    }
  }, [isChecking, fetchCampaigns]);

  const hasMore = campaigns.length === PAGE_SIZE;

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
            <Megaphone
              className="h-6 w-6 text-primary-600"
              aria-hidden="true"
            />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/admin/campaigns/new")}
              className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              {LABEL_NEW_CAMPAIGN}
            </button>
            <button
              onClick={fetchCampaigns}
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
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
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
          <div className="flex items-center gap-2">
            <label
              htmlFor="featured-filter"
              className="text-sm font-medium text-warm-text-secondary"
            >
              Destacada:
            </label>
            <select
              id="featured-filter"
              value={featuredFilter}
              onChange={(e) => setFeaturedFilter(e.target.value)}
              className="rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="">{LABEL_ALL}</option>
              <option value="true">Si</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
            <button
              onClick={fetchCampaigns}
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
        {!isLoading && !error && campaigns.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
            <Megaphone
              className="mx-auto h-12 w-12 text-primary-300"
              aria-hidden="true"
            />
            <p className="mt-4 text-warm-text-secondary">{LABEL_EMPTY}</p>
            <button
              onClick={() => router.push("/admin/campaigns/new")}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              {LABEL_NEW_CAMPAIGN}
            </button>
          </div>
        )}

        {/* Campaigns grid */}
        {!isLoading && !error && campaigns.length > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface transition-shadow hover:shadow-md"
                >
                  {/* Image or placeholder */}
                  <div className="relative h-40 bg-warm-bg">
                    {campaign.image_url ? (
                      <img
                        src={campaign.image_url}
                        alt={campaign.title}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center">
                        <Megaphone className="h-12 w-12 text-warm-text-tertiary opacity-30" />
                      </div>
                    )}
                    {/* Status badge */}
                    <span
                      className={`absolute left-3 top-3 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        STATUS_COLORS[campaign.status] ??
                        "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {STATUS_OPTIONS[campaign.status] ?? campaign.status}
                    </span>
                    {campaign.featured && (
                      <span className="absolute right-3 top-3">
                        <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3 className="text-sm font-semibold text-warm-text-primary line-clamp-1">
                      {campaign.title}
                    </h3>
                    <p className="mt-1 text-xs text-warm-text-tertiary line-clamp-2">
                      {campaign.description}
                    </p>

                    <div className="mt-3 flex items-center justify-between">
                      <div>
                        <p className="text-xs text-warm-text-tertiary">Meta</p>
                        <p className="text-sm font-medium text-warm-text-primary">
                          {formatCurrency(
                            campaign.target_amount_cents,
                            campaign.currency
                          )}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-warm-text-tertiary">
                          Categoria
                        </p>
                        <p className="text-sm text-warm-text-secondary">
                          {CATEGORY_LABELS[campaign.fund_category] ??
                            campaign.fund_category}
                        </p>
                      </div>
                    </div>

                    {campaign.deadline && (
                      <p className="mt-2 text-xs text-warm-text-tertiary">
                        Fecha limite: {formatDate(campaign.deadline)}
                      </p>
                    )}

                    <div className="mt-3 flex items-center justify-between border-t border-warm-border pt-3">
                      <p className="text-xs text-warm-text-tertiary">
                        Creada: {formatDate(campaign.created_at)}
                      </p>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() =>
                            router.push(`/admin/campaigns/${campaign.id}/progress`)
                          }
                          className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-green-600 transition-colors hover:bg-green-50"
                        >
                          <BarChart3 className="h-3 w-3" />
                          Progreso
                        </button>
                        <button
                          onClick={() =>
                            router.push(`/admin/campaigns/${campaign.id}/edit`)
                          }
                          className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-primary-600 transition-colors hover:bg-primary-50"
                        >
                          <Edit className="h-3 w-3" />
                          Editar
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-warm-text-secondary">
                {LABEL_SHOWING}{" "}
                {(currentPage - 1) * PAGE_SIZE + 1}-
                {(currentPage - 1) * PAGE_SIZE + campaigns.length}
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
