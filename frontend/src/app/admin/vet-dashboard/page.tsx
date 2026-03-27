"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Stethoscope,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  Calendar,
  Clock,
  Syringe,
  PawPrint,
  Activity,
  ArrowRight,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type {
  SurgeryScheduleListResponse,
  SurgeryWithAnimal,
  VaccinationAlertSummary,
  VaccinationAlertItem,
} from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Panel del Veterinario";
const LABEL_LOADING = "Cargando panel...";
const LABEL_ERROR = "Error al cargar datos";
const LABEL_RETRY = "Reintentar";
const LABEL_REFRESH = "Actualizar";
const LABEL_TODAY_SURGERIES = "Cirugias de hoy";
const LABEL_UPCOMING_SURGERIES = "Proximas cirugias";
const LABEL_IN_PROGRESS = "En curso";
const LABEL_COMPLICATIONS = "Con complicaciones";
const LABEL_OVERDUE_VAX = "Vacunas vencidas";
const LABEL_DUE_TODAY_VAX = "Vacunas para hoy";
const LABEL_UPCOMING_VAX = "Vacunas proximas";
const LABEL_EMPTY_SECTION = "Nada pendiente";
const LABEL_VIEW_SURGERIES = "Ver todas las cirugias";
const LABEL_VIEW_VACCINATIONS = "Ver alertas de vacunacion";
const LABEL_ANIMAL = "Animal";
const LABEL_VET = "Veterinario";
const LABEL_TYPE = "Tipo";
const LABEL_DATE = "Fecha";
const LABEL_DAYS = "dias";

const SURGERY_TYPE_LABELS: Record<string, string> = {
  spay: "Castracion (hembra)",
  neuter: "Castracion (macho)",
  mass_removal: "Extirpacion de masa",
  orthopedic: "Ortopedica",
  dental: "Dental",
  emergency: "Emergencia",
  biopsy: "Biopsia",
  eye: "Ocular",
  other: "Otra",
};

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("es-PY", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function isToday(dateString: string): boolean {
  const today = new Date();
  const date = new Date(dateString + "T00:00:00");
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  );
}

function isWithinDays(dateString: string, days: number): boolean {
  const now = new Date();
  const future = new Date();
  future.setDate(now.getDate() + days);
  const date = new Date(dateString + "T00:00:00");
  return date >= now && date <= future;
}

// --- Surgery item component ---
interface SurgeryItemProps {
  surgery: SurgeryWithAnimal;
  onViewRecovery: (id: string) => void;
  showRecovery?: boolean;
}

function SurgeryItem({ surgery, onViewRecovery, showRecovery }: SurgeryItemProps) {
  const typeLabel = SURGERY_TYPE_LABELS[surgery.surgery_type] ?? surgery.surgery_type;
  const isComplication = surgery.surgery_status === "complications";

  return (
    <div
      className={`flex items-start justify-between gap-3 rounded-lg border p-3 ${
        isComplication
          ? "border-red-200 bg-red-50"
          : "border-warm-border bg-warm-bg"
      }`}
    >
      <div className="flex min-w-0 items-start gap-2">
        <PawPrint
          className={`mt-0.5 h-4 w-4 flex-shrink-0 ${
            isComplication ? "text-red-500" : "text-primary-500"
          }`}
        />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-warm-text-primary">
            {surgery.animal_name}
          </p>
          <p className="text-xs text-warm-text-secondary">
            {typeLabel} · {LABEL_VET}: {surgery.veterinarian_name}
          </p>
          <p className="mt-0.5 text-xs text-warm-text-tertiary">
            {formatDate(surgery.scheduled_date)}
          </p>
        </div>
      </div>
      {showRecovery && (
        <button
          onClick={() => onViewRecovery(surgery.id)}
          className="flex items-center gap-1 rounded-lg border border-purple-200 bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 transition-colors hover:bg-purple-100 whitespace-nowrap"
        >
          <Activity className="h-3 w-3" />
          Recuperacion
        </button>
      )}
    </div>
  );
}

// --- Vaccination alert item component ---
interface VaxAlertItemProps {
  alert: VaccinationAlertItem;
  onViewAnimal: (animalId: string) => void;
}

