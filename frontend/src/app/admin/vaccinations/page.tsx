"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Syringe,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ArrowLeft,
  PawPrint,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { VaccinationAlertSummary, VaccinationAlertItem } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Calendario de Vacunacion";
const LABEL_LOADING = "Cargando alertas de vacunacion...";
const LABEL_ERROR = "Error al cargar alertas de vacunacion";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_REFRESH = "Actualizar";
const LABEL_OVERDUE = "Atrasadas";
const LABEL_DUE_TODAY = "Vencen hoy";
const LABEL_UPCOMING = "Proximas";
const LABEL_NO_OVERDUE = "Sin vacunas atrasadas";
const LABEL_NO_DUE_TODAY = "Sin vacunas para hoy";
const LABEL_NO_UPCOMING = "Sin vacunas proximas";
const LABEL_ANIMAL = "Animal";
const LABEL_VACCINE = "Vacuna";
const LABEL_SCHEDULED_DATE = "Fecha programada";
const LABEL_DOSE = "Dosis";
const LABEL_DAYS_OVERDUE = "dias de retraso";
const LABEL_DAYS_UNTIL = "dias";
const LABEL_TODAY = "Hoy";
const LABEL_VIEW_ANIMAL = "Ver animal";
const LABEL_WINDOW_LABEL = "Ventana de dias";

const WINDOW_OPTIONS = [
  { value: 7, label: "7 dias" },
  { value: 14, label: "14 dias" },
  { value: 30, label: "30 dias" },
  { value: 60, label: "60 dias" },
  { value: 90, label: "90 dias" },
];

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// --- Alert item row ---

interface AlertRowProps {
  alert: VaccinationAlertItem;
  onViewAnimal: (animalId: string) => void;
}

function AlertRow({ alert, onViewAnimal }: AlertRowProps) {
  const absOverdueDays = Math.abs(alert.days_until_due);

  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-warm-border bg-warm-bg px-4 py-3 hover:bg-warm-surface transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-primary-100">
          <PawPrint className="h-4 w-4 text-primary-600" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-warm-text-primary">
            {alert.animal_name}
          </p>
          <p className="text-xs text-warm-text-secondary">
            {alert.vaccine_name} — {LABEL_DOSE} {alert.dose_number}
          </p>
        </div>
      </div>

      <div className="flex flex-shrink-0 items-center gap-3">
        <div className="text-right">
          <p className="text-xs text-warm-text-secondary">
            {formatDate(alert.scheduled_date)}
          </p>
          {alert.severity === "overdue" && (
            <p className="text-xs font-medium text-red-600">
              {absOverdueDays} {LABEL_DAYS_OVERDUE}
            </p>
          )}
          {alert.severity === "due_today" && (
            <p className="text-xs font-medium text-orange-600">{LABEL_TODAY}</p>
          )}
          {alert.severity === "upcoming" && (
            <p className="text-xs text-warm-text-tertiary">
              {LABEL_TODAY} + {alert.days_until_due} {LABEL_DAYS_UNTIL}
            </p>
          )}
        </div>
        <button
          onClick={() => onViewAnimal(alert.animal_id)}
          className="rounded-lg border border-warm-border px-2.5 py-1 text-xs font-medium text-warm-text-secondary hover:bg-warm-surface hover:text-warm-text-primary"
        >
          {LABEL_VIEW_ANIMAL}
        </button>
      </div>
    </div>
  );
}

// --- Section card ---

interface AlertSectionProps {
  title: string;
  count: number;
  emptyMessage: string;
  alerts: VaccinationAlertItem[];
  icon: React.ReactNode;
  colorClass: string;
  badgeClass: string;
  onViewAnimal: (animalId: string) => void;
}

