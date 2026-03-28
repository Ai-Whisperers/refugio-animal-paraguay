"use client";

import { useEffect, useState, useCallback } from "react";
import { Users, Heart, Calendar, Share2, TrendingUp, BarChart3, Activity } from "lucide-react";

interface KPI { label: string; value: number; change_pct: number; trend: string; }
interface Overview { period_days: number; total_active_members: number; engagement_score: number; kpis: KPI[]; generated_at: string; }
interface VolunteerMetrics { total_volunteers: number; active_this_period: number; total_hours: number; avg_hours_per_volunteer: number; top_activities: { activity: string; hours: number; volunteers: number }[]; monthly_hours: { month: string; hours: number }[]; }
interface EventMetrics { total_events: number; total_attendees: number; avg_attendance: number; upcoming_events: number; events_by_type: { type: string; count: number; attendees: number }[]; monthly_events: { month: string; events: number; attendees: number }[]; }
interface SocialMetrics { total_followers: number; total_reach: number; engagement_rate: number; platforms: { platform: string; followers: number; reach: number; engagement: number }[]; monthly_reach: { month: string; reach: number }[]; }
interface ChannelEngagement { channel: string; label: string; score: number; active_users: number; interactions: number; trend: string; }

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TREND_COLORS: Record<string, string> = { up: "text-green-600", down: "text-red-600", stable: "text-gray-500" };
const TREND_ICONS: Record<string, string> = { up: "+", down: "-", stable: "~" };

function KPICard({ kpi }: { kpi: KPI }) {
  const fmt = kpi.value >= 10000 ? `${(kpi.value / 1000).toFixed(1)}K` : kpi.value.toLocaleString();
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-4 shadow-sm">
      <p className="text-sm text-[var(--color-text-secondary)]">{kpi.label}</p>
      <p className="mt-1 text-2xl font-bold text-[var(--color-text-primary)]">{fmt}</p>
      <p className={`mt-1 text-sm font-medium ${TREND_COLORS[kpi.trend] ?? "text-gray-500"}`}>
        {TREND_ICONS[kpi.trend]}{Math.abs(kpi.change_pct).toFixed(1)}%
      </p>
    </div>
  );
}

