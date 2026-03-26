/**
 * Shared API response types matching the FastAPI backend schemas.
 * These types are used by the API client and SWR hooks.
 */

// -- Animal types -------------------------------------------------------

export type AnimalStatus =
  | "available"
  | "reserved"
  | "adopted"
  | "fostered"
  | "medical_hold"
  | "intake";

export type AnimalSpecies = "dog" | "cat" | "other";

export type AnimalGender = "male" | "female" | "unknown";

export type AnimalSize = "small" | "medium" | "large" | "extra_large";

export interface Animal {
  id: number;
  name: string;
  species: AnimalSpecies;
  breed: string | null;
  gender: AnimalGender;
  size: AnimalSize;
  age_years: number | null;
  age_months: number | null;
  status: AnimalStatus;
  description: string | null;
  is_sterilized: boolean;
  is_vaccinated: boolean;
  intake_date: string;
  primary_photo_url: string | null;
  created_at: string;
  updated_at: string;
}

// -- Adopter types ------------------------------------------------------

export interface Adopter {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  has_gdpr_consent: boolean;
  created_at: string;
  updated_at: string;
}

// -- Adoption request types ---------------------------------------------

export type AdoptionRequestStatus =
  | "pending"
  | "under_review"
  | "approved"
  | "rejected"
  | "cancelled"
  | "completed";

export interface AdoptionRequest {
  id: number;
  adopter_id: number;
  animal_id: number;
  status: AdoptionRequestStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// -- Donation types -----------------------------------------------------

export type DonationStatus = "pending" | "completed" | "failed" | "refunded";

export interface Donor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  country: string | null;
  is_recurring: boolean;
  has_gdpr_consent: boolean;
  created_at: string;
}

export interface Donation {
  id: number;
  donor_id: number;
  amount_cents: number;
  currency: string;
  status: DonationStatus;
  stripe_payment_intent_id: string | null;
  created_at: string;
}

// -- Pagination ---------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// -- Auth ---------------------------------------------------------------

export interface UserRole {
  role: "admin" | "staff" | "adopter";
}