function VaxAlertItem({ alert, onViewAnimal }: VaxAlertItemProps) {
  const isOverdue = alert.severity === "overdue";

  return (
    <div
      className={`flex items-start justify-between gap-3 rounded-lg border p-3 ${
        isOverdue ? "border-red-200 bg-red-50" : "border-yellow-200 bg-yellow-50"
      }`}
    >
      <div className="flex min-w-0 items-start gap-2">
        <Syringe
          className={`mt-0.5 h-4 w-4 flex-shrink-0 ${
            isOverdue ? "text-red-500" : "text-yellow-600"
          }`}
        />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-warm-text-primary">
            {alert.animal_name}
          </p>
          <p className="text-xs text-warm-text-secondary">
            {alert.vaccine_name} · Dosis {alert.dose_number}
          </p>
          <p
            className={`mt-0.5 text-xs font-medium ${
              isOverdue ? "text-red-600" : "text-yellow-700"
            }`}
          >
            {isOverdue
              ? `Vencido hace ${Math.abs(alert.days_until_due)} ${LABEL_DAYS}`
              : alert.days_until_due === 0
              ? "Hoy"
              : `En ${alert.days_until_due} ${LABEL_DAYS}`}
          </p>
        </div>
      </div>
      <button
        onClick={() => onViewAnimal(alert.animal_id)}
        className="rounded-lg border border-warm-border px-2 py-1 text-xs text-warm-text-secondary transition-colors hover:bg-warm-surface whitespace-nowrap"
      >
        Ver animal
      </button>
    </div>
  );
}

// --- Section card ---
interface SectionCardProps {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  count: number;
  children: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

function SectionCard({
  title,
  icon: Icon,
  iconBg,
  iconColor,
  count,
  children,
  actionLabel,
  onAction,
}: SectionCardProps) {
  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={`flex h-7 w-7 items-center justify-center rounded-lg ${iconBg}`}
          >
            <Icon className={`h-4 w-4 ${iconColor}`} />
          </div>
          <h2 className="text-sm font-semibold text-warm-text-primary">{title}</h2>
          {count > 0 && (
            <span className="rounded-full bg-warm-bg px-2 py-0.5 text-xs font-medium text-warm-text-secondary">
              {count}
            </span>
          )}
        </div>
        {actionLabel && onAction && (
          <button
            onClick={onAction}
            className="flex items-center gap-1 text-xs text-primary-600 transition-colors hover:text-primary-700"
          >
            {actionLabel}
            <ArrowRight className="h-3 w-3" />
          </button>
        )}
      </div>
      {count === 0 ? (
        <p className="text-sm text-warm-text-tertiary">{LABEL_EMPTY_SECTION}</p>
      ) : (
        <div className="space-y-2">{children}</div>
      )}
    </div>
  );
}

// --- Main page ---

