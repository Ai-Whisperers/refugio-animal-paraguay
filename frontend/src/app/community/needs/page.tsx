"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Heart,
  HandHeart,
  Loader2,
  AlertCircle,
  Stethoscope,
  Utensils,
  Home,
  Truck,
  Package,
  HelpCircle,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const S = {
  PAGE_TITLE: "Necesidades de la Comunidad",
  PAGE_SUBTITLE:
    "Estas son necesidades reales de nuestra comunidad. Tu donacion va directamente a resolver una necesidad especifica.",
  HELP_BUTTON: "Ayudar con esto",
  LOADING: "Cargando necesidades...",
  ERROR: "Error al cargar las necesidades",
  RETRY: "Reintentar",
  EMPTY_TITLE: "No hay necesidades abiertas",
  EMPTY_SUBTITLE: "Todas las necesidades han sido cubiertas. Vuelve pronto.",
  RAISED: "Recaudado",
  OF: "de",
  DONORS: "donantes",
  DONOR: "donante",
  BACK_DONATE: "Volver a Donar",
} as const;

const CATEGORY_LABELS: Record<string, string> = {
  medical: "Medico",
  food: "Alimentacion",
  shelter: "Refugio",
  transport: "Transporte",
  supplies: "Suministros",
  other: "Otro",
};

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  medical: Stethoscope,
  food: Utensils,
  shelter: Home,
  transport: Truck,
  supplies: Package,
  other: HelpCircle,
};

const CATEGORY_COLORS: Record<string, string> = {
  medical: "bg-red-100 text-red-700",
  food: "bg-amber-100 text-amber-700",
  shelter: "bg-blue-100 text-blue-700",
  transport: "bg-purple-100 text-purple-700",
  supplies: "bg-green-100 text-green-700",
  other: "bg-gray-100 text-gray-700",
};

interface CommunityNeed {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  estimated_cost_cents: number;
  current_raised_cents: number;
  currency: string;
  donor_count: number;
  image_url: string | null;
  progress_percent: number;
  created_at: string;
}

interface NeedListResponse {
  items: CommunityNeed[];
  total: number;
}

function formatAmount(cents: number, currency: string): string {
  const amount = currency === "PYG" ? cents : cents / 100;
  if (currency === "PYG") {
    return `${amount.toLocaleString("es-PY")} PYG`;
  }
  if (currency === "EUR") {
    return `${amount.toLocaleString("de-DE", { minimumFractionDigits: 2 })} EUR`;
  }
  return `$${amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
}

function NeedCard({ need }: { need: CommunityNeed }) {
  const CategoryIcon = CATEGORY_ICONS[need.category] ?? HelpCircle;
  const categoryColor = CATEGORY_COLORS[need.category] ?? CATEGORY_COLORS.other;
  const categoryLabel = CATEGORY_LABELS[need.category] ?? need.category;

  return (
    <div className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition-shadow hover:shadow-md">
      {need.image_url && (
        <img
          src={need.image_url}
          alt={need.title}
          className="h-40 w-full object-cover"
        />
      )}
      <div className="p-5">
        {/* Category badge */}
        <div className="mb-3 flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${categoryColor}`}
          >
            <CategoryIcon className="h-3 w-3" />
            {categoryLabel}
          </span>
        </div>

        <h3 className="mb-2 text-lg font-semibold text-gray-900">{need.title}</h3>
        <p className="mb-4 line-clamp-2 text-sm text-gray-600">{need.description}</p>

        {/* Progress bar */}
        <div className="mb-3">
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-900">
              {formatAmount(need.current_raised_cents, need.currency)}
            </span>
            <span className="text-gray-500">
              {S.OF} {formatAmount(need.estimated_cost_cents, need.currency)}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-primary-500 transition-all"
              style={{ width: `${Math.min(100, need.progress_percent)}%` }}
            />
          </div>
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>{Math.round(need.progress_percent)}%</span>
            <span>
              {need.donor_count} {need.donor_count === 1 ? S.DONOR : S.DONORS}
            </span>
          </div>
        </div>

        {/* Help button — links to donate page with target params */}
        <Link
          href={`/donate?target_type=need&target_id=${need.id}`}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700"
        >
          <HandHeart className="h-4 w-4" />
          {S.HELP_BUTTON}
        </Link>
      </div>
    </div>
  );
}

export default function CommunityNeedsPage() {
  const [needs, setNeeds] = useState<CommunityNeed[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNeeds = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/community/needs?limit=50`,
      );
      if (!response.ok) {
        throw new Error(S.ERROR);
      }
      const data: NeedListResponse = await response.json();
      setNeeds(data.items);
    } catch {
      setError(S.ERROR);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNeeds();
  }, [fetchNeeds]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-green-50 px-4 py-12 sm:py-16">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-4 inline-flex items-center justify-center rounded-full bg-primary-100 p-3">
            <Heart className="h-8 w-8 text-primary-600" />
          </div>
          <h1 className="mb-4 text-3xl font-bold text-gray-900 sm:text-4xl">
            {S.PAGE_TITLE}
          </h1>
          <p className="mx-auto max-w-2xl text-base text-gray-600 sm:text-lg">
            {S.PAGE_SUBTITLE}
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="mx-auto max-w-6xl px-4 py-10 sm:py-16">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary-500" />
            <p className="text-gray-500">{S.LOADING}</p>
          </div>
        )}

        {error && (
          <div className="mx-auto max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <AlertCircle className="mx-auto mb-2 h-6 w-6 text-red-500" />
            <p className="mb-3 text-sm text-red-700">{error}</p>
            <button
              onClick={fetchNeeds}
              className="rounded-lg bg-red-100 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-200"
            >
              {S.RETRY}
            </button>
          </div>
        )}

        {!isLoading && !error && needs.length === 0 && (
          <div className="py-20 text-center">
            <Heart className="mx-auto mb-3 h-12 w-12 text-gray-300" />
            <h2 className="mb-1 text-lg font-semibold text-gray-700">
              {S.EMPTY_TITLE}
            </h2>
            <p className="text-sm text-gray-500">{S.EMPTY_SUBTITLE}</p>
          </div>
        )}

        {!isLoading && !error && needs.length > 0 && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {needs.map((need) => (
              <NeedCard key={need.id} need={need} />
            ))}
          </div>
        )}

        {/* Back link */}
        <div className="mt-12 text-center">
          <Link
            href="/donate"
            className="text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            {S.BACK_DONATE}
          </Link>
        </div>
      </section>
    </div>
  );
}
