/**
 * Admin API service layer for staff panel operations.
 *
 * Wraps the generic API client with typed functions for
 * animals CRUD and adoption request management.
 */

import { api } from "./api";
import type {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  AnimalSpecies,
  AnimalStatus,
  AdoptionRequest,
  AdoptionRequestStatus,
  UserInfo,
} from "@/types/api";

// --- Animals ---

interface ListAnimalsParams {
  species?: AnimalSpecies;
  status?: AnimalStatus;
  offset?: number;
  limit?: number;
}

export async function listAnimals(
  params: ListAnimalsParams = {}
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
  return api.get<Animal[]>(endpoint);
}

export async function getAnimal(id: string): Promise<Animal> {
  return api.get<Animal>(`/animals/${id}`);
}

export async function createAnimal(data: AnimalCreate): Promise<Animal> {
  return api.post<Animal>("/animals", data);
}

export async function updateAnimal(
  id: string,
  data: AnimalUpdate
): Promise<Animal> {
  return api.patch<Animal>(`/animals/${id}`, data);
}

export async function deleteAnimal(id: string): Promise<void> {
  return api.delete<void>(`/animals/${id}`);
}

// --- Adoption Requests ---

interface ListAdoptionRequestsParams {
  status?: AdoptionRequestStatus;
  animal_id?: string;
  adopter_id?: string;
  offset?: number;
  limit?: number;
}

export async function listAdoptionRequests(
  params: ListAdoptionRequestsParams = {}
): Promise<AdoptionRequest[]> {
  const searchParams = new URLSearchParams();
  if (params.status) searchParams.set("status", params.status);
  if (params.animal_id) searchParams.set("animal_id", params.animal_id);
  if (params.adopter_id) searchParams.set("adopter_id", params.adopter_id);
  if (params.offset !== undefined)
    searchParams.set("offset", String(params.offset));
  if (params.limit !== undefined)
    searchParams.set("limit", String(params.limit));

  const query = searchParams.toString();
  const endpoint = `/adoption-requests${query ? `?${query}` : ""}`;
  return api.get<AdoptionRequest[]>(endpoint);
}

export async function updateAdoptionRequestStatus(
  id: string,
  status: AdoptionRequestStatus
): Promise<AdoptionRequest> {
  return api.patch<AdoptionRequest>(`/adoption-requests/${id}/status`, {
    status,
  });
}

// --- Auth ---

export async function loginWithCredentials(
  email: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  // Backend uses OAuth2PasswordRequestForm (form-encoded, not JSON)
  const formData = new URLSearchParams();
  formData.set("username", email);
  formData.set("password", password);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/token`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    }
  );

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(errorBody.detail ?? "Invalid credentials");
  }

  return response.json();
}

export async function fetchCurrentUser(): Promise<UserInfo> {
  return api.get<UserInfo>("/auth/me");
}
