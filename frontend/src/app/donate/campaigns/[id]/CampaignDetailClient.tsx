"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Clock,
  Users,
  Target,
  CheckCircle,
  PartyPopper,
  TrendingUp,
} from "lucide-react";
import type { CampaignPublic } from "@/types/api";
import {
  formatCurrency,
  getCategoryIcon,
  getCategoryLabel,
} from "@/lib/campaign-utils";
import DynamicIcon from "@/components/DynamicIcon";
import DonationForm from "@/components/DonationForm";
import { SocialProofPanel } from "@/components/campaigns";
import { DONATE } from "@/lib/strings";
import { useCampaignPolling } from "@/hooks/useCampaignPolling";
import WhatsAppShareCampaign from "@/components/WhatsAppShareCampaign";

interface CampaignDetailClientProps {
  campaignId: string;
}

/** Spanish strings for campaign real-time progress. */
const S = {
  donationFlash: "Se acaba de recibir una donacion!",
  fullyFunded: "META ALCANZADA!",
  overFunded: "SUPERADO!",
  overAmount: "mas de la meta",
  goalReached: "Meta alcanzada",
  goalReachedThanks: "Gracias a todos los que apoyaron esta campana.",
  donations: "donaciones",
  reached: "alcanzado",
  progressUpdate: "Progreso actualizado",
  impactTitle: "Impacto de esta campana",
} as const;

export default function CampaignDetailClient({
  campaignId,
}: CampaignDetailClientProps) {
  const { campaign, loading, error, donationFlash, fullyFundedFlash } =
    useCampaignPolling(campaignId);
  const [donationSuccess, setDonationSuccess] = useState(false);

  function handleDonationSuccess() {
    setDonationSuccess(true);
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
        <p className="text-gray-500 mb-4">
          {error ?? "Campana no encontrada."}
        </p>
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
  const isCompleted =
    campaign.status === "completed" || progressPercent >= 100;
  const isOverFunded =
    campaign.allow_overfunding &&
    campaign.raised_amount_cents > campaign.target_amount_cents;
  const overAmount = isOverFunded
    ? campaign.raised_amount_cents - campaign.target_amount_cents
    : 0;

  if (donationSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-2xl p-8 mb-6">
          <div className="inline-flex items-center justify-center mb-4">
            <CheckCircle className="h-12 w-12 text-green-600" />
          </div>
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
      {/* ARIA live region for screen readers */}
      <div role="status" aria-live="polite" className="sr-only">
        {donationFlash && S.donationFlash}
        {fullyFundedFlash && S.fullyFunded}
        {!donationFlash &&
          !fullyFundedFlash &&
          campaign &&
          `${S.progressUpdate}: ${progressPercent.toFixed(0)}% ${S.reached}`}
      </div>

      {/* Donation flash notification */}
      <DonationFlashBanner visible={donationFlash} />

      {/* Fully funded flash */}
      <FullyFundedBanner
        visible={fullyFundedFlash}
        isOverFunded={isOverFunded}
        overAmount={overAmount}
        currency={campaign.currency}
      />

      {/* Back Link */}
      <Link
        href="/donate"
        className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        {DONATE.campaignDetailBack}
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Campaign Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Campaign Header */}
          <CampaignHero campaign={campaign} />

          {/* Category + Title + WhatsApp Share */}
          <div>
            <span className="inline-block text-xs font-medium text-primary-700 bg-primary-50 rounded-full px-2.5 py-0.5 mb-2">
              {getCategoryLabel(campaign.fund_category)}
            </span>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900">
                {campaign.title}
              </h1>
              <WhatsAppShareCampaign campaign={campaign} size="md" />
            </div>
          </div>

          {/* Progress Section with animation */}
          <CampaignProgressBar
            campaign={campaign}
            progressPercent={progressPercent}
            isCompleted={isCompleted}
            isOverFunded={isOverFunded}
            overAmount={overAmount}
          />

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
                {S.impactTitle}
              </h2>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {campaign.impact_story}
              </p>
            </div>
          )}
        </div>

        {/* Right Column - Donation Form + Social Proof */}
        <div className="lg:col-span-1">
          <div className="sticky top-4 space-y-6">
            {isCompleted && !campaign.allow_overfunding ? (
              <div className="bg-green-50 rounded-xl p-6 text-center">
                <div className="inline-flex items-center justify-center mb-2">
                  <PartyPopper className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-green-800 mb-1">
                  {S.goalReached}
                </h3>
                <p className="text-sm text-green-600">
                  {S.goalReachedThanks}
                </p>
              </div>
            ) : (
              <DonationForm
                campaign={campaign}
                onSuccess={handleDonationSuccess}
              />
            )}

            {/* Social proof - recent donors and momentum */}
            <SocialProofPanel campaignId={campaignId} />
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Sub-components ---

