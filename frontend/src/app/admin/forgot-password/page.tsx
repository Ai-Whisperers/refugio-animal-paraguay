"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { PawPrint, ArrowLeft, AlertCircle, CheckCircle, Loader2 } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const LABEL_TITLE = "Restablecer Contrasena";
const LABEL_SUBTITLE = "Ingresa tu email para recibir un enlace de restablecimiento";
const LABEL_EMAIL = "Email";
const LABEL_SUBMIT = "Enviar Enlace";
const LABEL_SENDING = "Enviando...";
const LABEL_BACK = "Volver al inicio de sesion";
const ERROR_NETWORK = "Error de conexion. Intenta de nuevo mas tarde.";
const SUCCESS_MESSAGE = "Si este email esta registrado, recibiras un enlace para restablecer tu contrasena.";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/password-reset/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        setError(ERROR_NETWORK);
        return;
      }

      setIsSubmitted(true);
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

        {isSubmitted ? (
          /* Success state */
          <div className="space-y-6">
            <div
              className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-4 text-sm text-green-800"
              role="status"
            >
              <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0" aria-hidden="true" />
              <span>{SUCCESS_MESSAGE}</span>
            </div>
            <Link
              href="/admin/login"
              className="flex items-center justify-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              {LABEL_BACK}
            </Link>
          </div>
        ) : (
          /* Form */
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

            <button
              type="submit"
              disabled={isLoading || !email}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  {LABEL_SENDING}
                </>
              ) : (
                LABEL_SUBMIT
              )}
            </button>

            <div className="text-center">
              <Link
                href="/admin/login"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                {LABEL_BACK}
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
