import type { Metadata } from "next";
import { SITE_TITLE } from "@/lib/strings";
import CampaignDetailClient from "./CampaignDetailClient";

export const metadata: Metadata = {
  title: `Campana | ${SITE_TITLE}`,
  description: "Apoya esta campana con tu donacion",
};

interface CampaignDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({ params }: CampaignDetailPageProps) {
  const { id } = await params;

  return <CampaignDetailClient campaignId={id} />;
}
