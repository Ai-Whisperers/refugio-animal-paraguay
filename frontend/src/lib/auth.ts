/**
 * JWT authentication utilities for the Refugio Animal Paraguay frontend.
 *
 * Handles token storage (in-memory + sessionStorage), parsing,
 * and expiration checking. Tokens are injected into API requests
 * via the api client (lib/api.ts).
 */

import type { TokenPayload, UserRole } from "@/types/api";

const TOKEN_STORAGE_KEY = "refugio_access_token";

// In-memory token for SSR safety (sessionStorage not available server-side)
let memoryToken: string | null = null;

/**
 * Store the access token after login.
 * Uses both in-memory and sessionStorage for persistence across page loads.
 */
export function setAccessToken(token: string): void {
  memoryToken = token;
  if (typeof window !== "undefined") {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

/**
 * Retrieve the current access token.
 * Falls back to sessionStorage if in-memory token is cleared (e.g., after HMR).
 */
export function getAccessToken(): string | null {
  if (memoryToken) {
    return memoryToken;
  }
  if (typeof window !== "undefined") {
    const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) {
      memoryToken = stored;
      return stored;
    }
  }
  return null;
}

/**
 * Remove the access token (logout).
 */
export function clearAccessToken(): void {
  memoryToken = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

/**
 * Decode a JWT token payload without verification.
 * Verification happens server-side; this is for UI display only.
 */
export function decodeToken(token: string): TokenPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload as TokenPayload;
  } catch {
    return null;
  }
}

/**
 * Check if the current token is expired.
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token);
  if (!payload?.exp) return true;
  // Allow 30-second buffer for clock skew
  const CLOCK_SKEW_BUFFER_SECONDS = 30;
  return Date.now() / 1000 > payload.exp - CLOCK_SKEW_BUFFER_SECONDS;
}

/**
 * Check if the user is currently authenticated with a valid token.
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;
  return !isTokenExpired(token);
}

/**
 * Get the current user's role from the token, if authenticated.
 */
export function getCurrentUserRole(): UserRole | null {
  const token = getAccessToken();
  if (!token) return null;
  const payload = decodeToken(token);
  return payload?.role ?? null;
}

/**
 * Get the current user's identifier (sub claim) from the token.
 */
export function getCurrentUserId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  const payload = decodeToken(token);
  return payload?.sub ?? null;
}
