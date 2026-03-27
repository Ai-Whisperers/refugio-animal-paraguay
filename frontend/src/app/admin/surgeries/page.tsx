"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Scissors,
  RefreshCw,
  AlertCircle,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  PawPrint,
  Activity,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { SurgeryScheduleListResponse, SurgeryWithAnimal, SurgeryStatus } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Agenda de Cirugias";
const LABEL_LOADING = "Cargando agenda de cirugias...";
const LABEL_ERROR = "Error al cargar cirugias";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_REFRESH = "Actualizar";
const LABEL_EMPTY = "Sin cirugias";
const LABEL_EMPTY_SUB = "No hay cirugias que coincidan con los filtros seleccionados";
const LABEL_VIEW_ANIMAL = "Ver animal";
const LABEL_VIEW_RECOVERY = "Ver recuperacion";
const LABEL_ALL_STATUSES = "Todos los estados";
const LABEL_STATUS_FILTER = "Estado";
const LABEL_VET = "Veterinario";
const LABEL_TYPE = "Tipo";
const LABEL_DATE = "Fecha";
const LABEL_STATUS = "Estado";
const LABEL_TOTAL = "Total";

const STATUS_OPTIONS: { value: SurgeryStatus | ""; label: string }[] = [
  { value: "", label: LABEL_ALL_STATUSES },
  { value: "scheduled", label: "Programada" },
  { value: "in_progress", label: "En curso" },
  { value: "completed", label: "Completada" },
  { value: "cancelled", label: "Cancelada" },
  { value: "complications", label: "Complicaciones" },
];

const SURGERY_TYPE_LABELS: Record<string, string> = {
  spay: "Castración (hembra)",
  neuter: "Castración (macho)",
  mass_removal: "Extirpación de masa",
  orthopedic: "Ortopédica",
  dental: "Dental",
  emergency: "Emergencia",
  biopsy: "Biopsia",
  eye: "Ocular",
  other: "Otra",
};

const STATUS_CONFIG: Record<
  SurgeryStatus,
  {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    badge: string;
  }
> = {
  scheduled: {
    label: "Programada",
    icon: Calendar,
    color: "text-blue-600",
    badge: "bg-blue-100 text-blue-800",
  },
  in_progress: {
    label: "En curso",
    icon: Clock,
    color: "text-orange-600",
    badge: "bg-orange-100 text-orange-800",
  },
  completed: {
    label: "Completada",
    icon: CheckCircle2,
    color: "text-green-600",
    badge: "bg-green-100 text-green-800",
  },
  cancelled: {
    label: "Cancelada",
    icon: XCircle,
    color: "text-gray-500",
    badge: "bg-gray-100 text-gray-700",
  },
  complications: {
    label: "Complicaciones",
    icon: AlertTriangle,
    color: "text-red-600",
    badge: "bg-red-100 text-red-800",
  },
};

