"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  Search,
  ChevronRight,
  AlertTriangle,
  Clock,
  User,
  PawPrint,
  Filter,
  X,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Spanish labels
// ---------------------------------------------------------------------------
const LABEL_PAGE_TITLE = "Pipeline de Adopciones";
const LABEL_BACK = "Volver";
const LABEL_LOADING = "Cargando pipeline...";
const LABEL_ERROR = "Error al cargar el pipeline";
const LABEL_RETRY = "Reintentar";
const LABEL_SEARCH = "Buscar por nombre...";
const LABEL_OVERDUE = "VENCIDO";
const LABEL_DAYS = "dias";
const LABEL_ADVANCE = "Avanzar";
const LABEL_MOVED = "Adopcion movida correctamente";
const LABEL_MOVE_ERROR = "Error al mover adopcion";
const LABEL_NO_ADOPTIONS = "Sin adopciones";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface PipelineStage {
  stage_id: string;
  stage_name: string;
  position: number;
  color: string;
  adoption_count: number;
}

interface AdoptionCard {
  id: string;
  animal_id: string;
  adopter_id: string;
  status: string;
  current_stage_id: string | null;
  current_stage_started_at: string | null;
  current_stage: {
    id: string;
    name: string;
    position: number;
    color: string;
    requires_approval: boolean;
    max_days: number | null;
  } | null;
  days_in_current_stage: number | null;
  // Enriched fields (from adoption request list)
  adopter_name?: string;
  animal_name?: string;
}

interface TimedOutAdoption {
  adoption_request_id: string;
  animal_id: string;
  adopter_id: string;
  stage_id: string;
  stage_name: string;
  max_days: number;
  days_in_stage: number;
  overdue_by: number;
}

