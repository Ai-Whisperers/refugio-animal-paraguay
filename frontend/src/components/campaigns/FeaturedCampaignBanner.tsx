"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Star, ArrowRight } from "lucide-react";
import type { CampaignPublic } from "@/types/api";
import { listCampaignsPublic } from "@/lib/public-api";
import { formatCurrency, getCategoryLabel } from "@/lib/campaign-utils";
import CampaignProgressBar from "./CampaignProgressBar";

const LABEL_FEATURED = "Campana destacada";
const LABEL_DONATE_NOW = "Donar ahora";
const LABEL_DONORS_SUFFIX = "donaciones";

/**
 * Prominent banner showcasing the first featured active campaign.
 *
 * Fetches the top featured campaign and displays it with a large progress
 * bar, raised amount, and a call-to-action link. Renders nothing if no
 * featured campaign is active.
 */
export default function FeaturedCampaignBanner() {
  const [campaign, setCampaign] = useState<CampaignPublic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchFeatured() {
      try {
        const response = await listCampaignsPublic({ page_size: 1 });
        // The API sorts featured first, so the first item is the top featured campaign
        const featured = response.items.find((c) => c.featured);
        setCampaign(featured ?? null);
      } catch {
        // Silently degrade — banner is not critical
      } finally {
        setLoading(false);
      }
    }
    fetchFeatured();
  }, []);

  if (loading) {
    return (
      <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-2xl p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4" />
        <div className="h-4 bg-gray-200 rounded w-2/3 mb-3" />
        <div className="h-3 bg-gray-200 rounded-full w-full mb-2" />
        <div className="h-4 bg-gray-200 rounded w-1/4" />
      </div>
    );
  }

  if (!campaign) return null;

  const isCompleted = campaign.status === "completed" || campaign.progress_percentage >= 100;

  return (
    <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-2xl overflow-hidden">
      <div className="flex flex-col md:flex-row">
        {/* Image */}
        {campaign.image_url && (
          <div className="md:w-1/3 h-48 md:h-auto">
            <img
              src={campaign.image_url}
              alt={campaign.title}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* Content */}
        <div className={`flex-1 p-6 sm:p-8 ${campaign.image_url ? "" : "w-full"}`}>
          <div className="flex items-center gap-2 mb-3">
            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
            <span className="text-xs font-semibold text-primary-700 uppercase tracking-wide">
              {LABEL_FEATURED}
            </span>
            <span className="text-xs text-gray-500 bg-white rounded-full px-2 py-0.5">
              {getCategoryLabel(campaign.fund_category)}
            </span>
          </div>

          <h3 className="text-xl sm:text-2xl font-heading font-bold text-gray-900 mb-2">
            {campaign.title}
          </h3>

          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {campaign.description}
          </p>

          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-semibold text-gray-900">
                {formatCurrency(campaign.raised_amount_cents, campaign.currency)}
              </span>
              <span className="text-gray-500">
                de {formatCurrency(campaign.target_amount_cents, campaign.currency)}
              </span>
            </div>
            <CampaignProgressBar
              percentage={campaign.progress_percentage}
              isCompleted={isCompleted}
              height="h-3"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1.5">
              <span>{campaign.donation_count} {LABEL_DONORS_SUFFIX}</span>
              <span>{Math.round(campaign.progress_percentage)}%</span>
            </div>
          </div>

          {/* CTA */}
          <Link
            href={`/donate/campaigns/${campaign.id}`}
            className="inline-flex items-center gap-2 bg-primary-600 text-white font-semibold px-5 py-2.5 rounded-lg hover:bg-primary-700 transition-colors text-sm"
          >
            {LABEL_DONATE_NOW}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
