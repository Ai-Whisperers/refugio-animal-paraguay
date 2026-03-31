"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Truck,
  MapPin,
  Camera,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  RefreshCw,
  Phone,
  Navigation,
  PawPrint,
  XCircle,
} from "lucide-react";

// --- Constants ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const REFRESH_INTERVAL_MS = 30000;

const STATUS_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  planned: { color: "text-gray-700", bg: "bg-gray-100", label: "Planificado" },
  driver_assigned: { color: "text-blue-700", bg: "bg-blue-100", label: "Conductor asignado" },
  pickup_en_route: { color: "text-amber-700", bg: "bg-amber-100", label: "En camino a recogida" },
  at_pickup: { color: "text-orange-700", bg: "bg-orange-100", label: "En punto de recogida" },
  animal_loaded: { color: "text-indigo-700", bg: "bg-indigo-100", label: "Animal cargado" },
  in_transit: { color: "text-primary-700", bg: "bg-primary-100", label: "En tránsito" },
  arriving: { color: "text-teal-700", bg: "bg-teal-100", label: "Llegando" },
  delivered: { color: "text-green-700", bg: "bg-green-100", label: "Entregado" },
  completed: { color: "text-green-800", bg: "bg-green-200", label: "Completado" },
  cancelled: { color: "text-red-700", bg: "bg-red-100", label: "Cancelado" },
};

// --- Types ---
interface Trip {
  id: string;
  animal_name: string;
  pickup_location: string;
  delivery_location: string;
  driver_name: string | null;
  driver_phone: string | null;
  status: string;
  status_label: string;
  checkpoint_count: number;
  photo_count: number;
  estimated_duration_minutes: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

interface TimelineEvent {
  event_type: string;
  timestamp: string;
  description: string;
  details: Record<string, unknown>;
}

// --- Components ---

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.planned;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.color} ${config.bg}`}
      role="status"
    >
      {config.label}
    </span>
  );
}

function TripCard({ trip, onSelect }: { trip: Trip; onSelect: (id: string) => void }) {
  const isActive = !["completed", "cancelled"].includes(trip.status);

  return (
    <article
      className={`border rounded-xl p-5 transition-all cursor-pointer hover:shadow-md ${
        isActive ? "border-primary-200 bg-white" : "border-gray-200 bg-gray-50"
      }`}
      onClick={() => onSelect(trip.id)}
      role="button"
      tabIndex={0}
      aria-label={`Viaje de ${trip.animal_name}: ${trip.status_label}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onSelect(trip.id);
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <PawPrint className="w-5 h-5 text-primary-600" aria-hidden="true" />
          <h3 className="font-semibold text-gray-900">{trip.animal_name}</h3>
        </div>
        <StatusBadge status={trip.status} />
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        <div className="flex items-start gap-2">
          <MapPin className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{trip.pickup_location}</span>
        </div>
        <div className="flex items-center gap-2 pl-2">
          <ChevronRight className="w-3 h-3 text-gray-400" aria-hidden="true" />
        </div>
        <div className="flex items-start gap-2">
          <MapPin className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <span>{trip.delivery_location}</span>
        </div>
      </div>

      <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
        {trip.driver_name && (
          <span className="flex items-center gap-1">
            <Truck className="w-3 h-3" aria-hidden="true" />
            {trip.driver_name}
          </span>
        )}
        <span className="flex items-center gap-1">
          <Navigation className="w-3 h-3" aria-hidden="true" />
          {trip.checkpoint_count} puntos
        </span>
        <span className="flex items-center gap-1">
          <Camera className="w-3 h-3" aria-hidden="true" />
          {trip.photo_count} fotos
        </span>
        {trip.estimated_duration_minutes && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" aria-hidden="true" />
            ~{trip.estimated_duration_minutes} min
          </span>
        )}
      </div>
    </article>
  );
}

