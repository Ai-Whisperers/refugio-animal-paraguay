"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Heart,
  Stethoscope,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import {
  getClinicPublic,
  getClinicFundingStats,
  createClinicFundDonation,
} from "@/lib/public-api";
import type {
  PublicClinicDetail,
  PublicServiceSummary,
  ClinicFundingStats,
} from "@/types/api";

const S = {
  loading: "Cargando...",
  notFound: "Clinica no encontrada.",
  backToClinic: "Volver a la clinica",
  title: (name: string) => `Apoyar a ${name}`,
  subtitle: "Tu donacion ayuda a financiar servicios veterinarios accesibles.",
  selectService: "Seleccionar servicio (opcional)",
  generalFund: "Fondo general de la clinica",
  selectAmount: "Monto de la donacion",
  customAmount: "Otro monto",
  customPlaceholder: "Monto en EUR",
  minAmount: "Minimo EUR 5,00",
  donorInfo: "Tus datos",
  fullName: "Nombre completo",
  email: "Correo electronico",
  message: "Mensaje (opcional)",
  messagePlaceholder: "Ej: Para castraciones en la comunidad",
  gdprConsent: "Acepto el procesamiento de mis datos personales segun la politica de privacidad.",
  submit: "Donar ahora",
  submitting: "Procesando...",
  successTitle: "Gracias por tu apoyo!",
  successMessage: (name: string) =>
    `Tu donacion a ${name} ha sido registrada exitosamente.`,
  stripeRedirect: "Completar pago con Stripe",
  donateMore: "Hacer otra donacion",
  totalFunded: "Total recaudado",
  donations: "donaciones",
  impactPrefix: "Tu",
  impactSuffix: (name: string) => `ayuda a ${name} a brindar servicios accesibles`,
  errorGeneric: "Error al procesar la donacion. Intente de nuevo.",
  errorRequired: "Este campo es requerido.",
  errorEmail: "Ingrese un correo electronico valido.",
} as const;

const PRESET_AMOUNTS = [1000, 2000, 5000, 10000] as const;
const MINIMUM_CENTS = 500;

function formatEur(cents: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(cents / 100);
}

interface DonorForm {
  full_name: string;
  email: string;
  message: string;
  gdpr_consent: boolean;
}

