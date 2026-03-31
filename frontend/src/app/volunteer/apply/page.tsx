"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, Heart, Clock, User } from "lucide-react";
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
] as const;

const AVAILABILITY_OPTIONS = [
  { value: "weekday_mornings", label: "Mañanas entre semana" },
  { value: "weekday_afternoons", label: "Tardes entre semana" },
  { value: "weekday_evenings", label: "Noches entre semana" },
  { value: "weekend_mornings", label: "Mañanas de fin de semana" },
  { value: "weekend_afternoons", label: "Tardes de fin de semana" },
  { value: "flexible", label: "Horario flexible" },
] as const;

const MIN_MOTIVATION_LENGTH = 20;

interface FormState {
  motivation: string;
  skills: string[];
  availability: string[];
  hours_per_week: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
}

interface FormErrors {
  motivation?: string;
  skills?: string;
  availability?: string;
  hours_per_week?: string;
  general?: string;
}

function validate(form: FormState): FormErrors {
  const errors: FormErrors = {};
  if (!form.motivation || form.motivation.trim().length < MIN_MOTIVATION_LENGTH) {
    errors.motivation = `Por favor describe tu motivación (mínimo ${MIN_MOTIVATION_LENGTH} caracteres).`;
  }
  if (form.hours_per_week) {
    const hours = parseInt(form.hours_per_week, 10);
    if (isNaN(hours) || hours < 1 || hours > 40) {
      errors.hours_per_week = "Las horas deben estar entre 1 y 40 por semana.";
    }
  }
  return errors;
}

function toggleItem(list: string[], item: string): string[] {
  return list.includes(item) ? list.filter((v) => v !== item) : [...list, item];
}

export default function VolunteerApplyPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>({
    motivation: "",
    skills: [],
    availability: [],
    hours_per_week: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  }

  function toggleSkill(value: string) {
    setForm((prev) => ({ ...prev, skills: toggleItem(prev.skills, value) }));
  }

  function toggleAvailability(value: string) {
    setForm((prev) => ({
      ...prev,
      availability: toggleItem(prev.availability, value),
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationErrors = validate(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});

    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      await apiFetch("/api/volunteers/apply", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          motivation: form.motivation.trim(),
          skills: form.skills,
          availability: form.availability,
          hours_per_week: form.hours_per_week
            ? parseInt(form.hours_per_week, 10)
            : null,
          emergency_contact_name: form.emergency_contact_name || null,
          emergency_contact_phone: form.emergency_contact_phone || null,
        }),
      });
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setErrors({
            general: "Debes iniciar sesión para enviar tu solicitud de voluntariado.",
          });
        } else if (err.status === 409) {
          setErrors({
            general:
              "Ya tienes una solicitud de voluntariado pendiente o aprobada.",
          });
        } else {
          setErrors({ general: err.message || "Error al enviar la solicitud." });
        }
      } else {
        setErrors({ general: "Error de conexión. Intenta nuevamente." });
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-primary-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            ¡Solicitud enviada!
          </h1>
          <p className="text-gray-600 mb-6">
            Gracias por querer ser voluntario/a. El equipo del refugio revisará tu
            solicitud y te contactará pronto.
          </p>
          <button
            onClick={() => router.push("/")}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-primary-100 rounded-full mb-4">
            <Heart className="w-7 h-7 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Quiero ser voluntario/a
          </h1>
          <p className="text-gray-600 max-w-lg mx-auto">
            Completa el formulario y nuestro equipo se pondrá en contacto contigo
            para coordinar tu incorporación.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm p-8 space-y-6">
          {/* Motivation */}
          <div>
            <label
              htmlFor="motivation"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              ¿Por qué quieres ser voluntario/a?{" "}
              <span className="text-red-500">*</span>
            </label>
            <textarea
              id="motivation"
              name="motivation"
              value={form.motivation}
              onChange={handleChange}
              rows={4}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none ${
                errors.motivation ? "border-red-400" : "border-gray-300"
              }`}
              placeholder="Cuéntanos sobre tu motivación para colaborar con el refugio..."
            />
            <div className="flex justify-between mt-1">
              {errors.motivation ? (
                <p className="text-xs text-red-500">{errors.motivation}</p>
              ) : (
                <span />
              )}
              <span className="text-xs text-gray-400">
                {form.motivation.length} caracteres
              </span>
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <span className="flex items-center gap-1">
                <User className="w-4 h-4" />
                Habilidades que aportas
              </span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {SKILL_OPTIONS.map((skill) => (
                <button
                  key={skill.value}
                  type="button"
                  onClick={() => toggleSkill(skill.value)}
                  className={`text-left text-sm px-3 py-2 rounded-lg border transition-colors ${
                    form.skills.includes(skill.value)
                      ? "bg-primary-600 text-white border-primary-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-primary-400"
                  }`}
                >
                  {skill.label}
                </button>
              ))}
            </div>
          </div>

          {/* Availability */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                Disponibilidad
              </span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {AVAILABILITY_OPTIONS.map((slot) => (
                <button
                  key={slot.value}
                  type="button"
                  onClick={() => toggleAvailability(slot.value)}
                  className={`text-left text-sm px-3 py-2 rounded-lg border transition-colors ${
                    form.availability.includes(slot.value)
                      ? "bg-primary-600 text-white border-primary-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-primary-400"
                  }`}
                >
                  {slot.label}
                </button>
              ))}
            </div>
          </div>

          {/* Hours per week */}
          <div>
            <label
              htmlFor="hours_per_week"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Horas disponibles por semana (opcional)
            </label>
            <input
              type="number"
              id="hours_per_week"
              name="hours_per_week"
              value={form.hours_per_week}
              onChange={handleChange}
              min={1}
              max={40}
              className={`w-32 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.hours_per_week ? "border-red-400" : "border-gray-300"
              }`}
              placeholder="Ej: 5"
            />
            {errors.hours_per_week && (
              <p className="text-xs text-red-500 mt-1">{errors.hours_per_week}</p>
            )}
          </div>

          {/* Emergency Contact */}
          <div className="bg-gray-50 rounded-xl p-4 space-y-3">
            <p className="text-sm font-medium text-gray-700">
              Contacto de emergencia (opcional)
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="emergency_contact_name"
                  className="block text-xs text-gray-500 mb-1"
                >
                  Nombre completo
                </label>
                <input
                  type="text"
                  id="emergency_contact_name"
                  name="emergency_contact_name"
                  value={form.emergency_contact_name}
                  onChange={handleChange}
                  maxLength={100}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Nombre del contacto"
                />
              </div>
              <div>
                <label
                  htmlFor="emergency_contact_phone"
                  className="block text-xs text-gray-500 mb-1"
                >
                  Teléfono
                </label>
                <input
                  type="tel"
                  id="emergency_contact_phone"
                  name="emergency_contact_phone"
                  value={form.emergency_contact_phone}
                  onChange={handleChange}
                  maxLength={20}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="+595 9xx xxx xxx"
                />
              </div>
            </div>
          </div>

          {errors.general && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              {errors.general}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300 text-white font-semibold py-3 px-6 rounded-xl transition-colors"
          >
            {submitting ? "Enviando solicitud..." : "Enviar solicitud de voluntariado"}
          </button>

          <p className="text-xs text-gray-500 text-center">
            Debes tener una cuenta registrada para enviar tu solicitud.{" "}
            <a href="/register" className="text-primary-600 hover:underline">
              Regístrate aquí
            </a>{" "}
            si aún no tienes una.
          </p>
        </form>
      </div>
    </div>
  );
}
