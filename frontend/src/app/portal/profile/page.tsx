"use client";

import { useState, useEffect, useCallback } from "react";
import {
  User,
  Lock,
  Bell,
  Save,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Download,
  Trash2,
  X,
  TriangleAlert,
} from "lucide-react";
import { api } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";
import type {
  ProfileResponse,
  ProfileUpdate,
  SimplePreferences,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PHONE_PATTERN = /^\+595\d{9}$/;
const MIN_PASSWORD_LENGTH = 8;

type TabKey = "personal" | "security" | "preferences";

const TABS: { key: TabKey; label: string; icon: typeof User }[] = [
  { key: "personal", label: "Datos personales", icon: User },
  { key: "security", label: "Seguridad", icon: Lock },
  { key: "preferences", label: "Preferencias", icon: Bell },
];

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  staff: "Personal",
  vet: "Veterinario/a",
  adopter: "Adoptante",
  donor: "Donante",
  volunteer: "Voluntario/a",
  foster: "Hogar transitorio",
};

// ---------------------------------------------------------------------------
// Feedback banner
// ---------------------------------------------------------------------------

function FeedbackBanner({
  type,
  message,
}: {
  type: "success" | "error";
  message: string;
}) {
  const isSuccess = type === "success";
  return (
    <div
      className={`flex items-center gap-2 p-3 rounded-lg text-sm mb-4 ${
        isSuccess
          ? "bg-green-50 border border-green-200 text-green-700"
          : "bg-red-50 border border-red-200 text-red-700"
      }`}
    >
      {isSuccess ? (
        <CheckCircle className="h-4 w-4 flex-shrink-0" />
      ) : (
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
      )}
      {message}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Account Deletion Modal
// ---------------------------------------------------------------------------

type DeletionModalState = "idle" | "confirming" | "submitting" | "sent" | "error";

interface AccountDeletionModalProps {
  onClose: () => void;
}

function AccountDeletionModal({ onClose }: AccountDeletionModalProps) {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [state, setState] = useState<DeletionModalState>("confirming");
  const [errorMessage, setErrorMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPasswordError("");
    setErrorMessage("");

    if (!password) {
      setPasswordError("Ingresa tu contrasena para confirmar.");
      return;
    }

    setState("submitting");
    try {
      await api.post("/portal/gdpr/delete", { password });
      setState("sent");
    } catch (err: unknown) {
      if (
        err &&
        typeof err === "object" &&
        "statusCode" in err &&
        (err as { statusCode: number }).statusCode === 400
      ) {
        setPasswordError("Contrasena incorrecta. Intenta nuevamente.");
        setState("confirming");
      } else {
        setErrorMessage(
          "No se pudo enviar la solicitud. Intenta mas tarde."
        );
        setState("error");
      }
    }
  }

  // Trap focus: close on Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deletion-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          aria-label="Cerrar"
        >
          <X className="h-5 w-5" />
        </button>

        {state === "sent" ? (
          /* Success state */
          <div className="text-center py-4">
            <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
            <h2
              id="deletion-modal-title"
              className="text-lg font-semibold text-gray-900 mb-2"
            >
              Solicitud enviada
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              Hemos recibido tu solicitud de eliminacion de cuenta. Revisa tu email para confirmar la accion. El enlace expira en 24 horas.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="bg-amber-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-amber-600 transition-colors"
            >
              Entendido
            </button>
          </div>
        ) : state === "error" ? (
          /* Error state */
          <div className="text-center py-4">
            <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h2
              id="deletion-modal-title"
              className="text-lg font-semibold text-gray-900 mb-2"
            >
              Error al enviar solicitud
            </h2>
            <p className="text-sm text-gray-600 mb-6">{errorMessage}</p>
            <div className="flex gap-3 justify-center">
              <button
                type="button"
                onClick={() => setState("confirming")}
                className="border border-gray-300 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Reintentar
              </button>
              <button
                type="button"
                onClick={onClose}
                className="border border-gray-300 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          /* Confirmation form */
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-start gap-3">
              <TriangleAlert className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h2
                  id="deletion-modal-title"
                  className="text-lg font-semibold text-red-700"
                >
                  Eliminar cuenta
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Esta accion es{" "}
                  <span className="font-semibold">irreversible</span>. Todos tus datos personales seran anonimizados de acuerdo con el GDPR Art. 17. Tus registros de adopcion y donaciones se conservan de forma anonima para la integridad operativa del refugio.
                </p>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              Para confirmar, ingresa tu contrasena actual:
            </div>

            <div>
              <label
                htmlFor="deletion-password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Contrasena
              </label>
              <div className="relative">
                <input
                  id="deletion-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoFocus
                  className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-red-500 focus:outline-none ${
                    passwordError ? "border-red-500" : "border-gray-300"
                  }`}
                  placeholder="Tu contrasena actual"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? "Ocultar" : "Mostrar"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {passwordError && (
                <p className="text-xs text-red-600 mt-1">{passwordError}</p>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={state === "submitting"}
                className="flex items-center gap-2 bg-red-600 text-white px-5 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                <Trash2 className="h-4 w-4" />
                {state === "submitting" ? "Enviando..." : "Eliminar mi cuenta"}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={state === "submitting"}
                className="border border-gray-300 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Personal Info Tab
// ---------------------------------------------------------------------------

function PersonalInfoTab({
  profile,
  onUpdate,
}: {
  profile: ProfileResponse;
  onUpdate: () => void;
}) {
  const [fullName, setFullName] = useState(profile.full_name ?? "");
  const [phone, setPhone] = useState(profile.phone ?? "");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);

  useEffect(() => {
    setFullName(profile.full_name ?? "");
    setPhone(profile.phone ?? "");
  }, [profile]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setFeedback(null);
    setPhoneError(null);

    if (phone && !PHONE_PATTERN.test(phone)) {
      setPhoneError("Formato: +595 seguido de 9 digitos (ej: +595981234567).");
      return;
    }

    setSaving(true);
    try {
      const body: ProfileUpdate = {};
      if (fullName !== (profile.full_name ?? "")) body.full_name = fullName;
      if (phone !== (profile.phone ?? "")) body.phone = phone;

      await api.put("/portal/profile", body);
      setFeedback({ type: "success", message: "Perfil actualizado." });
      onUpdate();
    } catch {
      setFeedback({
        type: "error",
        message: "No se pudo actualizar el perfil.",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-4">
      {feedback && <FeedbackBanner {...feedback} />}

      <div>
        <label
          htmlFor="profile-email"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Email
        </label>
        <input
          id="profile-email"
          type="email"
          value={profile.email}
          disabled
          className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
        />
        <p className="text-xs text-gray-400 mt-1">
          El email no se puede cambiar.
        </p>
      </div>

      <div>
        <label
          htmlFor="profile-role"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Rol
        </label>
        <input
          id="profile-role"
          type="text"
          value={ROLE_LABELS[profile.role] ?? profile.role}
          disabled
          className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
        />
      </div>

      <div>
        <label
          htmlFor="profile-name"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Nombre completo
        </label>
        <input
          id="profile-name"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          maxLength={100}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none"
          placeholder="Tu nombre"
        />
      </div>

      <div>
        <label
          htmlFor="profile-phone"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Telefono
        </label>
        <input
          id="profile-phone"
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
            phoneError ? "border-red-500" : "border-gray-300"
          }`}
          placeholder="+595981234567"
        />
        {phoneError && (
          <p className="text-xs text-red-600 mt-1">{phoneError}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={saving}
        className="flex items-center gap-2 bg-amber-500 text-white px-5 py-2 rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50"
      >
        <Save className="h-4 w-4" />
        {saving ? "Guardando..." : "Guardar cambios"}
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Security Tab
// ---------------------------------------------------------------------------

function SecurityTab() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showDeletionModal, setShowDeletionModal] = useState(false);

  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!currentPassword) {
      newErrors.current = "Ingresa tu contrasena actual.";
    }
    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      newErrors.new = `Minimo ${MIN_PASSWORD_LENGTH} caracteres.`;
    } else if (!/[A-Z]/.test(newPassword) || !/\d/.test(newPassword) || !/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(newPassword)) {
      newErrors.new = "Necesita mayuscula, numero y caracter especial.";
    }
    if (confirmPassword !== newPassword) {
      newErrors.confirm = "Las contrasenas no coinciden.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setFeedback(null);
    if (!validate()) return;

    setSaving(true);
    try {
      await api.post("/portal/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setFeedback({
        type: "success",
        message: "Contrasena cambiada exitosamente.",
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setFeedback({
        type: "error",
        message: "No se pudo cambiar la contrasena. Verifica tu contrasena actual.",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {showDeletionModal && (
        <AccountDeletionModal onClose={() => setShowDeletionModal(false)} />
      )}

      <form onSubmit={handleChangePassword} className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Cambiar contrasena
        </h3>

        {feedback && <FeedbackBanner {...feedback} />}

        <div>
          <label
            htmlFor="current-password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Contrasena actual
          </label>
          <div className="relative">
            <input
              id="current-password"
              type={showCurrent ? "text" : "password"}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                errors.current ? "border-red-500" : "border-gray-300"
              }`}
            />
            <button
              type="button"
              onClick={() => setShowCurrent(!showCurrent)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label={showCurrent ? "Ocultar" : "Mostrar"}
            >
              {showCurrent ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.current && (
            <p className="text-xs text-red-600 mt-1">{errors.current}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="new-password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nueva contrasena
          </label>
          <div className="relative">
            <input
              id="new-password"
              type={showNew ? "text" : "password"}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                errors.new ? "border-red-500" : "border-gray-300"
              }`}
              placeholder="Min. 8 caracteres"
            />
            <button
              type="button"
              onClick={() => setShowNew(!showNew)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label={showNew ? "Ocultar" : "Mostrar"}
            >
              {showNew ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>
          {errors.new && (
            <p className="text-xs text-red-600 mt-1">{errors.new}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="confirm-new-password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Confirmar nueva contrasena
          </label>
          <input
            id="confirm-new-password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
              errors.confirm ? "border-red-500" : "border-gray-300"
            }`}
          />
          {errors.confirm && (
            <p className="text-xs text-red-600 mt-1">{errors.confirm}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center gap-2 bg-amber-500 text-white px-5 py-2 rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50"
        >
          <Lock className="h-4 w-4" />
          {saving ? "Cambiando..." : "Cambiar contrasena"}
        </button>
      </form>

      <hr className="border-gray-200" />

      {/* GDPR Export */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Exportar mis datos
        </h3>
        <p className="text-sm text-gray-600 mb-3">
          Descarga una copia de todos tus datos almacenados en formato JSON (GDPR Art. 20).
        </p>
        <a
          href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/portal/gdpr/export`}
          className="inline-flex items-center gap-2 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm"
        >
          <Download className="h-4 w-4" />
          Descargar mis datos
        </a>
      </div>

      <hr className="border-gray-200" />

      {/* Account Deletion */}
      <div>
        <h3 className="text-lg font-semibold text-red-700 mb-2">
          Eliminar mi cuenta
        </h3>
        <p className="text-sm text-gray-600 mb-3">
          Esta accion es irreversible. Todos tus datos personales seran anonimizados de acuerdo con la normativa GDPR Art. 17. Recibiras un email de confirmacion antes de que se ejecute la accion.
        </p>
        <button
          type="button"
          onClick={() => setShowDeletionModal(true)}
          className="inline-flex items-center gap-2 border border-red-300 text-red-700 px-4 py-2 rounded-lg hover:bg-red-50 transition-colors text-sm"
        >
          <Trash2 className="h-4 w-4" />
          Solicitar eliminacion
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preferences Tab
// ---------------------------------------------------------------------------

function PreferencesTab() {
  const [prefs, setPrefs] = useState<SimplePreferences | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<SimplePreferences>("/portal/preferences");
        setPrefs(data);
      } catch {
        setPrefs({
          email_adoption: true,
          email_donations: true,
          email_volunteer: true,
          whatsapp_enabled: true,
          inapp_enabled: true,
        });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave() {
    if (!prefs) return;
    setSaving(true);
    setFeedback(null);
    try {
      const updated = await api.put<SimplePreferences>(
        "/portal/preferences",
        prefs
      );
      setPrefs(updated);
      setFeedback({
        type: "success",
        message: "Preferencias actualizadas.",
      });
    } catch {
      setFeedback({
        type: "error",
        message: "No se pudieron guardar las preferencias.",
      });
    } finally {
      setSaving(false);
    }
  }

  if (loading || !prefs) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-500" />
      </div>
    );
  }

  const toggles: { key: keyof SimplePreferences; label: string; description: string }[] = [
    {
      key: "email_adoption",
      label: "Adopciones por email",
      description: "Recibe actualizaciones sobre el estado de tus solicitudes de adopcion.",
    },
    {
      key: "email_donations",
      label: "Donaciones por email",
      description: "Recibe confirmaciones y recibos de tus donaciones.",
    },
    {
      key: "email_volunteer",
      label: "Voluntariado por email",
      description: "Recibe alertas del sistema y oportunidades de voluntariado.",
    },
    {
      key: "whatsapp_enabled",
      label: "Notificaciones WhatsApp",
      description: "Recibe alertas importantes por WhatsApp.",
    },
    {
      key: "inapp_enabled",
      label: "Notificaciones en la app",
      description: "Muestra notificaciones dentro de la plataforma.",
    },
  ];

  return (
    <div className="space-y-4">
      {feedback && <FeedbackBanner {...feedback} />}

      <p className="text-sm text-gray-600">
        Controla como y cuando te contactamos.
      </p>

      <div className="space-y-3">
        {toggles.map(({ key, label, description }) => (
          <label
            key={key}
            className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={prefs[key]}
              onChange={() => setPrefs({ ...prefs, [key]: !prefs[key] })}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500"
            />
            <div>
              <span className="block text-sm font-medium text-gray-900">
                {label}
              </span>
              <span className="block text-xs text-gray-500">{description}</span>
            </div>
          </label>
        ))}
      </div>

      <button
        type="button"
        onClick={handleSave}
        disabled={saving}
        className="flex items-center gap-2 bg-amber-500 text-white px-5 py-2 rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50"
      >
        <Save className="h-4 w-4" />
        {saving ? "Guardando..." : "Guardar preferencias"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Profile Page
// ---------------------------------------------------------------------------

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("personal");
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    try {
      const data = await api.get<ProfileResponse>("/portal/profile");
      setProfile(data);
      setError(null);
    } catch {
      setError("No se pudo cargar tu perfil. Verifica tu sesion.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      window.location.href = "/admin/login";
      return;
    }
    loadProfile();
  }, [loadProfile]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
      </main>
    );
  }

  if (error || !profile) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <p className="text-gray-700 mb-4">
            {error ?? "Error al cargar el perfil."}
          </p>
          <a
            href="/admin/login"
            className="inline-block bg-amber-500 text-white px-6 py-2 rounded-lg hover:bg-amber-600 transition-colors"
          >
            Iniciar sesion
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Mi perfil</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gestiona tu informacion personal, seguridad y preferencias.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === key
                  ? "border-amber-500 text-amber-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {activeTab === "personal" && (
            <PersonalInfoTab profile={profile} onUpdate={loadProfile} />
          )}
          {activeTab === "security" && <SecurityTab />}
          {activeTab === "preferences" && <PreferencesTab />}
        </div>
      </div>
    </main>
  );
}
