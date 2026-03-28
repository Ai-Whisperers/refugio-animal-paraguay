"use client";

import { useState, useEffect, useCallback } from "react";

// -- Types ------------------------------------------------------------------

interface RescuerCampaign {
  id: string;
  title: string;
  description: string;
  target_amount_eur: number;
  raised_amount_eur: number;
  donor_count: number;
  fund_category: string;
  category_label_es: string;
  status: string;
  status_label_es: string;
  goal_message: string | null;
  animal_ids: string[];
  photo_urls: string[];
  deadline: string | null;
  requires_approval: boolean;
  created_at: string;
}

interface CampaignListResponse {
  campaigns: RescuerCampaign[];
  total: number;
  page: number;
  page_size: number;
}

interface CreateCampaignForm {
  title: string;
  description: string;
  target_amount_eur: number | "";
  fund_category: string;
  goal_message: string;
  photo_urls: string;
  deadline: string;
}

// -- API helpers ------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// -- Sub-components ---------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-36 bg-gray-200 rounded-lg" />
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    draft: "bg-yellow-100 text-yellow-800",
    completed: "bg-blue-100 text-blue-800",
    archived: "bg-gray-100 text-gray-600",
  };
  const labels: Record<string, string> = {
    active: "Activa",
    draft: "Borrador",
    completed: "Completada",
    archived: "Archivada",
  };
  return (
    <span
      className={`px-2 py-0.5 text-xs font-semibold rounded-full ${colors[status] ?? "bg-gray-100"}`}
    >
      {labels[status] ?? status}
    </span>
  );
}

function ProgressBar({ raised, target }: { raised: number; target: number }) {
  const pct = target > 0 ? Math.min((raised / target) * 100, 100) : 0;
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>€{raised.toFixed(0)} recaudado</span>
        <span>Meta: €{target.toFixed(0)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-[var(--color-primary)] h-2 rounded-full transition-all"
          style={{ width: `${pct}%` }}
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          role="progressbar"
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">{pct.toFixed(0)}% completado</p>
    </div>
  );
}

