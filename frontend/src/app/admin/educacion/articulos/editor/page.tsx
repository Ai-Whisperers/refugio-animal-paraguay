"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Save,
  Eye,
  Send,
  ArrowLeft,
  Image as ImageIcon,
  Tag,
  X,
  FileText,
  Clock,
  Bold,
  Italic,
  Heading1,
  Heading2,
  List,
  ListOrdered,
  Link as LinkIcon,
  Quote,
  Code,
  Undo,
  Redo,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

// --- Constants ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const MAX_TITLE_LENGTH = 300;
const MAX_EXCERPT_LENGTH = 500;
const MAX_TAGS = 20;
const AUTO_SAVE_DELAY_MS = 5000;
const WORDS_PER_MINUTE = 200;

const CATEGORIES = [
  { value: "tenencia_responsable", label: "Tenencia Responsable" },
  { value: "salud", label: "Salud Animal" },
  { value: "nutricion", label: "Nutrición" },
  { value: "comportamiento", label: "Comportamiento" },
  { value: "legal", label: "Legal" },
  { value: "esterilizacion", label: "Esterilización" },
  { value: "adopcion", label: "Adopción" },
  { value: "general", label: "General" },
] as const;

// --- Types ---
interface ArticleForm {
  title: string;
  slug: string;
  body_html: string;
  excerpt: string;
  category: string;
  tags: string[];
  featured_image_url: string;
  meta_title: string;
  meta_description: string;
  author_name: string;
}

interface ArticleResponse {
  id: string;
  title: string;
  slug: string;
  body_html: string;
  excerpt: string | null;
  category: string;
  tags: string[];
  status: string;
  reading_time_minutes: number;
  word_count: number;
}

const INITIAL_FORM: ArticleForm = {
  title: "",
  slug: "",
  body_html: "",
  excerpt: "",
  category: "general",
  tags: [],
  featured_image_url: "",
  meta_title: "",
  meta_description: "",
  author_name: "",
};

// --- Helpers ---
function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/[\s-]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 350);
}

function estimateReadingTime(html: string): number {
  const text = html.replace(/<[^>]+>/g, "");
  const words = text.split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}

function countWords(html: string): number {
  const text = html.replace(/<[^>]+>/g, "");
  return text.split(/\s+/).filter(Boolean).length;
}

// --- Toolbar Component ---
function EditorToolbar({
  onAction,
}: {
  onAction: (tag: string, wrap?: string) => void;
}) {
  const tools = [
    { icon: Bold, action: "bold", label: "Negrita", wrap: "strong" },
    { icon: Italic, action: "italic", label: "Cursiva", wrap: "em" },
    { icon: Heading1, action: "h2", label: "Encabezado 2", wrap: "h2" },
    { icon: Heading2, action: "h3", label: "Encabezado 3", wrap: "h3" },
    { icon: List, action: "ul", label: "Lista", wrap: "ul" },
    { icon: ListOrdered, action: "ol", label: "Lista numerada", wrap: "ol" },
    { icon: Quote, action: "blockquote", label: "Cita", wrap: "blockquote" },
    { icon: Code, action: "code", label: "Código", wrap: "code" },
    { icon: LinkIcon, action: "link", label: "Enlace", wrap: "a" },
  ];

  return (
    <div
      className="flex flex-wrap gap-1 p-2 border-b border-gray-200 bg-gray-50 rounded-t-lg"
      role="toolbar"
      aria-label="Herramientas de formato"
    >
      {tools.map((tool) => (
        <button
          key={tool.action}
          type="button"
          onClick={() => onAction(tool.action, tool.wrap)}
          className="p-2 rounded hover:bg-gray-200 transition-colors text-gray-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label={tool.label}
          title={tool.label}
        >
          <tool.icon className="w-4 h-4" aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}

// --- Tag Input Component ---
function TagInput({
  tags,
  onAdd,
  onRemove,
}: {
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (tag: string) => void;
}) {
  const [input, setInput] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const tag = input.trim().toLowerCase();
      if (tag && !tags.includes(tag) && tags.length < MAX_TAGS) {
        onAdd(tag);
        setInput("");
      }
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2" role="list" aria-label="Etiquetas">
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
            role="listitem"
          >
            <Tag className="w-3 h-3" aria-hidden="true" />
            {tag}
            <button
              type="button"
              onClick={() => onRemove(tag)}
              className="ml-1 hover:text-red-600 transition-colors min-w-[20px] min-h-[20px]"
              aria-label={`Eliminar etiqueta: ${tag}`}
            >
              <X className="w-3 h-3" aria-hidden="true" />
            </button>
          </span>
        ))}
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Escribe una etiqueta y presiona Enter"
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
        aria-label="Nueva etiqueta"
        disabled={tags.length >= MAX_TAGS}
      />
      <p className="text-xs text-gray-500 mt-1">
        {tags.length}/{MAX_TAGS} etiquetas
      </p>
    </div>
  );
}

