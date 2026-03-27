"use client";

import { useState } from "react";
import { useStripe, useElements, PaymentElement } from "@stripe/react-stripe-js";
import { formatCurrency } from "@/lib/campaign-utils";
import type { CurrencyCode } from "@/types/api";

interface StripePaymentFormProps {
  donationId: string;
  amountCents: number;
  currency: CurrencyCode;
  returnUrl: string;
  onBack: () => void;
  onError: (message: string) => void;
}

/**
 * Inner Stripe form — must be rendered inside an Elements provider.
 * Calls stripe.confirmPayment() and redirects to returnUrl on success.
 */
export default function StripePaymentForm({
  donationId,
  amountCents,
  currency,
  returnUrl,
  onBack,
  onError,
}: StripePaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;

    setIsSubmitting(true);

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${returnUrl}?donation_id=${donationId}&status=success`,
      },
    });

    // confirmPayment only reaches here on error — success redirects the page
    if (error) {
      onError(
        error.message ??
          "Error al procesar el pago. Intenta de nuevo o elige otro metodo."
      );
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-gray-500 mb-4">
        Monto: {formatCurrency(amountCents, currency)} via tarjeta / SEPA
      </p>

      <PaymentElement
        options={{
          layout: "tabs",
        }}
      />

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onBack}
          disabled={isSubmitting}
          className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Volver
        </button>
        <button
          type="submit"
          disabled={!stripe || !elements || isSubmitting}
          className="flex-1 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Procesando..." : `Pagar ${formatCurrency(amountCents, currency)}`}
        </button>
      </div>
    </form>
  );
}
