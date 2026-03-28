"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Heart, Clock, ArrowRight } from "lucide-react";
import { listCampaignsPublic } from "@/lib/public-api";
import { formatCurrency, getCategoryLabel } from "@/lib/campaign-utils";
import CampaignProgressBar from "@/components/campaigns/CampaignProgressBar";
import type { CampaignPublic } from "@/types/api";
import { HOME } from "@/lib/strings";

const FEATURED_LIMIT = 3;

/** Format days remaining into a Spanish label. */
function daysLabel(days: number | null): string | null {
  if (days === null) return null;
  if (days === 0) return "Ultimo dia";
  if (days === 1) return "1 dia restante";
  return `${days} dias restantes`;
}

export default function FeaturedCampaigns() {
  const [campaigns, setCampaigns] = useState<CampaignPublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    listCampaignsPublic({ featured: true, page_size: FEATURED_LIMIT })
      .then((res) => {
        if (!cancelled) setCampaigns(res.items);
      })
      .catch(() => {
        // Silently degrade — section is not critical
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading || campaigns.length === 0) return null;

  return (
    <section className="py-10 sm:py-16 px-4 bg-gradient-to-br from-secondary-50 to-orange-50">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8 sm:mb-10">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-2">
            {HOME.campaignsTitle}
          </h2>
          <p className="text-gray-600">{HOME.campaignsSubtitle}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {campaigns.map((campaign) => {
            const isCompleted =
              campaign.status === "completed" ||
              campaign.progress_percentage >= 100;

            return (
              <Link
                key={campaign.id}
                href={`/donate/campaigns/${campaign.id}`}
                className="group bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-md hover:border-secondary-200 transition-all flex flex-col"
              >
                {/* Image */}
                {campaign.image_url ? (
                  <div className="aspect-[16/9] bg-gray-100 overflow-hidden">
                    <img
                      src={campaign.image_url}
                      alt={campaign.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                ) : (
                  <div className="aspect-[16/9] bg-gradient-to-br from-secondary-100 to-orange-100 flex items-center justify-center">
                    <Heart className="w-10 h-10 text-secondary-300" />
                  </div>
                )}

                {/* Content */}
                <div className="p-4 flex-1 flex flex-col">
                  {/* Category + deadline */}
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                    <span className="bg-secondary-50 text-secondary-700 px-2 py-0.5 rounded-full font-medium">
                      {getCategoryLabel(campaign.fund_category)}
                    </span>
                    {campaign.days_remaining !== null && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {daysLabel(campaign.days_remaining)}
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-semibold text-gray-900 group-hover:text-secondary-600 transition-colors mb-2 line-clamp-2">
                    {campaign.title}
                  </h3>

                  <p className="text-sm text-gray-600 mb-3 line-clamp-2 flex-1">
                    {campaign.description}
                  </p>

                  {/* Progress */}
                  <div className="mb-3">
                    <CampaignProgressBar
                      percentage={campaign.progress_percentage}
                      isCompleted={isCompleted}
                      height="h-2"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1.5">
                      <span className="font-medium text-gray-900">
                        {formatCurrency(
                          campaign.raised_amount_cents,
                          campaign.currency
                        )}
                      </span>
                      <span>
                        de{" "}
                        {formatCurrency(
                          campaign.target_amount_cents,
                          campaign.currency
                        )}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {campaign.donation_count} {HOME.campaignsDonations}
                    </div>
                  </div>

                  {/* CTA */}
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-secondary-600 group-hover:text-secondary-700">
                    {HOME.campaignsDonate}
                    <ArrowRight className="w-4 h-4" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>

        {/* View all link */}
        <div className="text-center mt-8">
          <Link
            href="/donate"
            className="inline-flex items-center text-secondary-600 hover:text-secondary-700 font-medium transition-colors"
          >
            {HOME.campaignsViewAll} &rarr;
          </Link>
        </div>
      </div>
    </section>
  );
}
