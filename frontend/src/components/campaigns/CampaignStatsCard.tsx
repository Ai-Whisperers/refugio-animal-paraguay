"use client";

import type { CurrencyCode } from "@/types/api";
import { formatCurrency } from "@/lib/campaign-utils";
import { Users, Target, Clock, TrendingUp } from "lucide-react";

interface CampaignStatsCardProps {
  /** Amount raised in cents. */
  raisedCents: number;
  /** Goal amount in cents. */
  targetCents: number;
  /** Currency code. */
  currency: CurrencyCode;
  /** Number of donors/donations. */
  donationCount: number;
  /** Progress percentage (0-100+). */
  progressPercentage: number;
  /** Days remaining until deadline (null if no deadline). */
  daysRemaining: number | null;
  /** Optional: donations in last 24 hours (momentum). */
  donationsLast24h?: number;
}

const LABEL_RAISED = "Recaudado";
const LABEL_GOAL = "Meta";
const LABEL_DONORS = "Donaciones";
const LABEL_PROGRESS = "Progreso";
const LABEL_DAYS_LEFT = "Dias restantes";
const LABEL_NO_DEADLINE = "Sin fecha limite";
const LABEL_MOMENTUM = "Ultimas 24h";

/**
 * Stats card showing key campaign metrics in a compact grid.
 *
 * Displays raised amount vs goal, donor count, progress, and time remaining.
 */
export default function CampaignStatsCard({
  raisedCents,
  targetCents,
  currency,
  donationCount,
  progressPercentage,
  daysRemaining,
  donationsLast24h,
}: CampaignStatsCardProps) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <div className="grid grid-cols-2 gap-4">
        {/* Raised */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Target className="h-3.5 w-3.5" />
            {LABEL_RAISED}
          </div>
          <p className="text-lg font-bold text-gray-900">
            {formatCurrency(raisedCents, currency)}
          </p>
        </div>

        {/* Goal */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Target className="h-3.5 w-3.5" />
            {LABEL_GOAL}
          </div>
          <p className="text-lg font-bold text-gray-900">
            {formatCurrency(targetCents, currency)}
          </p>
        </div>

        {/* Donation Count */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Users className="h-3.5 w-3.5" />
            {LABEL_DONORS}
          </div>
          <p className="text-lg font-bold text-gray-900">{donationCount}</p>
        </div>

        {/* Progress */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <TrendingUp className="h-3.5 w-3.5" />
            {LABEL_PROGRESS}
          </div>
          <p className={`text-lg font-bold ${progressPercentage >= 100 ? "text-green-600" : "text-primary-600"}`}>
            {Math.round(progressPercentage)}%
          </p>
        </div>

        {/* Days Remaining */}
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Clock className="h-3.5 w-3.5" />
            {LABEL_DAYS_LEFT}
          </div>
          <p className="text-lg font-bold text-gray-900">
            {daysRemaining !== null ? daysRemaining : LABEL_NO_DEADLINE}
          </p>
        </div>

        {/* Momentum (optional) */}
        {donationsLast24h !== undefined && (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <TrendingUp className="h-3.5 w-3.5" />
              {LABEL_MOMENTUM}
            </div>
            <p className="text-lg font-bold text-gray-900">
              {donationsLast24h}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
