"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Plus,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Save,
  X,
  Undo2,
  Redo2,
  Globe,
  Search,
} from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Spanish labels
// ---------------------------------------------------------------------------
const LABEL_PAGE_TITLE = "Gestion de Contenido";
const LABEL_LOADING = "Cargando contenido...";
const LABEL_ERROR = "Error al cargar contenido";
const LABEL_EMPTY = "No hay contenido creado";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_NEW_CONTENT = "Nuevo Contenido";
const LABEL_SHOWING = "Mostrando";
const LABEL_PREVIOUS = "Anterior";
const LABEL_NEXT = "Siguiente";
const LABEL_ALL = "Todos";
const LABEL_SEARCH = "Buscar...";
const LABEL_SAVE = "Guardar";
const LABEL_CANCEL = "Cancelar";
const LABEL_DELETE_CONFIRM = "Este contenido sera eliminado. Continuar?";
const LABEL_SAVED = "Guardado correctamente";
const LABEL_SAVE_ERROR = "Error al guardar";
const LABEL_DELETED = "Contenido eliminado";
const LABEL_PREVIEW = "Vista Previa";
const LABEL_EDITOR = "Editor";

const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface CMSBlock {
  id: string;
  content_type: string;
  slug: string;
  title: string;
  summary: string | null;
  body: string;
  status: string;
  featured_image_url: string | null;
  meta_description: string | null;
  tags: string[] | null;
  language: string;
  translation_status: string;
  sort_order: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

interface CMSListResponse {
  items: CMSBlock[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  published: "Publicado",
  archived: "Archivado",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-yellow-100 text-yellow-800",
  published: "bg-green-100 text-green-800",
  archived: "bg-gray-100 text-gray-600",
};

const TYPE_LABELS: Record<string, string> = {
  page: "Pagina",
  blog_post: "Blog",
  success_story: "Historia",
  announcement: "Anuncio",
  faq: "FAQ",
};

const LANGUAGE_LABELS: Record<string, string> = {
  es: "Espanol",
  en: "English",
  de: "Deutsch",
  nl: "Nederlands",
};

const CONTENT_TYPES = ["page", "blog_post", "success_story", "announcement", "faq"];
const LANGUAGES = ["es", "en", "de", "nl"];

// ---------------------------------------------------------------------------
// Undo/redo hook
// ---------------------------------------------------------------------------
function useUndoRedo(initial: string, maxHistory = 10) {
  const [history, setHistory] = useState<string[]>([initial]);
  const [pointer, setPointer] = useState(0);

  const current = history[pointer] ?? initial;

  const push = useCallback(
    (value: string) => {
      setHistory((prev) => {
        const trimmed = prev.slice(0, pointer + 1);
        const next = [...trimmed, value];
        if (next.length > maxHistory) next.shift();
        return next;
      });
      setPointer((p) => Math.min(p + 1, maxHistory - 1));
    },
    [pointer, maxHistory]
  );

  const undo = useCallback(() => {
    setPointer((p) => Math.max(0, p - 1));
  }, []);

  const redo = useCallback(() => {
    setPointer((p) => Math.min(history.length - 1, p + 1));
  }, [history.length]);

  const canUndo = pointer > 0;
  const canRedo = pointer < history.length - 1;

  const reset = useCallback((value: string) => {
    setHistory([value]);
    setPointer(0);
  }, []);

  return { current, push, undo, redo, canUndo, canRedo, reset };
}

// ---------------------------------------------------------------------------
// Toast component
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
        type === "success"
          ? "bg-green-600 text-white"
          : "bg-red-600 text-white"
      }`}
    >
      {message}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Content preview
// ---------------------------------------------------------------------------
function ContentPreview({ block }: { block: Partial<CMSBlock> }) {
  // Try to parse body as JSON for structured content
  let bodyContent: React.ReactNode;
  try {
    const parsed = JSON.parse(block.body ?? "");
    bodyContent = (
      <pre className="whitespace-pre-wrap rounded bg-gray-50 p-3 text-sm">
        {JSON.stringify(parsed, null, 2)}
      </pre>
    );
  } catch {
    // Render as HTML
    bodyContent = (
      <div
        className="prose prose-sm max-w-none"
        dangerouslySetInnerHTML={{ __html: block.body ?? "" }}
      />
    );
  }

  return (
    <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="text-lg font-semibold text-gray-900">
        {LABEL_PREVIEW}
      </h3>
      <div className="space-y-3">
        {block.featured_image_url && (
          <img
            src={block.featured_image_url}
            alt=""
            className="h-40 w-full rounded object-cover"
          />
        )}
        <h2 className="text-xl font-bold text-gray-900">{block.title || "Sin titulo"}</h2>
        {block.summary && (
          <p className="text-sm text-gray-600">{block.summary}</p>
        )}
        <div className="border-t pt-3">{bodyContent}</div>
        {block.tags && block.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {block.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Editor modal
// ---------------------------------------------------------------------------
interface EditorProps {
  block: CMSBlock | null;
  onSave: (data: Record<string, unknown>) => Promise<void>;
  onClose: () => void;
  saving: boolean;
}

function ContentEditor({ block, onSave, onClose, saving }: EditorProps) {
  const isNew = !block;
  const [title, setTitle] = useState(block?.title ?? "");
  const [slug, setSlug] = useState(block?.slug ?? "");
  const [contentType, setContentType] = useState(block?.content_type ?? "page");
  const [summary, setSummary] = useState(block?.summary ?? "");
  const [language, setLanguage] = useState(block?.language ?? "es");
  const [featuredImageUrl, setFeaturedImageUrl] = useState(block?.featured_image_url ?? "");
  const [metaDescription, setMetaDescription] = useState(block?.meta_description ?? "");
  const [tagsRaw, setTagsRaw] = useState((block?.tags ?? []).join(", "));
  const [isPublished, setIsPublished] = useState(block?.status === "published");
  const [showPreview, setShowPreview] = useState(false);
  const [dirty, setDirty] = useState(false);

  const bodyUndoRedo = useUndoRedo(block?.body ?? "");
  const previewTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [previewBody, setPreviewBody] = useState(block?.body ?? "");

  // Debounced preview update
  useEffect(() => {
    if (previewTimer.current) clearTimeout(previewTimer.current);
    previewTimer.current = setTimeout(() => {
      setPreviewBody(bodyUndoRedo.current);
    }, 500);
    return () => {
      if (previewTimer.current) clearTimeout(previewTimer.current);
    };
  }, [bodyUndoRedo.current]);

  // Warn on unsaved changes
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const handleBodyChange = (value: string) => {
    bodyUndoRedo.push(value);
    setDirty(true);
  };

  const handleSave = async () => {
    const tags = tagsRaw
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const data: Record<string, unknown> = {
      title,
      slug: slug || undefined,
      content_type: contentType,
      summary: summary || undefined,
      body: bodyUndoRedo.current,
      language,
      featured_image_url: featuredImageUrl || undefined,
      meta_description: metaDescription || undefined,
      tags: tags.length > 0 ? tags : undefined,
      status: isPublished ? "published" : "draft",
    };

    await onSave(data);
    setDirty(false);
  };

  const previewBlock: Partial<CMSBlock> = {
    title,
    summary: summary || null,
    body: previewBody,
    featured_image_url: featuredImageUrl || null,
    tags: tagsRaw.split(",").map((t) => t.trim()).filter(Boolean),
  };

  // Detect if body looks like JSON
  let isJsonContent = false;
  try {
    JSON.parse(bodyUndoRedo.current);
    isJsonContent = true;
  } catch {
    isJsonContent = false;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-auto bg-black/50 p-4">
      <div className="mt-8 w-full max-w-6xl rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {isNew ? "Crear Contenido" : `Editar: ${block.title}`}
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
            >
              {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showPreview ? "Ocultar Preview" : LABEL_PREVIEW}
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className={`flex ${showPreview ? "flex-col lg:flex-row" : ""}`}>
          {/* Editor panel */}
          <div className={`space-y-4 p-6 ${showPreview ? "w-full lg:w-1/2" : "w-full"}`}>
            {/* Title */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Titulo *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => { setTitle(e.target.value); setDirty(true); }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Titulo del contenido"
              />
            </div>

            {/* Row: Type + Language */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Tipo
                </label>
                <select
                  value={contentType}
                  onChange={(e) => { setContentType(e.target.value); setDirty(true); }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  disabled={!isNew}
                >
                  {CONTENT_TYPES.map((t) => (
                    <option key={t} value={t}>{TYPE_LABELS[t] ?? t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Idioma
                </label>
                <select
                  value={language}
                  onChange={(e) => { setLanguage(e.target.value); setDirty(true); }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{LANGUAGE_LABELS[l] ?? l}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Slug */}
            {isNew && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Slug (opcional — se genera automaticamente)
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => { setSlug(e.target.value); setDirty(true); }}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  placeholder="mi-articulo"
                />
              </div>
            )}

            {/* Summary */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Resumen
              </label>
              <input
                type="text"
                value={summary}
                onChange={(e) => { setSummary(e.target.value); setDirty(true); }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Breve descripcion"
                maxLength={500}
              />
            </div>

            {/* Body editor with undo/redo */}
            <div>
              <div className="mb-1 flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Contenido * {isJsonContent && <span className="ml-1 text-xs text-blue-600">(JSON)</span>}
                </label>
                <div className="flex gap-1">
                  <button
                    onClick={bodyUndoRedo.undo}
                    disabled={!bodyUndoRedo.canUndo}
                    className="rounded p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                    title="Deshacer"
                  >
                    <Undo2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={bodyUndoRedo.redo}
                    disabled={!bodyUndoRedo.canRedo}
                    className="rounded p-1 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                    title="Rehacer"
                  >
                    <Redo2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <textarea
                value={bodyUndoRedo.current}
                onChange={(e) => handleBodyChange(e.target.value)}
                className={`w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none ${
                  isJsonContent ? "font-mono" : ""
                }`}
                rows={12}
                placeholder="Contenido HTML o JSON..."
              />
            </div>

            {/* Featured image */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Imagen Destacada (URL)
              </label>
              <input
                type="url"
                value={featuredImageUrl}
                onChange={(e) => { setFeaturedImageUrl(e.target.value); setDirty(true); }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="https://..."
              />
            </div>

            {/* Tags */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Etiquetas (separadas por coma)
              </label>
              <input
                type="text"
                value={tagsRaw}
                onChange={(e) => { setTagsRaw(e.target.value); setDirty(true); }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="adopcion, gatos, historias"
              />
            </div>

            {/* Meta description */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Meta Descripcion (SEO)
              </label>
              <input
                type="text"
                value={metaDescription}
                onChange={(e) => { setMetaDescription(e.target.value); setDirty(true); }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Descripcion para buscadores"
                maxLength={300}
              />
            </div>

            {/* Publish toggle */}
            <div className="flex items-center gap-3">
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={isPublished}
                  onChange={(e) => { setIsPublished(e.target.checked); setDirty(true); }}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-300 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-green-600 peer-checked:after:translate-x-full" />
              </label>
              <span className="text-sm text-gray-700">
                {isPublished ? "Publicado" : "Borrador"}
              </span>
            </div>
          </div>

          {/* Preview panel */}
          {showPreview && (
            <div className="w-full border-t p-6 lg:w-1/2 lg:border-l lg:border-t-0">
              <ContentPreview block={previewBlock} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t px-6 py-4">
          <button
            onClick={onClose}
            className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            {LABEL_CANCEL}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !title.trim()}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? "Guardando..." : LABEL_SAVE}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function AdminContentPage() {
  const router = useRouter();
  const [blocks, setBlocks] = useState<CMSBlock[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterLang, setFilterLang] = useState("");

  // Editor state
  const [editing, setEditing] = useState<CMSBlock | null | "new">(null);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  // Fetch content list
  const fetchBlocks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(PAGE_SIZE));
      if (filterType) params.set("content_type", filterType);
      if (filterStatus) params.set("status", filterStatus);
      if (filterLang) params.set("language", filterLang);
      if (search) params.set("search", search);

      const data = await api<CMSListResponse>(
        `/api/cms/content?${params.toString()}`
      );
      setBlocks(data.items);
      setTotal(data.total);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, [page, filterType, filterStatus, filterLang, search]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
      return;
    }
    fetchBlocks();
  }, [fetchBlocks, router]);

  // Save handler (create or update)
  const handleSave = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      if (editing === "new") {
        await api(`/api/cms/content`, {
          method: "POST",
          body: data,
        });
        setToast({ message: LABEL_SAVED, type: "success" });
      } else if (editing) {
        await api(`/api/cms/content/${editing.id}`, {
          method: "PUT",
          body: data,
        });
        setToast({ message: LABEL_SAVED, type: "success" });
      }
      setEditing(null);
      await fetchBlocks();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail : LABEL_SAVE_ERROR;
      setToast({ message: msg, type: "error" });
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async (block: CMSBlock) => {
    if (!window.confirm(LABEL_DELETE_CONFIRM)) return;
    try {
      await api(`/api/cms/content/${block.id}`, { method: "DELETE" });
      setToast({ message: LABEL_DELETED, type: "success" });
      await fetchBlocks();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail : "Error al eliminar";
      setToast({ message: msg, type: "error" });
    }
  };

  // Status toggle (publish/unpublish)
  const handleToggleStatus = async (block: CMSBlock) => {
    const newStatus = block.status === "published" ? "draft" : "published";
    try {
      await api(`/api/cms/content/${block.id}/status`, {
        method: "POST",
        body: { status: newStatus },
      });
      setToast({
        message: newStatus === "published" ? "Publicado" : "Despublicado",
        type: "success",
      });
      await fetchBlocks();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail : "Error al cambiar estado";
      setToast({ message: msg, type: "error" });
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Group blocks by page_key / content_type for sidebar-like grouping
  const typeGroups = CONTENT_TYPES.reduce<Record<string, CMSBlock[]>>((acc, t) => {
    const matching = blocks.filter((b) => b.content_type === t);
    if (matching.length > 0) acc[t] = matching;
    return acc;
  }, {});

  return (
    <div className="mx-auto max-w-7xl">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => router.push("/admin/dashboard")}
            className="flex items-center gap-1 rounded-lg border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <ArrowLeft className="h-4 w-4" /> {LABEL_BACK}
          </button>
          <button
            onClick={() => setEditing("new")}
            className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" /> {LABEL_NEW_CONTENT}
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
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none"
            placeholder={LABEL_SEARCH}
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">{LABEL_ALL} Tipos</option>
          {CONTENT_TYPES.map((t) => (
            <option key={t} value={t}>{TYPE_LABELS[t]}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">{LABEL_ALL} Estados</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={filterLang}
          onChange={(e) => { setFilterLang(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">{LABEL_ALL} Idiomas</option>
          {LANGUAGES.map((l) => (
            <option key={l} value={l}>{LANGUAGE_LABELS[l]}</option>
          ))}
        </select>
        <button
          onClick={() => fetchBlocks()}
          className="rounded-lg border px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg bg-red-50 p-6 text-center">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchBlocks}
            className="mt-3 rounded-lg border px-4 py-2 text-sm hover:bg-white"
          >
            {LABEL_RETRY}
          </button>
        </div>
      ) : blocks.length === 0 ? (
        <div className="rounded-lg bg-gray-50 p-12 text-center">
          <FileText className="mx-auto mb-3 h-12 w-12 text-gray-400" />
          <p className="text-gray-600">{LABEL_EMPTY}</p>
          <button
            onClick={() => setEditing("new")}
            className="mt-3 flex items-center gap-1 mx-auto rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" /> {LABEL_NEW_CONTENT}
          </button>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <th className="px-4 py-3">Titulo</th>
                  <th className="hidden px-4 py-3 sm:table-cell">Tipo</th>
                  <th className="hidden px-4 py-3 md:table-cell">Idioma</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="hidden px-4 py-3 lg:table-cell">Actualizado</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {blocks.map((block) => (
                  <tr key={block.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{block.title}</div>
                      <div className="text-xs text-gray-500">/{block.slug}</div>
                    </td>
                    <td className="hidden px-4 py-3 sm:table-cell">
                      <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                        {TYPE_LABELS[block.content_type] ?? block.content_type}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 md:table-cell">
                      <span className="flex items-center gap-1 text-xs text-gray-600">
                        <Globe className="h-3 w-3" />
                        {LANGUAGE_LABELS[block.language] ?? block.language}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                          STATUS_COLORS[block.status] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {STATUS_LABELS[block.status] ?? block.status}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 text-xs text-gray-500 lg:table-cell">
                      {new Date(block.updated_at).toLocaleDateString("es-PY")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditing(block)}
                          className="rounded p-1.5 text-gray-500 hover:bg-blue-50 hover:text-blue-600"
                          title="Editar"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(block)}
                          className="rounded p-1.5 text-gray-500 hover:bg-green-50 hover:text-green-600"
                          title={block.status === "published" ? "Despublicar" : "Publicar"}
                        >
                          {block.status === "published" ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(block)}
                          className="rounded p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
              <span>
                {LABEL_SHOWING} {(page - 1) * PAGE_SIZE + 1}-
                {Math.min(page * PAGE_SIZE, total)} de {total}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex items-center gap-1 rounded-lg border px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" /> {LABEL_PREVIOUS}
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="flex items-center gap-1 rounded-lg border px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
                >
                  {LABEL_NEXT} <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Editor modal */}
      {editing !== null && (
        <ContentEditor
          block={editing === "new" ? null : editing}
          onSave={handleSave}
          onClose={() => setEditing(null)}
          saving={saving}
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
