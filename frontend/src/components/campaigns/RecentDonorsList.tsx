"use client";

import { Heart } from "lucide-react";
import type { RecentDonorEntry } from "@/types/api";
import { formatCurrency } from "@/lib/campaign-utils";

// --- Labels (Spanish) ---
const LABEL_RECENT_DONORS = "Donaciones recientes";
const LABEL_ANONYMOUS = "Anonimo";
const LABEL_NO_DONORS = "Se el primero en donar";

/**
 * Displays a list of recent donors for a campaign.
 *
 * Privacy-aware: shows "Anonimo" for anonymous donors and masks
 * names to first name + last initial for non-anonymous donors.
 */
export default function RecentDonorsList({
  donors,
  maxVisible = 5,
}: {
  donors: RecentDonorEntry[];
  maxVisible?: number;
}) {
  if (donors.length === 0) {
    return (
      <div className="text-center py-4">
        <Heart className="h-6 w-6 text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-400">{LABEL_NO_DONORS}</p>
      </div>
    );
  }

  const visible = donors.slice(0, maxVisible);

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-3">
        {LABEL_RECENT_DONORS}
      </h4>
      <ul className="space-y-2.5">
        {visible.map((donor, idx) => (
          <li
            key={`${donor.donated_at}-${idx}`}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary-50 text-primary-600 text-xs font-medium flex-shrink-0">
                {donor.is_anonymous
                  ? "?"
                  : donor.display_name.charAt(0).toUpperCase()}
              </span>
              <span className="text-gray-700 truncate">
                {donor.is_anonymous ? LABEL_ANONYMOUS : donor.display_name}
              </span>
            </div>
            <span className="font-medium text-gray-900 flex-shrink-0 ml-2">
              {formatCurrency(donor.amount_cents, donor.currency)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
