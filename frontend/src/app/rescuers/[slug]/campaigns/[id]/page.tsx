"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

// -- Types ------------------------------------------------------------------

interface DonorEntry {
  donor_name: string;
  amount_eur: number;
  donated_at: string;
}

interface PublicCampaign {
  id: string;
  rescuer_slug: string;
  rescuer_name: string;
  rescuer_verified: boolean;
  title: string;
  description: string;
  target_amount_eur: number;
  raised_amount_eur: number;
  progress_pct: number;
  donor_count: number;
  fund_category: string;
  category_label_es: string;
  status: string;
  status_label_es: string;
  goal_message: string | null;
  photo_urls: string[];
  deadline: string | null;
  recent_donors: DonorEntry[];
  created_at: string;
}

// -- Helpers ----------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PY", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

// -- Sub-components ---------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4 max-w-2xl mx-auto px-4 py-8">
      <div className="h-8 bg-gray-200 rounded w-3/4" />
      <div className="h-4 bg-gray-200 rounded w-1/2" />
      <div className="h-48 bg-gray-200 rounded-xl" />
      <div className="h-24 bg-gray-200 rounded" />
    </div>
  );
}

function ProgressBar({ pct, raised, target }: { pct: number; raised: number; target: number }) {
  return (
    <div className="mt-4">
      <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
        <span className="text-[var(--color-primary)] text-lg font-bold">
          €{raised.toFixed(0)}
        </span>
        <span className="text-gray-500">de €{target.toFixed(0)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-[var(--color-primary)] h-3 rounded-full transition-all"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1.5">{pct.toFixed(0)}% alcanzado</p>
    </div>
  );
}

function DonorList({ donors }: { donors: DonorEntry[] }) {
  if (donors.length === 0) {
    return (
      <p className="text-sm text-gray-500 italic">
        Se el primero en donar a esta campana.
      </p>
    );
  }

  return (
    <ul className="space-y-2" aria-label="Donantes recientes">
      {donors.map((d, i) => (
        <li key={i} className="flex items-center justify-between text-sm">
          <span className="text-gray-700 font-medium">{d.donor_name}</span>
          <span className="text-gray-500">
            €{d.amount_eur.toFixed(0)} &middot;{" "}
            <span className="text-xs">{formatDate(d.donated_at)}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

// -- Main page --------------------------------------------------------------

export default function PublicCampaignDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const id = params?.id as string;

  const [campaign, setCampaign] = useState<PublicCampaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug || !id) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchJSON<PublicCampaign>(
          `${API}/api/rescuers/${slug}/campaigns/${id}`
        );
        setCampaign(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Campana no encontrada"
        );
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [slug, id]);

  if (loading) return <LoadingSkeleton />;

  if (error || !campaign) {
    return (
      <main className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-4xl mb-4">🔍</p>
        <h1 className="text-lg font-semibold text-gray-900 mb-2">
          Campana no encontrada
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          {error ?? "Esta campana no existe o fue removida."}
        </p>
        <Link
          href={`/rescuers/${slug}`}
          className="text-[var(--color-primary)] text-sm font-medium underline"
        >
          Ver perfil del rescatista
        </Link>
      </main>
    );
  }

  const isClosed =
    campaign.status === "completed" || campaign.status === "archived";
  const deadlinePassed =
    campaign.deadline && new Date(campaign.deadline) < new Date();

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="text-xs text-gray-400 mb-6" aria-label="Navegacion">
        <Link href="/rescuers" className="hover:text-gray-600">
          Rescatistas
        </Link>
        {" / "}
        <Link
          href={`/rescuers/${campaign.rescuer_slug}`}
          className="hover:text-gray-600"
        >
          {campaign.rescuer_name}
        </Link>
        {" / Campana"}
      </nav>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
            {campaign.category_label_es}
          </span>
          {campaign.rescuer_verified && (
            <span
              className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"
              title="Rescatista verificado"
            >
              Verificado
            </span>
          )}
          {isClosed && (
            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full">
              {campaign.status_label_es}
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900 leading-tight">
          {campaign.title}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Por{" "}
          <Link
            href={`/rescuers/${campaign.rescuer_slug}`}
            className="text-[var(--color-primary)] font-medium hover:underline"
          >
            {campaign.rescuer_name}
          </Link>{" "}
          &middot; Iniciada el {formatDate(campaign.created_at)}
        </p>
      </div>

      {/* Photos */}
      {campaign.photo_urls.length > 0 && (
        <div className="mb-6 overflow-x-auto flex gap-3 pb-1">
          {campaign.photo_urls.map((url, i) => (
            <img
              key={i}
              src={url}
              alt={`Foto ${i + 1} de la campana`}
              className="h-48 w-auto rounded-xl object-cover flex-shrink-0 border border-gray-100"
            />
          ))}
        </div>
      )}

      {/* Progress */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6 shadow-sm">
        <div className="flex gap-4 text-center mb-2">
          <div className="flex-1">
            <p className="text-2xl font-bold text-[var(--color-primary)]">
              {campaign.donor_count}
            </p>
            <p className="text-xs text-gray-500">donantes</p>
          </div>
          <div className="flex-1">
            <p className="text-2xl font-bold text-gray-900">
              €{campaign.raised_amount_eur.toFixed(0)}
            </p>
            <p className="text-xs text-gray-500">recaudado</p>
          </div>
          <div className="flex-1">
            <p className="text-2xl font-bold text-gray-900">
              €{campaign.target_amount_eur.toFixed(0)}
            </p>
            <p className="text-xs text-gray-500">meta</p>
          </div>
        </div>
        <ProgressBar
          pct={campaign.progress_pct}
          raised={campaign.raised_amount_eur}
          target={campaign.target_amount_eur}
        />
        {campaign.deadline && (
          <p
            className={`text-xs mt-2 ${deadlinePassed ? "text-red-500" : "text-gray-500"}`}
          >
            {deadlinePassed ? "Plazo vencido" : "Plazo:"}{" "}
            {formatDate(campaign.deadline)}
          </p>
        )}
      </div>

      {/* Goal message */}
      {campaign.goal_message && (
        <blockquote className="border-l-4 border-[var(--color-primary)] pl-4 italic text-gray-700 text-sm mb-6">
          &ldquo;{campaign.goal_message}&rdquo;
        </blockquote>
      )}

      {/* Donate CTA */}
      {!isClosed && (
        <Link
          href={`/donar?target=campaign&campaign_id=${campaign.id}&rescuer=${campaign.rescuer_slug}`}
          className="block w-full text-center bg-[var(--color-primary)] text-white font-semibold rounded-xl py-3 hover:opacity-90 transition-opacity mb-8"
        >
          Donar a esta campana
        </Link>
      )}

      {/* Description */}
      <section className="mb-8">
        <h2 className="font-semibold text-gray-900 mb-3">Sobre esta campana</h2>
        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
          {campaign.description}
        </p>
      </section>

      {/* Recent donors */}
      <section>
        <h2 className="font-semibold text-gray-900 mb-3">
          Donantes recientes
        </h2>
        <DonorList donors={campaign.recent_donors} />
      </section>
    </main>
  );
}
