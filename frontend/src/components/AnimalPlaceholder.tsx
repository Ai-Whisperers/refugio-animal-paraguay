import type { AnimalSpecies } from "@/types/api";

interface AnimalPlaceholderProps {
  species: AnimalSpecies;
  className?: string;
}

/**
 * Branded SVG placeholder when no photo is available for an animal.
 * Uses shelter primary color and species-specific silhouettes.
 */
export default function AnimalPlaceholder({
  species,
  className = "w-full aspect-[4/3] bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center",
}: AnimalPlaceholderProps) {
  return (
    <div className={className}>
      <svg
        width="80"
        height="80"
        viewBox="0 0 80 80"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="opacity-40"
      >
        {species === "dog" ? (
          /* Dog silhouette */
          <path
            d="M40 12c-2 0-4 1-5 3l-6 10c-1 2-3 3-5 3h-4c-3 0-5 2-5 5v12c0 3 2 5 5 5h2v18c0 2 2 4 4 4h6c2 0 4-2 4-4V56h8v12c0 2 2 4 4 4h6c2 0 4-2 4-4V50h2c3 0 5-2 5-5V33c0-3-2-5-5-5h-4c-2 0-4-1-5-3l-6-10c-1-2-3-3-5-3z"
            fill="#E8622A"
          />
        ) : species === "cat" ? (
          /* Cat silhouette */
          <path
            d="M28 20l-4-12c-1-2 1-4 3-3l8 4h10l8-4c2-1 4 1 3 3l-4 12c4 3 6 8 6 14v14c0 3-2 5-5 5h-4v10c0 2-2 3-3 3h-4c-2 0-3-1-3-3V53h-8v10c0 2-1 3-3 3h-4c-2 0-3-1-3-3V53h-4c-3 0-5-2-5-5V34c0-6 2-11 6-14z"
            fill="#E8622A"
          />
        ) : (
          /* Generic paw print */
          <>
            <ellipse cx="30" cy="24" rx="6" ry="7" fill="#E8622A" />
            <ellipse cx="50" cy="24" rx="6" ry="7" fill="#E8622A" />
            <ellipse cx="22" cy="38" rx="5" ry="6" fill="#E8622A" />
            <ellipse cx="58" cy="38" rx="5" ry="6" fill="#E8622A" />
            <ellipse cx="40" cy="52" rx="12" ry="10" fill="#E8622A" />
          </>
        )}
      </svg>
    </div>
  );
}
