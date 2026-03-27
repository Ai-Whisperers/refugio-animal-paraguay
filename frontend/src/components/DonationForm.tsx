"use client";

import { useState } from "react";
import type { CampaignPublic, CurrencyCode } from "@/types/api";
import {
  createDonation,
  createDonor,
  createStripeIntent,
} from "@/lib/public-api";
import { formatCurrency, getSuggestedAmounts } from "@/lib/campaign-utils";
import StripePaymentStep from "@/components/StripePaymentStep";

interface DonationFormProps {
  campaign: CampaignPublic;
  onSuccess: (donationId: string) => void;
}

/**
 * Multi-step donation form.
 *
 * Steps:
 *   amount     — currency picker, amount presets, custom input, payment method toggle
 *   details    — donor name / email (or anonymous), GDPR consent
 *   payment    — Stripe Elements card/SEPA (only when paymentMethod === "stripe")
 *   submitting — spinner shown while creating donation record or bank-transfer submit
 *   error      — shown after a recoverable error, allows the user to retry
 *
 * For "transfer" payments the flow skips the "payment" step and calls
 * createDonation directly, then invokes onSuccess.
 *
 * For "stripe" payments:
 *   1. createDonor (if not anonymous) → get donorId
 *   2. createDonation → get donationId
 *   3. createStripeIntent(donationId) → get clientSecret
 *   4. Render StripePaymentStep — Stripe.js handles card collection & confirmation
 *   5. On stripe confirmation → onSuccess(donationId)
 */

type FormStep = "amount" | "details" | "payment" | "submitting" | "error";

