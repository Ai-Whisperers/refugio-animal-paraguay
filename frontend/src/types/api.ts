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

export interface Animal {
  id: number;
  name: string;
  species: string;
  breed: string | null;
  age_years: number | null;
  age_months: number | null;
  gender: string;
  size: string;
  status: AnimalStatus;
  description: string | null;
  intake_date: string;
  photo_url: string | null;
  created_at: string;
  updated_at: string;
}

export type AnimalStatus =
  | "available"
  | "adopted"
  | "fostered"
  | "medical_hold"
  | "intake"
  | "reserved";

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
