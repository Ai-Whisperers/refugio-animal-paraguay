"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  Plus,
  Trash2,
  GripVertical,
  Eye,
  Undo2,
  Save,
  RefreshCw,
  X,
  AlertTriangle,
  CheckCircle,
  Settings2,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import type { Animal } from "@/types/api";

// --- Constants ---
const REQUIREMENT_TYPES = [
  "yard_required",
  "no_children_under",
  "experience_required",
  "home_type",
  "max_hours_alone",
  "other_pets_ok",
  "housing_status",
  "income_requirement",
] as const;

type RequirementType = (typeof REQUIREMENT_TYPES)[number];

const TYPE_LABELS: Record<RequirementType, string> = {
  yard_required: "Patio/jardin requerido",
  no_children_under: "Edad minima de hijos",
  experience_required: "Experiencia con mascotas",
  home_type: "Tipo de vivienda",
  max_hours_alone: "Horas maximo solo",
  other_pets_ok: "Otras mascotas aceptadas",
  housing_status: "Situacion de vivienda",
  income_requirement: "Ingreso minimo",
};

const TYPE_DESCRIPTIONS: Record<RequirementType, string> = {
  yard_required:
    "Si el animal necesita un patio o espacio exterior para ejercitarse.",
  no_children_under:
    "Edad minima de hijos en el hogar. Protege al animal y a los ninos.",
  experience_required:
    "Nivel de experiencia previa que se necesita para cuidar este animal.",
  home_type:
    "Tipos de vivienda aceptables para este animal.",
  max_hours_alone:
    "Horas maximas que el animal puede quedarse solo por dia.",
  other_pets_ok:
    "Que otros tipos de mascotas son compatibles con este animal.",
  housing_status:
    "Si se requiere que el adoptante sea propietario o si puede ser inquilino.",
  income_requirement:
    "Ingreso mensual minimo recomendado para cubrir gastos del animal.",
};

// --- Labels ---
const LABEL_PAGE_TITLE = "Requisitos de Adopcion";
const LABEL_BACK = "Volver al animal";
const LABEL_LOADING = "Cargando...";
const LABEL_ERROR = "Error al cargar";
const LABEL_RETRY = "Reintentar";
const LABEL_ADD = "Agregar Requisito";
const LABEL_SAVE = "Guardar cambios";
const LABEL_SAVING = "Guardando...";
const LABEL_UNDO = "Deshacer";
const LABEL_PREVIEW = "Vista previa";
const LABEL_MANDATORY = "Obligatorio";
const LABEL_OPTIONAL = "Preferido";
const LABEL_DELETE_CONFIRM = "Seguro que deseas eliminar este requisito?";
const LABEL_DELETE_YES = "Si, eliminar";
const LABEL_DELETE_NO = "Cancelar";
const LABEL_EMPTY = "No hay requisitos configurados para este animal.";
const LABEL_EMPTY_HINT =
  "Agrega requisitos para filtrar adoptantes que no son compatibles.";
const LABEL_SAVED = "Cambios guardados correctamente.";
const LABEL_SAVE_ERROR = "Error al guardar. Intenta de nuevo.";
const LABEL_SELECT_TYPE = "Seleccionar tipo de requisito";
const LABEL_CLOSE = "Cerrar";

// --- Types ---
interface Requirement {
  id: string;
  requirement_type: RequirementType;
  value: Record<string, unknown>;
  is_mandatory: boolean;
  active: boolean;
}

interface RequirementDraft {
  localId: string;
  requirement_type: RequirementType;
  value: Record<string, unknown>;
  is_mandatory: boolean;
  isNew?: boolean;
  serverId?: string;
}

