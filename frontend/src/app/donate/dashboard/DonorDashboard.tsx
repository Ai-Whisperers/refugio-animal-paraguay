"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  CreditCard,
  Calendar,
  TrendingUp,
  Heart,
  ExternalLink,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { DONOR_DASHBOARD } from "@/lib/strings";
import { getDonorSubscriptions } from "@/lib/public-api";
import type { SubscriptionDetailResponse } from "@/types/api";

type DashboardView = "lookup" | "dashboard" | "not_found";

function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    active: DONOR_DASHBOARD.statusActive,
    paused: DONOR_DASHBOARD.statusPaused,
    canceled: DONOR_DASHBOARD.statusCanceled,
    past_due: DONOR_DASHBOARD.statusPastDue,
  };

  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    paused: "bg-yellow-100 text-yellow-800",
    canceled: "bg-gray-100 text-gray-600",
    past_due: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] ?? "bg-gray-100 text-gray-600"}`}
    >
      {labels[status] ?? status}
    </span>
  );
}

function formatCurrency(amountCents: number, currency: string): string {
  const amount = amountCents / 100;
  try {
    return new Intl.NumberFormat("es-PY", {
      style: "currency",
      currency: currency.toUpperCase(),
      minimumFractionDigits: currency.toUpperCase() === "PYG" ? 0 : 2,
    }).format(amount);
  } catch {
    return `${currency.toUpperCase()} ${amount.toFixed(2)}`;
  }
}

function formatDate(dateStr: string): string {
  try {
    return new Intl.DateTimeFormat("es-PY", {
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

export default function DonorDashboard() {
  const [view, setView] = useState<DashboardView>("lookup");
  const [donorId, setDonorId] = useState("");
  const [subscriptions, setSubscriptions] = useState<
    SubscriptionDetailResponse[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedId = donorId.trim();
    if (!trimmedId) return;

    setLoading(true);
    setError(null);

    try {
      const results = await getDonorSubscriptions(trimmedId);
      setSubscriptions(results);
      setView(results.length > 0 ? "dashboard" : "not_found");
    } catch (err) {
      if (err instanceof Error && "status" in err && (err as { status: number }).status === 404) {
        setView("not_found");
      } else {
        setError(
          err instanceof Error ? err.message : "Error al buscar suscripciones."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const activeSubscriptions = subscriptions.filter(
    (s) => s.status === "active" || s.status === "past_due"
  );

  const totalMonthlyCents = activeSubscriptions
    .filter((s) => s.interval === "month")
    .reduce((sum, s) => sum + s.amount_cents, 0);

  const earliestCreated = subscriptions.length > 0
    ? subscriptions.reduce((earliest, s) =>
        s.created_at < earliest.created_at ? s : earliest
      ).created_at
    : null;

  // --- Lookup View ---
  if (view === "lookup") {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 bg-primary-100 rounded-lg">
            <Search className="h-5 w-5 text-primary-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">
            {DONOR_DASHBOARD.lookupTitle}
          </h2>
        </div>

        <form onSubmit={handleLookup} className="space-y-4">
          <div>
            <label
              htmlFor="donor-id"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              {DONOR_DASHBOARD.donorIdLabel}
            </label>
            <input
              id="donor-id"
              type="text"
              value={donorId}
              onChange={(e) => setDonorId(e.target.value)}
              placeholder="ej. d1a2b3c4-..."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
              required
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !donorId.trim()}
            className="w-full bg-primary-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Buscando...
              </>
            ) : (
              DONOR_DASHBOARD.searchButton
            )}
          </button>
        </form>
      </div>
    );
  }

  // --- Not Found View ---
  if (view === "not_found") {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 text-center">
        <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-full mx-auto mb-4">
          <AlertCircle className="h-6 w-6 text-gray-400" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          {DONOR_DASHBOARD.notFoundTitle}
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          {DONOR_DASHBOARD.notFoundMessage}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => {
              setView("lookup");
              setDonorId("");
              setError(null);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Intentar con otro ID
          </button>
          <Link
            href="/donate/monthly"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors text-center"
          >
            {DONOR_DASHBOARD.startDonating}
          </Link>
        </div>
      </div>
    );
  }

  // --- Dashboard View ---
  const primaryCurrency =
    activeSubscriptions.length > 0
      ? activeSubscriptions[0].currency
      : "EUR";

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <span className="text-sm text-gray-500">
              {DONOR_DASHBOARD.totalMonthly}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {formatCurrency(totalMonthlyCents, primaryCurrency)}
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="h-5 w-5 text-primary-600" />
            <span className="text-sm text-gray-500">
              {DONOR_DASHBOARD.subscriptionCount}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {activeSubscriptions.length}
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="h-5 w-5 text-blue-600" />
            <span className="text-sm text-gray-500">
              {DONOR_DASHBOARD.memberSince}
            </span>
          </div>
          <p className="text-lg font-bold text-gray-900">
            {earliestCreated ? formatDate(earliestCreated) : "—"}
          </p>
        </div>
      </div>

      {/* Subscription List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
          <Heart className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            {DONOR_DASHBOARD.activeSubscriptions}
          </h2>
        </div>

        {subscriptions.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-gray-500">
              {DONOR_DASHBOARD.noSubscriptions}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {subscriptions.map((sub) => (
              <li key={sub.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-base font-semibold text-gray-900">
                        {formatCurrency(sub.amount_cents, sub.currency)}
                      </span>
                      <span className="text-sm text-gray-500">
                        {sub.interval === "month"
                          ? DONOR_DASHBOARD.perMonth
                          : DONOR_DASHBOARD.perYear}
                      </span>
                      <StatusBadge status={sub.status} />
                    </div>
                    {sub.current_period_end && (
                      <p className="text-xs text-gray-400">
                        Proximo cobro: {formatDate(sub.current_period_end)}
                      </p>
                    )}
                    {sub.cancel_at_period_end && (
                      <p className="text-xs text-yellow-600">
                        Se cancelara al final del periodo actual
                      </p>
                    )}
                  </div>
                  <Link
                    href={`/donate/manage?id=${sub.id}`}
                    className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {DONOR_DASHBOARD.manageLink}
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Back to Lookup */}
      <div className="text-center">
        <button
          onClick={() => {
            setView("lookup");
            setDonorId("");
            setSubscriptions([]);
            setError(null);
          }}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          Buscar otro donante
        </button>
      </div>
    </div>
  );
}
