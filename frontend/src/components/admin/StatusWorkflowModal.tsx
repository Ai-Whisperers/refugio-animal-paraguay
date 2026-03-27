"use client";

import { useState } from "react";
import { ArrowRight, X, AlertTriangle, RefreshCw } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import {
  VALID_TRANSITIONS,
  STATUS_LABELS,
  STATUS_COLORS,
} from "@/lib/animal-status";
import type { AnimalStatus } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_TITLE = "Cambiar Estado";
const LABEL_CURRENT = "Estado actual";
const LABEL_SELECT_NEW = "Seleccionar nuevo estado";
const LABEL_NO_TRANSITIONS = "No hay transiciones disponibles desde este estado";
const LABEL_CONFIRM = "Confirmar cambio";
const LABEL_CANCEL = "Cancelar";
const LABEL_PROCESSING = "Procesando...";
const LABEL_CONFIRM_MESSAGE = "Cambiar estado de";
const LABEL_TO = "a";
const LABEL_TERMINAL_WARNING =
  "Este es un estado terminal. No se podra revertir.";
const LABEL_ERROR = "Error al cambiar estado";

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
  const [selectedStatus, setSelectedStatus] = useState<AnimalStatus | null>(
    null
  );
  const [isConfirming, setIsConfirming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validTransitions = VALID_TRANSITIONS[currentStatus] ?? [];
  const isTerminalTarget =
    selectedStatus !== null &&
    VALID_TRANSITIONS[selectedStatus]?.length === 0;

  async function handleConfirm() {
    if (!selectedStatus) return;
    setIsProcessing(true);
    setError(null);

    try {
      await api.patch(`/animals/${animalId}`, { status: selectedStatus });
      onStatusChanged(selectedStatus);
    } catch (err) {
      const errorMsg =
        err instanceof ApiClientError ? err.detail : "Error desconocido";
      setError(`${LABEL_ERROR}: ${errorMsg}`);
      setIsProcessing(false);
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
        if (e.target === e.currentTarget && !isProcessing) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={LABEL_TITLE}
    >
      <div className="mx-4 w-full max-w-md rounded-xl border border-warm-border bg-warm-surface shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-warm-border px-5 py-4">
          <h2 className="text-base font-semibold text-warm-text-primary">
            {LABEL_TITLE}
          </h2>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="rounded-lg p-1 text-warm-text-tertiary transition-colors hover:bg-warm-bg hover:text-warm-text-primary disabled:opacity-50"
            aria-label={LABEL_CANCEL}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {/* Animal name and current status */}
          <div className="mb-4">
            <p className="text-sm font-medium text-warm-text-primary">
              {animalName}
            </p>
            <p className="mt-1 text-xs text-warm-text-tertiary">
              {LABEL_CURRENT}:{" "}
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[currentStatus]}`}
              >
                {STATUS_LABELS[currentStatus]}
              </span>
            </p>
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
                {validTransitions.length > 0
                  ? LABEL_SELECT_NEW
                  : LABEL_NO_TRANSITIONS}
              </p>

              {validTransitions.length > 0 && (
                <div className="space-y-2">
                  {validTransitions.map((status) => (
                    <button
                      key={status}
                      onClick={() => handleSelectStatus(status)}
                      className="flex w-full items-center gap-3 rounded-lg border border-warm-border px-4 py-3 text-left transition-colors hover:bg-warm-bg"
                    >
                      <ArrowRight className="h-4 w-4 text-warm-text-tertiary" />
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
                      >
                        {STATUS_LABELS[status]}
                      </span>
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
                  <p className="text-sm text-orange-800">
                    {LABEL_TERMINAL_WARNING}
                  </p>
                </div>
              )}

              <p className="text-sm text-warm-text-secondary">
                {LABEL_CONFIRM_MESSAGE}{" "}
                <strong className="text-warm-text-primary">{animalName}</strong>{" "}
                {LABEL_TO}{" "}
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[selectedStatus!]}`}
                >
                  {STATUS_LABELS[selectedStatus!]}
                </span>
                ?
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-warm-border px-5 py-3">
          {isConfirming ? (
            <>
              <button
                onClick={handleBack}
                disabled={isProcessing}
                className="rounded-lg border border-warm-border px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg disabled:opacity-50"
              >
                {LABEL_CANCEL}
              </button>
              <button
                onClick={handleConfirm}
                disabled={isProcessing}
                className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
              >
                {isProcessing && (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                )}
                {isProcessing ? LABEL_PROCESSING : LABEL_CONFIRM}
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
