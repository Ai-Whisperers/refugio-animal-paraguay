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

export interface UserInfo {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

// --- Animals ---

export type AnimalSpecies = "dog" | "cat" | "bird" | "rabbit" | "other";

export type AnimalSize = "small" | "medium" | "large" | "extra_large";

export type AnimalGender = "male" | "female" | "unknown";

export type AnimalStatus =
  | "available"
  | "adopted"
  | "fostered"
  | "medical_hold"
  | "intake"
  | "reserved";

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
  breed: string | null;
  size: AnimalSize | null;
  gender: AnimalGender | null;
  photos: AnimalPhoto[];
  created_at: string;
  updated_at: string;
}

export interface AnimalCreate {
  name: string;
  species: AnimalSpecies;
  status: AnimalStatus;
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

// --- Adoption Requests ---

export type AdoptionRequestStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "cancelled";

export interface AdoptionRequest {
  id: string;
  animal_id: string;
  adopter_id: string;
  status: AdoptionRequestStatus;
  submitted_at: string;
  decided_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
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
  detail: string;
  status_code: number;
}
