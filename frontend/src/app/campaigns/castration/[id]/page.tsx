"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Heart,
  MapPin,
  Calendar,
  Target,
  Share2,
  MessageCircle,
  Mail,
  Copy,
  Check,
  ArrowLeft,
  ExternalLink,
  Printer,
  Clock,
} from "lucide-react";
import type { CastrationCampaignPublic } from "@/types/api";
import { getCastrationCampaignPublic } from "@/lib/public-api";

// --- Constants ---
const WHATSAPP_BASE = "https://wa.me/595981000000";
const MILESTONE_PERCENTS = [25, 50, 75, 100];
const COUNTER_ANIMATION_DURATION_MS = 1500;
const COUNTER_ANIMATION_STEPS = 60;

// --- Spanish strings ---
const S = {
  loading: "Cargando campana...",
  notFound: "Campana no encontrada",
  backToCampaigns: "Ver todas las campanas",
  heroLabel: "Animales esterilizados",
  of: "de",
  goal: "objetivo",
  goalReached: "Meta alcanzada!",
  goalMessage: "Mensaje de la campana",
  progressLabel: (pct: number) => `${pct}% completado`,
  milestoneMsg: (pct: number) => `Alcanzamos el ${pct}% de nuestra meta!`,
  impactTitle: "Impacto de la campana",
  surgeriesPerformed: "Cirugias realizadas",
  targetGoal: "Objetivo",
  progressPercent: "Progreso",
  clinicsTitle: "Clinicas asociadas",
  noClinicLocation: "Ubicacion no disponible",
  dateRange: (start: string, end: string) => `Campana del ${start} al ${end}`,
  campaignEnded: (end: string) => `Campana finalizada el ${end}`,
  campaignActive: "Campana en curso",
  campaignPlanned: "Campana programada",
  targetArea: (area: string) => `Zona: ${area}`,
  donateCTA: "Apoyar programa de esterilizacion",
  donateSubtitle: "Tu donacion ayuda a esterilizar mas animales",
  shareTitle: "Compartir campana",
  shareWhatsApp: "Compartir por WhatsApp",
  shareEmail: "Compartir por email",
  shareCopied: "Enlace copiado!",
  shareCopyLink: "Copiar enlace",
  shareMsg: (title: string, pct: number) =>
    `Mira esta campana de esterilizacion: "${title}" — ya completamos ${pct}%! Apoya en:`,
  shareEmailSubject: (title: string) => `Campana de esterilizacion: ${title}`,
  printResults: "Imprimir",
  statusPlanned: "Programada",
  statusActive: "En curso",
  statusCompleted: "Finalizada",
} as const;

// --- Helpers ---

function formatDateES(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function statusBadge(status: string): { label: string; className: string } {
  switch (status) {
    case "active":
      return { label: S.statusActive, className: "bg-green-100 text-green-800" };
    case "completed":
      return { label: S.statusCompleted, className: "bg-blue-100 text-blue-800" };
    default:
      return { label: S.statusPlanned, className: "bg-gray-100 text-gray-700" };
  }
}

function highestMilestoneReached(pct: number): number | null {
  for (let i = MILESTONE_PERCENTS.length - 1; i >= 0; i--) {
    if (pct >= MILESTONE_PERCENTS[i]) return MILESTONE_PERCENTS[i];
  }
  return null;
}

// --- Animated Counter Hook ---

function useAnimatedCounter(target: number, isVisible: boolean): number {
  const [current, setCurrent] = useState(0);
  const prevTarget = useRef(0);

  useEffect(() => {
    if (!isVisible) return;
    const start = prevTarget.current;
    const diff = target - start;
    if (diff === 0) return;

    let step = 0;
    const interval = setInterval(() => {
      step++;
      const progress = step / COUNTER_ANIMATION_STEPS;
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(start + diff * eased));

      if (step >= COUNTER_ANIMATION_STEPS) {
        clearInterval(interval);
        setCurrent(target);
        prevTarget.current = target;
      }
    }, COUNTER_ANIMATION_DURATION_MS / COUNTER_ANIMATION_STEPS);

    return () => clearInterval(interval);
  }, [target, isVisible]);

  return current;
}

// --- Progress Bar ---

