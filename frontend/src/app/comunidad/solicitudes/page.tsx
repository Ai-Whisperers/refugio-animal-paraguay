"use client";

import { useState, useCallback } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const CATEGORIES = [
  { value: "adopcion", label: "Adopcion" },
  { value: "donaciones", label: "Donaciones" },
  { value: "voluntariado", label: "Voluntariado" },
  { value: "animales", label: "Animales" },
  { value: "sitio_web", label: "Sitio Web" },
  { value: "eventos", label: "Eventos" },
  { value: "otro", label: "Otro" },
] as const;

const STATUS_STYLES: Record<string, string> = {
  open: "bg-blue-100 text-blue-800",
  under_review: "bg-yellow-100 text-yellow-800",
  planned: "bg-purple-100 text-purple-800",
  in_progress: "bg-orange-100 text-orange-800",
  completed: "bg-green-100 text-green-800",
  declined: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Abierto",
  under_review: "En revision",
  planned: "Planificado",
  in_progress: "En progreso",
  completed: "Completado",
  declined: "Rechazado",
};

const MAX_TITLE_LENGTH = 120;
const MAX_DESCRIPTION_LENGTH = 1000;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FeatureRequest {
  id: number;
  title: string;
  description: string;
  category: string;
  category_label: string;
  status: string;
  status_label: string;
  votes: number;
  submitted_by_name: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// StatusBadge
// ---------------------------------------------------------------------------

function StatusBadge({ status, label }: { status: string; label: string }) {
  const style = STATUS_STYLES[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`text-xs font-medium px-2 py-1 rounded-full ${style}`}>
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// VoteButton
// ---------------------------------------------------------------------------

function VoteButton({
  requestId,
  votes,
  onVoted,
}: {
  requestId: number;
  votes: number;
  onVoted: (id: number, newVotes: number) => void;
}) {
  const [isVoting, setIsVoting] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);

  const handleVote = async () => {
    if (hasVoted || isVoting) return;
    setIsVoting(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/feature-requests/${requestId}/vote?voter_key=anonymous`,
        { method: "POST" }
      );
      if (response.ok) {
        const data = await response.json();
        setHasVoted(true);
        onVoted(requestId, data.votes);
      }
    } finally {
      setIsVoting(false);
    }
  };

  return (
    <button
      onClick={handleVote}
      disabled={hasVoted || isVoting}
      className={`flex flex-col items-center justify-center w-16 rounded-lg border transition-colors min-h-[44px] min-w-[44px] ${
        hasVoted
          ? "bg-primary-50 border-primary-300 text-primary-600"
          : "bg-white border-gray-200 hover:border-primary-300 text-gray-600 hover:text-primary-600"
      }`}
      aria-label={`Votar por esta solicitud. ${votes} votos actuales`}
    >
      <span className="text-lg" aria-hidden="true">
        {hasVoted ? "\u2714" : "\u25B2"}
      </span>
      <span className="text-sm font-medium">{votes}</span>
    </button>
  );
}

// ---------------------------------------------------------------------------
// RequestCard
// ---------------------------------------------------------------------------

function RequestCard({
  request,
  onVoted,
}: {
  request: FeatureRequest;
  onVoted: (id: number, newVotes: number) => void;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex gap-4">
      <VoteButton
        requestId={request.id}
        votes={request.votes}
        onVoted={onVoted}
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="text-base font-semibold text-gray-900 truncate">
            {request.title}
          </h3>
          <StatusBadge status={request.status} label={request.status_label} />
        </div>
        <p className="text-sm text-gray-600 line-clamp-2 mb-2">
          {request.description}
        </p>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span className="bg-gray-100 px-2 py-0.5 rounded">
            {request.category_label}
          </span>
          <span>{request.submitted_by_name}</span>
          <span>{new Date(request.created_at).toLocaleDateString("es-PY")}</span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SubmitForm
// ---------------------------------------------------------------------------

function SubmitForm({ onSubmitted }: { onSubmitted: () => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("otro");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFeedback(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/feature-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          category,
          submitted_by_name: name.trim(),
          submitted_by_email: email.trim(),
        }),
      });

      if (response.ok) {
        setFeedback({
          type: "success",
          message: "Solicitud enviada exitosamente",
        });
        setTitle("");
        setDescription("");
        setCategory("otro");
        setName("");
        setEmail("");
        onSubmitted();
      } else {
        setFeedback({
          type: "error",
          message: "Error al enviar la solicitud",
        });
      }
    } catch {
      setFeedback({
        type: "error",
        message: "Error de conexion. Intenta de nuevo.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="w-full py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors min-h-[44px]"
      >
        Enviar nueva solicitud
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-4"
    >
      <h2 className="text-lg font-semibold text-gray-900">
        Nueva solicitud de funcionalidad
      </h2>

      {feedback && (
        <div
          className={`p-3 rounded-lg text-sm ${
            feedback.type === "success"
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
          role="alert"
        >
          {feedback.message}
        </div>
      )}

      <div>
        <label htmlFor="req-title" className="block text-sm font-medium text-gray-700 mb-1">
          Titulo
        </label>
        <input
          id="req-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={MAX_TITLE_LENGTH}
          required
          minLength={5}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          placeholder="Describe brevemente tu idea"
        />
        <p className="text-xs text-gray-400 mt-1">
          {title.length}/{MAX_TITLE_LENGTH}
        </p>
      </div>

      <div>
        <label htmlFor="req-desc" className="block text-sm font-medium text-gray-700 mb-1">
          Descripcion
        </label>
        <textarea
          id="req-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={MAX_DESCRIPTION_LENGTH}
          required
          minLength={10}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          placeholder="Explica tu idea con mas detalle"
        />
        <p className="text-xs text-gray-400 mt-1">
          {description.length}/{MAX_DESCRIPTION_LENGTH}
        </p>
      </div>

      <div>
        <label htmlFor="req-cat" className="block text-sm font-medium text-gray-700 mb-1">
          Categoria
        </label>
        <select
          id="req-cat"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="req-name" className="block text-sm font-medium text-gray-700 mb-1">
            Tu nombre
          </label>
          <input
            id="req-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            minLength={1}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label htmlFor="req-email" className="block text-sm font-medium text-gray-700 mb-1">
            Tu email
          </label>
          <input
            id="req-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors min-h-[44px]"
        >
          {isSubmitting ? "Enviando..." : "Enviar solicitud"}
        </button>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors min-h-[44px] min-w-[44px]"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function FeatureRequestBoardPage() {
  const [requests, setRequests] = useState<FeatureRequest[]>([]);
  const [filterCategory, setFilterCategory] = useState("");
  const [sortBy, setSortBy] = useState("votes");
  const [refreshKey, setRefreshKey] = useState(0);

  const handleVoted = useCallback(
    (id: number, newVotes: number) => {
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, votes: newVotes } : r))
      );
    },
    []
  );

  const handleSubmitted = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  // Filter and sort displayed requests
  const displayedRequests = requests
    .filter((r) => !filterCategory || r.category === filterCategory)
    .sort((a, b) => {
      if (sortBy === "votes") return b.votes - a.votes;
      if (sortBy === "newest")
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    });

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">
          Tablero de Solicitudes
        </h1>
        <p className="text-gray-500 mt-2">
          Propone mejoras y vota por las ideas que mas te gustan.
        </p>
      </header>

      {/* Submit form */}
      <section className="mb-6" aria-label="Enviar solicitud">
        <SubmitForm onSubmitted={handleSubmitted} />
      </section>

      {/* Filters */}
      <section className="flex flex-wrap gap-3 mb-6" aria-label="Filtros">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[44px]"
          aria-label="Filtrar por categoria"
        >
          <option value="">Todas las categorias</option>
          {CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[44px]"
          aria-label="Ordenar por"
        >
          <option value="votes">Mas votados</option>
          <option value="newest">Mas recientes</option>
          <option value="oldest">Mas antiguos</option>
        </select>
      </section>

      {/* Request list */}
      <section aria-label="Lista de solicitudes">
        {displayedRequests.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p className="text-lg">No hay solicitudes todavia</p>
            <p className="text-sm mt-1">Se el primero en enviar una idea</p>
          </div>
        ) : (
          <div className="space-y-3" role="list">
            {displayedRequests.map((request) => (
              <div key={request.id} role="listitem">
                <RequestCard request={request} onVoted={handleVoted} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
