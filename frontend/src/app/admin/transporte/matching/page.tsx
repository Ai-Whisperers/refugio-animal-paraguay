"use client";

import { useEffect, useState } from "react";

// -- Types ---------------------------------------------------------------

interface ScoreBreakdown {
  vehicle: number;
  proximity: number;
  rating: number;
  urgency: number;
}

interface DriverMatch {
  match_id: string;
  request_id: string;
  driver_id: string;
  driver_name: string;
  vehicle_type: string;
  score: number;
  score_tier: string;
  distance_km: number;
  estimated_time_min: number;
  status: string;
  notified_at: string | null;
  responded_at: string | null;
  score_breakdown: ScoreBreakdown;
}

interface MatchResult {
  request_id: string;
  matches_found: number;
  matches: DriverMatch[];
  search_radius_km: number;
  urgency: string;
  matched_at: string;
}

interface MatchingStats {
  total_matches_created: number;
  matches_accepted: number;
  matches_declined: number;
  matches_expired: number;
  average_score: number;
  acceptance_rate_pct: number;
  top_zones: { zone: string; matches: number }[];
  busiest_days: { day: string; requests: number }[];
}

// -- Helpers -------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

function scoreTierColor(tier: string): string {
  switch (tier) {
    case "excellent":
      return "bg-green-100 text-green-800";
    case "good":
      return "bg-blue-100 text-blue-800";
    case "fair":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-red-100 text-red-800";
  }
}

function statusColor(status: string): string {
  switch (status) {
    case "accepted":
      return "bg-green-100 text-green-800";
    case "notified":
      return "bg-blue-100 text-blue-800";
    case "pending":
      return "bg-gray-100 text-gray-800";
    case "declined":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  notified: "Notificado",
  accepted: "Aceptado",
  declined: "Rechazado",
  expired: "Expirado",
  cancelled: "Cancelado",
};

const VEHICLE_LABELS: Record<string, string> = {
  car: "Auto",
  suv: "SUV",
  van: "Camioneta",
  truck: "Camion",
  motorcycle: "Moto",
};

// -- Sub-components ------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse" aria-busy="true" aria-label="Cargando matching">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-32 bg-gray-200 rounded-xl" />
      ))}
    </div>
  );
}

