import type { AnimalSpecies, AnimalStatus } from "@/types/api";

/** Human-readable status labels for display. */
export const STATUS_LABELS: Record<AnimalStatus, string> = {
  intake: "New Arrival",
  quarantine: "Quarantine",
  available: "Available",
  foster: "In Foster",
  under_treatment: "Under Treatment",
  adopted: "Adopted",
  deceased: "Deceased",
};

/** Tailwind CSS classes for status badge colors. */
export function statusBadgeClass(status: AnimalStatus): string {
  switch (status) {
    case "available":
      return "bg-green-100 text-green-800";
    case "adopted":
      return "bg-blue-100 text-blue-800";
    case "foster":
      return "bg-purple-100 text-purple-800";
    case "under_treatment":
      return "bg-yellow-100 text-yellow-800";
    case "quarantine":
      return "bg-red-100 text-red-800";
    case "intake":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

/** Calculate a human-readable age string from a birth date. */
export function calculateAge(birthDate: string): string {
  const birth = new Date(birthDate);
  const now = new Date();
  const months =
    (now.getFullYear() - birth.getFullYear()) * 12 +
    (now.getMonth() - birth.getMonth());

  if (months < 1) return "< 1 month";
  if (months < 12) return `${months} month${months === 1 ? "" : "s"}`;

  const years = Math.floor(months / 12);
  const remainingMonths = months % 12;
  if (remainingMonths === 0) return `${years} year${years === 1 ? "" : "s"}`;
  return `${years}y ${remainingMonths}m`;
}

/** Emoji placeholder for animals without photos. */
export function speciesEmoji(species: AnimalSpecies): string {
  switch (species) {
    case "dog":
      return "\u{1F415}";
    case "cat":
      return "\u{1F408}";
    default:
      return "\u{1F43E}";
  }
}