function ProgressBar({ percent }: { percent: number }) {
  const clampedPct = Math.min(percent, 100);

  return (
    <div className="relative w-full">
      {/* Track */}
      <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-[#E8622A] to-[#f59e0b]"
          style={{ width: `${clampedPct}%` }}
        />
      </div>
      {/* Milestone markers */}
      <div className="relative w-full h-0">
        {MILESTONE_PERCENTS.map((m) => (
          <div
            key={m}
            className="absolute -top-4 flex flex-col items-center"
            style={{ left: `${m}%`, transform: "translateX(-50%)" }}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                clampedPct >= m ? "bg-[#E8622A]" : "bg-gray-300"
              }`}
            />
            <span className="text-[10px] text-gray-400 mt-0.5">{m}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Share Dropdown ---

function ShareDropdown({
  title,
  campaignId,
  progressPercent,
}: {
  title: string;
  campaignId: string;
  progressPercent: number;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const pageUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/campaigns/castration/${campaignId}`
      : "";

  const message = S.shareMsg(title, progressPercent);
  const whatsappUrl = `${WHATSAPP_BASE}?text=${encodeURIComponent(`${message} ${pageUrl}`)}`;
  const emailSubject = encodeURIComponent(S.shareEmailSubject(title));
  const emailBody = encodeURIComponent(`${message}\n\n${pageUrl}`);
  const emailUrl = `mailto:?subject=${emailSubject}&body=${emailBody}`;

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(pageUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable
    }
  }, [pageUrl]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors text-sm"
        aria-expanded={open}
      >
        <Share2 className="h-4 w-4" />
        {S.shareTitle}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-1">
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setOpen(false)}
            >
              <MessageCircle className="h-4 w-4 text-[#25D366]" />
              {S.shareWhatsApp}
            </a>
            <a
              href={emailUrl}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setOpen(false)}
            >
              <Mail className="h-4 w-4 text-blue-500" />
              {S.shareEmail}
            </a>
            <button
              onClick={() => {
                handleCopy();
                setOpen(false);
              }}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 w-full text-left"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4 text-gray-400" />
              )}
              {copied ? S.shareCopied : S.shareCopyLink}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// --- Main Page ---

