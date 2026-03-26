/**
 * Shared API types for the Refugio Animal Paraguay frontend.
 * These mirror the backend Pydantic schemas.
 */

// --- Auth ---

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface TokenPayload {
  sub: string;
  role: UserRole;
  exp: number;
}

export type UserRole = "admin" | "staff" | "adopter";

// --- Animals ---

export type AnimalSpecies = "dog" | "cat" | "other";

export type AnimalStatus =
  | "intake"
  | "quarantine"
  | "available"
  | "foster"
  | "under_treatment"
  | "adopted"
  | "deceased";

export interface AnimalPhoto {
  id: string;
  animal_id: string;
  url: string;
  caption: string | null;
  display_order: number;
  created_at: string;
}

export interface Animal {
  id: string;
  name: string;
  species: AnimalSpecies;
  status: AnimalStatus;
  birth_date: string | null;
  description: string | null;
  primary_photo_url: string | null;
  photos: AnimalPhoto[];
  created_at: string;
  updated_at: string;
}

export interface AnimalCreate {
  name: string;
  species?: AnimalSpecies;
  status?: AnimalStatus;
  birth_date?: string | null;
  description?: string | null;
  primary_photo_url?: string | null;
}

export interface AnimalUpdate {
  name?: string;
  species?: AnimalSpecies;
  status?: AnimalStatus;
  birth_date?: string | null;
  description?: string | null;
  primary_photo_url?: string | null;
}

// --- Adoption Applications (Public) ---

export interface PublicAdoptionApplicationCreate {
  animal_id: string;
  full_name: string;
  email: string;
  phone?: string;
  message?: string;
  gdpr_consent: boolean;
}

export interface PublicAdoptionApplicationResponse {
  id: string;
  animal_id: string;
  status: string;
  submitted_at: string;
  message: string;
}

// --- Pagination ---

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// --- Campaigns ---

export type CampaignStatus = "draft" | "active" | "completed" | "cancelled";

export type FundCategory =
  | "medical"
  | "food"
  | "operations"
  | "rescue"
  | "infrastructure"
  | "general";

export type CurrencyCode = "EUR" | "PYG" | "USD";

export interface CampaignPublic {
  id: string;
  title: string;
  description: string;
  impact_story: string | null;
  target_amount_cents: number;
  raised_amount_cents: number;
  currency: CurrencyCode;
  fund_category: FundCategory;
  status: CampaignStatus;
  image_url: string | null;
  deadline: string | null;
  min_donation_cents: number | null;
  max_donation_cents: number | null;
  allow_overfunding: boolean;
  donation_count: number;
  progress_percentage: number;
  created_at: string;
}

export interface CampaignListResponse {
  items: CampaignPublic[];
  total: number;
  page: number;
  page_size: number;
}

export interface DonationCreateRequest {
  donor_id?: string | null;
  campaign_id?: string | null;
  amount_cents: number;
  currency: CurrencyCode;
  payment_method: "stripe" | "cash" | "transfer";
  notes?: string | null;
}

export interface DonationResponse {
  id: string;
  donor_id: string | null;
  amount_cents: number;
  currency: CurrencyCode;
  payment_method: string;
  stripe_payment_intent_id: string | null;
  status: string;
  fund_category: string | null;
  receipt_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface DonorCreateRequest {
  full_name: string;
  email: string;
  country?: string;
  currency_preference?: CurrencyCode;
  gdpr_consent_at?: string;
}

export interface DonorResponse {
  id: string;
  full_name: string;
  email: string;
  country: string | null;
  currency_preference: CurrencyCode;
  gdpr_consent_at: string | null;
  created_at: string;
  updated_at: string;
}

// --- API Error ---

export interface ApiError {
  detail?: string;
  message?: string;
  error_code?: string;
  status_code?: number;
}
