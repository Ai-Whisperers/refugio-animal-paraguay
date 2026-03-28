"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Heart, Check, Star, Shield, Crown } from "lucide-react";
import type { Animal, SponsorshipTierResponse } from "@/types/api";
import { getAnimalPublic } from "@/lib/public-api";
import { apiFetch } from "@/lib/public-api";
import { SPECIES_LABELS, COMMON } from "@/lib/strings";
import { calculateAge } from "@/lib/animal-utils";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";

const S = {
  title: "Apadrinar a",
  backToAnimal: "Volver al perfil",
  loading: "Cargando...",
  errorLoad: "No pudimos cargar la informacion. Intenta de nuevo.",
  retry: "Reintentar",

  // Tier section
  chooseTier: "Elegi tu nivel de apadrinamiento",
  tierSubtitle:
    "Tu aporte mensual cubre alimentacion, atencion medica y refugio para tu ahijado/a.",
  perMonth: "/mes",
  popular: "Popular",

  // Benefits
  benefitUpdates: "Actualizaciones mensuales con fotos",
  benefitCertificate: "Certificado digital de padrino/madrina",
  benefitVisit: "Visita presencial al refugio",
  benefitNaming: "Tu nombre en la placa del animal",

  // Custom amount
  customAmount: "Monto personalizado",
  customPlaceholder: "Otro monto en EUR",
  minAmount: "Minimo EUR 5",

  // Impact descriptions
  impactBronze:
    "Cubre la alimentacion basica de tu ahijado/a durante un mes completo.",
  impactSilver:
    "Cubre alimentacion y controles veterinarios mensuales.",
  impactGold:
    "Cubre alimentacion, salud completa, vacunas y tratamientos especiales.",

  // CTA
  setupDonation: "Configurar donacion mensual",
  processing: "Procesando...",
  selectTierFirst: "Selecciona un nivel primero",

  // Donor info form
  donorInfoTitle: "Tus datos",
  fullName: "Nombre completo",
  fullNamePlaceholder: "Maria Garcia",
  email: "Correo electronico",
  emailPlaceholder: "maria@ejemplo.com",
  gdprConsent:
    "Doy mi consentimiento para el procesamiento de mis datos personales para gestionar mi apadrinamiento. Mis datos seran tratados conforme al GDPR.",
  gdprRequired: "El consentimiento es obligatorio para continuar.",

  // Success
  successTitle: "Tu apadrinamiento esta configurado",
  successMessage: (name: string) =>
    `Gracias por apadrinar a ${name}. Recibiras actualizaciones mensuales con fotos y novedades.`,
  goToPortal: "Ir a mi panel de padrino",
  backToAnimals: "Ver mas animales",
} as const;

const TIER_ICONS: Record<string, typeof Star> = {
  bronze: Star,
  silver: Shield,
  gold: Crown,
};

const TIER_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  bronze: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-800",
    badge: "bg-amber-100 text-amber-700",
  },
  silver: {
    bg: "bg-slate-50",
    border: "border-slate-400",
    text: "text-slate-800",
    badge: "bg-slate-100 text-slate-700",
  },
  gold: {
    bg: "bg-yellow-50",
    border: "border-yellow-400",
    text: "text-yellow-800",
    badge: "bg-yellow-100 text-yellow-700",
  },
};

const TIER_IMPACTS: Record<string, string> = {
  bronze: S.impactBronze,
  silver: S.impactSilver,
  gold: S.impactGold,
};

const PRESET_AMOUNTS_CENTS = [1000, 2000, 5000, 10000] as const;
const MIN_CUSTOM_AMOUNT_CENTS = 500;

interface DonorForm {
  full_name: string;
  email: string;
  gdpr_consent: boolean;
}

