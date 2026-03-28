"use client";

/**
 * Responsive container and layout primitives for consistent mobile-first design.
 *
 * Provides standardized max-widths, padding, and responsive grid layouts
 * matching the shelter's Tailwind configuration.
 */

interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  /** Container width variant */
  size?: "sm" | "md" | "lg" | "xl" | "full";
  /** Add horizontal padding */
  padded?: boolean;
}

const SIZE_CLASSES = {
  sm: "max-w-2xl",
  md: "max-w-4xl",
  lg: "max-w-6xl",
  xl: "max-w-7xl",
  full: "max-w-full",
} as const;

/**
 * Responsive container with consistent max-width and padding.
 * Use instead of ad-hoc `max-w-7xl mx-auto px-4` patterns.
 */
export function ResponsiveContainer({
  children,
  className = "",
  size = "xl",
  padded = true,
}: ResponsiveContainerProps) {
  const paddingClass = padded ? "px-4 sm:px-6 lg:px-8" : "";
  return (
    <div className={`mx-auto ${SIZE_CLASSES[size]} ${paddingClass} ${className}`}>
      {children}
    </div>
  );
}

interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  /** Number of columns on different breakpoints */
  cols?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  /** Gap between items */
  gap?: "sm" | "md" | "lg";
}

const GAP_CLASSES = {
  sm: "gap-3 sm:gap-4",
  md: "gap-4 sm:gap-6",
  lg: "gap-6 sm:gap-8",
} as const;

/**
 * Responsive grid that automatically adjusts columns per breakpoint.
 * Mobile-first: starts with 1 column and increases.
 */
export function ResponsiveGrid({
  children,
  className = "",
  cols = { xs: 1, sm: 2, md: 3, lg: 4 },
  gap = "md",
}: ResponsiveGridProps) {
  const colClasses = [
    cols.xs ? `grid-cols-${cols.xs}` : "grid-cols-1",
    cols.sm ? `sm:grid-cols-${cols.sm}` : "",
    cols.md ? `md:grid-cols-${cols.md}` : "",
    cols.lg ? `lg:grid-cols-${cols.lg}` : "",
    cols.xl ? `xl:grid-cols-${cols.xl}` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={`grid ${colClasses} ${GAP_CLASSES[gap]} ${className}`}>
      {children}
    </div>
  );
}

/**
 * Responsive stack that switches from vertical to horizontal layout.
 * Useful for form rows, action bars, and card layouts.
 */
export function ResponsiveStack({
  children,
  className = "",
  breakAt = "sm",
  gap = "md",
  align = "start",
}: {
  children: React.ReactNode;
  className?: string;
  /** Breakpoint where layout switches from vertical to horizontal */
  breakAt?: "sm" | "md" | "lg";
  gap?: "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
}) {
  const ALIGN_MAP = {
    start: "items-start",
    center: "items-center",
    end: "items-end",
    stretch: "items-stretch",
  } as const;

  const DIRECTION_MAP = {
    sm: "flex-col sm:flex-row",
    md: "flex-col md:flex-row",
    lg: "flex-col lg:flex-row",
  } as const;

  return (
    <div
      className={`flex ${DIRECTION_MAP[breakAt]} ${GAP_CLASSES[gap]} ${ALIGN_MAP[align]} ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Hide/show content based on screen size.
 * Cleaner alternative to inline `hidden md:block` patterns.
 */
export function ResponsiveShow({
  children,
  above,
  below,
}: {
  children: React.ReactNode;
  /** Show only above this breakpoint */
  above?: "sm" | "md" | "lg" | "xl";
  /** Show only below this breakpoint */
  below?: "sm" | "md" | "lg" | "xl";
}) {
  const ABOVE_MAP = {
    sm: "hidden sm:block",
    md: "hidden md:block",
    lg: "hidden lg:block",
    xl: "hidden xl:block",
  } as const;

  const BELOW_MAP = {
    sm: "sm:hidden",
    md: "md:hidden",
    lg: "lg:hidden",
    xl: "xl:hidden",
  } as const;

  const visibilityClass = above
    ? ABOVE_MAP[above]
    : below
      ? BELOW_MAP[below]
      : "";

  return <div className={visibilityClass}>{children}</div>;
}

/**
 * Responsive image container that maintains aspect ratio.
 * Prevents layout shift by reserving space before image loads.
 */
export function ResponsiveImage({
  children,
  className = "",
  aspectRatio = "16/9",
}: {
  children: React.ReactNode;
  className?: string;
  aspectRatio?: "1/1" | "4/3" | "16/9" | "3/2" | "21/9";
}) {
  const RATIO_MAP = {
    "1/1": "aspect-square",
    "4/3": "aspect-[4/3]",
    "16/9": "aspect-video",
    "3/2": "aspect-[3/2]",
    "21/9": "aspect-[21/9]",
  } as const;

  return (
    <div className={`relative overflow-hidden ${RATIO_MAP[aspectRatio]} ${className}`}>
      {children}
    </div>
  );
}
