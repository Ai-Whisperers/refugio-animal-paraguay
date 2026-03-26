import type { AnimalSpecies } from "@/types/api";
import { speciesEmoji } from "@/lib/animal-utils";

interface AnimalPlaceholderProps {
  species: AnimalSpecies;
  className?: string;
}

/** Placeholder image when no photo is available for an animal. */
export default function AnimalPlaceholder({
  species,
  className = "w-full h-48 bg-gray-100 flex items-center justify-center text-5xl",
}: AnimalPlaceholderProps) {
  return (
    <div className={className}>
      {speciesEmoji(species)}
    </div>
  );
}
