"use client";

/**
 * Root error boundary — catches unhandled errors in the entire application.
 *
 * This component is rendered by Next.js when a child component throws an
 * unexpected error. It gives the user a clear message and a way to recover
 * without needing a full page reload.
 *
 * @see https://nextjs.org/docs/app/building-your-application/routing/error-handling
 */
import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to the browser console in development; Sentry will capture it in production.
    console.error("Unhandled application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="max-w-md space-y-4">
        <h2 className="text-2xl font-semibold text-gray-800">
          Algo salió mal
        </h2>
        <p className="text-gray-500">
          Ha ocurrido un error inesperado. Por favor, intente de nuevo.
        </p>
        {process.env.NODE_ENV === "development" && error.message && (
          <pre className="mt-2 max-h-32 overflow-auto rounded bg-red-50 p-3 text-left text-xs text-red-700">
            {error.message}
          </pre>
        )}
        <button
          onClick={reset}
          className="mt-4 rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
        >
          Intentar de nuevo
        </button>
      </div>
    </div>
  );
}