export default function VetDashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [allSurgeries, setAllSurgeries] = useState<SurgeryWithAnimal[]>([]);
  const [vacAlerts, setVacAlerts] = useState<VaccinationAlertSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchAll = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [surgeriesData, alertsData] = await Promise.all([
        api.get<SurgeryScheduleListResponse>("/surgeries?size=200"),
        api.get<VaccinationAlertSummary>("/vaccination-alerts?window_days=14"),
      ]);
      setAllSurgeries(surgeriesData.items);
      setVacAlerts(alertsData);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isChecking) {
      fetchAll();
    }
  }, [isChecking, fetchAll]);

  function handleViewRecovery(surgeryId: string) {
    router.push(`/admin/surgeries/${surgeryId}/recovery`);
  }

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

  // Derived lists
  const todaySurgeries = allSurgeries.filter(
    (s) => s.surgery_status === "scheduled" && isToday(s.scheduled_date)
  );
  const upcomingSurgeries = allSurgeries.filter(
    (s) =>
      s.surgery_status === "scheduled" &&
      !isToday(s.scheduled_date) &&
      isWithinDays(s.scheduled_date, 7)
  );
  const inProgressSurgeries = allSurgeries.filter(
    (s) => s.surgery_status === "in_progress"
  );
  const complicationSurgeries = allSurgeries.filter(
    (s) => s.surgery_status === "complications"
  );

  const overdueAlerts = vacAlerts?.overdue ?? [];
  const dueTodayAlerts = vacAlerts?.due_today ?? [];
  const upcomingAlerts = vacAlerts?.upcoming ?? [];

  return (
    <div className="mx-auto max-w-4xl">
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-100">
            <Stethoscope className="h-5 w-5 text-teal-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-warm-text-primary">
              {LABEL_PAGE_TITLE}
            </h1>
            <p className="text-xs text-warm-text-tertiary">
              {new Date().toLocaleDateString("es-PY", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
        </div>
        <button
          onClick={fetchAll}
          disabled={isLoading}
          className="flex items-center gap-1.5 rounded-lg border border-warm-border px-3 py-1.5 text-sm font-medium text-warm-text-secondary hover:bg-warm-bg disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          {LABEL_REFRESH}
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
          <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchAll}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Dashboard grid */}
      {!isLoading && !error && (
        <div className="space-y-4">
          {/* Urgent row: complications + in-progress */}
          {(complicationSurgeries.length > 0 || inProgressSurgeries.length > 0) && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <SectionCard
                title={LABEL_COMPLICATIONS}
                icon={AlertTriangle}
                iconBg="bg-red-100"
                iconColor="text-red-600"
                count={complicationSurgeries.length}
                actionLabel={LABEL_VIEW_SURGERIES}
                onAction={() => router.push("/admin/surgeries")}
              >
                {complicationSurgeries.map((s) => (
                  <SurgeryItem
                    key={s.id}
                    surgery={s}
                    onViewRecovery={handleViewRecovery}
                    showRecovery
                  />
                ))}
              </SectionCard>

              <SectionCard
                title={LABEL_IN_PROGRESS}
                icon={Clock}
                iconBg="bg-orange-100"
                iconColor="text-orange-600"
                count={inProgressSurgeries.length}
                actionLabel={LABEL_VIEW_SURGERIES}
                onAction={() => router.push("/admin/surgeries")}
              >
                {inProgressSurgeries.map((s) => (
                  <SurgeryItem
                    key={s.id}
                    surgery={s}
                    onViewRecovery={handleViewRecovery}
                    showRecovery
                  />
                ))}
              </SectionCard>
            </div>
          )}

          {/* Today + upcoming surgeries */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <SectionCard
              title={LABEL_TODAY_SURGERIES}
              icon={Calendar}
              iconBg="bg-blue-100"
              iconColor="text-blue-600"
              count={todaySurgeries.length}
              actionLabel={LABEL_VIEW_SURGERIES}
              onAction={() => router.push("/admin/surgeries")}
            >
              {todaySurgeries.map((s) => (
                <SurgeryItem
                  key={s.id}
                  surgery={s}
                  onViewRecovery={handleViewRecovery}
                />
              ))}
            </SectionCard>

            <SectionCard
              title={LABEL_UPCOMING_SURGERIES}
              icon={Calendar}
              iconBg="bg-indigo-100"
              iconColor="text-indigo-600"
              count={upcomingSurgeries.length}
              actionLabel={LABEL_VIEW_SURGERIES}
              onAction={() => router.push("/admin/surgeries")}
            >
              {upcomingSurgeries.slice(0, 5).map((s) => (
                <SurgeryItem
                  key={s.id}
                  surgery={s}
                  onViewRecovery={handleViewRecovery}
                />
              ))}
              {upcomingSurgeries.length > 5 && (
                <p className="text-xs text-warm-text-tertiary">
                  +{upcomingSurgeries.length - 5} mas esta semana
                </p>
              )}
            </SectionCard>
          </div>

          {/* Vaccination alerts */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <SectionCard
              title={LABEL_OVERDUE_VAX}
              icon={AlertTriangle}
              iconBg="bg-red-100"
              iconColor="text-red-600"
              count={overdueAlerts.length}
              actionLabel={LABEL_VIEW_VACCINATIONS}
              onAction={() => router.push("/admin/medical/alerts")}
            >
              {overdueAlerts.slice(0, 5).map((alert) => (
                <VaxAlertItem
                  key={alert.vaccination_id}
                  alert={alert}
                  onViewAnimal={handleViewAnimal}
                />
              ))}
              {overdueAlerts.length > 5 && (
                <p className="text-xs text-warm-text-tertiary">
                  +{overdueAlerts.length - 5} mas vencidas
                </p>
              )}
            </SectionCard>

            <SectionCard
              title={LABEL_DUE_TODAY_VAX}
              icon={Syringe}
              iconBg="bg-yellow-100"
              iconColor="text-yellow-600"
              count={dueTodayAlerts.length + upcomingAlerts.length}
              actionLabel={LABEL_VIEW_VACCINATIONS}
              onAction={() => router.push("/admin/medical/alerts")}
            >
              {[...dueTodayAlerts, ...upcomingAlerts].slice(0, 5).map((alert) => (
                <VaxAlertItem
                  key={alert.vaccination_id}
                  alert={alert}
                  onViewAnimal={handleViewAnimal}
                />
              ))}
              {dueTodayAlerts.length + upcomingAlerts.length > 5 && (
                <p className="text-xs text-warm-text-tertiary">
                  +{dueTodayAlerts.length + upcomingAlerts.length - 5} mas
                </p>
              )}
            </SectionCard>
          </div>
        </div>
      )}
    </div>
  );
}