function CampaignCard({
  campaign,
  onEnd,
}: {
  campaign: RescuerCampaign;
  onEnd: (id: string) => void;
}) {
  const isActive = campaign.status === "active" || campaign.status === "draft";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-gray-900 text-sm truncate">
              {campaign.title}
            </h3>
            <StatusBadge status={campaign.status} />
            {campaign.requires_approval && (
              <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">
                Pendiente aprobacion
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
            {campaign.description}
          </p>
          {campaign.goal_message && (
            <p className="text-xs italic text-[var(--color-primary)] mt-1">
              &ldquo;{campaign.goal_message}&rdquo;
            </p>
          )}
          <div className="flex gap-3 text-xs text-gray-500 mt-2">
            <span>{campaign.donor_count} donantes</span>
            <span className="text-gray-300">|</span>
            <span>{campaign.category_label_es}</span>
          </div>
        </div>
        {isActive && (
          <button
            onClick={() => onEnd(campaign.id)}
            className="text-xs text-gray-500 hover:text-red-600 whitespace-nowrap border border-gray-200 rounded px-2 py-1 transition-colors"
            aria-label={`Finalizar campana ${campaign.title}`}
          >
            Finalizar
          </button>
        )}
      </div>
      <ProgressBar
        raised={campaign.raised_amount_eur}
        target={campaign.target_amount_eur}
      />
    </div>
  );
}

function CreateCampaignModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (c: RescuerCampaign) => void;
}) {
  const [form, setForm] = useState<CreateCampaignForm>({
    title: "",
    description: "",
    target_amount_eur: "",
    fund_category: "rescue",
    goal_message: "",
    photo_urls: "",
    deadline: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof CreateCampaignForm, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const photoList = form.photo_urls
        ? form.photo_urls
            .split("\n")
            .map((u) => u.trim())
            .filter(Boolean)
        : [];

      const payload = {
        title: form.title,
        description: form.description,
        target_amount_eur: Number(form.target_amount_eur),
        fund_category: form.fund_category,
        goal_message: form.goal_message || null,
        photo_urls: photoList,
        deadline: form.deadline || null,
        animal_ids: [],
      };

      const created = await fetchJSON<RescuerCampaign>(
        `${API}/api/portal/rescuer/campaigns`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
          body: JSON.stringify(payload),
        }
      );
      onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear la campana");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 id="modal-title" className="font-bold text-gray-900">
            Nueva campana de recaudacion
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Cerrar"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              {error}
            </p>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Titulo <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              minLength={5}
              maxLength={200}
              value={form.title}
              onChange={(e) => updateField("title", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
              placeholder="Ej: Ayuda para tratamiento de Luna"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripcion <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              minLength={20}
              maxLength={2000}
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              rows={4}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent resize-none"
              placeholder="Describe la situacion y como se usaran los fondos..."
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meta (EUR) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                required
                min={10}
                max={50000}
                step="0.01"
                value={form.target_amount_eur}
                onChange={(e) => updateField("target_amount_eur", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
                placeholder="500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoria
              </label>
              <select
                value={form.fund_category}
                onChange={(e) => updateField("fund_category", e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
              >
                <option value="rescue">Rescate</option>
                <option value="medical">Medico</option>
                <option value="food">Alimento</option>
                <option value="operations">Operaciones</option>
                <option value="general">General</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mensaje motivador <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              maxLength={300}
              value={form.goal_message}
              onChange={(e) => updateField("goal_message", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
              placeholder="Ej: Juntos podemos darle una segunda oportunidad a Luna"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha limite <span className="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input
              type="date"
              value={form.deadline}
              onChange={(e) => updateField("deadline", e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg py-2 text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 bg-[var(--color-primary)] text-white rounded-lg py-2 text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {submitting ? "Creando..." : "Crear campana"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// -- Main page --------------------------------------------------------------

export default function RescuerCampaignsPage() {
  const [campaigns, setCampaigns] = useState<RescuerCampaign[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON<CampaignListResponse>(
        `${API}/api/portal/rescuer/campaigns?page=${page}&page_size=${PAGE_SIZE}`,
        { headers: getAuthHeaders() }
      );
      setCampaigns(data.campaigns);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar campanas");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadCampaigns();
  }, [loadCampaigns]);

  async function handleEndCampaign(id: string) {
    if (!confirm("Marcar esta campana como completada?")) return;
    try {
      await fetchJSON(`${API}/api/portal/rescuer/campaigns/${id}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ action: "complete" }),
      });
      await loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al finalizar campana");
    }
  }

  function handleCreated(campaign: RescuerCampaign) {
    setShowCreate(false);
    setCampaigns((prev) => [campaign, ...prev]);
    setTotal((prev) => prev + 1);
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Mis Campanas</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {total} campana{total !== 1 ? "s" : ""} en total
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-[var(--color-primary)] text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
        >
          + Nueva campana
        </button>
      </div>

      {loading && <LoadingSkeleton />}

      {!loading && error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && campaigns.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p className="text-4xl mb-3">📣</p>
          <p className="font-medium">Aun no tienes campanas</p>
          <p className="text-sm mt-1">
            Crea tu primera campana para recaudar fondos para tus rescates.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 bg-[var(--color-primary)] text-white text-sm font-medium px-5 py-2 rounded-lg hover:opacity-90 transition-opacity"
          >
            Crear primera campana
          </button>
        </div>
      )}

      {!loading && !error && campaigns.length > 0 && (
        <div className="space-y-4">
          {campaigns.map((c) => (
            <CampaignCard key={c.id} campaign={c} onEnd={handleEndCampaign} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Anterior
          </button>
          <span className="px-3 py-1.5 text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Siguiente
          </button>
        </div>
      )}

      {showCreate && (
        <CreateCampaignModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />
      )}
    </main>
  );
}
