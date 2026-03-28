"use client";

import { useCallback } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface WhatsAppShareButtonProps {
  /** Animal name for the share message. */
  animalName: string;
  /** Species key (dog, cat, other). */
  species: string;
  /** ISO birth date string for age calculation, if available. */
  birthDate?: string | null;
  /** Animal ID used to build the canonical URL. */
  animalId: string;
  /** Visual size variant. */
  size?: "sm" | "md";
  /** Additional CSS classes. */
  className?: string;
}

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  shareLabel: "Compartir en WhatsApp",
  dog: "Perro",
  cat: "Gato",
  other: "Animal",
  unknownAge: "edad desconocida",
} as const;

const SPECIES_MAP: Record<string, string> = {
  dog: S.dog,
  cat: S.cat,
  other: S.other,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? "https://refugioanimal.com.py";

function formatAge(birthDate: string): string {
  const birth = new Date(birthDate);
  const now = new Date();
  const months =
    (now.getFullYear() - birth.getFullYear()) * 12 +
    (now.getMonth() - birth.getMonth());

  if (months < 1) return "recien nacido";
  if (months < 12) return `${months} ${months === 1 ? "mes" : "meses"}`;
  const years = Math.floor(months / 12);
  return `${years} ${years === 1 ? "ano" : "anos"}`;
}

function buildWhatsAppUrl(
  animalName: string,
  species: string,
  birthDate: string | null | undefined,
  animalId: string,
): string {
  const speciesLabel = SPECIES_MAP[species] ?? S.other;
  const ageText = birthDate ? formatAge(birthDate) : S.unknownAge;
  const animalUrl = `${BASE_URL}/animals/${animalId}`;
  const message = `Mira a ${animalName}! ${speciesLabel}, ${ageText}. Esta buscando un hogar. ${animalUrl}`;
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

// ---------------------------------------------------------------------------
// WhatsApp icon (inline SVG — same as ShareWidget for consistency)
// ---------------------------------------------------------------------------

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * Reusable WhatsApp share button for animal cards and detail pages.
 *
 * Opens wa.me with a pre-filled Spanish message containing the animal's
 * name, species, age, and a direct link to the animal's profile.
 *
 * When used inside a parent <Link>, callers should wrap this in a <div>
 * with onClick={e => e.preventDefault()} to prevent navigation.
 */
export default function WhatsAppShareButton({
  animalName,
  species,
  birthDate,
  animalId,
  size = "sm",
  className = "",
}: WhatsAppShareButtonProps) {
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      // Prevent parent Link navigation when used inside card links
      e.preventDefault();
      e.stopPropagation();
      const url = buildWhatsAppUrl(animalName, species, birthDate, animalId);
      window.open(url, "_blank", "noopener,noreferrer");
    },
    [animalName, species, birthDate, animalId],
  );

  const sizeClasses =
    size === "md"
      ? "h-10 w-10"
      : "h-8 w-8";

  const iconClasses =
    size === "md"
      ? "h-5 w-5"
      : "h-4 w-4";

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex items-center justify-center rounded-full bg-[#25D366] text-white shadow-sm hover:bg-[#1fb855] hover:scale-110 transition-all duration-200 ${sizeClasses} ${className}`}
      aria-label={`${S.shareLabel}: ${animalName}`}
      title={S.shareLabel}
    >
      <WhatsAppIcon className={iconClasses} />
    </button>
  );
}
