"use client";

/**
 * Adoption requests management page for staff admin panel.
 * Lists requests with status filter, supports status transitions.
 */

import { useCallback, useEffect, useState } from "react";
import type { AdoptionRequest, AdoptionRequestStatus } from "@/types/api";
import {
  listAdoptionRequests,
  updateAdoptionRequestStatus,
} from "@/lib/admin-api";
import StatusBadge from "@/components/admin/StatusBadge";
import ConfirmDialog from "@/components/admin/ConfirmDialog";

const STATUS_FILTER_OPTIONS: Array<{
  value: AdoptionRequestStatus | "";
  label: string;
}> = [
  { value: "", label: "All Statuses" },
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "cancelled", label: "Cancelled" },
];

/** Valid status transitions matching backend state machine. */
const ALLOWED_TRANSITIONS: Record<AdoptionRequestStatus, AdoptionRequestStatus[]> = {
  pending: ["approved", "rejected", "cancelled"],
  approved: ["cancelled"],
  rejected: ["cancelled"],
  cancelled: [],
};

const TRANSITION_LABELS: Record<AdoptionRequestStatus, string> = {
  approved: "Approve",
  rejected: "Reject",
  cancelled: "Cancel",
  pending: "Pending",
};

const TRANSITION_COLORS: Record<AdoptionRequestStatus, string> = {
  approved: "bg-green-600 hover:bg-green-700 text-white",
  rejected: "bg-red-600 hover:bg-red-700 text-white",
  cancelled: "bg-gray-600 hover:bg-gray-700 text-white",
  pending: "bg-yellow-600 hover:bg-yellow-700 text-white",
};

const PAGE_SIZE = 20;

export default function AdoptionsPage() {
  const [requests, setRequests] = useState<AdoptionRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<
    AdoptionRequestStatus | ""
  >("");
  const [page, setPage] = useState(0);

  // Action state
  const [actionRequest, setActionRequest] = useState<{
    request: AdoptionRequest;
    newStatus: AdoptionRequestStatus;
  } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchRequests = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listAdoptionRequests({
        status: statusFilter || undefined,
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setRequests(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load adoption requests"
      );
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, page]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleStatusChange = async () => {
    if (!actionRequest) return;
    setIsUpdating(true);
    try {
      await updateAdoptionRequestStatus(
        actionRequest.request.id,
        actionRequest.newStatus
      );
      setActionRequest(null);
      await fetchRequests();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update request status"
      );
    } finally {
      setIsUpdating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const truncateId = (id: string) => {
    return id.length > 8 ? `${id.slice(0, 8)}...` : id;
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Adoption Requests</h1>
        <p className="text-sm text-gray-500">
          Review and process adoption applications
        </p>
      </div>

      {/* Filters */}
      <div className="flex space-x-4 mb-6">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as AdoptionRequestStatus | "");
            setPage(0);
          }}
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">
              Loading adoption requests...
            </p>
          </div>
        ) : requests.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No adoption requests found.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Request ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Animal ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Adopter ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Submitted
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Notes
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {requests.map((req) => {
                const transitions = ALLOWED_TRANSITIONS[req.status] ?? [];
                return (
                  <tr key={req.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {truncateId(req.id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {truncateId(req.animal_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {truncateId(req.adopter_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={req.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(req.submitted_at)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {req.notes ?? "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      {transitions.length > 0 ? (
                        <div className="flex justify-end space-x-2">
                          {transitions.map((newStatus) => (
                            <button
                              key={newStatus}
                              onClick={() =>
                                setActionRequest({
                                  request: req,
                                  newStatus,
                                })
                              }
                              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${TRANSITION_COLORS[newStatus]}`}
                            >
                              {TRANSITION_LABELS[newStatus]}
                            </button>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-xs">
                          No actions
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && requests.length > 0 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page + 1}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={requests.length < PAGE_SIZE}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!actionRequest}
        title={`${actionRequest ? TRANSITION_LABELS[actionRequest.newStatus] : ""} Adoption Request`}
        message={
          actionRequest
            ? `Are you sure you want to ${TRANSITION_LABELS[actionRequest.newStatus].toLowerCase()} this adoption request?${
                actionRequest.newStatus === "approved"
                  ? " This will also mark the animal as adopted."
                  : ""
              }`
            : ""
        }
        confirmLabel={
          actionRequest ? TRANSITION_LABELS[actionRequest.newStatus] : "Confirm"
        }
        onConfirm={handleStatusChange}
        onCancel={() => setActionRequest(null)}
        isLoading={isUpdating}
      />
    </div>
  );
}
