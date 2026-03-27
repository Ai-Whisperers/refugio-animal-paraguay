"use client";

import { useEffect, useState } from "react";
import { Users, TrendingUp, Flame } from "lucide-react";
import type { CampaignSocialProof } from "@/types/api";
import { getCampaignSocialProof } from "@/lib/public-api";
import { formatCurrency } from "@/lib/campaign-utils";
import CampaignProgressBar from "./CampaignProgressBar";
import RecentDonorsList from "./RecentDonorsList";

// --- Labels (Spanish) ---
const LABEL_TITLE = "Apoyo de la comunidad";
const LABEL_DONORS = "donantes";
const LABEL_RAISED = "recaudado";
const LABEL_MOMENTUM = "en las ultimas 24h";
const LABEL_LOADING = "Cargando...";

/**
 * Composite social proof panel combining progress, momentum stats,
 * and recent donors for a campaign. Fetches data independently so
 * it can be dropped into any page without prop drilling.
 */
export default function SocialProofPanel({
  campaignId,
}: {
  campaignId: string;
}) {
  const [data, setData] = useState<CampaignSocialProof | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function fetch() {
      try {
        const result = await getCampaignSocialProof(campaignId);
        if (!cancelled) setData(result);
      } catch {
        // Non-critical — degrade gracefully
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetch();
    return () => {
      cancelled = true;
    };
  }, [campaignId]);

  if (loading) {
    return (
      <div className="bg-gray-50 rounded-xl p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
        <div className="h-3 bg-gray-200 rounded-full w-full mb-3" />
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
        <div className="h-4 bg-gray-200 rounded w-1/4" />
      </div>
    );
  }

  if (!data) return null;

  const isCompleted = data.progress_percentage >= 100;

  return (
    <div className="bg-gray-50 rounded-xl p-6 space-y-5">
      <h3 className="text-base font-semibold text-gray-900">
        {LABEL_TITLE}
      </h3>

      {/* Progress bar */}
      <div>
        <CampaignProgressBar
          percentage={data.progress_percentage}
          isCompleted={isCompleted}
          height="h-2.5"
        />
        <p className="text-xs text-gray-500 mt-1.5 text-right">
          {Math.round(data.progress_percentage)}%
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3">
        <StatBadge
          icon={<Users className="h-4 w-4 text-blue-600" />}
          value={String(data.donor_count)}
          label={LABEL_DONORS}
        />
        <StatBadge
          icon={<TrendingUp className="h-4 w-4 text-green-600" />}
          value={formatCurrency(data.total_raised_cents, data.currency)}
          label={LABEL_RAISED}
        />
      </div>

      {/* Momentum indicator */}
      {data.donations_last_24_hours > 0 && (
        <div className="flex items-center gap-2 bg-orange-50 rounded-lg px-3 py-2">
          <Flame className="h-4 w-4 text-orange-500" />
          <span className="text-sm font-medium text-orange-700">
            {data.donations_last_24_hours} {LABEL_MOMENTUM}
          </span>
        </div>
      )}

      {/* Recent donors */}
      <RecentDonorsList donors={data.recent_donors} />
    </div>
  );
}

/** Small stat badge used in the 2-column grid. */
function StatBadge({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
}) {
  return (
    <div className="bg-white rounded-lg p-3 text-center">
      <div className="flex items-center justify-center mb-1">{icon}</div>
      <p className="text-lg font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
