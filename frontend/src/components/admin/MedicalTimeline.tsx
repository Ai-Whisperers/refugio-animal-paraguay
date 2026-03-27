"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Stethoscope,
  Syringe,
  Scissors,
  Pill,
  RefreshCw,
  AlertCircle,
  Plus,
  FileText,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import type {
  VetVisit,
  VetVisitListResponse,
  VaccinationRecord,
  VaccinationListResponse,
  DiagnosisRecord,
} from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_TITLE = "Historial Medico";
const LABEL_LOADING = "Cargando historial medico...";
const LABEL_ERROR = "Error al cargar el historial medico";
const LABEL_RETRY = "Reintentar";
const LABEL_EMPTY = "Sin registros medicos";
const LABEL_EMPTY_SUB = "Este animal no tiene registros medicos aun";
const LABEL_ADD_VISIT = "Agregar Consulta";
const LABEL_VET_VISIT = "Consulta veterinaria";
const LABEL_VACCINATION = "Vacunacion";
const LABEL_REASON = "Motivo";
const LABEL_VET = "Veterinario";
const LABEL_WEIGHT = "Peso";
const LABEL_TEMP = "Temperatura";
const LABEL_NOTES = "Notas";
const LABEL_DIAGNOSES = "Diagnosticos";
const LABEL_TREATMENTS = "Tratamientos";
const LABEL_MEDICATIONS = "Medicamentos";
const LABEL_SHOW_DETAILS = "Ver detalles";
const LABEL_HIDE_DETAILS = "Ocultar detalles";
const LABEL_VACCINE = "Vacuna";
const LABEL_DOSE = "Dosis";
const LABEL_ADMINISTERED_BY = "Aplicado por";
const LABEL_NEXT_DUE = "Proxima dosis";
const LABEL_SCHEDULED = "Programada para";
const LABEL_STATUS = "Estado";

// --- Status/type labels ---

const VISIT_TYPE_LABELS: Record<string, string> = {
  checkup: "Control",
  emergency: "Emergencia",
  surgery: "Cirugia",
  vaccination: "Vacunacion",
  follow_up: "Seguimiento",
  dental: "Dental",
  other: "Otro",
};

const VISIT_STATUS_LABELS: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  no_show: "No asistio",
};

const VISIT_STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  in_progress: "bg-yellow-100 text-yellow-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
  no_show: "bg-gray-100 text-gray-600",
};

const VACCINATION_STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  administered: "bg-green-100 text-green-800",
  overdue: "bg-red-100 text-red-800",
  skipped: "bg-gray-100 text-gray-600",
};

const SEVERITY_COLORS: Record<string, string> = {
  mild: "text-yellow-600",
  moderate: "text-orange-600",
  severe: "text-red-600",
  critical: "text-red-800 font-bold",
};

// --- Helper functions ---

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// --- Timeline event union type ---

type TimelineEventType = "vet_visit" | "vaccination";

interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  date: Date;
  data: VetVisit | VaccinationRecord;
}

function buildTimeline(
  vetVisits: VetVisit[],
  vaccinations: VaccinationRecord[]
): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  for (const visit of vetVisits) {
    events.push({
      id: visit.id,
      type: "vet_visit",
      date: new Date(visit.visit_date),
      data: visit,
    });
  }

  for (const vax of vaccinations) {
    const eventDate = vax.administered_date
      ? new Date(vax.administered_date)
      : new Date(vax.scheduled_date);
    events.push({
      id: vax.id,
      type: "vaccination",
      date: eventDate,
      data: vax,
    });
  }

  // Sort descending (most recent first)
  events.sort((a, b) => b.date.getTime() - a.date.getTime());
  return events;
}

// --- Diagnosis detail sub-component ---