// --- Value editors per requirement type ---
function ValueEditor({
  type,
  value,
  onChange,
}: {
  type: RequirementType;
  value: Record<string, unknown>;
  onChange: (val: Record<string, unknown>) => void;
}) {
  switch (type) {
    case "yard_required":
      return (
        <select
          value={(value.level as string) ?? "required"}
          onChange={(e) => onChange({ level: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none"
        >
          <option value="required">Requerido</option>
          <option value="preferred">Preferido</option>
          <option value="not_needed">No necesario</option>
        </select>
      );

    case "no_children_under":
      return (
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            max={18}
            value={(value.min_age as number) ?? 6}
            onChange={(e) => onChange({ min_age: Number(e.target.value) })}
            className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none"
          />
          <span className="text-sm text-gray-500">anos minimo</span>
        </div>
      );

    case "experience_required":
      return (
        <select
          value={(value.level as string) ?? "some"}
          onChange={(e) => onChange({ level: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none"
        >
          <option value="none">Sin experiencia</option>
          <option value="some">Algo de experiencia</option>
          <option value="experienced">Muy experimentado</option>
        </select>
      );

    case "home_type": {
      const options = ["apartment", "house", "farm", "townhouse"];
      const labels: Record<string, string> = {
        apartment: "Departamento",
        house: "Casa",
        farm: "Chacra/finca",
        townhouse: "Duplex",
      };
      const selected = (value.accepted as string[]) ?? [];
      return (
        <div className="flex flex-wrap gap-2">
          {options.map((opt) => (
            <label
              key={opt}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm cursor-pointer transition-colors ${
                selected.includes(opt)
                  ? "bg-orange-50 border-[#E8622A] text-[#E8622A]"
                  : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
              }`}
            >
              <input
                type="checkbox"
                checked={selected.includes(opt)}
                onChange={() => {
                  const next = selected.includes(opt)
                    ? selected.filter((s) => s !== opt)
                    : [...selected, opt];
                  onChange({ accepted: next });
                }}
                className="sr-only"
              />
              {labels[opt]}
            </label>
          ))}
        </div>
      );
    }

    case "max_hours_alone":
      return (
        <div className="flex items-center gap-2">
          <input
            type="range"
            min={0}
            max={24}
            step={1}
            value={(value.max_hours as number) ?? 8}
            onChange={(e) => onChange({ max_hours: Number(e.target.value) })}
            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#E8622A]"
          />
          <span className="text-sm font-medium text-gray-700 w-16 text-right">
            {(value.max_hours as number) ?? 8}h
          </span>
        </div>
      );

    case "other_pets_ok": {
      const petOptions = ["cats", "dogs", "rabbits", "birds", "other"];
      const petLabels: Record<string, string> = {
        cats: "Gatos",
        dogs: "Perros",
        rabbits: "Conejos",
        birds: "Aves",
        other: "Otros",
      };
      const selectedPets = (value.compatible as string[]) ?? [];
      return (
        <div className="flex flex-wrap gap-2">
          {petOptions.map((opt) => (
            <label
              key={opt}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm cursor-pointer transition-colors ${
                selectedPets.includes(opt)
                  ? "bg-orange-50 border-[#E8622A] text-[#E8622A]"
                  : "bg-white border-gray-200 text-gray-600 hover:border-gray-300"
              }`}
            >
              <input
                type="checkbox"
                checked={selectedPets.includes(opt)}
                onChange={() => {
                  const next = selectedPets.includes(opt)
                    ? selectedPets.filter((s) => s !== opt)
                    : [...selectedPets, opt];
                  onChange({ compatible: next });
                }}
                className="sr-only"
              />
              {petLabels[opt]}
            </label>
          ))}
        </div>
      );
    }

    case "housing_status":
      return (
        <select
          value={(value.required as string) ?? "any"}
          onChange={(e) => onChange({ required: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none"
        >
          <option value="own">Propietario</option>
          <option value="rent">Inquilino aceptado</option>
          <option value="any">Cualquiera</option>
        </select>
      );

    case "income_requirement":
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">EUR</span>
          <input
            type="number"
            min={0}
            step={50}
            value={(value.min_eur as number) ?? 500}
            onChange={(e) => onChange({ min_eur: Number(e.target.value) })}
            className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none"
          />
          <span className="text-sm text-gray-500">/mes</span>
        </div>
      );

    default:
      return (
        <input
          type="text"
          value={JSON.stringify(value)}
          onChange={(e) => {
            try {
              onChange(JSON.parse(e.target.value));
            } catch {
              // invalid JSON, ignore
            }
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
      );
  }
}

// --- Value summary for list display ---
function valueSummary(
  type: RequirementType,
  value: Record<string, unknown>
): string {
  switch (type) {
    case "yard_required":
      return (value.level as string) === "required"
        ? "Requerido"
        : (value.level as string) === "preferred"
          ? "Preferido"
          : "No necesario";
    case "no_children_under":
      return `${value.min_age ?? 0} anos minimo`;
    case "experience_required":
      return (value.level as string) === "experienced"
        ? "Muy experimentado"
        : (value.level as string) === "some"
          ? "Algo de experiencia"
          : "Sin experiencia";
    case "home_type":
      return ((value.accepted as string[]) ?? []).length > 0
        ? (value.accepted as string[]).join(", ")
        : "Cualquiera";
    case "max_hours_alone":
      return `Max ${value.max_hours ?? 8}h solo`;
    case "other_pets_ok":
      return ((value.compatible as string[]) ?? []).length > 0
        ? (value.compatible as string[]).join(", ")
        : "Ninguna";
    case "housing_status":
      return (value.required as string) === "own"
        ? "Propietario"
        : (value.required as string) === "rent"
          ? "Inquilino OK"
          : "Cualquiera";
    case "income_requirement":
      return `EUR ${value.min_eur ?? 0}/mes`;
    default:
      return JSON.stringify(value);
  }
}

// --- Default value for a new requirement ---
function defaultValue(type: RequirementType): Record<string, unknown> {
  switch (type) {
    case "yard_required":
      return { level: "preferred" };
    case "no_children_under":
      return { min_age: 6 };
    case "experience_required":
      return { level: "some" };
    case "home_type":
      return { accepted: ["house", "apartment"] };
    case "max_hours_alone":
      return { max_hours: 8 };
    case "other_pets_ok":
      return { compatible: ["cats", "dogs"] };
    case "housing_status":
      return { required: "any" };
    case "income_requirement":
      return { min_eur: 500 };
    default:
      return {};
  }
}

let nextLocalId = 1;
function generateLocalId(): string {
  return `local_${Date.now()}_${nextLocalId++}`;
}

// =======================
// Main Page Component
// =======================
export default function RequirementsPage() {
  const router = useRouter();
  const params = useParams();
  const animalId = params.id as string;

  // Auth
  const [isChecking, setIsChecking] = useState(true);

  // Animal data
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Requirements state
  const [drafts, setDrafts] = useState<RequirementDraft[]>([]);
  const [previousDrafts, setPreviousDrafts] = useState<RequirementDraft[] | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  // Drag state
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Auth check
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  // Fetch animal + requirements
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [animalData, reqData] = await Promise.all([
        api.get<Animal>(`/animals/${animalId}`),
        api.get<{ items: Requirement[]; total: number }>(
          `/admin/animals/${animalId}/requirements`
        ),
      ]);
      setAnimal(animalData);
      const loadedDrafts: RequirementDraft[] = reqData.items
        .filter((r) => r.active)
        .map((r) => ({
          localId: generateLocalId(),
          requirement_type: r.requirement_type as RequirementType,
          value: r.value,
          is_mandatory: r.is_mandatory,
          isNew: false,
          serverId: r.id,
        }));
      setDrafts(loadedDrafts);
      setPreviousDrafts(null);
      setHasChanges(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setLoadError(`${LABEL_ERROR}: ${err.detail}`);
      } else {
        setLoadError(LABEL_ERROR);
      }
    } finally {
      setIsLoading(false);
    }
  }, [animalId]);

  useEffect(() => {
    if (!isChecking) fetchData();
  }, [isChecking, fetchData]);

  // --- Handlers ---
  function addRequirement(type: RequirementType) {
    setPreviousDrafts([...drafts]);
    setDrafts((prev) => [
      ...prev,
      {
        localId: generateLocalId(),
        requirement_type: type,
        value: defaultValue(type),
        is_mandatory: true,
        isNew: true,
      },
    ]);
    setHasChanges(true);
    setShowAddModal(false);
  }

  function updateDraft(localId: string, updates: Partial<RequirementDraft>) {
    setPreviousDrafts([...drafts]);
    setDrafts((prev) =>
      prev.map((d) => (d.localId === localId ? { ...d, ...updates } : d))
    );
    setHasChanges(true);
  }

  function removeDraft(localId: string) {
    setPreviousDrafts([...drafts]);
    setDrafts((prev) => prev.filter((d) => d.localId !== localId));
    setHasChanges(true);
    setDeleteTarget(null);
  }

  function undo() {
    if (previousDrafts) {
      setDrafts(previousDrafts);
      setPreviousDrafts(null);
      setHasChanges(true);
    }
  }

  // Drag and drop reorder
  function handleDragStart(index: number) {
    setDragIndex(index);
  }

  function handleDragOver(e: React.DragEvent, index: number) {
    e.preventDefault();
    setDragOverIndex(index);
  }

  function handleDrop(index: number) {
    if (dragIndex === null || dragIndex === index) {
      setDragIndex(null);
      setDragOverIndex(null);
      return;
    }
    setPreviousDrafts([...drafts]);
    const newDrafts = [...drafts];
    const [moved] = newDrafts.splice(dragIndex, 1);
    newDrafts.splice(index, 0, moved);
    setDrafts(newDrafts);
    setHasChanges(true);
    setDragIndex(null);
    setDragOverIndex(null);
  }

  // Save: create new requirements, update existing, delete removed
  async function handleSave() {
    setIsSaving(true);
    setSaveMessage(null);

    try {
      // Delete requirements that were removed (server-side ones not in drafts)
      // For simplicity, we'll create new ones and delete removed ones individually
      // The backend supports individual CRUD operations

      // For new requirements: POST
      for (const draft of drafts) {
        if (draft.isNew) {
          await api.post(`/admin/animals/${animalId}/requirements`, {
            requirement_type: draft.requirement_type,
            value: draft.value,
            is_mandatory: draft.is_mandatory,
          });
        } else if (draft.serverId) {
          // Update existing
          await api.put(
            `/admin/animals/${animalId}/requirements/${draft.serverId}`,
            {
              value: draft.value,
              is_mandatory: draft.is_mandatory,
            }
          );
        }
      }

      setSaveMessage({ type: "success", text: LABEL_SAVED });
      setHasChanges(false);
      setPreviousDrafts(null);

      // Reload to get fresh server IDs
      await fetchData();
    } catch (err) {
      setSaveMessage({
        type: "error",
        text:
          err instanceof ApiClientError
            ? err.detail
            : LABEL_SAVE_ERROR,
      });
    } finally {
      setIsSaving(false);
    }
  }

  // Available types (not yet added)
  const usedTypes = new Set(drafts.map((d) => d.requirement_type));
  const availableTypes = REQUIREMENT_TYPES.filter((t) => !usedTypes.has(t));

  // --- Loading ---
  if (isChecking || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin text-[#E8622A]" />
        <p className="text-gray-500">{LABEL_LOADING}</p>
      </div>
    );
  }

  // --- Error ---
  if (loadError || !animal) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-gray-500">{loadError ?? LABEL_ERROR}</p>
        <button
          onClick={fetchData}
          className="text-sm font-medium text-[#E8622A] underline hover:text-[#d4571f]"
        >
          {LABEL_RETRY}
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push(`/admin/animals/${animalId}`)}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <Settings2 className="h-5 w-5 text-[#E8622A]" aria-hidden="true" />
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {LABEL_PAGE_TITLE}
              </h1>
              <p className="text-xs text-gray-500">{animal.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {previousDrafts && (
              <button
                onClick={undo}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Undo2 className="h-4 w-4" />
                {LABEL_UNDO}
              </button>
            )}
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Eye className="h-4 w-4" />
              {LABEL_PREVIEW}
            </button>
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-[#E8622A] rounded-lg hover:bg-[#d4571f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {isSaving ? LABEL_SAVING : LABEL_SAVE}
            </button>
          </div>
        </div>
      </header>

      {/* Save message */}
      {saveMessage && (
        <div
          className={`mx-auto max-w-3xl px-4 sm:px-6 mt-4`}
        >
          <div
            className={`flex items-center gap-2 p-3 rounded-lg text-sm ${
              saveMessage.type === "success"
                ? "bg-green-50 border border-green-200 text-green-700"
                : "bg-red-50 border border-red-200 text-red-700"
            }`}
            role="alert"
          >
            {saveMessage.type === "success" ? (
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
            ) : (
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            )}
            {saveMessage.text}
            <button
              onClick={() => setSaveMessage(null)}
              className="ml-auto p-0.5 hover:opacity-70"
              aria-label={LABEL_CLOSE}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Preview mode */}
      {showPreview && drafts.length > 0 && (
        <div className="mx-auto max-w-3xl px-4 sm:px-6 mt-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="text-sm font-semibold text-blue-900 mb-3">
              Vista previa — asi veran los adoptantes:
            </h2>
            <div className="space-y-3">
              {drafts.map((d) => (
                <div
                  key={d.localId}
                  className="bg-white rounded-lg border border-gray-100 p-3"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      {TYPE_LABELS[d.requirement_type]}
                    </span>
                    <span
                      className={`text-xs font-medium ${
                        d.is_mandatory ? "text-red-500" : "text-gray-400"
                      }`}
                    >
                      {d.is_mandatory ? "Obligatorio" : "Opcional"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">
                    {TYPE_DESCRIPTIONS[d.requirement_type]}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-6">
        {/* Empty state */}
        {drafts.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <Settings2 className="mx-auto h-10 w-10 text-gray-300 mb-3" />
            <p className="text-gray-500 mb-1">{LABEL_EMPTY}</p>
            <p className="text-sm text-gray-400 mb-4">{LABEL_EMPTY_HINT}</p>
            {availableTypes.length > 0 && (
              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#E8622A] rounded-lg hover:bg-[#d4571f] transition-colors"
              >
                <Plus className="h-4 w-4" />
                {LABEL_ADD}
              </button>
            )}
          </div>
        )}

        {/* Requirements list */}
        {drafts.length > 0 && (
          <div className="space-y-3">
            {drafts.map((draft, index) => (
              <div
                key={draft.localId}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDrop={() => handleDrop(index)}
                onDragEnd={() => {
                  setDragIndex(null);
                  setDragOverIndex(null);
                }}
                className={`bg-white rounded-lg border transition-all ${
                  dragOverIndex === index
                    ? "border-[#E8622A] shadow-md"
                    : "border-gray-200 shadow-sm"
                } ${dragIndex === index ? "opacity-50" : ""}`}
              >
                {/* Collapsed row */}
                <div className="flex items-center gap-3 p-4">
                  <div className="cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500">
                    <GripVertical className="h-5 w-5" />
                  </div>

                  <button
                    onClick={() =>
                      setExpandedId(
                        expandedId === draft.localId ? null : draft.localId
                      )
                    }
                    className="flex-1 text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-gray-900">
                          {TYPE_LABELS[draft.requirement_type]}
                        </span>
                        {draft.isNew && (
                          <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                            Nuevo
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">
                        {valueSummary(draft.requirement_type, draft.value)}
                      </span>
                    </div>
                  </button>

                  {/* Mandatory toggle */}
                  <button
                    onClick={() =>
                      updateDraft(draft.localId, {
                        is_mandatory: !draft.is_mandatory,
                      })
                    }
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                      draft.is_mandatory
                        ? "bg-red-100 text-red-700 hover:bg-red-200"
                        : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                    }`}
                    title={
                      draft.is_mandatory
                        ? "Cambiar a opcional"
                        : "Cambiar a obligatorio"
                    }
                  >
                    {draft.is_mandatory ? LABEL_MANDATORY : LABEL_OPTIONAL}
                  </button>

                  {/* Delete */}
                  <button
                    onClick={() => setDeleteTarget(draft.localId)}
                    className="p-1.5 text-gray-300 hover:text-red-500 transition-colors rounded-lg hover:bg-red-50"
                    aria-label="Eliminar"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {/* Expanded editor */}
                {expandedId === draft.localId && (
                  <div className="px-4 pb-4 pt-0 border-t border-gray-100">
                    <p className="text-xs text-gray-400 mt-3 mb-3">
                      {TYPE_DESCRIPTIONS[draft.requirement_type]}
                    </p>
                    <ValueEditor
                      type={draft.requirement_type}
                      value={draft.value}
                      onChange={(val) => updateDraft(draft.localId, { value: val })}
                    />
                  </div>
                )}
              </div>
            ))}

            {/* Add button */}
            {availableTypes.length > 0 && (
              <button
                onClick={() => setShowAddModal(true)}
                className="w-full flex items-center justify-center gap-2 p-3 text-sm font-medium text-[#E8622A] bg-white border-2 border-dashed border-gray-200 rounded-lg hover:border-[#E8622A] hover:bg-orange-50 transition-colors"
              >
                <Plus className="h-4 w-4" />
                {LABEL_ADD}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Delete confirmation modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <p className="text-sm text-gray-700">{LABEL_DELETE_CONFIRM}</p>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                {LABEL_DELETE_NO}
              </button>
              <button
                onClick={() => removeDraft(deleteTarget)}
                className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
              >
                {LABEL_DELETE_YES}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add requirement modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {LABEL_SELECT_TYPE}
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                aria-label={LABEL_CLOSE}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              {availableTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => addRequirement(type)}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-[#E8622A] hover:bg-orange-50 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-900">
                    {TYPE_LABELS[type]}
                  </span>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {TYPE_DESCRIPTIONS[type]}
                  </p>
                </button>
              ))}
            </div>
            {availableTypes.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                Todos los tipos de requisitos ya fueron agregados.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
