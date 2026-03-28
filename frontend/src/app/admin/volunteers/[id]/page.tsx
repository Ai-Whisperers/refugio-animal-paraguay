"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  UserCheck,
  Clock,
  CheckCircle,
  XCircle,
  UserMinus,
  Mail,
  Phone,
  Star,
  Calendar,
  MessageSquare,
  User,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { VolunteerProfileResponse, VolunteerStatus } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Solicitud de Voluntario";
const LABEL_LOADING = "Cargando solicitud...";
const LABEL_ERROR = "Error al cargar la solicitud";
const LABEL_NOT_FOUND = "Solicitud no encontrada";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a voluntarios";
const LABEL_SECTION_PERSONAL = "Informacion Personal";
const LABEL_SECTION_APPLICATION = "Detalles de la Solicitud";
const LABEL_SECTION_AVAILABILITY = "Disponibilidad";
const LABEL_SECTION_EMERGENCY = "Contacto de Emergencia";
const LABEL_SECTION_REVIEW = "Revision";
const LABEL_MOTIVATION = "Motivacion";
const LABEL_SKILLS = "Habilidades";
const LABEL_AVAILABILITY = "Disponibilidad";
const LABEL_HOURS = "Horas por semana";
const LABEL_LANGUAGES = "Idiomas";
const LABEL_EMERGENCY_NAME = "Nombre";
const LABEL_EMERGENCY_PHONE = "Telefono";
const LABEL_SUBMITTED = "Fecha de solicitud";
const LABEL_TOTAL_HOURS = "Total de horas registradas";
const LABEL_REJECTION_REASON = "Razon de rechazo";
const LABEL_NO_DATA = "—";
const LABEL_APPROVE = "Aprobar";
const LABEL_REJECT = "Rechazar";
const LABEL_CONFIRM_APPROVE = "Confirmar aprobacion";
const LABEL_CONFIRM_REJECT = "Confirmar rechazo";
const LABEL_REJECTION_PLACEHOLDER = "Explique por que se rechaza esta solicitud...";
const LABEL_REJECTION_REQUIRED = "La razon de rechazo es obligatoria.";
const LABEL_SUCCESS_APPROVED = "Solicitud aprobada correctamente.";
const LABEL_SUCCESS_REJECTED = "Solicitud rechazada correctamente.";
const LABEL_CANCEL = "Cancelar";

// --- Status config ---
const STATUS_LABELS: Record<VolunteerStatus, string> = {
  pending: "Pendiente",
  approved: "Aprobado",
  rejected: "Rechazado",
  inactive: "Inactivo",
};