export default function ClinicFundPage() {
  const params = useParams();
  const clinicId = params.id as string;

  const [clinic, setClinic] = useState<PublicClinicDetail | null>(null);
  const [stats, setStats] = useState<ClinicFundingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedService, setSelectedService] = useState<string>("");
  const [selectedAmount, setSelectedAmount] = useState<number>(2000);
  const [customAmount, setCustomAmount] = useState("");
  const [isCustom, setIsCustom] = useState(false);
  const [form, setForm] = useState<DonorForm>({
    full_name: "",
    email: "",
    message: "",
    gdpr_consent: false,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<{
    message: string;
    stripeUrl: string | null;
  } | null>(null);

  useEffect(() => {
    if (!clinicId) return;
    let cancelled = false;
    setLoading(true);

    Promise.all([getClinicPublic(clinicId), getClinicFundingStats(clinicId)])
      .then(([clinicData, statsData]) => {
        if (cancelled) return;
        setClinic(clinicData);
        setStats(statsData);
      })
      .catch(() => {
        if (!cancelled) setError(S.notFound);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [clinicId]);

  const getAmountCents = useCallback((): number => {
    if (isCustom) {
      const parsed = parseFloat(customAmount.replace(",", "."));
      return Math.round(parsed * 100) || 0;
    }
    return selectedAmount;
  }, [isCustom, customAmount, selectedAmount]);

  const validate = useCallback((): boolean => {
    const errors: Record<string, string> = {};
    if (!form.full_name.trim()) errors.full_name = S.errorRequired;
    if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errors.email = S.errorEmail;
    }
    if (!form.gdpr_consent) errors.gdpr_consent = S.errorRequired;
    const cents = getAmountCents();
    if (cents < MINIMUM_CENTS) errors.amount = S.minAmount;
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [form, getAmountCents]);

  const handleSubmit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    setError(null);

    try {
      const result = await createClinicFundDonation({
        clinic_id: clinicId,
        amount_cents: getAmountCents(),
        currency: "EUR",
        service_id: selectedService || null,
        donor_name: form.full_name.trim(),
        donor_email: form.email.trim().toLowerCase(),
        message: form.message.trim() || null,
      });
      setSuccess({
        message: result.message,
        stripeUrl: result.stripe_checkout_url,
      });
    } catch {
      setError(S.errorGeneric);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">{S.loading}</p>
      </main>
    );
  }

  if (!clinic) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-600">{error ?? S.notFound}</p>
        <Link href="/clinics" className="text-teal-600 hover:underline">
          {S.backToClinic}
        </Link>
      </main>
    );
  }

  if (success) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {S.successTitle}
          </h1>
          <p className="text-gray-600 mb-6">
            {success.message}
          </p>
          {success.stripeUrl && (
            <a
              href={success.stripeUrl}
              className="inline-block bg-teal-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-teal-700 transition-colors mb-4"
            >
              {S.stripeRedirect}
            </a>
          )}
          <div className="mt-4">
            <Link
              href={`/clinics/${clinicId}/fund`}
              onClick={() => setSuccess(null)}
              className="text-teal-600 hover:underline text-sm"
            >
              {S.donateMore}
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-gradient-to-r from-teal-600 to-teal-700 text-white py-8">
        <div className="max-w-3xl mx-auto px-4">
          <Link
            href={`/clinics/${clinicId}`}
            className="inline-flex items-center gap-1 text-teal-200 hover:text-white text-sm mb-3"
          >
            <ArrowLeft className="h-4 w-4" />
            {S.backToClinic}
          </Link>
          <div className="flex items-center gap-3">
            <Stethoscope className="h-8 w-8" />
            <div>
              <h1 className="text-2xl font-bold">{S.title(clinic.name)}</h1>
              <p className="text-teal-100 text-sm">{S.subtitle}</p>
            </div>
          </div>

          {stats && stats.total_funded_cents > 0 && (
            <div className="mt-4 bg-white/10 rounded-lg px-4 py-3">
              <p className="text-sm">
                {S.totalFunded}: <span className="font-bold">{formatEur(stats.total_funded_cents)}</span>
                {" "}({stats.donation_count} {S.donations})
              </p>
            </div>
          )}
        </div>
      </section>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        )}

        {/* Service selection */}
        {clinic.services.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {S.selectService}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => setSelectedService("")}
                className={`border rounded-lg p-3 text-left transition-colors ${
                  selectedService === ""
                    ? "border-teal-500 bg-teal-50"
                    : "border-gray-200 hover:border-teal-300"
                }`}
              >
                <p className="font-medium text-gray-900">{S.generalFund}</p>
              </button>
              {clinic.services.map((svc: PublicServiceSummary) => (
                <button
                  key={svc.id}
                  onClick={() => setSelectedService(svc.id)}
                  className={`border rounded-lg p-3 text-left transition-colors ${
                    selectedService === svc.id
                      ? "border-teal-500 bg-teal-50"
                      : "border-gray-200 hover:border-teal-300"
                  }`}
                >
                  <p className="font-medium text-gray-900">{svc.name}</p>
                  {svc.price_eur !== null && (
                    <p className="text-sm text-teal-600 mt-1">
                      {formatEur(Math.round(svc.price_eur * 100))}
                    </p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Amount selection */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {S.selectAmount}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {PRESET_AMOUNTS.map((amount) => (
              <button
                key={amount}
                onClick={() => {
                  setSelectedAmount(amount);
                  setIsCustom(false);
                }}
                className={`border rounded-lg py-3 text-center font-medium transition-colors ${
                  !isCustom && selectedAmount === amount
                    ? "border-teal-500 bg-teal-50 text-teal-700"
                    : "border-gray-200 text-gray-700 hover:border-teal-300"
                }`}
              >
                {formatEur(amount)}
              </button>
            ))}
          </div>
          <div>
            <button
              onClick={() => setIsCustom(true)}
              className={`text-sm font-medium mb-2 ${
                isCustom ? "text-teal-700" : "text-gray-500 hover:text-teal-600"
              }`}
            >
              {S.customAmount}
            </button>
            {isCustom && (
              <div>
                <input
                  type="number"
                  step="0.01"
                  min="5"
                  placeholder={S.customPlaceholder}
                  value={customAmount}
                  onChange={(e) => setCustomAmount(e.target.value)}
                  className="w-full max-w-xs px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">{S.minAmount}</p>
              </div>
            )}
            {formErrors.amount && (
              <p className="text-sm text-red-600 mt-1">{formErrors.amount}</p>
            )}
          </div>
        </div>

        {/* Donor info */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {S.donorInfo}
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {S.fullName}
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, full_name: e.target.value }))
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
              {formErrors.full_name && (
                <p className="text-sm text-red-600 mt-1">
                  {formErrors.full_name}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {S.email}
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) =>
                  setForm((f) => ({ ...f, email: e.target.value }))
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
              {formErrors.email && (
                <p className="text-sm text-red-600 mt-1">
                  {formErrors.email}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {S.message}
              </label>
              <textarea
                rows={2}
                value={form.message}
                onChange={(e) =>
                  setForm((f) => ({ ...f, message: e.target.value }))
                }
                placeholder={S.messagePlaceholder}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="gdpr"
                checked={form.gdpr_consent}
                onChange={(e) =>
                  setForm((f) => ({ ...f, gdpr_consent: e.target.checked }))
                }
                className="mt-1"
              />
              <label htmlFor="gdpr" className="text-sm text-gray-600">
                {S.gdprConsent}
              </label>
            </div>
            {formErrors.gdpr_consent && (
              <p className="text-sm text-red-600">{formErrors.gdpr_consent}</p>
            )}
          </div>
        </div>

        {/* Impact message */}
        <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-center">
          <Heart className="h-6 w-6 text-teal-500 mx-auto mb-2" />
          <p className="text-teal-800">
            {S.impactPrefix} <span className="font-bold">{formatEur(getAmountCents())}</span>{" "}
            {S.impactSuffix(clinic.name)}
          </p>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="w-full bg-teal-600 text-white py-3 rounded-xl font-semibold text-lg hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? S.submitting : S.submit}
        </button>
      </div>
    </main>
  );
}
