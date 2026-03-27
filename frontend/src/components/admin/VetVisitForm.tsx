"use client";

import { useState } from "react";
import { X, Stethoscope, AlertCircle, Loader2 } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import type { VetVisit, VetVisitCreate, VisitType, VisitStatus } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_TITLE = "Nueva Consulta Veterinaria";
const LABEL_VET_NAME = "Nombre del veterinario";
const LABEL_VET_NAME_PLACEHOLDER = "Dr. Garcia";
const LABEL_VISIT_TYPE = "Tipo de consulta";
const LABEL_VISIT_STATUS = "Estado";
const LABEL_VISIT_DATE = "Fecha y hora";
const LABEL_REASON = "Motivo de la consulta";
const LABEL_REASON_PLACEHOLDER = "Descripcion del motivo...";
const LABEL_WEIGHT = "Peso (kg)";
const LABEL_WEIGHT_PLACEHOLDER = "Ej: 12.5";
const LABEL_TEMPERATURE = "Temperatura (°C)";
const LABEL_TEMPERATURE_PLACEHOLDER = "Ej: 38.5";
const LABEL_NOTES = "Notas";
const LABEL_NOTES_PLACEHOLDER = "Observaciones adicionales...";
const LABEL_NEXT_VISIT = "Proxima visita";
const LABEL_CANCEL = "Cancelar";
const LABEL_SAVE = "Guardar consulta";
const LABEL_SAVING = "Guardando...";
const LABEL_REQUIRED = "Este campo es obligatorio";

const VISIT_TYPE_OPTIONS: { value: VisitType; label: string }[] = [
  { value: "checkup", label: "Control" },
  { value: "emergency", label: "Emergencia" },
  { value: "surgery", label: "Cirugia" },
  { value: "vaccination", label: "Vacunacion" },
  { value: "follow_up", label: "Seguimiento" },
  { value: "dental", label: "Dental" },
  { value: "other", label: "Otro" },
];

const VISIT_STATUS_OPTIONS: { value: VisitStatus; label: string }[] = [
  { value: "scheduled", label: "Programada" },
  { value: "in_progress", label: "En curso" },
  { value: "completed", label: "Completada" },
  { value: "cancelled", label: "Cancelada" },
  { value: "no_show", label: "No asistio" },
];

interface VetVisitFormProps {
  animalId: string;
  animalName: string;
  onClose: () => void;
  onSaved: (visit: VetVisit) => void;
}

interface FormState {
  veterinarian_name: string;
  visit_type: VisitType;
  visit_status: VisitStatus;
  visit_date: string;
  reason: string;
  weight_kg: string;
  temperature_celsius: string;
  notes: string;
  next_visit_date: string;
}

function toISOLocalString(localDatetime: string): string {
  // localDatetime is like "2026-03-27T14:30" — append seconds and Z indicator
  // We'll keep it as local time string by appending :00
  return localDatetime.length === 16 ? `${localDatetime}:00` : localDatetime;
}

