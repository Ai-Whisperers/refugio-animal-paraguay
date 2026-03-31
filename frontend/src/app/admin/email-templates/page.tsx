"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Edit, FileText, Plus, RefreshCw, Trash2 } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth";

// --- Labels (Spanish) ---
const LABEL_PAGE_TITLE = "Plantillas de Newsletter";
const LABEL_LOADING = "Cargando plantillas...";
const LABEL_ERROR = "Error al cargar plantillas";
const LABEL_EMPTY = "No hay plantillas creadas";
const LABEL_RETRY = "Reintentar";
const LABEL_BACK = "Volver al panel";
const LABEL_NEW_TEMPLATE = "Nueva Plantilla";
const LABEL_NAME = "Nombre";
const LABEL_SUBJECT = "Asunto";
const LABEL_STATUS = "Estado";
const LABEL_ACTIONS = "Acciones";
const LABEL_EDIT = "Editar";
const LABEL_ARCHIVE = "Archivar";
const LABEL_CONFIRM_ARCHIVE = "Confirmar archivo";
const LABEL_CANCEL = "Cancelar";
const LABEL_SAVE = "Guardar";
const LABEL_CREATE = "Crear";
const LABEL_DESCRIPTION = "Descripcion";
const LABEL_HTML_BODY = "Cuerpo HTML";
const LABEL_TEXT_BODY = "Cuerpo texto plano (opcional)";
const LABEL_PREVIEW = "Vista previa";
const LABEL_CLOSE_PREVIEW = "Cerrar vista previa";

const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  active: "Activo",
  archived: "Archivado",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  archived: "bg-gray-100 text-gray-400",
};

// --- Types ---
interface EmailTemplate {
  id: string;
  name: string;
  description: string | null;
  subject: string;
  html_body: string;
  text_body: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface TemplateFormData {
  name: string;
  description: string;
  subject: string;
  html_body: string;
  text_body: string;
}

const EMPTY_FORM: TemplateFormData = {
  name: "",
  description: "",
  subject: "",
  html_body: "",
  text_body: "",
};

export default function EmailTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<TemplateFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [archiveConfirmId, setArchiveConfirmId] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/admin/login");
    }
  }, [router]);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<EmailTemplate[]>("/email-templates");
      setTemplates(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError(LABEL_ERROR);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const openNewForm = () => {
    setEditingId(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (template: EmailTemplate) => {
    setEditingId(template.id);
    setFormData({
      name: template.name,
      description: template.description ?? "",
      subject: template.subject,
      html_body: template.html_body,
      text_body: template.text_body ?? "",
    });
    setFormError(null);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
  };

  const handleSave = async () => {
    if (!formData.name.trim() || !formData.subject.trim() || !formData.html_body.trim()) {
      setFormError("Nombre, asunto y cuerpo HTML son requeridos");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        subject: formData.subject.trim(),
        html_body: formData.html_body,
        text_body: formData.text_body.trim() || null,
      };
      if (editingId) {
        await api.patch(`/email-templates/${editingId}`, payload);
      } else {
        await api.post("/email-templates", payload);
      }
      closeForm();
      await fetchTemplates();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setFormError(err.message);
      } else {
        setFormError("Error al guardar la plantilla");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await api.delete(`/email-templates/${id}`);
      setArchiveConfirmId(null);
      await fetchTemplates();
    } catch {
      setArchiveConfirmId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin")}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              aria-label={LABEL_BACK}
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <FileText className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">{LABEL_PAGE_TITLE}</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchTemplates}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              aria-label={LABEL_RETRY}
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={openNewForm}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              {LABEL_NEW_TEMPLATE}
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center justify-between">
            <span className="text-red-700 text-sm">{error}</span>
            <button
              onClick={fetchTemplates}
              className="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              {LABEL_RETRY}
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <span className="ml-3 text-gray-500">{LABEL_LOADING}</span>
          </div>
        )}

        {/* Template Table */}
        {!loading && !error && (
          <>
            {templates.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
                <p>{LABEL_EMPTY}</p>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">
                        {LABEL_NAME}
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">
                        {LABEL_SUBJECT}
                      </th>
                      <th className="px-4 py-3 text-left font-medium text-gray-600">
                        {LABEL_STATUS}
                      </th>
                      <th className="px-4 py-3 text-right font-medium text-gray-600">
                        {LABEL_ACTIONS}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {templates.map((tpl) => (
                      <tr key={tpl.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{tpl.name}</div>
                          {tpl.description && (
                            <div className="text-xs text-gray-400 truncate max-w-xs">
                              {tpl.description}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                          {tpl.subject}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[tpl.status] ?? "bg-gray-100 text-gray-600"}`}
                          >
                            {STATUS_LABELS[tpl.status] ?? tpl.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => setPreviewHtml(tpl.html_body)}
                              className="text-gray-400 hover:text-blue-600 transition-colors text-xs"
                            >
                              {LABEL_PREVIEW}
                            </button>
                            <button
                              onClick={() => openEditForm(tpl)}
                              className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                              aria-label={LABEL_EDIT}
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            {tpl.status !== "archived" && (
                              <>
                                {archiveConfirmId === tpl.id ? (
                                  <div className="flex items-center gap-1">
                                    <button
                                      onClick={() => handleArchive(tpl.id)}
                                      className="text-xs text-red-600 font-medium hover:text-red-800"
                                    >
                                      {LABEL_CONFIRM_ARCHIVE}
                                    </button>
                                    <button
                                      onClick={() => setArchiveConfirmId(null)}
                                      className="text-xs text-gray-400 hover:text-gray-600"
                                    >
                                      {LABEL_CANCEL}
                                    </button>
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => setArchiveConfirmId(tpl.id)}
                                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                    aria-label={LABEL_ARCHIVE}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create / Edit Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingId ? LABEL_EDIT : LABEL_NEW_TEMPLATE}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              {formError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                  {formError}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {LABEL_NAME} *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={255}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {LABEL_DESCRIPTION}
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, description: e.target.value }))
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {LABEL_SUBJECT} *
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, subject: e.target.value }))
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={500}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {LABEL_HTML_BODY} *
                </label>
                <textarea
                  value={formData.html_body}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, html_body: e.target.value }))
                  }
                  rows={10}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="<html>...</html>"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {LABEL_TEXT_BODY}
                </label>
                <textarea
                  value={formData.text_body}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, text_body: e.target.value }))
                  }
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={closeForm}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={saving}
              >
                {LABEL_CANCEL}
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
              >
                {saving ? "Guardando..." : editingId ? LABEL_SAVE : LABEL_CREATE}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HTML Preview Modal */}
      {previewHtml !== null && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">{LABEL_PREVIEW}</h2>
              <button
                onClick={() => setPreviewHtml(null)}
                className="text-gray-400 hover:text-gray-700 text-sm"
              >
                {LABEL_CLOSE_PREVIEW}
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <iframe
                srcDoc={previewHtml}
                className="w-full h-[500px] border border-gray-200 rounded"
                sandbox="allow-same-origin"
                title="Email preview"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
