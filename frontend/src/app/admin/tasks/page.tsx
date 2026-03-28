"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  CheckSquare,
  Plus,
  RefreshCw,
  ArrowLeft,
  X,
  AlertCircle,
  Clock,
  ChevronDown,
  UserPlus,
  User,
  ClipboardCheck,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type {
  Task,
  TaskCategory,
  TaskPriority,
  TaskStatus,
  TaskListResponse,
  TaskCreateRequest,
  VolunteerListItem,
  PaginatedVolunteerList,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Constants & labels
// ---------------------------------------------------------------------------

const LABEL_PAGE_TITLE = "Tareas del Refugio";
const LABEL_BACK = "Volver al panel";
const LABEL_NEW_TASK = "Nueva tarea";
const LABEL_LOADING = "Cargando tareas...";
const LABEL_ERROR = "Error al cargar tareas";
const LABEL_RETRY = "Reintentar";
const LABEL_NO_TASKS = "Sin tareas";
const LABEL_FILTER_ALL = "Todas las categorías";
const LABEL_FILTER_PRIORITY = "Todas las prioridades";
const LABEL_UNASSIGNED = "Sin asignar";
const LABEL_REASSIGN = "Reasignar";
const LABEL_COMPLETE = "Completar";

const STATUS_COLUMNS: { status: TaskStatus; label: string; color: string; headerBg: string }[] = [
  {
    status: "pending",
    label: "Pendiente",
    color: "bg-yellow-100 text-yellow-800",
    headerBg: "bg-yellow-50 border-yellow-200",
  },
  {
    status: "in_progress",
    label: "En Progreso",
    color: "bg-blue-100 text-blue-800",
    headerBg: "bg-blue-50 border-blue-200",
  },
  {
    status: "completed",
    label: "Completado",
    color: "bg-green-100 text-green-800",
    headerBg: "bg-green-50 border-green-200",
  },
  {
    status: "cancelled",
    label: "Cancelado",
    color: "bg-gray-100 text-gray-600",
    headerBg: "bg-gray-50 border-gray-200",
  },
];

const CATEGORY_LABELS: Record<TaskCategory, string> = {
  feeding: "Alimentación",
  cleaning: "Limpieza",
  walking: "Paseo",
  socialization: "Socialización",
  veterinary_assistance: "Asistencia veterinaria",
  transport: "Transporte",
  admin: "Administración",
  other: "Otro",
};

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  urgent: "Urgente",
  high: "Alta",
  medium: "Media",
  low: "Baja",
};

const PRIORITY_COLORS: Record<TaskPriority, string> = {
  urgent: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-gray-100 text-gray-600 border-gray-200",
};

const CATEGORY_OPTIONS: TaskCategory[] = [
  "feeding",
  "cleaning",
  "walking",
  "socialization",
  "veterinary_assistance",
  "transport",
  "admin",
  "other",
];

const PRIORITY_OPTIONS: TaskPriority[] = ["urgent", "high", "medium", "low"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PY", { day: "2-digit", month: "short", year: "numeric" });
}

function isDueSoon(dueDate: string | null): boolean {
  if (!dueDate) return false;
  const due = new Date(dueDate);
  const now = new Date();
  const diffHours = (due.getTime() - now.getTime()) / (1000 * 60 * 60);
  return diffHours >= 0 && diffHours <= 24;
}

function isOverdue(dueDate: string | null, status: TaskStatus): boolean {
  if (!dueDate || status === "completed" || status === "cancelled") return false;
  return new Date(dueDate) < new Date();
}

function volunteerDisplayName(v: VolunteerListItem): string {
  return v.full_name ?? v.email;
}

// ---------------------------------------------------------------------------
// Task Card
// ---------------------------------------------------------------------------

interface TaskCardProps {
  task: Task;
  volunteers: VolunteerListItem[];
  onStatusChange: (taskId: string, newStatus: TaskStatus) => Promise<void>;
  onReassign: (task: Task) => void;
  onComplete: (task: Task) => void;
}

