"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

// -- Types ------------------------------------------------------------------

interface ProfileHeader {
  id: string;
  slug: string;
  display_name: string;
  photo_url: string | null;
  bio: string;
  location: string;
  is_verified: boolean;
  verification_method: string | null;
  verified_since: string | null;
  joined_date: string;
  social_links: Record<string, string>;
}

interface ImpactStats {
  animals_rescued: number;
  animals_adopted: number;
  animals_sterilized: number;
  financial_support_received_pyg: number;
  active_supporters: number;
  years_active: number;
}

interface AnimalCard {
  id: string;
  name: string;
  species: string;
  breed: string;
  age: string;
  photo_url: string | null;
  adoption_status: string;
  description: string;
}

interface CampaignCard {
  id: string;
  title: string;
  description: string;
  goal_amount: number;
  raised_amount: number;
  currency: string;
  progress_pct: number;
  status: string;
  supporter_count: number;
}

interface Supporter {
  id: string;
  display_name: string;
  is_anonymous: boolean;
  amount: number | null;
  currency: string | null;
  message: string | null;
  is_monthly: boolean;
}

interface DonationOption {
  label: string;
  amount: number;
  currency: string;
  is_monthly: boolean;
}

interface SupportOptions {
  donation_options: DonationOption[];
  accepts_monthly: boolean;
  custom_amount_allowed: boolean;
}

interface ContactInfo {
  email: string | null;
  whatsapp: string | null;
  phone: string | null;
  facebook_url: string | null;
  instagram_url: string | null;
  website_url: string | null;
  accepts_messages: boolean;
}

interface FullProfile {
  header: ProfileHeader;
  impact: ImpactStats;
  animals_preview: AnimalCard[];
  campaigns: CampaignCard[];
  support_options: SupportOptions;
  contact: ContactInfo;
}

// -- API helper -------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

// -- Sub-components ---------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-pulse space-y-6">
      <div className="h-48 bg-gray-200 rounded-xl" />
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-20 bg-gray-200 rounded-lg" />
        ))}
      </div>
      <div className="h-64 bg-gray-200 rounded-xl" />
    </div>
  );
}

function VerifiedBadge({ method }: { method: string | null }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
          clipRule="evenodd"
        />
      </svg>
      Verificado{method ? ` (${method.replace(/_/g, " ")})` : ""}
    </span>
  );
}

