"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, AlertCircle } from "lucide-react";
import { setAccessToken } from "@/lib/auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function GoogleOAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [linkEmail, setLinkEmail] = useState<string | null>(null);
  const [linkState, setLinkState] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      router.push(`/login?error=cancelled`);
      return;
    }

    if (!code || !state) {
      router.push(`/login?error=failed`);
      return;
    }

    async function exchangeCode() {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/google/callback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, state }),
        });

        if (!response.ok) {
          const data = await response.json().catch(() => null);
          setError(data?.detail ?? "Error en la autenticacion con Google.");
          return;
        }

        const data = await response.json();

        if (data.requires_linking) {
          setLinkEmail(data.email);
          setLinkState(data.access_token);
          return;
        }

        setAccessToken(data.access_token);
        router.push("/portal/profile");
      } catch {
        setError("Error de conexion. Intenta de nuevo mas tarde.");
      }
    }

    exchangeCode();
  }, [searchParams, router]);

  async function handleLink(confirm: boolean) {
    if (!linkState) return;

    if (!confirm) {
      router.push("/login");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/google/link/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: linkState, state: linkState }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setError(data?.detail ?? "Error al vincular la cuenta.");
        return;
      }

      const data = await response.json();
      setAccessToken(data.access_token);
      router.push("/portal/profile");
    } catch {
      setError("Error de conexion. Intenta de nuevo mas tarde.");
    }
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md space-y-4 text-center">
          <div className="flex items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => router.push("/login")}
            className="text-sm font-medium text-primary-600 hover:text-primary-700"
          >
            Volver al inicio de sesion
          </button>
        </div>
      </div>
    );
  }

  if (linkEmail) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-warm-text-primary">
              Vincular cuenta existente
            </h2>
            <p className="mt-2 text-sm text-warm-text-secondary">
              Ya existe una cuenta con el email <strong>{linkEmail}</strong>.
              Deseas vincularla con Google?
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleLink(false)}
              className="flex-1 rounded-lg border border-warm-border bg-white px-4 py-2.5 text-sm font-medium text-warm-text-primary hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              onClick={() => handleLink(true)}
              className="flex-1 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-700"
            >
              Vincular con Google
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        <p className="text-sm text-warm-text-secondary">
          Procesando autenticacion...
        </p>
      </div>
    </div>
  );
}
