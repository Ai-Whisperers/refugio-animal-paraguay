"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Users,
  Target,
  Clock,
  TrendingUp,
  DollarSign,
  Eye,
  Edit,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { getCampaignSocialProof } from "@/lib/public-api";
import { formatCurrency, getCategoryLabel } from "@/lib/campaign-utils";
import CampaignProgressBar from "@/components/campaigns/CampaignProgressBar";
import type { CampaignSocialProof, CurrencyCode } from "@/types/api";
import { getAccessToken } from "@/lib/auth";

interface CampaignDetail {
  id: string;
  title: string;
  description: string;
  impact_story: string | null;
  target_amount_cents: number;
  currency: CurrencyCode;
  fund_category: string;
  status: string;
  featured: boolean;
  image_url: string | null;
  deadline: string | null;
  allow_overfunding: boolean;
  created_at: string;
  updated_at: string;
}

const LABEL_PAGE_TITLE = "Progreso de Campana";
const LABEL_BACK = "Volver a campanas";
const LABEL_VIEW_PUBLIC = "Ver pagina publica";
const LABEL_EDIT = "Editar campana";
const LABEL_REFRESH = "Actualizar datos";
const LABEL_RAISED = "Recaudado";
const LABEL_GOAL = "Meta";
const LABEL_DONORS = "Donantes unicos";
const LABEL_DONATIONS_TOTAL = "Total donaciones";
const LABEL_PROGRESS = "Progreso";
const LABEL_DAYS_LEFT = "Dias restantes";
const LABEL_NO_DEADLINE = "Sin limite";
const LABEL_MOMENTUM_24H = "Donaciones (24h)";
const LABEL_MOMENTUM_7D = "Donaciones (7 dias)";
const LABEL_RECENT_DONORS = "Donaciones recientes";
const LABEL_ANONYMOUS = "Anonimo";
const LABEL_CAMPAIGN_INFO = "Informacion de la campana";
const LABEL_STATUS = "Estado";
const LABEL_CATEGORY = "Categoria";
const LABEL_FEATURED = "Destacada";
const LABEL_OVERFUNDING = "Sobre-financiamiento";
const LABEL_YES = "Si";
const LABEL_NO = "No";
const LABEL_CREATED = "Creada";
const LABEL_UPDATED = "Actualizada";
const LABEL_DEADLINE = "Fecha limite";
const LABEL_LOADING = "Cargando progreso...";
const LABEL_ERROR = "Error al cargar la campana.";

const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  active: "Activa",
  paused: "Pausada",
  completed: "Completada",
  archived: "Archivada",
  cancelled: "Cancelada",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  completed: "bg-blue-100 text-blue-700",
  archived: "bg-gray-100 text-gray-600",
  cancelled: "bg-red-100 text-red-700",
};