export default function DonationForm({ campaign, onSuccess }: DonationFormProps) {
  const [step, setStep] = useState<FormStep>("amount");
  const [selectedCurrency, setSelectedCurrency] = useState<CurrencyCode>(campaign.currency);
  const [amountCents, setAmountCents] = useState<number>(0);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [paymentMethod, setPaymentMethod] = useState<"stripe" | "transfer">("stripe");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [gdprConsent, setGdprConsent] = useState(false);

  // Stripe-specific state — set after createStripeIntent resolves
  const [stripeClientSecret, setStripeClientSecret] = useState<string>("");
  const [pendingDonationId, setPendingDonationId] = useState<string>("");

  const suggestedAmounts = getSuggestedAmounts(selectedCurrency);
  // PYG is a zero-decimal currency — amounts are in whole Guaraníes
  const divisor = selectedCurrency === "PYG" ? 1 : 100;

  function handleAmountSelect(cents: number) {
    setAmountCents(cents);
    setCustomAmount("");
  }

  function handleCustomAmountChange(value: string) {
    setCustomAmount(value);
    const parsed = parseFloat(value);
    if (!isNaN(parsed) && parsed > 0) {
      setAmountCents(Math.round(parsed * divisor));
    } else {
      setAmountCents(0);
    }
  }

  function handleContinueToDetails() {
    if (amountCents <= 0) return;
    if (campaign.min_donation_cents && amountCents < campaign.min_donation_cents) {
      setErrorMessage(
        `El monto minimo es ${formatCurrency(campaign.min_donation_cents, selectedCurrency)}`
      );
      return;
    }
    if (campaign.max_donation_cents && amountCents > campaign.max_donation_cents) {
      setErrorMessage(
        `El monto maximo es ${formatCurrency(campaign.max_donation_cents, selectedCurrency)}`
      );
      return;
    }
    setErrorMessage("");
    setStep("details");
  }

  /**
   * Resolve donor ID — creates a donor record if the user is not anonymous.
   * Returns null for anonymous donations.
   */
  async function resolveDonorId(): Promise<string | null> {
    if (isAnonymous || !fullName || !email) return null;
    const donor = await createDonor({
      full_name: fullName,
      email,
      currency_preference: selectedCurrency,
      gdpr_consent_at: gdprConsent ? new Date().toISOString() : undefined,
    });
    return donor.id;
  }

  /**
   * Handle "details" step continue.
   *
   * For transfer payments: creates donor + donation record and calls onSuccess.
   * For stripe payments: creates donor + donation + PaymentIntent, then shows
   *   the Stripe Elements payment step.
   */
  async function handleDetailsSubmit() {
    setStep("submitting");
    setErrorMessage("");

    try {
      const donorId = await resolveDonorId();

      const donation = await createDonation({
        donor_id: donorId,
        campaign_id: campaign.id,
        amount_cents: amountCents,
        currency: selectedCurrency,
        payment_method: paymentMethod,
      });

      if (paymentMethod === "transfer") {
        // Bank transfer: record created, donor will follow up manually
        onSuccess(donation.id);
        return;
      }

      // Stripe path: fetch client_secret and move to payment step
      const intent = await createStripeIntent(donation.id);
      setPendingDonationId(donation.id);
      setStripeClientSecret(intent.client_secret);
      setStep("payment");
    } catch (err) {
      setStep("error");
      setErrorMessage(
        err instanceof Error ? err.message : "Error al procesar la donacion"
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Render — step machine
  // ---------------------------------------------------------------------------

  if (step === "amount") {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Elegir monto</h3>

        <div className="flex gap-2 mb-4">
          {(["EUR", "USD", "PYG"] as CurrencyCode[]).map((cur) => (
            <button
              key={cur}
              onClick={() => { setSelectedCurrency(cur); setAmountCents(0); setCustomAmount(""); }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedCurrency === cur
                  ? "bg-primary-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {cur}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          {suggestedAmounts.map((cents) => (
            <button
              key={cents}
              onClick={() => handleAmountSelect(cents)}
              className={`py-3 rounded-lg text-sm font-medium transition-colors ${
                amountCents === cents && !customAmount
                  ? "bg-primary-600 text-white"
                  : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
              }`}
            >
              {formatCurrency(cents, selectedCurrency)}
            </button>
          ))}
        </div>

        <div className="mb-4">
          <label className="block text-sm text-gray-600 mb-1">
            Otro monto ({selectedCurrency})
          </label>
          <input
            type="number"
            min="0"
            step={selectedCurrency === "PYG" ? "1000" : "0.01"}
            value={customAmount}
            onChange={(e) => handleCustomAmountChange(e.target.value)}
            placeholder={selectedCurrency === "PYG" ? "50000" : "10.00"}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-gray-600 mb-2">Metodo de pago</label>
          <div className="flex gap-3">
            {selectedCurrency !== "PYG" && (
              <button
                onClick={() => setPaymentMethod("stripe")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  paymentMethod === "stripe"
                    ? "bg-primary-600 text-white"
                    : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
                }`}
              >
                Tarjeta / SEPA
              </button>
            )}
            <button
              onClick={() => setPaymentMethod("transfer")}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                paymentMethod === "transfer"
                  ? "bg-primary-600 text-white"
                  : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
              }`}
            >
              Transferencia
            </button>
          </div>
        </div>

        {errorMessage && <p className="text-sm text-red-600 mb-3">{errorMessage}</p>}

        <button
          onClick={handleContinueToDetails}
          disabled={amountCents <= 0}
          className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continuar
        </button>
      </div>
    );
  }

  if (step === "details" || step === "error") {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Tus datos</h3>
        <p className="text-sm text-gray-500 mb-4">
          Donacion: {formatCurrency(amountCents, selectedCurrency)} via{" "}
          {paymentMethod === "stripe" ? "tarjeta/SEPA" : "transferencia"}
        </p>

        <label className="flex items-center gap-2 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={isAnonymous}
            onChange={(e) => setIsAnonymous(e.target.checked)}
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700">Donar de forma anonima</span>
        </label>

        {!isAnonymous && (
          <div className="space-y-3 mb-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Nombre completo</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Tu nombre"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="tu@email.com"
              />
            </div>
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={gdprConsent}
                onChange={(e) => setGdprConsent(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mt-0.5"
              />
              <span className="text-xs text-gray-500">
                Acepto que mis datos sean procesados para gestionar mi donacion.
                Puedo solicitar la eliminacion de mis datos en cualquier momento.
              </span>
            </label>
          </div>
        )}

        {errorMessage && <p className="text-sm text-red-600 mb-3">{errorMessage}</p>}

        <div className="flex gap-3">
          <button
            onClick={() => { setStep("amount"); setErrorMessage(""); }}
            className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Volver
          </button>
          <button
            onClick={handleDetailsSubmit}
            disabled={!isAnonymous && (!fullName || !email)}
            className="flex-1 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {paymentMethod === "stripe"
              ? "Ir a pago"
              : `Donar ${formatCurrency(amountCents, selectedCurrency)}`}
          </button>
        </div>
      </div>
    );
  }

  if (step === "payment" && stripeClientSecret) {
    // Stripe Elements — card / SEPA / iDEAL / etc.
    const returnUrl =
      typeof window !== "undefined"
        ? `${window.location.origin}/donate/confirmation?donation_id=${pendingDonationId}`
        : `/donate/confirmation?donation_id=${pendingDonationId}`;

    return (
      <StripePaymentStep
        clientSecret={stripeClientSecret}
        amountLabel={formatCurrency(amountCents, selectedCurrency)}
        returnUrl={returnUrl}
        onBack={() => { setStep("details"); setErrorMessage(""); }}
        onError={(msg) => { setStep("error"); setErrorMessage(msg); }}
        onSuccess={() => onSuccess(pendingDonationId)}
      />
    );
  }

  // "submitting" and fallback (payment step before client secret is ready)
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
      <div className="animate-spin w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full mx-auto mb-4" />
      <p className="text-gray-600">Procesando tu donacion...</p>
    </div>
  );
}
