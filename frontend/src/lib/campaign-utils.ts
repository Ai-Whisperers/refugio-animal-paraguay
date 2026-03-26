/**
 * Utility functions for campaign display formatting.
 */

import type { CurrencyCode, FundCategory } from "@/types/api";

/** Format amount in cents to a human-readable currency string. */
export function formatCurrency(amountCents: number, currency: CurrencyCode): string {
  const amount = amountCents / 100;

  const formatters: Record<CurrencyCode, () => string> = {
    EUR: () =>
      new Intl.NumberFormat("es-PY", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount),
    USD: () =>
      new Intl.NumberFormat("es-PY", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amount),
    PYG: () =>
      new Intl.NumberFormat("es-PY", {
        style: "currency",
        currency: "PYG",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(amountCents), // PYG has no fractional unit
  };

  return formatters[currency]();
}

/** Get icon name for fund category (maps to lucide-react icons). */
export function getCategoryIcon(category: FundCategory): string {
  const icons: Record<FundCategory, string> = {
    medical: "stethoscope",
    food: "utensils",
    operations: "truck",
    rescue: "siren",
    infrastructure: "wrench",
    general: "heart",
  };
  return icons[category] ?? "heart";
}

/** Get Spanish label for fund category. */
export function getCategoryLabel(category: FundCategory): string {
  const labels: Record<FundCategory, string> = {
    medical: "Salud y Veterinaria",
    food: "Alimentacion",
    operations: "Operaciones",
    rescue: "Rescate",
    infrastructure: "Infraestructura",
    general: "General",
  };
  return labels[category] ?? "General";
}

/** Suggested donation amounts in cents for each currency. */
export function getSuggestedAmounts(currency: CurrencyCode): number[] {
  const amounts: Record<CurrencyCode, number[]> = {
    EUR: [500, 1000, 2500, 5000],
    USD: [500, 1000, 2500, 5000],
    PYG: [50000, 100000, 250000, 500000],
  };
  return amounts[currency];
}
