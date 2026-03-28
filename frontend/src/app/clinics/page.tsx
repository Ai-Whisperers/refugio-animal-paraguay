"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MapPin, Phone, AlertTriangle, Stethoscope, ChevronLeft, ChevronRight } from "lucide-react";
import { listClinicsPublic } from "@/lib/public-api";
import type { PublicClinicSummary } from "@/types/api";

const S = {
  title: "Clinicas Veterinarias Asociadas",
  subtitle: "Conoce las clinicas veterinarias que trabajan con nosotros para brindar atencion accesible.",
  filterByCity: "Filtrar por ciudad",
  emergencies: "Acepta emergencias",
  specialties: "Especialidades",
  fundClinic: "Apoyar esta clinica",
  noResults: "No se encontraron clinicas activas.",
  loading: "Cargando clinicas...",
  error: "Error al cargar las clinicas. Intente de nuevo.",
  previous: "Anterior",
  next: "Siguiente",
  page: (current: number, total: number) => `Pagina ${current} de ${total}`,
} as const;

const PAGE_SIZE = 12;

export default function ClinicsListPage() {
  const [clinics, setClinics] = useState<PublicClinicSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [city, setCity] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listClinicsPublic(city || undefined, page, PAGE_SIZE)
      .then((res) => {
        if (cancelled) return;
        setClinics(res.items);
        setTotal(res.total);
      })
      .catch(() => {
        if (cancelled) return;
        setError(S.error);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, city]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <section className="bg-gradient-to-r from-teal-600 to-teal-700 text-white py-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <Stethoscope className="h-12 w-12 mx-auto mb-4 opacity-80" />
          <h1 className="text-3xl font-bold mb-3">{S.title}</h1>
          <p className="text-teal-100 max-w-2xl mx-auto">{S.subtitle}</p>
        </div>
      </section>

      {/* Filter */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <input
          type="text"
          placeholder={S.filterByCity}
          value={city}
          onChange={(e) => {
            setCity(e.target.value);
            setPage(1);
          }}
          className="w-full max-w-sm px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        />
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 pb-12">
        {loading && (
          <p className="text-center text-gray-500 py-12">{S.loading}</p>
        )}

        {error && (
          <p className="text-center text-red-600 py-12">{error}</p>
        )}

        {!loading && !error && clinics.length === 0 && (
          <p className="text-center text-gray-500 py-12">{S.noResults}</p>
        )}

        {!loading && !error && clinics.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {clinics.map((clinic) => (
                <div
                  key={clinic.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    {clinic.name}
                  </h2>

                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <MapPin className="h-4 w-4 text-teal-500" />
                    <span>{clinic.city}{clinic.department ? `, ${clinic.department}` : ""}</span>
                  </div>

                  {clinic.accepts_emergencies && (
                    <div className="flex items-center gap-2 text-sm text-orange-600 mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span>{S.emergencies}</span>
                    </div>
                  )}

                  {clinic.specialties && (
                    <p className="text-sm text-gray-500 mb-4">
                      <span className="font-medium">{S.specialties}:</span>{" "}
                      {clinic.specialties}
                    </p>
                  )}

                  <Link
                    href={`/clinics/${clinic.id}`}
                    className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 font-medium text-sm"
                  >
                    {S.fundClinic}
                  </Link>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex items-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                  {S.previous}
                </button>
                <span className="text-sm text-gray-600">
                  {S.page(page, totalPages)}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="inline-flex items-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {S.next}
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
