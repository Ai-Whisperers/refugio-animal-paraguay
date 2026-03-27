"use client";

/**
 * Admin segment error boundary.
 */
import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AdminError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Admin page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
      <div className="max-w-sm space-y-3">
        <h2 className="text-xl font-semibold text-gray-800">
          Error en el panel de administración
        </h2>
        <p className="text-gray-500 text-sm">
          Ha ocurrido un error inesperado. Por favor, recargue la página o intente de nuevo.
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