/** Statuses that have post-op monitoring (show recovery button). */
const RECOVERY_STATUSES: Set<SurgeryStatus> = new Set([
  "in_progress",
  "completed",
  "complications",
]);

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("es-PY", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// --- Surgery row component ---

interface SurgeryRowProps {
  surgery: SurgeryWithAnimal;
  onViewAnimal: (animalId: string) => void;
  onViewRecovery: (surgeryId: string) => void;
}

function SurgeryRow({ surgery, onViewAnimal, onViewRecovery }: SurgeryRowProps) {
  const config = STATUS_CONFIG[surgery.surgery_status] ?? STATUS_CONFIG.scheduled;
  const StatusIcon = config.icon;
  const typeLabel = SURGERY_TYPE_LABELS[surgery.surgery_type] ?? surgery.surgery_type;
  const showRecovery = RECOVERY_STATUSES.has(surgery.surgery_status);

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-warm-border bg-warm-bg p-4 transition-colors hover:bg-warm-surface sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-primary-100">
          <PawPrint className="h-4 w-4 text-primary-600" />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="truncate text-sm font-semibold text-warm-text-primary">
              {surgery.animal_name}
            </p>
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.badge}`}
            >
              <StatusIcon className="h-3 w-3" />
              {config.label}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-warm-text-secondary">
            {typeLabel} · {LABEL_VET}: {surgery.veterinarian_name}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 sm:justify-end">
        <div className="text-right">
          <p className="text-xs font-medium text-warm-text-primary">
            {formatDate(surgery.scheduled_date)}
          </p>
          {surgery.follow_up_date && (
            <p className="text-xs text-warm-text-tertiary">
              Seguimiento: {formatDate(surgery.follow_up_date)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {showRecovery && (
            <button
              onClick={() => onViewRecovery(surgery.id)}
              className="inline-flex items-center gap-1 rounded-lg border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700 transition-colors hover:bg-purple-100 whitespace-nowrap"
            >
              <Activity className="h-3 w-3" />
              {LABEL_VIEW_RECOVERY}
            </button>
          )}
          <button
            onClick={() => onViewAnimal(surgery.animal_id)}
            className="rounded-lg border border-warm-border px-2.5 py-1 text-xs font-medium text-warm-text-secondary transition-colors hover:bg-warm-surface hover:text-warm-text-primary whitespace-nowrap"
          >
            {LABEL_VIEW_ANIMAL}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Main page ---

export default function SurgerySchedulePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [surgeries, setSurgeries] = useState<SurgeryWithAnimal[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<SurgeryStatus | "">("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchSurgeries = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ size: "100" });
      if (statusFilter) {
        params.set("surgery_status", statusFilter);
      }
      const data = await api.get<SurgeryScheduleListResponse>(
        `/surgeries?${params.toString()}`
      );
      setSurgeries(data.items);
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
  }, [statusFilter]);

  useEffect(() => {
    if (!isChecking) {
      fetchSurgeries();
    }
  }, [isChecking, fetchSurgeries]);

  function handleViewAnimal(animalId: string) {
    router.push(`/admin/animals/${animalId}?tab=medical`);
  }

  function handleViewRecovery(surgeryId: string) {
    router.push(`/admin/surgeries/${surgeryId}/recovery`);
  }

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  const statusCounts = surgeries.reduce<Record<string, number>>((acc, s) => {
    acc[s.surgery_status] = (acc[s.surgery_status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="mx-auto max-w-4xl">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
            <Scissors className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            {!isLoading && (
              <p className="text-xs text-warm-text-tertiary">
                {total} {LABEL_TOTAL.toLowerCase()}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-warm-text-secondary">
              {LABEL_STATUS_FILTER}:
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as SurgeryStatus | "")}
              className="rounded-lg border border-warm-border bg-warm-bg px-2 py-1.5 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={fetchSurgeries}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
        </div>
      </div>

      {/* Status summary pills */}
      {!isLoading && !error && surgeries.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {Object.entries(STATUS_CONFIG).map(([statusKey, cfg]) => {
            const count = statusCounts[statusKey] ?? 0;
            if (count === 0) return null;
            const Icon = cfg.icon;
            return (
              <button
                key={statusKey}
                onClick={() =>
                  setStatusFilter(
                    statusFilter === statusKey ? "" : (statusKey as SurgeryStatus)
                  )
                }
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-all ${
                  statusFilter === statusKey
                    ? `${cfg.badge} ring-2 ring-offset-1 ring-current`
                    : cfg.badge
                }`}
              >
                <Icon className="h-3 w-3" />
                {cfg.label}: {count}
              </button>
            );
          })}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
          <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchSurgeries}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && surgeries.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-warm-border bg-warm-surface py-16">
          <Scissors className="h-10 w-10 text-warm-text-tertiary" />
          <p className="mt-3 text-sm font-medium text-warm-text-secondary">
            {LABEL_EMPTY}
          </p>
          <p className="mt-1 text-xs text-warm-text-tertiary">{LABEL_EMPTY_SUB}</p>
        </div>
      )}

      {/* Surgery list */}
      {!isLoading && !error && surgeries.length > 0 && (
        <div className="space-y-2">
          {surgeries.map((surgery) => (
            <SurgeryRow
              key={surgery.id}
              surgery={surgery}
              onViewAnimal={handleViewAnimal}
              onViewRecovery={handleViewRecovery}
            />
          ))}
        </div>
      )}
    </div>
  );
}
