"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface EmergencyDonateInfo {
  id: string;
  title: string;
  description: string;
  photos: string[];
  amount_needed_cents: number;
  amount_raised_cents: number;
  remaining_cents: number;
  currency: string;
  progress_pct: number;
  suggested_amounts_cents: number[];
  status: string;
}

interface DonationResult {
  donation_id: string;
  emergency_id: string;
  amount_cents: number;
  currency: string;
  new_total_raised_cents: number;
  new_progress_pct: number;
  message: string;
}

/* ------------------------------------------------------------------ */
/* Constants                                                           */
/* ------------------------------------------------------------------ */

const CURRENCY_OPTIONS = [
  { value: "USD", label: "USD ($)", symbol: "$" },
  { value: "PYG", label: "PYG (Gs)", symbol: "Gs" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function formatAmount(cents: number, currency: string): string {
  const symbol = CURRENCY_OPTIONS.find((c) => c.value === currency)?.symbol ?? "$";
  if (currency === "PYG") {
    return `${symbol} ${cents.toLocaleString("es-PY")}`;
  }
  return `${symbol}${(cents / 100).toFixed(2)}`;
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function EmergencyDonatePage() {
  const params = useParams();
  const router = useRouter();
  const emergencyId = params.id as string;

  // Data state
  const [info, setInfo] = useState<EmergencyDonateInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [donorEmail, setDonorEmail] = useState("");
  const [donorName, setDonorName] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Success state
  const [result, setResult] = useState<DonationResult | null>(null);

  // Fetch emergency info
  useEffect(() => {
    if (!emergencyId) return;
    setLoading(true);
    fetch(`${API_BASE}/api/emergencies/${emergencyId}/donate/info`)
      .then((res) => {
        if (!res.ok) throw new Error("Emergency not found");
        return res.json();
      })
      .then((data: EmergencyDonateInfo) => {
        setInfo(data);
        setCurrency(data.currency);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [emergencyId]);

  // Computed final amount in cents
  const finalAmountCents = selectedAmount ?? (customAmount ? parseCentsFromInput(customAmount, currency) : 0);

  function parseCentsFromInput(input: string, curr: string): number {
    const num = parseFloat(input);
    if (isNaN(num) || num <= 0) return 0;
    return curr === "PYG" ? Math.round(num) : Math.round(num * 100);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (finalAmountCents <= 0) {
      setFormError("Por favor selecciona o ingresa un monto valido.");
      return;
    }

    setSubmitting(true);
    try {
      const body: Record<string, unknown> = {
        amount_cents: finalAmountCents,
        currency,
        payment_method: "stripe",
      };
      if (donorEmail) body.donor_email = donorEmail;
      if (donorName) body.donor_name = donorName;
      if (notes) body.notes = notes;

      const res = await fetch(`${API_BASE}/api/emergencies/${emergencyId}/donate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error al procesar la donacion" }));
        throw new Error(typeof err.detail === "string" ? err.detail : err.detail?.error ?? "Error");
      }

      const data: DonationResult = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setSubmitting(false);
    }
  }

  /* -- Loading / Error states -- */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500 text-lg">Cargando...</div>
      </div>
    );
  }

  if (error || !info) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-4">
        <p className="text-red-600 text-lg">{error ?? "Emergencia no encontrada"}</p>
        <Link href="/" className="text-primary-600 hover:underline">
          Volver al inicio
        </Link>
      </div>
    );
  }

  /* -- Success state -- */
  if (result) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-green-50 to-white flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Gracias por tu ayuda!
          </h1>
          <p className="text-gray-600 mb-4">{result.message}</p>
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500">Tu donacion</p>
            <p className="text-2xl font-bold text-primary-600">
              {formatAmount(result.amount_cents, result.currency)}
            </p>
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all"
                  style={{ width: `${result.new_progress_pct}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">{result.new_progress_pct}% de la meta alcanzada</p>
            </div>
          </div>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: `Ayuda a ${info.title}`,
                    text: `He donado para ayudar en esta emergencia animal. Tu tambien puedes ayudar!`,
                    url: window.location.href,
                  });
                }
              }}
              className="w-full bg-primary-600 text-white py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              Compartir esta emergencia
            </button>
            <Link
              href="/"
              className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors text-center"
            >
              Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    );
  }

  /* -- Donation form -- */
  const progressPct = info.progress_pct;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Emergency header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-500 text-white">
        <div className="max-w-2xl mx-auto px-4 py-8">
          {info.photos.length > 0 && (
            <div className="w-full h-48 rounded-xl overflow-hidden mb-4">
              <img
                src={info.photos[0]}
                alt={info.title}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">{info.title}</h1>
          <p className="text-white/90 text-sm sm:text-base mb-4 line-clamp-3">
            {info.description}
          </p>

          {/* Progress bar */}
          <div className="bg-white/20 rounded-full h-4 mb-2">
            <div
              className="bg-white h-4 rounded-full transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className="flex justify-between text-sm">
            <span>{formatAmount(info.amount_raised_cents, info.currency)} recaudado</span>
            <span>Meta: {formatAmount(info.amount_needed_cents, info.currency)}</span>
          </div>
        </div>
      </div>

      {/* Donation form */}
      <div className="max-w-2xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Suggested amounts */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Selecciona un monto
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {info.suggested_amounts_cents.map((amt) => (
                <button
                  key={amt}
                  type="button"
                  onClick={() => {
                    setSelectedAmount(amt);
                    setCustomAmount("");
                  }}
                  className={`py-3 px-4 rounded-lg font-semibold text-center transition-all border-2 ${
                    selectedAmount === amt
                      ? "border-primary-600 bg-primary-50 text-primary-700"
                      : "border-gray-200 bg-white text-gray-700 hover:border-primary-300"
                  }`}
                >
                  {formatAmount(amt, info.currency)}
                </button>
              ))}
            </div>
          </div>

          {/* Custom amount */}
          <div>
            <label htmlFor="custom-amount" className="block text-sm font-semibold text-gray-700 mb-2">
              O ingresa otro monto
            </label>
            <div className="flex gap-3">
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="px-3 py-3 border border-gray-300 rounded-lg bg-white text-gray-700 font-medium"
                aria-label="Moneda"
              >
                {CURRENCY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <input
                id="custom-amount"
                type="number"
                min="0"
                step={currency === "PYG" ? "1" : "0.01"}
                placeholder={currency === "PYG" ? "50000" : "25.00"}
                value={customAmount}
                onChange={(e) => {
                  setCustomAmount(e.target.value);
                  setSelectedAmount(null);
                }}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-lg"
              />
            </div>
          </div>

          {/* Guest donor info */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            <h3 className="text-sm font-semibold text-gray-700">Informacion del donante (opcional)</h3>
            <div>
              <label htmlFor="donor-name" className="block text-sm text-gray-600 mb-1">
                Nombre
              </label>
              <input
                id="donor-name"
                type="text"
                value={donorName}
                onChange={(e) => setDonorName(e.target.value)}
                placeholder="Tu nombre"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label htmlFor="donor-email" className="block text-sm text-gray-600 mb-1">
                Email
              </label>
              <input
                id="donor-email"
                type="email"
                value={donorEmail}
                onChange={(e) => setDonorEmail(e.target.value)}
                placeholder="tu@email.com"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label htmlFor="donation-notes" className="block text-sm text-gray-600 mb-1">
                Mensaje (opcional)
              </label>
              <textarea
                id="donation-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Un mensaje de apoyo..."
                rows={2}
                maxLength={500}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
              />
            </div>
          </div>

          {/* Error display */}
          {formError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
              {formError}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={submitting || finalAmountCents <= 0}
            className="w-full bg-primary-600 text-white py-4 rounded-lg font-bold text-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {submitting
              ? "Procesando..."
              : finalAmountCents > 0
                ? `Donar ${formatAmount(finalAmountCents, currency)}`
                : "Selecciona un monto"}
          </button>

          <p className="text-xs text-gray-400 text-center">
            Tu donacion es segura y se dirige directamente a esta emergencia.
          </p>
        </form>
      </div>
    </div>
  );
}
