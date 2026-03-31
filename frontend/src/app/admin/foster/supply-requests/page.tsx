"use client";

import { useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SupplyRequest {
  id: string;
  foster_profile_id: string;
  placement_id: string | null;
  supply_type: string;
  description: string;
  quantity: number | null;
  status: string;
  resolved_at: string | null;
  resolved_by: string | null;
  staff_notes: string | null;
  created_at: string;
  updated_at: string;
}

interface SupplyRequestListResponse {
  items: SupplyRequest[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PY", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusBadge(status: string): string {
  const map: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    approved: "bg-blue-100 text-blue-800",
    fulfilled: "bg-green-100 text-green-800",
    rejected: "bg-red-100 text-red-800",
  };
  return map[status] ?? "bg-gray-100 text-gray-800";
}

function supplyTypeLabel(type: string): string {
  const map: Record<string, string> = {
    food: "Alimento",
    medication: "Medicamento",
    bedding: "Cama / Ropa",
    toys: "Juguetes",
    transport: "Transporte",
    grooming: "Aseo",
    other: "Otro",
  };
  return map[type] ?? type;
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: "Pendiente",
    approved: "Aprobado",
    fulfilled: "Entregado",
    rejected: "Rechazado",
  };
  return map[status] ?? status;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function FosterSupplyRequestsPage() {
  const [requests, setRequests] = useState<SupplyRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [staffNotes, setStaffNotes] = useState<Record<string, string>>({});

  async function fetchRequests() {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (statusFilter) params.set("status", statusFilter);
    if (typeFilter) params.set("supply_type", typeFilter);
    try {
      const res = await fetch(`/api/staff/foster/supply-requests?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SupplyRequestListResponse = await res.json();
      setRequests(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar solicitudes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRequests();
  }, [page, statusFilter, typeFilter]);

  async function handleAction(requestId: string, action: "fulfill" | "reject") {
    setActionLoading(requestId + action);
    try {
      const body = staffNotes[requestId]
        ? JSON.stringify({ notes: staffNotes[requestId] })
        : null;
      const res = await fetch(
        `/api/staff/foster/supply-requests/${requestId}/${action}`,
        {
          method: "PUT",
          headers: body ? { "Content-Type": "application/json" } : {},
          body,
        }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      await fetchRequests();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al procesar solicitud");
    } finally {
      setActionLoading(null);
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Solicitudes de Insumos — Familias de Acogida
      </h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estado
          </label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            <option value="pending">Pendiente</option>
            <option value="approved">Aprobado</option>
            <option value="fulfilled">Entregado</option>
            <option value="rejected">Rechazado</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tipo de Insumo
          </label>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            <option value="food">Alimento</option>
            <option value="medication">Medicamento</option>
            <option value="bedding">Cama / Ropa</option>
            <option value="toys">Juguetes</option>
            <option value="transport">Transporte</option>
            <option value="grooming">Aseo</option>
            <option value="other">Otro</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading && (
        <p className="text-gray-500 text-sm">Cargando solicitudes...</p>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && requests.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No hay solicitudes de insumos que coincidan con los filtros seleccionados.
        </div>
      )}

      {!loading && !error && requests.length > 0 && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {total} solicitud{total !== 1 ? "es" : ""} encontrada{total !== 1 ? "s" : ""}
          </p>
          <div className="space-y-4">
            {requests.map((req) => (
              <div
                key={req.id}
                className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-900">
                        {supplyTypeLabel(req.supply_type)}
                      </span>
                      {req.quantity && (
                        <span className="text-gray-500 text-sm">
                          × {req.quantity}
                        </span>
                      )}
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusBadge(req.status)}`}
                      >
                        {statusLabel(req.status)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{req.description}</p>
                    <div className="text-xs text-gray-400 space-y-0.5">
                      <div>Solicitado: {formatDate(req.created_at)}</div>
                      {req.resolved_at && (
                        <div>Resuelto: {formatDate(req.resolved_at)}</div>
                      )}
                      {req.staff_notes && (
                        <div className="text-gray-500 italic">
                          Nota: {req.staff_notes}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions — only for non-terminal states */}
                  {req.status !== "fulfilled" && req.status !== "rejected" && (
                    <div className="flex flex-col gap-2 min-w-[180px]">
                      <textarea
                        placeholder="Nota del personal (opcional)"
                        value={staffNotes[req.id] ?? ""}
                        onChange={(e) =>
                          setStaffNotes((prev) => ({
                            ...prev,
                            [req.id]: e.target.value,
                          }))
                        }
                        rows={2}
                        className="border border-gray-300 rounded px-2 py-1 text-xs resize-none"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAction(req.id, "fulfill")}
                          disabled={actionLoading !== null}
                          className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs font-medium py-1.5 px-3 rounded"
                        >
                          {actionLoading === req.id + "fulfill"
                            ? "..."
                            : "Entregar"}
                        </button>
                        <button
                          onClick={() => handleAction(req.id, "reject")}
                          disabled={actionLoading !== null}
                          className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs font-medium py-1.5 px-3 rounded"
                        >
                          {actionLoading === req.id + "reject"
                            ? "..."
                            : "Rechazar"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Anterior
              </button>
              <span className="px-3 py-1 text-sm text-gray-600">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