interface AdoptionListItem {
  id: string;
  adopter_first_name?: string;
  adopter_last_name?: string;
  adopter?: { first_name?: string; last_name?: string };
  animal_name?: string;
  animal?: { name?: string };
  status: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function getUrgencyColor(daysInStage: number | null, maxDays: number | null): string {
  if (daysInStage === null || maxDays === null) return "border-l-gray-300";
  const ratio = daysInStage / maxDays;
  if (ratio >= 1) return "border-l-red-500";
  if (ratio >= 0.75) return "border-l-yellow-500";
  return "border-l-green-500";
}

function getDaysLabel(days: number | null): string {
  if (days === null) return "";
  return `${days} ${LABEL_DAYS}`;
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: "success" | "error";
  onClose: () => void;
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 rounded-lg px-4 py-3 shadow-lg ${
        type === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"
      }`}
    >
      {message}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Card detail modal
// ---------------------------------------------------------------------------
interface DetailModalProps {
  card: AdoptionCard;
  stages: PipelineStage[];
  onClose: () => void;
  onAdvance: (adoptionId: string) => Promise<void>;
}

function AdoptionDetailModal({ card, stages, onClose, onAdvance }: DetailModalProps) {
  const [advancing, setAdvancing] = useState(false);

  const handleAdvance = async () => {
    setAdvancing(true);
    try {
      await onAdvance(card.id);
      onClose();
    } finally {
      setAdvancing(false);
    }
  };

  const currentPos = card.current_stage?.position ?? 0;
  const isLastStage = stages.length > 0 && currentPos >= stages[stages.length - 1].position;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Detalle de Adopcion
          </h3>
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4 p-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Adoptante</p>
              <p className="font-medium text-gray-900">
                {card.adopter_name || card.adopter_id.slice(0, 8)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Animal</p>
              <p className="font-medium text-gray-900">
                {card.animal_name || card.animal_id.slice(0, 8)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Etapa Actual</p>
              <span
                className="inline-block rounded-full px-2 py-0.5 text-xs font-medium"
                style={{
                  backgroundColor: `${card.current_stage?.color ?? "#gray"}20`,
                  color: card.current_stage?.color ?? "#666",
                }}
              >
                {card.current_stage?.name ?? "Sin etapa"}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500">Dias en Etapa</p>
              <p className="font-medium text-gray-900">
                {getDaysLabel(card.days_in_current_stage)}
              </p>
            </div>
          </div>

          <div>
            <p className="text-xs text-gray-500">Estado</p>
            <p className="font-medium text-gray-900">{card.status}</p>
          </div>

          {/* Stage timeline */}
          <div>
            <p className="mb-2 text-xs text-gray-500">Progreso</p>
            <div className="flex items-center gap-1">
              {stages.map((stage) => (
                <div
                  key={stage.stage_id}
                  className={`flex-1 rounded-full py-1 text-center text-xs ${
                    stage.position <= currentPos
                      ? "text-white"
                      : "bg-gray-100 text-gray-500"
                  }`}
                  style={
                    stage.position <= currentPos
                      ? { backgroundColor: stage.color }
                      : undefined
                  }
                >
                  {stage.stage_name.length > 8
                    ? stage.stage_name.slice(0, 8) + "..."
                    : stage.stage_name}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Cerrar
          </button>
          {!isLastStage && card.status !== "rejected" && (
            <button
              onClick={handleAdvance}
              disabled={advancing}
              className="flex items-center gap-1 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <ChevronRight className="h-4 w-4" />
              {advancing ? "Moviendo..." : LABEL_ADVANCE}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pipeline card
// ---------------------------------------------------------------------------
interface CardProps {
  card: AdoptionCard;
  isOverdue: boolean;
  overdueBy?: number;
  onClick: () => void;
}

function PipelineCard({ card, isOverdue, overdueBy, onClick }: CardProps) {
  const maxDays = card.current_stage?.max_days ?? null;
  const urgencyBorder = getUrgencyColor(card.days_in_current_stage, maxDays);

  return (
    <button
      onClick={onClick}
      className={`w-full rounded-lg border border-l-4 bg-white p-3 text-left shadow-sm transition-shadow hover:shadow-md ${urgencyBorder}`}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <User className="h-3.5 w-3.5 flex-shrink-0 text-gray-400" />
            <p className="truncate text-sm font-medium text-gray-900">
              {card.adopter_name || card.adopter_id.slice(0, 8)}
            </p>
          </div>
          <div className="mt-1 flex items-center gap-1.5">
            <PawPrint className="h-3.5 w-3.5 flex-shrink-0 text-gray-400" />
            <p className="truncate text-xs text-gray-600">
              {card.animal_name || card.animal_id.slice(0, 8)}
            </p>
          </div>
        </div>
        {card.days_in_current_stage !== null && (
          <span className="ml-2 flex items-center gap-0.5 text-xs text-gray-500">
            <Clock className="h-3 w-3" />
            {card.days_in_current_stage}d
          </span>
        )}
      </div>
      {isOverdue && (
        <div className="mt-2 flex items-center gap-1 rounded bg-red-50 px-2 py-0.5">
          <AlertTriangle className="h-3 w-3 text-red-600" />
          <span className="text-xs font-medium text-red-700">
            {LABEL_OVERDUE} ({overdueBy}d)
          </span>
        </div>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function PipelineBoardPage() {
  const router = useRouter();
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [adoptions, setAdoptions] = useState<AdoptionCard[]>([]);
  const [timedOut, setTimedOut] = useState<TimedOutAdoption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterStage, setFilterStage] = useState("");
  const [selectedCard, setSelectedCard] = useState<AdoptionCard | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch pipeline summary (stages with counts) and timed-out adoptions
      const [summaryData, timedOutData, adoptionsList] = await Promise.all([
        api<PipelineStage[]>("/api/admin/adoptions/pipeline-summary"),
        api<TimedOutAdoption[]>("/api/admin/adoptions/timed-out"),
        api<AdoptionListItem[]>("/api/adoption-requests"),
      ]);

      setStages(summaryData.sort((a, b) => a.position - b.position));
      setTimedOut(timedOutData);

      // Enrich adoption cards with pipeline info
      const cards: AdoptionCard[] = [];
      for (const adoption of adoptionsList) {
        try {
          const pipelineInfo = await api<AdoptionCard>(
            `/api/admin/adoptions/${adoption.id}/pipeline`
          );
          cards.push({
            ...pipelineInfo,
            adopter_name:
              adoption.adopter?.first_name && adoption.adopter?.last_name
                ? `${adoption.adopter.first_name} ${adoption.adopter.last_name}`
                : adoption.adopter_first_name && adoption.adopter_last_name
                  ? `${adoption.adopter_first_name} ${adoption.adopter_last_name}`
                  : undefined,
            animal_name: adoption.animal?.name ?? adoption.animal_name,
          });
        } catch {
          // Skip adoptions without pipeline stage
        }
      }

      setAdoptions(cards);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
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
    fetchData();
  }, [fetchData, router]);

  // Advance adoption to next stage
  const handleAdvance = async (adoptionId: string) => {
    try {
      await api(`/api/admin/adoptions/${adoptionId}/advance`, {
        method: "POST",
        body: { notes: null },
      });
      setToast({ message: LABEL_MOVED, type: "success" });
      await fetchData();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail : LABEL_MOVE_ERROR;
      setToast({ message: msg, type: "error" });
    }
  };

  // Build overdue lookup
  const overdueMap = new Map<string, TimedOutAdoption>();
  for (const t of timedOut) {
    overdueMap.set(t.adoption_request_id, t);
  }

  // Filter adoptions
  const filtered = adoptions.filter((a) => {
    if (filterStage && a.current_stage_id !== filterStage) return false;
    if (search) {
      const q = search.toLowerCase();
      const name = (a.adopter_name ?? "").toLowerCase();
      const animal = (a.animal_name ?? "").toLowerCase();
      if (!name.includes(q) && !animal.includes(q)) return false;
    }
    return true;
  });

  // Group by stage
  const cardsByStage = new Map<string, AdoptionCard[]>();
  for (const stage of stages) {
    cardsByStage.set(stage.stage_id, []);
  }
  for (const card of filtered) {
    if (card.current_stage_id) {
      const existing = cardsByStage.get(card.current_stage_id) ?? [];
      existing.push(card);
      cardsByStage.set(card.current_stage_id, existing);
    }
  }

  return (
    <div className="mx-auto max-w-full">
      {/* Header */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
        <div className="flex gap-2">
          <button
            onClick={() => router.push("/admin/adoptions")}
            className="flex items-center gap-1 rounded-lg border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <ArrowLeft className="h-4 w-4" /> {LABEL_BACK}
          </button>
          <button
            onClick={fetchData}
            className="rounded-lg border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none"
            placeholder={LABEL_SEARCH}
          />
        </div>
        <select
          value={filterStage}
          onChange={(e) => setFilterStage(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Todas las Etapas</option>
          {stages.map((s) => (
            <option key={s.stage_id} value={s.stage_id}>
              {s.stage_name} ({s.adoption_count})
            </option>
          ))}
        </select>
        {timedOut.length > 0 && (
          <div className="flex items-center gap-1 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4" />
            {timedOut.length} vencidas
          </div>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="w-72 flex-shrink-0">
              <div className="mb-3 h-8 animate-pulse rounded bg-gray-200" />
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j} className="h-20 animate-pulse rounded-lg bg-gray-100" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg bg-red-50 p-6 text-center">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 rounded-lg border px-4 py-2 text-sm hover:bg-white"
          >
            {LABEL_RETRY}
          </button>
        </div>
      ) : stages.length === 0 ? (
        <div className="rounded-lg bg-gray-50 p-12 text-center">
          <Filter className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="text-gray-600">No hay etapas configuradas en el pipeline.</p>
          <p className="mt-1 text-sm text-gray-500">
            Configure las etapas del pipeline primero.
          </p>
        </div>
      ) : (
        /* Kanban board */
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stages.map((stage) => {
            const cards = cardsByStage.get(stage.stage_id) ?? [];
            return (
              <div
                key={stage.stage_id}
                className="w-72 flex-shrink-0"
              >
                {/* Column header */}
                <div
                  className="mb-3 flex items-center justify-between rounded-lg px-3 py-2"
                  style={{ backgroundColor: `${stage.color}15` }}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: stage.color }}
                    />
                    <h3 className="text-sm font-semibold text-gray-900">
                      {stage.stage_name}
                    </h3>
                  </div>
                  <span
                    className="rounded-full px-2 py-0.5 text-xs font-medium"
                    style={{
                      backgroundColor: `${stage.color}20`,
                      color: stage.color,
                    }}
                  >
                    {cards.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="space-y-2">
                  {cards.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-gray-200 p-4 text-center text-xs text-gray-400">
                      {LABEL_NO_ADOPTIONS}
                    </div>
                  ) : (
                    cards.map((card) => {
                      const overdue = overdueMap.get(card.id);
                      return (
                        <PipelineCard
                          key={card.id}
                          card={card}
                          isOverdue={!!overdue}
                          overdueBy={overdue?.overdue_by}
                          onClick={() => setSelectedCard(card)}
                        />
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detail modal */}
      {selectedCard && (
        <AdoptionDetailModal
          card={selectedCard}
          stages={stages}
          onClose={() => setSelectedCard(null)}
          onAdvance={handleAdvance}
        />
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