// --- Preview Component ---
function ArticlePreview({
  form,
  onClose,
}: {
  form: ArticleForm;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-label="Vista previa del artículo"
      aria-modal="true"
    >
      <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Vista previa</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Cerrar vista previa"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
        <article className="p-6">
          {form.featured_image_url && (
            <div className="w-full h-48 bg-gray-100 rounded-lg mb-6 flex items-center justify-center">
              <ImageIcon className="w-8 h-8 text-gray-400" aria-hidden="true" />
              <span className="sr-only">Imagen destacada</span>
            </div>
          )}
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs font-medium px-2 py-1 bg-primary-50 text-primary-700 rounded-full">
              {CATEGORIES.find((c) => c.value === form.category)?.label ?? form.category}
            </span>
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" aria-hidden="true" />
              {estimateReadingTime(form.body_html)} min de lectura
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {form.title || "Sin título"}
          </h1>
          {form.author_name && (
            <p className="text-sm text-gray-600 mb-4">Por {form.author_name}</p>
          )}
          {form.excerpt && (
            <p className="text-lg text-gray-600 mb-6 italic">{form.excerpt}</p>
          )}
          <div
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: form.body_html || "<p>Sin contenido</p>" }}
          />
          {form.tags.length > 0 && (
            <div className="mt-8 pt-4 border-t flex flex-wrap gap-2">
              {form.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </article>
      </div>
    </div>
  );
}

// --- Save Status Component ---
function SaveStatus({ status }: { status: "idle" | "saving" | "saved" | "error" }) {
  if (status === "idle") return null;
  return (
    <span
      className={`inline-flex items-center gap-1 text-sm ${
        status === "saving"
          ? "text-amber-600"
          : status === "saved"
            ? "text-green-600"
            : "text-red-600"
      }`}
      role="status"
      aria-live="polite"
    >
      {status === "saving" && "Guardando..."}
      {status === "saved" && (
        <>
          <CheckCircle className="w-4 h-4" aria-hidden="true" />
          Guardado
        </>
      )}
      {status === "error" && (
        <>
          <AlertCircle className="w-4 h-4" aria-hidden="true" />
          Error al guardar
        </>
      )}
    </span>
  );
}

// --- Loading Skeleton ---
function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8" aria-busy="true" aria-label="Cargando editor">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6 animate-pulse" />
      <div className="h-12 bg-gray-200 rounded w-full mb-4 animate-pulse" />
      <div className="h-64 bg-gray-200 rounded w-full mb-4 animate-pulse" />
      <div className="h-10 bg-gray-200 rounded w-1/4 animate-pulse" />
    </div>
  );
}

