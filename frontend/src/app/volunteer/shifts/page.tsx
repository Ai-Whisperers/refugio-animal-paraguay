"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  Clock,
  Users,
  MapPin,
  CheckCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  LogIn,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { Shift, PaginatedShiftList, ShiftSignup, MySignupsResponse, ShiftRole } from "@/types/api";

// ---------------------------------------------------------------------------
// Constants & labels
// ---------------------------------------------------------------------------

const LABEL_PAGE_TITLE = "Turnos Disponibles";
const LABEL_MY_SIGNUPS = "Mis turnos";
const LABEL_ALL_SHIFTS = "Todos los turnos";
const LABEL_LOADING = "Cargando turnos...";
const LABEL_ERROR = "Error al cargar turnos";
const LABEL_RETRY = "Reintentar";
const LABEL_NO_SHIFTS = "Sin turnos disponibles esta semana";
const LABEL_FULL = "Completo";
const LABEL_SIGNUP = "Apuntarme";
const LABEL_CANCEL_SIGNUP = "Cancelar apunte";
const LABEL_SIGNED_UP = "Apuntado";
const LABEL_PREV_WEEK = "Semana anterior";
const LABEL_NEXT_WEEK = "Semana siguiente";
const LABEL_LOGIN_REQUIRED = "Inicia sesión para apuntarte a un turno";
const LABEL_LOGIN = "Iniciar sesión";
const LABEL_BACK = "Volver";

const DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

const MONTHS_ES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

