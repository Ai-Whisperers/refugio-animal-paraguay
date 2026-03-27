"use client";

/**
 * Animals segment error boundary.
 *
 * Shown when the animals listing or detail page throws an error (e.g. API
 * unreachable, unexpected data shape). Isolated so other routes remain
 * unaffected.
 */
import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function AnimalsError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Animals page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
      <div className="max-w-sm space-y-3">
        <h2 className="text-xl font-semibold text-gray-800">
          No se pudieron cargar los animales
        </h2>
        <p className="text-gray-500 text-sm">
          Ha ocurrido un error al obtener la lista de animales. Por favor, intente de nuevo.
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
