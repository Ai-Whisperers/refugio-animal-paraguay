"use client";

import { useState } from "react";
import { ArrowRight, X, AlertTriangle, RefreshCw } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import type { AnimalStatus } from "@/types/api";

// --- Valid status transitions (mirrors backend src/services/animal_status.py) ---
const VALID_TRANSITIONS: Record<AnimalStatus, AnimalStatus[]> = {
  intake: ["quarantine", "available", "under_treatment"],
  quarantine: ["available", "under_treatment", "deceased"],
  available: ["foster", "adopted", "under_treatment", "quarantine", "deceased"],
  foster: ["available", "adopted", "under_treatment", "deceased"],
  under_treatment: ["available", "quarantine", "foster", "deceased"],
  adopted: ["available"],
  deceased: [],
};

// --- Status labels (Spanish) ---
const STATUS_LABELS: Record<AnimalStatus, string> = {
  intake: "Ingreso",
  quarantine: "Cuarentena",
  available: "Disponible",
  foster: "Acogida",
  under_treatment: "En tratamiento",
  adopted: "Adoptado",
  deceased: "Fallecido",
};

const STATUS_COLORS: Record<AnimalStatus, string> = {
  intake: "bg-yellow-100 text-yellow-800 border-yellow-300",
  quarantine: "bg-orange-100 text-orange-800 border-orange-300",
  available: "bg-green-100 text-green-800 border-green-300",
  foster: "bg-blue-100 text-blue-800 border-blue-300",
  under_treatment: "bg-red-100 text-red-800 border-red-300",
  adopted: "bg-purple-100 text-purple-800 border-purple-300",
  deceased: "bg-gray-100 text-gray-500 border-gray-300",
};

// --- Labels ---
const LABEL_TITLE = "Cambiar Estado";
const LABEL_CURRENT = "Estado actual";
const LABEL_SELECT_NEW = "Seleccionar nuevo estado";
const LABEL_NO_TRANSITIONS = "No hay transiciones disponibles desde este estado";
const LABEL_CONFIRM = "Confirmar cambio";
const LABEL_CANCEL = "Cancelar";
const LABEL_SAVING = "Guardando...";
const LABEL_CONFIRM_MESSAGE = "Estas seguro de cambiar el estado de";
const LABEL_TO = "a";
const LABEL_TERMINAL_WARNING = "Este es un estado terminal. No se podra revertir.";

interface StatusWorkflowModalProps {
  animalId: string;
  animalName: string;
  currentStatus: AnimalStatus;
  onClose: () => void;
  onStatusChanged: (newStatus: AnimalStatus) => void;
}

export default function StatusWorkflowModal({
  animalId,
  animalName,
  currentStatus,
  onClose,
  onStatusChanged,
}: StatusWorkflowModalProps) {
  const [selectedStatus, setSelectedStatus] = useState<AnimalStatus | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validNextStatuses = VALID_TRANSITIONS[currentStatus] ?? [];
  const isTerminalTarget = selectedStatus !== null && VALID_TRANSITIONS[selectedStatus]?.length === 0;

  async function handleConfirm() {
    if (!selectedStatus) return;
    setIsSaving(true);
    setError(null);

    try {
      await api.patch(`/animals/${animalId}`, { status: selectedStatus });
      onStatusChanged(selectedStatus);
      onClose();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError("Error al cambiar el estado");
      }
    } finally {
      setIsSaving(false);
    }
  }

  function handleSelectStatus(status: AnimalStatus) {
    setSelectedStatus(status);
    setIsConfirming(true);
    setError(null);
  }

  function handleBack() {
    setSelectedStatus(null);
    setIsConfirming(false);
    setError(null);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={LABEL_TITLE}
    >
      <div className="mx-4 w-full max-w-md rounded-xl border border-warm-border bg-warm-surface shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-warm-border px-5 py-4">
          <h2 className="text-base font-semibold text-warm-text-primary">
            {LABEL_TITLE}: {animalName}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-warm-text-tertiary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_CANCEL}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {/* Current status */}
          <div className="mb-4">
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
              {LABEL_CURRENT}
            </p>
            <span
              className={`inline-flex rounded-full border px-3 py-1 text-sm font-medium ${STATUS_COLORS[currentStatus]}`}
            >
              {STATUS_LABELS[currentStatus]}
            </span>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Status selection or confirmation */}
          {!isConfirming ? (
            <>
              <p className="mb-3 text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                {validNextStatuses.length > 0 ? LABEL_SELECT_NEW : LABEL_NO_TRANSITIONS}
              </p>

              {validNextStatuses.length > 0 && (
                <div className="space-y-2">
                  {validNextStatuses.map((status) => (
                    <button
                      key={status}
                      onClick={() => handleSelectStatus(status)}
                      className="flex w-full items-center justify-between rounded-lg border border-warm-border px-4 py-3 text-left transition-colors hover:bg-warm-bg"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[currentStatus]}`}
                        >
                          {STATUS_LABELS[currentStatus]}
                        </span>
                        <ArrowRight className="h-4 w-4 text-warm-text-tertiary" />
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
                        >
                          {STATUS_LABELS[status]}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div>
              {/* Terminal state warning */}
              {isTerminalTarget && (
                <div className="mb-4 flex items-start gap-2 rounded-lg border border-orange-200 bg-orange-50 p-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-600" />
                  <p className="text-sm text-orange-800">{LABEL_TERMINAL_WARNING}</p>
                </div>
              )}

              <p className="mb-4 text-sm text-warm-text-secondary">
                {LABEL_CONFIRM_MESSAGE}{" "}
                <strong className="text-warm-text-primary">{animalName}</strong>{" "}
                {LABEL_TO}{" "}
                <span
                  className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[selectedStatus!]}`}
                >
                  {STATUS_LABELS[selectedStatus!]}
                </span>
                ?
              </p>

              {/* Transition visual */}
              <div className="mb-4 flex items-center justify-center gap-3 rounded-lg bg-warm-bg p-4">
                <span
                  className={`inline-flex rounded-full border px-3 py-1 text-sm font-medium ${STATUS_COLORS[currentStatus]}`}
                >
                  {STATUS_LABELS[currentStatus]}
                </span>
                <ArrowRight className="h-5 w-5 text-warm-text-tertiary" />
                <span
                  className={`inline-flex rounded-full border px-3 py-1 text-sm font-medium ${STATUS_COLORS[selectedStatus!]}`}
                >
                  {STATUS_LABELS[selectedStatus!]}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-warm-border px-5 py-3">
          {isConfirming ? (
            <>
              <button
                onClick={handleBack}
                disabled={isSaving}
                className="rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:opacity-50"
              >
                {LABEL_CANCEL}
              </button>
              <button
                onClick={handleConfirm}
                disabled={isSaving}
                className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
              >
                {isSaving && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                {isSaving ? LABEL_SAVING : LABEL_CONFIRM}
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
            >
              {LABEL_CANCEL}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Export for reuse in other components
export { VALID_TRANSITIONS, STATUS_LABELS, STATUS_COLORS };
