"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  Calendar,
  Clock,
  Users,
  MapPin,
  ArrowLeft,
  RefreshCw,
  CheckCircle,
  XCircle,
  MinusCircle,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { Shift, ShiftSignup } from "@/types/api";

// ---------------------------------------------------------------------------
// Labels
// ---------------------------------------------------------------------------

const LABEL_PAGE_TITLE = "Detalle del turno";
const LABEL_LOADING = "Cargando turno...";
const LABEL_ERROR = "Error al cargar turno";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a turnos";
const LABEL_NO_SIGNUPS = "Ningún voluntario se ha apuntado a este turno";
const LABEL_VOLUNTEERS = "Voluntarios apuntados";
const LABEL_MARK_ATTENDED = "Asistió";
const LABEL_MARK_NO_SHOW = "No se presentó";
const LABEL_CLEAR = "Sin registro";
const LABEL_SAVING = "Guardando...";

const MONTHS_ES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

const ROLE_LABELS: Record<string, string> = {
  animal_care: "Cuidado animal",
  veterinary_assistance: "Asistencia veterinaria",
  cleaning: "Limpieza",
  transport_driving: "Transporte",
  admin_office: "Oficina / Admin",
  education_outreach: "Educación",
  event_coordination: "Eventos",
  general: "General",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Disponible",
  full: "Completo",
  cancelled: "Cancelado",
  completed: "Completado",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-green-100 text-green-800",
  full: "bg-orange-100 text-orange-800",
  cancelled: "bg-red-100 text-red-700",
  completed: "bg-gray-100 text-gray-600",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtTime(t: string): string {
  return t.slice(0, 5);
}

function fmtDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return `${d.getDate()} de ${MONTHS_ES[d.getMonth()]} ${d.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Signup row with attendance controls
// ---------------------------------------------------------------------------

interface SignupRowProps {
  signup: ShiftSignup;
  onAttendance: (signupId: string, attended: boolean | null) => Promise<void>;
}

function SignupRow({ signup, onAttendance }: SignupRowProps) {
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleMark(attended: boolean | null) {
    if (busy) return;
    setLocalError(null);
    setBusy(true);
    try {
      await onAttendance(signup.id, attended);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setLocalError(err.detail);
      } else {
        setLocalError("Error inesperado");
      }
    } finally {
      setBusy(false);
    }
  }

  const statusIcon =
    signup.attended === true ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : signup.attended === false ? (
      <XCircle className="h-4 w-4 text-red-500" />
    ) : (
      <MinusCircle className="h-4 w-4 text-gray-300" />
    );

  const statusLabel =
    signup.attended === true
      ? "Asistió"
      : signup.attended === false
      ? "No se presentó"
      : "Sin registro";

  const statusTextColor =
    signup.attended === true
      ? "text-green-700"
      : signup.attended === false
      ? "text-red-600"
      : "text-gray-400";

  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-gray-100 bg-white p-3">
      <div className="flex items-center gap-3 min-w-0">
        {statusIcon}
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-700 truncate">
            Voluntario{" "}
            <span className="font-mono text-xs text-gray-400">
              {signup.volunteer_id.slice(0, 8)}…
            </span>
          </p>
          {signup.notes && (
            <p className="text-xs text-gray-400 truncate">{signup.notes}</p>
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <span className={`text-xs font-medium ${statusTextColor}`}>
          {statusLabel}
        </span>

        {localError && (
          <span className="text-xs text-red-600">{localError}</span>
        )}

        <div className="flex gap-1">
          <button
            onClick={() => handleMark(true)}
            disabled={busy || signup.attended === true}
            title={LABEL_MARK_ATTENDED}
            className={`rounded-lg p-1.5 transition-colors ${
              signup.attended === true
                ? "bg-green-100 text-green-700"
                : "text-gray-400 hover:bg-green-50 hover:text-green-600"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            <CheckCircle className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleMark(false)}
            disabled={busy || signup.attended === false}
            title={LABEL_MARK_NO_SHOW}
            className={`rounded-lg p-1.5 transition-colors ${
              signup.attended === false
                ? "bg-red-100 text-red-600"
                : "text-gray-400 hover:bg-red-50 hover:text-red-500"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            <XCircle className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleMark(null)}
            disabled={busy || signup.attended === null}
            title={LABEL_CLEAR}
            className="rounded-lg p-1.5 text-gray-300 transition-colors hover:bg-gray-50 hover:text-gray-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <MinusCircle className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

interface SignupListItem extends ShiftSignup {
  attended: boolean | null;
}

export default function ShiftDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const shiftId = params.id;

  const [shift, setShift] = useState<Shift | null>(null);
  const [signups, setSignups] = useState<SignupListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
    }
  }, [router]);

  const loadData = useCallback(async () => {
    if (!shiftId) return;
    setLoading(true);
    setError(null);
    try {
      const [shiftData, signupsData] = await Promise.all([
        api.get<Shift>(`/api/shifts/${shiftId}`),
        api.get<{ items: ShiftSignup[]; total: number }>(`/api/shifts/${shiftId}/signups`),
      ]);
      setShift(shiftData);
      setSignups(signupsData.items as SignupListItem[]);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [shiftId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleAttendance(signupId: string, attended: boolean | null) {
    await api.patch<ShiftSignup>(`/api/shifts/${shiftId}/signups/${signupId}`, { attended });
    setSignups((prev) =>
      prev.map((s) => (s.id === signupId ? { ...s, attended } : s))
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/shifts")}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Calendar className="h-6 w-6 text-emerald-600" />
            <h1 className="text-xl font-bold text-gray-800">{LABEL_PAGE_TITLE}</h1>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="ml-auto rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-40"
            aria-label="Actualizar"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-3xl p-6">
        {loading && (
          <div className="flex items-center justify-center py-20 text-gray-400">
            <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
            {LABEL_LOADING}
          </div>
        )}

        {!loading && error && (
          <div className="flex flex-col items-center gap-4 py-16">
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadData}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {!loading && !error && shift && (
          <div className="space-y-6">
            {/* Shift info card */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  {shift.title && (
                    <h2 className="text-lg font-semibold text-gray-800">{shift.title}</h2>
                  )}
                  <p className="text-sm text-gray-500">
                    {ROLE_LABELS[shift.role] ?? shift.role}
                  </p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
                    STATUS_COLORS[shift.status] ?? "bg-gray-100 text-gray-600"
                  }`}
                >
                  {STATUS_LABELS[shift.status] ?? shift.status}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4 text-emerald-600" />
                  {fmtDate(shift.shift_date)}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="h-4 w-4 text-emerald-600" />
                  {fmtTime(shift.start_time)} – {fmtTime(shift.end_time)}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Users className="h-4 w-4 text-emerald-600" />
                  {shift.slots_filled} / {shift.capacity} voluntarios
                </div>
                {shift.location && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="h-4 w-4 text-emerald-600" />
                    {shift.location}
                  </div>
                )}
              </div>

              {shift.notes && (
                <p className="mt-3 rounded-lg bg-gray-50 p-3 text-sm text-gray-600">
                  {shift.notes}
                </p>
              )}
            </div>

            {/* Signups + attendance */}
            <div>
              <h3 className="mb-3 text-base font-semibold text-gray-800">
                {LABEL_VOLUNTEERS}
                <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                  {signups.length}
                </span>
              </h3>

              {signups.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-200 py-12 text-center text-sm text-gray-400">
                  {LABEL_NO_SIGNUPS}
                </div>
              ) : (
                <div className="space-y-2">
                  {signups.map((signup) => (
                    <SignupRow
                      key={signup.id}
                      signup={signup}
                      onAttendance={handleAttendance}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
