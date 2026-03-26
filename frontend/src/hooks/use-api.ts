/**
 * SWR-based hooks for data fetching from the FastAPI backend.
 */

import useSWR, { type SWRConfiguration } from "swr";
import { api, ApiError } from "@/lib/api";

/**
 * Generic SWR fetcher that uses our typed API client.
 */
async function fetcher<T>(endpoint: string): Promise<T> {
  return api.get<T>(endpoint);
}

/**
 * Hook for fetching data from the API with SWR caching.
 *
 * Usage:
 *   const { data, error, isLoading } = useApi<Animal[]>("/api/v1/animals");
 */
export function useApi<T>(
  endpoint: string | null,
  config?: SWRConfiguration<T, ApiError>
) {
  return useSWR<T, ApiError>(endpoint, fetcher, {
    revalidateOnFocus: false,
    ...config,
  });
}
