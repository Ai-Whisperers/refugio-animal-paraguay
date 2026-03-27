"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle, AlertCircle } from "lucide-react";

function DonateSuccessContent() {
  const searchParams = useSearchParams();
  const donationId = searchParams.get("donation_id");
  const status = searchParams.get("status");

  // Stripe also appends payment_intent and redirect_status on redirect
  const redirectStatus = searchParams.get("redirect_status");

  const [displayStatus, setDisplayStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    // redirect_status=succeeded means Stripe confirmed the payment
    if (redirectStatus === "succeeded" || status === "success") {
      setDisplayStatus("success");
    } else if (redirectStatus === "requires_payment_method" || redirectStatus === "failed") {
      setDisplayStatus("error");
    } else if (donationId) {
      // Fallback: if we have a donation_id and no explicit failure, assume success
      setDisplayStatus("success");
    } else {
      setDisplayStatus("error");
    }
  }, [redirectStatus, status, donationId]);

  if (displayStatus === "loading") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-10 h-10 border-4 border-[#E8622A]/20 border-t-[#E8622A] rounded-full" />
      </div>
    );
  }

  if (displayStatus === "error") {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-4">
            <AlertCircle className="h-8 w-8 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            El pago no se completo
          </h1>
          <p className="text-gray-500 mb-6">
            Hubo un problema al procesar tu donacion. El pago NO fue cobrado.
            Por favor intenta de nuevo.
          </p>
          <Link
            href="/donate"
            className="inline-block px-6 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
          >
            Intentar de nuevo
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-50 mb-4">
          <CheckCircle className="h-8 w-8 text-green-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Gracias por tu donacion
        </h1>
        <p className="text-gray-500 mb-6">
          Tu contribucion ayuda a los animales del refugio.
          {donationId && (
            <span className="block mt-2 text-xs text-gray-400">
              Referencia: {donationId.slice(0, 8).toUpperCase()}
            </span>
          )}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/animals"
            className="px-6 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
          >
            Ver animales
          </Link>
          <Link
            href="/donate"
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Donar de nuevo
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function DonateSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-10 h-10 border-4 border-[#E8622A]/20 border-t-[#E8622A] rounded-full" />
      </div>
    }>
      <DonateSuccessContent />
    </Suspense>
  );
}