function TimelineView({ events }: { events: TimelineEvent[] }) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case "status_change":
        return <RefreshCw className="w-4 h-4" aria-hidden="true" />;
      case "checkpoint":
        return <MapPin className="w-4 h-4" aria-hidden="true" />;
      case "photo":
        return <Camera className="w-4 h-4" aria-hidden="true" />;
      default:
        return <Clock className="w-4 h-4" aria-hidden="true" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case "status_change":
        return "bg-blue-100 text-blue-600";
      case "checkpoint":
        return "bg-green-100 text-green-600";
      case "photo":
        return "bg-purple-100 text-purple-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div className="space-y-0" role="list" aria-label="Línea de tiempo del viaje">
      {events.map((event, idx) => (
        <div key={`${event.timestamp}-${idx}`} className="flex gap-3" role="listitem">
          <div className="flex flex-col items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getEventColor(event.event_type)}`}>
              {getEventIcon(event.event_type)}
            </div>
            {idx < events.length - 1 && (
              <div className="w-0.5 h-8 bg-gray-200" aria-hidden="true" />
            )}
          </div>
          <div className="pb-4">
            <p className="text-sm font-medium text-gray-900">{event.description}</p>
            <p className="text-xs text-gray-500">
              {new Date(event.timestamp).toLocaleString("es-PY")}
            </p>
          </div>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">
          No hay eventos en la línea de tiempo.
        </p>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8" aria-busy="true" aria-label="Cargando seguimiento">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6 animate-pulse" />
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="border rounded-xl p-5 animate-pulse">
            <div className="h-5 bg-gray-200 rounded w-2/3 mb-3" />
            <div className="h-4 bg-gray-200 rounded w-full mb-2" />
            <div className="h-4 bg-gray-200 rounded w-full mb-2" />
            <div className="h-3 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Page ---
export default function TripTrackingPage() {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"active" | "all">("active");

  const fetchTrips = useCallback(async () => {
    try {
      const endpoint =
        filter === "active"
          ? `${API_BASE}/api/transport/trips/active`
          : `${API_BASE}/api/transport/trips`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error("Error al cargar viajes");
      const data = await res.json();
      setTrips(filter === "active" ? data : data.trips ?? []);
    } catch {
      setError("No se pudieron cargar los viajes.");
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  const fetchTimeline = useCallback(async (tripId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/transport/trips/${tripId}/timeline`);
      if (!res.ok) throw new Error("Error al cargar línea de tiempo");
      const data = await res.json();
      setTimeline(data.events ?? []);
    } catch {
      setTimeline([]);
    }
  }, []);

  useEffect(() => {
    fetchTrips();
    const interval = setInterval(fetchTrips, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchTrips]);

  useEffect(() => {
    if (selectedTrip) {
      fetchTimeline(selectedTrip);
    }
  }, [selectedTrip, fetchTimeline]);

  const selectedTripData = trips.find((t) => t.id === selectedTrip);

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Seguimiento de transporte
          </h1>
          <p className="text-gray-600 mt-1">
            Seguimiento en tiempo real de viajes de transporte animal
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setFilter("active"); setSelectedTrip(null); }}
            className={`px-4 py-2 text-sm font-medium rounded-lg min-h-[44px] transition-colors ${
              filter === "active"
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            aria-pressed={filter === "active"}
          >
            Activos
          </button>
          <button
            onClick={() => { setFilter("all"); setSelectedTrip(null); }}
            className={`px-4 py-2 text-sm font-medium rounded-lg min-h-[44px] transition-colors ${
              filter === "all"
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            aria-pressed={filter === "all"}
          >
            Todos
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

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trip List */}
        <div className={`${selectedTrip ? "lg:col-span-2" : "lg:col-span-3"}`}>
          {trips.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-xl">
              <Truck className="w-12 h-12 text-gray-400 mx-auto mb-3" aria-hidden="true" />
              <p className="text-gray-600 font-medium">
                {filter === "active"
                  ? "No hay viajes activos en este momento"
                  : "No hay viajes registrados"}
              </p>
            </div>
          ) : (
            <div className={`grid gap-4 ${selectedTrip ? "md:grid-cols-1" : "md:grid-cols-2"}`}>
              {trips.map((trip) => (
                <TripCard
                  key={trip.id}
                  trip={trip}
                  onSelect={setSelectedTrip}
                />
              ))}
            </div>
          )}
        </div>

        {/* Timeline Panel */}
        {selectedTrip && selectedTripData && (
          <div className="lg:col-span-1">
            <div className="sticky top-4 border rounded-xl bg-white p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">
                  {selectedTripData.animal_name}
                </h2>
                <button
                  onClick={() => setSelectedTrip(null)}
                  className="p-1 hover:bg-gray-100 rounded min-w-[44px] min-h-[44px] flex items-center justify-center"
                  aria-label="Cerrar detalle"
                >
                  <XCircle className="w-5 h-5 text-gray-400" aria-hidden="true" />
                </button>
              </div>

              <StatusBadge status={selectedTripData.status} />

              {selectedTripData.driver_name && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700">Conductor</p>
                  <p className="text-sm text-gray-900">{selectedTripData.driver_name}</p>
                  {selectedTripData.driver_phone && (
                    <a
                      href={`tel:${selectedTripData.driver_phone}`}
                      className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 mt-1 min-h-[44px]"
                      aria-label={`Llamar a ${selectedTripData.driver_name}`}
                    >
                      <Phone className="w-4 h-4" aria-hidden="true" />
                      {selectedTripData.driver_phone}
                    </a>
                  )}
                </div>
              )}

              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Línea de tiempo
                </h3>
                <TimelineView events={timeline} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
