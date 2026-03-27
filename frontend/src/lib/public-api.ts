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
  AnimalSize,
  AnimalGender,
  CampaignListResponse,
  CampaignPublic,
  DonationCreateRequest,
  DonationResponse,
  DonorCreateRequest,
  DonorResponse,
  FundCategory,
  PaginatedAnimalListResponse,
  PublicAdoptionApplicationCreate,
  PublicAdoptionApplicationResponse,
} from "@/types/api";

const NO_AUTH = { requiresAuth: false } as const;

/** Query parameters for filtering the public animal listing. */
export interface AnimalListParams {
  species?: AnimalSpecies;
  size?: AnimalSize;
  gender?: AnimalGender;
  breed?: string;
  min_age_months?: number;
  max_age_months?: number;
  search?: string;
  page?: number;
  page_size?: number;
}

/**
 * Fetch a paginated/filtered list of available animals (no auth required).
 * Calls GET /public/animals — returns only animals with status=available.
 */
export async function listAnimalsPublic(
  params: AnimalListParams = {}
): Promise<PaginatedAnimalListResponse> {
  const searchParams = new URLSearchParams();
  if (params.species) searchParams.set("species", params.species);
  if (params.size) searchParams.set("size", params.size);
  if (params.gender) searchParams.set("gender", params.gender);
  if (params.breed) searchParams.set("breed", params.breed);
  if (params.min_age_months !== undefined)
    searchParams.set("min_age_months", String(params.min_age_months));
  if (params.max_age_months !== undefined)
    searchParams.set("max_age_months", String(params.max_age_months));
  if (params.search) searchParams.set("search", params.search);
  if (params.page !== undefined)
    searchParams.set("page", String(params.page));
  if (params.page_size !== undefined)
    searchParams.set("page_size", String(params.page_size));

  const query = searchParams.toString();
  const endpoint = `/public/animals${query ? `?${query}` : ""}`;
  return api.get<PaginatedAnimalListResponse>(endpoint, NO_AUTH);
}

/**
 * Fetch a single available animal by ID (no auth required).
 * Returns 404 if the animal doesn't exist or is not available.
 */
export async function getAnimalPublic(animalId: string): Promise<Animal> {
  return api.get<Animal>(`/public/animals/${animalId}`, NO_AUTH);
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

// --- Campaigns ---

/** Query parameters for filtering campaign listings. */
export interface CampaignListParams {
  category?: FundCategory;
  page?: number;
  page_size?: number;
}

/**
 * Fetch a list of active campaigns with progress stats (no auth required).
 */
export async function listCampaignsPublic(
  params: CampaignListParams = {}
): Promise<CampaignListResponse> {
  const searchParams = new URLSearchParams();
  if (params.category) searchParams.set("category", params.category);
  if (params.page !== undefined)
    searchParams.set("page", String(params.page));
  if (params.page_size !== undefined)
    searchParams.set("page_size", String(params.page_size));

  const query = searchParams.toString();
  const endpoint = `/public/campaigns${query ? `?${query}` : ""}`;
  return api.get<CampaignListResponse>(endpoint, NO_AUTH);
}

/**
 * Fetch a single campaign by ID (no auth required).
 */
export async function getCampaignPublic(
  campaignId: string
): Promise<CampaignPublic> {
  return api.get<CampaignPublic>(`/public/campaigns/${campaignId}`, NO_AUTH);
}

// --- Donations (public) ---

/**
 * Create a donation record (no auth required, anonymous donations allowed).
 */
export async function createDonation(
  data: DonationCreateRequest
): Promise<DonationResponse> {
  return api.post<DonationResponse>("/donations", data, NO_AUTH);
}

/**
 * Create a donor profile (no auth required).
 */
export async function createDonor(
  data: DonorCreateRequest
): Promise<DonorResponse> {
  return api.post<DonorResponse>("/donors", data, NO_AUTH);
}
