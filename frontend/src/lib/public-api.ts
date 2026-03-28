/**
 * Public API client for unauthenticated endpoints.
 *
 * Used by the public-facing pages: animal browsing, detail, and
 * adoption application submission. All requests skip JWT injection.
 *
 * Also exports ApiError and apiFetch for centralized error handling
 * across all public API calls.
 */

import { api } from "./api";

// --- Centralized error class ---

/**
 * Structured API error thrown by apiFetch when the backend returns
 * a non-2xx response.
 *
 * Satisfies the ApiError type from error-handling.ts, enabling
 * getErrorMessage() and getRecoveryAction() to work with these errors.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly error_code: string,
    public readonly detail: string
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Centralized fetch wrapper for public (no-auth) API calls.
 *
 * Parses error responses into ApiError instances so callers can use
 * getErrorMessage() and getRecoveryAction() from error-handling.ts.
 * Network failures (DNS, timeout, etc.) are re-thrown as plain Error.
 */
export async function apiFetch<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      `Network error — unable to reach ${endpoint}. Please check your connection.`
    );
  }

  if (!response.ok) {
    let error_code = "UNKNOWN_ERROR";
    let detail = "Unknown error";
    try {
      const body = (await response.json()) as {
        error_code?: string;
        detail?: string;
        message?: string;
      };
      if (body.error_code) error_code = body.error_code;
      detail = body.detail ?? body.message ?? detail;
    } catch {
      // Response body was not JSON — keep defaults
    }
    throw new ApiError(response.status, error_code, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
import type {
  Animal,
  AnimalSpecies,
  AnimalSize,
  AnimalGender,
  CampaignListResponse,
  CampaignPublic,
  CastrationGalleryResponse,
  CampaignSocialProof,
  CastrationCampaignPublic,
  CastrationCampaignListResponse,
  CastrationDriveListResponse,
  DonationCreateRequest,
  DonationResponse,
  ImpactReportResponse,
  ImpactResponse,
  DonorCreateRequest,
  DonorResponse,
  FundCategory,
  LeaderboardResponse,
  PaginatedAnimalListResponse,
  PreQualifyQuestionsResponse,
  PreQualifyRequest,
  PreQualifyResult,
  PublicAdoptionApplicationCreate,
  PublicAdoptionApplicationResponse,
  PublicClinicDetail,
  PublicClinicListResponse,
  ClinicFundingStats,
  ClinicFundRequest,
  ClinicFundResponse,
  PublicStatisticsResponse,
  StripeIntentResponse,
  SubscriptionCreateRequest,
  SubscriptionDetailResponse,
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
  featured?: boolean;
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
  if (params.featured !== undefined)
    searchParams.set("featured", String(params.featured));
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
  featured?: boolean;
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
  if (params.featured !== undefined)
    searchParams.set("featured", String(params.featured));
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

/**
 * Fetch social proof data for a campaign (no auth required).
 * Includes donor count, momentum, and recent donors list.
 */
export async function getCampaignSocialProof(
  campaignId: string
): Promise<CampaignSocialProof> {
  return api.get<CampaignSocialProof>(
    `/public/campaigns/${campaignId}/social-proof`,
    NO_AUTH
  );
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

/**
 * Create a Stripe PaymentIntent for an existing pending donation.
 * Returns a client_secret to pass to Stripe.js confirmPayment().
 * POST /donations/{donationId}/stripe-intent (no auth required — public campaign flow)
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

// --- Subscriptions (Recurring Donations) ---

/**
 * Create a recurring donation subscription via Stripe.
 * POST /subscriptions (no auth required — public monthly giving flow)
 */
export async function createSubscription(
  data: SubscriptionCreateRequest
): Promise<SubscriptionDetailResponse> {
  return api.post<SubscriptionDetailResponse>("/subscriptions", data, NO_AUTH);
}

/**
 * Fetch subscriptions for a specific donor.
 * GET /subscriptions/donor/{donorId}
 */
export async function getDonorSubscriptions(
  donorId: string
): Promise<SubscriptionDetailResponse[]> {
  return api.get<SubscriptionDetailResponse[]>(
    `/subscriptions/donor/${donorId}`,
    NO_AUTH
  );
}

/**
 * Fetch a single subscription by ID.
 * GET /subscriptions/{subscriptionId}
 */
export async function getSubscription(
  subscriptionId: string
): Promise<SubscriptionDetailResponse> {
  return api.get<SubscriptionDetailResponse>(
    `/subscriptions/${subscriptionId}`,
    NO_AUTH
  );
}

/**
 * Pause an active subscription.
 * POST /subscriptions/{subscriptionId}/pause
 */
export async function pauseSubscription(
  subscriptionId: string
): Promise<SubscriptionDetailResponse> {
  return api.post<SubscriptionDetailResponse>(
    `/subscriptions/${subscriptionId}/pause`,
    {},
    NO_AUTH
  );
}

/**
 * Resume a paused subscription.
 * POST /subscriptions/{subscriptionId}/resume
 */
export async function resumeSubscription(
  subscriptionId: string
): Promise<SubscriptionDetailResponse> {
  return api.post<SubscriptionDetailResponse>(
    `/subscriptions/${subscriptionId}/resume`,
    {},
    NO_AUTH
  );
}

/**
 * Cancel a subscription.
 * POST /subscriptions/{subscriptionId}/cancel
 */
export async function cancelSubscription(
  subscriptionId: string,
  cancelImmediately: boolean = false,
  reason?: string
): Promise<SubscriptionDetailResponse> {
  return api.post<SubscriptionDetailResponse>(
    `/subscriptions/${subscriptionId}/cancel`,
    {
      cancel_immediately: cancelImmediately,
      reason: reason ?? null,
    },
    NO_AUTH
  );
}

/**
 * Update a subscription (amount, notes).
 * PATCH /subscriptions/{subscriptionId}
 */
export async function updateSubscription(
  subscriptionId: string,
  data: { amount_cents?: number; notes?: string | null }
): Promise<SubscriptionDetailResponse> {
  return api.patch<SubscriptionDetailResponse>(
    `/subscriptions/${subscriptionId}`,
    data,
    NO_AUTH
  );
}

// --- Pre-Qualification ---

/**
 * Fetch pre-qualification questions for an animal.
 * GET /api/animals/{animalId}/pre-qualify (requires auth — staff token).
 */
export async function getPreQualifyQuestions(
  animalId: string
): Promise<PreQualifyQuestionsResponse> {
  return apiFetch<PreQualifyQuestionsResponse>(
    `/api/animals/${animalId}/pre-qualify`
  );
}

/**
 * Submit pre-qualification answers and get result.
 * POST /api/adoption/pre-qualify (requires auth — staff token).
 */
export async function submitPreQualification(
  data: PreQualifyRequest
): Promise<PreQualifyResult> {
  return apiFetch<PreQualifyResult>("/api/adoption/pre-qualify", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// --- Castration Campaigns (public) ---

/**
 * Fetch list of public castration campaigns (active + completed).
 */
export async function listCastrationCampaignsPublic(): Promise<CastrationCampaignListResponse> {
  return api.get<CastrationCampaignListResponse>(
    "/public/castration-campaigns",
    NO_AUTH
  );
}

/**
 * Fetch a single castration campaign by ID (public).
 */
export async function getCastrationCampaignPublic(
  campaignId: string
): Promise<CastrationCampaignPublic> {
  return api.get<CastrationCampaignPublic>(
    `/public/castration-campaigns/${campaignId}`,
    NO_AUTH
  );
}

// --- Castration Drives ---

/**
 * Fetch upcoming castration drives for a campaign.
 * GET /public/castration-campaigns/{campaignId}/drives
 */
export async function getCastrationCampaignDrives(
  campaignId: string,
  page = 1,
  pageSize = 20,
  includePast = false
): Promise<CastrationDriveListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (includePast) params.set("include_past", "true");
  return apiFetch<CastrationDriveListResponse>(
    `/public/castration-campaigns/${campaignId}/drives?${params}`
  );
}

// --- Castration Campaign Gallery ---

/**
 * Fetch public gallery photos for a castration campaign.
 * GET /public/castration-campaigns/{campaignId}/gallery
 */
export async function getCastrationCampaignGallery(
  campaignId: string,
  page = 1,
  pageSize = 20,
  photoType?: string
): Promise<CastrationGalleryResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (photoType) params.set("photo_type", photoType);
  return apiFetch<CastrationGalleryResponse>(
    `/public/castration-campaigns/${campaignId}/gallery?${params}`
  );
}

// --- Donor Leaderboard ---

/**
 * Fetch public donor leaderboard.
 * GET /public/leaderboard/donors
 */
export async function getDonorLeaderboard(
  currency = "EUR",
  limit = 20,
  offset = 0,
  campaignId?: string
): Promise<LeaderboardResponse> {
  const params = new URLSearchParams({
    currency,
    limit: String(limit),
    offset: String(offset),
  });
  if (campaignId) params.set("campaign_id", campaignId);
  return apiFetch<LeaderboardResponse>(
    `/public/leaderboard/donors?${params}`
  );
}

// --- Castration Impact Report ---

/**
 * Fetch the impact report for a castration campaign.
 * GET /public/castration-campaigns/{campaignId}/report
 */
export async function getCastrationCampaignReport(
  campaignId: string
): Promise<ImpactReportResponse> {
  return apiFetch<ImpactReportResponse>(
    `/public/castration-campaigns/${campaignId}/report`
  );
}
// --- Public Statistics ---

/**
 * Fetch public shelter statistics (cached 5 min).
 * GET /api/stats/public
 */
export async function getPublicStatistics(): Promise<PublicStatisticsResponse> {
  return apiFetch<PublicStatisticsResponse>("/api/stats/public");
}

/**
 * Fetch public impact statistics (monthly aggregates, cached 1 hour).
 * GET /api/stats/impact
 */
export async function getImpactStatistics(): Promise<ImpactResponse> {
  return apiFetch<ImpactResponse>("/api/stats/impact");
}

// --- Public Clinic Fund ---

/**
 * Fetch list of active clinics (public, no auth).
 * GET /public/clinics
 */
export async function listClinicsPublic(
  city?: string,
  page = 1,
  pageSize = 20
): Promise<PublicClinicListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (city) params.set("city", city);
  return apiFetch<PublicClinicListResponse>(`/public/clinics?${params}`);
}

/**
 * Fetch a single clinic with services (public, no auth).
 * GET /public/clinics/{clinicId}
 */
export async function getClinicPublic(
  clinicId: string
): Promise<PublicClinicDetail> {
  return apiFetch<PublicClinicDetail>(`/public/clinics/${clinicId}`);
}

/**
 * Fetch funding stats for a clinic (public, no auth).
 * GET /public/clinics/{clinicId}/stats
 */
export async function getClinicFundingStats(
  clinicId: string
): Promise<ClinicFundingStats> {
  return apiFetch<ClinicFundingStats>(`/public/clinics/${clinicId}/stats`);
}

/**
 * Create a clinic-targeted donation (public, no auth).
 * POST /public/clinic-fund
 */
export async function createClinicFundDonation(
  data: ClinicFundRequest
): Promise<ClinicFundResponse> {
  return apiFetch<ClinicFundResponse>("/public/clinic-fund", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