const STATUS_COLORS: Record<VolunteerStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800 border-yellow-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  inactive: "bg-gray-100 text-gray-700 border-gray-200",
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
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-medium ${STATUS_COLORS[status]}`}
    >
      <Icon className="h-4 w-4" />
      {STATUS_LABELS[status]}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatSkill(skill: string) {
  return skill.replace(/_/g, " ");
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 py-2 sm:flex-row sm:gap-4">
      <dt className="w-40 shrink-0 text-sm font-medium text-[var(--color-text-secondary)]">
        {label}
      </dt>
      <dd className="text-sm text-[var(--color-text-primary)]">{children}</dd>
    </div>
  );
}

// --- Review action modal ---
interface ReviewModalProps {
  action: "approve" | "reject";
  onConfirm: (rejectionReason?: string) => void;
  onCancel: () => void;
  submitting: boolean;
}

function ReviewModal({ action, onConfirm, onCancel, submitting }: ReviewModalProps) {
  const [reason, setReason] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleConfirm = () => {
    if (action === "reject") {
      if (!reason.trim()) {
        setValidationError(LABEL_REJECTION_REQUIRED);
        return;
      }
      onConfirm(reason.trim());
    } else {
      onConfirm();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold text-[var(--color-text-primary)]">
          {action === "approve" ? LABEL_CONFIRM_APPROVE : LABEL_CONFIRM_REJECT}
        </h2>
        {action === "reject" && (
          <div className="mb-4">
            <label
              htmlFor="rejection-reason"
              className="mb-1 block text-sm font-medium text-[var(--color-text-secondary)]"
            >
              {LABEL_REJECTION_PLACEHOLDER}
            </label>
            <textarea
              id="rejection-reason"
              value={reason}
              onChange={(e) => {
                setReason(e.target.value);
                setValidationError(null);
              }}
              rows={4}
              maxLength={500}
              placeholder={LABEL_REJECTION_PLACEHOLDER}
              className="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-none"
            />
            {validationError && (
              <p className="mt-1 text-xs text-red-600">{validationError}</p>
            )}
            <p className="mt-1 text-right text-xs text-[var(--color-text-secondary)]">
              {reason.length}/500
            </p>
          </div>
        )}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={submitting}
            className="rounded-md border border-[var(--color-border)] px-4 py-2 text-sm hover:bg-[var(--color-bg-secondary)] disabled:opacity-50 transition-colors"
          >
            {LABEL_CANCEL}
          </button>
          <button
            onClick={handleConfirm}
            disabled={submitting}
            className={`rounded-md px-4 py-2 text-sm text-white disabled:opacity-50 transition-colors ${
              action === "approve"
                ? "bg-green-600 hover:bg-green-700"
                : "bg-red-600 hover:bg-red-700"
            }`}
          >
            {submitting
              ? "Guardando..."
              : action === "approve"
              ? LABEL_APPROVE
              : LABEL_REJECT}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function VolunteerDetailPage() {
  const router = useRouter();
  const params = useParams();
  const volunteerId = params.id as string;

  const [volunteer, setVolunteer] = useState<VolunteerProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewAction, setReviewAction] = useState<"approve" | "reject" | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<VolunteerProfileResponse>(
        `/api/staff/volunteers/${volunteerId}`
      );
      setVolunteer(data);
    } catch (err) {
      if (err instanceof ApiClientError && err.statusCode === 404) {
        setError(LABEL_NOT_FOUND);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [volunteerId]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    load();
  }, [load, router]);

  const handleReview = async (rejectionReason?: string) => {
    if (!volunteer || !reviewAction) return;
    setSubmitting(true);
    try {
      const decision: VolunteerStatus = reviewAction === "approve" ? "approved" : "rejected";
      const body: { decision: VolunteerStatus; rejection_reason?: string } = { decision };
      if (rejectionReason) body.rejection_reason = rejectionReason;

      const updated = await api.put<VolunteerProfileResponse>(
        `/api/staff/volunteers/${volunteerId}/review`,
        body
      );
      setVolunteer(updated);
      setSuccessMessage(
        reviewAction === "approve" ? LABEL_SUCCESS_APPROVED : LABEL_SUCCESS_REJECTED
      );
      setReviewAction(null);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail || LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="py-12 text-center text-[var(--color-text-secondary)]">{LABEL_LOADING}</div>
    );
  }

  if (error && !volunteer) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.push("/admin/volunteers")}
          className="flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {LABEL_BACK}
        </button>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <p className="font-medium">{LABEL_ERROR}</p>
          <p className="mt-1">{error}</p>
          <button onClick={load} className="mt-2 text-red-600 underline hover:text-red-800">
            {LABEL_RETRY}
          </button>
        </div>
      </div>
    );
  }

  if (!volunteer) return null;

  const isPending = volunteer.status === "pending";

  return (
    <>
      {reviewAction && (
        <ReviewModal
          action={reviewAction}
          onConfirm={handleReview}
          onCancel={() => setReviewAction(null)}
          submitting={submitting}
        />
      )}

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <button
              onClick={() => router.push("/admin/volunteers")}
              className="mb-2 flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              {LABEL_BACK}
            </button>
            <h1 className="flex items-center gap-2 text-xl font-semibold text-[var(--color-text-primary)]">
              <UserCheck className="h-5 w-5 text-[var(--color-primary)]" />
              {LABEL_PAGE_TITLE}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={volunteer.status} />
            <button
              onClick={load}
              className="flex items-center gap-1 rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-bg-secondary)] transition-colors"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Success message */}
        {successMessage && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
            {successMessage}
          </div>
        )}

        {/* Error (non-blocking) */}
        {error && volunteer && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Personal info */}
        <section className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-[var(--color-text-primary)]">
            <User className="h-4 w-4 text-[var(--color-primary)]" />
            {LABEL_SECTION_PERSONAL}
          </h2>
          <dl className="divide-y divide-[var(--color-border)]">
            <InfoRow label="Nombre">
              {volunteer.full_name ?? LABEL_NO_DATA}
            </InfoRow>
            <InfoRow label="Correo electrónico">
              <a
                href={`mailto:${volunteer.email}`}
                className="flex items-center gap-1 text-[var(--color-primary)] hover:underline"
              >
                <Mail className="h-3.5 w-3.5" />
                {volunteer.email}
              </a>
            </InfoRow>
            <InfoRow label={LABEL_SUBMITTED}>
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-[var(--color-text-secondary)]" />
                {formatDate(volunteer.created_at)}
              </span>
            </InfoRow>
            {volunteer.total_hours_logged > 0 && (
              <InfoRow label={LABEL_TOTAL_HOURS}>{volunteer.total_hours_logged}h</InfoRow>
            )}
          </dl>
        </section>

        {/* Application details */}
        <section className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-[var(--color-text-primary)]">
            <MessageSquare className="h-4 w-4 text-[var(--color-primary)]" />
            {LABEL_SECTION_APPLICATION}
          </h2>
          <dl className="divide-y divide-[var(--color-border)]">
            <InfoRow label={LABEL_MOTIVATION}>
              <span className="whitespace-pre-wrap">{volunteer.motivation}</span>
            </InfoRow>
            <InfoRow label={LABEL_SKILLS}>
              {volunteer.skills.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {volunteer.skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-[var(--color-bg-secondary)] px-2 py-0.5 text-xs text-[var(--color-text-secondary)]"
                    >
                      {formatSkill(s)}
                    </span>
                  ))}
                </div>
              ) : (
                LABEL_NO_DATA
              )}
            </InfoRow>
            {volunteer.bio && (
              <InfoRow label="Bio">
                <span className="whitespace-pre-wrap">{volunteer.bio}</span>
              </InfoRow>
            )}
          </dl>
        </section>

        {/* Availability */}
        <section className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-5">
          <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-[var(--color-text-primary)]">
            <Calendar className="h-4 w-4 text-[var(--color-primary)]" />
            {LABEL_SECTION_AVAILABILITY}
          </h2>
          <dl className="divide-y divide-[var(--color-border)]">
            <InfoRow label={LABEL_AVAILABILITY}>
              {volunteer.availability.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {volunteer.availability.map((a) => (
                    <span
                      key={a}
                      className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                    >
                      {a.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              ) : (
                LABEL_NO_DATA
              )}
            </InfoRow>
            <InfoRow label={LABEL_HOURS}>
              {volunteer.hours_per_week != null ? `${volunteer.hours_per_week}h` : LABEL_NO_DATA}
            </InfoRow>
            {volunteer.languages_spoken.length > 0 && (
              <InfoRow label={LABEL_LANGUAGES}>{volunteer.languages_spoken.join(", ")}</InfoRow>
            )}
          </dl>
        </section>

        {/* Emergency contact */}
        {(volunteer.emergency_contact_name || volunteer.emergency_contact_phone) && (
          <section className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-5">
            <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-[var(--color-text-primary)]">
              <Phone className="h-4 w-4 text-[var(--color-primary)]" />
              {LABEL_SECTION_EMERGENCY}
            </h2>
            <dl className="divide-y divide-[var(--color-border)]">
              {volunteer.emergency_contact_name && (
                <InfoRow label={LABEL_EMERGENCY_NAME}>
                  {volunteer.emergency_contact_name}
                </InfoRow>
              )}
              {volunteer.emergency_contact_phone && (
                <InfoRow label={LABEL_EMERGENCY_PHONE}>
                  <a
                    href={`tel:${volunteer.emergency_contact_phone}`}
                    className="flex items-center gap-1 text-[var(--color-primary)] hover:underline"
                  >
                    <Phone className="h-3.5 w-3.5" />
                    {volunteer.emergency_contact_phone}
                  </a>
                </InfoRow>
              )}
            </dl>
          </section>
        )}

        {/* Rejection reason (for rejected applications) */}
        {volunteer.status === "rejected" && volunteer.rejection_reason && (
          <section className="rounded-lg border border-red-200 bg-red-50 p-5">
            <h2 className="mb-2 flex items-center gap-2 text-base font-semibold text-red-800">
              <XCircle className="h-4 w-4" />
              {LABEL_REJECTION_REASON}
            </h2>
            <p className="text-sm text-red-700 whitespace-pre-wrap">
              {volunteer.rejection_reason}
            </p>
          </section>
        )}

        {/* Review actions */}
        {isPending && (
          <section className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-primary)] p-5">
            <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-[var(--color-text-primary)]">
              <Star className="h-4 w-4 text-[var(--color-primary)]" />
              {LABEL_SECTION_REVIEW}
            </h2>
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                onClick={() => setReviewAction("approve")}
                className="flex items-center justify-center gap-2 rounded-md bg-green-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-green-700 transition-colors"
              >
                <CheckCircle className="h-4 w-4" />
                {LABEL_APPROVE}
              </button>
              <button
                onClick={() => setReviewAction("reject")}
                className="flex items-center justify-center gap-2 rounded-md border border-red-300 bg-white px-5 py-2.5 text-sm font-medium text-red-700 hover:bg-red-50 transition-colors"
              >
                <XCircle className="h-4 w-4" />
                {LABEL_REJECT}
              </button>
            </div>
          </section>
        )}
      </div>
    </>
  );
}
