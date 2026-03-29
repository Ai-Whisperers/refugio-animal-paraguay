"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PreferenceResponse {
  notification_type: string;
  channel: string;
  enabled: boolean;
}

interface PreferenceListResponse {
  preferences: PreferenceResponse[];
}

type PreferenceMatrix = Record<string, Record<string, boolean>>;

// Ordered list of notification types with human-readable labels
const NOTIFICATION_TYPES: { key: string; label: string; description: string }[] = [
  {
    key: "adoption_request_created",
    label: "Adoption Application Received",
    description: "When a new adoption application is submitted",
  },
  {
    key: "adoption_status_changed",
    label: "Adoption Status Changed",
    description: "When an adoption application status is updated",
  },
  {
    key: "donation_received",
    label: "Donation Received",
    description: "When a new donation is confirmed",
  },
  {
    key: "donation_refunded",
    label: "Donation Refunded",
    description: "When a donation is refunded",
  },
  {
    key: "animal_intake_completed",
    label: "Animal Intake Completed",
    description: "When a new animal completes intake",
  },
  {
    key: "animal_status_changed",
    label: "Animal Status Changed",
    description: "When an animal's status changes",
  },
  {
    key: "system_alert",
    label: "System Alerts",
    description: "Important system-level notifications",
  },
  {
    key: "gdpr_request",
    label: "GDPR Requests",
    description: "When a data subject submits a GDPR request",
  },
];

const CHANNELS = ["in_app", "email"] as const;
type Channel = (typeof CHANNELS)[number];

const CHANNEL_LABELS: Record<Channel, string> = {
  in_app: "In-App",
  email: "Email",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildMatrix(preferences: PreferenceResponse[]): PreferenceMatrix {
  const matrix: PreferenceMatrix = {};
  for (const type of NOTIFICATION_TYPES) {
    matrix[type.key] = {};
    for (const ch of CHANNELS) {
      matrix[type.key][ch] = true; // default enabled
    }
  }
  for (const pref of preferences) {
    if (matrix[pref.notification_type]) {
      matrix[pref.notification_type][pref.channel] = pref.enabled;
    }
  }
  return matrix;
}

function matrixToPayload(
  matrix: PreferenceMatrix
): { notification_type: string; channel: string; enabled: boolean }[] {
  const items: { notification_type: string; channel: string; enabled: boolean }[] = [];
  for (const [notifType, channels] of Object.entries(matrix)) {
    for (const [channel, enabled] of Object.entries(channels)) {
      items.push({ notification_type: notifType, channel, enabled });
    }
  }
  return items;
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function NotificationPreferencesPage() {
  const [matrix, setMatrix] = useState<PreferenceMatrix>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch current preferences
  const fetchPreferences = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<PreferenceListResponse>("/notification-preferences", {
        requiresAuth: true,
      });
      setMatrix(buildMatrix(data.preferences));
    } catch {
      setError("Failed to load notification preferences. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  // Toggle a single preference
  const handleToggle = (notifType: string, channel: string) => {
    setMatrix((prev) => ({
      ...prev,
      [notifType]: {
        ...prev[notifType],
        [channel]: !prev[notifType]?.[channel],
      },
    }));
    setSuccessMessage(null);
  };

  // Save all preferences
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await api.put("/notification-preferences", { preferences: matrixToPayload(matrix) }, {
        requiresAuth: true,
      });
      setSuccessMessage("Preferences saved successfully.");
    } catch {
      setError("Failed to save preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Notification Preferences</h1>
        <p className="mt-1 text-sm text-gray-500">
          Choose which notifications you receive and through which channels.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {/* Success banner */}
      {successMessage && (
        <div
          role="status"
          className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700"
        >
          {successMessage}
        </div>
      )}

      {/* Preferences table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="py-3 pl-6 pr-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500"
              >
                Notification type
              </th>
              {CHANNELS.map((ch) => (
                <th
                  key={ch}
                  scope="col"
                  className="px-6 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500"
                >
                  {CHANNEL_LABELS[ch]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {NOTIFICATION_TYPES.map((type) => (
              <tr key={type.key} className="hover:bg-gray-50">
                <td className="py-4 pl-6 pr-3">
                  <div className="font-medium text-gray-900">{type.label}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                </td>
                {CHANNELS.map((ch) => {
                  const enabled = matrix[type.key]?.[ch] ?? true;
                  return (
                    <td key={ch} className="px-6 py-4 text-center">
                      <button
                        type="button"
                        role="switch"
                        aria-checked={enabled}
                        aria-label={`${enabled ? "Disable" : "Enable"} ${type.label} via ${CHANNEL_LABELS[ch]}`}
                        onClick={() => handleToggle(type.key, ch)}
                        className={[
                          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                          enabled ? "bg-primary" : "bg-gray-200",
                        ].join(" ")}
                      >
                        <span
                          className={[
                            "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
                            enabled ? "translate-x-6" : "translate-x-1",
                          ].join(" ")}
                        />
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Save button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? (
            <>
              <span
                className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                aria-hidden="true"
              />
              Saving...
            </>
          ) : (
            "Save preferences"
          )}
        </button>
      </div>
    </div>
  );
}
