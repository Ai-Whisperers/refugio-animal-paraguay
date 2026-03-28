"use client";

import { useState, useEffect } from "react";
import { CheckCircle, Clock, Heart, Edit2, Save, X, User, Languages } from "lucide-react";
import { apiFetch, ApiError } from "@/lib/public-api";

const SKILL_OPTIONS = [
  { value: "animal_care", label: "Cuidado de animales" },
  { value: "veterinary_assistance", label: "Asistencia veterinaria" },
  { value: "photography", label: "Fotografía" },
  { value: "social_media", label: "Redes sociales" },
  { value: "transport_driving", label: "Transporte / manejo" },
  { value: "fundraising", label: "Recaudación de fondos" },
  { value: "admin_office", label: "Administración / oficina" },
  { value: "cleaning", label: "Limpieza e higiene" },
  { value: "construction_maintenance", label: "Construcción y mantenimiento" },
  { value: "education_outreach", label: "Educación comunitaria" },
  { value: "translation", label: "Traducción" },
  { value: "web_tech", label: "Web y tecnología" },
  { value: "event_coordination", label: "Coordinación de eventos" },
];

const AVAILABILITY_OPTIONS = [
  { value: "weekday_mornings", label: "Mañanas entre semana" },
  { value: "weekday_afternoons", label: "Tardes entre semana" },
  { value: "weekday_evenings", label: "Noches entre semana" },
  { value: "weekend_mornings", label: "Mañanas de fin de semana" },
  { value: "weekend_afternoons", label: "Tardes de fin de semana" },
  { value: "flexible", label: "Horario flexible" },
];

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: "Solicitud pendiente", color: "bg-yellow-100 text-yellow-800" },
  approved: { label: "Voluntario activo", color: "bg-green-100 text-green-800" },
  rejected: { label: "Solicitud rechazada", color: "bg-red-100 text-red-800" },
  inactive: { label: "Inactivo", color: "bg-gray-100 text-gray-700" },
};

interface VolunteerProfile {
  id: string;
  user_id: string;
  full_name: string | null;
  email: string;
  motivation: string;
  bio: string | null;
  skills: string[];
  availability: string[];
  hours_per_week: number | null;
  languages_spoken: string[];
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  status: string;
  rejection_reason: string | null;
  total_hours_logged: number;
  created_at: string;
}

interface EditForm {
  bio: string;
  skills: string[];
  availability: string[];
  hours_per_week: string;
  languages_spoken: string;
}

