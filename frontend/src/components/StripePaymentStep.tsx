"use client";

/**
 * StripePaymentStep
 *
 * Renders a Stripe PaymentElement inside an Elements provider and handles
 * payment confirmation. Intended for use as a step inside DonationForm.
 *
 * Props:
 *   clientSecret  — PaymentIntent client_secret from the backend
 *   amountLabel   — Human-readable amount string for the submit button
 *   returnUrl     — Absolute URL Stripe redirects to on 3DS completion
 *   onBack        — Called when the user navigates back to the details step
 *   onError       — Called with an error message when payment fails
 *   onSuccess     — Called when the payment is confirmed successfully
 */

import { useState } from "react";
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import type { StripePaymentElementOptions } from "@stripe/stripe-js";
import { stripePromise } from "@/lib/stripe";

// ---------------------------------------------------------------------------
// Inner form — rendered inside Elements provider (has access to Stripe hooks)
// ---------------------------------------------------------------------------

interface PaymentFormProps {
  amountLabel: string;
  returnUrl: string;
  onBack: () => void;
  onError: (message: string) => void;
  onSuccess: () => void;
}

const PAYMENT_ELEMENT_OPTIONS: StripePaymentElementOptions = {
  layout: "tabs",
};

function PaymentForm({
  amountLabel,
  returnUrl,
  onBack,
  onError,
  onSuccess,
}: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleConfirm() {
    if (!stripe || !elements) return;

    setIsSubmitting(true);

    const { error, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: returnUrl },
      // Avoid redirect for card payments that don't require 3DS
      redirect: "if_required",
    });

    if (error) {
      // error.message is localised by Stripe
      onError(error.message ?? "Error al procesar el pago. Intente de nuevo.");
      setIsSubmitting(false);
      return;
    }

    // Payment succeeded without redirect (redirect: "if_required")
    if (
      paymentIntent?.status === "succeeded" ||
      paymentIntent?.status === "processing"
    ) {
      onSuccess();
    } else {
      onError("El pago no fue completado. Intente de nuevo.");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <PaymentElement options={PAYMENT_ELEMENT_OPTIONS} />

      {isSubmitting && (
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500 py-2">
          <div className="animate-spin w-4 h-4 border-2 border-primary-200 border-t-primary-600 rounded-full" />
          Procesando pago...
        </div>
      )}

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
        >
          Volver
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={!stripe || !elements || isSubmitting}
          className="flex-1 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Procesando..." : `Pagar ${amountLabel}`}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Public component — owns the Elements provider
// ---------------------------------------------------------------------------

interface StripePaymentStepProps {
  clientSecret: string;
  amountLabel: string;
  returnUrl: string;
  onBack: () => void;
  onError: (message: string) => void;
  onSuccess: () => void;
}

export default function StripePaymentStep({
  clientSecret,
  amountLabel,
  returnUrl,
  onBack,
  onError,
  onSuccess,
}: StripePaymentStepProps) {
  return (
    <Elements
      stripe={stripePromise}
      options={{
        clientSecret,
        appearance: {
          theme: "stripe",
          variables: {
            colorPrimary: "#d97706", // primary-600 amber to match brand
            borderRadius: "8px",
          },
        },
      }}
    >
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Datos de pago
        </h3>
        <PaymentForm
          amountLabel={amountLabel}
          returnUrl={returnUrl}
          onBack={onBack}
          onError={onError}
          onSuccess={onSuccess}
        />
      </div>
    </Elements>
  );
}
