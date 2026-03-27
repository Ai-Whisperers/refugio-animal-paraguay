"use client";

/**
 * /donate/confirmation
 *
 * Landing page for Stripe 3DS redirect flows.
 *
 * When Stripe requires 3D Secure authentication it redirects the browser to
 * the return_url we supply to confirmPayment(). That URL includes
 * `payment_intent_client_secret` and `payment_intent` as search params.
 *
 * This page reads those params, confirms the final status of the intent, and
 * shows either a success or failure message.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { loadStripe } from "@stripe/stripe-js";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";

type PageStatus = "loading" | "success" | "failed" | "unknown";

export default function DonationConfirmationPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<PageStatus>("loading");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const donationId = searchParams.get("donation_id") ?? "";
  const clientSecret = searchParams.get("payment_intent_client_secret");

  useEffect(() => {
    if (!clientSecret) {
      // Direct navigation without Stripe params — treat as success if donation_id present
      setStatus(donationId ? "success" : "unknown");
      return;
    }

    const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ?? "";
    if (!publishableKey) {
      setStatus("unknown");
      return;
    }

    loadStripe(publishableKey).then(async (stripe) => {
      if (!stripe) { setStatus("unknown"); return; }

      const { paymentIntent, error } = await stripe.retrievePaymentIntent(clientSecret);
      if (error) {
        setErrorMessage(error.message ?? "Error al verificar el pago.");
        setStatus("failed");
        return;
      }

      switch (paymentIntent?.status) {
        case "succeeded":
        case "processing":
          setStatus("success");
          break;
        case "requires_payment_method":
          setErrorMessage("El pago fue rechazado. Por favor, intenta con otra tarjeta.");
          setStatus("failed");
          break;
        default:
          setErrorMessage(`Estado del pago: ${paymentIntent?.status ?? "desconocido"}.`);
          setStatus("failed");
      }
    });
  }, [clientSecret, donationId]);

  if (status === "loading") {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <Loader2 className="h-10 w-10 text-primary-600 animate-spin mx-auto mb-4" />
        <p className="text-gray-600">Verificando pago...</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-2xl p-8 mb-6">
          <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            ¡Muchas gracias!
          </h1>
          <p className="text-gray-600">
            Tu donacion fue procesada exitosamente. Cada contribucion hace una diferencia
            para los animales en nuestro refugio.
          </p>
        </div>
        <Link
          href="/donate"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Ver mas campanas
        </Link>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="bg-red-50 rounded-2xl p-8 mb-6">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            Pago no completado
          </h1>
          {errorMessage && (
            <p className="text-gray-600 mb-4">{errorMessage}</p>
          )}
        </div>
        <Link
          href="/donate"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Volver a las campanas
        </Link>
      </div>
    );
  }

  // "unknown" — generic fallback
  return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <p className="text-gray-500 mb-4">No se pudo determinar el estado del pago.</p>
      <Link
        href="/donate"
        className="text-primary-600 hover:text-primary-700 font-medium"
      >
        Volver a las campanas
      </Link>
    </div>
  );
}
