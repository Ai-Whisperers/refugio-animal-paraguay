"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Clock, Users, Target, CheckCircle, PartyPopper } from "lucide-react";
import type { CampaignPublic } from "@/types/api";
import { getCampaignPublic } from "@/lib/public-api";
import {
  formatCurrency,
  getCategoryIcon,
  getCategoryLabel,
} from "@/lib/campaign-utils";
import DynamicIcon from "@/components/DynamicIcon";
import DonationForm from "@/components/DonationForm";
import { SocialProofPanel } from "@/components/campaigns";
import { DONATE } from "@/lib/strings";

interface CampaignDetailClientProps {
  campaignId: string;
}

export default function CampaignDetailClient({ campaignId }: CampaignDetailClientProps) {
  const [campaign, setCampaign] = useState<CampaignPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [donationSuccess, setDonationSuccess] = useState(false);

  useEffect(() => {
    async function fetchCampaign() {
      try {
        const data = await getCampaignPublic(campaignId);
        setCampaign(data);
      } catch {
        setError("No se pudo cargar la campana.");
      } finally {
        setLoading(false);
      }
    }
    fetchCampaign();
  }, [campaignId]);

  function handleDonationSuccess() {
    setDonationSuccess(true);
    // Refresh campaign data to show updated progress
    getCampaignPublic(campaignId).then(setCampaign).catch(() => {
      // Silently ignore refresh error; donation was successful
    });
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          <div className="h-48 bg-gray-200 rounded-xl" />
          <div className="h-8 bg-gray-200 rounded w-2/3" />
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-3/4" />
        </div>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-gray-500 mb-4">{error ?? "Campana no encontrada."}</p>
        <Link
          href="/donate"
          className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          {DONATE.campaignDetailBack}
        </Link>
      </div>
    );
  }

  const progressPercent = Math.min(campaign.progress_percentage, 100);
  const isCompleted = campaign.status === "completed" || progressPercent >= 100;

  if (donationSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-2xl p-8 mb-6">
          <div className="inline-flex items-center justify-center mb-4"><CheckCircle className="h-12 w-12 text-green-600" /></div>
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            {DONATE.donationSuccess}
          </h1>
          <p className="text-gray-600 mb-4">
            {DONATE.donationSuccessMessage}
          </p>
        </div>
        <Link
          href="/donate"
          className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          {DONATE.campaignDetailBack}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12">
      {/* Back Link */}
      <Link
        href="/donate"
        className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        {DONATE.campaignDetailBack}
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column — Campaign Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Campaign Header */}
          {campaign.image_url ? (
            <div className="rounded-xl overflow-hidden h-64 bg-gray-100">
              <img
                src={campaign.image_url}
                alt={campaign.title}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="rounded-xl h-40 bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
              <DynamicIcon
                name={getCategoryIcon(campaign.fund_category)}
                className="h-16 w-16 text-primary-600"
              />
            </div>
          )}

          {/* Category + Title */}
          <div>
            <span className="inline-block text-xs font-medium text-primary-700 bg-primary-50 rounded-full px-2.5 py-0.5 mb-2">
              {getCategoryLabel(campaign.fund_category)}
            </span>
            <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900">
              {campaign.title}
            </h1>
          </div>

          {/* Progress Section */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex justify-between text-sm mb-2">
              <span className="font-semibold text-gray-900 text-lg">
                {formatCurrency(campaign.raised_amount_cents, campaign.currency)}
              </span>
              <span className="text-gray-500">
                de {formatCurrency(campaign.target_amount_cents, campaign.currency)}
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3 mb-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  isCompleted ? "bg-green-500" : "bg-primary-500"
                }`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="flex gap-6 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                {campaign.donation_count} donaciones
              </span>
              <span className="flex items-center gap-1">
                <Target className="h-4 w-4" />
                {progressPercent.toFixed(0)}% alcanzado
              </span>
              {campaign.deadline && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {new Date(campaign.deadline).toLocaleDateString("es-PY", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 leading-relaxed whitespace-pre-line">
              {campaign.description}
            </p>
          </div>

          {/* Impact Story */}
          {campaign.impact_story && (
            <div className="bg-gray-50 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Impacto de esta campana
              </h2>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {campaign.impact_story}
              </p>
            </div>
          )}
        </div>

        {/* Right Column — Donation Form + Social Proof */}
        <div className="lg:col-span-1">
          <div className="sticky top-4 space-y-6">
            {isCompleted && !campaign.allow_overfunding ? (
              <div className="bg-green-50 rounded-xl p-6 text-center">
                <div className="inline-flex items-center justify-center mb-2"><PartyPopper className="h-8 w-8 text-green-600" /></div>
                <h3 className="text-lg font-semibold text-green-800 mb-1">
                  Meta alcanzada
                </h3>
                <p className="text-sm text-green-600">
                  Gracias a todos los que apoyaron esta campana.
                </p>
              </div>
            ) : (
              <DonationForm
                campaign={campaign}
                onSuccess={handleDonationSuccess}
              />
            )}

            {/* Social proof — recent donors and momentum */}
            <SocialProofPanel campaignId={campaignId} />
          </div>
        </div>
      </div>
    </div>
  );
}
