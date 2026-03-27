"use client";

import { useEffect, useState } from "react";

interface CampaignProgressBarProps {
  /** Percentage of goal reached (0-100+). */
  percentage: number;
  /** Whether the campaign has reached its goal. */
  isCompleted?: boolean;
  /** Height class for the bar (default: "h-3"). */
  height?: string;
  /** Whether to animate the fill on mount. */
  animate?: boolean;
  /** Show percentage label inline. */
  showLabel?: boolean;
}

/**
 * Animated campaign progress bar with color transitions.
 *
 * Fills green when completed, primary color otherwise.
 * Optionally shows the percentage label below the bar.
 */
export default function CampaignProgressBar({
  percentage,
  isCompleted = false,
  height = "h-3",
  animate = true,
  showLabel = false,
}: CampaignProgressBarProps) {
  const capped = Math.min(percentage, 100);
  const [displayWidth, setDisplayWidth] = useState(animate ? 0 : capped);

  useEffect(() => {
    if (!animate) return;
    // Small delay so the animation is visible on mount
    const timer = setTimeout(() => setDisplayWidth(capped), 100);
    return () => clearTimeout(timer);
  }, [capped, animate]);

  const barColor = isCompleted ? "bg-green-500" : "bg-primary-500";

  return (
    <div>
      <div className={`w-full bg-gray-100 rounded-full ${height} overflow-hidden`}>
        <div
          className={`${height} rounded-full transition-all duration-700 ease-out ${barColor}`}
          style={{ width: `${displayWidth}%` }}
          role="progressbar"
          aria-valuenow={Math.round(percentage)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${Math.round(percentage)}% alcanzado`}
        />
      </div>
      {showLabel && (
        <p className={`text-xs mt-1 text-right ${isCompleted ? "text-green-600" : "text-gray-500"}`}>
          {Math.round(percentage)}% alcanzado
        </p>
      )}
    </div>
  );
}
