"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  MapPin,
  Phone,
  Mail,
  AlertTriangle,
  Stethoscope,
  ArrowLeft,
  Heart,
  DollarSign,
  Users,
} from "lucide-react";
import { getClinicPublic, getClinicFundingStats } from "@/lib/public-api";
import type { PublicClinicDetail, ClinicFundingStats } from "@/types/api";

const S = {
  loading: "Cargando clinica...",
  notFound: "Clinica no encontrada.",
  backToList: "Volver a clinicas",
  emergencies: "Acepta emergencias",
  specialties: "Especialidades",
  services: "Servicios disponibles",
  noServices: "No hay servicios listados actualmente.",
  fundThisClinic: "Apoyar esta clinica",
  fundDescription: "Tu donacion ayuda a esta clinica a ofrecer servicios accesibles.",
  totalFunded: "Total recaudado",
  donations: "donaciones",
  contact: "Contacto",
  priceEur: (price: number) =>
    new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(price),
  category: (cat: string) => {
    const map: Record<string, string> = {
      consultation: "Consulta",
      vaccination: "Vacunacion",
      surgery: "Cirugia",
      dental: "Dental",
      diagnostic: "Diagnostico",
      grooming: "Estetica",
      emergency: "Emergencia",
      preventive: "Preventivo",
      other: "Otro",
    };
    return map[cat] ?? cat;
  },
} as const;

function formatEur(cents: number): string {
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
  }).format(cents / 100);
}

export default function ClinicDetailPage() {
  const params = useParams();
  const clinicId = params.id as string;

  const [clinic, setClinic] = useState<PublicClinicDetail | null>(null);
  const [stats, setStats] = useState<ClinicFundingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clinicId) return;
    let cancelled = false;
    setLoading(true);

    Promise.all([
      getClinicPublic(clinicId),
      getClinicFundingStats(clinicId),
    ])
      .then(([clinicData, statsData]) => {
        if (cancelled) return;
        setClinic(clinicData);
        setStats(statsData);
      })
      .catch(() => {
        if (!cancelled) setError(S.notFound);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [clinicId]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">{S.loading}</p>
      </main>
    );
  }

  if (error || !clinic) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-600">{error ?? S.notFound}</p>
        <Link href="/clinics" className="text-teal-600 hover:underline">
          {S.backToList}
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-gradient-to-r from-teal-600 to-teal-700 text-white py-10">
        <div className="max-w-4xl mx-auto px-4">
          <Link
            href="/clinics"
            className="inline-flex items-center gap-1 text-teal-200 hover:text-white text-sm mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            {S.backToList}
          </Link>
          <div className="flex items-start gap-4">
            <div className="bg-white/20 rounded-full p-3">
              <Stethoscope className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">{clinic.name}</h1>
              <div className="flex items-center gap-2 text-teal-100 mt-1">
                <MapPin className="h-4 w-4" />
                <span>
                  {clinic.city}
                  {clinic.department ? `, ${clinic.department}` : ""}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Stats + CTA */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats && (
            <>
              <div className="bg-white rounded-xl shadow-sm border p-5 text-center">
                <DollarSign className="h-6 w-6 text-teal-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {formatEur(stats.total_funded_cents)}
                </p>
                <p className="text-sm text-gray-500">{S.totalFunded}</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-5 text-center">
                <Users className="h-6 w-6 text-teal-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {stats.donation_count}
                </p>
                <p className="text-sm text-gray-500">{S.donations}</p>
              </div>
            </>
          )}
          <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl shadow-sm p-5 text-center text-white flex flex-col justify-center">
            <Heart className="h-6 w-6 mx-auto mb-2" />
            <Link
              href={`/clinics/${clinicId}/fund`}
              className="text-lg font-semibold hover:underline"
            >
              {S.fundThisClinic}
            </Link>
            <p className="text-teal-100 text-sm mt-1">{S.fundDescription}</p>
          </div>
        </div>

        {/* Info grid */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{S.contact}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <MapPin className="h-5 w-5 text-gray-400" />
              <span className="text-gray-700">{clinic.address}</span>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="h-5 w-5 text-gray-400" />
              <a href={`tel:${clinic.phone}`} className="text-teal-600 hover:underline">
                {clinic.phone}
              </a>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-gray-400" />
              <a href={`mailto:${clinic.email}`} className="text-teal-600 hover:underline">
                {clinic.email}
              </a>
            </div>
            {clinic.accepts_emergencies && (
              <div className="flex items-center gap-3 text-orange-600">
                <AlertTriangle className="h-5 w-5" />
                <span>{S.emergencies}</span>
              </div>
            )}
          </div>

          {clinic.specialties && (
            <div className="mt-4">
              <span className="text-sm font-medium text-gray-500">{S.specialties}: </span>
              <span className="text-gray-700">{clinic.specialties}</span>
            </div>
          )}
        </div>

        {/* Services */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{S.services}</h2>
          {clinic.services.length === 0 ? (
            <p className="text-gray-500">{S.noServices}</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {clinic.services.map((svc) => (
                <div
                  key={svc.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-teal-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium text-gray-900">{svc.name}</h3>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                      {S.category(svc.category)}
                    </span>
                  </div>
                  {svc.description && (
                    <p className="text-sm text-gray-500 mb-2">{svc.description}</p>
                  )}
                  {svc.price_eur !== null && (
                    <p className="text-sm font-semibold text-teal-600">
                      {S.priceEur(svc.price_eur)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
