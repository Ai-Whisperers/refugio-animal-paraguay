"use client";

/**
 * SepaSetupFlow
 *
 * Multi-step form for saving a donor's IBAN as a SEPA Direct Debit mandate.
 *
 * Step 1 – Donor details: email + full name (or donor_id if known)
 * Step 2 – SEPA form: IbanElement + mandate acceptance checkbox
 * Step 3 – Confirmation: success/failure feedback
 *
 * Flow:
 *   1. POST /api/donors (or look up existing) to get donor_id
 *   2. POST /donations/sepa/setup-intent → { client_secret, stripe_customer_id }
 *   3. stripe.confirmSepaDebitSetup(clientSecret, { payment_method: { sepa_debit, billing_details } })
 *   4. Show success or error
 */

import { useState } from "react";
import {
  Elements,
  IbanElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import type { StripeIbanElementOptions } from "@stripe/stripe-js";
import { stripePromise } from "@/lib/stripe";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DonorStep {
  fullName: string;
  email: string;
}

interface SetupIntentData {
  clientSecret: string;
  stripeCustomerId: string;
  donorId: string;
}

// ---------------------------------------------------------------------------
// IBAN element styles
// ---------------------------------------------------------------------------

const IBAN_ELEMENT_OPTIONS: StripeIbanElementOptions = {
  supportedCountries: ["SEPA"],
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
// Step 2: SEPA IBAN form (rendered inside Elements provider)
// ---------------------------------------------------------------------------

interface SepaFormProps {
  clientSecret: string;
  donorName: string;
  donorEmail: string;
  onSuccess: () => void;
  onError: (message: string) => void;
  onBack: () => void;
}

function SepaIbanForm({
  clientSecret,
  donorName,
  donorEmail,
  onSuccess,
  onError,
  onBack,
}: SepaFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [mandateAccepted, setMandateAccepted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!stripe || !elements || !mandateAccepted) return;

    setIsSubmitting(true);

    const ibanElement = elements.getElement(IbanElement);
    if (!ibanElement) {
      onError("No se pudo cargar el formulario IBAN.");
      setIsSubmitting(false);
      return;
    }

    const { error } = await stripe.confirmSepaDebitSetup(clientSecret, {
      payment_method: {
        sepa_debit: ibanElement,
        billing_details: {
          name: donorName,
          email: donorEmail,
        },
      },
    });

    setIsSubmitting(false);

    if (error) {
      onError(error.message ?? "Error al configurar el débito SEPA.");
    } else {
      onSuccess();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          IBAN
        </label>
        <div className="border border-gray-300 rounded-lg px-3 py-3 focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-primary-500 bg-white">
          <IbanElement options={IBAN_ELEMENT_OPTIONS} />
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Ingresa el IBAN de tu cuenta bancaria europea (ej. NL02ABNA0123456789)
        </p>
      </div>

      {/* Mandate authorization text (legally required for SEPA) */}
      <div className="bg-blue-50 rounded-lg p-4 text-sm text-blue-800 border border-blue-200">
        <p className="font-medium mb-2">Autorización de Adeudo Directo SEPA</p>
        <p className="mb-2">
          Al confirmar esta autorización, permites a{" "}
          <strong>Refugio Animal Paraguay</strong> y a Stripe, su proveedor de
          pagos, enviar instrucciones a tu banco para cargar en tu cuenta los
          importes que hayas autorizado.
        </p>
        <p>
          Tienes derecho a obtener el reembolso de tu banco según los términos y
          condiciones del contrato que tienes con él. El reembolso deberá
          solicitarse en un plazo de 8 semanas desde la fecha de cargo.
        </p>
      </div>

      <label className="flex items-start gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={mandateAccepted}
          onChange={(e) => setMandateAccepted(e.target.checked)}
          className="mt-0.5 h-4 w-4 text-primary-600 border-gray-300 rounded"
        />
        <span className="text-sm text-gray-700">
          Acepto la autorización de Adeudo Directo SEPA indicada arriba y
          autorizo los cargos futuros según lo acordado.
        </span>
      </label>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 py-2.5 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors text-sm"
        >
          Atrás
        </button>
        <button
          type="submit"
          disabled={!stripe || !mandateAccepted || isSubmitting}
          className="flex-1 py-2.5 px-4 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
        >
          {isSubmitting ? "Guardando..." : "Guardar cuenta bancaria"}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main flow component (manages steps)
// ---------------------------------------------------------------------------

type Step = "donor-details" | "iban" | "success" | "error";

export default function SepaSetupFlow() {
  const [step, setStep] = useState<Step>("donor-details");
  const [donorData, setDonorData] = useState<DonorStep>({
    fullName: "",
    email: "",
  });
  const [setupIntentData, setSetupIntentData] =
    useState<SetupIntentData | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Step 1: collect donor info, call backend to create setup intent
  async function handleDonorSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage("");

    try {
      // Create or look up donor
      const donorResp = await fetch(`${API_BASE}/donors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: donorData.fullName,
          email: donorData.email,
          currency_preference: "EUR",
        }),
      });

      let donorId: string;

      if (donorResp.status === 201) {
        const donor = await donorResp.json();
        donorId = donor.id;
      } else if (donorResp.status === 409) {
        // Donor already exists — look them up by email
        const searchResp = await fetch(
          `${API_BASE}/donors?email=${encodeURIComponent(donorData.email)}`
        );
        if (!searchResp.ok) {
          throw new Error("No se pudo encontrar el donante existente.");
        }
        const donors = await searchResp.json();
        if (!donors.items || donors.items.length === 0) {
          throw new Error("Donante no encontrado.");
        }
        donorId = donors.items[0].id;
      } else {
        const err = await donorResp.json();
        throw new Error(err.message ?? "Error al crear el perfil de donante.");
      }

      // Create SEPA SetupIntent
      const setupResp = await fetch(`${API_BASE}/donations/sepa/setup-intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ donor_id: donorId }),
      });

      if (!setupResp.ok) {
        const err = await setupResp.json();
        throw new Error(
          err.message ?? "Error al inicializar el débito SEPA."
        );
      }

      const setup = await setupResp.json();
      setSetupIntentData({
        clientSecret: setup.client_secret,
        stripeCustomerId: setup.stripe_customer_id,
        donorId,
      });
      setStep("iban");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Error inesperado."
      );
    } finally {
      setIsLoading(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (step === "success") {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
          ¡Cuenta guardada!
        </h2>
        <p className="text-gray-500 text-sm mb-6">
          Tu cuenta bancaria ha sido guardada de forma segura. Recibirás una
          confirmación por correo electrónico con los detalles del mandato SEPA.
        </p>
        <a
          href="/donate"
          className="inline-block bg-primary-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-primary-700 transition-colors text-sm"
        >
          Volver a donaciones
        </a>
      </div>
    );
  }

  if (step === "error") {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </div>
        <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
          Error al configurar SEPA
        </h2>
        <p className="text-gray-500 text-sm mb-6">{errorMessage}</p>
        <button
          onClick={() => {
            setStep("donor-details");
            setErrorMessage("");
          }}
          className="inline-block bg-primary-600 text-white font-medium px-6 py-2.5 rounded-lg hover:bg-primary-700 transition-colors text-sm"
        >
          Intentar de nuevo
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8">
      {/* Progress indicator */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === "donor-details"
              ? "bg-primary-600 text-white"
              : "bg-green-100 text-green-700"
          }`}
        >
          {step !== "donor-details" ? "✓" : "1"}
        </div>
        <div className="w-8 h-px bg-gray-200" />
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            step === "iban"
              ? "bg-primary-600 text-white"
              : "bg-gray-100 text-gray-400"
          }`}
        >
          2
        </div>
      </div>

      {step === "donor-details" && (
        <form onSubmit={handleDonorSubmit} className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Tus datos
          </h2>
          {errorMessage && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {errorMessage}
            </div>
          )}
          <div>
            <label
              htmlFor="fullName"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Nombre completo
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={donorData.fullName}
              onChange={(e) =>
                setDonorData((prev) => ({ ...prev, fullName: e.target.value }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              placeholder="Jan de Vries"
            />
          </div>
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              required
              value={donorData.email}
              onChange={(e) =>
                setDonorData((prev) => ({ ...prev, email: e.target.value }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              placeholder="jan@ejemplo.nl"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 px-4 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors text-sm mt-2"
          >
            {isLoading ? "Procesando..." : "Continuar"}
          </button>
        </form>
      )}

      {step === "iban" && setupIntentData && (
        <Elements
          stripe={stripePromise}
          options={{ clientSecret: setupIntentData.clientSecret }}
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Datos bancarios
          </h2>
          <SepaIbanForm
            clientSecret={setupIntentData.clientSecret}
            donorName={donorData.fullName}
            donorEmail={donorData.email}
            onSuccess={() => setStep("success")}
            onError={(msg) => {
              setErrorMessage(msg);
              setStep("error");
            }}
            onBack={() => setStep("donor-details")}
          />
        </Elements>
      )}
    </div>
  );
}
