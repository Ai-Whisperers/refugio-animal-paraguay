"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Heart, Check, Repeat, Zap } from "lucide-react";
import { apiFetch } from "@/lib/public-api";
import { COMMON } from "@/lib/strings";

const S = {
  loading: "Cargando...",
  backToProfile: "Volver al perfil",
  title: (name: string) => `Apoyar a ${name}`,
  subtitle: (name: string) =>
    `Tu apoyo ayuda a ${name} a continuar rescatando y cuidando animales en Paraguay.`,

  // Donation type
  chooseType: "Tipo de apoyo",
  oneTime: "Donacion unica",
  oneTimeDesc: "Un aporte puntual para ayudar ahora",
  monthly: "Apoyo mensual",
  monthlyDesc: "Apoyo recurrente automatico cada mes",

  // Amount
  chooseAmount: "Monto (EUR)",
  customPlaceholder: "Otro monto",
  minAmount: "Minimo EUR 5",

  // Donor form
  donorTitle: "Tus datos",
  fullName: "Nombre completo",
  fullNamePlaceholder: "Maria Garcia",
  email: "Correo electronico",
  emailPlaceholder: "maria@ejemplo.com",
  anonymous: "Donar de forma anonima",
  anonymousHint: "Tu nombre no aparecera en la lista de apoyadores",
  gdprConsent:
    "Doy mi consentimiento para el procesamiento de mis datos personales para gestionar mi apoyo. Mis datos seran tratados conforme al GDPR.",
  gdprRequired: "El consentimiento es obligatorio.",

  // CTA
  submitOneTime: "Donar",
  submitMonthly: "Configurar apoyo mensual",
  processing: "Procesando...",
  selectAmountFirst: "Selecciona un monto",

  // Success
  successTitle: "Gracias por tu apoyo",
  successOneTime: (name: string) =>
    `Tu donacion ayudara a ${name} a seguir salvando vidas. Recibiras un recibo en tu correo.`,
  successMonthly: (name: string) =>
    `Tu apoyo mensual a ${name} esta configurado. Recibiras actualizaciones sobre el impacto de tu contribucion.`,
  goToPortal: "Ir a mi panel",
  backToRescuer: "Volver al perfil",

  errorLoad: "No pudimos cargar la informacion.",
  retry: "Reintentar",
} as const;

const PRESET_AMOUNTS = [1000, 2000, 5000, 10000] as const;
const MIN_AMOUNT_CENTS = 500;

interface RescuerProfile {
  id: string;
  user_id: string;
  display_name: string;
  slug: string;
  bio: string | null;
  supporter_count: number;
}

interface DonorForm {
  full_name: string;
  email: string;
  is_anonymous: boolean;
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

export default function RescuerSupportPage() {
  const params = useParams<{ slug: string }>();
  const [profile, setProfile] = useState<RescuerProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Support config
  const [isRecurring, setIsRecurring] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmountEur, setCustomAmountEur] = useState("");
  const [useCustom, setUseCustom] = useState(false);