function getSkillLabel(value: string): string {
  return SKILL_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

function getAvailabilityLabel(value: string): string {
  return AVAILABILITY_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

function toggleItem(list: string[], item: string): string[] {
  return list.includes(item) ? list.filter((v) => v !== item) : [...list, item];
}

export default function VolunteerProfilePage() {
  const [profile, setProfile] = useState<VolunteerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [editForm, setEditForm] = useState<EditForm>({
    bio: "",
    skills: [],
    availability: [],
    hours_per_week: "",
    languages_spoken: "",
  });

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    setLoading(true);
    setError(null);
    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      if (!token) {
        setError("Debes iniciar sesión para ver tu perfil de voluntario.");
        setLoading(false);
        return;
      }
      const data = await apiFetch<VolunteerProfile>("/api/volunteers/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProfile(data);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError("Tu sesión ha expirado. Por favor vuelve a iniciar sesión.");
        } else if (err.status === 404) {
          setError("No tienes un perfil de voluntario. Completa la solicitud primero.");
        } else {
          setError("Error al cargar tu perfil. Intenta nuevamente.");
        }
      } else {
        setError("Error de conexión. Intenta nuevamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  function startEditing() {
    if (!profile) return;
    setEditForm({
      bio: profile.bio ?? "",
      skills: [...profile.skills],
      availability: [...profile.availability],
      hours_per_week: profile.hours_per_week?.toString() ?? "",
      languages_spoken: profile.languages_spoken.join(", "),
    });
    setSaveError(null);
    setSaveSuccess(false);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setSaveError(null);
  }

  async function saveProfile() {
    if (!profile) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    const languages = editForm.languages_spoken
      .split(",")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const updated = await apiFetch<VolunteerProfile>("/api/volunteers/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          bio: editForm.bio || null,
          skills: editForm.skills,
          availability: editForm.availability,
          hours_per_week: editForm.hours_per_week
            ? parseInt(editForm.hours_per_week, 10)
            : null,
          languages_spoken: languages,
        }),
      });
      setProfile(updated);
      setEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      if (err instanceof ApiError) {
        setSaveError(err.detail ?? "Error al guardar. Intenta nuevamente.");
      } else {
        setSaveError("Error de conexión. Intenta nuevamente.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-amber-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto mb-4" />
          <p className="text-gray-600">Cargando tu perfil...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-amber-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <Heart className="mx-auto mb-4 text-red-400" size={40} />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Perfil no disponible</h2>
          <p className="text-gray-600 mb-6">{error ?? "No se pudo cargar el perfil."}</p>
          <a
            href="/volunteer/apply"
            className="inline-block bg-amber-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-amber-700 transition"
          >
            Solicitar ser voluntario
          </a>
        </div>
      </div>
    );
  }

  const statusInfo = STATUS_LABELS[profile.status] ?? {
    label: profile.status,
    color: "bg-gray-100 text-gray-700",
  };
  const canEdit = profile.status !== "rejected";

  return (
    <div className="min-h-screen bg-amber-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header card */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-amber-100 rounded-full p-3">
                <User className="text-amber-700" size={28} />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {profile.full_name ?? "Mi perfil de voluntario"}
                </h1>
                <p className="text-gray-500 text-sm">{profile.email}</p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusInfo.color}`}>
              {statusInfo.label}
            </span>
          </div>

          {profile.status === "approved" && (
            <div className="mt-4 flex items-center gap-2 text-green-700 bg-green-50 rounded-xl px-4 py-3">
              <CheckCircle size={18} />
              <span className="text-sm font-medium">
                Voluntario activo — {profile.total_hours_logged} horas registradas
              </span>
            </div>
          )}

          {profile.status === "rejected" && profile.rejection_reason && (
            <div className="mt-4 bg-red-50 rounded-xl px-4 py-3">
              <p className="text-sm text-red-700">
                <strong>Motivo:</strong> {profile.rejection_reason}
              </p>
              <a
                href="/volunteer/apply"
                className="mt-2 inline-block text-sm text-amber-700 underline"
              >
                Volver a solicitar
              </a>
            </div>
          )}
        </div>

        {/* Save success banner */}
        {saveSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 flex items-center gap-2 text-green-800">
            <CheckCircle size={16} />
            <span className="text-sm font-medium">Perfil actualizado correctamente.</span>
          </div>
        )}

        {/* Profile details / edit form */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">Mis datos</h2>
            {canEdit && !editing && (
              <button
                onClick={startEditing}
                className="flex items-center gap-1 text-sm text-amber-700 hover:text-amber-800 font-medium"
              >
                <Edit2 size={15} />
                Editar
              </button>
            )}
            {editing && (
              <div className="flex gap-2">
                <button
                  onClick={cancelEditing}
                  className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
                >
                  <X size={15} />
                  Cancelar
                </button>
                <button
                  onClick={saveProfile}
                  disabled={saving}
                  className="flex items-center gap-1 text-sm text-white bg-amber-600 hover:bg-amber-700 px-3 py-1.5 rounded-lg font-medium disabled:opacity-50"
                >
                  <Save size={15} />
                  {saving ? "Guardando..." : "Guardar"}
                </button>
              </div>
            )}
          </div>

          {saveError && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm">
              {saveError}
            </div>
          )}

          {/* Bio */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Presentación breve
            </label>
            {editing ? (
              <textarea
                value={editForm.bio}
                onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                rows={3}
                maxLength={500}
                placeholder="Cuéntanos brevemente sobre ti y tu experiencia con animales..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none"
              />
            ) : (
              <p className="text-sm text-gray-700">
                {profile.bio ?? <span className="text-gray-400 italic">Sin presentación todavía.</span>}
              </p>
            )}
          </div>

          {/* Skills */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mis habilidades
            </label>
            {editing ? (
              <div className="flex flex-wrap gap-2">
                {SKILL_OPTIONS.map((opt) => {
                  const selected = editForm.skills.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() =>
                        setEditForm({
                          ...editForm,
                          skills: toggleItem(editForm.skills, opt.value),
                        })
                      }
                      className={`px-3 py-1.5 rounded-full text-sm border transition ${
                        selected
                          ? "bg-amber-600 text-white border-amber-600"
                          : "bg-white text-gray-600 border-gray-300 hover:border-amber-400"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            ) : profile.skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill) => (
                  <span
                    key={skill}
                    className="px-3 py-1 rounded-full text-sm bg-amber-100 text-amber-800"
                  >
                    {getSkillLabel(skill)}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">Sin habilidades registradas.</p>
            )}
          </div>

          {/* Availability */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Clock size={15} className="inline mr-1" />
              Disponibilidad
            </label>
            {editing ? (
              <div className="flex flex-wrap gap-2">
                {AVAILABILITY_OPTIONS.map((opt) => {
                  const selected = editForm.availability.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() =>
                        setEditForm({
                          ...editForm,
                          availability: toggleItem(editForm.availability, opt.value),
                        })
                      }
                      className={`px-3 py-1.5 rounded-full text-sm border transition ${
                        selected
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            ) : profile.availability.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.availability.map((slot) => (
                  <span
                    key={slot}
                    className="px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {getAvailabilityLabel(slot)}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">Sin horarios registrados.</p>
            )}
          </div>

          {/* Hours per week */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Horas disponibles por semana
            </label>
            {editing ? (
              <input
                type="number"
                min={1}
                max={40}
                value={editForm.hours_per_week}
                onChange={(e) => setEditForm({ ...editForm, hours_per_week: e.target.value })}
                className="w-32 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
                placeholder="Ej. 5"
              />
            ) : (
              <p className="text-sm text-gray-700">
                {profile.hours_per_week
                  ? `${profile.hours_per_week} horas/semana`
                  : <span className="text-gray-400 italic">No especificado</span>}
              </p>
            )}
          </div>

          {/* Languages */}
          <div className="mb-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Languages size={15} className="inline mr-1" />
              Idiomas que hablo
            </label>
            {editing ? (
              <input
                type="text"
                value={editForm.languages_spoken}
                onChange={(e) => setEditForm({ ...editForm, languages_spoken: e.target.value })}
                placeholder="Ej. Español, Inglés, Guaraní"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            ) : profile.languages_spoken.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.languages_spoken.map((lang) => (
                  <span
                    key={lang}
                    className="px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">Sin idiomas registrados.</p>
            )}
          </div>
        </div>

        {/* Motivation (read-only) */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Mi motivación</h2>
          <p className="text-sm text-gray-700 leading-relaxed">{profile.motivation}</p>
          {profile.status === "pending" && (
            <p className="mt-3 text-xs text-gray-400">
              Para actualizar tu motivación mientras tu solicitud está pendiente, usa{" "}
              <a href="/volunteer/apply" className="underline text-amber-600">
                la página de solicitud
              </a>
              .
            </p>
          )}
        </div>

        {/* Emergency contact (read-only) */}
        {(profile.emergency_contact_name || profile.emergency_contact_phone) && (
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">Contacto de emergencia</h2>
            <p className="text-sm text-gray-700">{profile.emergency_contact_name}</p>
            <p className="text-sm text-gray-500">{profile.emergency_contact_phone}</p>
          </div>
        )}
      </div>
    </div>
  );
}