function StatsSection({ stats }: { stats: MatchingStats }) {
  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Estadisticas de matching</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{stats.total_matches_created}</p>
          <p className="text-sm text-gray-500">Total matches</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">{stats.matches_accepted}</p>
          <p className="text-sm text-gray-500">Aceptados</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">{stats.matches_declined}</p>
          <p className="text-sm text-gray-500">Rechazados</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-[var(--color-primary)]">
            {stats.acceptance_rate_pct}%
          </p>
          <p className="text-sm text-gray-500">Tasa aceptacion</p>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Zonas mas activas</h3>
          {stats.top_zones.map((z) => (
            <div key={z.zone} className="flex justify-between text-sm py-1">
              <span className="text-gray-600">{z.zone}</span>
              <span className="font-medium text-gray-900">{z.matches}</span>
            </div>
          ))}
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Dias mas ocupados</h3>
          {stats.busiest_days.map((d) => (
            <div key={d.day} className="flex justify-between text-sm py-1">
              <span className="text-gray-600">{d.day}</span>
              <span className="font-medium text-gray-900">{d.requests} solicitudes</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function MatchCard({
  match,
  onAccept,
  onDecline,
  onNotify,
}: {
  match: DriverMatch;
  onAccept: (id: string) => void;
  onDecline: (id: string) => void;
  onNotify: (id: string) => void;
}) {
  const canRespond = match.status === "pending" || match.status === "notified";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{match.driver_name}</h3>
          <p className="text-sm text-gray-500">
            {VEHICLE_LABELS[match.vehicle_type] ?? match.vehicle_type} | {match.distance_km} km |{" "}
            ~{match.estimated_time_min} min
          </p>
        </div>
        <div className="flex gap-2">
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${scoreTierColor(match.score_tier)}`}
          >
            {match.score}pts
          </span>
          <span
            className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor(match.status)}`}
          >
            {STATUS_LABELS[match.status] ?? match.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 mb-3">
        {Object.entries(match.score_breakdown).map(([key, val]) => (
          <div key={key} className="text-center">
            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--color-primary)] rounded-full"
                style={{ width: `${(val / 30) * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1 capitalize">{key}</p>
          </div>
        ))}
      </div>

      {canRespond && (
        <div className="flex gap-2">
          {match.status === "pending" && (
            <button
              onClick={() => onNotify(match.match_id)}
              className="flex-1 px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
            >
              Notificar
            </button>
          )}
          <button
            onClick={() => onAccept(match.match_id)}
            className="flex-1 px-3 py-2 text-sm bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors"
          >
            Aceptar
          </button>
          <button
            onClick={() => onDecline(match.match_id)}
            className="flex-1 px-3 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
          >
            Rechazar
          </button>
        </div>
      )}
    </div>
  );
}

// -- Main page -----------------------------------------------------------

export default function RequestMatchingPage() {
  const [stats, setStats] = useState<MatchingStats | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [requestId, setRequestId] = useState("req-demo-001");
  const [vehicleType, setVehicleType] = useState("car");
  const [urgency, setUrgency] = useState("normal");

  useEffect(() => {
    fetchJSON<MatchingStats>("/api/transport/matching/stats")
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async () => {
    setSearching(true);
    try {
      const result = await fetchJSON<MatchResult>("/api/transport/matching/find", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: requestId,
          pickup_zone: "Asuncion Centro",
          dropoff_zone: "San Lorenzo",
          vehicle_needed: vehicleType,
          urgency,
          animal_count: 1,
        }),
      });
      setMatchResult(result);
    } catch {
      /* handled by UI */
    } finally {
      setSearching(false);
    }
  };

  const handleAccept = async (matchId: string) => {
    try {
      await fetchJSON(`/api/transport/matching/${matchId}/accept`, { method: "POST" });
      if (matchResult) {
        setMatchResult({
          ...matchResult,
          matches: matchResult.matches.map((m) =>
            m.match_id === matchId ? { ...m, status: "accepted" } : m
          ),
        });
      }
    } catch {
      /* handled */
    }
  };

  const handleDecline = async (matchId: string) => {
    try {
      await fetchJSON(`/api/transport/matching/${matchId}/decline`, { method: "POST" });
      if (matchResult) {
        setMatchResult({
          ...matchResult,
          matches: matchResult.matches.map((m) =>
            m.match_id === matchId ? { ...m, status: "declined" } : m
          ),
        });
      }
    } catch {
      /* handled */
    }
  };

  const handleNotify = async (matchId: string) => {
    try {
      await fetchJSON("/api/transport/matching/notify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request_id: requestId, match_ids: [matchId] }),
      });
      if (matchResult) {
        setMatchResult({
          ...matchResult,
          matches: matchResult.matches.map((m) =>
            m.match_id === matchId ? { ...m, status: "notified" } : m
          ),
        });
      }
    } catch {
      /* handled */
    }
  };

  if (loading) return <LoadingSkeleton />;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Matching de transporte</h1>
        <p className="text-gray-500 mt-1">
          Buscar conductores disponibles para solicitudes de transporte
        </p>
      </div>

      {stats && <StatsSection stats={stats} />}

      <section className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Buscar conductores</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label htmlFor="requestId" className="block text-sm font-medium text-gray-700 mb-1">
              ID de solicitud
            </label>
            <input
              id="requestId"
              type="text"
              value={requestId}
              onChange={(e) => setRequestId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label htmlFor="vehicleType" className="block text-sm font-medium text-gray-700 mb-1">
              Vehiculo necesario
            </label>
            <select
              id="vehicleType"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="car">Auto</option>
              <option value="suv">SUV</option>
              <option value="van">Camioneta</option>
              <option value="truck">Camion</option>
            </select>
          </div>
          <div>
            <label htmlFor="urgency" className="block text-sm font-medium text-gray-700 mb-1">
              Urgencia
            </label>
            <select
              id="urgency"
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="low">Baja</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
              <option value="emergency">Emergencia</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-6 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors disabled:opacity-50"
        >
          {searching ? "Buscando..." : "Buscar conductores"}
        </button>
      </section>

      {matchResult && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {matchResult.matches_found} conductores encontrados
          </h2>
          <div className="space-y-3">
            {matchResult.matches.map((match) => (
              <MatchCard
                key={match.match_id}
                match={match}
                onAccept={handleAccept}
                onDecline={handleDecline}
                onNotify={handleNotify}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
