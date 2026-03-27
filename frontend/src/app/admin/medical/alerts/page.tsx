"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  Clock,
  Calendar,
  RefreshCw,
  ArrowLeft,
  Syringe,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Alertas Medicas";
const LABEL_LOADING = "Cargando alertas...";
const LABEL_ERROR = "Error al cargar alertas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_OVERDUE = "Vencidas";
const LABEL_DUE_TODAY = "Vencen Hoy";
const LABEL_UPCOMING = "Proximas (7 dias)";
const LABEL_EMPTY = "No hay alertas medicas en este momento.";
const LABEL_ANIMAL = "Animal";
const LABEL_VACCINE = "Vacuna";
const LABEL_DATE = "Fecha";
const LABEL_DAYS = "dias";
const LABEL_DAY = "dia";
const LABEL_OVERDUE_LABEL = "vencida hace";
const LABEL_DUE_IN = "vence en";
const LABEL_TODAY = "vence hoy";
const LABEL_DOSE = "Dosis";
const LABEL_REFRESH = "Actualizar";

// --- Types ---
interface VaccinationAlertItem {
  vaccination_id: string;
  animal_id: string;
  animal_name: string;
  vaccine_name: string;
  scheduled_date: string;
  days_until_due: number;
  severity: "overdue" | "due_today" | "upcoming";
  dose_number: number;
}

interface VaccinationAlertSummary {
  overdue: VaccinationAlertItem[];
  due_today: VaccinationAlertItem[];
  upcoming: VaccinationAlertItem[];
  total_overdue: number;
  total_due_today: number;
  total_upcoming: number;
}

// --- Severity config ---
const SEVERITY_CONFIG = {
  overdue: {
    label: LABEL_OVERDUE,
    icon: AlertTriangle,
    headerClass: "bg-red-50 border-red-200",
    titleClass: "text-red-800",
    badgeClass: "bg-red-100 text-red-700",
    rowClass: "hover:bg-red-50",
    iconClass: "text-red-600",
    countClass: "bg-red-600 text-white",
  },
  due_today: {
    label: LABEL_DUE_TODAY,
    icon: Clock,
    headerClass: "bg-yellow-50 border-yellow-200",
    titleClass: "text-yellow-800",
    badgeClass: "bg-yellow-100 text-yellow-700",
    rowClass: "hover:bg-yellow-50",
    iconClass: "text-yellow-600",
    countClass: "bg-yellow-500 text-white",
  },
  upcoming: {
    label: LABEL_UPCOMING,
    icon: Calendar,
    headerClass: "bg-green-50 border-green-200",
    titleClass: "text-green-800",
    badgeClass: "bg-green-100 text-green-700",
    rowClass: "hover:bg-green-50",
    iconClass: "text-green-600",
    countClass: "bg-green-600 text-white",
  },
} as const;

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("es-PY", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatDaysLabel(daysUntilDue: number): string {
  if (daysUntilDue === 0) return LABEL_TODAY;
  const absdays = Math.abs(daysUntilDue);
  const unit = absdays === 1 ? LABEL_DAY : LABEL_DAYS;
  if (daysUntilDue < 0) return `${LABEL_OVERDUE_LABEL} ${absdays} ${unit}`;
  return `${LABEL_DUE_IN} ${absdays} ${unit}`;
}

// --- Alert section component ---
interface AlertSectionProps {
  severity: "overdue" | "due_today" | "upcoming";
  items: VaccinationAlertItem[];
  onViewAnimal: (animalId: string) => void;
}

function AlertSection({ severity, items, onViewAnimal }: AlertSectionProps) {
  const config = SEVERITY_CONFIG[severity];
  const Icon = config.icon;

  if (items.length === 0) return null;

  return (
    <section aria-labelledby={`alert-section-${severity}`}>
      <div className={`mb-3 flex items-center gap-3 rounded-t-lg border px-4 py-3 ${config.headerClass}`}>
        <Icon className={`h-5 w-5 ${config.iconClass}`} aria-hidden="true" />
        <h2 id={`alert-section-${severity}`} className={`text-base font-semibold ${config.titleClass}`}>
          {config.label}
        </h2>
        <span className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-bold ${config.countClass}`}>
          {items.length}
        </span>
      </div>

      <div className="overflow-hidden rounded-b-lg border border-t-0 border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-100" role="table">
          <thead>
            <tr className="bg-gray-50">
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {LABEL_ANIMAL}
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {LABEL_VACCINE}
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {LABEL_DOSE}
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                {LABEL_DATE}
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gray-500"
              >
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item) => (
              <tr key={item.vaccination_id} className={`transition-colors ${config.rowClass}`}>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onViewAnimal(item.animal_id)}
                    className="font-medium text-primary-600 hover:text-primary-800 hover:underline"
                  >
                    {item.animal_name}
                  </button>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  <span className="flex items-center gap-1.5">
                    <Syringe className="h-3.5 w-3.5 text-gray-400" aria-hidden="true" />
                    {item.vaccine_name}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  #{item.dose_number}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {formatDate(item.scheduled_date)}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${config.badgeClass}`}>
                    {formatDaysLabel(item.days_until_due)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// --- Main page ---
export default function MedicalAlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<VaccinationAlertSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auth guard
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<VaccinationAlertSummary>(
        "/vaccinations/vaccination-alerts?window_days=7"
      );
      setAlerts(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${err.statusCode}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  function handleViewAnimal(animalId: string) {
    router.push(`/admin/animals/${animalId}`);
  }

  const totalAlerts =
    (alerts?.total_overdue ?? 0) +
    (alerts?.total_due_today ?? 0) +
    (alerts?.total_upcoming ?? 0);

  const hasNoAlerts = alerts !== null && totalAlerts === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            {alerts && !loading && (
              <p className="text-sm text-warm-text-secondary">
                {totalAlerts === 0
                  ? "Sin alertas activas"
                  : `${totalAlerts} alerta${totalAlerts !== 1 ? "s" : ""} activa${totalAlerts !== 1 ? "s" : ""}`}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={fetchAlerts}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          aria-label={LABEL_REFRESH}
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
          {LABEL_REFRESH}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16 text-warm-text-secondary">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />
          {LABEL_LOADING}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-500" aria-hidden="true" />
          <p className="mb-4 font-medium text-red-800">{error}</p>
          <button
            onClick={fetchAlerts}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && hasNoAlerts && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-10 text-center">
          <Calendar className="mx-auto mb-3 h-10 w-10 text-green-500" aria-hidden="true" />
          <p className="text-base font-medium text-green-800">{LABEL_EMPTY}</p>
        </div>
      )}

      {/* Alerts sections */}
      {!loading && !error && alerts && totalAlerts > 0 && (
        <div className="space-y-6">
          <AlertSection
            severity="overdue"
            items={alerts.overdue}
            onViewAnimal={handleViewAnimal}
          />
          <AlertSection
            severity="due_today"
            items={alerts.due_today}
            onViewAnimal={handleViewAnimal}
          />
          <AlertSection
            severity="upcoming"
            items={alerts.upcoming}
            onViewAnimal={handleViewAnimal}
          />
        </div>
      )}
    </div>
  );
}
