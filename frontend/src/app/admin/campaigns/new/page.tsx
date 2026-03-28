"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Megaphone, Save } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import ImageUploader from "@/components/admin/ImageUploader";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Nueva Campana";
const LABEL_BACK = "Volver a campanas";
const LABEL_SAVE = "Crear Campana";
const LABEL_SAVING = "Creando...";

const FUND_CATEGORIES: Record<string, string> = {
  medical: "Medico",
  food: "Alimentacion",
  operations: "Operaciones",
  rescue: "Rescate",
  infrastructure: "Infraestructura",
  general: "General",
};

const CURRENCY_OPTIONS: Record<string, string> = {
  EUR: "Euro (EUR)",
  USD: "Dolar (USD)",
  PYG: "Guarani (PYG)",
};

interface CampaignFormData {
  title: string;
  description: string;
  impact_story: string;
  target_amount: string;
  currency: string;
  fund_category: string;
  featured: boolean;
  image_url: string;
  deadline: string;
  min_donation: string;
  max_donation: string;
  allow_overfunding: boolean;
}

const INITIAL_FORM: CampaignFormData = {
  title: "",
  description: "",
  impact_story: "",
  target_amount: "",
  currency: "EUR",
  fund_category: "general",
  featured: false,
  image_url: "",
  deadline: "",
  min_donation: "",
  max_donation: "",
  allow_overfunding: true,
};

export default function NewCampaignPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [form, setForm] = useState<CampaignFormData>(INITIAL_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  function handleChange(
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setForm((prev) => ({ ...prev, [name]: checked }));
    } else {
      setForm((prev) => ({ ...prev, [name]: value }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const targetCents = Math.round(parseFloat(form.target_amount) * 100);
      if (isNaN(targetCents) || targetCents <= 0) {
        setError("El monto objetivo debe ser mayor a 0");
        setIsSaving(false);
        return;
      }

      const payload: Record<string, unknown> = {
        title: form.title.trim(),
        description: form.description.trim(),
        target_amount_cents: targetCents,
        currency: form.currency,
        fund_category: form.fund_category,
        featured: form.featured,
        allow_overfunding: form.allow_overfunding,
      };

      if (form.impact_story.trim()) {
        payload.impact_story = form.impact_story.trim();
      }
      if (form.image_url.trim()) {
        payload.image_url = form.image_url.trim();
      }
      if (form.deadline) {
        payload.deadline = new Date(form.deadline).toISOString();
      }
      if (form.min_donation) {
        const minCents = Math.round(parseFloat(form.min_donation) * 100);
        if (!isNaN(minCents) && minCents > 0) {
          payload.min_donation_cents = minCents;
        }
      }
      if (form.max_donation) {
        const maxCents = Math.round(parseFloat(form.max_donation) * 100);
        if (!isNaN(maxCents) && maxCents > 0) {
          payload.max_donation_cents = maxCents;
        }
      }

      await api.post("/admin/campaigns", payload);
      router.push("/admin/campaigns");
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError("Error al crear la campana");
      }
    } finally {
      setIsSaving(false);
    }
  }

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">Cargando...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6">
          <button
            onClick={() => router.push("/admin/campaigns")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <Megaphone className="h-6 w-6 text-primary-600" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-warm-text-primary">
            {LABEL_PAGE_TITLE}
          </h1>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <label
              htmlFor="title"
              className="mb-1 block text-sm font-medium text-warm-text-primary"
            >
              Titulo *
            </label>
            <input
              id="title"
              name="title"
              type="text"
              required
              maxLength={255}
              value={form.title}
              onChange={handleChange}
              className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Nombre de la campana"
            />
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="description"
              className="mb-1 block text-sm font-medium text-warm-text-primary"
            >
              Descripcion *
            </label>
            <textarea
              id="description"
              name="description"
              required
              rows={4}
              value={form.description}
              onChange={handleChange}
              className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Descripcion de la campana"
            />
          </div>

          {/* Impact Story */}
          <div>
            <label
              htmlFor="impact_story"
              className="mb-1 block text-sm font-medium text-warm-text-primary"
            >
              Historia de Impacto
            </label>
            <textarea
              id="impact_story"
              name="impact_story"
              rows={3}
              value={form.impact_story}
              onChange={handleChange}
              className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Narrativa sobre el impacto de esta campana (opcional)"
            />
          </div>

          {/* Target Amount + Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="target_amount"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Monto Objetivo *
              </label>
              <input
                id="target_amount"
                name="target_amount"
                type="number"
                required
                min="0.01"
                step="0.01"
                value={form.target_amount}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="1000.00"
              />
            </div>
            <div>
              <label
                htmlFor="currency"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Moneda
              </label>
              <select
                id="currency"
                name="currency"
                value={form.currency}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                {Object.entries(CURRENCY_OPTIONS).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Category + Deadline */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="fund_category"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Categoria
              </label>
              <select
                id="fund_category"
                name="fund_category"
                value={form.fund_category}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                {Object.entries(FUND_CATEGORIES).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor="deadline"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Fecha Limite
              </label>
              <input
                id="deadline"
                name="deadline"
                type="date"
                value={form.deadline}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Min/Max donation */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="min_donation"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Donacion Minima
              </label>
              <input
                id="min_donation"
                name="min_donation"
                type="number"
                min="0.01"
                step="0.01"
                value={form.min_donation}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Opcional"
              />
            </div>
            <div>
              <label
                htmlFor="max_donation"
                className="mb-1 block text-sm font-medium text-warm-text-primary"
              >
                Donacion Maxima
              </label>
              <input
                id="max_donation"
                name="max_donation"
                type="number"
                min="0.01"
                step="0.01"
                value={form.max_donation}
                onChange={handleChange}
                className="w-full rounded-lg border border-warm-border bg-warm-surface px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Opcional"
              />
            </div>
          </div>

          {/* Campaign Image */}
          <ImageUploader
            label="Imagen de Campana"
            value={form.image_url}
            onChange={(url) => setForm((prev) => ({ ...prev, image_url: url }))}
          />

          {/* Toggles */}
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                name="featured"
                checked={form.featured}
                onChange={handleChange}
                className="h-4 w-4 rounded border-warm-border text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-warm-text-primary">
                Campana Destacada
              </span>
            </label>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                name="allow_overfunding"
                checked={form.allow_overfunding}
                onChange={handleChange}
                className="h-4 w-4 rounded border-warm-border text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-warm-text-primary">
                Permitir Sobrefinanciamiento
              </span>
            </label>
          </div>

          {/* Submit */}
          <div className="flex justify-end border-t border-warm-border pt-6">
            <button
              type="button"
              onClick={() => router.push("/admin/campaigns")}
              className="mr-3 rounded-lg border border-warm-border px-4 py-2 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-warm-bg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {isSaving ? LABEL_SAVING : LABEL_SAVE}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
