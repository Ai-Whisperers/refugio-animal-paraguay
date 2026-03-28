"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";

import { getHomepageTeam } from "@/lib/public-api";
import type { HomepageTeamMember } from "@/lib/public-api";
import { HOME } from "@/lib/strings";

// ---------------------------------------------------------------------------
// Fallback data — used when CMS has no entries
// ---------------------------------------------------------------------------

const FALLBACK_TEAM: HomepageTeamMember[] = HOME.trustTeam.map((m) => ({
  name: m.name,
  role: m.role,
  image_url: null,
}));

// ---------------------------------------------------------------------------
// Skeleton loader
// ---------------------------------------------------------------------------

function TeamSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
      {[0, 1, 2, 3].map((i) => (
        <div
          key={i}
          className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 text-center animate-pulse"
        >
          <div className="w-16 h-16 rounded-full bg-white/60 mx-auto mb-4" />
          <div className="h-5 w-28 bg-white/60 rounded mx-auto mb-2" />
          <div className="h-4 w-36 bg-white/60 rounded mx-auto" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function HomeTeam() {
  const [team, setTeam] = useState<HomepageTeamMember[] | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchTeam() {
      try {
        const data = await getHomepageTeam();
        if (!cancelled) {
          // Use CMS data if available, otherwise fall back
          setTeam(data.items.length > 0 ? data.items : FALLBACK_TEAM);
        }
      } catch {
        if (!cancelled) {
          setTeam(FALLBACK_TEAM);
        }
      } finally {
        if (!cancelled) {
          setLoaded(true);
        }
      }
    }

    fetchTeam();
    return () => {
      cancelled = true;
    };
  }, []);

  const members = team ?? FALLBACK_TEAM;

  return (
    <section className="py-10 sm:py-16 px-4 bg-white">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
          {HOME.trustTeamTitle}
        </h2>

        {!loaded ? (
          <TeamSkeleton />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {members.map((member, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-white border-2 border-primary-200 flex items-center justify-center mx-auto mb-4">
                  {member.image_url ? (
                    <img
                      src={member.image_url}
                      alt={member.name}
                      className="w-16 h-16 rounded-full object-cover"
                    />
                  ) : (
                    <Users className="w-8 h-8 text-primary-600" />
                  )}
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {member.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">{member.role}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
