"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  ArrowLeft,
  RefreshCw,
  Search,
  X,
  Clock,
  CheckCircle,
  UserMinus,
  Mail,
  Phone,
  Star,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { VolunteerListItem, VolunteerStatus, PaginatedVolunteerList } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Directorio de Voluntarios";
const LABEL_SUBTITLE = "Voluntarios activos del refugio";
const LABEL_LOADING = "Cargando directorio...";
const LABEL_ERROR = "Error al cargar el directorio";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a solicitudes";
const LABEL_SEARCH_PLACEHOLDER = "Buscar por nombre o correo...";
const LABEL_FILTER_SKILL = "Filtrar por habilidad";
const LABEL_FILTER_AVAILABILITY = "Filtrar por disponibilidad";
const LABEL_FILTER_STATUS = "Estado";
const LABEL_ALL_SKILLS = "Todas las habilidades";
const LABEL_ALL_AVAILABILITY = "Cualquier disponibilidad";
const LABEL_ALL_STATUSES = "Aprobados e inactivos";
const LABEL_APPROVED_ONLY = "Solo aprobados";
const LABEL_INACTIVE_ONLY = "Solo inactivos";
const LABEL_EMPTY = "No hay voluntarios en el directorio";
const LABEL_EMPTY_FILTERED = "Ningun voluntario coincide con los filtros";
const LABEL_VIEW = "Ver perfil";
const LABEL_CLEAR_FILTERS = "Limpiar filtros";
const LABEL_TOTAL = "voluntarios encontrados";
const LABEL_HOURS_WEEK = "h/sem";
const LABEL_HOURS_TOTAL = "h totales";

const DIRECTORY_PAGE_SIZE = 100;

// --- Availability labels (Spanish) ---
const AVAILABILITY_LABELS: Record<string, string> = {
  weekday_mornings: "Dias habiles manana",
  weekday_afternoons: "Dias habiles tarde",
  weekday_evenings: "Dias habiles noche",
  weekend_mornings: "Fines de semana manana",
  weekend_afternoons: "Fines de semana tarde",
  flexible: "Flexible",
};

// --- Skill labels (Spanish) ---
const SKILL_LABELS: Record<string, string> = {
  animal_care: "Cuidado animal",
  veterinary_assistance: "Asistencia veterinaria",
  photography: "Fotografia",
  social_media: "Redes sociales",
  transport_driving: "Transporte / manejo",
  fundraising: "Recaudacion de fondos",
  admin_office: "Administracion",
  cleaning: "Limpieza",
  construction_maintenance: "Construccion y mantenimiento",
  education_outreach: "Educacion y difusion",
  translation: "Traduccion",
  web_tech: "Web y tecnologia",
  event_coordination: "Coordinacion de eventos",
};

// --- Status config ---
const STATUS_LABELS: Record<VolunteerStatus, string> = {
  pending: "Pendiente",
  approved: "Aprobado",
  rejected: "Rechazado",
  inactive: "Inactivo",
};

const STATUS_COLORS: Record<VolunteerStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  inactive: "bg-gray-100 text-gray-700",
};

const STATUS_ICONS: Record<VolunteerStatus, React.ComponentType<{ className?: string }>> = {
  pending: Clock,
  approved: CheckCircle,
  rejected: X,
  inactive: UserMinus,
};

type StatusFilter = "all" | "approved" | "inactive";

interface DirectoryFilters {
  search: string;
  skill: string;
  availability: string;
  statusFilter: StatusFilter;
}

function StatusBadge({ status }: { status: VolunteerStatus }) {
  const Icon = STATUS_ICONS[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
    >
      <Icon className="h-3 w-3" />
      {STATUS_LABELS[status]}
    </span>
  );
}

