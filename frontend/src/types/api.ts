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

// --- API Error ---

export interface ApiError {
  detail?: string;
  message?: string;
  error_code?: string;
  status_code?: number;
}
