"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  Scissors,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ArrowLeft,
  Thermometer,
  Activity,
  Heart,
  FileText,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { Surgery, PostOpCheck, PostOpCheckListResponse } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_LOADING = "Cargando recuperacion...";
const LABEL_ERROR_SURGERY = "Error al cargar la cirugia";
const LABEL_ERROR_CHECKS = "Error al cargar controles post-operatorios";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a agenda";
const LABEL_REFRESH = "Actualizar";
const LABEL_TITLE = "Recuperacion Post-Operatoria";
const LABEL_ANIMAL = "Animal";
const LABEL_VET = "Veterinario";
const LABEL_PROCEDURE = "Procedimiento";
const LABEL_DATE = "Fecha";
const LABEL_STATUS = "Estado";
const LABEL_NO_CHECKS = "Sin controles registrados";
const LABEL_NO_CHECKS_SUB = "No hay controles post-operatorios para esta cirugia";
const LABEL_CHECKED_BY = "Controlado por";
const LABEL_TEMP = "Temperatura";
const LABEL_PAIN = "Dolor";
const LABEL_APPETITE = "Apetito";
const LABEL_MOBILITY = "Movilidad";
const LABEL_WOUND = "Herida";
const LABEL_NOTES = "Notas";
const LABEL_CONCERNS = "Preocupaciones";
const LABEL_SURGERY_INFO = "Informacion de Cirugia";
const LABEL_RECOVERY_TIMELINE = "Linea de Tiempo de Recuperacion";

const SURGERY_TYPE_LABELS: Record<string, string> = {
  spay: "Castración (hembra)",
  neuter: "Castración (macho)",
  mass_removal: "Extirpación de masa",
  orthopedic: "Ortopédica",
  dental: "Dental",
  emergency: "Emergencia",
  biopsy: "Biopsia",
  eye: "Ocular",
  other: "Otra",
};

const SURGERY_STATUS_LABELS: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  complications: "Complicaciones",
};

const CHECK_STATUS_CONFIG: Record<
  string,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string; dot: string }
> = {
  pending: {
    label: "Pendiente",
    icon: Clock,
    color: "text-blue-600",
    dot: "bg-blue-400",
  },
  completed: {
    label: "Completado",
    icon: CheckCircle2,
    color: "text-green-600",
    dot: "bg-green-500",
  },
  missed: {
    label: "Omitido",
    icon: XCircle,
    color: "text-gray-400",
    dot: "bg-gray-300",
  },
  concern: {
    label: "Preocupacion",
    icon: AlertTriangle,
    color: "text-red-600",
    dot: "bg-red-500",
  },
};

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  return date.toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// --- Post-op check card ---

interface CheckCardProps {
  check: PostOpCheck;
  index: number;
  total: number;
}

