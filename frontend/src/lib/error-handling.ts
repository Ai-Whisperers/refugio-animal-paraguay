/**
 * Centralized API error handling utilities.
 *
 * Provides consistent error message resolution (in Spanish) and
 * recovery action selection for all API errors across the frontend.
 * Designed to work with ApiError from public-api.ts and generic
 * network/Error instances.
 */

/** Shape of a structured API error returned by the backend. */
export type ApiError = {
  status: number;
  error_code: string;
  detail: string;
};

/** Recovery actions the UI can take after an API error. */
export type RecoveryAction = "retry" | "reload" | "login" | "none";

/**
 * Parse any API error or network error and return a user-friendly
 * Spanish message.
 *
 * Handles:
 * - Generic Error instances (network errors, timeouts)
 * - Structured ApiError objects from the backend
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    if (error.message.toLowerCase().includes("fetch")) {
      return "Problemas de conexión. Por favor, intente de nuevo.";
    }
    return error.message;
  }

  const apiError = error as ApiError;

  switch (apiError.error_code) {
    case "NOT_AUTHENTICATED":
      return "Debe iniciar sesión para continuar.";
    case "INSUFFICIENT_PERMISSIONS":
      return "No tiene permiso para realizar esta acción.";
    case "ANIMAL_NOT_FOUND":
      return "El animal no fue encontrado.";
    case "DUPLICATE_ADOPTION_REQUEST":
      return "Ya tiene una solicitud de adopción pendiente para este animal.";
    case "INVALID_EMAIL":
      return "El correo electrónico no es válido.";
    case "VALIDATION_ERROR":
      return "Por favor, revise los datos ingresados.";
    case "CARD_DECLINED":
      return "Tu tarjeta fue rechazada. Intenta con otra tarjeta.";
    case "PAYMENT_SERVICE_UNAVAILABLE":
      return "El servicio de pagos no está disponible. Intenta más tarde.";
    default:
      return apiError.detail || "Ocurrió un error. Por favor, intente de nuevo.";
  }
}

/**
 * Determine the appropriate recovery action for a given API error.
 *
 * Status-based mapping:
 * - 401 → login   (session expired or unauthenticated)
 * - 403 → none    (permission denied, user cannot recover)
 * - 404 → reload  (resource gone, reload to sync state)
 * - 409 → reload  (conflict, reload to get fresh data)
 * - 422 → none    (validation error, user must fix input)
 * - 503 → retry   (service unavailable, transient)
 * - other → retry (default: assume transient)
 */
export function getRecoveryAction(error: ApiError): RecoveryAction {
  switch (error.status) {
    case 401:
      return "login";
    case 403:
      return "none";
    case 404:
      return "reload";
    case 409:
      return "reload";
    case 422:
      return "none";
    case 503:
      return "retry";
    default:
      return "retry";
  }
}

/**
 * Handle an API error: log it, optionally display a message, and
 * execute the appropriate recovery action.
 *
 * Recovery side effects (login redirect, page reload) only run in
 * browser environments (guards against Next.js SSR execution).
 */
export async function handleApiError(
  error: unknown,
  options: {
    showToast?: boolean;
    onError?: (action: RecoveryAction) => void;
  } = {}
): Promise<void> {
  // Always log for debugging / Sentry integration
  console.error("API Error:", error);

  const message = getErrorMessage(error);

  if (options.showToast) {
    // Replace with toast library when integrated (e.g. react-hot-toast)
    console.log("Error:", message);
  }

  const action = getRecoveryAction(error as ApiError);
  options.onError?.(action);

  if (typeof window === "undefined") {
    // SSR context — skip browser-only side effects
    return;
  }

  switch (action) {
    case "login":
      window.location.href = "/login";
      break;
    case "reload":
      window.location.reload();
      break;
    case "retry":
    case "none":
      // Caller is responsible for retry UI; no automatic recovery
      break;
  }
}