export default function CastrationCampaignPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<CastrationCampaignPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const [heroVisible, setHeroVisible] = useState(false);

  useEffect(() => {
    if (!params.id) return;
    async function fetchCampaign() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getCastrationCampaignPublic(params.id);
        setCampaign(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : S.notFound);
      } finally {
        setIsLoading(false);
      }
    }
    fetchCampaign();
  }, [params.id]);

  // Observe hero for counter animation trigger
  useEffect(() => {
    if (!heroRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setHeroVisible(true);
      },
      { threshold: 0.3 }
    );
    observer.observe(heroRef.current);
    return () => observer.disconnect();
  }, [campaign]);

  const animatedCount = useAnimatedCounter(
    campaign?.completed_count ?? 0,
    heroVisible
  );

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#E8622A] border-r-transparent" />
        <p className="mt-3 text-gray-500">{S.loading}</p>
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 mb-4">{error ?? S.notFound}</p>
        <Link href="/campaigns" className="text-[#E8622A] hover:underline font-medium">
          {S.backToCampaigns}
        </Link>
      </div>
    );
  }

  const badge = statusBadge(campaign.status);
  const milestone = highestMilestoneReached(campaign.progress_percent);
  const isActive = campaign.status === "active";
  const isCompleted = campaign.status === "completed";

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 print:px-0 print:py-4">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500 print:hidden">
        <Link href="/campaigns" className="hover:text-[#E8622A] transition-colors">
          Campanas
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{campaign.title}</span>
      </nav>

      {/* Hero Section */}
      <div
        ref={heroRef}
        className="bg-gradient-to-br from-[#E8622A] to-[#d4571f] rounded-2xl p-8 sm:p-12 text-white mb-8 relative overflow-hidden"
      >
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/3 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/3 -translate-x-1/3" />

        <div className="relative z-10">
          {/* Status + area */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${badge.className}`}>
              {badge.label}
            </span>
            <span className="flex items-center gap-1 text-sm text-white/80">
              <MapPin className="h-3.5 w-3.5" />
              {S.targetArea(campaign.target_area)}
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-bold mb-2">
            {campaign.title}
          </h1>

          {/* Counter */}
          <div className="mt-8 mb-6">
            <p className="text-sm text-white/70 uppercase tracking-wide mb-2">
              {S.heroLabel}
            </p>
            <div className="flex items-baseline gap-3">
              <span className="text-6xl sm:text-7xl font-bold tabular-nums">
                {animatedCount}
              </span>
              <span className="text-2xl text-white/60">
                {S.of} {campaign.target_count}
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <ProgressBar percent={campaign.progress_percent} />
            <p className="text-sm text-white/70 mt-3">
              {S.progressLabel(campaign.progress_percent)}
            </p>
          </div>

          {/* Milestone message */}
          {milestone && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-lg">
              <Target className="h-4 w-4" />
              <span className="text-sm font-medium">
                {campaign.progress_percent >= 100
                  ? S.goalReached
                  : S.milestoneMsg(milestone)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Description + Goal Message */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 sm:p-8 mb-8">
        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
          {campaign.description}
        </p>
        {campaign.goal_message && (
          <div className="mt-6 p-4 bg-orange-50 border border-orange-100 rounded-lg">
            <p className="text-sm font-medium text-[#E8622A] mb-1">
              {S.goalMessage}
            </p>
            <p className="text-gray-700 text-sm italic">
              &ldquo;{campaign.goal_message}&rdquo;
            </p>
          </div>
        )}
      </div>

      {/* Impact Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 text-center">
          <p className="text-3xl font-bold text-[#E8622A]">
            {campaign.completed_count}
          </p>
          <p className="text-sm text-gray-500 mt-1">{S.surgeriesPerformed}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 text-center">
          <p className="text-3xl font-bold text-gray-900">
            {campaign.target_count}
          </p>
          <p className="text-sm text-gray-500 mt-1">{S.targetGoal}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 text-center">
          <p className="text-3xl font-bold text-green-600">
            {campaign.progress_percent}%
          </p>
          <p className="text-sm text-gray-500 mt-1">{S.progressPercent}</p>
        </div>
      </div>

      {/* Date info */}
      <div className="flex flex-wrap items-center gap-4 mb-8 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-gray-400" />
          {isCompleted
            ? S.campaignEnded(formatDateES(campaign.end_date))
            : S.dateRange(
                formatDateES(campaign.start_date),
                formatDateES(campaign.end_date)
              )}
        </div>
        {isActive && (
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-green-500" />
            <span className="text-green-600 font-medium">{S.campaignActive}</span>
          </div>
        )}
      </div>

      {/* Partner Clinics */}
      {campaign.partner_clinics.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            {S.clinicsTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campaign.partner_clinics.map((clinic) => (
              <div
                key={clinic.id}
                className="flex items-start gap-4 p-4 bg-white rounded-xl border border-gray-100 shadow-sm"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center">
                  <Heart className="h-5 w-5 text-[#E8622A]" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{clinic.name}</p>
                  <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                    <MapPin className="h-3 w-3" />
                    {clinic.city}
                    {clinic.department && `, ${clinic.department}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Donate CTA */}
      {isActive && (
        <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl border border-orange-100 p-6 sm:p-8 mb-8 text-center">
          <Heart className="h-8 w-8 text-[#E8622A] mx-auto mb-3" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {S.donateCTA}
          </h2>
          <p className="text-sm text-gray-600 mb-4">{S.donateSubtitle}</p>
          <Link
            href="/donate"
            className="inline-flex items-center gap-2 bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
          >
            <Heart className="h-4 w-4" />
            {S.donateCTA}
          </Link>
        </div>
      )}

      {/* Actions bar */}
      <div className="flex flex-wrap items-center gap-3 print:hidden">
        <Link
          href="/campaigns"
          className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          {S.backToCampaigns}
        </Link>
        <ShareDropdown
          title={campaign.title}
          campaignId={campaign.id}
          progressPercent={campaign.progress_percent}
        />
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg font-medium hover:bg-gray-50 transition-colors text-sm"
        >
          <Printer className="h-4 w-4" />
          {S.printResults}
        </button>
      </div>

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          nav,
          header,
          footer,
          .print\\:hidden {
            display: none !important;
          }
          body {
            font-size: 12pt;
            color: #000;
          }
          a {
            text-decoration: none;
            color: inherit;
          }
        }
      `}</style>
    </div>
  );
}
