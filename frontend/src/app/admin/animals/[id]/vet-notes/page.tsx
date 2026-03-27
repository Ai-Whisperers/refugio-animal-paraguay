"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  Save,
  Plus,
  ChevronDown,
  ChevronUp,
  Stethoscope,
  AlertCircle,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import RichTextEditor from "@/components/admin/RichTextEditor";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Notas Veterinarias";
const LABEL_LOADING = "Cargando visitas...";
const LABEL_ERROR = "Error al cargar visitas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al animal";
const LABEL_NEW_VISIT = "Nueva Visita";
const LABEL_SAVE = "Guardar Notas";
const LABEL_SAVING = "Guardando...";
const LABEL_SAVED = "Notas guardadas";
const LABEL_EMPTY = "Sin visitas registradas";
const LABEL_ADD_FIRST = "Agregar primera visita";
const LABEL_VISIT_TYPE = "Tipo de visita";
const LABEL_VET_NAME = "Veterinario";
const LABEL_VISIT_DATE = "Fecha";
const LABEL_NOTES_LABEL = "Notas";
const LABEL_REASON = "Motivo";
const LABEL_EXPAND = "Ver notas";
const LABEL_COLLAPSE = "Ocultar notas";
const LABEL_NEW_VISIT_TITLE = "Nueva Visita";
const LABEL_CANCEL = "Cancelar";
const LABEL_VET_NAME_PLACEHOLDER = "Nombre del veterinario";
const LABEL_REASON_PLACEHOLDER = "Motivo de la visita";
const LABEL_SAVE_ERROR = "Error al guardar notas";
const LABEL_CREATE_ERROR = "Error al crear visita";
const LABEL_CREATE_SUCCESS = "Visita creada";
const LABEL_VISIT_TYPE_CHECKUP = "Control";
const LABEL_VISIT_TYPE_VACCINATION = "Vacunacion";
const LABEL_VISIT_TYPE_TREATMENT = "Tratamiento";
const LABEL_VISIT_TYPE_SURGERY = "Cirugia";
const LABEL_VISIT_TYPE_EMERGENCY = "Emergencia";
const LABEL_VISIT_TYPE_FOLLOWUP = "Seguimiento";

// --- Types ---
interface VetVisitListItem {
  id: string;
  animal_id: string;
  veterinarian_name: string;
  visit_type: string;
  visit_status: string;
  visit_date: string;
  reason: string | null;
  notes: string | null;
  created_at: string;
}

interface VetVisitListResponse {
  items: VetVisitListItem[];
  total: number;
}

const VISIT_TYPE_LABELS: Record<string, string> = {
  checkup: LABEL_VISIT_TYPE_CHECKUP,
  vaccination: LABEL_VISIT_TYPE_VACCINATION,
  treatment: LABEL_VISIT_TYPE_TREATMENT,
  surgery: LABEL_VISIT_TYPE_SURGERY,
  emergency: LABEL_VISIT_TYPE_EMERGENCY,
  follow_up: LABEL_VISIT_TYPE_FOLLOWUP,
};

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-PY", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

// --- New visit form ---
interface NewVisitFormProps {
  animalId: string;
  onCreated: () => void;
  onCancel: () => void;
}

