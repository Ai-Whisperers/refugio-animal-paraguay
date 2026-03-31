"use client";

/**
 * /portal/gdpr/confirm-deletion?token=...
 *
 * Landing page for GDPR account deletion confirmation emails.
 *
 * When a user requests account deletion (POST /portal/gdpr/delete), they receive
 * an email with a confirmation link pointing to this page. The page reads the
 * `token` search param, calls POST /portal/gdpr/delete/confirm, and shows the
 * result. On success it redirects to /login after a short delay.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { clearAccessToken } from "@/lib/auth";

type PageStatus = "loading" | "success" | "invalid_token" | "expired" | "error";

interface ConfirmDeleteResponse {
  message: string;
  deleted: boolean;
}

const REDIRECT_DELAY_MS = 5000;

export default function GdprConfirmDeletionPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<PageStatus>("loading");
  const [countdown, setCountdown] = useState(REDIRECT_DELAY_MS / 1000);

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setStatus("invalid_token");
      return;
    }

    api
      .post<ConfirmDeleteResponse>("/portal/gdpr/delete/confirm", { token }, { requiresAuth: false })
      .then((response) => {
        if (response.deleted) {
          // Clear local auth state — account no longer exists
          clearAccessToken();
          setStatus("success");
        } else {
          setStatus("error");
        }
      })
      .catch((err: unknown) => {
        const statusCode =
          err &&
          typeof err === "object" &&
          "statusCode" in err
            ? (err as { statusCode: number }).statusCode
            : 0;

        if (statusCode === 400) {
          // Backend returns 400 for invalid or expired tokens
          setStatus("invalid_token");
        } else {
          setStatus("error");
        }
      });
  }, [token]);

  // Countdown redirect after success
  useEffect(() => {
    if (status !== "success") return;

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          window.location.href = "/login";
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [status]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-md p-8 text-center">
        {status === "loading" && (
          <>
            <Loader2 className="mx-auto h-12 w-12 text-amber-500 animate-spin mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Procesando solicitud
            </h1>
            <p className="text-sm text-gray-600">
              Confirmando la eliminacion de tu cuenta...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Cuenta eliminada
            </h1>
            <p className="text-sm text-gray-600 mb-4">
              Tus datos personales han sido anonimizados de acuerdo con el GDPR Art. 17. Gracias por haber sido parte de la comunidad del Refugio Animal Paraguay.
            </p>
            <p className="text-xs text-gray-400">
              Redirigiendo al inicio de sesion en {countdown}s...
            </p>
            <a
              href="/login"
              className="inline-block mt-4 text-sm text-amber-600 hover:text-amber-700 underline"
            >
              Ir al inicio ahora
            </a>
          </>
        )}

        {status === "invalid_token" && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Enlace invalido o expirado
            </h1>
            <p className="text-sm text-gray-600 mb-6">
              El enlace de confirmacion no es valido o ha expirado. Los enlaces son validos por 24 horas. Puedes solicitar una nueva eliminacion desde tu perfil.
            </p>
            <a
              href="/portal/profile"
              className="inline-block bg-amber-500 text-white px-6 py-2 rounded-lg hover:bg-amber-600 transition-colors text-sm"
            >
              Volver a mi perfil
            </a>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Error al procesar solicitud
            </h1>
            <p className="text-sm text-gray-600 mb-6">
              Ocurrio un error al procesar tu solicitud. Por favor intenta nuevamente o contacta al equipo del refugio.
            </p>
            <div className="flex gap-3 justify-center">
              <a
                href="/portal/profile"
                className="border border-gray-300 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              >
                Volver a mi perfil
              </a>
              <a
                href="/contact"
                className="bg-amber-500 text-white px-5 py-2 rounded-lg hover:bg-amber-600 transition-colors text-sm"
              >
                Contactar soporte
              </a>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
