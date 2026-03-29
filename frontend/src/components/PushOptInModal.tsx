"use client";

import { useEffect, useRef } from "react";
import { Bell, X, Shield, Zap, Heart } from "lucide-react";

/**
 * PushOptInModal — explains push notifications before requesting permission.
 *
 * Shows a value-proposition dialog so users understand what they are
 * consenting to before the browser's native permission prompt appears.
 * Accessible: focus trap, ESC key dismiss, ARIA dialog role.
 */

interface PushOptInModalProps {
  /** Called when the user clicks "Activar" — the caller should then request permission */
  onConfirm: () => void;
  /** Called when the user dismisses without opting in */
  onDismiss: () => void;
}

const NOTIFICATION_EXAMPLES = [
  { icon: Heart, text: "Nuevas solicitudes de adopcion recibidas" },
  { icon: Zap, text: "Alertas de emergencia para animales en riesgo" },
  { icon: Bell, text: "Actualizaciones de donaciones y campanas" },
  { icon: Shield, text: "Cambios importantes en el estado del refugio" },
];

export default function PushOptInModal({ onConfirm, onDismiss }: PushOptInModalProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus the confirm button on mount
  useEffect(() => {
    confirmButtonRef.current?.focus();
  }, []);

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onDismiss();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onDismiss]);

  // Trap focus within the modal
  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;

    const focusableSelectors =
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusable = modal.querySelectorAll<HTMLElement>(focusableSelectors);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      if (event.shiftKey) {
        if (document.activeElement === first) {
          event.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    modal.addEventListener("keydown", trapFocus);
    return () => modal.removeEventListener("keydown", trapFocus);
  }, []);

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onDismiss();
      }}
    >
      {/* Dialog */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="push-opt-in-title"
        aria-describedby="push-opt-in-desc"
        className="relative w-full max-w-md rounded-2xl bg-white shadow-2xl"
      >
        {/* Close button */}
        <button
          onClick={onDismiss}
          className="absolute right-4 top-4 rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          aria-label="Cerrar"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="px-6 pt-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Bell className="h-8 w-8 text-primary" aria-hidden="true" />
          </div>
          <h2
            id="push-opt-in-title"
            className="text-xl font-bold text-gray-900"
          >
            Mantente informado/a
          </h2>
          <p
            id="push-opt-in-desc"
            className="mt-2 text-sm text-gray-500"
          >
            Activa las notificaciones para recibir alertas importantes del refugio directamente en tu dispositivo.
          </p>
        </div>

        {/* Notification examples */}
        <ul className="mt-5 space-y-3 px-6" aria-label="Ejemplos de notificaciones">
          {NOTIFICATION_EXAMPLES.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-center gap-3">
              <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
              </span>
              <span className="text-sm text-gray-700">{text}</span>
            </li>
          ))}
        </ul>

        {/* Privacy note */}
        <p className="mt-5 px-6 text-center text-xs text-gray-400">
          Puedes desactivar las notificaciones en cualquier momento desde la configuracion.
        </p>

        {/* Actions */}
        <div className="mt-6 flex flex-col gap-3 border-t border-gray-100 px-6 py-4">
          <button
            ref={confirmButtonRef}
            onClick={onConfirm}
            className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Activar notificaciones
          </button>
          <button
            onClick={onDismiss}
            className="w-full rounded-lg px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
          >
            Ahora no
          </button>
        </div>
      </div>
    </div>
  );
}