export default function CampaignProgressPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [socialProof, setSocialProof] = useState<CampaignSocialProof | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  async function fetchData() {
    const token = getAccessToken();
    if (!token) {
      router.replace("/admin/login");
      return;
    }

    try {
      const [campaignData, proofData] = await Promise.all([
        api.get<CampaignDetail>(`/admin/campaigns/${id}`),
        getCampaignSocialProof(id),
      ]);
      setCampaign(campaignData);
      setSocialProof(proofData);
      setError(null);
    } catch {
      setError(LABEL_ERROR);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function handleRefresh() {
    setRefreshing(true);
    fetchData();
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          <div className="h-8 bg-gray-200 rounded w-1/2" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl" />
            ))}
          </div>
          <div className="h-4 bg-gray-200 rounded-full w-full" />
        </div>
      </div>
    );
  }

  if (error || !campaign || !socialProof) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-600 mb-4">{error ?? LABEL_ERROR}</p>
        <button
          onClick={() => router.push("/admin/campaigns")}
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          {LABEL_BACK}
        </button>
      </div>
    );
  }

  const progressPercent = socialProof.progress_percentage;
  const isCompleted = campaign.status === "completed" || progressPercent >= 100;
  const daysRemaining = campaign.deadline
    ? Math.max(0, Math.ceil((new Date(campaign.deadline).getTime() - Date.now()) / 86400000))
    : null;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <button
            onClick={() => router.push("/admin/campaigns")}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            {LABEL_BACK}
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
          <p className="text-gray-500 text-sm mt-1">{campaign.title}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
          <button
            onClick={() => window.open(`/donate/campaigns/${id}`, "_blank")}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Eye className="h-4 w-4" />
            {LABEL_VIEW_PUBLIC}
          </button>
          <button
            onClick={() => router.push(`/admin/campaigns/${id}/edit`)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Edit className="h-4 w-4" />
            {LABEL_EDIT}
          </button>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
        <div className="flex justify-between items-end mb-3">
          <div>
            <p className="text-3xl font-bold text-gray-900">
              {formatCurrency(socialProof.total_raised_cents, socialProof.currency)}
            </p>
            <p className="text-sm text-gray-500">
              de {formatCurrency(campaign.target_amount_cents, campaign.currency)} meta
            </p>
          </div>
          <span className={`text-2xl font-bold ${isCompleted ? "text-green-600" : "text-primary-600"}`}>
            {Math.round(progressPercent)}%
          </span>
        </div>
        <CampaignProgressBar
          percentage={progressPercent}
          isCompleted={isCompleted}
          height="h-4"
          animate={true}
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatBox
          icon={<Users className="h-5 w-5 text-blue-600" />}
          label={LABEL_DONORS}
          value={String(socialProof.donor_count)}
          bgColor="bg-blue-50"
        />
        <StatBox
          icon={<DollarSign className="h-5 w-5 text-green-600" />}
          label={LABEL_DONATIONS_TOTAL}
          value={formatCurrency(socialProof.total_raised_cents, socialProof.currency)}
          bgColor="bg-green-50"
        />
        <StatBox
          icon={<TrendingUp className="h-5 w-5 text-orange-600" />}
          label={LABEL_MOMENTUM_24H}
          value={String(socialProof.donations_last_24_hours)}
          bgColor="bg-orange-50"
        />
        <StatBox
          icon={<Clock className="h-5 w-5 text-purple-600" />}
          label={LABEL_DAYS_LEFT}
          value={daysRemaining !== null ? String(daysRemaining) : LABEL_NO_DEADLINE}
          bgColor="bg-purple-50"
        />
      </div>

      {/* Two-column layout: Recent Donors + Campaign Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Donors */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-gray-400" />
            {LABEL_RECENT_DONORS}
          </h2>
          {socialProof.recent_donors.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">
              Aun no hay donaciones para esta campana.
            </p>
          ) : (
            <div className="space-y-3">
              {socialProof.recent_donors.map((donor, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {donor.is_anonymous ? LABEL_ANONYMOUS : donor.display_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(donor.donated_at).toLocaleDateString("es-PY", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {formatCurrency(donor.amount_cents, donor.currency)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* 7-day momentum */}
          <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
            <span className="text-sm text-gray-500">{LABEL_MOMENTUM_7D}</span>
            <span className="text-sm font-semibold text-gray-900">
              {socialProof.donations_last_7_days}
            </span>
          </div>
        </div>

        {/* Campaign Info */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="h-5 w-5 text-gray-400" />
            {LABEL_CAMPAIGN_INFO}
          </h2>
          <dl className="space-y-3">
            <InfoRow label={LABEL_STATUS}>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[campaign.status] ?? "bg-gray-100 text-gray-700"}`}>
                {STATUS_LABELS[campaign.status] ?? campaign.status}
              </span>
            </InfoRow>
            <InfoRow label={LABEL_CATEGORY}>
              {getCategoryLabel(campaign.fund_category as Parameters<typeof getCategoryLabel>[0])}
            </InfoRow>
            <InfoRow label={LABEL_GOAL}>
              {formatCurrency(campaign.target_amount_cents, campaign.currency)}
            </InfoRow>
            <InfoRow label={LABEL_FEATURED}>
              {campaign.featured ? LABEL_YES : LABEL_NO}
            </InfoRow>
            <InfoRow label={LABEL_OVERFUNDING}>
              {campaign.allow_overfunding ? LABEL_YES : LABEL_NO}
            </InfoRow>
            <InfoRow label={LABEL_DEADLINE}>
              {campaign.deadline
                ? new Date(campaign.deadline).toLocaleDateString("es-PY", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })
                : LABEL_NO_DEADLINE}
            </InfoRow>
            <InfoRow label={LABEL_CREATED}>
              {new Date(campaign.created_at).toLocaleDateString("es-PY", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </InfoRow>
            <InfoRow label={LABEL_UPDATED}>
              {new Date(campaign.updated_at).toLocaleDateString("es-PY", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </InfoRow>
          </dl>
        </div>
      </div>
    </div>
  );
}

/** Compact stat box used in the stats grid. */
function StatBox({
  icon,
  label,
  value,
  bgColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  bgColor: string;
}) {
  return (
    <div className={`${bgColor} rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

/** Key-value row for the campaign info panel. */
function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
      <dt className="text-sm text-gray-500">{label}</dt>
      <dd className="text-sm font-medium text-gray-900">{children}</dd>
    </div>
  );
}
