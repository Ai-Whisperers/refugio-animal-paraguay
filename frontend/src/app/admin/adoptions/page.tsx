"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Heart,
  Search,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Clock,
  CheckCircle,
  XCircle,
  Ban,
  Filter,
  BarChart3,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { AdoptionRequestStatus } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Solicitudes de Adopcion";
const LABEL_LOADING = "Cargando solicitudes...";
const LABEL_ERROR = "Error al cargar solicitudes";
const LABEL_EMPTY = "No hay solicitudes de adopcion";
const LABEL_EMPTY_FILTERED = "No hay solicitudes con este estado";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_ANALYTICS = "Analiticas";
const LABEL_SHOWING = "Mostrando";
const LABEL_OF = "de";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ALL = "Todas";
const LABEL_PENDING = "Pendientes";
const LABEL_APPROVED = "Aprobadas";
const LABEL_REJECTED = "Rechazadas";
const LABEL_CANCELLED = "Canceladas";
const LABEL_ADOPTER = "Adoptante";
const LABEL_ANIMAL = "Animal";
const LABEL_STATUS = "Estado";
const LABEL_SUBMITTED = "Fecha de solicitud";
const LABEL_DECIDED = "Fecha de decision";
const LABEL_VIEW = "Ver detalle";

const PAGE_SIZE = 20;

// --- Status config ---
const STATUS_TABS: { key: AdoptionRequestStatus | "all"; label: string }[] = [
  { key: "all", label: LABEL_ALL },
  { key: "pending", label: LABEL_PENDING },
  { key: "approved", label: LABEL_APPROVED },
  { key: "rejected", label: LABEL_REJECTED },
  { key: "cancelled", label: LABEL_CANCELLED },
];

