"use client";

import { useCallback } from "react";
import type { CampaignPublic } from "@/types/api";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  shareLabel: "Compartir campaña en WhatsApp",
  generalMessage: (pct: number, title: string, url: string) =>
    `Ayudanos a alcanzar nuestra meta! Ya logramos ${pct}% de ${title}. ${url}`,
  castrationMessage: (done: number, target: number, title: string, url: string) =>
    `Ya castramos ${done} animales! Ayudanos a llegar a ${target} — ${title}. ${url}`,
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? "https://refugioanimal.com.py";

/** Keywords that identify a castration-related campaign. */
const CASTRATION_KEYWORDS = ["castrac", "esteriliz", "spay", "neuter"];

function isCastrationCampaign(campaign: CampaignPublic): boolean {
  const text = `${campaign.title} ${campaign.description}`.toLowerCase();
  return CASTRATION_KEYWORDS.some((kw) => text.includes(kw));
}

function buildCampaignShareUrl(campaign: CampaignPublic): string {
  const campaignUrl = `${BASE_URL}/donate/campaigns/${campaign.id}`;
  const pct = Math.min(Math.round(campaign.progress_percentage), 100);

  let message: string;
  if (isCastrationCampaign(campaign)) {
    message = S.castrationMessage(
      campaign.donation_count,
      Math.ceil(campaign.target_amount_cents / 100),
      campaign.title,
      campaignUrl,
    );
  } else {
    message = S.generalMessage(pct, campaign.title, campaignUrl);
  }

  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

// ---------------------------------------------------------------------------
// WhatsApp icon (inline SVG)
// ---------------------------------------------------------------------------

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface WhatsAppShareCampaignProps {
  campaign: CampaignPublic;
  /** Visual size variant. */
  size?: "sm" | "md";
  /** Additional CSS classes. */
  className?: string;
}

/**
 * WhatsApp share button for campaign pages.
 *
 * Generates a context-aware message based on campaign type:
 * - General campaigns: shows progress percentage
 * - Castration campaigns: shows animals castrated vs target
 */
export default function WhatsAppShareCampaign({
  campaign,
  size = "md",
  className = "",
}: WhatsAppShareCampaignProps) {
  const handleClick = useCallback(() => {
    const url = buildCampaignShareUrl(campaign);
    window.open(url, "_blank", "noopener,noreferrer");
  }, [campaign]);

  const sizeClasses = size === "md" ? "h-10 w-10" : "h-8 w-8";
  const iconClasses = size === "md" ? "h-5 w-5" : "h-4 w-4";

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex items-center justify-center rounded-full bg-[#25D366] text-white shadow-sm hover:bg-[#1fb855] hover:scale-110 transition-all duration-200 ${sizeClasses} ${className}`}
      aria-label={S.shareLabel}
      title={S.shareLabel}
    >
      <WhatsAppIcon className={iconClasses} />
    </button>
  );
}
