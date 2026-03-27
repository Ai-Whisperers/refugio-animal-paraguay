/**
 * Animal status transition rules and display metadata.
 *
 * Mirrors the backend transition map in src/services/animal_status.py.
 * Shared by StatusWorkflowModal (RAP-107) and batch operations (RAP-108).
 */

import type { AnimalStatus } from "@/types/api";

// Valid status transitions — must stay in sync with backend
export const VALID_TRANSITIONS: Record<AnimalStatus, AnimalStatus[]> = {
  intake: ["quarantine", "available", "under_treatment"],
  quarantine: ["available", "under_treatment", "deceased"],
  available: ["foster", "adopted", "under_treatment", "quarantine", "deceased"],
  foster: ["available", "adopted", "under_treatment", "deceased"],
  under_treatment: ["available", "quarantine", "foster", "deceased"],
  adopted: ["available"],
  deceased: [],
};

export const STATUS_LABELS: Record<AnimalStatus, string> = {
  intake: "Ingreso",
  quarantine: "Cuarentena",
  available: "Disponible",
  foster: "Acogida",
  under_treatment: "En tratamiento",
  adopted: "Adoptado",
  deceased: "Fallecido",
};

export const STATUS_COLORS: Record<AnimalStatus, string> = {
  intake: "bg-yellow-100 text-yellow-800",
  quarantine: "bg-orange-100 text-orange-800",
  available: "bg-green-100 text-green-800",
  foster: "bg-blue-100 text-blue-800",
  under_treatment: "bg-red-100 text-red-800",
  adopted: "bg-purple-100 text-purple-800",
  deceased: "bg-gray-100 text-gray-500",
};

/**
 * Given a set of current statuses, return the valid transitions
 * that ALL animals share in common (intersection).
 */
export function getCommonTransitions(statuses: AnimalStatus[]): AnimalStatus[] {
  if (statuses.length === 0) return [];

  const sets = statuses.map(
    (s) => new Set(VALID_TRANSITIONS[s] ?? [])
  );

  const first = sets[0];
  return [...first].filter((status) =>
    sets.every((set) => set.has(status))
  );
}
