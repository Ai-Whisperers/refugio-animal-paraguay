"use client";

import { useState } from "react";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import type { Stripe } from "@stripe/stripe-js";
import type { CampaignPublic, CurrencyCode } from "@/types/api";
import { createDonation, createDonor, createStripeIntent } from "@/lib/public-api";
import { formatCurrency, getSuggestedAmounts } from "@/lib/campaign-utils";
import StripePaymentForm from "@/components/StripePaymentForm";

// Stripe is loaded lazily — returns null when publishable key is missing,
// which gracefully disables the PaymentElement (transfer-only mode).
const stripePromise: Promise<Stripe | null> = (() => {
  const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
  return key ? loadStripe(key) : Promise.resolve(null);
})();

interface DonationFormProps {
  campaign: CampaignPublic;
  onSuccess: (donationId: string) => void;
}

type FormStep = "amount" | "details" | "initiating" | "payment" | "submitting" | "error";

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

  // Set when the Stripe PaymentIntent is created
  const [donationId, setDonationId] = useState<string | null>(null);
  const [stripeClientSecret, setStripeClientSecret] = useState<string | null>(null);

  const suggestedAmounts = getSuggestedAmounts(selectedCurrency);
  const divisor = selectedCurrency === "PYG" ? 1 : 100;

  // Stripe Elements is only available for EUR/USD (not PYG)
  const stripeAvailable =
    selectedCurrency !== "PYG" && !!process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;

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

  async function handleSubmitDetails() {
    setErrorMessage("");

    if (paymentMethod === "stripe" && stripeAvailable) {
      // Stripe flow: create donation + PaymentIntent, then show Elements
      setStep("initiating");
      try {
        let donorIdValue: string | null = null;
        if (!isAnonymous && fullName && email) {
          const donor = await createDonor({
            full_name: fullName,
            email,
            currency_preference: selectedCurrency,
            gdpr_consent_at: gdprConsent ? new Date().toISOString() : undefined,
          });
          donorIdValue = donor.id;
        }

        const donation = await createDonation({
          donor_id: donorIdValue,
          campaign_id: campaign.id,
          amount_cents: amountCents,
          currency: selectedCurrency,
          payment_method: "stripe",
        });

        const intent = await createStripeIntent(donation.id);
        setDonationId(donation.id);
        setStripeClientSecret(intent.client_secret);
        setStep("payment");
      } catch (err) {
        setStep("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Error al iniciar el pago"
        );
      }
    } else {
      // Transfer flow: create donation record directly and complete
      setStep("submitting");
      try {
        let donorIdValue: string | null = null;
        if (!isAnonymous && fullName && email) {
          const donor = await createDonor({
            full_name: fullName,
            email,
            currency_preference: selectedCurrency,
            gdpr_consent_at: gdprConsent ? new Date().toISOString() : undefined,
          });
          donorIdValue = donor.id;
        }

        const donation = await createDonation({
          donor_id: donorIdValue,
          campaign_id: campaign.id,
          amount_cents: amountCents,
          currency: selectedCurrency,
          payment_method: "transfer",
        });

        onSuccess(donation.id);
      } catch (err) {
        setStep("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Error al registrar la donacion"
        );
      }
    }
  }

  // --- Step: amount selection ---

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
                  ? "bg-[#E8622A] text-white"
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
                  ? "bg-[#E8622A] text-white"
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A]"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-gray-600 mb-2">Metodo de pago</label>
          <div className="flex gap-3">
            {stripeAvailable && (
              <button
                onClick={() => setPaymentMethod("stripe")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                  paymentMethod === "stripe"
                    ? "bg-[#E8622A] text-white"
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
                  ? "bg-[#E8622A] text-white"
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
          className="w-full py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continuar
        </button>
      </div>
    );
  }

  // --- Step: donor details ---

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
            className="rounded border-gray-300 text-[#E8622A] focus:ring-[#E8622A]/30"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A]"
                placeholder="Tu nombre"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A]"
                placeholder="tu@email.com"
              />
            </div>
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={gdprConsent}
                onChange={(e) => setGdprConsent(e.target.checked)}
                className="rounded border-gray-300 text-[#E8622A] focus:ring-[#E8622A]/30 mt-0.5"
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
            onClick={handleSubmitDetails}
            disabled={!isAnonymous && (!fullName || !email)}
            className="flex-1 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {paymentMethod === "stripe" ? "Ir a pago" : `Donar ${formatCurrency(amountCents, selectedCurrency)}`}
          </button>
        </div>
      </div>
    );
  }

  // --- Step: initiating Stripe payment intent ---

  if (step === "initiating") {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#E8622A]/20 border-t-[#E8622A] rounded-full mx-auto mb-4" />
        <p className="text-gray-600">Preparando el formulario de pago...</p>
      </div>
    );
  }

  // --- Step: Stripe PaymentElement ---

  if (step === "payment" && stripeClientSecret && donationId) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Datos de pago</h3>
        <Elements
          stripe={stripePromise}
          options={{
            clientSecret: stripeClientSecret,
            appearance: {
              theme: "stripe",
              variables: {
                colorPrimary: "#E8622A",
                borderRadius: "8px",
              },
            },
          }}
        >
          <StripePaymentForm
            donationId={donationId}
            amountCents={amountCents}
            currency={selectedCurrency}
            returnUrl={
              typeof window !== "undefined"
                ? `${window.location.origin}/donate/success`
                : "/donate/success"
            }
            onBack={() => { setStep("details"); setErrorMessage(""); }}
            onError={(msg) => {
              setErrorMessage(msg);
              setStep("payment");
            }}
          />
        </Elements>
        {errorMessage && (
          <p className="text-sm text-red-600 mt-3">{errorMessage}</p>
        )}
      </div>
    );
  }

  // --- Step: processing (transfer) ---

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
      <div className="animate-spin w-8 h-8 border-4 border-[#E8622A]/20 border-t-[#E8622A] rounded-full mx-auto mb-4" />
      <p className="text-gray-600">Procesando tu donacion...</p>
    </div>
  );
}
