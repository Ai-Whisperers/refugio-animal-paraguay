/**
 * Typed fetch wrapper for the Refugio Animal Paraguay API.
 *
 * All API requests go through this client, which handles:
 * - Base URL configuration via NEXT_PUBLIC_API_URL
 * - JWT token injection for authenticated requests
 * - Consistent error handling and response parsing
 */

import { getAccessToken } from "./auth";
import type { ApiError } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail: string
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  requiresAuth?: boolean;
}

/**
 * Core fetch wrapper with typed response.
 * Automatically injects JWT token when requiresAuth is true (default).
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, requiresAuth = true, headers: customHeaders, ...rest } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  if (requiresAuth) {
    const token = getAccessToken();
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...rest,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = "An unexpected error occurred";
    try {
      const errorBody = (await response.json()) as ApiError;
      detail = errorBody.message ?? errorBody.detail ?? detail;
    } catch {
      // Response body was not JSON
    }
    throw new ApiClientError(
      `API error ${response.status}: ${detail}`,
      response.status,
      detail
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Public API client with typed HTTP methods.
 */
export const api = {
  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>(endpoint, { ...options, method: "GET" });
  },

  post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(endpoint, { ...options, method: "POST", body });
  },

  put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(endpoint, { ...options, method: "PUT", body });
  },

  patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(endpoint, { ...options, method: "PATCH", body });
  },

  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>(endpoint, { ...options, method: "DELETE" });
  },
};

/**
 * SWR fetcher that uses the API client.
 * Usage: useSWR("/api/v1/animals", swrFetcher)
 */
export async function swrFetcher<T>(endpoint: string): Promise<T> {
  return api.get<T>(endpoint);
}
