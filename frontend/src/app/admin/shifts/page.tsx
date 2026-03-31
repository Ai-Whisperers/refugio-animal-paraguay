"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  Users,
  RefreshCw,
  X,
  ArrowLeft,
  ChevronRight as ChevronRightSm,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { Shift, PaginatedShiftList, ShiftCreateRequest, ShiftRole } from "@/types/api";

// ---------------------------------------------------------------------------
// Constants & labels
// ---------------------------------------------------------------------------

const LABEL_PAGE_TITLE = "Turnos de Voluntarios";
const LABEL_BACK = "Volver al panel";
const LABEL_PREV_WEEK = "Semana anterior";
const LABEL_NEXT_WEEK = "Semana siguiente";
const LABEL_NEW_SHIFT = "Nuevo turno";
const LABEL_LOADING = "Cargando turnos...";
const LABEL_ERROR = "Error al cargar turnos";
const LABEL_RETRY = "Reintentar";
const LABEL_NO_SHIFTS = "Sin turnos esta semana";
const LABEL_CAPACITY = "Capacidad";
const LABEL_SLOTS_OPEN = "lugares disponibles";
const LABEL_SLOTS_FULL = "Completo";

const DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

const MONTHS_ES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
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

const STATUS_COLORS: Record<string, string> = {
  open: "bg-green-100 text-green-800",
  full: "bg-orange-100 text-orange-800",
  cancelled: "bg-red-100 text-red-700",
  completed: "bg-gray-100 text-gray-600",
};