function TaskCard({ task, volunteers, onStatusChange, onReassign, onComplete }: TaskCardProps) {
  const [updating, setUpdating] = useState(false);

  const nextStatusOptions = STATUS_COLUMNS.filter(
    (col) => col.status !== task.status && col.status !== "completed"
  ).map((col) => ({ status: col.status, label: col.label }));

  async function handleStatusChange(newStatus: TaskStatus) {
    setUpdating(true);
    try {
      await onStatusChange(task.id, newStatus);
    } finally {
      setUpdating(false);
    }
  }

  const overdue = isOverdue(task.due_date, task.status);
  const dueSoon = isDueSoon(task.due_date);

  const assignedVolunteer = task.assigned_to
    ? volunteers.find((v) => v.user_id === task.assigned_to)
    : null;

  return (
    <div
      className={`rounded-lg border bg-white p-3 shadow-sm transition-shadow hover:shadow-md ${
        overdue ? "border-red-300" : "border-gray-200"
      }`}
    >
      {/* Title + priority badge */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold leading-snug text-gray-800 line-clamp-2">
          {task.title}
        </p>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium ${
            PRIORITY_COLORS[task.priority]
          }`}
        >
          {PRIORITY_LABELS[task.priority]}
        </span>
      </div>

      {/* Category */}
      <p className="mt-1 text-xs text-gray-500">{CATEGORY_LABELS[task.category]}</p>

      {/* Description (truncated) */}
      {task.description && (
        <p className="mt-1.5 text-xs text-gray-400 line-clamp-2">{task.description}</p>
      )}

      {/* Assignee row */}
      <div className="mt-2 flex items-center justify-between gap-1">
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <User className="h-3 w-3 shrink-0 text-gray-400" />
          <span className={assignedVolunteer ? "text-gray-700" : "text-gray-400 italic"}>
            {assignedVolunteer
              ? volunteerDisplayName(assignedVolunteer)
              : LABEL_UNASSIGNED}
          </span>
        </div>
        {task.status !== "completed" && task.status !== "cancelled" && (
          <button
            onClick={() => onReassign(task)}
            className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-xs text-gray-400 hover:bg-blue-50 hover:text-blue-600"
            title={LABEL_REASSIGN}
          >
            <UserPlus className="h-3 w-3" />
            {LABEL_REASSIGN}
          </button>
        )}
      </div>

      {/* Due date */}
      {task.due_date && (
        <div
          className={`mt-1.5 flex items-center gap-1 text-xs ${
            overdue
              ? "font-medium text-red-600"
              : dueSoon
              ? "font-medium text-orange-500"
              : "text-gray-400"
          }`}
        >
          <Clock className="h-3 w-3" />
          {overdue ? "Vencida: " : dueSoon ? "Vence hoy: " : ""}
          {fmtDate(task.due_date)}
        </div>
      )}

      {/* Status change dropdown + complete button */}
      {task.status !== "completed" && task.status !== "cancelled" && (
        <div className="mt-2.5 flex gap-1.5">
          {/* Move to non-completed statuses */}
          {nextStatusOptions.length > 0 && (
            <div className="relative flex-1">
              <select
                disabled={updating}
                value=""
                onChange={(e) => {
                  if (e.target.value) handleStatusChange(e.target.value as TaskStatus);
                }}
                className="w-full appearance-none rounded border border-gray-200 bg-gray-50 py-1 pl-2 pr-6 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-50 cursor-pointer"
                aria-label="Cambiar estado"
              >
                <option value="" disabled>
                  {updating ? "..." : "Mover a..."}
                </option>
                {nextStatusOptions.map((opt) => (
                  <option key={opt.status} value={opt.status}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-gray-400" />
            </div>
          )}
          {/* Complete button — opens notes modal */}
          <button
            onClick={() => onComplete(task)}
            disabled={updating}
            className="flex shrink-0 items-center gap-1 rounded border border-green-200 bg-green-50 px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
            title={LABEL_COMPLETE}
          >
            <ClipboardCheck className="h-3 w-3" />
            {LABEL_COMPLETE}
          </button>
        </div>
      )}

      {/* Completion timestamp + notes */}
      {task.status === "completed" && (
        <div className="mt-1.5 space-y-0.5">
          {task.completed_at && (
            <p className="text-xs text-green-600">Completado: {fmtDate(task.completed_at)}</p>
          )}
          {task.completion_notes && (
            <p className="rounded bg-green-50 px-2 py-1 text-xs text-green-700 italic line-clamp-3">
              {task.completion_notes}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Assign Volunteer Modal
// ---------------------------------------------------------------------------

interface AssignModalProps {
  task: Task;
  volunteers: VolunteerListItem[];
  onClose: () => void;
  onAssigned: (taskId: string, userId: string | null) => Promise<void>;
}

function AssignModal({ task, volunteers, onClose, onAssigned }: AssignModalProps) {
  const currentAssignee = task.assigned_to
    ? volunteers.find((v) => v.user_id === task.assigned_to)
    : null;

  const [selected, setSelected] = useState<string>(task.assigned_to ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onAssigned(task.id, selected || null);
      onClose();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || "Error al asignar la tarea");
      } else {
        setError("Error inesperado");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-800">Asignar voluntario</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-3 text-xs text-gray-500 line-clamp-2">
          Tarea: <span className="font-medium text-gray-700">{task.title}</span>
        </p>

        {currentAssignee && (
          <p className="mb-3 text-xs text-gray-500">
            Asignado actualmente:{" "}
            <span className="font-medium text-blue-700">
              {volunteerDisplayName(currentAssignee)}
            </span>
          </p>
        )}

        {error && (
          <div className="mb-3 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Voluntario</label>
            {volunteers.length === 0 ? (
              <p className="mt-1 text-sm text-gray-400 italic">
                No hay voluntarios aprobados disponibles.
              </p>
            ) : (
              <select
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              >
                <option value="">{LABEL_UNASSIGNED}</option>
                {volunteers.map((v) => (
                  <option key={v.user_id} value={v.user_id}>
                    {volunteerDisplayName(v)} — {v.email}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving || volunteers.length === 0}
              className="flex-1 rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Complete Task Modal
// ---------------------------------------------------------------------------

interface CompleteTaskModalProps {
  task: Task;
  onClose: () => void;
  onCompleted: (taskId: string, notes: string | null) => Promise<void>;
}

function CompleteTaskModal({ task, onClose, onCompleted }: CompleteTaskModalProps) {
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onCompleted(task.id, notes.trim() || null);
      onClose();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || "Error al completar la tarea");
      } else {
        setError("Error inesperado");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-800">Completar tarea</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="mb-3 text-xs text-gray-500 line-clamp-2">
          <span className="font-medium text-gray-700">{task.title}</span>
        </p>

        {error && (
          <div className="mb-3 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Notas de cierre (opcional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              maxLength={2000}
              placeholder="Describe cómo se completó la tarea, observaciones, etc."
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <p className="mt-0.5 text-right text-xs text-gray-400">{notes.length}/2000</p>
          </div>

          <div className="flex gap-3 pt-1">
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
              className="flex-1 rounded-lg bg-green-600 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Marcar completa"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Create Task Modal
// ---------------------------------------------------------------------------

interface CreateTaskModalProps {
  volunteers: VolunteerListItem[];
  onClose: () => void;
  onCreated: () => void;
}

function CreateTaskModal({ volunteers, onClose, onCreated }: CreateTaskModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<TaskCategory>("other");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [dueDate, setDueDate] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const body: TaskCreateRequest = {
        title: title.trim(),
        description: description.trim() || null,
        category,
        priority,
        assigned_to: assignedTo || null,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
      };
      await api.post("/api/tasks", body);
      onCreated();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || "Error al crear la tarea");
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
          <h2 className="text-lg font-semibold text-gray-800">Crear nueva tarea</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Título *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              placeholder="Ej: Alimentar perros bloque A"
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Descripción (opcional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="Detalles adicionales..."
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Categoría</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as TaskCategory)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {CATEGORY_LABELS[c]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Prioridad</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as TaskPriority)}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              >
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {PRIORITY_LABELS[p]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Asignar a voluntario (opcional)
            </label>
            <select
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
            >
              <option value="">{LABEL_UNASSIGNED}</option>
              {volunteers.map((v) => (
                <option key={v.user_id} value={v.user_id}>
                  {volunteerDisplayName(v)} — {v.email}
                </option>
              ))}
            </select>
            {volunteers.length === 0 && (
              <p className="mt-1 text-xs text-gray-400 italic">
                No hay voluntarios aprobados.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fecha límite (opcional)
            </label>
            <input
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
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
              {saving ? "Guardando..." : "Crear tarea"}
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

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [volunteers, setVolunteers] = useState<VolunteerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [reassignTask, setReassignTask] = useState<Task | null>(null);
  const [completeTask, setCompleteTask] = useState<Task | null>(null);
  const [filterCategory, setFilterCategory] = useState<TaskCategory | "">("");
  const [filterPriority, setFilterPriority] = useState<TaskPriority | "">("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
    }
  }, [router]);

  const loadVolunteers = useCallback(async () => {
    try {
      const data = await api.get<PaginatedVolunteerList>(
        "/api/volunteers?status=approved&page_size=100"
      );
      setVolunteers(data.items);
    } catch {
      // Non-fatal: tasks board still works without volunteer data
      setVolunteers([]);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page_size: "200" });
      if (filterCategory) params.set("category", filterCategory);
      if (filterPriority) params.set("priority", filterPriority);
      const data = await api.get<TaskListResponse>(`/api/tasks?${params.toString()}`);
      setTasks(data.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [filterCategory, filterPriority]);

  useEffect(() => {
    loadVolunteers();
    loadTasks();
  }, [loadVolunteers, loadTasks]);

  async function handleStatusChange(taskId: string, newStatus: TaskStatus) {
    try {
      await api.patch(`/api/tasks/${taskId}`, { status: newStatus });
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId
            ? {
                ...t,
                status: newStatus,
                completed_at: newStatus === "completed" ? new Date().toISOString() : null,
              }
            : t
        )
      );
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || "Error al actualizar la tarea");
      } else {
        setError("Error inesperado al actualizar");
      }
    }
  }

  async function handleAssign(taskId: string, userId: string | null) {
    await api.patch(`/api/tasks/${taskId}`, { assigned_to: userId });
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, assigned_to: userId } : t))
    );
  }

  async function handleComplete(taskId: string, notes: string | null) {
    await api.patch(`/api/tasks/${taskId}`, {
      status: "completed",
      completion_notes: notes,
    });
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? {
              ...t,
              status: "completed" as TaskStatus,
              completed_at: new Date().toISOString(),
              completion_notes: notes,
            }
          : t
      )
    );
  }

  function handleCreated() {
    setShowCreate(false);
    loadTasks();
  }

  const tasksByStatus = STATUS_COLUMNS.reduce<Record<TaskStatus, Task[]>>(
    (acc, col) => {
      acc[col.status] = tasks.filter((t) => t.status === col.status);
      return acc;
    },
    { pending: [], in_progress: [], completed: [], cancelled: [] }
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin")}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <CheckSquare className="h-6 w-6 text-emerald-600" />
              <h1 className="text-xl font-bold text-gray-800">{LABEL_PAGE_TITLE}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => { loadTasks(); loadVolunteers(); }}
              disabled={loading}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 disabled:opacity-40"
              aria-label="Actualizar"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              <Plus className="h-4 w-4" />
              {LABEL_NEW_TASK}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-3 flex flex-wrap gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as TaskCategory | "")}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none"
          >
            <option value="">{LABEL_FILTER_ALL}</option>
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABELS[c]}
              </option>
            ))}
          </select>

          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value as TaskPriority | "")}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none"
          >
            <option value="">{LABEL_FILTER_PRIORITY}</option>
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {PRIORITY_LABELS[p]}
              </option>
            ))}
          </select>

          {(filterCategory || filterPriority) && (
            <button
              onClick={() => { setFilterCategory(""); setFilterPriority(""); }}
              className="flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-50"
            >
              <X className="h-3.5 w-3.5" />
              Limpiar filtros
            </button>
          )}
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
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              {error}
            </div>
            <button
              onClick={loadTasks}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {STATUS_COLUMNS.map((col) => {
              const colTasks = tasksByStatus[col.status];
              return (
                <div key={col.status} className="flex flex-col gap-2">
                  {/* Column header */}
                  <div
                    className={`flex items-center justify-between rounded-lg border px-3 py-2 ${col.headerBg}`}
                  >
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${col.color}`}>
                      {col.label}
                    </span>
                    <span className="text-xs font-medium text-gray-500">{colTasks.length}</span>
                  </div>

                  {/* Task cards */}
                  <div className="flex flex-col gap-2">
                    {colTasks.length === 0 ? (
                      <div className="rounded-lg border border-dashed border-gray-200 py-8 text-center text-xs text-gray-400">
                        {LABEL_NO_TASKS}
                      </div>
                    ) : (
                      colTasks.map((task) => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          volunteers={volunteers}
                          onStatusChange={handleStatusChange}
                          onReassign={setReassignTask}
                          onComplete={setCompleteTask}
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

      {/* Create modal */}
      {showCreate && (
        <CreateTaskModal
          volunteers={volunteers}
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}

      {/* Assign modal */}
      {reassignTask && (
        <AssignModal
          task={reassignTask}
          volunteers={volunteers}
          onClose={() => setReassignTask(null)}
          onAssigned={handleAssign}
        />
      )}

      {/* Complete modal */}
      {completeTask && (
        <CompleteTaskModal
          task={completeTask}
          onClose={() => setCompleteTask(null)}
          onCompleted={handleComplete}
        />
      )}
    </div>
  );
}
