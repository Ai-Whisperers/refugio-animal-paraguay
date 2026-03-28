"use client";

import { useEffect, useState, useCallback } from "react";
import { User, Truck, Phone, Mail, MapPin, Clock, CheckCircle, XCircle, Search, Plus, Shield, Star } from "lucide-react";

interface AvailabilitySlot { day: string; start_time: string; end_time: string; }
interface Driver {
  id: string; full_name: string; email: string; phone: string;
  vehicle_type: string; vehicle_plate: string; license_number: string;
  has_animal_transport_box: boolean; max_animal_capacity: number;
  coverage_areas: string[]; availability: AvailabilitySlot[];
  bio: string | null; status: string; admin_notes: string | null;
  registered_at: string; updated_at: string; total_trips: number; rating: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800", verified: "bg-blue-100 text-blue-800",
  active: "bg-green-100 text-green-800", inactive: "bg-gray-100 text-gray-800",
  suspended: "bg-red-100 text-red-800",
};
const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente", verified: "Verificado", active: "Activo",
  inactive: "Inactivo", suspended: "Suspendido",
};
const VEHICLE_LABELS: Record<string, string> = {
  car: "Auto", suv: "Camioneta", van: "Furgoneta", truck: "Camion", motorcycle: "Motocicleta",
};
const DAY_LABELS: Record<string, string> = {
  monday: "Lun", tuesday: "Mar", wednesday: "Mie", thursday: "Jue",
  friday: "Vie", saturday: "Sab", sunday: "Dom",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status] ?? "bg-gray-100 text-gray-800"}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function DriverCard({ driver, onVerify, onReject }: { driver: Driver; onVerify: (id: string) => void; onReject: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-primary)]/10">
            <User className="h-5 w-5 text-[var(--color-primary)]" />
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text-primary)]">{driver.full_name}</h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              {VEHICLE_LABELS[driver.vehicle_type] ?? driver.vehicle_type} &mdash; {driver.vehicle_plate}
            </p>
          </div>
        </div>
        <StatusBadge status={driver.status} />
      </div>
      <div className="mt-3 grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
        <div className="flex items-center gap-2 text-[var(--color-text-secondary)]"><Mail className="h-4 w-4" />{driver.email}</div>
        <div className="flex items-center gap-2 text-[var(--color-text-secondary)]"><Phone className="h-4 w-4" />{driver.phone}</div>
        <div className="flex items-center gap-2 text-[var(--color-text-secondary)]"><Truck className="h-4 w-4" />Capacidad: {driver.max_animal_capacity} animales</div>
        {driver.coverage_areas.length > 0 && (
          <div className="flex items-center gap-2 text-[var(--color-text-secondary)]"><MapPin className="h-4 w-4" />{driver.coverage_areas.join(", ")}</div>
        )}
      </div>
      {driver.availability.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {driver.availability.map((slot, i) => (
            <span key={i} className="inline-flex items-center gap-1 rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
              <Clock className="h-3 w-3" />{DAY_LABELS[slot.day] ?? slot.day} {slot.start_time}-{slot.end_time}
            </span>
          ))}
        </div>
      )}
      {driver.rating > 0 && (
        <div className="mt-2 flex items-center gap-1 text-sm text-yellow-600">
          <Star className="h-4 w-4 fill-current" />{driver.rating.toFixed(1)} &middot; {driver.total_trips} viajes
        </div>
      )}
      <button onClick={() => setExpanded(!expanded)} className="mt-2 text-xs text-[var(--color-primary)] hover:underline">
        {expanded ? "Menos detalles" : "Mas detalles"}
      </button>
      {expanded && (
        <div className="mt-2 space-y-1 border-t border-[var(--color-border)] pt-2 text-sm">
          <p><span className="font-medium">Licencia:</span> {driver.license_number}</p>
          <p><span className="font-medium">Caja de transporte:</span> {driver.has_animal_transport_box ? "Si" : "No"}</p>
          {driver.bio && <p><span className="font-medium">Bio:</span> {driver.bio}</p>}
          {driver.admin_notes && <p><span className="font-medium">Notas admin:</span> {driver.admin_notes}</p>}
        </div>
      )}
      {driver.status === "pending" && (
        <div className="mt-3 flex gap-2 border-t border-[var(--color-border)] pt-3">
          <button onClick={() => onVerify(driver.id)} className="flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700">
            <CheckCircle className="h-4 w-4" />Verificar
          </button>
          <button onClick={() => onReject(driver.id)} className="flex items-center gap-1 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700">
            <XCircle className="h-4 w-4" />Rechazar
          </button>
        </div>
      )}
    </div>
  );
}

