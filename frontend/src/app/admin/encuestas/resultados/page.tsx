"use client";

import { useState, useEffect, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REFRESH_INTERVAL_MS = 300_000;

const CHART_COLORS = [
  "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
  "#EC4899", "#06B6D4", "#84CC16",
];

const RATING_LABELS: Record<string, string> = {
  "1": "Muy malo",
  "2": "Malo",
  "3": "Regular",
  "4": "Bueno",
  "5": "Excelente",
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChoiceBreakdown {
  option: string;
  count: number;
  percentage: number;
}

interface QuestionAnalytics {
  question_id: string;
  question_text: string;
  question_type: string;
  total_answers: number;
  choice_breakdown: ChoiceBreakdown[];
  text_responses: string[];
  average_rating: number | null;
}

interface ResponseTrend {
  period: string;
  count: number;
}

interface SurveyAnalytics {
  survey_id: string;
  survey_title: string;
  total_responses: number;
  completion_rate: number;
  average_time_display: string;
  questions: QuestionAnalytics[];
  response_trends: ResponseTrend[];
  trend_direction: string;
  last_response_at: string | null;
  generated_at: string;
}

// ---------------------------------------------------------------------------
// Metric Card
// ---------------------------------------------------------------------------

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-5"
      role="group"
      aria-label={`${label}: ${value}`}
    >
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {detail && <p className="text-xs text-gray-400 mt-1">{detail}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Horizontal Bar Chart
// ---------------------------------------------------------------------------

function HorizontalBarChart({
  data,
  title,
}: {
  data: ChoiceBreakdown[];
  title: string;
}) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div role="img" aria-label={`Grafico de barras: ${title}`}>
      <div className="space-y-2">
        {data.map((item, idx) => (
          <div key={item.option} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 w-28 truncate text-right">
              {item.option}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${(item.count / maxCount) * 100}%`,
                  backgroundColor: CHART_COLORS[idx % CHART_COLORS.length],
                  minWidth: item.count > 0 ? "8px" : "0",
                }}
              />
            </div>
            <span className="text-sm font-medium text-gray-700 w-16 text-right">
              {item.count} ({item.percentage}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Rating Display
// ---------------------------------------------------------------------------

function RatingDisplay({ analytics }: { analytics: QuestionAnalytics }) {
  const avg = analytics.average_rating;

  return (
    <div className="space-y-3">
      {avg !== null && (
        <div className="flex items-center gap-3" aria-label={`Puntuacion promedio: ${avg} de 5`}>
          <span className="text-3xl font-bold text-amber-500">{avg}</span>
          <span className="text-gray-500 text-sm">/ 5 promedio</span>
          <div className="flex gap-1 ml-2" role="img" aria-label={`${avg} estrellas de 5`}>
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                className={`text-xl ${star <= Math.round(avg) ? "text-amber-400" : "text-gray-300"}`}
              >
                ★
              </span>
            ))}
          </div>
        </div>
      )}
      <HorizontalBarChart
        data={analytics.choice_breakdown.map((cb) => ({
          ...cb,
          option: RATING_LABELS[cb.option] ?? cb.option,
        }))}
        title={analytics.question_text}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Text Responses
// ---------------------------------------------------------------------------

function TextResponseList({ responses }: { responses: string[] }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? responses : responses.slice(0, 5);

  return (
    <div role="list" aria-label="Respuestas de texto">
      {visible.map((text, idx) => (
        <div
          key={idx}
          role="listitem"
          className="bg-gray-50 rounded-lg p-3 mb-2 text-sm text-gray-700 border border-gray-100"
        >
          &ldquo;{text}&rdquo;
        </div>
      ))}
      {responses.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-1 min-h-[44px] min-w-[44px]"
          aria-expanded={showAll}
        >
          {showAll ? "Mostrar menos" : `Ver todas (${responses.length} respuestas)`}
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Trend Chart
// ---------------------------------------------------------------------------

function TrendChart({
  trends,
  direction,
}: {
  trends: ResponseTrend[];
  direction: string;
}) {
  const maxCount = Math.max(...trends.map((t) => t.count), 1);
  const directionLabel =
    direction === "up" ? "En aumento" : direction === "down" ? "Disminuyendo" : "Estable";
  const directionColor =
    direction === "up"
      ? "text-green-600"
      : direction === "down"
        ? "text-red-600"
        : "text-gray-500";

  return (
    <div role="img" aria-label="Tendencia de respuestas por semana">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-700">Tendencia de respuestas</h3>
        <span className={`text-sm font-medium ${directionColor}`}>{directionLabel}</span>
      </div>
      <div className="flex items-end gap-1 h-32">
        {trends.map((trend) => (
          <div key={trend.period} className="flex-1 flex flex-col items-center justify-end">
            <span className="text-xs text-gray-500 mb-1">{trend.count}</span>
            <div
              className="w-full bg-blue-500 rounded-t transition-all duration-300"
              style={{
                height: `${(trend.count / maxCount) * 100}%`,
                minHeight: trend.count > 0 ? "4px" : "0",
              }}
            />
            <span className="text-xs text-gray-400 mt-1 truncate w-full text-center">
              {trend.period.replace(/^\d{4}-/, "")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Question Card
// ---------------------------------------------------------------------------

function QuestionCard({ analytics }: { analytics: QuestionAnalytics }) {
  const typeLabels: Record<string, string> = {
    single_choice: "Opcion unica",
    multiple_choice: "Opcion multiple",
    rating: "Puntuacion",
    text: "Texto libre",
    yes_no: "Si / No",
  };

  return (
    <section
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-5"
      aria-label={`Pregunta: ${analytics.question_text}`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-gray-900">{analytics.question_text}</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {typeLabels[analytics.question_type] ?? analytics.question_type} · {analytics.total_answers} respuestas
          </p>
        </div>
      </div>

      {analytics.question_type === "rating" && <RatingDisplay analytics={analytics} />}

      {(analytics.question_type === "single_choice" ||
        analytics.question_type === "multiple_choice" ||
        analytics.question_type === "yes_no") && (
        <HorizontalBarChart data={analytics.choice_breakdown} title={analytics.question_text} />
      )}

      {analytics.question_type === "text" && (
        <TextResponseList responses={analytics.text_responses} />
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Loading / Error
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Cargando resultados">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="bg-gray-200 rounded-xl h-24" />
        ))}
      </div>
      <div className="bg-gray-200 rounded-xl h-48" />
      <div className="space-y-4">
        {[1, 2, 3].map((n) => (
          <div key={n} className="bg-gray-200 rounded-xl h-40" />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p className="text-red-700 font-medium mb-2">Error al cargar resultados</p>
      <p className="text-red-600 text-sm mb-4">{message}</p>
      <button
        onClick={onRetry}
        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors min-h-[44px] min-w-[44px]"
      >
        Reintentar
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function SurveyResultsPage() {
  const [analytics, setAnalytics] = useState<SurveyAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [surveyId] = useState("survey-satisfaccion");

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE_URL}/api/admin/surveys/${surveyId}/analytics`);
      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }, [surveyId]);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAnalytics]);

  const handleExport = async (format: string) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/admin/surveys/${surveyId}/export?format=${format}`
      );
      if (!res.ok) throw new Error("Export failed");
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data.data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `survey-results-${surveyId}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Export error handled silently — non-critical UI action
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Resultados de Encuesta</h1>
              {analytics && (
                <p className="text-sm text-gray-500 mt-1">{analytics.survey_title}</p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleExport("json")}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium min-h-[44px] min-w-[44px]"
                aria-label="Exportar resultados en formato JSON"
              >
                Exportar JSON
              </button>
              <button
                onClick={() => handleExport("csv")}
                className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium min-h-[44px] min-w-[44px]"
                aria-label="Exportar resultados en formato CSV"
              >
                Exportar CSV
              </button>
              <button
                onClick={fetchAnalytics}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium min-h-[44px] min-w-[44px]"
                aria-label="Actualizar resultados"
              >
                Actualizar
              </button>
            </div>
          </div>
        </header>

        {loading && !analytics && <LoadingSkeleton />}
        {error && <ErrorState message={error} onRetry={fetchAnalytics} />}

        {analytics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard label="Total respuestas" value={analytics.total_responses} />
              <MetricCard label="Tasa de completado" value={`${analytics.completion_rate}%`} />
              <MetricCard label="Tiempo promedio" value={analytics.average_time_display} />
              <MetricCard
                label="Ultima respuesta"
                value={
                  analytics.last_response_at
                    ? new Date(analytics.last_response_at).toLocaleDateString("es-PY")
                    : "Sin respuestas"
                }
              />
            </div>

            {analytics.response_trends.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                <TrendChart trends={analytics.response_trends} direction={analytics.trend_direction} />
              </div>
            )}

            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Resultados por pregunta</h2>
              <div className="space-y-4">
                {analytics.questions.map((q) => (
                  <QuestionCard key={q.question_id} analytics={q} />
                ))}
              </div>
            </div>

            <p className="text-xs text-gray-400 text-center">
              Generado: {new Date(analytics.generated_at).toLocaleString("es-PY")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
