"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";

// -- Types -------------------------------------------------------------------

interface EmergencyItem {
  id: string;
  title: string;
  description: string;
  photos: string[];
  amount_needed_cents: number;
  amount_raised_cents: number;
  currency: string;
  deadline: string;
  status: string;
  urgency: string;
  progress_pct: number;
}

interface EmergencyListResponse {
  items: EmergencyItem[];
  total: number;
}

// -- Constants ---------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DISMISS_KEY = "emergency_banner_dismissed";
const REFRESH_INTERVAL_MS = 60_000; // 1 minute

// -- Helpers -----------------------------------------------------------------

function formatTimeRemaining(deadline: string): string {
  const now = new Date();
  const end = new Date(deadline);
  const diffMs = end.getTime() - now.getTime();

  if (diffMs <= 0) return "Finalizado";

  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days} dia${days > 1 ? "s" : ""} restante${days > 1 ? "s" : ""}`;
  return `${hours} hora${hours > 1 ? "s" : ""} restante${hours > 1 ? "s" : ""}`;
}

function formatAmount(cents: number, currency: string): string {
  const amount = cents / 100;
  if (currency === "PYG") {
    return new Intl.NumberFormat("es-PY", { style: "currency", currency: "PYG", maximumFractionDigits: 0 }).format(amount);
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

// -- Component ---------------------------------------------------------------

export default function EmergencyBanner() {
  const [emergency, setEmergency] = useState<EmergencyItem | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchEmergency = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/public/emergencies/active?limit=1`);
      if (!res.ok) {
        setEmergency(null);
        return;
      }
      const data: EmergencyListResponse = await res.json();
      if (data.items.length > 0) {
        setEmergency(data.items[0]);
      } else {
        setEmergency(null);
      }
    } catch {
      setEmergency(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check if dismissed in session
    if (typeof window !== "undefined") {
      const dismissedVal = sessionStorage.getItem(DISMISS_KEY);
      if (dismissedVal === "true") {
        setDismissed(true);
        setLoading(false);
        return;
      }
    }

    fetchEmergency();

    const interval = setInterval(fetchEmergency, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchEmergency]);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
    if (typeof window !== "undefined") {
      sessionStorage.setItem(DISMISS_KEY, "true");
    }
  }, []);

  if (loading || dismissed || !emergency) return null;

  const progressPct = emergency.progress_pct;
  const timeLeft = formatTimeRemaining(emergency.deadline);
  const raised = formatAmount(emergency.amount_raised_cents, emergency.currency);
  const needed = formatAmount(emergency.amount_needed_cents, emergency.currency);

  return (
    <div
      className="relative bg-gradient-to-r from-red-600 to-orange-500 text-white shadow-lg"
      role="region"
      aria-label="Emergencia activa"
      aria-live="polite"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        {/* Pulsing indicator */}
        <div className="flex-shrink-0">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-white" />
          </span>
        </div>

        {/* Content */}
        <div className="flex min-w-0 flex-1 flex-col gap-1 sm:flex-row sm:items-center sm:gap-4">
          <div className="flex min-w-0 items-center gap-2">
            <AlertTriangle className="hidden h-5 w-5 flex-shrink-0 sm:block" />
            <span className="truncate text-sm font-bold sm:text-base">
              EMERGENCIA: {emergency.title}
            </span>
          </div>

          {/* Progress */}
          <div className="flex items-center gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <div className="h-2 w-20 overflow-hidden rounded-full bg-white/30">
                <div
                  className="h-full rounded-full bg-white transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <span className="whitespace-nowrap font-medium">
                {raised} / {needed}
              </span>
            </div>
            <span className="hidden whitespace-nowrap text-white/80 sm:inline">
              {timeLeft}
            </span>
          </div>

          {/* CTA */}
          <a
            href={`/emergencies/${emergency.id}/donate`}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md bg-white px-4 py-1.5 text-sm font-bold text-red-600 shadow-sm transition-colors hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white sm:ml-auto"
          >
            DONAR AHORA
          </a>
        </div>

        {/* Dismiss */}
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 rounded-full p-1 text-white/70 transition-colors hover:bg-white/20 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
          aria-label="Cerrar banner de emergencia"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