function AlertSection({
  title,
  count,
  emptyMessage,
  alerts,
  icon,
  colorClass,
  badgeClass,
  onViewAnimal,
}: AlertSectionProps) {
  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface">
      {/* Section header */}
      <div className={`flex items-center justify-between border-b border-warm-border px-4 py-3 ${colorClass}`}>
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-sm font-semibold text-warm-text-primary">{title}</h2>
        </div>
        <span className={`inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-xs font-bold ${badgeClass}`}>
          {count}
        </span>
      </div>

      {/* Items */}
      <div className="divide-y divide-warm-border p-3 space-y-1.5">
        {alerts.length === 0 ? (
          <div className="flex items-center justify-center py-4">
            <p className="text-sm text-warm-text-tertiary">{emptyMessage}</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <AlertRow
              key={alert.vaccination_id}
              alert={alert}
              onViewAnimal={onViewAnimal}
            />
          ))
        )}
      </div>
    </div>
  );
}

// --- Main page ---

export default function VaccinationSchedulePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [alerts, setAlerts] = useState<VaccinationAlertSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(30);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<VaccinationAlertSummary>(
        `/vaccination-alerts?window_days=${windowDays}`
      );
      setAlerts(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [windowDays]);

  useEffect(() => {
    if (!isChecking) {
      fetchAlerts();
    }
  }, [isChecking, fetchAlerts]);

  function handleViewAnimal(animalId: string) {
    router.push(`/admin/animals/${animalId}?tab=medical`);
  }

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
            <Syringe className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Window days selector */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-warm-text-secondary">
              {LABEL_WINDOW_LABEL}:
            </label>
            <select
              value={windowDays}
              onChange={(e) => setWindowDays(Number(e.target.value))}
              className="rounded-lg border border-warm-border bg-warm-bg px-2 py-1.5 text-sm text-warm-text-primary focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              {WINDOW_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={fetchAlerts}
            disabled={isLoading}
            className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
        </div>
      </div>

      {/* Loading / error states */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
          <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchAlerts}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {!isLoading && !error && alerts && (
        <>
          {/* KPI summary row */}
          <div className="mb-6 grid grid-cols-3 gap-4">
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
              <p className="text-2xl font-bold text-red-700">
                {alerts.total_overdue}
              </p>
              <p className="mt-1 text-xs font-medium text-red-600">
                {LABEL_OVERDUE}
              </p>
            </div>
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-center">
              <p className="text-2xl font-bold text-orange-700">
                {alerts.total_due_today}
              </p>
              <p className="mt-1 text-xs font-medium text-orange-600">
                {LABEL_DUE_TODAY}
              </p>
            </div>
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-center">
              <p className="text-2xl font-bold text-blue-700">
                {alerts.total_upcoming}
              </p>
              <p className="mt-1 text-xs font-medium text-blue-600">
                {LABEL_UPCOMING}
              </p>
            </div>
          </div>

          {/* Alert sections */}
          <div className="space-y-4">
            <AlertSection
              title={LABEL_OVERDUE}
              count={alerts.total_overdue}
              emptyMessage={LABEL_NO_OVERDUE}
              alerts={alerts.overdue}
              icon={<AlertCircle className="h-4 w-4 text-red-500" />}
              colorClass="bg-red-50"
              badgeClass="bg-red-200 text-red-800"
              onViewAnimal={handleViewAnimal}
            />
            <AlertSection
              title={LABEL_DUE_TODAY}
              count={alerts.total_due_today}
              emptyMessage={LABEL_NO_DUE_TODAY}
              alerts={alerts.due_today}
              icon={<AlertTriangle className="h-4 w-4 text-orange-500" />}
              colorClass="bg-orange-50"
              badgeClass="bg-orange-200 text-orange-800"
              onViewAnimal={handleViewAnimal}
            />
            <AlertSection
              title={LABEL_UPCOMING}
              count={alerts.total_upcoming}
              emptyMessage={LABEL_NO_UPCOMING}
              alerts={alerts.upcoming}
              icon={<Clock className="h-4 w-4 text-blue-500" />}
              colorClass="bg-blue-50"
              badgeClass="bg-blue-200 text-blue-800"
              onViewAnimal={handleViewAnimal}
            />
          </div>
        </>
      )}
    </div>
  );
}
