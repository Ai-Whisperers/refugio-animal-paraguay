"use client";

import { useState } from "react";
import { CheckCircle, XCircle, X, AlertTriangle } from "lucide-react";
import type { AdoptionRequestStatus } from "@/types/api";

// --- Spanish labels ---
const LABEL_APPROVE_TITLE = "Aprobar Solicitud";
const LABEL_REJECT_TITLE = "Rechazar Solicitud";
const LABEL_APPROVE_DESCRIPTION = "Al aprobar, el estado del animal cambiara a 'adoptado'.";
const LABEL_REJECT_DESCRIPTION = "El adoptante sera notificado del rechazo.";
const LABEL_NOTES_LABEL = "Notas (obligatorio)";
const LABEL_NOTES_PLACEHOLDER_APPROVE = "Motivo de aprobacion, condiciones especiales, etc.";
const LABEL_NOTES_PLACEHOLDER_REJECT = "Motivo del rechazo...";
const LABEL_CONFIRM_APPROVE = "Confirmar Aprobacion";
const LABEL_CONFIRM_REJECT = "Confirmar Rechazo";
const LABEL_CANCEL = "Cancelar";
const LABEL_NOTES_REQUIRED = "Las notas son obligatorias para registrar la decision.";
const LABEL_PROCESSING = "Procesando...";
const LABEL_MIN_LENGTH = "Minimo 10 caracteres";

const MIN_NOTES_LENGTH = 10;

interface AdoptionStatusModalProps {
  action: "approved" | "rejected";
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (status: AdoptionRequestStatus, notes: string) => Promise<void>;
}

export default function AdoptionStatusModal({
  action,
  isOpen,
  onClose,
  onConfirm,
}: AdoptionStatusModalProps) {
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isApprove = action === "approved";
  const title = isApprove ? LABEL_APPROVE_TITLE : LABEL_REJECT_TITLE;
  const description = isApprove ? LABEL_APPROVE_DESCRIPTION : LABEL_REJECT_DESCRIPTION;
  const placeholder = isApprove ? LABEL_NOTES_PLACEHOLDER_APPROVE : LABEL_NOTES_PLACEHOLDER_REJECT;
  const confirmLabel = isApprove ? LABEL_CONFIRM_APPROVE : LABEL_CONFIRM_REJECT;
  const confirmColor = isApprove
    ? "bg-green-600 hover:bg-green-700 focus:ring-green-500"
    : "bg-red-600 hover:bg-red-700 focus:ring-red-500";
  const Icon = isApprove ? CheckCircle : XCircle;

  const isValid = notes.trim().length >= MIN_NOTES_LENGTH;

  async function handleSubmit() {
    if (!isValid) {
      setError(LABEL_MIN_LENGTH);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onConfirm(action, notes.trim());
      setNotes("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar la solicitud");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleClose() {
    if (!isSubmitting) {
      setNotes("");
      setError(null);
      onClose();
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative z-10 mx-4 w-full max-w-md rounded-lg bg-warm-surface shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-warm-border p-4">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${isApprove ? "text-green-600" : "text-red-600"}`} />
            <h2 className="text-lg font-semibold text-warm-text-primary">{title}</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="rounded-lg p-1 text-warm-text-secondary hover:bg-warm-bg"
            aria-label={LABEL_CANCEL}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          <div className={`flex items-start gap-2 rounded-lg p-3 text-sm ${
            isApprove ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
          }`}>
            <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p>{description}</p>
          </div>

          <div>
            <label
              htmlFor="decision-notes"
              className="block text-sm font-medium text-warm-text-primary mb-1"
            >
              {LABEL_NOTES_LABEL}
            </label>
            <textarea
              id="decision-notes"
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value);
                setError(null);
              }}
              placeholder={placeholder}
              rows={4}
              disabled={isSubmitting}
              className="w-full rounded-lg border border-warm-border bg-warm-bg px-3 py-2 text-sm text-warm-text-primary placeholder-warm-text-secondary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:opacity-50"
            />
            <p className="mt-1 text-xs text-warm-text-secondary">
              {LABEL_NOTES_REQUIRED} {LABEL_MIN_LENGTH}.
            </p>
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-warm-border p-4">
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="rounded-lg px-4 py-2 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
          >
            {LABEL_CANCEL}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !isValid}
            className={`rounded-lg px-4 py-2 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 ${confirmColor}`}
          >
            {isSubmitting ? LABEL_PROCESSING : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
