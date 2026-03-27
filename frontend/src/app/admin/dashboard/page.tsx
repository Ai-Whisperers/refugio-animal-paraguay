"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  PawPrint,
  Heart,
  DollarSign,
  Users,
  TrendingUp,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { isAuthenticated, getAccessToken, decodeToken } from "@/lib/auth";
import { api } from "@/lib/api";
import type { UserRole } from "@/types/api";

// -- Spanish labels --
const LABEL_DASHBOARD = "Panel de Administracion";
const LABEL_WELCOME_PREFIX = "Bienvenido";
const LABEL_LOADING = "Cargando datos del panel...";
const LABEL_ERROR = "Error al cargar datos";
const LABEL_RETRY = "Reintentar";
const LABEL_TOTAL_ANIMALS = "Total de Animales";
const LABEL_PENDING_ADOPTIONS = "Adopciones Pendientes";
const LABEL_DONATIONS_MONTH = "Donaciones del Mes";
const LABEL_TOTAL_DONATIONS = "Total de Donaciones";
const LABEL_QUICK_LINKS = "Accesos Rapidos";
const LABEL_VIEW_ANIMALS = "Ver Animales";
const LABEL_VIEW_ADOPTIONS = "Ver Adopciones";
const LABEL_VIEW_DONATIONS = "Ver Donaciones";
const LABEL_VIEW_DONORS = "Ver Donantes";

// -- Types for API responses --
interface AnimalListItem {
  id: string;
  name: string;
  status: string;
}

interface StatusBreakdown {
  pending: number;
  approved: number;
  rejected: number;
  cancelled: number;
}

interface AdoptionAnalytics {
  total_requests: number;
  avg_time_to_decision_hours: number | null;
  approval_rate_percent: number | null;
  requests_last_7_days: number;
  requests_last_30_days: number;
  status_breakdown: StatusBreakdown;
}

interface CurrencyBreakdown {
  currency: string;
  count: number;
  total_amount_cents: number;
}

interface DonationStats {
  total_donations: number;
  by_currency: CurrencyBreakdown[];
  date_from: string | null;
  date_to: string | null;
}

interface DashboardData {
  totalAnimals: number;
  pendingAdoptions: number;
  donationsThisMonth: number;
  donationAmounts: CurrencyBreakdown[];
}

function formatCurrency(amountCents: number, currency: string): string {
  const amount = currency === "PYG" ? amountCents : amountCents / 100;
  if (currency === "PYG") {
    return `${amount.toLocaleString("es-PY")} PYG`;
  }
  if (currency === "EUR") {
    return `${amount.toLocaleString("de-DE", { minimumFractionDigits: 2 })} EUR`;
  }
  return `${amount.toLocaleString("en-US", { minimumFractionDigits: 2 })} ${currency}`;
}

function getMonthDateRange(): { dateFrom: string; dateTo: string } {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const dateFrom = firstDay.toISOString();
  const dateTo = now.toISOString();
  return { dateFrom, dateTo };
}

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

