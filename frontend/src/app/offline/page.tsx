"use client";

import { WifiOff } from "lucide-react";

export default function OfflinePage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <WifiOff className="h-16 w-16 text-warm-text-secondary opacity-40" />
      <h1 className="mt-6 text-2xl font-bold text-warm-text-primary">
        Sin conexion a internet
      </h1>
      <p className="mt-3 max-w-md text-warm-text-secondary">
        No pudimos cargar esta pagina. Verifica tu conexion a internet e intenta de nuevo.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="mt-6 rounded-lg bg-primary-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-700"
      >
        Reintentar
      </button>
    </div>
  );
}
