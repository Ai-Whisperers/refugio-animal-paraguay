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
  StripeIntentResponse,
  CampaignListResponse,
  CampaignPublic,
  DonationCreateRequest,
  DonationResponse,
  DonorCreateRequest,
  DonorResponse,
  FundCategory,
  PublicAdoptionApplicationCreate,
  PublicAdoptionApplicationResponse,
} from "@/types/api";

const NO_AUTH = { requiresAuth: false } as const;

/** Query parameters for filtering animal listings. */
export interface AnimalListParams {
  species?: AnimalSpecies;
  status?: AnimalStatus;
  size?: string;
  age_min?: number;
  age_max?: number;
  search?: string;
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
  if (params.size) searchParams.set("size", params.size);
  if (params.age_min !== undefined)
    searchParams.set("age_min", String(params.age_min));
  if (params.age_max !== undefined)
    searchParams.set("age_max", String(params.age_max));
  if (params.search) searchParams.set("search", params.search);
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
 * Create a Stripe PaymentIntent for an existing pending donation.
 * Returns a client_secret to confirm the payment with Stripe.js.
 * POST /donations/{donationId}/stripe-intent (no auth required).
 */
export async function createStripeIntent(
  donationId: string
): Promise<StripeIntentResponse> {
  return api.post<StripeIntentResponse>(
    `/donations/${donationId}/stripe-intent`,
    {},
    NO_AUTH
  );
}

/**
 * Create a donor profile (no auth required).
 */
export async function createDonor(
  data: DonorCreateRequest
): Promise<DonorResponse> {
  return api.post<DonorResponse>("/donors", data, NO_AUTH);
}
