"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { PawPrint, Eye, EyeOff, AlertCircle, Loader2 } from "lucide-react";
import { setAccessToken } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ERROR_INVALID_CREDENTIALS = "Credenciales incorrectas. Verifica tu email y contrasena.";
const ERROR_NETWORK = "Error de conexion. Intenta de nuevo mas tarde.";
const ERROR_SESSION_EXPIRED = "Tu sesion ha expirado. Inicia sesion nuevamente.";

const LABEL_EMAIL = "Email";
const LABEL_PASSWORD = "Contrasena";
const LABEL_LOGIN = "Iniciar Sesion";
const LABEL_LOGGING_IN = "Iniciando sesion...";
const LABEL_TITLE = "Panel de Administracion";
const LABEL_SUBTITLE = "Refugio Animal Paraguay";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Check for session expired query param
  const isSessionExpired =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("expired") === "true";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setError(ERROR_INVALID_CREDENTIALS);
        } else {
          setError(ERROR_NETWORK);
        }
        return;
      }

      const data = await response.json();
      setAccessToken(data.access_token);
      router.push("/admin/dashboard");
    } catch {
      setError(ERROR_NETWORK);
    } finally {
      setIsLoading(false);
    }
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
          <p className="mt-1 text-sm text-warm-text-secondary">
            {LABEL_SUBTITLE}
          </p>
        </div>

        {/* Session expired banner */}
        {isSessionExpired && !error && (
          <div
            className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
            role="alert"
          >
            <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <span>{ERROR_SESSION_EXPIRED}</span>
          </div>
        )}

        {/* Login form */}
        <form onSubmit={handleSubmit} className="space-y-6" noValidate>
          {/* Error message */}
          {error && (
            <div
              className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
              role="alert"
            >
              <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Email field */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-warm-text-primary"
            >
              {LABEL_EMAIL}
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              className="mt-1 block w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2.5 text-warm-text-primary shadow-sm placeholder:text-warm-text-muted focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:opacity-50"
              placeholder="staff@refugioanimal.org"
            />
          </div>

          {/* Password field */}
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
                autoComplete="current-password"
                required
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

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                {LABEL_LOGGING_IN}
              </>
            ) : (
              LABEL_LOGIN
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
