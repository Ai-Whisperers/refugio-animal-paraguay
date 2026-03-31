"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Trophy,
  ArrowLeft,
  RefreshCw,
  Medal,
  Clock,
  Users,
  Star,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { LeaderboardEntry, LeaderboardPeriod, LeaderboardResponse } from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Tabla de Honor — Voluntarios";
const LABEL_LOADING = "Cargando tabla de honor...";
const LABEL_ERROR = "Error al cargar la tabla de honor";
const LABEL_EMPTY = "Aún no hay voluntarios con horas registradas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a voluntarios";
const LABEL_REFRESH = "Actualizar";
const LABEL_RANK = "Puesto";
const LABEL_NAME = "Voluntario";
const LABEL_HOURS = "Horas";
const LABEL_SKILLS = "Habilidades";
const LABEL_TOTAL_VOLUNTEERS = "Total de voluntarios aprobados";
const LABEL_LIMIT = "Mostrar top";

const PERIOD_LABELS: Record<LeaderboardPeriod, string> = {
  all: "Todos los tiempos",
  month: "Este mes",
  quarter: "Este trimestre",
  year: "Este año",
};

const LIMIT_OPTIONS = [5, 10, 25, 50];
const PERIOD_OPTIONS: LeaderboardPeriod[] = ["all", "month", "quarter", "year"];

// --- Medal colours for top 3 ---
function RankBadge({ rank }: { rank: number }) {
  if (rank === 1)
    return (
      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-yellow-400 text-white font-bold text-sm">
        <Trophy className="h-4 w-4" />
      </span>
    );
  if (rank === 2)
    return (
      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-300 text-white font-bold text-sm">
        <Medal className="h-4 w-4" />
      </span>
    );
  if (rank === 3)
    return (
      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-amber-600 text-white font-bold text-sm">
        <Star className="h-4 w-4" />
      </span>
    );
  return (
    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-600 font-semibold text-sm">
      {rank}
    </span>
  );
}

export default function VolunteerLeaderboardPage() {
  const router = useRouter();
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<LeaderboardPeriod>("all");
  const [limit, setLimit] = useState(10);

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<LeaderboardResponse>(
        `/api/staff/volunteers/leaderboard?period=${period}&limit=${limit}`
      );
      setData(response);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message ?? LABEL_ERROR);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [period, limit]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    fetchLeaderboard();
  }, [fetchLeaderboard, router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/volunteers")}
              className="text-gray-500 hover:text-gray-700 flex items-center gap-1 text-sm"
            >
              <ArrowLeft className="h-4 w-4" />
              {LABEL_BACK}
            </button>
          </div>
          <button
            onClick={fetchLeaderboard}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <Trophy className="h-8 w-8 text-yellow-500" />
          <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6 flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-400" />
            <label className="text-sm font-medium text-gray-700">Período</label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as LeaderboardPeriod)}
              className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-emerald-500"
            >
              {PERIOD_OPTIONS.map((p) => (
                <option key={p} value={p}>
                  {PERIOD_LABELS[p]}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-gray-400" />
            <label className="text-sm font-medium text-gray-700">{LABEL_LIMIT}</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:ring-2 focus:ring-emerald-500"
            >
              {LIMIT_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          {data && (
            <div className="ml-auto text-sm text-gray-500">
              {LABEL_TOTAL_VOLUNTEERS}:{" "}
              <span className="font-semibold text-gray-700">{data.total_approved_volunteers}</span>
            </div>
          )}
        </div>

        {/* Content */}
        {loading && (
          <div className="text-center py-16 text-gray-400">
            <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin" />
            <p>{LABEL_LOADING}</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-700 mb-3">{error}</p>
            <button
              onClick={fetchLeaderboard}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {!loading && !error && data && data.entries.length === 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-400">
            <Trophy className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="text-lg">{LABEL_EMPTY}</p>
          </div>
        )}

        {!loading && !error && data && data.entries.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-16">
                    {LABEL_RANK}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {LABEL_NAME}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {LABEL_SKILLS}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider w-28">
                    {LABEL_HOURS}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.entries.map((entry: LeaderboardEntry) => (
                  <tr
                    key={entry.volunteer_id}
                    className={`hover:bg-gray-50 transition-colors ${entry.rank <= 3 ? "bg-amber-50/40" : ""}`}
                  >
                    <td className="px-4 py-3">
                      <RankBadge rank={entry.rank} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">
                        {entry.full_name ?? entry.email}
                      </div>
                      {entry.full_name && (
                        <div className="text-xs text-gray-400">{entry.email}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {entry.skills.slice(0, 3).map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-emerald-100 text-emerald-700"
                          >
                            {skill}
                          </span>
                        ))}
                        {entry.skills.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{entry.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-semibold text-gray-900">
                        {entry.total_hours_logged.toFixed(1)}
                      </span>
                      <span className="text-xs text-gray-400 ml-1">h</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
