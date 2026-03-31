"use client";

import { useState, useEffect } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface QuestionOption {
  id: string;
  text: string;
}

interface SurveyQuestion {
  id: string;
  text: string;
  question_type: "text" | "single_choice" | "multiple_choice" | "rating" | "yes_no";
  required: boolean;
  options: QuestionOption[];
  min_rating: number;
  max_rating: number;
}

interface Survey {
  id: string;
  title: string;
  description: string;
  questions: SurveyQuestion[];
  thank_you_message: string;
  estimated_minutes: number;
  response_count: number;
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// RatingInput
// ---------------------------------------------------------------------------

function RatingInput({
  value,
  onChange,
  min,
  max,
  questionId,
}: {
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  questionId: string;
}) {
  const ratings = Array.from({ length: max - min + 1 }, (_, i) => min + i);
  return (
    <div className="flex gap-2" role="radiogroup" aria-label="Calificacion">
      {ratings.map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onChange(r)}
          className={`w-10 h-10 rounded-full border-2 font-medium transition-colors min-h-[44px] min-w-[44px] ${
            value === r
              ? "bg-primary-600 border-primary-600 text-white"
              : "border-gray-300 text-gray-600 hover:border-primary-400"
          }`}
          role="radio"
          aria-checked={value === r}
          aria-label={`${r} de ${max}`}
        >
          {r}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// YesNoInput
// ---------------------------------------------------------------------------

function YesNoInput({
  value,
  onChange,
  questionId,
}: {
  value: string;
  onChange: (v: string) => void;
  questionId: string;
}) {
  return (
    <div className="flex gap-3" role="radiogroup" aria-label="Si o No">
      {[
        { val: "si", label: "Si" },
        { val: "no", label: "No" },
      ].map((opt) => (
        <button
          key={opt.val}
          type="button"
          onClick={() => onChange(opt.val)}
          className={`px-6 py-2 rounded-lg border-2 font-medium transition-colors min-h-[44px] min-w-[44px] ${
            value === opt.val
              ? "bg-primary-600 border-primary-600 text-white"
              : "border-gray-300 text-gray-600 hover:border-primary-400"
          }`}
          role="radio"
          aria-checked={value === opt.val}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// QuestionRenderer
// ---------------------------------------------------------------------------

function QuestionRenderer({
  question,
  value,
  onChange,
}: {
  question: SurveyQuestion;
  value: string | number | string[];
  onChange: (v: string | number | string[]) => void;
}) {
  switch (question.question_type) {
    case "text":
      return (
        <textarea
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          maxLength={2000}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          placeholder="Escribe tu respuesta aqui..."
          aria-label={question.text}
        />
      );
    case "rating":
      return (
        <RatingInput
          value={value as number}
          onChange={onChange}
          min={question.min_rating}
          max={question.max_rating}
          questionId={question.id}
        />
      );
    case "yes_no":
      return (
        <YesNoInput
          value={value as string}
          onChange={onChange}
          questionId={question.id}
        />
      );
    case "single_choice":
      return (
        <div className="space-y-2" role="radiogroup" aria-label={question.text}>
          {question.options.map((opt) => (
            <label
              key={opt.id}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors min-h-[44px] ${
                value === opt.id
                  ? "border-primary-500 bg-primary-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <input
                type="radio"
                name={question.id}
                value={opt.id}
                checked={value === opt.id}
                onChange={() => onChange(opt.id)}
                className="sr-only"
              />
              <span
                className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                  value === opt.id ? "border-primary-600" : "border-gray-400"
                }`}
              >
                {value === opt.id && (
                  <span className="w-2 h-2 rounded-full bg-primary-600" />
                )}
              </span>
              <span className="text-sm text-gray-700">{opt.text}</span>
            </label>
          ))}
        </div>
      );
    case "multiple_choice":
      return (
        <div className="space-y-2" role="group" aria-label={question.text}>
          {question.options.map((opt) => {
            const selected = (value as string[]).includes(opt.id);
            return (
              <label
                key={opt.id}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors min-h-[44px] ${
                  selected
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  value={opt.id}
                  checked={selected}
                  onChange={() => {
                    const current = value as string[];
                    const next = selected
                      ? current.filter((id) => id !== opt.id)
                      : [...current, opt.id];
                    onChange(next);
                  }}
                  className="sr-only"
                />
                <span
                  className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                    selected ? "bg-primary-600 border-primary-600" : "border-gray-400"
                  }`}
                >
                  {selected && (
                    <span className="text-white text-xs">{"\u2713"}</span>
                  )}
                </span>
                <span className="text-sm text-gray-700">{opt.text}</span>
              </label>
            );
          })}
        </div>
      );
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// SurveyForm
// ---------------------------------------------------------------------------

function SurveyForm({
  survey,
  onCompleted,
}: {
  survey: Survey;
  onCompleted: () => void;
}) {
  const [answers, setAnswers] = useState<Record<string, string | number | string[]>>({});
  const [respondentName, setRespondentName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize default values
  useEffect(() => {
    const defaults: Record<string, string | number | string[]> = {};
    survey.questions.forEach((q) => {
      if (q.question_type === "multiple_choice") defaults[q.id] = [];
      else if (q.question_type === "rating") defaults[q.id] = 0;
      else defaults[q.id] = "";
    });
    setAnswers(defaults);
  }, [survey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const formattedAnswers = Object.entries(answers)
      .filter(([_, v]) => {
        if (Array.isArray(v)) return v.length > 0;
        return v !== "" && v !== 0;
      })
      .map(([questionId, value]) => ({ question_id: questionId, value }));

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/surveys/${survey.id}/responses`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            respondent_name: respondentName.trim(),
            answers: formattedAnswers,
          }),
        }
      );

      if (response.ok) {
        onCompleted();
      } else {
        const data = await response.json();
        setError(data.detail ?? "Error al enviar la respuesta");
      }
    } catch {
      setError("Error de conexion. Intenta de nuevo.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="respondent-name" className="block text-sm font-medium text-gray-700 mb-1">
          Tu nombre (opcional)
        </label>
        <input
          id="respondent-name"
          type="text"
          value={respondentName}
          onChange={(e) => setRespondentName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          placeholder="Anonimo si lo dejas vacio"
        />
      </div>

      {survey.questions.map((question, index) => (
        <div
          key={question.id}
          className="bg-white rounded-xl shadow-sm border border-gray-100 p-5"
        >
          <p className="text-base font-medium text-gray-900 mb-3">
            {index + 1}. {question.text}
            {question.required && (
              <span className="text-red-500 ml-1" aria-label="obligatorio">
                *
              </span>
            )}
          </p>
          <QuestionRenderer
            question={question}
            value={answers[question.id] ?? ""}
            onChange={(v) => setAnswers((prev) => ({ ...prev, [question.id]: v }))}
          />
        </div>
      ))}

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm" role="alert">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors min-h-[44px]"
      >
        {isSubmitting ? "Enviando..." : "Enviar respuesta"}
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// ThankYou
// ---------------------------------------------------------------------------

function ThankYouMessage({ message }: { message: string }) {
  return (
    <div className="text-center py-12">
      <div className="text-5xl mb-4" aria-hidden="true">
        {"\u2705"}
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Respuesta enviada
      </h2>
      <p className="text-gray-500 text-lg">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function EncuestasPage() {
  const [surveys, setSurveys] = useState<Survey[]>([]);
  const [selectedSurvey, setSelectedSurvey] = useState<Survey | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSurveys() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/surveys/active`);
        if (response.ok) {
          const data = await response.json();
          setSurveys(data);
        }
      } catch {
        setError("Error al cargar las encuestas");
      } finally {
        setIsLoading(false);
      }
    }
    fetchSurveys();
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          Encuestas
        </h1>
        <p className="text-gray-500 mt-2">
          Tu opinion nos ayuda a mejorar. Completa una encuesta rapida.
        </p>
      </header>

      {isLoading ? (
        <div className="animate-pulse space-y-4" aria-label="Cargando encuestas">
          {[1, 2].map((i) => (
            <div key={i} className="bg-gray-200 rounded-xl h-24" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-500" role="alert">
          {error}
        </div>
      ) : isCompleted && selectedSurvey ? (
        <ThankYouMessage message={selectedSurvey.thank_you_message} />
      ) : selectedSurvey ? (
        <section aria-label="Formulario de encuesta">
          <button
            onClick={() => setSelectedSurvey(null)}
            className="text-sm text-primary-600 hover:text-primary-700 mb-4 min-h-[44px] min-w-[44px]"
          >
            Volver a la lista
          </button>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {selectedSurvey.title}
          </h2>
          <p className="text-gray-500 mb-6">{selectedSurvey.description}</p>
          <SurveyForm
            survey={selectedSurvey}
            onCompleted={() => setIsCompleted(true)}
          />
        </section>
      ) : (
        <section aria-label="Lista de encuestas disponibles">
          {surveys.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg">No hay encuestas activas en este momento</p>
            </div>
          ) : (
            <div className="space-y-4" role="list">
              {surveys.map((survey) => (
                <button
                  key={survey.id}
                  onClick={() => setSelectedSurvey(survey)}
                  className="w-full text-left bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:border-primary-300 transition-colors min-h-[44px]"
                  role="listitem"
                >
                  <h3 className="text-lg font-semibold text-gray-900">
                    {survey.title}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {survey.description}
                  </p>
                  <div className="flex gap-4 mt-3 text-xs text-gray-400">
                    <span>
                      Tiempo estimado: {survey.estimated_minutes} min
                    </span>
                    <span>{survey.response_count} respuestas</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