function KpiCard({ title, value, subtitle, icon: Icon, color }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-warm-border bg-warm-surface p-6 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-warm-text-tertiary">{title}</p>
          <p className="mt-2 text-3xl font-bold text-warm-text-primary">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-warm-text-secondary">{subtitle}</p>
          )}
        </div>
        <div className={`rounded-lg p-3 ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { dateFrom, dateTo } = getMonthDateRange();

      const [animals, adoptionAnalytics, donationStats] = await Promise.all([
        api.get<AnimalListItem[]>("/animals?limit=1&offset=0").catch(() => [] as AnimalListItem[]),
        api.get<AdoptionAnalytics>("/adoption-requests/analytics").catch(() => null),
        api.get<DonationStats>(
          `/donations/stats?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`
        ).catch(() => null),
      ]);

      // For animal count, we need total. The list endpoint returns a list,
      // so we fetch with a large limit to count. For MVP, use a separate count approach.
      // Since we don't have a count endpoint, fetch all IDs with minimal data.
      let totalAnimals = animals.length;
      if (totalAnimals === 1) {
        // We got limit=1, try fetching actual count
        const allAnimals = await api.get<AnimalListItem[]>("/animals?limit=100&offset=0").catch(() => []);
        totalAnimals = allAnimals.length;
      }

      setData({
        totalAnimals,
        pendingAdoptions: adoptionAnalytics?.status_breakdown?.pending ?? 0,
        donationsThisMonth: donationStats?.total_donations ?? 0,
        donationAmounts: donationStats?.by_currency ?? [],
      });
    } catch {
      setError(LABEL_ERROR);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }

    const token = getAccessToken();
    if (token) {
      const payload = decodeToken(token);
      if (payload) {
        setUserRole(payload.role);
      }
    }
    setIsChecking(false);
    fetchDashboardData();
  }, [router, fetchDashboardData]);

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
        <p className="ml-2 text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  const donationSubtitle =
    data?.donationAmounts && data.donationAmounts.length > 0
      ? data.donationAmounts.map((c) => formatCurrency(c.total_amount_cents, c.currency)).join(" | ")
      : undefined;

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-warm-text-primary">{LABEL_DASHBOARD}</h1>
        <p className="mt-1 text-warm-text-secondary">
          {LABEL_WELCOME_PREFIX}
          {userRole && (
            <span className="ml-2 inline-flex rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-medium text-primary-700 capitalize">
              {userRole}
            </span>
          )}
        </p>
      </div>

      {/* Error state */}
      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <p className="flex-1 text-sm text-red-700">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="rounded-lg bg-red-100 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-200 transition-colors"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-xl border border-warm-border bg-warm-surface"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title={LABEL_TOTAL_ANIMALS}
            value={data?.totalAnimals ?? 0}
            icon={PawPrint}
            color="bg-blue-500"
          />
          <KpiCard
            title={LABEL_PENDING_ADOPTIONS}
            value={data?.pendingAdoptions ?? 0}
            icon={Heart}
            color="bg-pink-500"
          />
          <KpiCard
            title={LABEL_DONATIONS_MONTH}
            value={data?.donationsThisMonth ?? 0}
            subtitle={donationSubtitle}
            icon={DollarSign}
            color="bg-green-500"
          />
          <KpiCard
            title={LABEL_TOTAL_DONATIONS}
            value={
              data?.donationAmounts && data.donationAmounts.length > 0
                ? data.donationAmounts.map((c) => formatCurrency(c.total_amount_cents, c.currency)).join(" | ")
                : "0"
            }
            subtitle={LABEL_DONATIONS_MONTH}
            icon={TrendingUp}
            color="bg-purple-500"
          />
        </div>
      )}

      {/* Quick Links */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-warm-text-primary">{LABEL_QUICK_LINKS}</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <QuickLink
            label={LABEL_VIEW_ANIMALS}
            href="/admin/animals"
            icon={PawPrint}
            description="Gestionar registro de animales"
          />
          <QuickLink
            label={LABEL_VIEW_ADOPTIONS}
            href="/admin/adoptions"
            icon={Heart}
            description="Revisar solicitudes de adopcion"
          />
          <QuickLink
            label={LABEL_VIEW_DONATIONS}
            href="/admin/donations"
            icon={DollarSign}
            description="Historial de donaciones"
          />
          <QuickLink
            label={LABEL_VIEW_DONORS}
            href="/admin/donors"
            icon={Users}
            description="Perfiles de donantes"
          />
        </div>
      </div>
    </div>
  );
}

interface QuickLinkProps {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

function QuickLink({ label, href, icon: Icon, description }: QuickLinkProps) {
  const router = useRouter();
  return (
    <button
      onClick={() => router.push(href)}
      className="group flex items-start gap-4 rounded-lg border border-warm-border bg-warm-surface p-4 text-left transition-all hover:border-primary-300 hover:shadow-md"
    >
      <div className="rounded-lg bg-primary-50 p-2.5 group-hover:bg-primary-100 transition-colors">
        <Icon className="h-5 w-5 text-primary-600" />
      </div>
      <div>
        <p className="font-medium text-warm-text-primary">{label}</p>
        <p className="mt-0.5 text-sm text-warm-text-secondary">{description}</p>
      </div>
    </button>
  );
}