const STATUS_LABELS: Record<AdoptionRequestStatus, string> = {
  pending: "Pendiente",
  approved: "Aprobada",
  rejected: "Rechazada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<AdoptionRequestStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

const STATUS_ICONS: Record<AdoptionRequestStatus, typeof Clock> = {
  pending: Clock,
  approved: CheckCircle,
  rejected: XCircle,
  cancelled: Ban,
};

// --- Types for enriched response ---
interface AdoptionRequestListItem {
  id: string;
  animal_id: string;
  adopter_id: string;
  status: AdoptionRequestStatus;
  submitted_at: string;
  decided_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface AdopterInfo {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
}

interface AnimalInfo {
  id: string;
  name: string;
  species: string;
  breed: string | null;
  primary_photo_url: string | null;
}

interface EnrichedAdoptionRequest extends AdoptionRequestListItem {
  adopter?: AdopterInfo;
  animal?: AnimalInfo;
}

export default function AdminAdoptionsPage() {
  const router = useRouter();

  // --- Auth check ---
  const [isChecking, setIsChecking] = useState(true);

  // --- Data state ---
  const [requests, setRequests] = useState<EnrichedAdoptionRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- Filter state ---
  const [activeTab, setActiveTab] = useState<AdoptionRequestStatus | "all">("all");
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchRequests = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (activeTab !== "all") {
        params.set("status", activeTab);
      }
      params.set("offset", String(page * PAGE_SIZE));
      params.set("limit", String(PAGE_SIZE));

      const queryString = params.toString();
      const endpoint = `/adoption-requests${queryString ? `?${queryString}` : ""}`;

      const data = await api.get<AdoptionRequestListItem[]>(endpoint);
      setTotalCount(data.length < PAGE_SIZE ? page * PAGE_SIZE + data.length : (page + 1) * PAGE_SIZE + 1);

      // Enrich with adopter and animal info
      const enriched: EnrichedAdoptionRequest[] = await Promise.all(
        data.map(async (req) => {
          const enrichedReq: EnrichedAdoptionRequest = { ...req };

          try {
            enrichedReq.adopter = await api.get<AdopterInfo>(`/adopters/${req.adopter_id}`);
          } catch {
            // Adopter may have been deleted (GDPR)
          }

          try {
            enrichedReq.animal = await api.get<AnimalInfo>(`/animals/${req.animal_id}`);
          } catch {
            // Animal may have been removed
          }

          return enrichedReq;
        })
      );

      setRequests(enriched);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [activeTab, page]);

  useEffect(() => {
    if (!isChecking) {
      fetchRequests();
    }
  }, [isChecking, fetchRequests]);

  function handleTabChange(tab: AdoptionRequestStatus | "all") {
    setActiveTab(tab);
    setPage(0);
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  const hasMore = requests.length === PAGE_SIZE;

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
            <Heart className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push("/admin/adoptions/analytics")}
              className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            >
              <BarChart3 className="h-4 w-4" />
              {LABEL_ANALYTICS}
            </button>
            <button
              onClick={fetchRequests}
              disabled={isLoading}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary disabled:opacity-50"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Status filter tabs */}
        <div className="mb-6 flex flex-wrap gap-2" role="tablist" aria-label="Filtrar por estado">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-primary-600 text-white"
                  : "bg-warm-surface text-warm-text-secondary hover:bg-warm-bg hover:text-warm-text-primary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

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
              onClick={fetchRequests}
              className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && requests.length === 0 && (
          <div className="rounded-lg border border-warm-border bg-warm-surface p-12 text-center">
            <Heart className="mx-auto h-12 w-12 text-warm-text-secondary opacity-40" />
            <p className="mt-4 text-warm-text-secondary">
              {activeTab === "all" ? LABEL_EMPTY : LABEL_EMPTY_FILTERED}
            </p>
          </div>
        )}

        {/* Request list */}
        {!isLoading && !error && requests.length > 0 && (
          <>
            <div className="overflow-hidden rounded-lg border border-warm-border bg-warm-surface">
              <table className="min-w-full divide-y divide-warm-border">
                <thead className="bg-warm-bg">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-warm-text-secondary">
                      {LABEL_ADOPTER}
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-warm-text-secondary">
                      {LABEL_ANIMAL}
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-warm-text-secondary">
                      {LABEL_STATUS}
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-warm-text-secondary">
                      {LABEL_SUBMITTED}
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-warm-text-secondary">
                      {LABEL_DECIDED}
                    </th>
                    <th scope="col" className="relative px-4 py-3">
                      <span className="sr-only">{LABEL_VIEW}</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-warm-border">
                  {requests.map((req) => {
                    const StatusIcon = STATUS_ICONS[req.status];
                    return (
                      <tr
                        key={req.id}
                        className="transition-colors hover:bg-warm-bg cursor-pointer"
                        onClick={() => router.push(`/admin/adoptions/${req.id}`)}
                      >
                        <td className="whitespace-nowrap px-4 py-3">
                          <div>
                            <p className="text-sm font-medium text-warm-text-primary">
                              {req.adopter?.full_name ?? "Adoptante eliminado"}
                            </p>
                            <p className="text-xs text-warm-text-secondary">
                              {req.adopter?.email ?? "—"}
                            </p>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <div className="flex items-center gap-2">
                            {req.animal?.primary_photo_url && (
                              <img
                                src={req.animal.primary_photo_url}
                                alt={req.animal.name}
                                className="h-8 w-8 rounded-full object-cover"
                              />
                            )}
                            <div>
                              <p className="text-sm font-medium text-warm-text-primary">
                                {req.animal?.name ?? "Animal eliminado"}
                              </p>
                              <p className="text-xs text-warm-text-secondary capitalize">
                                {req.animal?.species ?? "—"}{req.animal?.breed ? ` - ${req.animal.breed}` : ""}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[req.status]}`}>
                            <StatusIcon className="h-3 w-3" />
                            {STATUS_LABELS[req.status]}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-warm-text-secondary">
                          {formatDate(req.submitted_at)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-sm text-warm-text-secondary">
                          {req.decided_at ? formatDate(req.decided_at) : "—"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                          <span className="text-primary-600 hover:text-primary-800 font-medium">
                            {LABEL_VIEW}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-warm-text-secondary">
                {LABEL_SHOWING} {page * PAGE_SIZE + 1}-{page * PAGE_SIZE + requests.length}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                  {LABEL_PREVIOUS}
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasMore}
                  className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:opacity-40"
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