function nowLocalDatetimeString(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

export default function VetVisitForm({
  animalId,
  animalName,
  onClose,
  onSaved,
}: VetVisitFormProps) {
  const [form, setForm] = useState<FormState>({
    veterinarian_name: "",
    visit_type: "checkup",
    visit_status: "completed",
    visit_date: nowLocalDatetimeString(),
    reason: "",
    weight_kg: "",
    temperature_celsius: "",
    notes: "",
    next_visit_date: "",
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function validate(): boolean {
    const newErrors: Partial<Record<keyof FormState, string>> = {};
    if (!form.veterinarian_name.trim()) {
      newErrors.veterinarian_name = LABEL_REQUIRED;
    }
    if (!form.visit_date) {
      newErrors.visit_date = LABEL_REQUIRED;
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setIsSaving(true);
    setSubmitError(null);

    const payload: VetVisitCreate = {
      veterinarian_name: form.veterinarian_name.trim(),
      visit_type: form.visit_type,
      visit_status: form.visit_status,
      visit_date: toISOLocalString(form.visit_date),
      reason: form.reason.trim() || null,
      notes: form.notes.trim() || null,
      weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
      temperature_celsius: form.temperature_celsius
        ? parseFloat(form.temperature_celsius)
        : null,
      next_visit_date: form.next_visit_date || null,
    };

    try {
      const saved = await api.post<VetVisit>(
        `/animals/${animalId}/vet-visits`,
        payload
      );
      onSaved(saved);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError("Error al guardar la consulta");
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-warm-surface shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-warm-border px-6 py-4">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-primary-500" />
            <h2 className="text-base font-semibold text-warm-text-primary">
              {LABEL_TITLE}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-warm-text-tertiary">{animalName}</span>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-warm-text-secondary hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_CANCEL}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 overflow-y-auto max-h-[70vh] px-6 py-4">
          {submitError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3">
              <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-500" />
              <p className="text-sm text-red-800">{submitError}</p>
            </div>
          )}

          {/* Vet name */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
              {LABEL_VET_NAME} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.veterinarian_name}
              onChange={(e) => updateField("veterinarian_name", e.target.value)}
              placeholder={LABEL_VET_NAME_PLACEHOLDER}
              className={`w-full rounded-lg border px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-400 ${
                errors.veterinarian_name
                  ? "border-red-300 bg-red-50"
                  : "border-warm-border bg-warm-bg"
              }`}
            />
            {errors.veterinarian_name && (
              <p className="mt-1 text-xs text-red-600">{errors.veterinarian_name}</p>
            )}
          </div>

          {/* Visit type + status */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
                {LABEL_VISIT_TYPE}
              </label>
              <select
                value={form.visit_type}
                onChange={(e) => updateField("visit_type", e.target.value as VisitType)}
                className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
              >
                {VISIT_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
                {LABEL_VISIT_STATUS}
              </label>
              <select
                value={form.visit_status}
                onChange={(e) => updateField("visit_status", e.target.value as VisitStatus)}
                className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
              >
                {VISIT_STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Visit date */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
              {LABEL_VISIT_DATE} <span className="text-red-500">*</span>
            </label>
            <input
              type="datetime-local"
              value={form.visit_date}
              onChange={(e) => updateField("visit_date", e.target.value)}
              className={`w-full rounded-lg border px-3 py-2 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400 ${
                errors.visit_date
                  ? "border-red-300 bg-red-50"
                  : "border-warm-border bg-warm-bg"
              }`}
            />
            {errors.visit_date && (
              <p className="mt-1 text-xs text-red-600">{errors.visit_date}</p>
            )}
          </div>

          {/* Reason */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
              {LABEL_REASON}
            </label>
            <input
              type="text"
              value={form.reason}
              onChange={(e) => updateField("reason", e.target.value)}
              placeholder={LABEL_REASON_PLACEHOLDER}
              className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          {/* Weight + temperature */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
                {LABEL_WEIGHT}
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="9999.99"
                value={form.weight_kg}
                onChange={(e) => updateField("weight_kg", e.target.value)}
                placeholder={LABEL_WEIGHT_PLACEHOLDER}
                className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
                {LABEL_TEMPERATURE}
              </label>
              <input
                type="number"
                step="0.1"
                min="30"
                max="45"
                value={form.temperature_celsius}
                onChange={(e) => updateField("temperature_celsius", e.target.value)}
                placeholder={LABEL_TEMPERATURE_PLACEHOLDER}
                className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
              {LABEL_NOTES}
            </label>
            <textarea
              rows={3}
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              placeholder={LABEL_NOTES_PLACEHOLDER}
              className="w-full resize-none rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          {/* Next visit date */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-warm-text-primary">
              {LABEL_NEXT_VISIT}
            </label>
            <input
              type="date"
              value={form.next_visit_date}
              onChange={(e) => updateField("next_visit_date", e.target.value)}
              className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-warm-border px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="rounded-lg border border-warm-border px-4 py-2 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
          >
            {LABEL_CANCEL}
          </button>
          <button
            type="submit"
            form="vet-visit-form"
            onClick={handleSubmit}
            disabled={isSaving}
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSaving ? LABEL_SAVING : LABEL_SAVE}
          </button>
        </div>
      </div>
    </div>
  );
}