function DonationFlashBanner({ visible }: { visible: boolean }) {
  return (
    <div
      className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ${
        visible
          ? "opacity-100 translate-y-0"
          : "opacity-0 -translate-y-4 pointer-events-none"
      }`}
    >
      <div className="bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3">
        <CheckCircle className="h-5 w-5 flex-shrink-0" />
        <span className="font-medium text-sm">{S.donationFlash}</span>
      </div>
    </div>
  );
}

function FullyFundedBanner({
  visible,
  isOverFunded,
  overAmount,
  currency,
}: {
  visible: boolean;
  isOverFunded: boolean;
  overAmount: number;
  currency: CampaignPublic["currency"];
}) {
  return (
    <div
      className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-500 ${
        visible
          ? "opacity-100 translate-y-0"
          : "opacity-0 -translate-y-4 pointer-events-none"
      }`}
    >
      <div className="bg-blue-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-3">
        <PartyPopper className="h-5 w-5 flex-shrink-0" />
        <span className="font-medium text-sm">
          {isOverFunded
            ? `${S.overFunded} +${formatCurrency(overAmount, currency)} ${S.overAmount}`
            : S.fullyFunded}
        </span>
      </div>
    </div>
  );
}

function CampaignHero({ campaign }: { campaign: CampaignPublic }) {
  if (campaign.image_url) {
    return (
      <div className="rounded-xl overflow-hidden h-64 bg-gray-100">
        <img
          src={campaign.image_url}
          alt={campaign.title}
          className="w-full h-full object-cover"
        />
      </div>
    );
  }
  return (
    <div className="rounded-xl h-40 bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
      <DynamicIcon
        name={getCategoryIcon(campaign.fund_category)}
        className="h-16 w-16 text-primary-600"
      />
    </div>
  );
}

function CampaignProgressBar({
  campaign,
  progressPercent,
  isCompleted,
  isOverFunded,
  overAmount,
}: {
  campaign: CampaignPublic;
  progressPercent: number;
  isCompleted: boolean;
  isOverFunded: boolean;
  overAmount: number;
}) {
  const barColor = isCompleted
    ? isOverFunded
      ? "bg-blue-500"
      : "bg-green-500"
    : "bg-primary-500";

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-semibold text-gray-900 text-lg">
          {formatCurrency(campaign.raised_amount_cents, campaign.currency)}
        </span>
        <span className="text-gray-500">
          de{" "}
          {formatCurrency(campaign.target_amount_cents, campaign.currency)}
        </span>
      </div>

      {/* Animated progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-3 mb-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-1000 ease-out ${barColor}`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Status badges */}
      <div className="flex flex-wrap gap-3 text-sm text-gray-500 mb-1">
        <span className="flex items-center gap-1">
          <Users className="h-4 w-4" />
          {campaign.donation_count} {S.donations}
        </span>
        <span className="flex items-center gap-1">
          <Target className="h-4 w-4" />
          {progressPercent.toFixed(0)}% {S.reached}
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

      {/* Fully funded badge */}
      {isCompleted && (
        <div className="mt-3">
          {isOverFunded ? (
            <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-700 bg-blue-50 rounded-full px-3 py-1">
              <TrendingUp className="h-4 w-4" />
              {S.overFunded} +
              {formatCurrency(overAmount, campaign.currency)}{" "}
              {S.overAmount}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-green-700 bg-green-50 rounded-full px-3 py-1">
              <PartyPopper className="h-4 w-4" />
              {S.fullyFunded}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