function NewVisitForm({ animalId, onCreated, onCancel }: NewVisitFormProps) {
  const [vetName, setVetName] = useState("");
  const [visitType, setVisitType] = useState("checkup");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!vetName.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.post(`/animals/${animalId}/vet-visits`, {
        veterinarian_name: vetName.trim(),
        visit_type: visitType,
        reason: reason.trim() || null,
        notes: notes || null,
        visit_date: new Date().toISOString(),
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_CREATE_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_CREATE_ERROR);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-primary-200 bg-primary-50 p-4 space-y-4">
      <h3 className="font-semibold text-primary-800">{LABEL_NEW_VISIT_TITLE}</h3>

      {error && (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="new-vet-name" className="block text-sm font-medium text-gray-700 mb-1">
            {LABEL_VET_NAME} <span className="text-red-500">*</span>
          </label>
          <input
            id="new-vet-name"
            type="text"
            value={vetName}
            onChange={(e) => setVetName(e.target.value)}
            placeholder={LABEL_VET_NAME_PLACEHOLDER}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>

        <div>
          <label htmlFor="new-visit-type" className="block text-sm font-medium text-gray-700 mb-1">
            {LABEL_VISIT_TYPE}
          </label>
          <select
            id="new-visit-type"
            value={visitType}
            onChange={(e) => setVisitType(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {Object.entries(VISIT_TYPE_LABELS).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="new-reason" className="block text-sm font-medium text-gray-700 mb-1">
          {LABEL_REASON}
        </label>
        <input
          id="new-reason"
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder={LABEL_REASON_PLACEHOLDER}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
      </div>

      <div>
        <label htmlFor="new-notes" className="block text-sm font-medium text-gray-700 mb-1">
          {LABEL_NOTES_LABEL}
        </label>
        <RichTextEditor
          id="new-notes"
          value={notes}
          onChange={setNotes}
          placeholder="Escriba las notas de la visita..."
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {LABEL_CANCEL}
        </button>
        <button
          type="submit"
          disabled={saving || !vetName.trim()}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          {saving ? (
            <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Save className="h-4 w-4" aria-hidden="true" />
          )}
          {saving ? LABEL_SAVING : LABEL_SAVE}
        </button>
      </div>
    </form>
  );
}

// --- Visit notes card ---
interface VisitNotesCardProps {
  visit: VetVisitListItem;
  onNotesUpdated: () => void;
}

function VisitNotesCard({ visit, onNotesUpdated }: VisitNotesCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState(visit.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  async function handleSaveNotes() {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await api.patch(`/animals/${visit.animal_id}/vet-visits/${visit.id}`, {
        notes: notes || null,
      });
      setSaveSuccess(true);
      onNotesUpdated();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setSaveError(`${LABEL_SAVE_ERROR}: ${err.detail}`);
      } else {
        setSaveError(LABEL_SAVE_ERROR);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      {/* Visit header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-gray-50">
        <Stethoscope className="h-4 w-4 text-primary-500 flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-800">{visit.veterinarian_name}</span>
            <span className="inline-flex rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700">
              {VISIT_TYPE_LABELS[visit.visit_type] ?? visit.visit_type}
            </span>
            <span className="text-xs text-gray-500">{formatDate(visit.visit_date)}</span>
          </div>
          {visit.reason && (
            <p className="mt-0.5 text-xs text-gray-500 truncate">{visit.reason}</p>
          )}
        </div>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-200"
          aria-expanded={expanded}
          aria-label={expanded ? LABEL_COLLAPSE : LABEL_EXPAND}
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4" aria-hidden="true" />
          ) : (
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          )}
          {expanded ? LABEL_COLLAPSE : LABEL_EXPAND}
        </button>
      </div>

      {/* Expanded notes editor */}
      {expanded && (
        <div className="px-4 py-4 space-y-3 border-t border-gray-100">
          <label className="block text-sm font-medium text-gray-700">
            {LABEL_NOTES_LABEL}
          </label>
          <RichTextEditor
            value={notes}
            onChange={setNotes}
          />

          {saveError && (
            <div className="flex items-center gap-2 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
              {saveError}
            </div>
          )}

          {saveSuccess && (
            <p className="text-sm text-green-600 font-medium">{LABEL_SAVED}</p>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleSaveNotes}
              disabled={saving}
              className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {saving ? (
                <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Save className="h-4 w-4" aria-hidden="true" />
              )}
              {saving ? LABEL_SAVING : LABEL_SAVE}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Main page ---
export default function VetNotesPage() {
  const router = useRouter();
  const params = useParams();
  const animalId = params.id as string;

  const [visits, setVisits] = useState<VetVisitListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewVisitForm, setShowNewVisitForm] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  const fetchVisits = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<VetVisitListResponse>(
        `/animals/${animalId}/vet-visits?limit=50`
      );
      setVisits(data.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${err.statusCode}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [animalId]);

  useEffect(() => {
    fetchVisits();
  }, [fetchVisits]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push(`/admin/animals/${animalId}`)}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-xl font-bold text-warm-text-primary">
            {LABEL_PAGE_TITLE}
          </h1>
        </div>
        <button
          onClick={() => setShowNewVisitForm(true)}
          disabled={showNewVisitForm}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          {LABEL_NEW_VISIT}
        </button>
      </div>

      {/* New visit form */}
      {showNewVisitForm && (
        <NewVisitForm
          animalId={animalId}
          onCreated={() => {
            setShowNewVisitForm(false);
            fetchVisits();
          }}
          onCancel={() => setShowNewVisitForm(false)}
        />
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16 text-warm-text-secondary">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />
          {LABEL_LOADING}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <AlertCircle className="mx-auto mb-2 h-8 w-8 text-red-500" aria-hidden="true" />
          <p className="mb-4 font-medium text-red-800">{error}</p>
          <button
            onClick={fetchVisits}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && visits.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <Stethoscope className="mx-auto mb-3 h-10 w-10 text-gray-300" aria-hidden="true" />
          <p className="mb-4 text-base text-gray-500">{LABEL_EMPTY}</p>
          <button
            onClick={() => setShowNewVisitForm(true)}
            className="flex items-center gap-2 mx-auto rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            {LABEL_ADD_FIRST}
          </button>
        </div>
      )}

      {/* Visit cards */}
      {!loading && !error && visits.length > 0 && (
        <div className="space-y-3">
          {visits.map((visit) => (
            <VisitNotesCard
              key={visit.id}
              visit={visit}
              onNotesUpdated={fetchVisits}
            />
          ))}
        </div>
      )}
    </div>
  );
}
