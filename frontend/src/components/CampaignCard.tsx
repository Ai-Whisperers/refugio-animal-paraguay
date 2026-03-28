"use client";

import Link from "next/link";
import type { CampaignPublic } from "@/types/api";
import { formatCurrency, getCategoryIcon, getCategoryLabel } from "@/lib/campaign-utils";
import DynamicIcon from "@/components/DynamicIcon";
import WhatsAppShareCampaign from "@/components/WhatsAppShareCampaign";

interface CampaignCardProps {
  campaign: CampaignPublic;
}

export default function CampaignCard({ campaign }: CampaignCardProps) {
  const progressPercent = Math.min(campaign.progress_percentage, 100);
  const isCompleted = campaign.status === "completed" || progressPercent >= 100;

  return (
    <div className="relative bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
      <Link
        href={`/donate/campaigns/${campaign.id}`}
        className="block"
      >
        {campaign.image_url ? (
          <div className="h-40 bg-gray-100 overflow-hidden">
            <img
              src={campaign.image_url}
              alt={campaign.title}
              className="w-full h-full object-cover"
            />
          </div>
        ) : (
          <div className="h-24 bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
            <DynamicIcon name={getCategoryIcon(campaign.fund_category)} className="h-10 w-10 text-primary-600" />
          </div>
        )}

        <div className="p-5">
          <span className="inline-block text-xs font-medium text-primary-700 bg-primary-50 rounded-full px-2.5 py-0.5 mb-2">
            {getCategoryLabel(campaign.fund_category)}
          </span>

          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
            {campaign.title}
          </h3>

          <p className="text-sm text-gray-500 mb-4 line-clamp-2">
            {campaign.description}
          </p>

          <div className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-900">
                {formatCurrency(campaign.raised_amount_cents, campaign.currency)}
              </span>
              <span className="text-gray-500">
                de {formatCurrency(campaign.target_amount_cents, campaign.currency)}
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all ${
                  isCompleted ? "bg-green-500" : "bg-primary-500"
                }`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-500">
              {campaign.donation_count} {campaign.donation_count === 1 ? "donacion" : "donaciones"}
            </span>
            <span className={`font-medium ${isCompleted ? "text-green-600" : "text-primary-600"}`}>
              {isCompleted ? "Meta alcanzada" : `${progressPercent.toFixed(0)}%`}
            </span>
          </div>

          {campaign.deadline && !isCompleted && (
            <p className="text-xs text-gray-400 mt-2">
              Hasta {new Date(campaign.deadline).toLocaleDateString("es-PY", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </p>
          )}
        </div>
      </Link>

      {/* WhatsApp share button — bottom right of card */}
      <div className="absolute bottom-4 right-4 z-10">
        <WhatsAppShareCampaign campaign={campaign} size="sm" />
      </div>
    </div>
  );
}
