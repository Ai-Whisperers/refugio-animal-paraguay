"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  RefreshCw,
  AlertCircle,
  PawPrint,
  Plus,
  X,
  Clock,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Citas Medicas";
const LABEL_SUBTITLE = "Proximas consultas veterinarias programadas";
const LABEL_LOADING = "Cargando citas...";
const LABEL_ERROR = "Error al cargar citas";
const LABEL_RETRY = "Reintentar";
const LABEL_REFRESH = "Actualizar";
const LABEL_EMPTY = "No hay citas programadas.";
const LABEL_TOTAL = "Total";
const LABEL_VET = "Veterinario";
const LABEL_ANIMAL = "Animal";
const LABEL_TYPE = "Tipo";
const LABEL_DATE = "Fecha";
const LABEL_REASON = "Motivo";
const LABEL_VIEW_ANIMAL = "Ver animal";
const LABEL_NEW_APPOINTMENT = "Nueva Cita";
const LABEL_INCLUDE_PAST = "Incluir pasadas";
const LABEL_CANCEL = "Cancelar";
const LABEL_SAVE = "Guardar";
const LABEL_SAVING = "Guardando...";
const LABEL_FORM_ANIMAL_ID = "ID del Animal";
const LABEL_FORM_VET = "Nombre del Veterinario";
const LABEL_FORM_DATE = "Fecha y Hora";
const LABEL_FORM_TYPE = "Tipo de Visita";
const LABEL_FORM_REASON = "Motivo (opcional)";

const VISIT_TYPE_LABELS: Record<string, string> = {
  checkup: "Chequeo general",
  emergency: "Emergencia",
  surgery: "Cirugia",
  vaccination: "Vacunacion",
  follow_up: "Seguimiento",
  dental: "Dental",
  other: "Otro",
};

const VISIT_TYPES = Object.entries(VISIT_TYPE_LABELS);

type VisitType = "checkup" | "emergency" | "surgery" | "vaccination" | "follow_up" | "dental" | "other";

