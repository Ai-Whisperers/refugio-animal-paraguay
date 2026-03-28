"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Truck,
  MapPin,
  Phone,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle,
  Plus,
  ChevronDown,
  ChevronUp,
  Send,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LocationInfo {
  address: string;
  city: string;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

interface AnimalInfo {
  animal_id?: string;
  name: string;
  species: string;
  special_needs?: string;
}

interface TransportRequest {
  id: string;
  reason: string;
  reason_label: string;
  urgency: string;
  urgency_label: string;
  status: string;
  status_label: string;
  pickup: LocationInfo;
  delivery: LocationInfo;
  animals: AnimalInfo[];
  animal_count: number;
  preferred_date?: string;
  preferred_time?: string;
  notes?: string;
  requester_name: string;
  requester_phone: string;
  assigned_driver?: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  approved: "bg-blue-100 text-blue-700",
  assigned: "bg-purple-100 text-purple-700",
  in_progress: "bg-orange-100 text-orange-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-gray-100 text-gray-500",
};

const URGENCY_COLORS: Record<string, string> = {
  emergency: "bg-red-100 text-red-700 border-red-300",
  high: "bg-orange-100 text-orange-700 border-orange-300",
  normal: "bg-blue-100 text-blue-700 border-blue-300",
  low: "bg-gray-100 text-gray-600 border-gray-300",
};

const REASON_OPTIONS = [
  { value: "adoption_delivery", label: "Entrega de adopcion" },
  { value: "vet_appointment", label: "Cita veterinaria" },
  { value: "rescue", label: "Rescate" },
  { value: "shelter_transfer", label: "Transferencia entre refugios" },
  { value: "foster_placement", label: "Acogida temporal" },
  { value: "return_to_shelter", label: "Retorno al refugio" },
  { value: "event", label: "Evento" },
];

const URGENCY_OPTIONS = [
  { value: "emergency", label: "Emergencia" },
  { value: "high", label: "Alta" },
  { value: "normal", label: "Normal" },
  { value: "low", label: "Baja" },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function StatusBadge({ status, label }: { status: string; label: string }) {
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700"}`}>
      {label}
    </span>
  );
}

function UrgencyBadge({ urgency, label }: { urgency: string; label: string }) {
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-medium border ${URGENCY_COLORS[urgency] ?? "bg-gray-100 text-gray-600"}`}>
      {label}
    </span>
  );
}

function RequestCard({
  request,
  expanded,
  onToggle,
}: {
  request: TransportRequest;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden" role="article" aria-label={`Solicitud de transporte: ${request.reason_label}`}>
      <button
        onClick={onToggle}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onToggle(); }}
        className="w-full text-left p-4 flex items-center gap-3 hover:bg-gray-50 min-h-[44px]"
        aria-expanded={expanded}
      >
        <Truck className="w-5 h-5 text-gray-400 shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900">{request.reason_label}</span>
            <StatusBadge status={request.status} label={request.status_label} />
            <UrgencyBadge urgency={request.urgency} label={request.urgency_label} />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {request.animal_count} animal{request.animal_count !== 1 ? "es" : ""} - {request.requester_name}
          </p>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-gray-400" aria-hidden="true" /> : <ChevronDown className="w-5 h-5 text-gray-400" aria-hidden="true" />}
      </button>

      {expanded && (
        <div className="border-t border-gray-200 p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Pickup */}
            <div className="bg-green-50 rounded-lg p-3" role="region" aria-label="Punto de recogida">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="w-4 h-4 text-green-600" aria-hidden="true" />
                <span className="text-sm font-medium text-green-700">Recogida</span>
              </div>
              <p className="text-sm text-gray-900">{request.pickup.address}</p>
              <p className="text-sm text-gray-600">{request.pickup.city}</p>
              <div className="flex items-center gap-1 mt-1">
                <Phone className="w-3 h-3 text-gray-400" aria-hidden="true" />
                <span className="text-xs text-gray-500">{request.pickup.contact_name} - {request.pickup.contact_phone}</span>
              </div>
            </div>

            {/* Delivery */}
            <div className="bg-blue-50 rounded-lg p-3" role="region" aria-label="Punto de entrega">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="w-4 h-4 text-blue-600" aria-hidden="true" />
                <span className="text-sm font-medium text-blue-700">Entrega</span>
              </div>
              <p className="text-sm text-gray-900">{request.delivery.address}</p>
              <p className="text-sm text-gray-600">{request.delivery.city}</p>
              <div className="flex items-center gap-1 mt-1">
                <Phone className="w-3 h-3 text-gray-400" aria-hidden="true" />
                <span className="text-xs text-gray-500">{request.delivery.contact_name} - {request.delivery.contact_phone}</span>
              </div>
            </div>
          </div>

          {/* Animals */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Animales</h4>
            <div className="flex flex-wrap gap-2" role="list" aria-label="Animales a transportar">
              {request.animals.map((a, idx) => (
                <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full" role="listitem">
                  {a.name} ({a.species})
                  {a.special_needs && <span className="text-orange-600 ml-1">- {a.special_needs}</span>}
                </span>
              ))}
            </div>
          </div>

          {/* Schedule & Notes */}
          {(request.preferred_date || request.notes) && (
            <div className="text-sm text-gray-600">
              {request.preferred_date && (
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-gray-400" aria-hidden="true" />
                  <span>Fecha preferida: {request.preferred_date} {request.preferred_time ?? ""}</span>
                </div>
              )}
              {request.notes && <p className="mt-1 text-gray-500 italic">{request.notes}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TransportRequestForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [reason, setReason] = useState("adoption_delivery");
  const [urgency, setUrgency] = useState("normal");
  const [animalName, setAnimalName] = useState("");
  const [animalSpecies, setAnimalSpecies] = useState("Perro");
  const [animals, setAnimals] = useState<AnimalInfo[]>([]);
  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupCity, setPickupCity] = useState("");
  const [pickupContact, setPickupContact] = useState("");
  const [pickupPhone, setPickupPhone] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryCity, setDeliveryCity] = useState("");
  const [deliveryContact, setDeliveryContact] = useState("");
  const [deliveryPhone, setDeliveryPhone] = useState("");
  const [requesterName, setRequesterName] = useState("");
  const [requesterPhone, setRequesterPhone] = useState("");
  const [preferredDate, setPreferredDate] = useState("");
  const [notes, setNotes] = useState("");

  const addAnimal = () => {
    if (animalName.trim() && animals.length < 10) {
      setAnimals([...animals, { name: animalName.trim(), species: animalSpecies }]);
      setAnimalName("");
    }
  };

  const removeAnimal = (idx: number) => {
    setAnimals(animals.filter((_, i) => i !== idx));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (animals.length === 0) return;
    onSubmit({
      reason,
      urgency,
      pickup: { address: pickupAddress, city: pickupCity, contact_name: pickupContact, contact_phone: pickupPhone },
      delivery: { address: deliveryAddress, city: deliveryCity, contact_name: deliveryContact, contact_phone: deliveryPhone },
      animals,
      preferred_date: preferredDate || null,
      notes: notes || null,
      requester_name: requesterName,
      requester_phone: requesterPhone,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 p-6 space-y-6" aria-label="Formulario de solicitud de transporte">
      <h2 className="text-lg font-semibold text-gray-900">Nueva Solicitud de Transporte</h2>

      {/* Reason & Urgency */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-1">Motivo</label>
          <select id="reason" value={reason} onChange={(e) => setReason(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" aria-required="true">
            {REASON_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="urgency" className="block text-sm font-medium text-gray-700 mb-1">Urgencia</label>
          <select id="urgency" value={urgency} onChange={(e) => setUrgency(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
            {URGENCY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      {/* Animals */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Animales a transportar</label>
        <div className="flex gap-2 mb-2">
          <input type="text" value={animalName} onChange={(e) => setAnimalName(e.target.value)} placeholder="Nombre del animal" className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm" aria-label="Nombre del animal" />
          <select value={animalSpecies} onChange={(e) => setAnimalSpecies(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm" aria-label="Especie">
            <option value="Perro">Perro</option>
            <option value="Gato">Gato</option>
            <option value="Otro">Otro</option>
          </select>
          <button type="button" onClick={addAnimal} className="px-3 py-2 bg-green-500 text-white rounded-lg text-sm min-h-[44px] hover:bg-green-600" aria-label="Agregar animal">
            <Plus className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
        {animals.length > 0 && (
          <div className="flex flex-wrap gap-2" role="list" aria-label="Animales agregados">
            {animals.map((a, idx) => (
              <span key={idx} className="flex items-center gap-1 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full" role="listitem">
                {a.name} ({a.species})
                <button type="button" onClick={() => removeAnimal(idx)} className="text-red-500 hover:text-red-700 ml-1" aria-label={`Quitar ${a.name}`}>
                  <XCircle className="w-3 h-3" aria-hidden="true" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Pickup */}
      <fieldset className="border border-gray-200 rounded-lg p-4">
        <legend className="text-sm font-medium text-green-700 px-2">Punto de Recogida</legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input type="text" value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} placeholder="Direccion" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Direccion de recogida" />
          <input type="text" value={pickupCity} onChange={(e) => setPickupCity(e.target.value)} placeholder="Ciudad" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Ciudad de recogida" />
          <input type="text" value={pickupContact} onChange={(e) => setPickupContact(e.target.value)} placeholder="Nombre de contacto" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Contacto de recogida" />
          <input type="tel" value={pickupPhone} onChange={(e) => setPickupPhone(e.target.value)} placeholder="Telefono" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Telefono de recogida" />
        </div>
      </fieldset>

      {/* Delivery */}
      <fieldset className="border border-gray-200 rounded-lg p-4">
        <legend className="text-sm font-medium text-blue-700 px-2">Punto de Entrega</legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input type="text" value={deliveryAddress} onChange={(e) => setDeliveryAddress(e.target.value)} placeholder="Direccion" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Direccion de entrega" />
          <input type="text" value={deliveryCity} onChange={(e) => setDeliveryCity(e.target.value)} placeholder="Ciudad" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Ciudad de entrega" />
          <input type="text" value={deliveryContact} onChange={(e) => setDeliveryContact(e.target.value)} placeholder="Nombre de contacto" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Contacto de entrega" />
          <input type="tel" value={deliveryPhone} onChange={(e) => setDeliveryPhone(e.target.value)} placeholder="Telefono" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Telefono de entrega" />
        </div>
      </fieldset>

      {/* Requester & Schedule */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <input type="text" value={requesterName} onChange={(e) => setRequesterName(e.target.value)} placeholder="Su nombre" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Nombre del solicitante" />
        <input type="tel" value={requesterPhone} onChange={(e) => setRequesterPhone(e.target.value)} placeholder="Su telefono" className="border border-gray-300 rounded-lg px-3 py-2 text-sm" required aria-label="Telefono del solicitante" />
        <input type="date" value={preferredDate} onChange={(e) => setPreferredDate(e.target.value)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm" aria-label="Fecha preferida" />
      </div>

      {/* Notes */}
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">Notas adicionales</label>
        <textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} maxLength={1000} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 min-h-[44px]">
          Cancelar
        </button>
        <button type="submit" disabled={animals.length === 0} className="px-4 py-2 text-sm text-white bg-orange-500 rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] flex items-center gap-2">
          <Send className="w-4 h-4" aria-hidden="true" />
          Crear Solicitud
        </button>
      </div>
    </form>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-4" aria-busy="true" aria-label="Cargando solicitudes de transporte">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-gray-200 rounded-xl h-20" />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function TransportRequestsPage() {
  const [requests, setRequests] = useState<TransportRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    try {
      const params = statusFilter !== "all" ? `?status=${statusFilter}` : "";
      const res = await fetch(`${API_BASE}/api/transport/requests${params}`);
      if (res.ok) {
        const data = await res.json();
        setRequests(data.requests ?? []);
      }
    } catch {
      setError("Error al cargar las solicitudes");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleCreate = async (formData: Record<string, unknown>) => {
    try {
      const res = await fetch(`${API_BASE}/api/transport/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        setShowForm(false);
        setSuccessMessage("Solicitud creada exitosamente");
        setTimeout(() => setSuccessMessage(null), 3000);
        fetchRequests();
      }
    } catch {
      setError("Error al crear la solicitud");
    }
  };

  const STATUS_FILTERS = [
    { value: "all", label: "Todas" },
    { value: "pending", label: "Pendientes" },
    { value: "approved", label: "Aprobadas" },
    { value: "assigned", label: "Asignadas" },
    { value: "in_progress", label: "En progreso" },
    { value: "completed", label: "Completadas" },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            <Truck className="w-7 h-7 inline-block mr-2 text-orange-500" aria-hidden="true" />
            Solicitudes de Transporte
          </h1>
          <p className="text-gray-500 mt-1">Gestionar solicitudes de transporte de animales</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600 min-h-[44px] flex items-center gap-2"
          aria-label={showForm ? "Cerrar formulario" : "Nueva solicitud de transporte"}
        >
          <Plus className="w-4 h-4" aria-hidden="true" />
          {showForm ? "Cerrar" : "Nueva Solicitud"}
        </button>
      </div>

      {/* Success */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 flex items-center gap-2" role="status">
          <CheckCircle className="w-5 h-5" aria-hidden="true" />
          {successMessage}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 flex items-center gap-2" role="alert">
          <AlertCircle className="w-5 h-5" aria-hidden="true" />
          {error}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <div className="mb-6">
          <TransportRequestForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-4 overflow-x-auto" role="group" aria-label="Filtrar por estado">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={`px-3 py-2 text-sm rounded-lg whitespace-nowrap min-h-[44px] transition-colors ${
              statusFilter === f.value
                ? "bg-orange-500 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            aria-pressed={statusFilter === f.value}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Request list */}
      {loading ? (
        <LoadingSkeleton />
      ) : requests.length === 0 ? (
        <div className="text-center py-12 text-gray-500" role="status">
          <Truck className="w-12 h-12 mx-auto mb-3 text-gray-300" aria-hidden="true" />
          <p>No hay solicitudes de transporte</p>
        </div>
      ) : (
        <div className="space-y-3" role="list" aria-label="Lista de solicitudes de transporte">
          {requests.map((r) => (
            <div key={r.id} role="listitem">
              <RequestCard
                request={r}
                expanded={expandedId === r.id}
                onToggle={() => setExpandedId(expandedId === r.id ? null : r.id)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
