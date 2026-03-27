"use client";

/**
 * MonthlyGivingFlow
 *
 * Multi-step form for setting up a recurring donation (Stripe subscription).
 *
 * Steps:
 *   1. Amount   - pick currency, interval, and amount (presets or custom)
 *   2. Details  - donor name, email, GDPR consent
 *   3. Payment  - Stripe CardElement to collect payment method
 *   4. Success  - confirmation message
 *
 * Flow:
 *   1. Collect amount + donor info
 *   2. POST /donors to create/find donor -> donor_id
 *   3. stripe.createPaymentMethod with card details -> payment_method_id
 *   4. POST /subscriptions with { donor_id, amount_cents, currency, interval, payment_method_id }
 *   5. Show success
 */

import { useState } from "react";
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import type { StripeCardElementOptions } from "@stripe/stripe-js";
import { stripePromise } from "@/lib/stripe";
import { createDonor, createSubscription } from "@/lib/public-api";
import { MONTHLY_GIVING } from "@/lib/strings";
import type { CurrencyCode, SubscriptionInterval } from "@/types/api";
import { CheckCircle, AlertTriangle, Loader2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type FlowStep = "amount" | "details" | "payment" | "processing" | "success" | "error";

interface FormData {
  currency: CurrencyCode;
  interval: SubscriptionInterval;
  amountCents: number;
  fullName: string;
  email: string;
  gdprConsent: boolean;
}

// ---------------------------------------------------------------------------
// Card element styles
// ---------------------------------------------------------------------------

const CARD_ELEMENT_OPTIONS: StripeCardElementOptions = {
  style: {
    base: {
      fontSize: "16px",
      color: "#111827",
      "::placeholder": {
        color: "#9ca3af",
      },
    },
    invalid: {
      color: "#ef4444",
    },
  },
};

// ---------------------------------------------------------------------------
// Step indicator
// ---------------------------------------------------------------------------

const STEPS = [
  MONTHLY_GIVING.stepAmount,
  MONTHLY_GIVING.stepDetails,
  MONTHLY_GIVING.stepPayment,
  MONTHLY_GIVING.stepConfirmation,
] as const;

function StepIndicator({ currentIndex }: { currentIndex: number }) {
  return (
    <div className="flex items-center justify-between mb-8">
      {STEPS.map((label, i) => (
        <div key={label} className="flex items-center">
          <div
            className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
              i < currentIndex
                ? "bg-primary-600 text-white"
                : i === currentIndex
                  ? "bg-primary-100 text-primary-700 ring-2 ring-primary-600"
                  : "bg-gray-100 text-gray-400"
            }`}
          >
            {i + 1}
          </div>
          <span
            className={`ml-2 text-xs hidden sm:inline ${
              i <= currentIndex ? "text-gray-900" : "text-gray-400"
            }`}
          >
            {label}
          </span>
          {i < STEPS.length - 1 && (
            <div
              className={`w-8 sm:w-12 h-0.5 mx-2 ${
                i < currentIndex ? "bg-primary-600" : "bg-gray-200"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Payment step (inside Elements provider)
// ---------------------------------------------------------------------------

interface PaymentStepProps {
  formData: FormData;
  onSuccess: () => void;
  onError: (message: string) => void;
  onBack: () => void;
}

function PaymentStep({ formData, onSuccess, onError, onBack }: PaymentStepProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const divisor = formData.currency === "PYG" ? 1 : 100;
  const displayAmount = (formData.amountCents / divisor).toLocaleString("es-PY");
  const currencySymbol = formData.currency === "EUR" ? "\u20AC" : "Gs.";
  const intervalLabel =
    formData.interval === "month"
      ? MONTHLY_GIVING.intervalMonth.toLowerCase()
      : MONTHLY_GIVING.intervalYear?.toLowerCase() ?? "anual";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;

    setIsSubmitting(true);

    try {
      // 1. Create payment method from card
      const cardElement = elements.getElement(CardElement);
      if (!cardElement) {
        onError("No se pudo cargar el formulario de tarjeta.");
        return;
      }

      const { error: pmError, paymentMethod } = await stripe.createPaymentMethod({
        type: "card",
        card: cardElement,
        billing_details: {
          name: formData.fullName,
          email: formData.email,
        },
      });

      if (pmError || !paymentMethod) {
        onError(pmError?.message ?? "Error al procesar la tarjeta.");
        setIsSubmitting(false);
        return;
      }

      // 2. Create donor
      const donor = await createDonor({
        full_name: formData.fullName,
        email: formData.email,
        currency_preference: formData.currency,
        gdpr_consent_at: new Date().toISOString(),
      });

      // 3. Create subscription
      await createSubscription({
        donor_id: donor.id,
        amount_cents: formData.amountCents,
        currency: formData.currency,
        interval: formData.interval,
        payment_method_id: paymentMethod.id,
      });

      onSuccess();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Error inesperado. Intenta de nuevo.";
      onError(message);
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Order summary */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <p className="text-sm text-gray-600">
          Donacion {intervalLabel}:{" "}
          <span className="font-semibold text-gray-900">
            {currencySymbol} {displayAmount}
          </span>
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {formData.fullName} &middot; {formData.email}
        </p>
      </div>

      {/* Card element */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Datos de la tarjeta
        </label>
        <div className="border border-gray-300 rounded-lg p-3 bg-white">
          <CardElement options={CARD_ELEMENT_OPTIONS} />
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Tu tarjeta sera cargada {intervalLabel}mente. Puedes cancelar en cualquier momento.
        </p>
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {MONTHLY_GIVING.backButton}
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !stripe}
          className="flex-1 py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {MONTHLY_GIVING.processing}
            </>
          ) : (
            MONTHLY_GIVING.submitButton
          )}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main flow component
// ---------------------------------------------------------------------------

export default function MonthlyGivingFlow() {
  const [step, setStep] = useState<FlowStep>("amount");
  const [errorMessage, setErrorMessage] = useState("");
  const [formData, setFormData] = useState<FormData>({
    currency: "EUR",
    interval: "month",
    amountCents: 0,
    fullName: "",
    email: "",
    gdprConsent: false,
  });

  const [customAmount, setCustomAmount] = useState("");

  const isPYG = formData.currency === "PYG";
  const divisor = isPYG ? 1 : 100;
  const suggestedAmounts = isPYG
    ? MONTHLY_GIVING.suggestedAmountsPYG
    : MONTHLY_GIVING.suggestedAmountsEUR;

  function stepIndex(): number {
    switch (step) {
      case "amount":
        return 0;
      case "details":
        return 1;
      case "payment":
      case "processing":
        return 2;
      case "success":
      case "error":
        return 3;
    }
  }

  // --- Step 1: Amount ---
  function renderAmountStep() {
    return (
      <div className="space-y-6">
        {/* Currency selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {MONTHLY_GIVING.currencyLabel}
          </label>
          <div className="flex gap-2">
            {(["EUR", "PYG"] as CurrencyCode[]).map((cur) => (
              <button
                key={cur}
                type="button"
                onClick={() => {
                  setFormData((d) => ({ ...d, currency: cur, amountCents: 0 }));
                  setCustomAmount("");
                }}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  formData.currency === cur
                    ? "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {cur === "EUR" ? "\u20AC EUR" : "Gs. PYG"}
              </button>
            ))}
          </div>
        </div>

        {/* Interval selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {MONTHLY_GIVING.intervalLabel}
          </label>
          <div className="flex gap-2">
            {(["month", "year"] as SubscriptionInterval[]).map((int) => (
              <button
                key={int}
                type="button"
                onClick={() => setFormData((d) => ({ ...d, interval: int }))}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  formData.interval === int
                    ? "bg-primary-600 text-white border-primary-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {int === "month" ? MONTHLY_GIVING.intervalMonth : MONTHLY_GIVING.intervalYear}
              </button>
            ))}
          </div>
        </div>

        {/* Amount presets */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {MONTHLY_GIVING.chooseAmount}
          </label>
          <div className="grid grid-cols-2 gap-3">
            {suggestedAmounts.map((cents) => {
              const display = (cents / divisor).toLocaleString("es-PY");
              const symbol = isPYG ? "Gs." : "\u20AC";
              return (
                <button
                  key={cents}
                  type="button"
                  onClick={() => {
                    setFormData((d) => ({ ...d, amountCents: cents }));
                    setCustomAmount("");
                  }}
                  className={`py-3 px-4 rounded-lg text-sm font-medium border transition-colors ${
                    formData.amountCents === cents && customAmount === ""
                      ? "bg-primary-600 text-white border-primary-600"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  {symbol} {display}
                </button>
              );
            })}
          </div>
        </div>

        {/* Custom amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {MONTHLY_GIVING.customAmount}
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
              {isPYG ? "Gs." : "\u20AC"}
            </span>
            <input
              type="number"
              min="1"
              step={isPYG ? "1000" : "0.01"}
              value={customAmount}
              onChange={(e) => {
                const val = e.target.value;
                setCustomAmount(val);
                const parsed = parseFloat(val);
                if (!isNaN(parsed) && parsed > 0) {
                  setFormData((d) => ({
                    ...d,
                    amountCents: Math.round(parsed * divisor),
                  }));
                } else {
                  setFormData((d) => ({ ...d, amountCents: 0 }));
                }
              }}
              placeholder="0"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        <button
          type="button"
          disabled={formData.amountCents <= 0}
          onClick={() => setStep("details")}
          className="w-full py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {MONTHLY_GIVING.continueButton}
        </button>
      </div>
    );
  }

  // --- Step 2: Details ---
  function renderDetailsStep() {
    const isValid =
      formData.fullName.trim().length >= 2 &&
      formData.email.includes("@") &&
      formData.gdprConsent;

    return (
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {MONTHLY_GIVING.donorName}
          </label>
          <input
            type="text"
            required
            value={formData.fullName}
            onChange={(e) =>
              setFormData((d) => ({ ...d, fullName: e.target.value }))
            }
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {MONTHLY_GIVING.donorEmail}
          </label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) =>
              setFormData((d) => ({ ...d, email: e.target.value }))
            }
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.gdprConsent}
            onChange={(e) =>
              setFormData((d) => ({ ...d, gdprConsent: e.target.checked }))
            }
            className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-xs text-gray-600 leading-relaxed">
            {MONTHLY_GIVING.gdprConsent}
          </span>
        </label>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setStep("amount")}
            className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            {MONTHLY_GIVING.backButton}
          </button>
          <button
            type="button"
            disabled={!isValid}
            onClick={() => setStep("payment")}
            className="flex-1 py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {MONTHLY_GIVING.continueButton}
          </button>
        </div>
      </div>
    );
  }

  // --- Step 3: Payment (Stripe Elements) ---
  function renderPaymentStep() {
    return (
      <Elements stripe={stripePromise}>
        <PaymentStep
          formData={formData}
          onSuccess={() => setStep("success")}
          onError={(msg) => {
            setErrorMessage(msg);
            setStep("error");
          }}
          onBack={() => setStep("details")}
        />
      </Elements>
    );
  }

  // --- Step 4: Success ---
  function renderSuccessStep() {
    return (
      <div className="text-center py-8">
        <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
          {MONTHLY_GIVING.successTitle}
        </h2>
        <p className="text-gray-600 text-sm mb-6">
          {MONTHLY_GIVING.successMessage}
        </p>
        <a
          href="/"
          className="inline-block bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          {MONTHLY_GIVING.successBackHome}
        </a>
      </div>
    );
  }

  // --- Error step ---
  function renderErrorStep() {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
          {MONTHLY_GIVING.errorTitle}
        </h2>
        <p className="text-red-600 text-sm mb-6">{errorMessage}</p>
        <button
          type="button"
          onClick={() => setStep("payment")}
          className="inline-block bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          {MONTHLY_GIVING.errorRetry}
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
      <StepIndicator currentIndex={stepIndex()} />
      {step === "amount" && renderAmountStep()}
      {step === "details" && renderDetailsStep()}
      {step === "payment" && renderPaymentStep()}
      {step === "processing" && (
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 text-primary-600 animate-spin mx-auto mb-3" />
          <p className="text-gray-600 text-sm">{MONTHLY_GIVING.processing}</p>
        </div>
      )}
      {step === "success" && renderSuccessStep()}
      {step === "error" && renderErrorStep()}
    </div>
  );
}