function DiagnosisDetail({ diagnosis }: { diagnosis: DiagnosisRecord }) {
  return (
    <div className="rounded border border-warm-border bg-warm-bg p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-sm font-medium text-warm-text-primary">
            {diagnosis.condition}
          </span>
          {diagnosis.is_chronic && (
            <span className="ml-2 rounded-full bg-orange-100 px-1.5 py-0.5 text-xs text-orange-700">
              Cronico
            </span>
          )}
        </div>
        <span
          className={`text-xs ${SEVERITY_COLORS[diagnosis.severity] ?? "text-warm-text-tertiary"}`}
        >
          {diagnosis.severity}
        </span>
      </div>
      {diagnosis.description && (
        <p className="mt-1 text-xs text-warm-text-secondary">
          {diagnosis.description}
        </p>
      )}
      {diagnosis.treatments.length > 0 && (
        <div className="mt-2 space-y-1">
          <p className="text-xs font-medium text-warm-text-tertiary">
            {LABEL_TREATMENTS}:
          </p>
          {diagnosis.treatments.map((treatment) => (
            <div key={treatment.id} className="ml-2">
              <span className="text-xs text-warm-text-secondary">
                {treatment.name}
              </span>
              {treatment.medications.length > 0 && (
                <div className="ml-2">
                  {treatment.medications.map((med) => (
                    <div key={med.id} className="flex items-center gap-1 text-xs text-warm-text-tertiary">
                      <Pill className="h-2.5 w-2.5" />
                      {med.name} — {med.dosage} ({med.frequency})
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Vet visit event ---

function VetVisitEvent({ visit }: { visit: VetVisit }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetails =
    !!visit.reason ||
    !!visit.notes ||
    !!visit.weight_kg ||
    !!visit.temperature_celsius ||
    visit.diagnoses.length > 0 ||
    visit.medical_documents.length > 0;

  return (
    <div className="flex-1 min-w-0">
      <div className="flex flex-wrap items-baseline justify-between gap-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-warm-text-primary">
            {VISIT_TYPE_LABELS[visit.visit_type] ?? visit.visit_type}
          </span>
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              VISIT_STATUS_COLORS[visit.visit_status] ?? "bg-gray-100 text-gray-600"
            }`}
          >
            {VISIT_STATUS_LABELS[visit.visit_status] ?? visit.visit_status}
          </span>
        </div>
        <time className="text-xs text-warm-text-tertiary">
          {formatDateTime(visit.visit_date)}
        </time>
      </div>

      <p className="mt-0.5 text-xs text-warm-text-secondary">
        {LABEL_VET}: {visit.veterinarian_name}
      </p>

      {visit.reason && (
        <p className="mt-0.5 text-xs text-warm-text-secondary">
          {LABEL_REASON}: {visit.reason}
        </p>
      )}

      {hasDetails && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-1 flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3 w-3" />
              {LABEL_HIDE_DETAILS}
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" />
              {LABEL_SHOW_DETAILS}
            </>
          )}
        </button>
      )}

      {expanded && (
        <div className="mt-2 space-y-2">
          {(visit.weight_kg || visit.temperature_celsius) && (
            <div className="flex gap-4 text-xs text-warm-text-secondary">
              {visit.weight_kg && (
                <span>
                  {LABEL_WEIGHT}: {visit.weight_kg} kg
                </span>
              )}
              {visit.temperature_celsius && (
                <span>
                  {LABEL_TEMP}: {visit.temperature_celsius} °C
                </span>
              )}
            </div>
          )}

          {visit.notes && (
            <p className="text-xs text-warm-text-secondary">
              {LABEL_NOTES}: {visit.notes}
            </p>
          )}

          {visit.diagnoses.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-warm-text-tertiary">
                {LABEL_DIAGNOSES}:
              </p>
              <div className="space-y-1">
                {visit.diagnoses.map((diagnosis) => (
                  <DiagnosisDetail key={diagnosis.id} diagnosis={diagnosis} />
                ))}
              </div>
            </div>
          )}

          {visit.medical_documents.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-warm-text-tertiary">
                Documentos:
              </p>
              <div className="space-y-1">
                {visit.medical_documents.map((doc) => (
                  <a
                    key={doc.id}
                    href={doc.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-primary-600 hover:underline"
                  >
                    <FileText className="h-3 w-3" />
                    {doc.title}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- Vaccination event ---

function VaccinationEvent({ vaccination }: { vaccination: VaccinationRecord }) {
  return (
    <div className="flex-1 min-w-0">
      <div className="flex flex-wrap items-baseline justify-between gap-1">
        <span className="text-sm font-medium text-warm-text-primary">
          {vaccination.vaccine_type?.name ?? LABEL_VACCINE}
        </span>
        <time className="text-xs text-warm-text-tertiary">
          {vaccination.administered_date
            ? formatDate(vaccination.administered_date)
            : formatDate(vaccination.scheduled_date)}
        </time>
      </div>

      <div className="mt-0.5 flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            VACCINATION_STATUS_COLORS[vaccination.vaccination_status] ??
            "bg-gray-100 text-gray-600"
          }`}
        >
          {vaccination.vaccination_status}
        </span>
        <span className="text-xs text-warm-text-tertiary">
          {LABEL_DOSE} {vaccination.dose_number}
        </span>
      </div>

      {vaccination.administered_by && (
        <p className="mt-0.5 text-xs text-warm-text-secondary">
          {LABEL_ADMINISTERED_BY}: {vaccination.administered_by}
        </p>
      )}

      {!vaccination.administered_date && (
        <p className="mt-0.5 text-xs text-warm-text-tertiary">
          {LABEL_SCHEDULED}: {formatDate(vaccination.scheduled_date)}
        </p>
      )}

      {vaccination.next_due_date && (
        <p className="mt-0.5 text-xs text-warm-text-secondary">
          {LABEL_NEXT_DUE}: {formatDate(vaccination.next_due_date)}
        </p>
      )}

      {vaccination.notes && (
        <p className="mt-0.5 text-xs text-warm-text-secondary">
          {LABEL_NOTES}: {vaccination.notes}
        </p>
      )}
    </div>
  );
}

// --- Event icon ---

function EventIcon({ type, visitType }: { type: TimelineEventType; visitType?: string }) {
  if (type === "vaccination") {
    return <Syringe className="h-4 w-4 text-green-600" />;
  }
  if (visitType === "surgery") {
    return <Scissors className="h-4 w-4 text-red-600" />;
  }
  return <Stethoscope className="h-4 w-4 text-primary-600" />;
}

// --- Props ---

interface MedicalTimelineProps {
  animalId: string;
  onAddVisit?: () => void;
}

// --- Main component ---

export default function MedicalTimeline({
  animalId,
  onAddVisit,
}: MedicalTimelineProps) {
  const [vetVisits, setVetVisits] = useState<VetVisit[]>([]);
  const [vaccinations, setVaccinations] = useState<VaccinationRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMedicalData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [visitsData, vaxData] = await Promise.all([
        api.get<VetVisitListResponse>(
          `/animals/${animalId}/vet-visits?page_size=100`
        ),
        api.get<VaccinationListResponse>(
          `/animals/${animalId}/vaccinations?page_size=100`
        ),
      ]);
      setVetVisits(visitsData.items);
      setVaccinations(vaxData.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [animalId]);

  useEffect(() => {
    fetchMedicalData();
  }, [fetchMedicalData]);

  const timeline = buildTimeline(vetVisits, vaccinations);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
          <Stethoscope className="h-5 w-5 text-primary-500" />
          {LABEL_TITLE}
        </h2>
        <div className="flex items-center justify-center py-6">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin text-primary-400" />
          <p className="text-sm text-warm-text-tertiary">{LABEL_LOADING}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-warm-text-primary">
          <Stethoscope className="h-5 w-5 text-primary-500" />
          {LABEL_TITLE}
        </h2>
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchMedicalData}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-base font-semibold text-warm-text-primary">
          <Stethoscope className="h-5 w-5 text-primary-500" />
          {LABEL_TITLE}
        </h2>
        {onAddVisit && (
          <button
            onClick={onAddVisit}
            className="flex items-center gap-1.5 rounded-lg bg-primary-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-600"
          >
            <Plus className="h-3.5 w-3.5" />
            {LABEL_ADD_VISIT}
          </button>
        )}
      </div>

      {timeline.length === 0 ? (
        <div className="flex flex-col items-center py-8">
          <Stethoscope className="mb-2 h-10 w-10 text-warm-border" />
          <p className="text-sm font-medium text-warm-text-secondary">
            {LABEL_EMPTY}
          </p>
          <p className="mt-1 text-xs text-warm-text-tertiary">
            {LABEL_EMPTY_SUB}
          </p>
          {onAddVisit && (
            <button
              onClick={onAddVisit}
              className="mt-4 flex items-center gap-1.5 rounded-lg border border-primary-300 px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50"
            >
              <Plus className="h-3.5 w-3.5" />
              {LABEL_ADD_VISIT}
            </button>
          )}
        </div>
      ) : (
        <div className="relative space-y-0">
          {/* Timeline vertical line */}
          <div className="absolute left-4 top-2 bottom-2 w-px bg-warm-border" />

          {timeline.map((event, index) => {
            const visit = event.type === "vet_visit" ? (event.data as VetVisit) : undefined;
            const vaccination =
              event.type === "vaccination"
                ? (event.data as VaccinationRecord)
                : undefined;

            return (
              <div key={event.id} className="relative flex gap-4 pb-5 last:pb-0">
                {/* Icon dot */}
                <div
                  className={`relative z-10 mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 ${
                    index === 0
                      ? "border-primary-400 bg-primary-50"
                      : "border-warm-border bg-warm-surface"
                  }`}
                >
                  <EventIcon
                    type={event.type}
                    visitType={visit?.visit_type}
                  />
                </div>

                {/* Content */}
                {visit && <VetVisitEvent visit={visit} />}
                {vaccination && <VaccinationEvent vaccination={vaccination} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