function SkillTag({ skill }: { skill: string }) {
  return (
    <span className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
      {SKILL_LABELS[skill] ?? skill.replace(/_/g, " ")}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function extractAllSkills(volunteers: VolunteerListItem[]): string[] {
  const skillSet = new Set<string>();
  for (const v of volunteers) {
    for (const s of v.skills) {
      skillSet.add(s);
    }
  }
  return Array.from(skillSet).sort();
}

function VolunteerCard({
  volunteer,
  onView,
}: {
  volunteer: VolunteerListItem;
  onView: (id: string) => void;
}) {
  const initials = volunteer.full_name
    ? volunteer.full_name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-4 hover:shadow-sm transition-shadow">
      {/* Header row: avatar + name + status */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[var(--color-primary)] text-sm font-semibold text-white">
            {initials}
          </div>
          <div>
            <p className="font-medium text-[var(--color-text-primary)]">
              {volunteer.full_name ?? "Sin nombre"}
            </p>
            <p className="flex items-center gap-1 text-xs text-[var(--color-text-secondary)]">
              <Mail className="h-3 w-3" />
              {volunteer.email}
            </p>
          </div>
        </div>
        <StatusBadge status={volunteer.status} />
      </div>

      {/* Skills */}
      {volunteer.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {volunteer.skills.map((s) => (
            <SkillTag key={s} skill={s} />
          ))}
        </div>
      )}

      {/* Stats row */}
      <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
        {volunteer.hours_per_week != null && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {volunteer.hours_per_week}
            {LABEL_HOURS_WEEK}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Star className="h-3 w-3" />
          {formatDate(volunteer.created_at)}
        </span>
      </div>

      {/* Action */}
      <button
        onClick={() => onView(volunteer.id)}
        className="mt-1 w-full rounded bg-[var(--color-primary)] py-1.5 text-xs font-medium text-white hover:opacity-90 transition-opacity"
      >
        {LABEL_VIEW}
      </button>
    </div>
  );
}

export default function VolunteerDirectoryPage() {
  const router = useRouter();
  const [volunteers, setVolunteers] = useState<VolunteerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DirectoryFilters>({
    search: "",
    skill: "",
    availability: "",
    statusFilter: "all",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Load approved volunteers
      const approvedData = await api.get<PaginatedVolunteerList>(
        `/api/staff/volunteers?status=approved&page=1&page_size=${DIRECTORY_PAGE_SIZE}`
      );
      // Load inactive volunteers
      const inactiveData = await api.get<PaginatedVolunteerList>(
        `/api/staff/volunteers?status=inactive&page=1&page_size=${DIRECTORY_PAGE_SIZE}`
      );
      setVolunteers([...approvedData.items, ...inactiveData.items]);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    load();
    // router intentionally omitted: redirect is a one-time mount action, not reactive
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  // All skills present in the loaded data (for filter dropdown)
  const allSkills = useMemo(() => extractAllSkills(volunteers), [volunteers]);

  // Client-side filtering
  const filtered = useMemo(() => {
    return volunteers.filter((v) => {
      // Status filter
      if (filters.statusFilter === "approved" && v.status !== "approved") return false;
      if (filters.statusFilter === "inactive" && v.status !== "inactive") return false;

      // Search filter
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        const nameMatch = (v.full_name ?? "").toLowerCase().includes(q);
        const emailMatch = v.email.toLowerCase().includes(q);
        if (!nameMatch && !emailMatch) return false;
      }

      // Skill filter
      if (filters.skill && !v.skills.includes(filters.skill)) return false;

      return true;
    });
  }, [volunteers, filters]);

  const hasActiveFilters =
    filters.search !== "" || filters.skill !== "" || filters.availability !== "" || filters.statusFilter !== "all";

  const clearFilters = () => {
    setFilters({ search: "", skill: "", availability: "", statusFilter: "all" });
  };

  const isEmpty = !loading && !error && filtered.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/volunteers")}
            className="flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">{LABEL_BACK}</span>
          </button>
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold text-[var(--color-text-primary)]">
              <Users className="h-5 w-5 text-[var(--color-primary)]" />
              {LABEL_PAGE_TITLE}
            </h1>
            <p className="text-sm text-[var(--color-text-secondary)]">{LABEL_SUBTITLE}</p>
          </div>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1 rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-bg-secondary)] transition-colors"
          aria-label={LABEL_RETRY}
        >
          <RefreshCw className="h-4 w-4" />
          <span>Actualizar</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-4 sm:flex-row sm:items-end sm:flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-secondary)]" />
          <input
            type="text"
            placeholder={LABEL_SEARCH_PLACEHOLDER}
            value={filters.search}
            onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-primary)] py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            aria-label={LABEL_SEARCH_PLACEHOLDER}
          />
        </div>

        {/* Skill filter */}
        <div className="min-w-[180px]">
          <label className="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]">
            {LABEL_FILTER_SKILL}
          </label>
          <select
            value={filters.skill}
            onChange={(e) => setFilters((f) => ({ ...f, skill: e.target.value }))}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-primary)] py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            aria-label={LABEL_FILTER_SKILL}
          >
            <option value="">{LABEL_ALL_SKILLS}</option>
            {allSkills.map((s) => (
              <option key={s} value={s}>
                {SKILL_LABELS[s] ?? s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Status filter */}
        <div className="min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-[var(--color-text-secondary)]">
            {LABEL_FILTER_STATUS}
          </label>
          <select
            value={filters.statusFilter}
            onChange={(e) =>
              setFilters((f) => ({ ...f, statusFilter: e.target.value as StatusFilter }))
            }
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-primary)] py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            aria-label={LABEL_FILTER_STATUS}
          >
            <option value="all">{LABEL_ALL_STATUSES}</option>
            <option value="approved">{LABEL_APPROVED_ONLY}</option>
            <option value="inactive">{LABEL_INACTIVE_ONLY}</option>
          </select>
        </div>

        {/* Clear filters */}
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-md border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-primary)] transition-colors"
          >
            <X className="h-4 w-4" />
            {LABEL_CLEAR_FILTERS}
          </button>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="py-12 text-center text-[var(--color-text-secondary)]">{LABEL_LOADING}</div>
      )}

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p className="font-medium">{LABEL_ERROR}</p>
          <p className="mt-1">{error}</p>
          <button onClick={load} className="mt-2 text-red-600 underline hover:text-red-800">
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Results count */}
      {!loading && !error && volunteers.length > 0 && (
        <p className="text-sm text-[var(--color-text-secondary)]">
          {filtered.length} {LABEL_TOTAL}
        </p>
      )}

      {/* Empty state */}
      {isEmpty && (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] py-12 text-center">
          <Users className="mx-auto mb-3 h-10 w-10 text-[var(--color-text-secondary)]" />
          <p className="text-[var(--color-text-secondary)]">
            {hasActiveFilters ? LABEL_EMPTY_FILTERED : LABEL_EMPTY}
          </p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-3 text-sm text-[var(--color-primary)] underline hover:opacity-80"
            >
              {LABEL_CLEAR_FILTERS}
            </button>
          )}
        </div>
      )}

      {/* Volunteer grid */}
      {!loading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((v) => (
            <VolunteerCard
              key={v.id}
              volunteer={v}
              onView={(id) => router.push(`/admin/volunteers/${id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
