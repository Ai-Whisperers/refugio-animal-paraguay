/**
 * Reusable loading spinner for inline and full-page use.
 *
 * Displays a centered animated ring with an optional label beneath it.
 * Uses the brand orange for the spinning arc and a lighter gray for
 * the track, matching the shelter's design language.
 */

interface LoadingSpinnerProps {
  /** Optional accessible label (screen readers). Defaults to "Cargando…" */
  label?: string;
  /** Size variant. Defaults to "md". */
  size?: "sm" | "md" | "lg";
}

const SIZE_CLASSES: Record<NonNullable<LoadingSpinnerProps["size"]>, string> = {
  sm: "h-5 w-5 border-2",
  md: "h-9 w-9 border-4",
  lg: "h-14 w-14 border-4",
};

export default function LoadingSpinner({
  label = "Cargando\u2026",
  size = "md",
}: LoadingSpinnerProps) {
  return (
    <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
      <div className="flex flex-col items-center gap-3">
        <div
          className={`animate-spin rounded-full border-[#E8622A]/20 border-t-[#E8622A] ${SIZE_CLASSES[size]}`}
          aria-hidden="true"
        />
        <p className="text-sm text-gray-500">{label}</p>
        <span className="sr-only">{label}</span>
      </div>
    </div>
  );
}