const STATUS_LABELS_ES: Record<string, string> = {
  open: "Disponible",
  full: "Completo",
  cancelled: "Cancelado",
  completed: "Completado",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Get the Monday of the week containing `d`. */
function getMondayOf(d: Date): Date {
  const day = d.getDay(); // 0 = Sunday
  const diff = day === 0 ? -6 : 1 - day;
  const monday = new Date(d);
  monday.setDate(d.getDate() + diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

/** Format a Date as YYYY-MM-DD. */
function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/** Format time HH:MM:SS to HH:MM. */
function fmtTime(t: string): string {
  return t.slice(0, 5);
}

/** Format date string as "Lun 28 mar". */
function fmtDayHeader(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  const dow = d.getDay();
  const dayIdx = dow === 0 ? 6 : dow - 1;
  return `${DAYS_ES[dayIdx].slice(0, 3)} ${d.getDate()} ${MONTHS_ES[d.getMonth()].slice(0, 3)}`;
}

/** Build ISO date for each day of the week starting Monday. */
function weekDays(monday: Date): string[] {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return toIsoDate(d);
  });
}

/** Format week range label e.g. "28 mar – 3 abr 2026". */
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
// Sub-components
// ---------------------------------------------------------------------------

interface ShiftCardProps {
  shift: Shift;
}

function ShiftCard({ shift }: ShiftCardProps) {
  const slotsLeft = shift.capacity - shift.slots_filled;
  return (
    <Link
      href={`/admin/shifts/${shift.id}`}
      className="block rounded-lg border border-gray-200 bg-white p-3 shadow-sm hover:shadow-md transition-shadow hover:border-emerald-300"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {shift.title && (
            <p className="truncate text-sm font-semibold text-gray-800">{shift.title}</p>
          )}
          <p className="text-xs text-gray-500">
            {ROLE_LABELS[shift.role] ?? shift.role}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
            STATUS_COLORS[shift.status] ?? "bg-gray-100 text-gray-600"
          }`}
        >
          {STATUS_LABELS_ES[shift.status] ?? shift.status}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {fmtTime(shift.start_time)} – {fmtTime(shift.end_time)}
        </span>
        <span className="flex items-center gap-1">
          <Users className="h-3 w-3" />
          {shift.slots_filled}/{shift.capacity}{" "}
          {shift.status === "full" ? (
            <span className="font-medium text-orange-600">{LABEL_SLOTS_FULL}</span>
          ) : (
            <span>{slotsLeft} {LABEL_SLOTS_OPEN}</span>
          )}
        </span>
      </div>
      {shift.location && (
        <p className="mt-1 truncate text-xs text-gray-400">{shift.location}</p>
      )}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// New Shift Modal
// ---------------------------------------------------------------------------

const SHIFT_ROLES: { value: ShiftRole; label: string }[] = Object.entries(ROLE_LABELS).map(
  ([value, label]) => ({ value: value as ShiftRole, label })
);

interface CreateShiftModalProps {
  defaultDate: string;
  onClose: () => void;
  onCreated: () => void;
}

function CreateShiftModal({ defaultDate, onClose, onCreated }: CreateShiftModalProps) {
  const [date, setDate] = useState(defaultDate);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("13:00");
  const [role, setRole] = useState<ShiftRole>("general");
  const [capacity, setCapacity] = useState(1);
  const [title, setTitle] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const body: ShiftCreateRequest = {
        shift_date: date,
        start_time: startTime + ":00",
        end_time: endTime + ":00",
        role,
        capacity,
        title: title.trim() || null,
        location: location.trim() || null,
        notes: notes.trim() || null,
      };
      await api.post("/api/shifts", body);
      onCreated();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || "Error al crear el turno");
      } else {
        setError("Error inesperado");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Crear nuevo turno</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Fecha</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Hora inicio</label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Hora fin</label>
              <input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Tipo de tarea</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as ShiftRole)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            >
              {SHIFT_ROLES.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Capacidad (voluntarios)
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value))}
              required
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Título (opcional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              placeholder="Ej: Turno mañana — limpieza kennels"
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Lugar (opcional)
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              maxLength={200}
              placeholder="Ej: Bloque A, Refugio Central"
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Notas (opcional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Instrucciones especiales para los voluntarios..."
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Crear turno"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ShiftsPage() {
  const router = useRouter();
  const [monday, setMonday] = useState<Date>(() => getMondayOf(new Date()));
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createDefaultDate, setCreateDefaultDate] = useState<string>("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
    }
  }, [router]);

  const days = weekDays(monday);

  const loadShifts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dateFrom = toIsoDate(monday);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      const dateTo = toIsoDate(sunday);

      const data = await api.get<PaginatedShiftList>(
        `/api/shifts?date_from=${dateFrom}&date_to=${dateTo}&page_size=100`
      );
      setShifts(data.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [monday]);

  useEffect(() => {
    loadShifts();
  }, [loadShifts]);

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

  function openCreateForDay(dayIso: string) {
    setCreateDefaultDate(dayIso);
    setShowCreate(true);
  }

  function handleCreated() {
    setShowCreate(false);
    loadShifts();
  }

  const shiftsByDay = days.reduce<Record<string, Shift[]>>((acc, day) => {
    acc[day] = shifts.filter((s) => s.shift_date === day);
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin")}
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
            <button
              onClick={() => openCreateForDay(toIsoDate(new Date()))}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              <Plus className="h-4 w-4" />
              {LABEL_NEW_SHIFT}
            </button>
          </div>
        </div>

        {/* Week navigation */}
        <div className="mt-3 flex items-center gap-3">
          <button
            onClick={prevWeek}
            className="rounded-lg border border-gray-200 p-1.5 text-gray-600 hover:bg-gray-50"
            aria-label={LABEL_PREV_WEEK}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="min-w-[220px] text-center text-sm font-medium text-gray-700">
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
      <div className="p-6">
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
                  {/* Day header */}
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">
                      {fmtDayHeader(day)}
                    </h3>
                    <button
                      onClick={() => openCreateForDay(day)}
                      className="rounded p-0.5 text-gray-400 hover:bg-emerald-50 hover:text-emerald-600"
                      aria-label={`Agregar turno ${day}`}
                      title="Agregar turno"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Shifts */}
                  <div className="space-y-2">
                    {dayShifts.length === 0 ? (
                      <div className="rounded-lg border border-dashed border-gray-200 py-6 text-center text-xs text-gray-400">
                        {LABEL_NO_SHIFTS}
                      </div>
                    ) : (
                      dayShifts.map((shift) => (
                        <ShiftCard key={shift.id} shift={shift} />
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create shift modal */}
      {showCreate && (
        <CreateShiftModal
          defaultDate={createDefaultDate}
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
