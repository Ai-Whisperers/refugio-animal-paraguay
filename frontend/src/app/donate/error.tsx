"use client";

/**
 * Donation segment error boundary.
 *
 * Critical path: donation failures must be surfaced clearly so donors
 * know their payment was NOT processed and can try again safely.
 */
import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DonateError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Donation page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
      <div className="max-w-sm space-y-3">
        <h2 className="text-xl font-semibold text-gray-800">
          Error en la página de donaciones
        </h2>
        <p className="text-gray-500 text-sm">
          Ha ocurrido un problema al cargar el formulario de donación.
          Su pago NO ha sido procesado. Por favor, intente de nuevo.
        </p>
        <button
          onClick={reset}
          className="mt-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          Intentar de nuevo
        </button>
      </div>
    </div>
  );
}
