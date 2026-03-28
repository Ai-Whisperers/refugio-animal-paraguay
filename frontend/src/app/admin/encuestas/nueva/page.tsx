"use client";

import { useState, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const QUESTION_TYPES = [
  { value: "text", label: "Texto libre" },
  { value: "single_choice", label: "Opcion unica" },
  { value: "multiple_choice", label: "Opcion multiple" },
  { value: "rating", label: "Puntuacion (1-5)" },
  { value: "yes_no", label: "Si / No" },
] as const;

const MAX_TITLE_LENGTH = 200;
const MAX_DESCRIPTION_LENGTH = 2000;
const MAX_QUESTION_TEXT_LENGTH = 500;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface QuestionOption {
  label: string;
  value: string;
}

interface Question {
  id: string;
  text: string;
  questionType: string;
  required: boolean;
  options: QuestionOption[];
  order: number;
}

interface SurveyFormData {
  title: string;
  description: string;
  startDate: string;
  endDate: string;
  questions: Question[];
}

// ---------------------------------------------------------------------------
// Question Builder
// ---------------------------------------------------------------------------

function QuestionBuilder({
  question,
  index,
  totalQuestions,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
}: {
  question: Question;
  index: number;
  totalQuestions: number;
  onUpdate: (updated: Question) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}) {
  const needsOptions = question.questionType === "single_choice" || question.questionType === "multiple_choice";

  const addOption = () => {
    onUpdate({
      ...question,
      options: [...question.options, { label: "", value: "" }],
    });
  };

  const updateOption = (optIdx: number, label: string) => {
    const newOptions = [...question.options];
    newOptions[optIdx] = { label, value: label };
    onUpdate({ ...question, options: newOptions });
  };

  const removeOption = (optIdx: number) => {
    onUpdate({
      ...question,
      options: question.options.filter((_, i) => i !== optIdx),
    });
  };

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
      role="group"
      aria-label={`Pregunta ${index + 1}`}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-bold text-gray-500">
          Pregunta {index + 1}
        </span>
        <div className="flex gap-1">
          <button
            onClick={onMoveUp}
            disabled={index === 0}
            className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30 min-h-[44px] min-w-[44px]"
            aria-label={`Mover pregunta ${index + 1} arriba`}
          >
            ▲
          </button>
          <button
            onClick={onMoveDown}
            disabled={index === totalQuestions - 1}
            className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-30 min-h-[44px] min-w-[44px]"
            aria-label={`Mover pregunta ${index + 1} abajo`}
          >
            ▼
          </button>
          <button
            onClick={onRemove}
            className="p-2 text-red-400 hover:text-red-600 min-h-[44px] min-w-[44px]"
            aria-label={`Eliminar pregunta ${index + 1}`}
          >
            ✕
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Texto de la pregunta
          </label>
          <input
            type="text"
            value={question.text}
            onChange={(e) => onUpdate({ ...question, text: e.target.value })}
            maxLength={MAX_QUESTION_TEXT_LENGTH}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
            placeholder="Escribe tu pregunta aqui..."
            aria-label="Texto de la pregunta"
          />
          <span className="text-xs text-gray-400">
            {question.text.length}/{MAX_QUESTION_TEXT_LENGTH}
          </span>
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de pregunta
            </label>
            <select
              value={question.questionType}
              onChange={(e) =>
                onUpdate({ ...question, questionType: e.target.value, options: [] })
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-orange-500"
              aria-label="Tipo de pregunta"
            >
              {QUESTION_TYPES.map((qt) => (
                <option key={qt.value} value={qt.value}>
                  {qt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 min-h-[44px]">
              <input
                type="checkbox"
                checked={question.required}
                onChange={(e) =>
                  onUpdate({ ...question, required: e.target.checked })
                }
                className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
              />
              <span className="text-sm text-gray-700">Obligatoria</span>
            </label>
          </div>
        </div>

        {needsOptions && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Opciones
            </label>
            <div className="space-y-2">
              {question.options.map((opt, optIdx) => (
                <div key={optIdx} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={opt.label}
                    onChange={(e) => updateOption(optIdx, e.target.value)}
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder={`Opcion ${optIdx + 1}`}
                    aria-label={`Opcion ${optIdx + 1}`}
                  />
                  <button
                    onClick={() => removeOption(optIdx)}
                    className="text-red-400 hover:text-red-600 min-h-[44px] min-w-[44px]"
                    aria-label={`Eliminar opcion ${optIdx + 1}`}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={addOption}
              className="mt-2 text-sm text-orange-600 hover:text-orange-700 font-medium min-h-[44px] min-w-[44px]"
            >
              + Agregar opcion
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preview
// ---------------------------------------------------------------------------

function SurveyPreview({
  data,
  onClose,
}: {
  data: SurveyFormData;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6"
        role="dialog"
        aria-label="Vista previa de la encuesta"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Vista previa</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 min-h-[44px] min-w-[44px]"
            aria-label="Cerrar vista previa"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{data.title || "Sin titulo"}</h3>
            {data.description && (
              <p className="text-sm text-gray-600 mt-1">{data.description}</p>
            )}
          </div>

          {data.questions.length === 0 && (
            <p className="text-gray-400 text-center py-8">No hay preguntas todavia</p>
          )}

          {data.questions.map((q, idx) => (
            <div key={q.id} className="border border-gray-200 rounded-lg p-4">
              <p className="font-medium text-gray-900 mb-2">
                {idx + 1}. {q.text || "Pregunta sin texto"}
                {q.required && <span className="text-red-500 ml-1">*</span>}
              </p>

              {q.questionType === "text" && (
                <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-400">
                  Campo de texto libre...
                </div>
              )}

              {(q.questionType === "single_choice" || q.questionType === "yes_no") && (
                <div className="space-y-2">
                  {(q.questionType === "yes_no"
                    ? [{ label: "Si" }, { label: "No" }]
                    : q.options
                  ).map((opt, oi) => (
                    <label key={oi} className="flex items-center gap-2">
                      <input type="radio" disabled className="text-orange-600" />
                      <span className="text-sm text-gray-700">{opt.label || `Opcion ${oi + 1}`}</span>
                    </label>
                  ))}
                </div>
              )}

              {q.questionType === "multiple_choice" && (
                <div className="space-y-2">
                  {q.options.map((opt, oi) => (
                    <label key={oi} className="flex items-center gap-2">
                      <input type="checkbox" disabled className="text-orange-600" />
                      <span className="text-sm text-gray-700">{opt.label || `Opcion ${oi + 1}`}</span>
                    </label>
                  ))}
                </div>
              )}

              {q.questionType === "rating" && (
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <span key={star} className="text-2xl text-gray-300">★</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 font-medium min-h-[44px] min-w-[44px]"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AdminSurveyCreationPage() {
  const [formData, setFormData] = useState<SurveyFormData>({
    title: "",
    description: "",
    startDate: "",
    endDate: "",
    questions: [],
  });
  const [showPreview, setShowPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  let nextQuestionId = 1;
  const generateId = () => {
    nextQuestionId += 1;
    return `new-q-${Date.now()}-${nextQuestionId}`;
  };

  const addQuestion = () => {
    setFormData((prev) => ({
      ...prev,
      questions: [
        ...prev.questions,
        {
          id: generateId(),
          text: "",
          questionType: "text",
          required: true,
          options: [],
          order: prev.questions.length,
        },
      ],
    }));
  };

  const updateQuestion = (idx: number, updated: Question) => {
    setFormData((prev) => ({
      ...prev,
      questions: prev.questions.map((q, i) => (i === idx ? updated : q)),
    }));
  };

  const removeQuestion = (idx: number) => {
    setFormData((prev) => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== idx),
    }));
  };

  const moveQuestion = (idx: number, direction: "up" | "down") => {
    setFormData((prev) => {
      const questions = [...prev.questions];
      const targetIdx = direction === "up" ? idx - 1 : idx + 1;
      if (targetIdx < 0 || targetIdx >= questions.length) return prev;
      [questions[idx], questions[targetIdx]] = [questions[targetIdx], questions[idx]];
      return { ...prev, questions };
    });
  };

  const saveSurvey = useCallback(
    async (status: "draft" | "active") => {
      setError(null);
      setSuccess(null);
      setSaving(true);

      try {
        const payload = {
          title: formData.title,
          description: formData.description,
          start_date: formData.startDate || null,
          end_date: formData.endDate || null,
          status,
          questions: formData.questions.map((q, idx) => ({
            text: q.text,
            question_type: q.questionType,
            required: q.required,
            options: q.options.map((o) => ({ label: o.label, value: o.value || o.label })),
            order: idx,
          })),
        };

        const res = await fetch(`${API_BASE_URL}/api/admin/survey-management`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data?.detail?.errors?.join(", ") ?? `Error ${res.status}`);
        }

        const data = await res.json();
        setSuccess(
          status === "draft"
            ? `Encuesta guardada como borrador (${data.id})`
            : `Encuesta publicada exitosamente (${data.id})`
        );

        // Reset form on success
        setFormData({
          title: "",
          description: "",
          startDate: "",
          endDate: "",
          questions: [],
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al guardar");
      } finally {
        setSaving(false);
      }
    },
    [formData]
  );

  const isValid = formData.title.length >= 3 && formData.questions.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Crear nueva encuesta</h1>
          <p className="text-sm text-gray-500 mt-1">
            Disena tu encuesta con diferentes tipos de preguntas
          </p>
        </header>

        {success && (
          <div role="alert" className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
            <p className="text-green-700 font-medium">{success}</p>
          </div>
        )}

        {error && (
          <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-700 font-medium">{error}</p>
          </div>
        )}

        <div className="space-y-6">
          {/* Survey metadata */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Informacion general</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="survey-title" className="block text-sm font-medium text-gray-700 mb-1">
                  Titulo *
                </label>
                <input
                  id="survey-title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  maxLength={MAX_TITLE_LENGTH}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Titulo de la encuesta"
                />
                <span className="text-xs text-gray-400">
                  {formData.title.length}/{MAX_TITLE_LENGTH}
                </span>
              </div>

              <div>
                <label htmlFor="survey-desc" className="block text-sm font-medium text-gray-700 mb-1">
                  Descripcion
                </label>
                <textarea
                  id="survey-desc"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  maxLength={MAX_DESCRIPTION_LENGTH}
                  rows={3}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Descripcion de la encuesta (opcional)"
                />
                <span className="text-xs text-gray-400">
                  {formData.description.length}/{MAX_DESCRIPTION_LENGTH}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha de inicio
                  </label>
                  <input
                    id="start-date"
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500"
                  />
                </div>
                <div>
                  <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha de fin
                  </label>
                  <input
                    id="end-date"
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Questions */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Preguntas ({formData.questions.length})
              </h2>
              <button
                onClick={addQuestion}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium min-h-[44px] min-w-[44px]"
                aria-label="Agregar pregunta"
              >
                + Agregar pregunta
              </button>
            </div>

            {formData.questions.length === 0 && (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 text-center">
                <p className="text-gray-400">
                  No hay preguntas. Haz clic en &quot;Agregar pregunta&quot; para comenzar.
                </p>
              </div>
            )}

            <div className="space-y-4">
              {formData.questions.map((q, idx) => (
                <QuestionBuilder
                  key={q.id}
                  question={q}
                  index={idx}
                  totalQuestions={formData.questions.length}
                  onUpdate={(updated) => updateQuestion(idx, updated)}
                  onRemove={() => removeQuestion(idx)}
                  onMoveUp={() => moveQuestion(idx, "up")}
                  onMoveDown={() => moveQuestion(idx, "down")}
                />
              ))}
            </div>
          </section>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={() => setShowPreview(true)}
              disabled={formData.questions.length === 0}
              className="bg-white border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 min-h-[44px] min-w-[44px]"
              aria-label="Vista previa de la encuesta"
            >
              Vista previa
            </button>
            <button
              onClick={() => saveSurvey("draft")}
              disabled={!isValid || saving}
              className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium disabled:opacity-50 min-h-[44px] min-w-[44px]"
              aria-label="Guardar como borrador"
            >
              {saving ? "Guardando..." : "Guardar borrador"}
            </button>
            <button
              onClick={() => saveSurvey("active")}
              disabled={!isValid || saving}
              className="bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition-colors font-medium disabled:opacity-50 min-h-[44px] min-w-[44px]"
              aria-label="Publicar encuesta"
            >
              {saving ? "Publicando..." : "Publicar encuesta"}
            </button>
          </div>
        </div>

        {showPreview && (
          <SurveyPreview data={formData} onClose={() => setShowPreview(false)} />
        )}
      </div>
    </div>
  );
}