const ROLE_LABELS: Record<ShiftRole, string> = {
  animal_care: "Cuidado animal",
  veterinary_assistance: "Asistencia veterinaria",
  cleaning: "Limpieza",
  transport_driving: "Transporte",
  admin_office: "Oficina / Admin",
  education_outreach: "Educación",
  event_coordination: "Eventos",
  general: "General",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getMondayOf(d: Date): Date {
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  const monday = new Date(d);
  monday.setDate(d.getDate() + diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function fmtTime(t: string): string {
  return t.slice(0, 5);
}

function fmtDayHeader(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const dow = d.getDay();
  const dayIdx = dow === 0 ? 6 : dow - 1;
  return `${DAYS_ES[dayIdx].slice(0, 3)} ${d.getDate()} ${MONTHS_ES[d.getMonth()].slice(0, 3)}`;
}

function weekDays(monday: Date): string[] {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return toIsoDate(d);
  });
}

function weekLabel(monday: Date): string {
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const m1 = MONTHS_ES[monday.getMonth()].slice(0, 3);
  const m2 = MONTHS_ES[sunday.getMonth()].slice(0, 3);
  const same = monday.getMonth() === sunday.getMonth();
  return same
    ? `${monday.getDate()} – ${sunday.getDate()} ${m1} ${sunday.getFullYear()}`
    : `${monday.getDate()} ${m1} – ${sunday.getDate()} ${m2} ${sunday.getFullYear()}`;
}

// ---------------------------------------------------------------------------
// Shift card with signup action
// ---------------------------------------------------------------------------

interface ShiftCardProps {
  shift: Shift;
  isSignedUp: boolean;
  onSignup: (shiftId: string) => Promise<void>;
  onCancel: (shiftId: string) => Promise<void>;
  authenticated: boolean;
}

function ShiftCard({ shift, isSignedUp, onSignup, onCancel, authenticated }: ShiftCardProps) {
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const slotsLeft = shift.capacity - shift.slots_filled;
  const isFull = shift.status === "full";
  const isOpen = shift.status === "open";
  const isCancelled = shift.status === "cancelled";
  const isCompleted = shift.status === "completed";
  const canAct = authenticated && (isOpen || isSignedUp) && !isCancelled && !isCompleted;

  async function handleClick() {
    setLocalError(null);
    setBusy(true);
    try {
      if (isSignedUp) {
        await onCancel(shift.id);
      } else {
        await onSignup(shift.id);
      }
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

  return (
    <div
      className={`rounded-lg border bg-white p-3 shadow-sm transition-shadow hover:shadow-md ${
        isSignedUp ? "border-emerald-300 ring-1 ring-emerald-200" : "border-gray-200"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {shift.title && (
            <p className="truncate text-sm font-semibold text-gray-800">{shift.title}</p>
          )}
          <p className="text-xs text-gray-500">{ROLE_LABELS[shift.role] ?? shift.role}</p>
        </div>
        {isSignedUp && (
          <span className="shrink-0 flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
            <CheckCircle className="h-3 w-3" />
            {LABEL_SIGNED_UP}
          </span>
        )}
        {!isSignedUp && isFull && (
          <span className="shrink-0 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800">
            {LABEL_FULL}
          </span>
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {fmtTime(shift.start_time)} – {fmtTime(shift.end_time)}
        </span>
        <span className="flex items-center gap-1">
          <Users className="h-3 w-3" />
          {shift.slots_filled}/{shift.capacity}
          {!isFull && <span className="ml-1 text-gray-400">({slotsLeft} libre{slotsLeft !== 1 ? "s" : ""})</span>}
        </span>
      </div>

      {shift.location && (
        <p className="mt-1 flex items-center gap-1 truncate text-xs text-gray-400">
          <MapPin className="h-3 w-3 shrink-0" />
          {shift.location}
        </p>
      )}

      {shift.notes && (
        <p className="mt-1 line-clamp-2 text-xs text-gray-400">{shift.notes}</p>
      )}

      {localError && (
        <p className="mt-2 text-xs text-red-600">{localError}</p>
      )}

      {canAct && (
        <button
          onClick={handleClick}
          disabled={busy || (isFull && !isSignedUp)}
          className={`mt-3 w-full rounded-lg py-1.5 text-xs font-semibold transition-colors disabled:opacity-50 ${
            isSignedUp
              ? "border border-gray-300 text-gray-600 hover:bg-gray-50"
              : "bg-emerald-600 text-white hover:bg-emerald-700"
          }`}
        >
          {busy ? "..." : isSignedUp ? LABEL_CANCEL_SIGNUP : LABEL_SIGNUP}
        </button>
      )}

      {!authenticated && isOpen && (
        <p className="mt-2 text-xs text-gray-400 italic">{LABEL_LOGIN_REQUIRED}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function VolunteerShiftsPage() {
  const router = useRouter();
  const [monday, setMonday] = useState<Date>(() => getMondayOf(new Date()));
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [mySignupIds, setMySignupIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showMyShifts, setShowMyShifts] = useState(false);
  const [authenticated] = useState(() => isAuthenticated());

  const days = weekDays(monday);

  const loadShifts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dateFrom = toIsoDate(monday);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      const dateTo = toIsoDate(sunday);

      const [shiftsData, signupsData] = await Promise.all([
        api.get<PaginatedShiftList>(
          `/api/shifts?date_from=${dateFrom}&date_to=${dateTo}&page_size=100`
        ),
        authenticated
          ? api.get<MySignupsResponse>("/api/shifts/my-signups")
          : Promise.resolve({ items: [], total: 0 } as MySignupsResponse),
      ]);

      setShifts(shiftsData.items);
      setMySignupIds(new Set(signupsData.items.map((s: ShiftSignup) => s.shift_id)));
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [monday, authenticated]);

  useEffect(() => {
    loadShifts();
  }, [loadShifts]);

  async function handleSignup(shiftId: string) {
    if (!authenticated) {
      router.push("/login");
      return;
    }
    await api.post<ShiftSignup>(`/api/shifts/${shiftId}/signup`, {});
    setMySignupIds((prev) => new Set([...prev, shiftId]));
    setShifts((prev) =>
      prev.map((s) => {
        if (s.id !== shiftId) return s;
        const newFilled = s.slots_filled + 1;
        return {
          ...s,
          slots_filled: newFilled,
          status: newFilled >= s.capacity ? "full" : s.status,
        };
      })
    );
  }

  async function handleCancel(shiftId: string) {
    await api.delete(`/api/shifts/${shiftId}/signup`);
    setMySignupIds((prev) => {
      const next = new Set(prev);
      next.delete(shiftId);
      return next;
    });
    setShifts((prev) =>
      prev.map((s) => {
        if (s.id !== shiftId) return s;
        const newFilled = Math.max(s.slots_filled - 1, 0);
        return {
          ...s,
          slots_filled: newFilled,
          status: s.status === "full" && newFilled < s.capacity ? "open" : s.status,
        };
      })
    );
  }

  const displayedShifts = showMyShifts
    ? shifts.filter((s) => mySignupIds.has(s.id))
    : shifts.filter((s) => s.status === "open" || mySignupIds.has(s.id));

  const shiftsByDay = days.reduce<Record<string, Shift[]>>((acc, day) => {
    acc[day] = displayedShifts.filter((s) => s.shift_date === day);
    return acc;
  }, {});

  function prevWeek() {
    setMonday((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() - 7);
      return d;
    });
  }

  function nextWeek() {
    setMonday((prev) => {
      const d = new Date(prev);
      d.setDate(d.getDate() + 7);
      return d;
    });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <Calendar className="h-6 w-6 text-emerald-600" />
              <h1 className="text-xl font-bold text-gray-800">{LABEL_PAGE_TITLE}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadShifts}
              disabled={loading}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-40"
              aria-label="Actualizar"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
            </button>
            {!authenticated && (
              <button
                onClick={() => router.push("/login")}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
              >
                <LogIn className="h-4 w-4" />
                {LABEL_LOGIN}
              </button>
            )}
          </div>
        </div>

        {/* View toggle */}
        {authenticated && (
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => setShowMyShifts(false)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                !showMyShifts
                  ? "bg-emerald-600 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {LABEL_ALL_SHIFTS}
            </button>
            <button
              onClick={() => setShowMyShifts(true)}
              className={`flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                showMyShifts
                  ? "bg-emerald-600 text-white"
                  : "border border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              <CheckCircle className="h-3.5 w-3.5" />
              {LABEL_MY_SIGNUPS}
              {mySignupIds.size > 0 && (
                <span className={`ml-1 rounded-full px-1.5 text-xs font-bold ${
                  showMyShifts ? "bg-white/20 text-white" : "bg-emerald-100 text-emerald-700"
                }`}>
                  {mySignupIds.size}
                </span>
              )}
            </button>
          </div>
        )}

        {/* Week navigation */}
        <div className="mt-3 flex items-center gap-3">
          <button
            onClick={prevWeek}
            className="rounded-lg border border-gray-200 p-1.5 text-gray-600 hover:bg-gray-50"
            aria-label={LABEL_PREV_WEEK}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="min-w-[200px] text-center text-sm font-medium text-gray-700">
            {weekLabel(monday)}
          </span>
          <button
            onClick={nextWeek}
            className="rounded-lg border border-gray-200 p-1.5 text-gray-600 hover:bg-gray-50"
            aria-label={LABEL_NEXT_WEEK}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 sm:p-6">
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
              onClick={loadShifts}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
            {days.map((day) => {
              const dayShifts = shiftsByDay[day] ?? [];
              return (
                <div key={day} className="min-w-0">
                  <h3 className="mb-2 text-sm font-semibold text-gray-700">
                    {fmtDayHeader(day)}
                  </h3>
                  <div className="space-y-2">
                    {dayShifts.length === 0 ? (
                      <div className="rounded-lg border border-dashed border-gray-200 py-6 text-center text-xs text-gray-400">
                        {LABEL_NO_SHIFTS}
                      </div>
                    ) : (
                      dayShifts.map((shift) => (
                        <ShiftCard
                          key={shift.id}
                          shift={shift}
                          isSignedUp={mySignupIds.has(shift.id)}
                          onSignup={handleSignup}
                          onCancel={handleCancel}
                          authenticated={authenticated}
                        />
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
