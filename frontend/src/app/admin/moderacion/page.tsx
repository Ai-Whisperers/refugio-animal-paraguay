"use client";

import { useState, useEffect, useCallback } from "react";

// -- Types ------------------------------------------------------------------

interface RescuerInfo {
  id: string;
  name: string;
  email: string;
  status: string;
  verification_status: string;
  animal_count: number;
  supporter_count: number;
  flag_count: number;
  registered_at: string;
  last_active: string;
  location: string;
}

interface CampaignInfo {
  id: string;
  title: string;
  rescuer_name: string;
  description: string;
  goal_amount: number;
  currency: string;
  status: string;
  created_at: string;
  rescuer_verified: boolean;
}

interface FlagInfo {
  id: string;
  content_type: string;
  content_id: string;
  flagged_by: string;
  reason: string;
  details: string;
  status: string;
  created_at: string;
}

interface LogEntry {
  id: string;
  action: string;
  target_type: string;
  target_name: string;
  reason: string;
  timestamp: string;
}

// -- API helpers ------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

// -- Sub-components ---------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 bg-gray-200 rounded-lg" />
      ))}
    </div>
  );
}

function StatusBadge({ status, type }: { status: string; type: "account" | "verification" | "campaign" | "flag" }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    suspended: "bg-red-100 text-red-800",
    pending: "bg-yellow-100 text-yellow-800",
    verified: "bg-blue-100 text-blue-800",
    unverified: "bg-gray-100 text-gray-800",
    under_review: "bg-orange-100 text-orange-800",
    approved: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
    open: "bg-red-100 text-red-800",
    reviewed: "bg-blue-100 text-blue-800",
    dismissed: "bg-gray-100 text-gray-600",
    action_taken: "bg-purple-100 text-purple-800",
  };

  const label = status.replace(/_/g, " ");

  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${colors[status] ?? "bg-gray-100 text-gray-700"}`}>
      {type === "verification" ? `${label}` : label}
    </span>
  );
}

function RescuerRow({ rescuer }: { rescuer: RescuerInfo }) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="py-3 px-4">
        <div className="font-medium text-gray-900">{rescuer.name}</div>
        <div className="text-sm text-gray-500">{rescuer.email}</div>
      </td>
      <td className="py-3 px-4">
        <StatusBadge status={rescuer.status} type="account" />
      </td>
      <td className="py-3 px-4">
        <StatusBadge status={rescuer.verification_status} type="verification" />
      </td>
      <td className="py-3 px-4 text-center">{rescuer.animal_count}</td>
      <td className="py-3 px-4 text-center">{rescuer.supporter_count}</td>
      <td className="py-3 px-4 text-center">
        {rescuer.flag_count > 0 ? (
          <span className="text-red-600 font-medium">{rescuer.flag_count}</span>
        ) : (
          <span className="text-gray-400">0</span>
        )}
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">{rescuer.location}</td>
      <td className="py-3 px-4">
        <div className="flex gap-1">
          <button className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors">
            Verificar
          </button>
          <button className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors">
            Suspender
          </button>
        </div>
      </td>
    </tr>
  );
}

function CampaignCard({ campaign }: { campaign: CampaignInfo }) {
  const amount = new Intl.NumberFormat("es-PY").format(campaign.goal_amount);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-medium text-gray-900">{campaign.title}</h3>
        <StatusBadge status={campaign.status} type="campaign" />
      </div>
      <p className="text-sm text-gray-600 mb-3">{campaign.description}</p>
      <div className="flex items-center justify-between text-sm">
        <div>
          <span className="text-gray-500">Por: </span>
          <span className="font-medium">{campaign.rescuer_name}</span>
          {campaign.rescuer_verified && (
            <span className="ml-1 text-blue-600" title="Verificado">&#10003;</span>
          )}
        </div>
        <div className="font-medium">
          {amount} {campaign.currency}
        </div>
      </div>
      {campaign.status === "pending" && (
        <div className="mt-3 flex gap-2">
          <button className="flex-1 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors">
            Aprobar
          </button>
          <button className="flex-1 px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors">
            Rechazar
          </button>
        </div>
      )}
    </div>
  );
}

function FlagRow({ flag }: { flag: FlagInfo }) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="py-3 px-4 text-sm capitalize">{flag.content_type}</td>
      <td className="py-3 px-4 text-sm font-mono text-gray-600">{flag.content_id}</td>
      <td className="py-3 px-4">
        <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 capitalize">
          {flag.reason}
        </span>
      </td>
      <td className="py-3 px-4 text-sm text-gray-600 max-w-xs truncate">{flag.details}</td>
      <td className="py-3 px-4">
        <StatusBadge status={flag.status} type="flag" />
      </td>
      <td className="py-3 px-4">
        {flag.status === "open" && (
          <div className="flex gap-1">
            <button className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors">
              Descartar
            </button>
            <button className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors">
              Accion
            </button>
          </div>
        )}
      </td>
    </tr>
  );
}

// -- Tabs -------------------------------------------------------------------

type TabId = "rescuers" | "campaigns" | "flags" | "history";

const TABS: { id: TabId; label: string }[] = [
  { id: "rescuers", label: "Rescatistas" },
  { id: "campaigns", label: "Campanas" },
  { id: "flags", label: "Reportes" },
  { id: "history", label: "Historial" },
];

// -- Main page --------------------------------------------------------------

export default function AdminModerationPage() {
  const [activeTab, setActiveTab] = useState<TabId>("rescuers");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [rescuers, setRescuers] = useState<RescuerInfo[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignInfo[]>([]);
  const [flags, setFlags] = useState<FlagInfo[]>([]);
  const [history, setHistory] = useState<LogEntry[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);

      if (activeTab === "rescuers") {
        const data = await fetchJSON<{ rescuers: RescuerInfo[] }>(
          `${API}/api/admin/moderation/rescuers?${params}`
        );
        setRescuers(data.rescuers);
      } else if (activeTab === "campaigns") {
        const data = await fetchJSON<{ campaigns: CampaignInfo[] }>(
          `${API}/api/admin/moderation/campaigns?${params}`
        );
        setCampaigns(data.campaigns);
      } else if (activeTab === "flags") {
        const data = await fetchJSON<{ flags: FlagInfo[] }>(
          `${API}/api/admin/moderation/flags?${params}`
        );
        setFlags(data.flags);
      } else {
        const data = await fetchJSON<{ entries: LogEntry[] }>(
          `${API}/api/admin/moderation/history`
        );
        setHistory(data.entries);
      }
    } catch {
      /* API not yet connected */
    } finally {
      setLoading(false);
    }
  }, [activeTab, search, statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Moderacion</h1>
        <p className="text-gray-600 mt-1">
          Gestionar rescatistas, campanas y contenido reportado
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setStatusFilter(""); }}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      {activeTab !== "history" && (
        <div className="flex flex-wrap gap-3 mb-6">
          {activeTab === "rescuers" && (
            <>
              <input
                type="text"
                placeholder="Buscar por nombre o email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">Todos los estados</option>
                <option value="active">Activo</option>
                <option value="suspended">Suspendido</option>
                <option value="pending">Pendiente</option>
              </select>
            </>
          )}
          {activeTab === "campaigns" && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Todas las campanas</option>
              <option value="pending">Pendientes</option>
              <option value="approved">Aprobadas</option>
              <option value="rejected">Rechazadas</option>
            </select>
          )}
          {activeTab === "flags" && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Todos los reportes</option>
              <option value="open">Abiertos</option>
              <option value="reviewed">Revisados</option>
              <option value="dismissed">Descartados</option>
            </select>
          )}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <LoadingSkeleton />
      ) : (
        <>
          {/* Rescuers tab */}
          {activeTab === "rescuers" && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Rescatista</th>
                    <th className="py-3 px-4">Estado</th>
                    <th className="py-3 px-4">Verificacion</th>
                    <th className="py-3 px-4 text-center">Animales</th>
                    <th className="py-3 px-4 text-center">Apoyos</th>
                    <th className="py-3 px-4 text-center">Reportes</th>
                    <th className="py-3 px-4">Ubicacion</th>
                    <th className="py-3 px-4">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {rescuers.map((r) => (
                    <RescuerRow key={r.id} rescuer={r} />
                  ))}
                  {rescuers.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-gray-500">
                        No se encontraron rescatistas
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Campaigns tab */}
          {activeTab === "campaigns" && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {campaigns.map((c) => (
                <CampaignCard key={c.id} campaign={c} />
              ))}
              {campaigns.length === 0 && (
                <p className="col-span-full text-center text-gray-500 py-8">
                  No hay campanas pendientes
                </p>
              )}
            </div>
          )}

          {/* Flags tab */}
          {activeTab === "flags" && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="py-3 px-4">Tipo</th>
                    <th className="py-3 px-4">Contenido</th>
                    <th className="py-3 px-4">Razon</th>
                    <th className="py-3 px-4">Detalles</th>
                    <th className="py-3 px-4">Estado</th>
                    <th className="py-3 px-4">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.map((f) => (
                    <FlagRow key={f.id} flag={f} />
                  ))}
                  {flags.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-gray-500">
                        No hay reportes
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* History tab */}
          {activeTab === "history" && (
            <div className="bg-white rounded-lg border border-gray-200">
              {history.length === 0 ? (
                <p className="py-8 text-center text-gray-500">
                  No hay acciones de moderacion registradas
                </p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {history.map((entry) => (
                    <li key={entry.id} className="px-4 py-3 flex items-center justify-between">
                      <div>
                        <span className="font-medium text-gray-900 capitalize">
                          {entry.action.replace(/_/g, " ")}
                        </span>
                        <span className="text-gray-500 mx-2">&rarr;</span>
                        <span className="text-gray-700">{entry.target_name}</span>
                        <p className="text-sm text-gray-500 mt-0.5">{entry.reason}</p>
                      </div>
                      <time className="text-xs text-gray-400 whitespace-nowrap">
                        {new Date(entry.timestamp).toLocaleDateString("es-PY")}
                      </time>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