function RegistrationForm({ onSubmit }: { onSubmit: () => void }) {
  const [formData, setFormData] = useState({
    full_name: "", email: "", phone: "", vehicle_type: "car",
    vehicle_plate: "", license_number: "", has_animal_transport_box: false,
    max_animal_capacity: 1, coverage_areas: "", bio: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = { ...formData, coverage_areas: formData.coverage_areas.split(",").map((a) => a.trim()).filter(Boolean), availability: [] };
      const res = await fetch(`${API_BASE}/api/transport/drivers/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("Error al registrar conductor");
      onSubmit();
      setFormData({ full_name: "", email: "", phone: "", vehicle_type: "car", vehicle_plate: "", license_number: "", has_animal_transport_box: false, max_animal_capacity: 1, coverage_areas: "", bio: "" });
    } finally { setSubmitting(false); }
  };
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div><label className="mb-1 block text-sm font-medium">Nombre completo</label><input type="text" required value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
        <div><label className="mb-1 block text-sm font-medium">Email</label><input type="email" required value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
        <div><label className="mb-1 block text-sm font-medium">Telefono</label><input type="tel" required value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
        <div><label className="mb-1 block text-sm font-medium">Tipo de vehiculo</label><select value={formData.vehicle_type} onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2">{Object.entries(VEHICLE_LABELS).map(([val, label]) => (<option key={val} value={val}>{label}</option>))}</select></div>
        <div><label className="mb-1 block text-sm font-medium">Placa del vehiculo</label><input type="text" required value={formData.vehicle_plate} onChange={(e) => setFormData({ ...formData, vehicle_plate: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
        <div><label className="mb-1 block text-sm font-medium">Numero de licencia</label><input type="text" required value={formData.license_number} onChange={(e) => setFormData({ ...formData, license_number: e.target.value })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
      </div>
      <div><label className="mb-1 block text-sm font-medium">Areas de cobertura (separadas por coma)</label><input type="text" value={formData.coverage_areas} onChange={(e) => setFormData({ ...formData, coverage_areas: e.target.value })} placeholder="Asuncion, Lambare, San Lorenzo" className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex items-center gap-2"><input type="checkbox" id="transport_box" checked={formData.has_animal_transport_box} onChange={(e) => setFormData({ ...formData, has_animal_transport_box: e.target.checked })} className="h-4 w-4 rounded" /><label htmlFor="transport_box" className="text-sm font-medium">Tiene caja de transporte</label></div>
        <div><label className="mb-1 block text-sm font-medium">Capacidad maxima de animales</label><input type="number" min={1} max={20} value={formData.max_animal_capacity} onChange={(e) => setFormData({ ...formData, max_animal_capacity: parseInt(e.target.value) || 1 })} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
      </div>
      <div><label className="mb-1 block text-sm font-medium">Biografia / experiencia</label><textarea value={formData.bio} onChange={(e) => setFormData({ ...formData, bio: e.target.value })} rows={3} maxLength={500} className="w-full rounded-lg border border-[var(--color-border)] px-3 py-2" /></div>
      <button type="submit" disabled={submitting} className="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 font-medium text-white hover:bg-[var(--color-primary-dark)] disabled:opacity-50"><Plus className="h-4 w-4" />{submitting ? "Registrando..." : "Registrar conductor"}</button>
    </form>
  );
}

function LoadingSkeleton() {
  return (<div className="space-y-4">{[1, 2, 3].map((i) => (<div key={i} className="h-40 animate-pulse rounded-lg bg-gray-100" />))}</div>);
}

export default function VolunteerDriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [totalDrivers, setTotalDrivers] = useState(0);

  const fetchDrivers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.set("search", searchQuery);
      if (statusFilter) params.set("status", statusFilter);
      const res = await fetch(`${API_BASE}/api/transport/drivers/?${params.toString()}`);
      if (!res.ok) throw new Error("Error fetching drivers");
      const data = await res.json();
      setDrivers(data.drivers ?? []);
      setTotalDrivers(data.total ?? 0);
    } catch { setDrivers([]); } finally { setLoading(false); }
  }, [searchQuery, statusFilter]);

  useEffect(() => { fetchDrivers(); }, [fetchDrivers]);

  const handleVerify = async (driverId: string) => {
    await fetch(`${API_BASE}/api/transport/drivers/${driverId}/verify`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verified: true, admin_notes: "Verificado por admin" }) });
    fetchDrivers();
  };
  const handleReject = async (driverId: string) => {
    await fetch(`${API_BASE}/api/transport/drivers/${driverId}/verify`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verified: false, admin_notes: "Documentacion incompleta" }) });
    fetchDrivers();
  };

  const statusButtons = ["", "pending", "verified", "active", "inactive", "suspended"];

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Conductores Voluntarios</h1>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{totalDrivers} conductores registrados</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-4 py-2 font-medium text-white hover:bg-[var(--color-primary-dark)]">
          <Shield className="h-4 w-4" />{showForm ? "Cerrar formulario" : "Nuevo conductor"}
        </button>
      </div>
      {showForm && (
        <div className="mb-6 rounded-lg border border-[var(--color-border)] bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">Registro de conductor</h2>
          <RegistrationForm onSubmit={() => { setShowForm(false); fetchDrivers(); }} />
        </div>
      )}
      <div className="mb-6 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Buscar por nombre o email..." className="w-full rounded-lg border border-[var(--color-border)] py-2 pl-10 pr-4" />
        </div>
        <div className="flex flex-wrap gap-2">
          {statusButtons.map((s) => (
            <button key={s} onClick={() => setStatusFilter(s)} className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${statusFilter === s ? "bg-[var(--color-primary)] text-white" : "bg-gray-100 text-[var(--color-text-secondary)] hover:bg-gray-200"}`}>
              {s === "" ? "Todos" : STATUS_LABELS[s] ?? s}
            </button>
          ))}
        </div>
      </div>
      {loading ? (<LoadingSkeleton />) : drivers.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-white p-12 text-center">
          <Truck className="mx-auto h-12 w-12 text-[var(--color-text-muted)]" />
          <h3 className="mt-3 font-semibold text-[var(--color-text-primary)]">No se encontraron conductores</h3>
          <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Ajuste los filtros o registre un nuevo conductor.</p>
        </div>
      ) : (
        <div className="space-y-4">{drivers.map((driver) => (<DriverCard key={driver.id} driver={driver} onVerify={handleVerify} onReject={handleReject} />))}</div>
      )}
    </div>
  );
}
