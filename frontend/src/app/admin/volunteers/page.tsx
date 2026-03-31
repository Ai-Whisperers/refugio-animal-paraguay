"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  UserCheck,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Clock,
  CheckCircle,
  XCircle,
  UserMinus,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { VolunteerListItem, VolunteerStatus, PaginatedVolunteerList } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Solicitudes de Voluntarios";
const LABEL_LOADING = "Cargando solicitudes...";
const LABEL_ERROR = "Error al cargar solicitudes";
const LABEL_EMPTY = "No hay solicitudes de voluntarios";
const LABEL_EMPTY_FILTERED = "No hay solicitudes con este estado";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_SHOWING = "Mostrando";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ALL = "Todas";
const LABEL_PENDING = "Pendientes";
const LABEL_APPROVED = "Aprobados";
const LABEL_REJECTED = "Rechazados";
const LABEL_INACTIVE = "Inactivos";
const LABEL_NAME = "Nombre";
const LABEL_EMAIL = "Correo";
const LABEL_STATUS = "Estado";
const LABEL_SKILLS = "Habilidades";
const LABEL_SUBMITTED = "Fecha de solicitud";
const LABEL_HOURS = "Hrs/sem";
const LABEL_VIEW = "Ver detalle";

const PAGE_SIZE = 20;

// --- Status config ---
const STATUS_TABS: { key: VolunteerStatus | "all"; label: string }[] = [
  { key: "all", label: LABEL_ALL },
  { key: "pending", label: LABEL_PENDING },
  { key: "approved", label: LABEL_APPROVED },
  { key: "rejected", label: LABEL_REJECTED },
  { key: "inactive", label: LABEL_INACTIVE },
];

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
  rejected: XCircle,
  inactive: UserMinus,
};

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

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatSkills(skills: string[]) {
  if (skills.length === 0) return "—";
  const display = skills.slice(0, 2).map((s) => s.replace(/_/g, " "));
  const extra = skills.length > 2 ? ` +${skills.length - 2}` : "";
  return display.join(", ") + extra;
}

export default function VolunteersAdminPage() {
  const router = useRouter();
  const [volunteers, setVolunteers] = useState<VolunteerListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<VolunteerStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (pg: number, sf: VolunteerStatus | "all") => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          page: String(pg),
          page_size: String(PAGE_SIZE),
        });
        if (sf !== "all") params.set("status", sf);
        const data = await api.get<PaginatedVolunteerList>(
          `/api/staff/volunteers?${params.toString()}`
        );
        setVolunteers(data.items);
        setTotal(data.total);
      } catch (err) {
        if (err instanceof ApiClientError) {
          setError(err.detail || LABEL_ERROR);
        } else {
          setError(LABEL_ERROR);
        }
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    load(page, statusFilter);
  }, [page, statusFilter, load, router]);

  const handleStatusFilter = (sf: VolunteerStatus | "all") => {
    setStatusFilter(sf);
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const isEmpty = !loading && !error && volunteers.length === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">{LABEL_BACK}</span>
          </button>
          <h1 className="flex items-center gap-2 text-xl font-semibold text-[var(--color-text-primary)]">
            <UserCheck className="h-5 w-5 text-[var(--color-primary)]" />
            {LABEL_PAGE_TITLE}
          </h1>
        </div>
        <button
          onClick={() => load(page, statusFilter)}
          className="flex items-center gap-1 rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-bg-secondary)] transition-colors"
          aria-label={LABEL_RETRY}
        >
          <RefreshCw className="h-4 w-4" />
          <span>Actualizar</span>
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 overflow-x-auto border-b border-[var(--color-border)] pb-px">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleStatusFilter(tab.key)}
            className={`whitespace-nowrap rounded-t px-3 py-2 text-sm font-medium transition-colors ${
              statusFilter === tab.key
                ? "border-b-2 border-[var(--color-primary)] text-[var(--color-primary)]"
                : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
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
          <button
            onClick={() => load(page, statusFilter)}
            className="mt-2 text-red-600 underline hover:text-red-800"
          >
            {LABEL_RETRY}
          </button>
        </div>
      )}

      {/* Empty state */}
      {isEmpty && (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] py-12 text-center">
          <UserCheck className="mx-auto mb-3 h-10 w-10 text-[var(--color-text-secondary)]" />
          <p className="text-[var(--color-text-secondary)]">
            {statusFilter === "all" ? LABEL_EMPTY : LABEL_EMPTY_FILTERED}
          </p>
        </div>
      )}

      {/* Table */}
      {!loading && !error && volunteers.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-lg border border-[var(--color-border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--color-bg-secondary)] text-left text-[var(--color-text-secondary)]">
                <tr>
                  <th className="px-4 py-3 font-medium">{LABEL_NAME}</th>
                  <th className="hidden px-4 py-3 font-medium md:table-cell">{LABEL_EMAIL}</th>
                  <th className="px-4 py-3 font-medium">{LABEL_STATUS}</th>
                  <th className="hidden px-4 py-3 font-medium lg:table-cell">{LABEL_SKILLS}</th>
                  <th className="hidden px-4 py-3 font-medium lg:table-cell">{LABEL_HOURS}</th>
                  <th className="hidden px-4 py-3 font-medium sm:table-cell">{LABEL_SUBMITTED}</th>
                  <th className="px-4 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)] bg-[var(--color-bg-primary)]">
                {volunteers.map((v) => (
                  <tr key={v.id} className="hover:bg-[var(--color-bg-secondary)] transition-colors">
                    <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">
                      {v.full_name ?? "—"}
                    </td>
                    <td className="hidden px-4 py-3 text-[var(--color-text-secondary)] md:table-cell">
                      {v.email}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={v.status} />
                    </td>
                    <td className="hidden px-4 py-3 text-[var(--color-text-secondary)] lg:table-cell">
                      {formatSkills(v.skills)}
                    </td>
                    <td className="hidden px-4 py-3 text-[var(--color-text-secondary)] lg:table-cell">
                      {v.hours_per_week != null ? `${v.hours_per_week}h` : "—"}
                    </td>
                    <td className="hidden px-4 py-3 text-[var(--color-text-secondary)] sm:table-cell">
                      {formatDate(v.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => router.push(`/admin/volunteers/${v.id}`)}
                        className="rounded bg-[var(--color-primary)] px-3 py-1 text-xs text-white hover:opacity-90 transition-opacity"
                      >
                        {LABEL_VIEW}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm text-[var(--color-text-secondary)]">
            <span>
              {LABEL_SHOWING} {(page - 1) * PAGE_SIZE + 1}–
              {Math.min(page * PAGE_SIZE, total)} de {total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg-secondary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                {LABEL_PREVIOUS}
              </button>
              <span className="flex items-center px-2">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 rounded border border-[var(--color-border)] px-2 py-1 hover:bg-[var(--color-bg-secondary)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {LABEL_NEXT}
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