function CheckCard({ check, index, total }: CheckCardProps) {
  const config = CHECK_STATUS_CONFIG[check.check_status] ?? CHECK_STATUS_CONFIG.pending;
  const StatusIcon = config.icon;
  const isLast = index === total - 1;

  return (
    <div className="relative flex gap-4">
      {/* Timeline connector */}
      <div className="flex flex-col items-center">
        <div className={`mt-1 h-4 w-4 flex-shrink-0 rounded-full ${config.dot} ring-2 ring-white`} />
        {!isLast && <div className="mt-1 w-px flex-1 bg-warm-border" />}
      </div>

      {/* Card content */}
      <div className="mb-4 flex-1 rounded-lg border border-warm-border bg-warm-surface p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon className={`h-4 w-4 ${config.color}`} />
            <span className={`text-sm font-semibold ${config.color}`}>
              Control {index + 1} — {config.label}
            </span>
          </div>
          <p className="text-xs text-warm-text-tertiary">
            {formatDateTime(check.scheduled_time)}
          </p>
        </div>

        {/* Metrics grid */}
        <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {check.temperature_celsius !== null && (
            <div className="flex items-center gap-1.5 rounded-md bg-warm-bg px-2.5 py-1.5">
              <Thermometer className="h-3.5 w-3.5 text-orange-500" />
              <div>
                <p className="text-xs text-warm-text-tertiary">{LABEL_TEMP}</p>
                <p className="text-sm font-medium text-warm-text-primary">
                  {check.temperature_celsius}°C
                </p>
              </div>
            </div>
          )}
          {check.pain_level !== null && (
            <div className="flex items-center gap-1.5 rounded-md bg-warm-bg px-2.5 py-1.5">
              <Activity className="h-3.5 w-3.5 text-red-500" />
              <div>
                <p className="text-xs text-warm-text-tertiary">{LABEL_PAIN}</p>
                <p className="text-sm font-medium text-warm-text-primary">
                  {check.pain_level}/10
                </p>
              </div>
            </div>
          )}
          {check.appetite && (
            <div className="flex items-center gap-1.5 rounded-md bg-warm-bg px-2.5 py-1.5">
              <Heart className="h-3.5 w-3.5 text-pink-500" />
              <div>
                <p className="text-xs text-warm-text-tertiary">{LABEL_APPETITE}</p>
                <p className="text-sm font-medium text-warm-text-primary capitalize">
                  {check.appetite}
                </p>
              </div>
            </div>
          )}
          {check.mobility && (
            <div className="flex items-center gap-1.5 rounded-md bg-warm-bg px-2.5 py-1.5">
              <Activity className="h-3.5 w-3.5 text-blue-500" />
              <div>
                <p className="text-xs text-warm-text-tertiary">{LABEL_MOBILITY}</p>
                <p className="text-sm font-medium text-warm-text-primary capitalize">
                  {check.mobility}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Text details */}
        <div className="space-y-1.5">
          {check.checked_by && (
            <p className="text-xs text-warm-text-secondary">
              <span className="font-medium">{LABEL_CHECKED_BY}:</span>{" "}
              {check.checked_by}
            </p>
          )}
          {check.wound_condition && (
            <p className="text-xs text-warm-text-secondary">
              <span className="font-medium">{LABEL_WOUND}:</span>{" "}
              {check.wound_condition}
            </p>
          )}
          {check.notes && (
            <p className="text-xs text-warm-text-secondary">
              <span className="font-medium">{LABEL_NOTES}:</span> {check.notes}
            </p>
          )}
          {check.concerns && (
            <div className="mt-2 flex items-start gap-1.5 rounded-md border border-red-200 bg-red-50 px-2.5 py-1.5">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-red-500" />
              <p className="text-xs text-red-800">
                <span className="font-medium">{LABEL_CONCERNS}:</span>{" "}
                {check.concerns}
              </p>
            </div>
          )}
        </div>

        {check.completed_time && (
          <p className="mt-2 text-xs text-warm-text-tertiary">
            Completado: {formatDateTime(check.completed_time)}
          </p>
        )}
      </div>
    </div>
  );
}

// --- Main page ---

export default function SurgeryRecoveryPage() {
  const router = useRouter();
  const params = useParams();
  const surgeryId = params.id as string;

  const [isChecking, setIsChecking] = useState(true);
  const [surgery, setSurgery] = useState<Surgery | null>(null);
  const [checks, setChecks] = useState<PostOpCheck[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  const fetchData = useCallback(async () => {
    if (!surgeryId) return;
    setIsLoading(true);
    setError(null);
    try {
      const [surgeryData, checksData] = await Promise.all([
        api.get<Surgery>(`/surgeries/${surgeryId}`),
        api.get<PostOpCheckListResponse>(
          `/surgeries/${surgeryId}/post-op-checks`
        ),
      ]);
      setSurgery(surgeryData);
      setChecks(checksData.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.status === 404 ? "Cirugia no encontrada" : LABEL_ERROR_SURGERY);
      } else {
        setError(LABEL_ERROR_SURGERY);
      }
    } finally {
      setIsLoading(false);
    }
  }, [surgeryId]);

  useEffect(() => {
    if (!isChecking) {
      fetchData();
    }
  }, [isChecking, fetchData]);

  if (isChecking) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  const pendingCount = checks.filter((c) => c.check_status === "pending").length;
  const completedCount = checks.filter((c) => c.check_status === "completed").length;
  const concernCount = checks.filter((c) => c.check_status === "concern").length;

  return (
    <div className="mx-auto max-w-3xl">
      {/* Page header */}
      <div className="mb-6 flex items-center gap-3">
        <button
          onClick={() => router.push("/admin/surgeries")}
          className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
          aria-label={LABEL_BACK}
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
          <Scissors className="h-5 w-5 text-purple-600" />
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-warm-text-primary">
            {LABEL_TITLE}
          </h1>
        </div>
        <button
          onClick={fetchData}
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
            onClick={fetchData}
            className="ml-auto text-xs font-medium text-red-700 underline hover:text-red-900"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {!isLoading && !error && surgery && (
        <>
          {/* Surgery summary card */}
          <div className="mb-6 rounded-lg border border-warm-border bg-warm-surface p-4">
            <div className="mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-warm-text-tertiary" />
              <h2 className="text-sm font-semibold text-warm-text-primary">
                {LABEL_SURGERY_INFO}
              </h2>
            </div>
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div>
                <dt className="text-xs text-warm-text-tertiary">{LABEL_PROCEDURE}</dt>
                <dd className="text-sm font-medium text-warm-text-primary">
                  {SURGERY_TYPE_LABELS[surgery.surgery_type] ?? surgery.surgery_type}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-warm-text-tertiary">{LABEL_VET}</dt>
                <dd className="text-sm font-medium text-warm-text-primary">
                  {surgery.veterinarian_name}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-warm-text-tertiary">{LABEL_DATE}</dt>
                <dd className="text-sm font-medium text-warm-text-primary">
                  {formatDate(surgery.scheduled_date)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-warm-text-tertiary">{LABEL_STATUS}</dt>
                <dd className="text-sm font-medium text-warm-text-primary">
                  {SURGERY_STATUS_LABELS[surgery.surgery_status] ?? surgery.surgery_status}
                </dd>
              </div>
              {surgery.outcome && (
                <div>
                  <dt className="text-xs text-warm-text-tertiary">Resultado</dt>
                  <dd className="text-sm font-medium text-warm-text-primary capitalize">
                    {surgery.outcome}
                  </dd>
                </div>
              )}
              {surgery.follow_up_date && (
                <div>
                  <dt className="text-xs text-warm-text-tertiary">Seguimiento</dt>
                  <dd className="text-sm font-medium text-warm-text-primary">
                    {formatDate(surgery.follow_up_date)}
                  </dd>
                </div>
              )}
            </dl>
            {surgery.recovery_notes && (
              <div className="mt-3 border-t border-warm-border pt-3">
                <p className="text-xs text-warm-text-tertiary">Notas de recuperacion</p>
                <p className="mt-0.5 text-sm text-warm-text-secondary">
                  {surgery.recovery_notes}
                </p>
              </div>
            )}
          </div>

          {/* Recovery progress summary */}
          {checks.length > 0 && (
            <div className="mb-6 grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-center">
                <p className="text-lg font-bold text-green-700">{completedCount}</p>
                <p className="text-xs text-green-600">Completados</p>
              </div>
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-center">
                <p className="text-lg font-bold text-blue-700">{pendingCount}</p>
                <p className="text-xs text-blue-600">Pendientes</p>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center">
                <p className="text-lg font-bold text-red-700">{concernCount}</p>
                <p className="text-xs text-red-600">Preocupaciones</p>
              </div>
            </div>
          )}

          {/* Recovery timeline */}
          <div>
            <h2 className="mb-4 text-sm font-semibold text-warm-text-primary">
              {LABEL_RECOVERY_TIMELINE}
            </h2>

            {checks.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-lg border border-warm-border bg-warm-surface py-12">
                <Scissors className="h-8 w-8 text-warm-text-tertiary" />
                <p className="mt-3 text-sm font-medium text-warm-text-secondary">
                  {LABEL_NO_CHECKS}
                </p>
                <p className="mt-1 text-xs text-warm-text-tertiary">
                  {LABEL_NO_CHECKS_SUB}
                </p>
              </div>
            ) : (
              <div>
                {checks.map((check, i) => (
                  <CheckCard
                    key={check.id}
                    check={check}
                    index={i}
                    total={checks.length}
                  />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
