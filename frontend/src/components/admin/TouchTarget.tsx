"use client";

import { forwardRef } from "react";

/**
 * Touch target wrapper that ensures minimum 44x44px interactive area
 * per WCAG 2.1 Success Criterion 2.5.5 (Target Size).
 *
 * Use around small interactive elements in the admin interface
 * to ensure they are easily tappable on touch devices.
 */

interface TouchTargetProps {
  children: React.ReactNode;
  className?: string;
  as?: "button" | "div" | "span";
  onClick?: () => void;
}

const TouchTarget = forwardRef<HTMLElement, TouchTargetProps>(
  ({ children, className = "", as: Component = "div", onClick, ...props }, ref) => {
    return (
      <Component
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ref={ref as any}
        className={`relative inline-flex items-center justify-center min-h-[44px] min-w-[44px] ${className}`}
        onClick={onClick}
        {...props}
      >
        {children}
      </Component>
    );
  },
);

TouchTarget.displayName = "TouchTarget";

export default TouchTarget;

/**
 * Admin-specific touch-friendly CSS classes.
 * Import and spread these into component classNames for consistent touch UX.
 */
export const TOUCH_CLASSES = {
  /** Minimum 44px touch target for buttons and links */
  target: "min-h-[44px] min-w-[44px]",
  /** Touch-friendly table row with larger padding */
  tableRow: "py-3 px-4 sm:py-2 sm:px-3",
  /** Touch-friendly form input */
  input: "h-12 sm:h-10 text-base sm:text-sm px-4 sm:px-3",
  /** Touch-friendly select */
  select: "h-12 sm:h-10 text-base sm:text-sm px-4 sm:px-3",
  /** Touch-friendly button */
  button: "min-h-[44px] px-4 py-2.5 sm:min-h-0 sm:px-3 sm:py-1.5 text-base sm:text-sm",
  /** Larger checkbox/radio for touch */
  checkbox: "h-5 w-5 sm:h-4 sm:w-4",
  /** Spacing between interactive elements to prevent mis-taps */
  gap: "gap-3 sm:gap-2",
} as const;

/**
 * Responsive table wrapper that enables horizontal scrolling on small screens.
 * Adds touch-friendly overflow hints (fade edges) and momentum scrolling.
 */
export function TouchScrollTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0 touch-pan-x">
      <div className="inline-block min-w-full align-middle px-4 sm:px-0">
        {children}
      </div>
    </div>
  );
}

/**
 * Pull-to-refresh indicator for touch devices.
 * Shows a loading spinner when the user pulls down at the top of a list.
 */
export function PullToRefreshIndicator({
  isRefreshing,
  label = "Actualizando...",
}: {
  isRefreshing: boolean;
  label?: string;
}) {
  if (!isRefreshing) return null;

  return (
    <div className="flex items-center justify-center py-3 text-sm text-warm-text-secondary animate-pulse">
      <svg
        className="h-4 w-4 mr-2 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {label}
    </div>
  );
}
