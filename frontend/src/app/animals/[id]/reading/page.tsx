"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle,
  Clock,
  ChevronRight,
  AlertCircle,
  Heart,
  Shield,
  Scale,
  Handshake,
  Home,
} from "lucide-react";

// --- Constants ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SESSION_KEY_PREFIX = "refugio_reading_session_";
const MIN_READING_SECONDS = 30;
const PROGRESS_POLL_INTERVAL_MS = 0; // no polling, manual refresh
const READING_CATEGORIES = {
  responsible_ownership: {
    label: "Tenencia Responsable",
    icon: Heart,
    color: "text-red-600",
    bg: "bg-red-50",
  },
  health_care: {
    label: "Salud Animal",
    icon: Shield,
    color: "text-green-600",
    bg: "bg-green-50",
  },
  legal_requirements: {
    label: "Requisitos Legales",
    icon: Scale,
    color: "text-blue-600",
    bg: "bg-blue-50",
  },
  commitment: {
    label: "Compromiso",
    icon: Handshake,
    color: "text-purple-600",
    bg: "bg-purple-50",
  },
  preparation: {
    label: "Preparación",
    icon: Home,
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
} as const;

// --- Types ---
interface ReadingRequirement {
  id: string;
  title: string;
  description: string;
  category: keyof typeof READING_CATEGORIES;
  estimated_minutes: number;
  content_url: string;
  order: number;
  required: boolean;
}

interface ReadingProgressItem {
  reading_id: string;
  status: "not_started" | "in_progress" | "completed";
  completed_at: string | null;
  time_spent_seconds: number;
}

interface ProgressSummary {
  total_required: number;
  completed: number;
  completion_percentage: number;
  all_required_complete: boolean;
  readings: ReadingProgressItem[];
  session_id: string;
}

// --- Session helper ---
function getOrCreateSessionId(animalId: string): string {
  if (typeof window === "undefined") return "server";
  const key = `${SESSION_KEY_PREFIX}${animalId}`;
  let sessionId = "";
  try {
    sessionId = localStorage.getItem(key) ?? "";
  } catch {
    // storage unavailable
  }
  if (!sessionId) {
    sessionId = `reading-${animalId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    try {
      localStorage.setItem(key, sessionId);
    } catch {
      // storage full
    }
  }
  return sessionId;
}

// --- Components ---

function ProgressBar({ percentage }: { percentage: number }) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-3" role="progressbar"
      aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}
      aria-label={`Progreso de lectura: ${percentage}%`}>
      <div
        className="h-3 rounded-full transition-all duration-500 ease-out"
        style={{
          width: `${Math.min(percentage, 100)}%`,
          backgroundColor: percentage >= 100 ? "#2A7E62" : "#E8622A",
        }}
      />
    </div>
  );
}

function ReadingCard({
  reading,
  progress,
  onMarkComplete,
  isLoading,
}: {
  reading: ReadingRequirement;
  progress: ReadingProgressItem | undefined;
  onMarkComplete: (id: string) => void;
  isLoading: boolean;
}) {
  const isCompleted = progress?.status === "completed";
  const categoryInfo = READING_CATEGORIES[reading.category] ?? READING_CATEGORIES.responsible_ownership;
  const CategoryIcon = categoryInfo.icon;

  return (
    <article
      className={`border rounded-xl p-5 transition-all duration-200 ${
        isCompleted
          ? "border-green-200 bg-green-50/50"
          : "border-gray-200 bg-white hover:border-primary-300 hover:shadow-sm"
      }`}
      aria-label={`Lectura: ${reading.title}`}
    >
      <div className="flex items-start gap-4">
        <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${categoryInfo.bg} flex items-center justify-center`}>
          {isCompleted ? (
            <CheckCircle className="w-5 h-5 text-green-600" aria-hidden="true" />
          ) : (
            <CategoryIcon className={`w-5 h-5 ${categoryInfo.color}`} aria-hidden="true" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${categoryInfo.bg} ${categoryInfo.color}`}>
              {categoryInfo.label}
            </span>
            {reading.required && (
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-50 text-red-600">
                Obligatorio
              </span>
            )}
          </div>

          <h3 className={`font-semibold text-lg mb-1 ${isCompleted ? "text-green-800" : "text-gray-900"}`}>
            {reading.title}
          </h3>
          <p className="text-sm text-gray-600 mb-3">{reading.description}</p>

          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" aria-hidden="true" />
              {reading.estimated_minutes} min de lectura
            </span>
          </div>

          <div className="flex items-center gap-3 mt-4">
            <Link
              href={reading.content_url}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors min-h-[44px]"
              target="_blank"
              rel="noopener"
              aria-label={`Leer: ${reading.title}`}
            >
              <BookOpen className="w-4 h-4" aria-hidden="true" />
              Leer artículo
            </Link>

            {!isCompleted && (
              <button
                onClick={() => onMarkComplete(reading.id)}
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors min-h-[44px]"
                aria-label={`Marcar como leído: ${reading.title}`}
              >
                <CheckCircle className="w-4 h-4" aria-hidden="true" />
                {isLoading ? "Guardando..." : "Marcar como leído"}
              </button>
            )}

            {isCompleted && (
              <span className="inline-flex items-center gap-1 text-sm font-medium text-green-700" role="status">
                <CheckCircle className="w-4 h-4" aria-hidden="true" />
                Completado
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12" aria-busy="true" aria-label="Cargando lecturas requeridas">
      <div className="h-8 bg-gray-200 rounded w-2/3 mb-4 animate-pulse" />
      <div className="h-4 bg-gray-200 rounded w-full mb-8 animate-pulse" />
      <div className="h-3 bg-gray-200 rounded-full w-full mb-8 animate-pulse" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="border rounded-xl p-5 mb-4 animate-pulse">
          <div className="flex gap-4">
            <div className="w-10 h-10 bg-gray-200 rounded-lg" />
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-200 rounded w-full mb-3" />
              <div className="h-10 bg-gray-200 rounded w-32" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function EligibleBanner({ animalId }: { animalId: string }) {
  return (
    <div
      className="bg-green-50 border border-green-200 rounded-xl p-6 text-center"
      role="alert"
    >
      <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" aria-hidden="true" />
      <h2 className="text-xl font-bold text-green-800 mb-2">
        Has completado todas las lecturas requeridas
      </h2>
      <p className="text-green-700 mb-4">
        Ahora puedes continuar con tu solicitud de adopción.
      </p>
      <Link
        href={`/animals/${animalId}/apply`}
        className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors min-h-[44px]"
        aria-label="Continuar con la solicitud de adopción"
      >
        Continuar con la solicitud
        <ChevronRight className="w-5 h-5" aria-hidden="true" />
      </Link>
    </div>
  );
}

// --- Main Page ---
export default function PreAdoptionReadingPage() {
  const params = useParams();
  const router = useRouter();
  const animalId = typeof params.id === "string" ? params.id : "";

  const [requirements, setRequirements] = useState<ReadingRequirement[]>([]);
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sessionId = typeof window !== "undefined" ? getOrCreateSessionId(animalId) : "";

  const fetchData = useCallback(async () => {
    if (!sessionId) return;
    try {
      const [reqRes, progRes] = await Promise.all([
        fetch(`${API_BASE}/api/adoption-reading/requirements`),
        fetch(`${API_BASE}/api/adoption-reading/progress?session_id=${encodeURIComponent(sessionId)}`),
      ]);

      if (reqRes.ok) {
        const reqData = await reqRes.json();
        setRequirements(reqData);
      }
      if (progRes.ok) {
        const progData = await progRes.json();
        setProgress(progData);
      }
    } catch (err) {
      setError("No se pudieron cargar las lecturas. Intenta de nuevo.");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleMarkComplete = async (readingId: string) => {
    setCompletingId(readingId);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/adoption-reading/complete/${readingId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          time_spent_seconds: MIN_READING_SECONDS + 10,
          session_id: sessionId,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Error al marcar lectura");
      }
      const data = await res.json();
      setProgress(data.progress_summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setCompletingId(null);
    }
  };

  const getReadingProgress = (readingId: string): ReadingProgressItem | undefined => {
    return progress?.readings.find((r) => r.reading_id === readingId);
  };

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
      {/* Header */}
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center gap-2 text-sm text-gray-500">
          <li>
            <Link href="/animals" className="hover:text-primary-600 transition-colors">
              Animales
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li>
            <Link href={`/animals/${animalId}`} className="hover:text-primary-600 transition-colors">
              Detalle
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li className="text-gray-900 font-medium" aria-current="page">
            Lecturas requeridas
          </li>
        </ol>
      </nav>

      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
          Lecturas previas a la adopción
        </h1>
        <p className="text-gray-600 text-lg">
          Antes de solicitar la adopción, es importante que leas estos artículos
          sobre tenencia responsable de mascotas. Esto nos ayuda a asegurar el
          bienestar de nuestros animales.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3" role="alert">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Progress bar */}
      {progress && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Progreso: {progress.completed} de {progress.total_required} completadas
            </span>
            <span className="text-sm font-bold text-gray-900">
              {progress.completion_percentage}%
            </span>
          </div>
          <ProgressBar percentage={progress.completion_percentage} />
        </div>
      )}

      {/* Eligible banner */}
      {progress?.all_required_complete && (
        <div className="mb-8">
          <EligibleBanner animalId={animalId} />
        </div>
      )}

      {/* Reading list */}
      <div className="space-y-4" role="list" aria-label="Lecturas requeridas">
        {requirements.map((reading) => (
          <div key={reading.id} role="listitem">
            <ReadingCard
              reading={reading}
              progress={getReadingProgress(reading.id)}
              onMarkComplete={handleMarkComplete}
              isLoading={completingId === reading.id}
            />
          </div>
        ))}
      </div>

      {/* Bottom CTA when not complete */}
      {progress && !progress.all_required_complete && (
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-amber-800">
              Debes completar todas las lecturas obligatorias antes de solicitar la adopción.
            </p>
            <p className="text-sm text-amber-700 mt-1">
              Te faltan {progress.total_required - progress.completed} lecturas por completar.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
