"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Heart, MapPin, Shield, Users, PawPrint, ExternalLink } from "lucide-react";
import { apiFetch } from "@/lib/public-api";
import { COMMON } from "@/lib/strings";

const S = {
  loading: "Cargando perfil...",
  notFound: "Rescatista no encontrado",
  backToRescuers: "Volver",
  verified: "Verificado",
  animals: "Animales rescatados",
  supporters: "Personas apoyando",
  about: "Sobre",
  supportButton: (name: string) => `Apoyar a ${name}`,
  impactMessage: (name: string) =>
    `Tu apoyo ayuda a ${name} a seguir salvando vidas de animales en situacion de calle.`,
  socialLinks: "Redes sociales",
  noSocial: "Sin redes sociales registradas",
  errorLoad: "No pudimos cargar el perfil. Intenta de nuevo.",
  retry: "Reintentar",
} as const;

interface RescuerProfile {
  id: string;
  user_id: string;
  display_name: string;
  slug: string;
  bio: string | null;
  location_city: string | null;
  is_verified: boolean;
  verification_method: string | null;
  animal_count: number;
  supporter_count: number;
  social_links: Record<string, string> | null;
  phone_whatsapp: string | null;
}

const SOCIAL_LABELS: Record<string, string> = {
  facebook: "Facebook",
  instagram: "Instagram",
  whatsapp: "WhatsApp",
  email: "Email",
};

export default function RescuerProfilePage() {
  const params = useParams<{ slug: string }>();
  const [profile, setProfile] = useState<RescuerProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.slug) return;
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.slug]);

  async function loadProfile() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiFetch<RescuerProfile>(`/api/rescuers/${params.slug}`);
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : COMMON.error);
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-gray-500">{S.loading}</div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-red-600">{error ?? S.notFound}</p>
        <button
          onClick={loadProfile}
          className="px-4 py-2 bg-[#E8622A] text-white rounded-lg hover:bg-[#d4571f] transition-colors"
        >
          {S.retry}
        </button>
      </div>
    );
  }

  const socialEntries = profile.social_links
    ? Object.entries(profile.social_links).filter(([, v]) => v)
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <Link
            href="/rescuers"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            {S.backToRescuers}
          </Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Profile Card */}
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <div className="flex items-start gap-4 mb-6">
            {/* Avatar placeholder */}
            <div className="w-16 h-16 rounded-full bg-[#E8622A] flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
              {profile.display_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold text-gray-900">
                  {profile.display_name}
                </h1>
                {profile.is_verified && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                    <Shield className="h-3 w-3" />
                    {S.verified}
                  </span>
                )}
              </div>
              {profile.location_city && (
                <p className="text-gray-500 text-sm flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {profile.location_city}
                </p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-orange-50 rounded-xl p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-[#E8622A] mb-1">
                <PawPrint className="h-5 w-5" />
                <span className="text-2xl font-bold">{profile.animal_count}</span>
              </div>
              <p className="text-sm text-gray-600">{S.animals}</p>
            </div>
            <div className="bg-pink-50 rounded-xl p-4 text-center">
              <div className="flex items-center justify-center gap-2 text-pink-600 mb-1">
                <Users className="h-5 w-5" />
                <span className="text-2xl font-bold">{profile.supporter_count}</span>
              </div>
              <p className="text-sm text-gray-600">{S.supporters}</p>
            </div>
          </div>

          {/* Bio */}
          {profile.bio && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                {S.about} {profile.display_name}
              </h2>
              <p className="text-gray-600 whitespace-pre-line">{profile.bio}</p>
            </div>
          )}

          {/* Social Links */}
          {socialEntries.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">{S.socialLinks}</h3>
              <div className="flex flex-wrap gap-2">
                {socialEntries.map(([key, url]) => (
                  <a
                    key={key}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {SOCIAL_LABELS[key] ?? key}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Impact Message + Support CTA */}
          <div className="bg-gradient-to-r from-pink-50 to-orange-50 rounded-xl p-6 text-center">
            <p className="text-gray-700 mb-4">{S.impactMessage(profile.display_name)}</p>
            <Link
              href={`/rescuers/${profile.slug}/support`}
              className="inline-flex items-center gap-2 bg-pink-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-pink-600 transition-colors"
            >
              <Heart className="h-5 w-5" />
              {S.supportButton(profile.display_name)}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
