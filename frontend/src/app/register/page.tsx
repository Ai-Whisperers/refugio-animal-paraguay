"use client";

import { useState } from "react";
import { UserPlus, CheckCircle, Eye, EyeOff } from "lucide-react";
import { apiFetch, ApiError } from "@/lib/public-api";

const ROLES = [
  { value: "adopter", label: "Adoptante" },
  { value: "donor", label: "Donante" },
  { value: "volunteer", label: "Voluntario/a" },
  { value: "foster", label: "Hogar transitorio" },
] as const;

const MIN_PASSWORD_LENGTH = 8;
const PHONE_PATTERN = /^\+595\d{9}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormErrors {
  full_name?: string;
  email?: string;
  phone?: string;
  password?: string;
  confirm_password?: string;
  role?: string;
}

interface PasswordStrength {
  hasUppercase: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
  hasMinLength: boolean;
}

function getPasswordStrength(password: string): PasswordStrength {
  return {
    hasUppercase: /[A-Z]/.test(password),
    hasNumber: /\d/.test(password),
    hasSpecial: /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/.test(password),
    hasMinLength: password.length >= MIN_PASSWORD_LENGTH,
  };
}

function getStrengthScore(strength: PasswordStrength): number {
  return [
    strength.hasMinLength,
    strength.hasUppercase,
    strength.hasNumber,
    strength.hasSpecial,
  ].filter(Boolean).length;
}

function StrengthIndicator({ strength }: { strength: PasswordStrength }) {
  const score = getStrengthScore(strength);
  const colors = ["bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"];
  const labels = ["Muy debil", "Debil", "Aceptable", "Fuerte"];

  return (
    <div className="mt-1">
      <div className="flex gap-1 mb-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded ${
              i < score ? colors[score - 1] : "bg-gray-200"
            }`}
          />
        ))}
      </div>
      {score > 0 && (
        <p className={`text-xs ${score >= 3 ? "text-green-600" : "text-gray-500"}`}>
          {labels[score - 1]}
        </p>
      )}
      <ul className="text-xs text-gray-500 mt-1 space-y-0.5">
        <li className={strength.hasMinLength ? "text-green-600" : ""}>
          {strength.hasMinLength ? "\u2713" : "\u2717"} Minimo {MIN_PASSWORD_LENGTH} caracteres
        </li>
        <li className={strength.hasUppercase ? "text-green-600" : ""}>
          {strength.hasUppercase ? "\u2713" : "\u2717"} Al menos 1 mayuscula
        </li>
        <li className={strength.hasNumber ? "text-green-600" : ""}>
          {strength.hasNumber ? "\u2713" : "\u2717"} Al menos 1 numero
        </li>
        <li className={strength.hasSpecial ? "text-green-600" : ""}>
          {strength.hasSpecial ? "\u2713" : "\u2717"} Al menos 1 caracter especial
        </li>
      </ul>
    </div>
  );
}

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const passwordStrength = getPasswordStrength(password);

  function validateForm(): boolean {
    const newErrors: FormErrors = {};

    if (!fullName.trim() || fullName.trim().length < 2) {
      newErrors.full_name = "El nombre debe tener al menos 2 caracteres.";
    } else if (fullName.trim().length > 100) {
      newErrors.full_name = "El nombre no puede superar los 100 caracteres.";
    }

    if (!email.trim() || !EMAIL_PATTERN.test(email.trim())) {
      newErrors.email = "Ingresa un email valido.";
    }

    if (!phone.trim() || !PHONE_PATTERN.test(phone.trim())) {
      newErrors.phone = "Formato: +595 seguido de 9 digitos (ej: +595981234567).";
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      newErrors.password = `La contrasena debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
    } else if (getStrengthScore(passwordStrength) < 4) {
      newErrors.password =
        "La contrasena necesita mayuscula, numero y caracter especial.";
    }

    if (confirmPassword !== password) {
      newErrors.confirm_password = "Las contrasenas no coinciden.";
    }

    if (!role) {
      newErrors.role = "Selecciona un rol.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!validateForm()) return;
    if (isSubmitting) return;

    setIsSubmitting(true);

    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          phone: phone.trim(),
          password,
          role,
        }),
      });
      setIsSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError("Error de conexion. Intenta de nuevo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSuccess) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Registro exitoso
          </h1>
          <p className="text-gray-600 mb-6">
            Te enviamos un email de verificacion a{" "}
            <span className="font-medium">{email}</span>. Revisa tu bandeja de
            entrada y haz clic en el enlace para activar tu cuenta.
          </p>
          <a
            href="/"
            className="inline-block bg-amber-500 text-white px-6 py-2 rounded-lg hover:bg-amber-600 transition-colors"
          >
            Volver al inicio
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="flex items-center gap-3 mb-6">
            <UserPlus className="h-8 w-8 text-amber-500" />
            <h1 className="text-2xl font-bold text-gray-900">Crear cuenta</h1>
          </div>

          {submitError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {submitError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Nombre completo
              </label>
              <input
                id="full_name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                  errors.full_name ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Maria Garcia"
                maxLength={100}
              />
              {errors.full_name && (
                <p className="text-xs text-red-600 mt-1">{errors.full_name}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                  errors.email ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="tu@email.com"
              />
              {errors.email && (
                <p className="text-xs text-red-600 mt-1">{errors.email}</p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Telefono
              </label>
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                  errors.phone ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="+595981234567"
              />
              {errors.phone && (
                <p className="text-xs text-red-600 mt-1">{errors.phone}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Contrasena
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                    errors.password ? "border-red-500" : "border-gray-300"
                  }`}
                  placeholder="Min. 8 caracteres"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {password && <StrengthIndicator strength={passwordStrength} />}
              {errors.password && (
                <p className="text-xs text-red-600 mt-1">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirm_password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Confirmar contrasena
              </label>
              <input
                id="confirm_password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none ${
                  errors.confirm_password ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Repite tu contrasena"
              />
              {errors.confirm_password && (
                <p className="text-xs text-red-600 mt-1">
                  {errors.confirm_password}
                </p>
              )}
            </div>

            {/* Role */}
            <div>
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Quiero ser...
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-amber-500 focus:outline-none bg-white ${
                  errors.role ? "border-red-500" : "border-gray-300"
                }`}
              >
                <option value="">Selecciona un rol</option>
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
              {errors.role && (
                <p className="text-xs text-red-600 mt-1">{errors.role}</p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-amber-500 text-white py-2.5 rounded-lg font-medium hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Registrando..." : "Crear cuenta"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            Ya tienes cuenta?{" "}
            <a href="/admin" className="text-amber-600 hover:underline">
              Inicia sesion
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}