// --- Main Page ---
export default function AdminArticleEditorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("id");

  const [form, setForm] = useState<ArticleForm>(INITIAL_FORM);
  const [showPreview, setShowPreview] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [isLoading, setIsLoading] = useState(!!editId);
  const [error, setError] = useState<string | null>(null);
  const [articleId, setArticleId] = useState<string | null>(editId);
  const [autoSlug, setAutoSlug] = useState(true);
  const bodyRef = useRef<HTMLTextAreaElement>(null);

  // Load existing article for editing
  useEffect(() => {
    if (!editId) return;
    const loadArticle = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/admin/articles/${editId}`);
        if (!res.ok) throw new Error("No se pudo cargar el artículo");
        const data: ArticleResponse = await res.json();
        setForm({
          title: data.title,
          slug: data.slug,
          body_html: data.body_html,
          excerpt: data.excerpt ?? "",
          category: data.category,
          tags: data.tags,
          featured_image_url: "",
          meta_title: "",
          meta_description: "",
          author_name: "",
        });
        setAutoSlug(false);
        setArticleId(data.id);
      } catch {
        setError("No se pudo cargar el artículo para editar.");
      } finally {
        setIsLoading(false);
      }
    };
    loadArticle();
  }, [editId]);

  const updateField = useCallback(
    <K extends keyof ArticleForm>(field: K, value: ArticleForm[K]) => {
      setForm((prev) => {
        const updated = { ...prev, [field]: value };
        if (field === "title" && autoSlug) {
          updated.slug = generateSlug(value as string);
        }
        return updated;
      });
    },
    [autoSlug],
  );

  const handleToolbarAction = useCallback(
    (action: string, wrap?: string) => {
      if (!bodyRef.current || !wrap) return;
      const textarea = bodyRef.current;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const selected = form.body_html.slice(start, end) || "texto";

      let insertion: string;
      if (action === "link") {
        insertion = `<a href="url">${selected}</a>`;
      } else if (action === "ul") {
        insertion = `<ul>\n  <li>${selected}</li>\n</ul>`;
      } else if (action === "ol") {
        insertion = `<ol>\n  <li>${selected}</li>\n</ol>`;
      } else {
        insertion = `<${wrap}>${selected}</${wrap}>`;
      }

      const newContent =
        form.body_html.slice(0, start) + insertion + form.body_html.slice(end);
      updateField("body_html", newContent);
    },
    [form.body_html, updateField],
  );

  const handleSave = async (publish: boolean = false) => {
    setError(null);
    setSaveStatus("saving");

    const payload = {
      title: form.title,
      slug: form.slug || undefined,
      body_html: form.body_html,
      excerpt: form.excerpt || undefined,
      category: form.category,
      tags: form.tags,
      featured_image_url: form.featured_image_url || undefined,
      meta_title: form.meta_title || undefined,
      meta_description: form.meta_description || undefined,
      author_name: form.author_name || undefined,
      publish,
    };

    try {
      let res: Response;
      if (articleId) {
        res = await fetch(`${API_BASE}/api/admin/articles/${articleId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        res = await fetch(`${API_BASE}/api/admin/articles`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Error al guardar");
      }

      const data = await res.json();
      setArticleId(data.id);
      setSaveStatus("saved");

      if (publish) {
        // Also publish if creating as published
        if (!articleId) {
          // Already published via publish flag
        } else {
          await fetch(`${API_BASE}/api/admin/articles/${data.id}/publish`, {
            method: "POST",
          });
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      setSaveStatus("error");
    }
  };

  if (isLoading) return <LoadingSkeleton />;

  const wordCount = countWords(form.body_html);
  const readingTime = estimateReadingTime(form.body_html);

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 sm:py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link
            href="/admin/content"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Volver al listado"
          >
            <ArrowLeft className="w-5 h-5" aria-hidden="true" />
          </Link>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              {editId ? "Editar artículo" : "Nuevo artículo educativo"}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" aria-hidden="true" />
                {wordCount} palabras
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" aria-hidden="true" />
                ~{readingTime} min lectura
              </span>
              <SaveStatus status={saveStatus} />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowPreview(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors min-h-[44px]"
            aria-label="Vista previa"
          >
            <Eye className="w-4 h-4" aria-hidden="true" />
            <span className="hidden sm:inline">Vista previa</span>
          </button>
          <button
            type="button"
            onClick={() => handleSave(false)}
            className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors min-h-[44px]"
            aria-label="Guardar borrador"
          >
            <Save className="w-4 h-4" aria-hidden="true" />
            <span className="hidden sm:inline">Guardar</span>
          </button>
          <button
            type="button"
            onClick={() => handleSave(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors min-h-[44px]"
            aria-label="Publicar artículo"
          >
            <Send className="w-4 h-4" aria-hidden="true" />
            <span className="hidden sm:inline">Publicar</span>
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3" role="alert">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSave(false);
        }}
        className="space-y-6"
      >
        {/* Title */}
        <div>
          <label htmlFor="article-title" className="block text-sm font-medium text-gray-700 mb-1">
            Título del artículo *
          </label>
          <input
            id="article-title"
            type="text"
            value={form.title}
            onChange={(e) => updateField("title", e.target.value)}
            maxLength={MAX_TITLE_LENGTH}
            required
            placeholder="Escribe el título del artículo..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg font-medium focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
          />
          <p className="text-xs text-gray-500 mt-1">
            {form.title.length}/{MAX_TITLE_LENGTH}
          </p>
        </div>

        {/* Slug */}
        <div>
          <label htmlFor="article-slug" className="block text-sm font-medium text-gray-700 mb-1">
            URL (slug)
          </label>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">/educacion/articulos/</span>
            <input
              id="article-slug"
              type="text"
              value={form.slug}
              onChange={(e) => {
                setAutoSlug(false);
                updateField("slug", e.target.value);
              }}
              placeholder="url-del-articulo"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
            />
          </div>
        </div>

        {/* Category & Author */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="article-category" className="block text-sm font-medium text-gray-700 mb-1">
              Categoría
            </label>
            <select
              id="article-category"
              value={form.category}
              onChange={(e) => updateField("category", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="article-author" className="block text-sm font-medium text-gray-700 mb-1">
              Autor
            </label>
            <input
              id="article-author"
              type="text"
              value={form.author_name}
              onChange={(e) => updateField("author_name", e.target.value)}
              placeholder="Nombre del autor"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
            />
          </div>
        </div>

        {/* Rich Text Editor */}
        <div>
          <label htmlFor="article-body" className="block text-sm font-medium text-gray-700 mb-1">
            Contenido del artículo *
          </label>
          <div className="border border-gray-300 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-primary-500">
            <EditorToolbar onAction={handleToolbarAction} />
            <textarea
              id="article-body"
              ref={bodyRef}
              value={form.body_html}
              onChange={(e) => updateField("body_html", e.target.value)}
              required
              rows={20}
              placeholder="Escribe el contenido del artículo en HTML..."
              className="w-full px-4 py-3 border-0 focus:ring-0 resize-y font-mono text-sm"
              style={{ minHeight: "400px" }}
            />
          </div>
        </div>

        {/* Excerpt */}
        <div>
          <label htmlFor="article-excerpt" className="block text-sm font-medium text-gray-700 mb-1">
            Extracto
          </label>
          <textarea
            id="article-excerpt"
            value={form.excerpt}
            onChange={(e) => updateField("excerpt", e.target.value)}
            maxLength={MAX_EXCERPT_LENGTH}
            rows={3}
            placeholder="Breve resumen del artículo (se genera automáticamente si se deja vacío)..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            {form.excerpt.length}/{MAX_EXCERPT_LENGTH}
          </p>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Etiquetas
          </label>
          <TagInput
            tags={form.tags}
            onAdd={(tag) => updateField("tags", [...form.tags, tag])}
            onRemove={(tag) => updateField("tags", form.tags.filter((t) => t !== tag))}
          />
        </div>

        {/* SEO Section */}
        <details className="border border-gray-200 rounded-lg">
          <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50 min-h-[44px] flex items-center">
            Opciones SEO
          </summary>
          <div className="px-4 pb-4 space-y-4">
            <div>
              <label htmlFor="meta-title" className="block text-sm font-medium text-gray-700 mb-1">
                Meta título
              </label>
              <input
                id="meta-title"
                type="text"
                value={form.meta_title}
                onChange={(e) => updateField("meta_title", e.target.value)}
                maxLength={200}
                placeholder="Título para motores de búsqueda"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
              />
            </div>
            <div>
              <label htmlFor="meta-description" className="block text-sm font-medium text-gray-700 mb-1">
                Meta descripción
              </label>
              <textarea
                id="meta-description"
                value={form.meta_description}
                onChange={(e) => updateField("meta_description", e.target.value)}
                maxLength={300}
                rows={2}
                placeholder="Descripción para resultados de búsqueda"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label htmlFor="featured-image" className="block text-sm font-medium text-gray-700 mb-1">
                URL de imagen destacada
              </label>
              <input
                id="featured-image"
                type="url"
                value={form.featured_image_url}
                onChange={(e) => updateField("featured_image_url", e.target.value)}
                placeholder="https://..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-h-[44px]"
              />
            </div>
          </div>
        </details>
      </form>

      {/* Preview Modal */}
      {showPreview && (
        <ArticlePreview form={form} onClose={() => setShowPreview(false)} />
      )}
    </div>
  );
}
