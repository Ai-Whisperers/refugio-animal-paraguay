"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart2,
  ArrowLeft,
  RefreshCw,
  Users,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  XCircle,
  MinusCircle,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type {
  MonthlyCount,
  SkillFrequency,
  VolunteerAnalyticsResponse,
} from "@/types/api";

// --- Spanish labels ---
const LABEL_PAGE_TITLE = "Analítica del Programa de Voluntarios";
const LABEL_LOADING = "Cargando analítica...";
const LABEL_ERROR = "Error al cargar la analítica";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver a voluntarios";
const LABEL_REFRESH = "Actualizar";

const LABEL_TOTAL_VOLUNTEERS = "Total voluntarios";
const LABEL_APPROVED = "Aprobados";
const LABEL_PENDING = "Pendientes";
const LABEL_REJECTED = "Rechazados";
const LABEL_INACTIVE = "Inactivos";
const LABEL_TOTAL_HOURS = "Horas totales";
const LABEL_AVG_HOURS = "Promedio horas";
const LABEL_PER_VOLUNTEER = "por voluntario";

const LABEL_SKILLS_TITLE = "Distribución de habilidades";
const LABEL_JOINS_TITLE = "Nuevos voluntarios por mes";
const LABEL_NO_SKILLS = "Sin datos de habilidades";
const LABEL_NO_JOINS = "Sin datos de actividad reciente";

const MONTH_NAMES = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun",
  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
];

const SKILL_LABELS: Record<string, string> = {
  animal_care: "Cuidado animal",
  veterinary_assistance: "Asistencia veterinaria",
  photography: "Fotografía",
  social_media: "Redes sociales",
  transport_driving: "Transporte",
  fundraising: "Recaudación de fondos",
  admin_office: "Administración",
  cleaning: "Limpieza",
  construction_maintenance: "Mantenimiento",
  education_outreach: "Educación",
  translation: "Traducción",
  web_tech: "Web / Tecnología",
  event_coordination: "Coordinación de eventos",
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 flex items-start gap-4">
      <div className={`rounded-full p-2 ${color}`}>{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function StatusCard({
  icon,
  label,
  count,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div className={`rounded-lg border p-4 flex items-center gap-3 ${color}`}>
      {icon}
      <div>
        <p className="text-xs font-medium">{label}</p>
        <p className="text-xl font-bold">{count}</p>
      </div>
    </div>
  );
}

function SkillsChart({ skills }: { skills: SkillFrequency[] }) {
  if (skills.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-8">{LABEL_NO_SKILLS}</p>
    );
  }
  const max = skills[0].count;
  return (
    <div className="space-y-2">
      {skills.map(({ skill, count }) => (
        <div key={skill} className="flex items-center gap-3">
          <span className="text-xs text-gray-600 w-44 shrink-0 truncate">
            {SKILL_LABELS[skill] ?? skill}
          </span>
          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
            <div
              className="h-3 rounded-full bg-emerald-500 transition-all"
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-gray-700 w-6 text-right">
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}

function MonthlyJoinsChart({ data }: { data: MonthlyCount[] }) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-8">{LABEL_NO_JOINS}</p>
    );
  }
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div className="flex items-end gap-3 h-32">
      {data.map(({ year, month, count }) => (
        <div
          key={`${year}-${month}`}
          className="flex-1 flex flex-col items-center gap-1"
        >
          <span className="text-xs font-semibold text-gray-700">{count > 0 ? count : ""}</span>
          <div className="w-full bg-gray-100 rounded-t-sm overflow-hidden flex items-end" style={{ height: "80px" }}>
            <div
              className="w-full bg-emerald-400 rounded-t-sm transition-all"
              style={{ height: `${(count / max) * 80}px` }}
            />
          </div>
          <span className="text-xs text-gray-400">{MONTH_NAMES[month - 1]}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function VolunteerAnalyticsPage() {
  const router = useRouter();
  const [data, setData] = useState<VolunteerAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<VolunteerAnalyticsResponse>(
        "/api/staff/volunteers/analytics"
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
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    fetchAnalytics();
  }, [fetchAnalytics, router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => router.push("/admin/volunteers")}
            className="text-gray-500 hover:text-gray-700 flex items-center gap-1 text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            {LABEL_BACK}
          </button>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {LABEL_REFRESH}
          </button>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <BarChart2 className="h-8 w-8 text-emerald-600" />
          <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
        </div>

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
              onClick={fetchAnalytics}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {!loading && !error && data && (
          <div className="space-y-6">
            {/* KPI cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <KpiCard
                icon={<Users className="h-5 w-5 text-emerald-600" />}
                label={LABEL_TOTAL_VOLUNTEERS}
                value={data.total_volunteers}
                color="bg-emerald-50"
              />
              <KpiCard
                icon={<Clock className="h-5 w-5 text-blue-600" />}
                label={LABEL_TOTAL_HOURS}
                value={data.total_hours_logged.toFixed(1) + " h"}
                color="bg-blue-50"
              />
              <KpiCard
                icon={<TrendingUp className="h-5 w-5 text-amber-600" />}
                label={LABEL_AVG_HOURS}
                value={data.avg_hours_per_volunteer.toFixed(1) + " h"}
                sub={LABEL_PER_VOLUNTEER}
                color="bg-amber-50"
              />
            </div>

            {/* Status breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatusCard
                icon={<CheckCircle className="h-5 w-5 text-emerald-600" />}
                label={LABEL_APPROVED}
                count={data.total_approved}
                color="bg-emerald-50 border-emerald-200 text-emerald-800"
              />
              <StatusCard
                icon={<AlertCircle className="h-5 w-5 text-amber-600" />}
                label={LABEL_PENDING}
                count={data.total_pending}
                color="bg-amber-50 border-amber-200 text-amber-800"
              />
              <StatusCard
                icon={<XCircle className="h-5 w-5 text-red-500" />}
                label={LABEL_REJECTED}
                count={data.total_rejected}
                color="bg-red-50 border-red-200 text-red-800"
              />
              <StatusCard
                icon={<MinusCircle className="h-5 w-5 text-gray-500" />}
                label={LABEL_INACTIVE}
                count={data.total_inactive}
                color="bg-gray-50 border-gray-200 text-gray-700"
              />
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">
                  {LABEL_SKILLS_TITLE}
                </h2>
                <SkillsChart skills={data.skills_distribution} />
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">
                  {LABEL_JOINS_TITLE}
                </h2>
                <MonthlyJoinsChart data={data.monthly_joins} />
              </div>
            </div>

            <p className="text-xs text-gray-400 text-right">
              Generado: {data.generated_at}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