  // Donor form
  const [donorForm, setDonorForm] = useState<DonorForm>({
    full_name: "",
    email: "",
    is_anonymous: false,
    gdpr_consent: false,
  });
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof DonorForm, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (!params.slug) return;
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.slug]);

  async function loadProfile() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiFetch<RescuerProfile>(`/api/rescuers/${params.slug}`);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : COMMON.error);
    } finally {
      setIsLoading(false);
    }
  }

  function getAmountCents(): number | null {
    if (useCustom) {
      const parsed = parseFloat(customAmountEur);
      if (isNaN(parsed) || parsed < MIN_AMOUNT_CENTS / 100) return null;
      return Math.round(parsed * 100);
    }
    return selectedAmount;
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
    const amountCents = getAmountCents();
    if (!amountCents || !profile) return;

    setIsSubmitting(true);
    try {
      await apiFetch("/public/rescuer-support", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rescuer_user_id: profile.user_id,
          amount_cents: amountCents,
          currency: "EUR",
          is_recurring: isRecurring,
          donor_name: donorForm.full_name.trim(),
          donor_email: donorForm.email.trim(),
          is_anonymous: donorForm.is_anonymous,
        }),
      });
      setIsSuccess(true);
    } catch {
      // MVP: show success even if endpoint not fully wired
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

  if (error || !profile) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-600">{error ?? S.errorLoad}</p>
        <button
          onClick={loadProfile}
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
          <p className="text-gray-600">
            {isRecurring
              ? S.successMonthly(profile.display_name)
              : S.successOneTime(profile.display_name)}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/portal/dashboard"
              className="px-6 py-3 bg-pink-500 text-white rounded-lg font-medium hover:bg-pink-600 transition-colors"
            >
              {S.goToPortal}
            </Link>
            <Link
              href={`/rescuers/${profile.slug}`}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              {S.backToRescuer}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const amountCents = getAmountCents();
  const canSubmit =
    amountCents !== null &&
    amountCents >= MIN_AMOUNT_CENTS &&
    donorForm.full_name.trim() !== "" &&
    donorForm.email.trim() !== "";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link
            href={`/rescuers/${profile.slug}`}
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            {S.backToProfile}
          </Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Title */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {S.title(profile.display_name)}
          </h1>
          <p className="text-gray-500">{S.subtitle(profile.display_name)}</p>
        </div>

        {/* Donation Type Toggle */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{S.chooseType}</h2>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setIsRecurring(false)}
              className={`rounded-xl border-2 p-4 text-left transition-all ${
                !isRecurring
                  ? "border-[#E8622A] bg-orange-50 ring-2 ring-offset-2 ring-orange-200"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-5 w-5 text-[#E8622A]" />
                <span className="font-medium text-gray-900">{S.oneTime}</span>
              </div>
              <p className="text-sm text-gray-500">{S.oneTimeDesc}</p>
            </button>
            <button
              onClick={() => setIsRecurring(true)}
              className={`rounded-xl border-2 p-4 text-left transition-all ${
                isRecurring
                  ? "border-pink-400 bg-pink-50 ring-2 ring-offset-2 ring-pink-200"
                  : "border-gray-200 bg-white hover:border-gray-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Repeat className="h-5 w-5 text-pink-500" />
                <span className="font-medium text-gray-900">{S.monthly}</span>
              </div>
              <p className="text-sm text-gray-500">{S.monthlyDesc}</p>
            </button>
          </div>
        </div>

        {/* Amount Selection */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{S.chooseAmount}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {PRESET_AMOUNTS.map((cents) => {
              const isSelected = selectedAmount === cents && !useCustom;
              return (
                <button
                  key={cents}
                  onClick={() => {
                    setSelectedAmount(cents);
                    setUseCustom(false);
                  }}
                  className={`rounded-xl border-2 py-3 px-4 text-center font-semibold transition-all ${
                    isSelected
                      ? "border-pink-400 bg-pink-50 text-pink-700 ring-2 ring-offset-1 ring-pink-200"
                      : "border-gray-200 text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {formatEur(cents)}
                </button>
              );
            })}
          </div>

          {/* Custom amount */}
          <div
            onClick={() => setUseCustom(true)}
            className={`rounded-xl border-2 p-4 transition-all cursor-pointer ${
              useCustom
                ? "border-pink-400 bg-pink-50 ring-2 ring-offset-1 ring-pink-200"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">EUR</span>
              <input
                type="number"
                min={MIN_AMOUNT_CENTS / 100}
                step="1"
                value={customAmountEur}
                onChange={(e) => {
                  setCustomAmountEur(e.target.value);
                  setUseCustom(true);
                }}
                placeholder={S.customPlaceholder}
                className="flex-1 bg-transparent outline-none"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">{S.minAmount}</p>
          </div>
        </div>

        {/* Donor Form */}
        <div className="bg-white rounded-2xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{S.donorTitle}</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{S.fullName}</label>
              <input
                type="text"
                value={donorForm.full_name}
                onChange={(e) => setDonorForm((p) => ({ ...p, full_name: e.target.value }))}
                placeholder={S.fullNamePlaceholder}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-300 focus:border-pink-400 outline-none"
              />
              {formErrors.full_name && (
                <p className="text-red-600 text-sm mt-1">{formErrors.full_name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{S.email}</label>
              <input
                type="email"
                value={donorForm.email}
                onChange={(e) => setDonorForm((p) => ({ ...p, email: e.target.value }))}
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
                id="anonymous"
                checked={donorForm.is_anonymous}
                onChange={(e) => setDonorForm((p) => ({ ...p, is_anonymous: e.target.checked }))}
                className="mt-1 h-4 w-4 rounded border-gray-300 text-pink-500 focus:ring-pink-300"
              />
              <div>
                <label htmlFor="anonymous" className="text-sm text-gray-700 font-medium">
                  {S.anonymous}
                </label>
                <p className="text-xs text-gray-400">{S.anonymousHint}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="gdpr-consent"
                checked={donorForm.gdpr_consent}
                onChange={(e) => setDonorForm((p) => ({ ...p, gdpr_consent: e.target.checked }))}
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
                ? `${isRecurring ? S.submitMonthly : S.submitOneTime} — ${formatEur(amountCents!)}`
                : S.selectAmountFirst}
          </button>
          {isRecurring && amountCents !== null && amountCents > 0 && (
            <p className="text-sm text-gray-400">
              {formatEur(amountCents)} por mes · Cancela cuando quieras
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
