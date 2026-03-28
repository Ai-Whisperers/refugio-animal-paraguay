"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getPublicStatistics } from "@/lib/public-api";
import type { PublicStatisticsResponse } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  rescued: "Animales rescatados",
  adopted: "Adopciones exitosas",
  castrated: "Castraciones realizadas",
  volunteers: "Voluntarios activos",
} as const;

// ---------------------------------------------------------------------------
// Fallback values (shown when API fails)
// ---------------------------------------------------------------------------

const FALLBACK_STATS: PublicStatisticsResponse = {
  total_animals_rescued: 150,
  total_adopted: 80,
  total_castrated: 60,
  total_donors: 40,
  total_donations_amount_cents: 0,
  total_volunteers: 50,
  last_updated: new Date().toISOString(),
};

// ---------------------------------------------------------------------------
// Count-up animation hook
// ---------------------------------------------------------------------------

const ANIMATION_DURATION_MS = 2000;
const ANIMATION_STEPS = 60;

function useCountUp(target: number, shouldAnimate: boolean): number {
  const [current, setCurrent] = useState(0);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!shouldAnimate || hasAnimated.current || target === 0) return;
    hasAnimated.current = true;

    const stepDuration = ANIMATION_DURATION_MS / ANIMATION_STEPS;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      // Ease-out cubic for smooth deceleration
      const progress = step / ANIMATION_STEPS;
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(eased * target));

      if (step >= ANIMATION_STEPS) {
        clearInterval(timer);
        setCurrent(target);
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [target, shouldAnimate]);

  return current;
}

// ---------------------------------------------------------------------------
// Stat card with animation
// ---------------------------------------------------------------------------

interface StatItemProps {
  value: number;
  label: string;
  bgClass: string;
  textClass: string;
  shouldAnimate: boolean;
}

function StatItem({
  value,
  label,
  bgClass,
  textClass,
  shouldAnimate,
}: StatItemProps) {
  const displayValue = useCountUp(value, shouldAnimate);

  return (
    <div className={`rounded-xl p-4 sm:p-6 ${bgClass}`}>
      <p className={`text-2xl sm:text-4xl font-bold ${textClass}`}>
        {displayValue.toLocaleString("es-PY")}+
      </p>
      <p className="text-gray-600 mt-2 text-xs sm:text-base font-medium">
        {label}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------

function StatSkeleton() {
  return (
    <div className="rounded-xl p-4 sm:p-6 bg-gray-100 animate-pulse">
      <div className="h-8 sm:h-10 w-20 bg-gray-200 rounded mb-2 mx-auto" />
      <div className="h-4 w-28 bg-gray-200 rounded mx-auto" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function LiveStats() {
  const [stats, setStats] = useState<PublicStatisticsResponse | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [visible, setVisible] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  // Fetch stats on mount
  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await getPublicStatistics();
        setStats(data);
      } catch {
        // Use fallback values on error — don't show error to user
        setStats(FALLBACK_STATS);
      } finally {
        setLoaded(true);
      }
    }
    fetchStats();
  }, []);

  // Intersection Observer — animate only when visible
  const observerCallback = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      if (entries[0]?.isIntersecting) {
        setVisible(true);
      }
    },
    []
  );

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(observerCallback, {
      threshold: 0.3,
    });
    observer.observe(node);

    return () => observer.disconnect();
  }, [observerCallback]);

  const shouldAnimate = loaded && visible;

  return (
    <section ref={sectionRef} className="py-10 sm:py-16 px-4 bg-white">
      <div className="max-w-5xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-8 text-center">
        {!loaded ? (
          <>
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
            <StatSkeleton />
          </>
        ) : (
          <>
            <StatItem
              value={stats?.total_animals_rescued ?? FALLBACK_STATS.total_animals_rescued}
              label={S.rescued}
              bgClass="bg-primary-50"
              textClass="text-primary-600"
              shouldAnimate={shouldAnimate}
            />
            <StatItem
              value={stats?.total_adopted ?? FALLBACK_STATS.total_adopted}
              label={S.adopted}
              bgClass="bg-orange-50"
              textClass="text-orange-600"
              shouldAnimate={shouldAnimate}
            />
            <StatItem
              value={stats?.total_castrated ?? FALLBACK_STATS.total_castrated}
              label={S.castrated}
              bgClass="bg-secondary-50"
              textClass="text-secondary-600"
              shouldAnimate={shouldAnimate}
            />
            <StatItem
              value={stats?.total_volunteers ?? FALLBACK_STATS.total_volunteers}
              label={S.volunteers}
              bgClass="bg-emerald-50"
              textClass="text-emerald-600"
              shouldAnimate={shouldAnimate}
            />
          </>
        )}
      </div>
    </section>
  );
}
