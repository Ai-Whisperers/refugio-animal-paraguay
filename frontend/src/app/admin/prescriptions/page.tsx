"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ClipboardList,
  RefreshCw,
  AlertCircle,
  PawPrint,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Recetas Medicas";
const LABEL_SUBTITLE = "Medicamentos activos y prescritos por animal";
const LABEL_LOADING = "Cargando recetas...";
const LABEL_ERROR = "Error al cargar recetas";
const LABEL_RETRY = "Reintentar";
const LABEL_REFRESH = "Actualizar";
const LABEL_EMPTY = "No hay recetas para mostrar.";
const LABEL_ANIMAL = "Animal";
const LABEL_MEDICATION = "Medicamento";
const LABEL_DOSAGE = "Dosis";
const LABEL_FREQUENCY = "Frecuencia";
const LABEL_STATUS = "Estado";
const LABEL_START = "Inicio";
const LABEL_END = "Fin";
const LABEL_VIEW_ANIMAL = "Ver animal";
const LABEL_FILTER_STATUS = "Estado";
const LABEL_FILTER_ALL = "Todos";
const LABEL_TOTAL = "Total";

const FREQUENCY_LABELS: Record<string, string> = {
  once: "Una vez",
  daily: "Diario",
  twice_daily: "2 veces/dia",
  three_times_daily: "3 veces/dia",
  weekly: "Semanal",
  biweekly: "Quincenal",
  monthly: "Mensual",
  as_needed: "Segun necesidad",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Activo",
  completed: "Completado",
  discontinued: "Discontinuado",
};

type MedicationStatus = "active" | "completed" | "discontinued";

interface PrescriptionRow {
  id: string;
  treatment_id: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string | null;
  start_date: string;
  end_date: string | null;
  medication_status: MedicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  animal_id: string;
  animal_name: string;
  animal_species: string;
}

interface PrescriptionListResponse {
  items: PrescriptionRow[];
  total: number;
  page: number;
  page_size: number;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function StatusBadge({ status }: { status: MedicationStatus }) {
  const configs: Record<MedicationStatus, { icon: React.ReactNode; classes: string }> = {
    active: {
      icon: <Clock className="h-3 w-3" />,
      classes: "bg-green-100 text-green-700 border-green-200",
    },
    completed: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      classes: "bg-blue-100 text-blue-700 border-blue-200",
    },
    discontinued: {
      icon: <XCircle className="h-3 w-3" />,
      classes: "bg-gray-100 text-gray-600 border-gray-200",
    },
  };

  const { icon, classes } = configs[status] ?? configs.active;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${classes}`}
    >
      {icon}
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

interface PrescriptionRowProps {
  row: PrescriptionRow;
  onViewAnimal: (id: string) => void;
}

function PrescriptionItem({ row, onViewAnimal }: PrescriptionRowProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-warm-border bg-warm-bg px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3 min-w-0">
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-100">
          <PawPrint className="h-4 w-4 text-primary-600" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-warm-text-primary">
            {row.animal_name}
            <span className="ml-1.5 text-xs font-normal text-warm-text-tertiary">
              ({row.animal_species})
            </span>
          </p>
          <p className="text-sm text-warm-text-primary font-medium mt-0.5">{row.name}</p>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-warm-text-secondary">
            <span>
              {LABEL_DOSAGE}: {row.dosage}
            </span>
            <span>
              {LABEL_FREQUENCY}: {FREQUENCY_LABELS[row.frequency] ?? row.frequency}
            </span>
            {row.route && <span>Via: {row.route}</span>}
            <span>
              {LABEL_START}: {formatDate(row.start_date)}
            </span>
            {row.end_date && (
              <span>
                {LABEL_END}: {formatDate(row.end_date)}
              </span>
            )}
          </div>
          {row.notes && (
            <p className="mt-1 text-xs text-warm-text-tertiary italic line-clamp-1">
              {row.notes}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 sm:flex-shrink-0 pl-11 sm:pl-0">
        <StatusBadge status={row.medication_status} />
        <button
          onClick={() => onViewAnimal(row.animal_id)}
          className="rounded-lg border border-warm-border px-2.5 py-1 text-xs text-warm-text-secondary transition-colors hover:bg-warm-surface whitespace-nowrap"
        >
          {LABEL_VIEW_ANIMAL}
        </button>
      </div>
    </div>
  );
}

export default function PrescriptionsPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [items, setItems] = useState<PrescriptionRow[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("active");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchPrescriptions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: "1", page_size: "50" });
      if (statusFilter !== "all") {
        params.set("status", statusFilter);
      }
      const data = await api.get<PrescriptionListResponse>(
        `/prescriptions?${params.toString()}`
      );
      setItems(data.items);
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
      fetchPrescriptions();
    }
  }, [isChecking, fetchPrescriptions]);

  function handleViewAnimal(animalId: string) {
    router.push(`/admin/animals/${animalId}?tab=medical`);
  }

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-100">
            <ClipboardList className="h-5 w-5 text-teal-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">{LABEL_PAGE_TITLE}</h1>
            <p className="text-xs text-warm-text-tertiary">{LABEL_SUBTITLE}</p>
          </div>
        </div>
        <button
          onClick={fetchPrescriptions}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          {LABEL_REFRESH}
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex items-center gap-3">
        <span className="text-sm text-warm-text-secondary">{LABEL_FILTER_STATUS}:</span>
        <div className="flex gap-2">
          {[
            { value: "all", label: LABEL_FILTER_ALL },
            { value: "active", label: "Activos" },
            { value: "completed", label: "Completados" },
            { value: "discontinued", label: "Discontinuados" },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setStatusFilter(value)}
              className={`rounded-lg px-3 py-1 text-xs font-medium border transition-colors ${
                statusFilter === value
                  ? "bg-primary-600 text-white border-primary-600"
                  : "border-warm-border text-warm-text-secondary hover:bg-warm-bg"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        {!isLoading && (
          <span className="ml-auto text-xs text-warm-text-tertiary">
            {LABEL_TOTAL}: {total}
          </span>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
          <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchPrescriptions}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Prescription list */}
      {!isLoading && !error && (
        <>
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-warm-border bg-warm-surface py-16 text-center">
              <ClipboardList className="mb-3 h-10 w-10 text-warm-text-tertiary" />
              <p className="text-sm text-warm-text-secondary">{LABEL_EMPTY}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((row) => (
                <PrescriptionItem
                  key={row.id}
                  row={row}
                  onViewAnimal={handleViewAnimal}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
