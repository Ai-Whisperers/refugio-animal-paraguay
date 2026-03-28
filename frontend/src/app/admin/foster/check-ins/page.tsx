"use client";

import { useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CheckIn {
  id: string;
  foster_placement_id: string;
  check_in_type: string;
  status: string;
  scheduled_at: string;
  completed_at: string | null;
  notes: string | null;
  cancellation_reason: string | null;
  interval_days: number;
  reminder_sent_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

interface CheckInListResponse {
  items: CheckIn[];
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
    completed: "bg-green-100 text-green-800",
    missed: "bg-red-100 text-red-800",
    cancelled: "bg-gray-100 text-gray-600",
  };
  return map[status] ?? "bg-gray-100 text-gray-600";
}

function isOverdue(checkIn: CheckIn): boolean {
  return (
    checkIn.status === "pending" && new Date(checkIn.scheduled_at) < new Date()
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function FosterCheckInsPage() {
  const [data, setData] = useState<CheckInListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysAhead, setDaysAhead] = useState(7);
  const [includeOverdue, setIncludeOverdue] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  async function fetchCheckIns() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        days_ahead: String(daysAhead),
        include_overdue: String(includeOverdue),
        page_size: "50",
      });
      const resp = await fetch(
        `/api/staff/foster/check-ins/upcoming?${params.toString()}`,
        { credentials: "include" }
      );
      if (!resp.ok) {
        throw new Error(`Server responded with ${resp.status}`);
      }
      const json = (await resp.json()) as CheckInListResponse;
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load check-ins");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchCheckIns();
  }, [daysAhead, includeOverdue]);

  async function handleComplete(checkInId: string) {
    setActionLoading(checkInId);
    try {
      const resp = await fetch(
        `/api/staff/foster/check-ins/${checkInId}/complete`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ auto_schedule_next: true }),
        }
      );
      if (!resp.ok) {
        const body = (await resp.json()) as { detail?: string };
        throw new Error(body.detail ?? "Failed to complete check-in");
      }
      await fetchCheckIns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error completing check-in");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleSendReminder(checkInId: string) {
    setActionLoading(`remind-${checkInId}`);
    try {
      const resp = await fetch(
        `/api/staff/foster/check-ins/${checkInId}/remind`,
        {
          method: "POST",
          credentials: "include",
        }
      );
      if (!resp.ok) {
        const body = (await resp.json()) as { detail?: string };
        throw new Error(body.detail ?? "Failed to send reminder");
      }
      await fetchCheckIns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error sending reminder");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleCancel(checkInId: string) {
    if (!confirm("Cancel this check-in?")) return;
    setActionLoading(`cancel-${checkInId}`);
    try {
      const resp = await fetch(
        `/api/staff/foster/check-ins/${checkInId}/cancel`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({}),
        }
      );
      if (!resp.ok) {
        const body = (await resp.json()) as { detail?: string };
        throw new Error(body.detail ?? "Failed to cancel check-in");
      }
      await fetchCheckIns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error cancelling check-in");
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Foster Check-In Schedule
        </h1>
        <p className="text-gray-500 mt-1 text-sm">
          Upcoming and overdue welfare check-ins for active foster placements.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div>
          <label
            htmlFor="days-ahead"
            className="block text-xs font-medium text-gray-600 mb-1"
          >
            Look-ahead window
          </label>
          <select
            id="days-ahead"
            value={daysAhead}
            onChange={(e) => setDaysAhead(Number(e.target.value))}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm"
          >
            <option value={3}>3 days</option>
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>
        <div className="flex items-end gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={includeOverdue}
              onChange={(e) => setIncludeOverdue(e.target.checked)}
              className="rounded"
            />
            Include overdue
          </label>
        </div>
        <div className="flex items-end">
          <button
            onClick={() => void fetchCheckIns()}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-10 text-gray-400 text-sm">
          Loading check-ins...
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && data && data.total === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg font-medium">No check-ins due</p>
          <p className="text-sm mt-1">
            No upcoming or overdue check-ins in the selected window.
          </p>
        </div>
      )}

      {/* Check-in table */}
      {!loading && !error && data && data.total > 0 && (
        <>
          <p className="text-sm text-gray-500 mb-3">
            Showing {data.items.length} of {data.total} check-in
            {data.total !== 1 ? "s" : ""}
          </p>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Scheduled</th>
                  <th className="px-4 py-3 text-left">Placement</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Reminder sent</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {data.items.map((ci) => (
                  <tr
                    key={ci.id}
                    className={isOverdue(ci) ? "bg-red-50" : ""}
                  >
                    <td className="px-4 py-3 font-medium text-gray-800 whitespace-nowrap">
                      {formatDate(ci.scheduled_at)}
                      {isOverdue(ci) && (
                        <span className="ml-2 text-xs font-semibold text-red-600 uppercase">
                          Overdue
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                      {ci.foster_placement_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 text-gray-600 capitalize">
                      {ci.check_in_type}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${statusBadge(ci.status)}`}
                      >
                        {ci.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {ci.reminder_sent_at
                        ? formatDate(ci.reminder_sent_at)
                        : "Not sent"}
                    </td>
                    <td className="px-4 py-3">
                      {ci.status === "pending" && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => void handleComplete(ci.id)}
                            disabled={actionLoading === ci.id}
                            className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                          >
                            {actionLoading === ci.id
                              ? "Saving…"
                              : "Complete"}
                          </button>
                          <button
                            onClick={() => void handleSendReminder(ci.id)}
                            disabled={actionLoading === `remind-${ci.id}`}
                            className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                          >
                            {actionLoading === `remind-${ci.id}`
                              ? "Sending…"
                              : "Remind"}
                          </button>
                          <button
                            onClick={() => void handleCancel(ci.id)}
                            disabled={actionLoading === `cancel-${ci.id}`}
                            className="px-2 py-1 text-xs border border-gray-300 text-gray-600 rounded hover:bg-gray-50 disabled:opacity-50 transition-colors"
                          >
                            {actionLoading === `cancel-${ci.id}`
                              ? "Cancelling…"
                              : "Cancel"}
                          </button>
                        </div>
                      )}
                      {ci.status !== "pending" && (
                        <span className="text-xs text-gray-400 italic">
                          No actions available
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