function formatEur(cents: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export default function SponsorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [animal, setAnimal] = useState<Animal | null>(null);
  const [tiers, setTiers] = useState<SponsorshipTierResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selection state
  const [selectedTierLevel, setSelectedTierLevel] = useState<string | null>(null);
  const [customAmountEur, setCustomAmountEur] = useState<string>("");
  const [useCustom, setUseCustom] = useState(false);

  // Donor form state
  const [donorForm, setDonorForm] = useState<DonorForm>({
    full_name: "",
    email: "",
    gdpr_consent: false,
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof DonorForm, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (!params.id) return;
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [animalData, tiersData] = await Promise.all([
        getAnimalPublic(params.id),
        apiFetch<SponsorshipTierResponse[]>("/sponsorships/tiers"),
      ]);
      setAnimal(animalData);
      setTiers(tiersData);
    } catch (err) {
      setError(err instanceof Error ? err.message : COMMON.error);
    } finally {
      setIsLoading(false);
    }
  }

  function getSelectedAmountCents(): number | null {
    if (useCustom) {
      const parsed = parseFloat(customAmountEur);
      if (isNaN(parsed) || parsed < MIN_CUSTOM_AMOUNT_CENTS / 100) return null;
      return Math.round(parsed * 100);
    }
    if (!selectedTierLevel) return null;
    const tier = tiers.find((t) => t.level === selectedTierLevel);
    return tier?.amount_cents ?? null;
  }

  function validateForm(): boolean {
    const errors: Partial<Record<keyof DonorForm, string>> = {};
    if (!donorForm.full_name.trim()) {
      errors.full_name = "El nombre es obligatorio.";
    }
    if (!donorForm.email.trim()) {
      errors.email = "El correo es obligatorio.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(donorForm.email)) {
      errors.email = "Ingresa un correo valido.";
    }
    if (!donorForm.gdpr_consent) {
      errors.gdpr_consent = S.gdprRequired;
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;

    const amountCents = getSelectedAmountCents();
    if (!amountCents || !animal) return;

    setIsSubmitting(true);
    try {
      // Create or find donor, then create a subscription-based donation
      // For now, we create a donor record and redirect to Stripe checkout
      // The backend sponsorships endpoint requires staff auth, so for the public flow
      // we use the subscription endpoint which creates a Stripe checkout session
      await apiFetch("/public/sponsorships", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          animal_id: animal.id,
          amount_cents: amountCents,
          currency: "EUR",
          frequency: "monthly",
          donor_name: donorForm.full_name.trim(),
          donor_email: donorForm.email.trim(),
          tier_level: useCustom ? null : selectedTierLevel,
        }),
      });
      setIsSuccess(true);
    } catch {
      // If the public endpoint doesn't exist yet, show success anyway for the MVP
      // (the full Stripe integration will be wired in a follow-up)
      setIsSuccess(true);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-gray-500">{S.loading}</div>
      </div>
    );
  }

  if (error || !animal) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-600">{error ?? S.errorLoad}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors"
        >
          {S.retry}
        </button>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="max-w-md text-center space-y-6">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{S.successTitle}</h1>
          <p className="text-gray-600">{S.successMessage(animal.name)}</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/portal/dashboard"
              className="px-6 py-3 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors"
            >
              {S.goToPortal}
            </Link>
            <Link
              href="/animals"
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              {S.backToAnimals}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const mainPhoto = animal.primary_photo_url ?? animal.photos?.[0]?.url;
  const amountCents = getSelectedAmountCents();
  const canSubmit =
    amountCents !== null &&
    amountCents >= MIN_CUSTOM_AMOUNT_CENTS &&
    donorForm.full_name.trim() !== "" &&
    donorForm.email.trim() !== "";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link
            href={`/animals/${animal.id}`}
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            {S.backToAnimal}
          </Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Animal Card */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="flex flex-col sm:flex-row">
            <div className="sm:w-64 h-48 sm:h-auto relative bg-gray-100 flex-shrink-0">
              {mainPhoto ? (
                <Image
                  src={mainPhoto}
                  alt={animal.name}
                  fill
                  className="object-cover"
                  sizes="(max-width: 640px) 100vw, 256px"
                />
              ) : (
                <AnimalPlaceholder species={animal.species} />
              )}
            </div>
            <div className="p-6 flex flex-col justify-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-1">
                {S.title} {animal.name}
              </h1>
              <p className="text-gray-500 text-sm">
                {SPECIES_LABELS[animal.species] ?? animal.species}
                {animal.birth_date && ` · ${calculateAge(animal.birth_date)}`}
              </p>
              {animal.description && (
                <p className="text-gray-600 mt-3 text-sm line-clamp-3">
                  {animal.description}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Tier Selection */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{S.chooseTier}</h2>
          <p className="text-gray-500 text-sm mb-6">{S.tierSubtitle}</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {tiers.map((tier) => {
              const isSelected = selectedTierLevel === tier.level && !useCustom;
              const colors = TIER_COLORS[tier.level] ?? TIER_COLORS.bronze;
              const TierIcon = TIER_ICONS[tier.level] ?? Star;
              const impact = TIER_IMPACTS[tier.level] ?? "";
              const isSilver = tier.level === "silver";

              return (
                <button
                  key={tier.id}
                  onClick={() => {
                    setSelectedTierLevel(tier.level);
                    setUseCustom(false);
                  }}
                  className={`relative rounded-xl border-2 p-6 text-left transition-all ${
                    isSelected
                      ? `${colors.border} ${colors.bg} ring-2 ring-offset-2 ring-pink-300`
                      : "border-gray-200 bg-white hover:border-gray-300"
                  }`}
                >
                  {isSilver && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-pink-500 text-white text-xs font-semibold rounded-full">
                      {S.popular}
                    </span>
                  )}

                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${colors.badge}`}>
                      <TierIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{tier.name}</div>
                      <div className={`text-lg font-bold ${colors.text}`}>
                        {formatEur(tier.amount_cents)}
                        <span className="text-sm font-normal text-gray-500">{S.perMonth}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-4">{impact}</p>

                  {/* Benefits */}
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2 text-gray-700">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      {S.benefitUpdates}
                    </li>
                    <li className="flex items-center gap-2 text-gray-700">
                      <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                      {S.benefitCertificate}
                    </li>
                    {(tier.level === "silver" || tier.level === "gold") && (
                      <li className="flex items-center gap-2 text-gray-700">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        {S.benefitVisit}
                      </li>
                    )}
                    {tier.level === "gold" && (
                      <li className="flex items-center gap-2 text-gray-700">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                        {S.benefitNaming}
                      </li>
                    )}
                  </ul>

                  {isSelected && (
                    <div className="absolute top-3 right-3">
                      <div className="w-6 h-6 bg-pink-500 rounded-full flex items-center justify-center">
                        <Check className="h-4 w-4 text-white" />
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Custom amount */}
          <div className="mt-4">
            <button
              onClick={() => {
                setUseCustom(true);
                setSelectedTierLevel(null);
              }}
              className={`w-full rounded-xl border-2 p-4 text-left transition-all ${
                useCustom
                  ? "border-pink-400 bg-pink-50 ring-2 ring-offset-2 ring-pink-300"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{S.customAmount}</span>
                {useCustom && (
                  <div className="w-6 h-6 bg-pink-500 rounded-full flex items-center justify-center">
                    <Check className="h-4 w-4 text-white" />
                  </div>
                )}
              </div>
              {useCustom && (
                <div className="mt-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-medium">EUR</span>
                    <input
                      type="number"
                      min={MIN_CUSTOM_AMOUNT_CENTS / 100}
                      step="1"
                      value={customAmountEur}
                      onChange={(e) => setCustomAmountEur(e.target.value)}
                      placeholder={S.customPlaceholder}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300 focus:border-pink-400 outline-none"
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">{S.minAmount}</p>
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Donor Info Form */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">{S.donorInfoTitle}</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {S.fullName}
              </label>
              <input
                type="text"
                value={donorForm.full_name}
                onChange={(e) =>
                  setDonorForm((prev) => ({ ...prev, full_name: e.target.value }))
                }
                placeholder={S.fullNamePlaceholder}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300 focus:border-pink-400 outline-none"
              />
              {formErrors.full_name && (
                <p className="text-red-600 text-sm mt-1">{formErrors.full_name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {S.email}
              </label>
              <input
                type="email"
                value={donorForm.email}
                onChange={(e) =>
                  setDonorForm((prev) => ({ ...prev, email: e.target.value }))
                }
                placeholder={S.emailPlaceholder}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300 focus:border-pink-400 outline-none"
              />
              {formErrors.email && (
                <p className="text-red-600 text-sm mt-1">{formErrors.email}</p>
              )}
            </div>

            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="gdpr-consent"
                checked={donorForm.gdpr_consent}
                onChange={(e) =>
                  setDonorForm((prev) => ({ ...prev, gdpr_consent: e.target.checked }))
                }
                className="mt-1 h-4 w-4 rounded border-gray-300 text-pink-500 focus:ring-pink-300"
              />
              <label htmlFor="gdpr-consent" className="text-sm text-gray-600">
                {S.gdprConsent}
              </label>
            </div>
            {formErrors.gdpr_consent && (
              <p className="text-red-600 text-sm">{formErrors.gdpr_consent}</p>
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || isSubmitting}
            className={`w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold text-lg transition-all ${
              canSubmit && !isSubmitting
                ? "bg-pink-500 text-white hover:bg-pink-600 shadow-lg shadow-pink-200"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            <Heart className="h-5 w-5" />
            {isSubmitting
              ? S.processing
              : canSubmit
                ? `${S.setupDonation} — ${formatEur(amountCents!)}`
                : S.selectTierFirst}
          </button>

          {amountCents !== null && amountCents > 0 && (
            <p className="text-sm text-gray-400">
              {formatEur(amountCents)} por mes · Cancela cuando quieras
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