function ImpactSection({ impact }: { impact: ImpactStats }) {
  const stats = [
    { label: "Rescatados", value: impact.animals_rescued },
    { label: "Adoptados", value: impact.animals_adopted },
    { label: "Esterilizados", value: impact.animals_sterilized },
    { label: "Apoyo recibido", value: `${new Intl.NumberFormat("es-PY").format(impact.financial_support_received_pyg)} Gs` },
    { label: "Apoyadores", value: impact.active_supporters },
    { label: "Anos activo", value: impact.years_active.toFixed(1) },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((s) => (
        <div key={s.label} className="bg-white rounded-lg border border-gray-200 p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{s.value}</div>
          <div className="text-xs text-gray-500 mt-1">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

function AnimalSection({ animals, slug }: { animals: AnimalCard[]; slug: string }) {
  if (animals.length === 0) return null;

  const statusColors: Record<string, string> = {
    available: "bg-green-100 text-green-800",
    in_process: "bg-yellow-100 text-yellow-800",
    adopted: "bg-blue-100 text-blue-800",
    medical_hold: "bg-red-100 text-red-800",
  };

  const statusLabels: Record<string, string> = {
    available: "Disponible",
    in_process: "En proceso",
    adopted: "Adoptado",
    medical_hold: "En tratamiento",
  };

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Animales en cuidado</h2>
        <Link href={`/rescuers/${slug}/animals`} className="text-sm text-orange-600 hover:underline">
          Ver todos
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {animals.map((animal) => (
          <div key={animal.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div className="h-40 bg-gray-100 flex items-center justify-center text-gray-400">
              {animal.photo_url ? (
                <div className="w-full h-full bg-gray-200" />
              ) : (
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              )}
            </div>
            <div className="p-3">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-medium text-gray-900">{animal.name}</h3>
                <span className={`px-2 py-0.5 text-xs rounded-full ${statusColors[animal.adoption_status] ?? "bg-gray-100"}`}>
                  {statusLabels[animal.adoption_status] ?? animal.adoption_status}
                </span>
              </div>
              <p className="text-sm text-gray-500">{animal.species} &middot; {animal.breed} &middot; {animal.age}</p>
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{animal.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CampaignSection({ campaigns }: { campaigns: CampaignCard[] }) {
  if (campaigns.length === 0) return null;

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Campanas</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {campaigns.map((c) => {
          const raised = new Intl.NumberFormat("es-PY").format(c.raised_amount);
          const goal = new Intl.NumberFormat("es-PY").format(c.goal_amount);

          return (
            <div key={c.id} className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 mb-1">{c.title}</h3>
              <p className="text-sm text-gray-600 mb-3">{c.description}</p>
              <div className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>{raised} {c.currency}</span>
                  <span className="text-gray-500">de {goal} {c.currency}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full transition-all"
                    style={{ width: `${Math.min(c.progress_pct, 100)}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{c.supporter_count} apoyadores</span>
                <span className="capitalize">{c.status === "completed" ? "Completada" : c.status === "active" ? "Activa" : "Pausada"}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SupporterWall({ supporters }: { supporters: Supporter[] }) {
  if (supporters.length === 0) return null;

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Apoyadores</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {supporters.map((s) => (
          <div key={s.id} className="bg-white rounded-lg border border-gray-200 p-3 flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-medium text-sm flex-shrink-0">
              {s.is_anonymous ? "?" : s.display_name.charAt(0)}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900 text-sm">
                  {s.is_anonymous ? "Anonimo" : s.display_name}
                </span>
                {s.is_monthly && (
                  <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Mensual</span>
                )}
              </div>
              {s.message && <p className="text-xs text-gray-500 mt-0.5 truncate">{s.message}</p>}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function SupportButton({ options }: { options: SupportOptions }) {
  const [showOptions, setShowOptions] = useState(false);

  return (
    <div className="bg-white rounded-lg border-2 border-orange-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-2">Apoyar este rescatista</h2>
      <p className="text-sm text-gray-600 mb-4">Tu apoyo ayuda a salvar mas animales</p>

      {!showOptions ? (
        <button
          onClick={() => setShowOptions(true)}
          className="w-full py-3 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors"
        >
          Apoyar ahora
        </button>
      ) : (
        <div className="space-y-2">
          {options.donation_options.map((opt, i) => {
            const amount = opt.currency === "PYG"
              ? `${new Intl.NumberFormat("es-PY").format(opt.amount)} Gs`
              : `${opt.amount} ${opt.currency}`;

            return (
              <button
                key={i}
                className="w-full py-2 px-4 text-left border border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors flex items-center justify-between"
              >
                <span className="text-sm">{opt.label}</span>
                <span className="text-sm font-medium text-orange-600">
                  {amount} {opt.is_monthly ? "/mes" : ""}
                </span>
              </button>
            );
          })}
          {options.custom_amount_allowed && (
            <button className="w-full py-2 px-4 text-sm text-center text-orange-600 border border-dashed border-orange-300 rounded-lg hover:bg-orange-50 transition-colors">
              Monto personalizado
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function ContactSection({ contact }: { contact: ContactInfo }) {
  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Contacto</h2>
      <div className="space-y-2">
        {contact.whatsapp && (
          <a
            href={`https://wa.me/${contact.whatsapp.replace(/\+/g, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-green-700 hover:underline"
          >
            WhatsApp
          </a>
        )}
        {contact.email && (
          <a href={`mailto:${contact.email}`} className="flex items-center gap-2 text-sm text-gray-700 hover:underline">
            {contact.email}
          </a>
        )}
        {contact.facebook_url && (
          <a href={contact.facebook_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-blue-700 hover:underline">
            Facebook
          </a>
        )}
        {contact.instagram_url && (
          <a href={contact.instagram_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-pink-700 hover:underline">
            Instagram
          </a>
        )}
        {contact.website_url && (
          <a href={contact.website_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm text-gray-700 hover:underline">
            Sitio web
          </a>
        )}
      </div>
    </section>
  );
}

function ShareButtons({ name, slug }: { name: string; slug: string }) {
  const url = `https://refugioanimal.com.py/rescuers/${slug}`;
  const text = `Conoce a ${name}, rescatista de animales en Paraguay`;

  return (
    <div className="flex gap-2">
      <a
        href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`}
        target="_blank"
        rel="noopener noreferrer"
        className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Facebook
      </a>
      <a
        href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`}
        target="_blank"
        rel="noopener noreferrer"
        className="px-3 py-1.5 text-xs bg-gray-800 text-white rounded hover:bg-gray-900 transition-colors"
      >
        Twitter
      </a>
      <a
        href={`https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`}
        target="_blank"
        rel="noopener noreferrer"
        className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
      >
        WhatsApp
      </a>
    </div>
  );
}

// -- Main page --------------------------------------------------------------

export default function RescuerProfilePage() {
  const params = useParams();
  const slug = params.slug as string;
  const [profile, setProfile] = useState<FullProfile | null>(null);
  const [supporters, setSupporters] = useState<Supporter[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [profileRes, supportersRes] = await Promise.all([
          fetch(`${API}/api/rescuers/${slug}/profile`),
          fetch(`${API}/api/rescuers/${slug}/supporters`),
        ]);

        if (profileRes.ok) {
          setProfile(await profileRes.json());
        }
        if (supportersRes.ok) {
          const data = await supportersRes.json();
          setSupporters(data.supporters ?? []);
        }
      } catch {
        /* API not connected */
      } finally {
        setLoading(false);
      }
    }
    if (slug) load();
  }, [slug]);

  if (loading) return <LoadingSkeleton />;

  if (!profile) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Rescatista no encontrado</h1>
        <p className="text-gray-600 mb-6">El perfil que buscas no existe o fue removido.</p>
        <Link href="/rescuers" className="text-orange-600 hover:underline">
          Ver directorio de rescatistas
        </Link>
      </div>
    );
  }

  const { header, impact, animals_preview, campaigns, support_options, contact } = profile;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Profile header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex flex-col sm:flex-row gap-6">
          {/* Photo */}
          <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-full bg-gray-100 flex-shrink-0 flex items-center justify-center overflow-hidden">
            {header.photo_url ? (
              <div className="w-full h-full bg-gray-200" />
            ) : (
              <span className="text-4xl text-gray-400">{header.display_name.charAt(0)}</span>
            )}
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{header.display_name}</h1>
              {header.is_verified && <VerifiedBadge method={header.verification_method} />}
            </div>
            <p className="text-sm text-gray-500 mb-3">{header.location} &middot; Desde {new Date(header.joined_date).getFullYear()}</p>
            <p className="text-gray-700 mb-4">{header.bio}</p>
            <div className="flex flex-wrap items-center gap-3">
              <ShareButtons name={header.display_name} slug={header.slug} />
            </div>
          </div>
        </div>
      </div>

      {/* Impact stats */}
      <div className="mb-6">
        <ImpactSection impact={impact} />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: animals + campaigns + supporters */}
        <div className="lg:col-span-2 space-y-8">
          <AnimalSection animals={animals_preview} slug={header.slug} />
          <CampaignSection campaigns={campaigns} />
          <SupporterWall supporters={supporters} />
        </div>

        {/* Right column: support + contact */}
        <div className="space-y-6">
          <SupportButton options={support_options} />
          <ContactSection contact={contact} />
        </div>
      </div>
    </div>
  );
}
