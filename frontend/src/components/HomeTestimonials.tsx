"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";

import { getHomepageTestimonials } from "@/lib/public-api";
import type { HomepageTestimonial } from "@/lib/public-api";
import { HOME } from "@/lib/strings";

// ---------------------------------------------------------------------------
// Fallback data — used when CMS has no entries
// ---------------------------------------------------------------------------

const FALLBACK_TESTIMONIALS: HomepageTestimonial[] = HOME.testimonials.map(
  (t) => ({
    quote: t.quote,
    name: t.name,
    animal: t.animal,
  })
);

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------

function TestimonialSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 sm:p-8 animate-pulse"
        >
          <div className="flex gap-1 mb-4">
            {[0, 1, 2, 3, 4].map((s) => (
              <div key={s} className="h-5 w-5 rounded bg-orange-200" />
            ))}
          </div>
          <div className="h-4 w-full bg-white/60 rounded mb-2" />
          <div className="h-4 w-3/4 bg-white/60 rounded mb-4" />
          <div className="border-t border-primary-200 pt-4">
            <div className="h-4 w-24 bg-white/60 rounded mb-1" />
            <div className="h-3 w-20 bg-white/60 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Star rating display
// ---------------------------------------------------------------------------

function StarRating() {
  return (
    <div className="flex gap-1 mb-4">
      {[0, 1, 2, 3, 4].map((i) => (
        <Star
          key={i}
          className="h-5 w-5 text-orange-400 fill-orange-400"
          aria-hidden="true"
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function HomeTestimonials() {
  const [testimonials, setTestimonials] = useState<
    HomepageTestimonial[] | null
  >(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchTestimonials() {
      try {
        const data = await getHomepageTestimonials();
        if (!cancelled) {
          setTestimonials(
            data.items.length > 0 ? data.items : FALLBACK_TESTIMONIALS
          );
        }
      } catch {
        if (!cancelled) {
          setTestimonials(FALLBACK_TESTIMONIALS);
        }
      } finally {
        if (!cancelled) {
          setLoaded(true);
        }
      }
    }

    fetchTestimonials();
    return () => {
      cancelled = true;
    };
  }, []);

  const items = testimonials ?? FALLBACK_TESTIMONIALS;

  return (
    <section className="py-10 sm:py-16 px-4 bg-white">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
          {HOME.socialProofTitle}
        </h2>

        {!loaded ? (
          <TestimonialSkeleton />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8">
            {items.map((testimonial, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 sm:p-8"
              >
                <StarRating />
                <p className="text-gray-700 italic mb-4 leading-relaxed">
                  &quot;{testimonial.quote}&quot;
                </p>
                <div className="border-t border-primary-200 pt-4">
                  <p className="font-semibold text-gray-900">
                    {testimonial.name}
                  </p>
                  <p className="text-sm text-gray-600">{testimonial.animal}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
