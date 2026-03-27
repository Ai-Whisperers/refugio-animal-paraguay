"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  TrendingUp,
  Calendar,
  Ban,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Analiticas de Adopciones";
const LABEL_LOADING = "Cargando analiticas...";
const LABEL_ERROR = "Error al cargar analiticas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a solicitudes";
const LABEL_TOTAL = "Total de solicitudes";
const LABEL_AVG_TIME = "Tiempo promedio de decision";
const LABEL_APPROVAL_RATE = "Tasa de aprobacion";
const LABEL_LAST_7 = "Ultimos 7 dias";
const LABEL_LAST_30 = "Ultimos 30 dias";
const LABEL_HOURS = "horas";
const LABEL_NO_DATA = "Sin datos suficientes";
const LABEL_STATUS_BREAKDOWN = "Desglose por Estado";
const LABEL_PENDING = "Pendientes";
const LABEL_APPROVED = "Aprobadas";
const LABEL_REJECTED = "Rechazadas";
const LABEL_CANCELLED = "Canceladas";

// --- Types ---
interface StatusBreakdown {
  pending: number;
  approved: number;
  rejected: number;
  cancelled: number;
}

interface AnalyticsData {
  total_requests: number;
  avg_time_to_decision_hours: number | null;
  approval_rate_percent: number | null;
  requests_last_7_days: number;
  requests_last_30_days: number;
  status_breakdown: StatusBreakdown;
}

export default function AdoptionAnalyticsPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyticsData | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.get<AnalyticsData>("/adoption-requests/analytics");
      setData(result);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isChecking) {
      fetchData();
    }
  }, [isChecking, fetchData]);

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/adoptions")}
              className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <BarChart3 className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary disabled:opacity-50"
            aria-label={LABEL_RETRY}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="flex items-center gap-3 text-warm-text-secondary">
              <RefreshCw className="h-5 w-5 animate-spin" />
              <span>{LABEL_LOADING}</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={fetchData}
              className="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Analytics cards */}
        {!isLoading && !error && data && (
          <div className="space-y-6">
            {/* KPI cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Total requests */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-5">
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="h-5 w-5 text-primary-600" />
                  <h3 className="text-sm font-medium text-warm-text-secondary">{LABEL_TOTAL}</h3>
                </div>
                <p className="text-3xl font-bold text-warm-text-primary">{data.total_requests}</p>
              </div>

              {/* Avg time to decision */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="h-5 w-5 text-yellow-600" />
                  <h3 className="text-sm font-medium text-warm-text-secondary">{LABEL_AVG_TIME}</h3>
                </div>
                <p className="text-3xl font-bold text-warm-text-primary">
                  {data.avg_time_to_decision_hours !== null
                    ? `${data.avg_time_to_decision_hours} ${LABEL_HOURS}`
                    : LABEL_NO_DATA}
                </p>
              </div>

              {/* Approval rate */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-5">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <h3 className="text-sm font-medium text-warm-text-secondary">{LABEL_APPROVAL_RATE}</h3>
                </div>
                <p className="text-3xl font-bold text-warm-text-primary">
                  {data.approval_rate_percent !== null
                    ? `${data.approval_rate_percent}%`
                    : LABEL_NO_DATA}
                </p>
              </div>

              {/* Recent volume */}
              <div className="rounded-lg border border-warm-border bg-warm-surface p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-5 w-5 text-blue-600" />
                  <h3 className="text-sm font-medium text-warm-text-secondary">{LABEL_LAST_7}</h3>
                </div>
                <p className="text-3xl font-bold text-warm-text-primary">{data.requests_last_7_days}</p>
                <p className="text-sm text-warm-text-secondary mt-1">
                  {LABEL_LAST_30}: {data.requests_last_30_days}
                </p>
              </div>
            </div>

            {/* Status breakdown */}
            <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
              <h2 className="text-lg font-semibold text-warm-text-primary mb-4">
                {LABEL_STATUS_BREAKDOWN}
              </h2>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4 text-center">
                  <Clock className="h-6 w-6 text-yellow-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-yellow-800">{data.status_breakdown.pending}</p>
                  <p className="text-sm text-yellow-700">{LABEL_PENDING}</p>
                </div>
                <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-center">
                  <CheckCircle className="h-6 w-6 text-green-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-green-800">{data.status_breakdown.approved}</p>
                  <p className="text-sm text-green-700">{LABEL_APPROVED}</p>
                </div>
                <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-center">
                  <XCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-red-800">{data.status_breakdown.rejected}</p>
                  <p className="text-sm text-red-700">{LABEL_REJECTED}</p>
                </div>
                <div className="rounded-lg bg-gray-50 border border-gray-200 p-4 text-center">
                  <Ban className="h-6 w-6 text-gray-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-gray-800">{data.status_breakdown.cancelled}</p>
                  <p className="text-sm text-gray-700">{LABEL_CANCELLED}</p>
                </div>
              </div>

              {/* Progress bar */}
              {data.total_requests > 0 && (
                <div className="mt-4">
                  <div className="flex h-4 rounded-full overflow-hidden">
                    {data.status_breakdown.approved > 0 && (
                      <div
                        className="bg-green-500"
                        style={{ width: `${(data.status_breakdown.approved / data.total_requests) * 100}%` }}
                        title={`${LABEL_APPROVED}: ${data.status_breakdown.approved}`}
                      />
                    )}
                    {data.status_breakdown.pending > 0 && (
                      <div
                        className="bg-yellow-400"
                        style={{ width: `${(data.status_breakdown.pending / data.total_requests) * 100}%` }}
                        title={`${LABEL_PENDING}: ${data.status_breakdown.pending}`}
                      />
                    )}
                    {data.status_breakdown.rejected > 0 && (
                      <div
                        className="bg-red-500"
                        style={{ width: `${(data.status_breakdown.rejected / data.total_requests) * 100}%` }}
                        title={`${LABEL_REJECTED}: ${data.status_breakdown.rejected}`}
                      />
                    )}
                    {data.status_breakdown.cancelled > 0 && (
                      <div
                        className="bg-gray-400"
                        style={{ width: `${(data.status_breakdown.cancelled / data.total_requests) * 100}%` }}
                        title={`${LABEL_CANCELLED}: ${data.status_breakdown.cancelled}`}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
