"use client";

import { useState } from "react";
import { ArrowRight, X, AlertTriangle, RefreshCw, CheckCircle, XCircle } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import {
  VALID_TRANSITIONS,
  STATUS_LABELS,
  STATUS_COLORS,
  getCommonTransitions,
} from "@/lib/animal-status";
import type { AnimalStatus } from "@/types/api";

// --- Labels ---
const LABEL_TITLE = "Cambio de Estado en Lote";
const LABEL_SELECTED = "animales seleccionados";
const LABEL_SELECT_NEW = "Seleccionar nuevo estado";
const LABEL_NO_COMMON_TRANSITIONS = "Los animales seleccionados no comparten transiciones validas";
const LABEL_CONFIRM = "Confirmar cambio";
const LABEL_CANCEL = "Cancelar";
const LABEL_PROCESSING = "Procesando...";
const LABEL_CONFIRM_MESSAGE = "Cambiar el estado de";
const LABEL_TO = "a";
const LABEL_TERMINAL_WARNING = "Este es un estado terminal. No se podra revertir.";
const LABEL_RESULTS_TITLE = "Resultado del cambio en lote";
const LABEL_SUCCESS_COUNT = "exitosos";
const LABEL_FAILURE_COUNT = "fallidos";
const LABEL_CLOSE = "Cerrar";

interface BatchAnimal {
  id: string;
  name: string;
  status: AnimalStatus;
}

interface BatchResult {
  animalId: string;
  animalName: string;
  success: boolean;
  error?: string;
}

interface BatchStatusModalProps {
  animals: BatchAnimal[];
  onClose: () => void;
  onBatchCompleted: (updatedIds: string[], newStatus: AnimalStatus) => void;
}

export default function BatchStatusModal({
  animals,
  onClose,
  onBatchCompleted,
}: BatchStatusModalProps) {
  const [selectedStatus, setSelectedStatus] = useState<AnimalStatus | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<BatchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currentStatuses = [...new Set(animals.map((a) => a.status))];
  const commonTransitions = getCommonTransitions(currentStatuses);
  const isTerminalTarget = selectedStatus !== null && VALID_TRANSITIONS[selectedStatus]?.length === 0;

  async function handleConfirm() {
    if (!selectedStatus) return;
    setIsProcessing(true);
    setError(null);

    const batchResults: BatchResult[] = [];

    for (const animal of animals) {
      try {
        await api.patch(`/animals/${animal.id}`, { status: selectedStatus });
        batchResults.push({ animalId: animal.id, animalName: animal.name, success: true });
      } catch (err) {
        const errorMsg = err instanceof ApiClientError ? err.detail : "Error desconocido";
        batchResults.push({ animalId: animal.id, animalName: animal.name, success: false, error: errorMsg });
      }
    }

    setResults(batchResults);
    setIsProcessing(false);

    const successIds = batchResults
      .filter((r) => r.success)
      .map((r) => r.animalId);

    if (successIds.length > 0) {
      onBatchCompleted(successIds, selectedStatus);
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

  const successCount = results?.filter((r) => r.success).length ?? 0;
  const failureCount = results?.filter((r) => !r.success).length ?? 0;

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
      <div className="mx-4 w-full max-w-lg rounded-xl border border-warm-border bg-warm-surface shadow-lg">
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
          {/* Selected count */}
          <p className="mb-4 text-sm text-warm-text-secondary">
            <strong className="text-warm-text-primary">{animals.length}</strong>{" "}
            {LABEL_SELECTED}
          </p>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Results view */}
          {results !== null ? (
            <div>
              <h3 className="mb-3 text-sm font-medium text-warm-text-primary">
                {LABEL_RESULTS_TITLE}
              </h3>
              <div className="mb-3 flex items-center gap-4">
                <span className="flex items-center gap-1 text-sm text-green-700">
                  <CheckCircle className="h-4 w-4" />
                  {successCount} {LABEL_SUCCESS_COUNT}
                </span>
                {failureCount > 0 && (
                  <span className="flex items-center gap-1 text-sm text-red-700">
                    <XCircle className="h-4 w-4" />
                    {failureCount} {LABEL_FAILURE_COUNT}
                  </span>
                )}
              </div>
              {failureCount > 0 && (
                <div className="max-h-40 space-y-1 overflow-y-auto">
                  {results
                    .filter((r) => !r.success)
                    .map((r) => (
                      <div
                        key={r.animalId}
                        className="rounded border border-red-100 bg-red-50 px-3 py-1.5 text-xs text-red-800"
                      >
                        <strong>{r.animalName}</strong>: {r.error}
                      </div>
                    ))}
                </div>
              )}
            </div>
          ) : !isConfirming ? (
            <>
              <p className="mb-3 text-xs font-medium uppercase tracking-wide text-warm-text-tertiary">
                {commonTransitions.length > 0 ? LABEL_SELECT_NEW : LABEL_NO_COMMON_TRANSITIONS}
              </p>

              {commonTransitions.length > 0 && (
                <div className="space-y-2">
                  {commonTransitions.map((status) => (
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
                  <p className="text-sm text-orange-800">{LABEL_TERMINAL_WARNING}</p>
                </div>
              )}

              <p className="mb-4 text-sm text-warm-text-secondary">
                {LABEL_CONFIRM_MESSAGE}{" "}
                <strong className="text-warm-text-primary">{animals.length} animales</strong>{" "}
                {LABEL_TO}{" "}
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[selectedStatus!]}`}
                >
                  {STATUS_LABELS[selectedStatus!]}
                </span>
                ?
              </p>

              {/* Animal names list */}
              <div className="mb-4 max-h-32 overflow-y-auto rounded-lg bg-warm-bg p-3">
                <ul className="space-y-1 text-sm text-warm-text-secondary">
                  {animals.map((animal) => (
                    <li key={animal.id} className="flex items-center justify-between">
                      <span>{animal.name}</span>
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs ${STATUS_COLORS[animal.status]}`}
                      >
                        {STATUS_LABELS[animal.status]}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-warm-border px-5 py-3">
          {results !== null ? (
            <button
              onClick={onClose}
              className="rounded-lg bg-primary-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
            >
              {LABEL_CLOSE}
            </button>
          ) : isConfirming ? (
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
                {isProcessing && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
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