function VolunteerSection({ data }: { data: VolunteerMetrics | null }) {
  if (!data) return null;
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4"><Users className="h-5 w-5 text-[var(--color-primary)]" /><h2 className="text-lg font-semibold">Voluntarios</h2></div>
      <div className="grid grid-cols-2 gap-4 mb-4 md:grid-cols-4">
        <div><p className="text-sm text-[var(--color-text-secondary)]">Total</p><p className="text-xl font-bold">{data.total_volunteers}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Activos</p><p className="text-xl font-bold">{data.active_this_period}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Horas totales</p><p className="text-xl font-bold">{data.total_hours.toLocaleString()}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Promedio hrs/vol</p><p className="text-xl font-bold">{data.avg_hours_per_volunteer}</p></div>
      </div>
      <h3 className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">Principales actividades</h3>
      <div className="space-y-2">
        {data.top_activities.map((a, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span>{a.activity}</span>
            <span className="font-medium">{a.hours}h ({a.volunteers} vol.)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function EventSection({ data }: { data: EventMetrics | null }) {
  if (!data) return null;
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4"><Calendar className="h-5 w-5 text-[var(--color-secondary)]" /><h2 className="text-lg font-semibold">Eventos</h2></div>
      <div className="grid grid-cols-2 gap-4 mb-4 md:grid-cols-4">
        <div><p className="text-sm text-[var(--color-text-secondary)]">Total eventos</p><p className="text-xl font-bold">{data.total_events}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Asistentes</p><p className="text-xl font-bold">{data.total_attendees.toLocaleString()}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Promedio asist.</p><p className="text-xl font-bold">{data.avg_attendance.toFixed(0)}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Proximos</p><p className="text-xl font-bold">{data.upcoming_events}</p></div>
      </div>
      <h3 className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">Por tipo de evento</h3>
      <div className="space-y-2">
        {data.events_by_type.map((e, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span>{e.type}</span>
            <span className="font-medium">{e.count} eventos ({e.attendees} asist.)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SocialSection({ data }: { data: SocialMetrics | null }) {
  if (!data) return null;
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4"><Share2 className="h-5 w-5 text-blue-500" /><h2 className="text-lg font-semibold">Redes Sociales</h2></div>
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div><p className="text-sm text-[var(--color-text-secondary)]">Seguidores</p><p className="text-xl font-bold">{data.total_followers.toLocaleString()}</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Alcance</p><p className="text-xl font-bold">{(data.total_reach / 1000).toFixed(1)}K</p></div>
        <div><p className="text-sm text-[var(--color-text-secondary)]">Engagement</p><p className="text-xl font-bold">{data.engagement_rate}%</p></div>
      </div>
      <div className="space-y-2">
        {data.platforms.map((p, i) => (
          <div key={i} className="flex items-center justify-between text-sm rounded-lg bg-gray-50 px-3 py-2">
            <span className="font-medium">{p.platform}</span>
            <div className="flex gap-4">
              <span>{p.followers.toLocaleString()} seg.</span>
              <span>{p.engagement}% eng.</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EngagementSection({ data }: { data: ChannelEngagement[] | null }) {
  if (!data) return null;
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4"><Activity className="h-5 w-5 text-purple-500" /><h2 className="text-lg font-semibold">Engagement por Canal</h2></div>
      <div className="space-y-3">
        {data.map((ch, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">{ch.label}</span>
                <span className={`text-sm font-medium ${TREND_COLORS[ch.trend] ?? "text-gray-500"}`}>{ch.score.toFixed(0)}%</span>
              </div>
              <div className="h-2 rounded-full bg-gray-100">
                <div className="h-2 rounded-full bg-[var(--color-primary)]" style={{ width: `${ch.score}%` }} />
              </div>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">{ch.active_users.toLocaleString()} usuarios &middot; {ch.interactions.toLocaleString()} interacciones</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (<div className="space-y-4">{[1, 2, 3, 4].map((i) => (<div key={i} className="h-48 animate-pulse rounded-lg bg-gray-100" />))}</div>);
}

export default function CommunityAnalyticsPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [volunteers, setVolunteers] = useState<VolunteerMetrics | null>(null);
  const [events, setEvents] = useState<EventMetrics | null>(null);
  const [social, setSocial] = useState<SocialMetrics | null>(null);
  const [channels, setChannels] = useState<ChannelEngagement[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [ovRes, volRes, evRes, socRes, engRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/analytics/community/overview?period_days=${period}`),
        fetch(`${API_BASE}/api/admin/analytics/community/volunteers`),
        fetch(`${API_BASE}/api/admin/analytics/community/events`),
        fetch(`${API_BASE}/api/admin/analytics/community/social`),
        fetch(`${API_BASE}/api/admin/analytics/community/engagement`),
      ]);
      if (ovRes.ok) setOverview(await ovRes.json());
      if (volRes.ok) setVolunteers(await volRes.json());
      if (evRes.ok) setEvents(await evRes.json());
      if (socRes.ok) setSocial(await socRes.json());
      if (engRes.ok) { const d = await engRes.json(); setChannels(d.channels ?? []); }
    } catch { /* fail silently */ } finally { setLoading(false); }
  }, [period]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const periods = [{ value: 30, label: "30 dias" }, { value: 90, label: "90 dias" }, { value: 180, label: "6 meses" }, { value: 365, label: "1 ano" }];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Engagement Comunitario</h1>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Metricas de participacion y crecimiento de la comunidad</p>
        </div>
        <div className="flex gap-2">
          {periods.map((p) => (
            <button key={p.value} onClick={() => setPeriod(p.value)} className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${period === p.value ? "bg-[var(--color-primary)] text-white" : "bg-gray-100 text-[var(--color-text-secondary)] hover:bg-gray-200"}`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (<LoadingSkeleton />) : (
        <div className="space-y-6">
          {overview && (
            <div>
              <div className="mb-4 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-[var(--color-primary)]" />
                <h2 className="text-lg font-semibold">Resumen</h2>
                <span className="ml-auto rounded-full bg-[var(--color-primary)]/10 px-3 py-1 text-sm font-medium text-[var(--color-primary)]">
                  Score: {overview.engagement_score}%
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                {overview.kpis.map((kpi, i) => (<KPICard key={i} kpi={kpi} />))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <VolunteerSection data={volunteers} />
            <EventSection data={events} />
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <SocialSection data={social} />
            <EngagementSection data={channels} />
          </div>
        </div>
      )}
    </div>
  );
}
