"use client";

import { Suspense, useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { PawPrint, AlertCircle, CheckCircle, Loader2, Eye, EyeOff } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const MIN_PASSWORD_LENGTH = 8;

const LABEL_TITLE = "Nueva Contrasena";
const LABEL_PASSWORD = "Nueva contrasena";
const LABEL_CONFIRM = "Confirmar contrasena";
const LABEL_SUBMIT = "Restablecer Contrasena";
const LABEL_RESETTING = "Restableciendo...";
const LABEL_LOGIN = "Ir a Iniciar Sesion";
const LABEL_VALIDATING = "Validando enlace...";

const ERROR_INVALID_TOKEN = "Este enlace es invalido o ha expirado. Solicita uno nuevo.";
const ERROR_NETWORK = "Error de conexion. Intenta de nuevo mas tarde.";
const ERROR_PASSWORD_MISMATCH = "Las contrasenas no coinciden.";
const ERROR_PASSWORD_SHORT = `La contrasena debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
const SUCCESS_MESSAGE = "Tu contrasena ha sido restablecida. Ya puedes iniciar sesion.";

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isValidating, setIsValidating] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setIsValidating(false);
      return;
    }

    async function validateToken() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/auth/password-reset/validate?token=${encodeURIComponent(token!)}`,
        );
        if (response.ok) {
          const data = await response.json();
          setIsTokenValid(data.valid);
        }
      } catch {
        // Token validation failed — show invalid state
      } finally {
        setIsValidating(false);
      }
    }

    validateToken();
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(ERROR_PASSWORD_SHORT);
      return;
    }

    if (password !== confirmPassword) {
      setError(ERROR_PASSWORD_MISMATCH);
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || ERROR_NETWORK);
        return;
      }

      setIsSuccess(true);
    } catch {
      setError(ERROR_NETWORK);
    } finally {
      setIsLoading(false);
    }
  }

  // Loading state
  if (isValidating) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex items-center gap-2 text-warm-text-secondary">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          <span>{LABEL_VALIDATING}</span>
        </div>
      </div>
    );
  }

  // Invalid or missing token
  if (!token || !isTokenValid) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <AlertCircle className="h-8 w-8 text-red-600" aria-hidden="true" />
          </div>
          <h1 className="text-xl font-bold text-warm-text-primary">{ERROR_INVALID_TOKEN}</h1>
          <Link
            href="/admin/forgot-password"
            className="inline-block rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
          >
            Solicitar nuevo enlace
          </Link>
        </div>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md space-y-6 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-8 w-8 text-green-600" aria-hidden="true" />
          </div>
          <h1 className="text-xl font-bold text-warm-text-primary">{SUCCESS_MESSAGE}</h1>
          <Link
            href="/admin/login"
            className="inline-block rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
          >
            {LABEL_LOGIN}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
            <PawPrint className="h-8 w-8 text-primary-600" aria-hidden="true" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-warm-text-primary">
            {LABEL_TITLE}
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {error && (
            <div
              className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* New password */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-warm-text-primary"
            >
              {LABEL_PASSWORD}
            </label>
            <div className="relative mt-1">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                minLength={MIN_PASSWORD_LENGTH}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="block w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2.5 pr-10 text-warm-text-primary shadow-sm placeholder:text-warm-text-muted focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-warm-text-muted hover:text-warm-text-secondary"
                aria-label={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          {/* Confirm password */}
          <div>
            <label
              htmlFor="confirm-password"
              className="block text-sm font-medium text-warm-text-primary"
            >
              {LABEL_CONFIRM}
            </label>
            <input
              id="confirm-password"
              name="confirm-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              minLength={MIN_PASSWORD_LENGTH}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              className="mt-1 block w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2.5 text-warm-text-primary shadow-sm placeholder:text-warm-text-muted focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:opacity-50"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !password || !confirmPassword}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                {LABEL_RESETTING}
              </>
            ) : (
              LABEL_SUBMIT
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <div className="flex items-center gap-2 text-warm-text-secondary">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            <span>{LABEL_VALIDATING}</span>
          </div>
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
