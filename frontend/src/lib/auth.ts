/**
 * JWT authentication utilities.
 *
 * Handles token storage, retrieval, and basic JWT payload decoding
 * for client-side auth guards. Tokens are stored in localStorage.
 */

import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "./constants";

// -- Types --------------------------------------------------------------

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

export interface JwtPayload {
  sub: string;
  exp: number;
  iat?: number;
  role?: string;
  email?: string;
}

export interface AuthUser {
  id: string;
  email?: string;
  role?: string;
}

// -- Token storage ------------------------------------------------------

function isClient(): boolean {
  return typeof window !== "undefined";
}

export function getAccessToken(): string | null {
  if (!isClient()) return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (!isClient()) return null;
  return localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: AuthTokens): void {
  if (!isClient()) return;
  localStorage.setItem(AUTH_TOKEN_KEY, tokens.access_token);
  if (tokens.refresh_token) {
    localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
}

export function clearTokens(): void {
  if (!isClient()) return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
}

// -- JWT decoding -------------------------------------------------------

/**
 * Decode a JWT payload without verification.
 * This is for client-side display only; the backend validates tokens.
 */
export function decodeToken(token: string): JwtPayload | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
}

/**
 * Check whether the stored access token is expired.
 * Returns true if no token exists or if it has expired.
 */
export function isTokenExpired(): boolean {
  const token = getAccessToken();
  if (!token) return true;

  const payload = decodeToken(token);
  if (!payload) return true;

  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

/**
 * Get the currently authenticated user from the stored token.
 * Returns null if not authenticated or token is expired.
 */
export function getCurrentUser(): AuthUser | null {
  const token = getAccessToken();
  if (!token) return null;

  const payload = decodeToken(token);
  if (!payload) return null;

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp < now) return null;

  return {
    id: payload.sub,
    email: payload.email,
    role: payload.role,
  };
}

// -- Auth actions -------------------------------------------------------

/**
 * Log in with username and password.
 * The FastAPI backend expects form-encoded OAuth2 credentials.
 */
export async function login(credentials: LoginCredentials): Promise<AuthUser> {
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const url = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/login`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => response.text());
    throw new Error(
      typeof errorBody === "object" && errorBody !== null && "detail" in errorBody
        ? String((errorBody as { detail: unknown }).detail)
        : "Login failed"
    );
  }

  const tokens = (await response.json()) as AuthTokens;
  setTokens(tokens);

  const user = getCurrentUser();
  if (!user) {
    throw new Error("Failed to decode token after login");
  }

  return user;
}

/**
 * Log out by clearing stored tokens.
 */
export function logout(): void {
  clearTokens();
}

/**
 * Check if a user is currently authenticated (has a non-expired token).
 */
export function isAuthenticated(): boolean {
  return !isTokenExpired();
}
