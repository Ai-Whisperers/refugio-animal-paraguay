"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Heart, Stethoscope, Building2, PawPrint } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ServiceBreakdown {
  category: string;
  count: number;
}

interface TopClinic {
  clinic_name: string;
  city: string | null;
  voucher_count: number;
}

interface VoucherStatistics {
  total_vouchers_purchased: number;
  total_vouchers_redeemed: number;
  total_animals_treated: number;
  active_clinics: number;
  total_donated_eur: number;
  total_donated_pyg: number;
  service_breakdown: ServiceBreakdown[];
  top_clinics: TopClinic[];
  last_updated: string;
}

interface RecentRedemption {
  voucher_code: string;
  service_category: string | null;
  clinic_name: string | null;
  redeemed_at: string | null;
  amount_pyg: number;
}

function StatCard({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode;
  value: string;
  label: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-md p-6 text-center">
      <div className="flex justify-center mb-3 text-primary-600">{icon}</div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function ServiceBar({
  category,
  count,
  maxCount,
}: {
  category: string;
  count: number;
  maxCount: number;
}) {
  const widthPct = maxCount > 0 ? (count / maxCount) * 100 : 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700 font-medium">{category}</span>
        <span className="text-gray-500">{count}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div
          className="bg-primary-500 h-3 rounded-full transition-all duration-700"
          style={{ width: `${widthPct}%` }}
        />
      </div>
    </div>
  );
}

export default function VoucherImpactPage() {
  const [stats, setStats] = useState<VoucherStatistics | null>(null);
  const [recent, setRecent] = useState<RecentRedemption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, recentRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/public/vouchers/statistics`),
          fetch(`${API_BASE_URL}/api/public/vouchers/recent`),
        ]);

        if (!statsRes.ok || !recentRes.ok) {
          throw new Error("No se pudieron cargar las estadisticas");
        }

        const statsData = await statsRes.json();
        const recentData = await recentRes.json();

        setStats(statsData);
        setRecent(recentData.items || []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Error al cargar datos"
        );
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-lg text-gray-600 mb-4">
            {error ?? "No se pudieron cargar las estadisticas."}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const maxServiceCount = Math.max(
    ...stats.service_breakdown.map((s) => s.count),
    1
  );

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-green-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            Impacto del Programa de Vouchers
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Gracias a nuestros donantes, los animales reciben la atencion
            veterinaria que necesitan.
          </p>
          <p className="text-5xl sm:text-6xl font-bold text-primary-600 mt-8">
            {stats.total_vouchers_purchased.toLocaleString()}
          </p>
          <p className="text-lg text-gray-500 mt-2">Vouchers Comprados</p>
        </div>
      </section>

      {/* Stats Cards */}
      <section className="py-10 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
          <StatCard
            icon={<PawPrint className="w-8 h-8" />}
            value={stats.total_animals_treated.toLocaleString()}
            label="Animales Atendidos"
          />
          <StatCard
            icon={<Building2 className="w-8 h-8" />}
            value={stats.active_clinics.toLocaleString()}
            label="Clinicas Asociadas"
          />
          <StatCard
            icon={<Heart className="w-8 h-8" />}
            value={`EUR ${stats.total_donated_eur.toLocaleString()}`}
            label="Donado en Vouchers"
          />
          <StatCard
            icon={<Stethoscope className="w-8 h-8" />}
            value={stats.total_vouchers_redeemed.toLocaleString()}
            label="Vouchers Canjeados"
          />
        </div>
      </section>

      {/* Service Breakdown */}
      {stats.service_breakdown.length > 0 && (
        <section className="py-10 px-4 bg-gray-50">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-heading font-bold text-gray-900 mb-6 text-center">
              Servicios Realizados
            </h2>
            <div className="bg-white rounded-xl shadow-md p-6">
              {stats.service_breakdown.map((s) => (
                <ServiceBar
                  key={s.category}
                  category={s.category}
                  count={s.count}
                  maxCount={maxServiceCount}
                />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Top Clinics */}
      {stats.top_clinics.length > 0 && (
        <section className="py-10 px-4 bg-white">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-heading font-bold text-gray-900 mb-6 text-center">
              Clinicas Destacadas
            </h2>
            <div className="grid gap-4">
              {stats.top_clinics.map((clinic, idx) => (
                <div
                  key={clinic.clinic_name}
                  className="flex items-center justify-between bg-gray-50 rounded-lg p-4"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-primary-600 w-8">
                      #{idx + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {clinic.clinic_name}
                      </p>
                      {clinic.city && (
                        <p className="text-sm text-gray-500">{clinic.city}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-600">
                    {clinic.voucher_count} vouchers
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Recent Redemptions */}
      {recent.length > 0 && (
        <section className="py-10 px-4 bg-gray-50">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-heading font-bold text-gray-900 mb-6 text-center">
              Canjes Recientes
            </h2>
            <div className="space-y-3">
              {recent.map((r) => (
                <div
                  key={r.voucher_code}
                  className="bg-white rounded-lg p-4 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {r.service_category ?? "Servicio veterinario"}
                    </p>
                    <p className="text-sm text-gray-500">
                      {r.clinic_name ?? "Clinica"} &middot;{" "}
                      {r.redeemed_at
                        ? new Date(r.redeemed_at).toLocaleDateString("es-PY")
                        : ""}
                    </p>
                  </div>
                  <span className="text-sm font-medium text-primary-600">
                    {r.amount_pyg.toLocaleString()} PYG
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="py-12 px-4 bg-primary-600 text-white text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold mb-4">
            Ayuda a Mas Animales
          </h2>
          <p className="text-primary-100 mb-6">
            Compra un voucher veterinario y ayuda directamente a un animal que
            lo necesita.
          </p>
          <Link
            href="/donate"
            className="inline-block bg-white text-primary-600 font-semibold px-8 py-3 rounded-lg hover:bg-primary-50 transition-colors"
          >
            Donar Ahora
          </Link>
        </div>
      </section>
    </div>
  );
}
