/**
 * Public API client for unauthenticated endpoints.
 *
 * Used by the public-facing pages: animal browsing, detail, and
 * adoption application submission. All requests skip JWT injection.
 */

import { api } from "./api";
import type {
  Animal,
  AnimalSpecies,
  AnimalStatus,
  PublicAdoptionApplicationCreate,
  PublicAdoptionApplicationResponse,
} from "@/types/api";

const NO_AUTH = { requiresAuth: false } as const;

/** Query parameters for filtering animal listings. */
export interface AnimalListParams {
  species?: AnimalSpecies;
  status?: AnimalStatus;
  offset?: number;
  limit?: number;
}

/**
 * Fetch a paginated/filtered list of animals (no auth required).
 * The backend GET /animals does not require authentication.
 */
export async function listAnimalsPublic(
  params: AnimalListParams = {}
): Promise<Animal[]> {
  const searchParams = new URLSearchParams();
  if (params.species) searchParams.set("species", params.species);
  if (params.status) searchParams.set("status", params.status);
  if (params.offset !== undefined)
    searchParams.set("offset", String(params.offset));
  if (params.limit !== undefined)
    searchParams.set("limit", String(params.limit));

  const query = searchParams.toString();
  const endpoint = `/animals${query ? `?${query}` : ""}`;
  return api.get<Animal[]>(endpoint, NO_AUTH);
}

/**
 * Fetch a single animal by ID (no auth required).
 */
export async function getAnimalPublic(animalId: string): Promise<Animal> {
  return api.get<Animal>(`/animals/${animalId}`, NO_AUTH);
}

/**
 * Submit a public adoption application.
 * POST /public/adoption-applications (rate limited, no auth).
 */
export async function submitAdoptionApplication(
  data: PublicAdoptionApplicationCreate
): Promise<PublicAdoptionApplicationResponse> {
  return api.post<PublicAdoptionApplicationResponse>(
    "/public/adoption-applications",
    data,
    NO_AUTH
  );
}
