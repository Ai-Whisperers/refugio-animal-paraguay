"use client";

import { useCallback, useEffect, useState } from "react";

import { getDonorLeaderboard } from "@/lib/public-api";
import type { CurrencyCode, LeaderboardEntry, LeaderboardResponse } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  title: "Tabla de Honor",
  subtitle: "Gracias a quienes hacen posible nuestra mision",
  totalRaised: "Total recaudado",
  totalDonors: "Donantes",
  rank: "#",
  donor: "Donante",
  country: "Pais",
  amount: "Total donado",
  donations: "Donaciones",
  loadMore: "Ver mas donantes",
  loading: "Cargando...",
  noDonors: "Aun no hay donaciones registradas.",
  currencyLabel: "Moneda",
  eurLabel: "EUR",
  pygLabel: "PYG",
  usdLabel: "USD",
} as const;

// ---------------------------------------------------------------------------
// Currency formatting
// ---------------------------------------------------------------------------

const CURRENCY_CONFIG: Record<string, { locale: string; symbol: string; decimals: number }> = {
  EUR: { locale: "de-DE", symbol: "\u20AC", decimals: 2 },
  PYG: { locale: "es-PY", symbol: "\u20B2", decimals: 0 },
  USD: { locale: "en-US", symbol: "$", decimals: 2 },
};

function formatCents(cents: number, currency: string): string {
  const config = CURRENCY_CONFIG[currency] ?? CURRENCY_CONFIG.EUR;
  const value = cents / (config.decimals === 0 ? 1 : 100);
  return new Intl.NumberFormat(config.locale, {
    style: "currency",
    currency,
    minimumFractionDigits: config.decimals,
    maximumFractionDigits: config.decimals,
  }).format(value);
}

// ---------------------------------------------------------------------------
// Rank badge
// ---------------------------------------------------------------------------

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full
                       bg-yellow-400 text-sm font-bold text-yellow-900 shadow-sm">
        1
      </span>
    );
  }
  if (rank === 2) {
    return (
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full
                       bg-gray-300 text-sm font-bold text-gray-700 shadow-sm">
        2
      </span>
    );
  }
  if (rank === 3) {
    return (
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full
                       bg-amber-600 text-sm font-bold text-white shadow-sm">
        3
      </span>
    );
  }
  return (
    <span className="inline-flex h-8 w-8 items-center justify-center text-sm
                     font-medium text-gray-500">
      {rank}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Country flag (emoji from ISO 3166-1 alpha-2)
// ---------------------------------------------------------------------------

function countryFlag(code: string | null): string {
  if (!code || code.length !== 2) return "";
  const offset = 0x1f1e6;
  const a = code.toUpperCase().charCodeAt(0) - 65 + offset;
  const b = code.toUpperCase().charCodeAt(1) - 65 + offset;
  return String.fromCodePoint(a, b);
}

// ---------------------------------------------------------------------------
// Leaderboard row
// ---------------------------------------------------------------------------

function LeaderboardRow({ entry, currency }: { entry: LeaderboardEntry; currency: string }) {
  return (
    <tr className="border-b border-gray-100 transition-colors hover:bg-emerald-50/50">
      <td className="py-3 pl-4 pr-2">
        <RankBadge rank={entry.rank} />
      </td>
      <td className="py-3 px-3">
        <div className="flex items-center gap-2">
          {entry.country && (
            <span className="text-lg" title={entry.country}>
              {countryFlag(entry.country)}
            </span>
          )}
          <span className="font-medium text-gray-900">{entry.display_name}</span>
        </div>
      </td>
      <td className="hidden py-3 px-3 text-sm text-gray-500 sm:table-cell">
        {entry.donation_count}
      </td>
      <td className="py-3 px-3 pr-4 text-right font-semibold text-emerald-700">
        {formatCents(entry.total_donated_cents, currency)}
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const PAGE_SIZE = 20;
const CURRENCIES: CurrencyCode[] = ["EUR", "PYG", "USD"];

export default function DonorLeaderboardPage() {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState<CurrencyCode>("EUR");
  const [offset, setOffset] = useState(0);

  const fetchLeaderboard = useCallback(
    async (curr: CurrencyCode, off: number, append: boolean) => {
      setLoading(true);
      try {
        const result = await getDonorLeaderboard(curr, PAGE_SIZE, off);
        setData(result);
        setEntries((prev) => (append ? [...prev, ...result.items] : result.items));
      } catch {
        // Keep existing data on error
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    setOffset(0);
    fetchLeaderboard(currency, 0, false);
  }, [currency, fetchLeaderboard]);

  const handleLoadMore = () => {
    const nextOffset = offset + PAGE_SIZE;
    setOffset(nextOffset);
    fetchLeaderboard(currency, nextOffset, true);
  };

  const hasMore = data ? entries.length < data.total_donors : false;

  return (
    <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">{S.title}</h1>
        <p className="mt-2 text-lg text-gray-600">{S.subtitle}</p>
      </div>

      {/* Stats cards */}
      {data && (
        <div className="mb-8 grid grid-cols-2 gap-4">
          <div className="rounded-xl bg-emerald-50 p-6 text-center">
            <p className="text-sm font-medium text-emerald-700">{S.totalRaised}</p>
            <p className="mt-1 text-2xl font-bold text-emerald-900">
              {formatCents(data.total_raised_cents, data.currency)}
            </p>
          </div>
          <div className="rounded-xl bg-blue-50 p-6 text-center">
            <p className="text-sm font-medium text-blue-700">{S.totalDonors}</p>
            <p className="mt-1 text-2xl font-bold text-blue-900">{data.total_donors}</p>
          </div>
        </div>
      )}

      {/* Currency toggle */}
      <div className="mb-6 flex items-center justify-end gap-2">
        <span className="text-sm text-gray-500">{S.currencyLabel}:</span>
        {CURRENCIES.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setCurrency(c)}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors
              ${
                currency === c
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Table */}
      {!loading && entries.length === 0 ? (
        <div className="rounded-xl bg-gray-50 py-16 text-center">
          <p className="text-gray-500">{S.noDonors}</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="py-3 pl-4 pr-2 text-left text-xs font-semibold
                               uppercase tracking-wider text-gray-500">
                  {S.rank}
                </th>
                <th className="py-3 px-3 text-left text-xs font-semibold
                               uppercase tracking-wider text-gray-500">
                  {S.donor}
                </th>
                <th className="hidden py-3 px-3 text-left text-xs font-semibold
                               uppercase tracking-wider text-gray-500 sm:table-cell">
                  {S.donations}
                </th>
                <th className="py-3 px-3 pr-4 text-right text-xs font-semibold
                               uppercase tracking-wider text-gray-500">
                  {S.amount}
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <LeaderboardRow key={`${entry.rank}-${entry.donor_id}`} entry={entry} currency={currency} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={handleLoadMore}
            disabled={loading}
            className="rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-medium
                       text-white shadow-sm transition-colors hover:bg-emerald-700
                       disabled:opacity-50"
          >
            {loading ? S.loading : S.loadMore}
          </button>
        </div>
      )}

      {/* Loading spinner */}
      {loading && entries.length === 0 && (
        <div className="flex justify-center py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-4
                          border-emerald-200 border-t-emerald-600" />
        </div>
      )}
    </main>
  );
}