interface AppointmentRow {
  id: string;
  animal_id: string;
  animal_name: string;
  animal_species: string;
  veterinarian_name: string;
  visit_type: VisitType;
  visit_status: string;
  visit_date: string;
  reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface AppointmentListResponse {
  items: AppointmentRow[];
  total: number;
  page: number;
  page_size: number;
}

function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("es-PY", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isUpcoming(isoString: string): boolean {
  return new Date(isoString) > new Date();
}

interface AppointmentItemProps {
  row: AppointmentRow;
  onViewAnimal: (id: string) => void;
}

function AppointmentItem({ row, onViewAnimal }: AppointmentItemProps) {
  const upcoming = isUpcoming(row.visit_date);

  return (
    <div
      className={`flex flex-col gap-2 rounded-lg border px-4 py-3 sm:flex-row sm:items-center sm:justify-between ${
        upcoming ? "border-warm-border bg-warm-bg" : "border-gray-200 bg-gray-50 opacity-75"
      }`}
    >
      <div className="flex items-start gap-3 min-w-0">
        <div
          className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${
            upcoming ? "bg-blue-100" : "bg-gray-100"
          }`}
        >
          <Calendar className={`h-4 w-4 ${upcoming ? "text-blue-600" : "text-gray-400"}`} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <p className="text-sm font-semibold text-warm-text-primary">{row.animal_name}</p>
            <span className="text-xs text-warm-text-tertiary">({row.animal_species})</span>
            <span className="text-xs text-warm-text-secondary">
              · {VISIT_TYPE_LABELS[row.visit_type] ?? row.visit_type}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-warm-text-secondary">
            <Clock className="inline h-3 w-3 mr-0.5" />
            {formatDateTime(row.visit_date)}
          </p>
          <p className="text-xs text-warm-text-secondary">{LABEL_VET}: {row.veterinarian_name}</p>
          {row.reason && (
            <p className="mt-0.5 text-xs text-warm-text-tertiary italic line-clamp-1">
              {row.reason}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 pl-11 sm:pl-0 sm:flex-shrink-0">
        <button
          onClick={() => onViewAnimal(row.animal_id)}
          className="rounded-lg border border-warm-border px-2.5 py-1 text-xs text-warm-text-secondary transition-colors hover:bg-warm-surface whitespace-nowrap"
        >
          <PawPrint className="inline h-3 w-3 mr-0.5" />
          {LABEL_VIEW_ANIMAL}
        </button>
      </div>
    </div>
  );
}

interface NewAppointmentFormProps {
  onClose: () => void;
  onCreated: () => void;
}

function NewAppointmentForm({ onClose, onCreated }: NewAppointmentFormProps) {
  const [animalId, setAnimalId] = useState("");
  const [vetName, setVetName] = useState("");
  const [visitDate, setVisitDate] = useState("");
  const [visitType, setVisitType] = useState<VisitType>("checkup");
  const [reason, setReason] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!animalId || !vetName || !visitDate) return;

    setIsSaving(true);
    setFormError(null);
    try {
      await api.post("/appointments", {
        animal_id: animalId,
        veterinarian_name: vetName,
        visit_date: new Date(visitDate).toISOString(),
        visit_type: visitType,
        reason: reason || null,
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setFormError(err.detail ?? "Error al guardar la cita");
      } else {
        setFormError("Error al guardar la cita");
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-blue-900">{LABEL_NEW_APPOINTMENT}</h2>
        <button onClick={onClose} className="text-blue-600 hover:text-blue-800">
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-blue-800">
            {LABEL_FORM_ANIMAL_ID} *
          </label>
          <input
            type="text"
            value={animalId}
            onChange={(e) => setAnimalId(e.target.value)}
            placeholder="UUID del animal"
            required
            className="w-full rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-sm text-warm-text-primary focus:border-blue-400 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-blue-800">
            {LABEL_FORM_VET} *
          </label>
          <input
            type="text"
            value={vetName}
            onChange={(e) => setVetName(e.target.value)}
            placeholder="Dr. Garcia"
            required
            className="w-full rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-sm text-warm-text-primary focus:border-blue-400 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-blue-800">
            {LABEL_FORM_DATE} *
          </label>
          <input
            type="datetime-local"
            value={visitDate}
            onChange={(e) => setVisitDate(e.target.value)}
            required
            className="w-full rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-sm text-warm-text-primary focus:border-blue-400 focus:outline-none"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-blue-800">
            {LABEL_FORM_TYPE}
          </label>
          <select
            value={visitType}
            onChange={(e) => setVisitType(e.target.value as VisitType)}
            className="w-full rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-sm text-warm-text-primary focus:border-blue-400 focus:outline-none"
          >
            {VISIT_TYPES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className="mb-1 block text-xs font-medium text-blue-800">
            {LABEL_FORM_REASON}
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Motivo de la consulta"
            className="w-full rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-sm text-warm-text-primary focus:border-blue-400 focus:outline-none"
          />
        </div>

        {formError && (
          <div className="sm:col-span-2">
            <p className="text-xs text-red-700">{formError}</p>
          </div>
        )}

        <div className="flex gap-2 sm:col-span-2">
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isSaving ? LABEL_SAVING : LABEL_SAVE}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-warm-border px-4 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-surface"
          >
            {LABEL_CANCEL}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function AppointmentsPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [items, setItems] = useState<AppointmentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includePast, setIncludePast] = useState(false);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchAppointments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: "1",
        page_size: "50",
        include_past: includePast ? "true" : "false",
      });
      const data = await api.get<AppointmentListResponse>(
        `/appointments?${params.toString()}`
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
  }, [includePast]);

  useEffect(() => {
    if (!isChecking) {
      fetchAppointments();
    }
  }, [isChecking, fetchAppointments]);

  function handleViewAnimal(animalId: string) {
    router.push(`/admin/animals/${animalId}?tab=medical`);
  }

  function handleCreated() {
    setShowForm(false);
    fetchAppointments();
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
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
            <Calendar className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">{LABEL_PAGE_TITLE}</h1>
            <p className="text-xs text-warm-text-tertiary">{LABEL_SUBTITLE}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAppointments}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
          >
            <Plus className="h-4 w-4" />
            {LABEL_NEW_APPOINTMENT}
          </button>
        </div>
      </div>

      {/* New appointment form */}
      {showForm && (
        <NewAppointmentForm onClose={() => setShowForm(false)} onCreated={handleCreated} />
      )}

      {/* Filters */}
      <div className="mb-4 flex items-center gap-3">
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={includePast}
            onChange={(e) => setIncludePast(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-warm-border"
          />
          <span className="text-sm text-warm-text-secondary">{LABEL_INCLUDE_PAST}</span>
        </label>
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
            onClick={fetchAppointments}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Appointment list */}
      {!isLoading && !error && (
        <>
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-warm-border bg-warm-surface py-16 text-center">
              <Calendar className="mb-3 h-10 w-10 text-warm-text-tertiary" />
              <p className="text-sm text-warm-text-secondary">{LABEL_EMPTY}</p>
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((row) => (
                <AppointmentItem
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
