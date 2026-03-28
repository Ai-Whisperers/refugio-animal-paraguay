"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Wifi,
  WifiOff,
  Clock,
  Trash2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { useNetworkStatus } from "@/lib/useNetworkStatus";
import {
  type QueuedDonation,
  addToQueue,
  getQueuedDonations,
  removeFromQueue,
  processQueue,
} from "@/lib/offlineDonationQueue";

// -- Toast component for connection status ----------------------------------

function ConnectionToast({
  isOnline,
  wasOffline,
}: {
  isOnline: boolean;
  wasOffline: boolean;
}) {
  if (wasOffline && isOnline) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="fixed top-4 right-4 z-50 flex items-center gap-2 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg"
      >
        <Wifi className="w-5 h-5" aria-hidden="true" />
        <span>Conexion restaurada</span>
      </div>
    );
  }

  if (!isOnline) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="fixed top-4 right-4 z-50 flex items-center gap-2 bg-yellow-600 text-white px-4 py-3 rounded-lg shadow-lg"
      >
        <WifiOff className="w-5 h-5" aria-hidden="true" />
        <span>Sin conexion a internet</span>
      </div>
    );
  }

  return null;
}

// -- Queued donations list --------------------------------------------------

interface QueuedDonationsListProps {
  donations: QueuedDonation[];
  onDelete: (id: number) => void;
  isProcessing: boolean;
}

function QueuedDonationsList({
  donations,
  onDelete,
  isProcessing,
}: QueuedDonationsListProps) {
  if (donations.length === 0) return null;

  return (
    <div className="mt-4 border border-yellow-200 rounded-lg bg-yellow-50 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-5 h-5 text-yellow-600" aria-hidden="true" />
        <h3 className="font-semibold text-yellow-800">
          {donations.length} donacion{donations.length !== 1 ? "es" : ""}{" "}
          pendiente{donations.length !== 1 ? "s" : ""}
        </h3>
      </div>
      <ul className="space-y-2" role="list" aria-label="Donaciones en cola">
        {donations.map((d) => (
          <li
            key={d.id}
            className="flex items-center justify-between bg-white rounded-md px-3 py-2 text-sm"
          >
            <div>
              <span className="font-medium">
                {d.currency} {d.amount.toLocaleString()}
              </span>
              {d.name && (
                <span className="text-gray-500 ml-2">— {d.name}</span>
              )}
              {d.retries > 0 && (
                <span className="text-orange-600 ml-2 text-xs">
                  (Reintento {d.retries}/3)
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={() => onDelete(d.id!)}
              disabled={isProcessing}
              className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-md min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label={`Eliminar donacion de ${d.currency} ${d.amount}`}
            >
              <Trash2 className="w-4 h-4" aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// -- Submission feedback banner ---------------------------------------------

interface FeedbackBannerProps {
  type: "success" | "offline" | "error" | "retrying" | "queue-full";
  message: string;
  onDismiss: () => void;
}

function FeedbackBanner({ type, message, onDismiss }: FeedbackBannerProps) {
  const styles = {
    success: "bg-green-50 border-green-200 text-green-800",
    offline: "bg-yellow-50 border-yellow-200 text-yellow-800",
    error: "bg-red-50 border-red-200 text-red-800",
    retrying: "bg-orange-50 border-orange-200 text-orange-800",
    "queue-full": "bg-red-50 border-red-200 text-red-800",
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5" aria-hidden="true" />,
    offline: <WifiOff className="w-5 h-5" aria-hidden="true" />,
    error: <AlertCircle className="w-5 h-5" aria-hidden="true" />,
    retrying: <RefreshCw className="w-5 h-5 animate-spin" aria-hidden="true" />,
    "queue-full": <AlertCircle className="w-5 h-5" aria-hidden="true" />,
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${styles[type]}`}
    >
      {icons[type]}
      <span className="flex-1">{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="text-current opacity-60 hover:opacity-100 min-h-[44px] min-w-[44px] flex items-center justify-center"
        aria-label="Cerrar mensaje"
      >
        &times;
      </button>
    </div>
  );
}

// -- Main manager component -------------------------------------------------

export interface OfflineDonationManagerProps {
  onSubmitOnline: (data: {
    amount: number;
    currency: string;
    name: string;
    email: string;
    message: string;
  }) => Promise<boolean>;
  children: (props: {
    handleSubmit: (data: {
      amount: number;
      currency: string;
      name: string;
      email: string;
      message: string;
    }) => Promise<void>;
    isProcessing: boolean;
    isOnline: boolean;
  }) => React.ReactNode;
}

export default function OfflineDonationManager({
  onSubmitOnline,
  children,
}: OfflineDonationManagerProps) {
  const { isOnline, wasOffline } = useNetworkStatus();
  const [queuedDonations, setQueuedDonations] = useState<QueuedDonation[]>([]);
  const [feedback, setFeedback] = useState<{
    type: "success" | "offline" | "error" | "retrying" | "queue-full";
    message: string;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const refreshQueue = useCallback(async () => {
    try {
      const donations = await getQueuedDonations();
      setQueuedDonations(donations);
    } catch {
      // IndexedDB not available
    }
  }, []);

  // Load queue on mount
  useEffect(() => {
    refreshQueue();
  }, [refreshQueue]);

  // Auto-process queue when coming back online
  useEffect(() => {
    if (isOnline && wasOffline && queuedDonations.length > 0) {
      processQueuedDonations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline, wasOffline]);

  const processQueuedDonations = useCallback(async () => {
    if (isProcessing) return;
    setIsProcessing(true);
    setFeedback({ type: "retrying", message: "Reintentando..." });

    const result = await processQueue(
      () => {
        // onSuccess per donation
      },
      (_donation, attempt) => {
        setFeedback({
          type: "retrying",
          message: `Reintentando... (intento ${attempt}/3)`,
        });
      },
      () => {
        // onFailed
      }
    );

    if (result.submitted > 0 && result.failed === 0) {
      setFeedback({
        type: "success",
        message: `${result.submitted} donacion${result.submitted !== 1 ? "es" : ""} enviada${result.submitted !== 1 ? "s" : ""} exitosamente`,
      });
    } else if (result.failed > 0) {
      setFeedback({
        type: "error",
        message: `${result.failed} donacion${result.failed !== 1 ? "es" : ""} no se pudo${result.failed !== 1 ? "ieron" : ""} enviar`,
      });
    }

    await refreshQueue();
    setIsProcessing(false);
  }, [isProcessing, refreshQueue]);

  const handleSubmit = useCallback(
    async (data: {
      amount: number;
      currency: string;
      name: string;
      email: string;
      message: string;
    }) => {
      if (isOnline) {
        try {
          const success = await onSubmitOnline(data);
          if (success) {
            setFeedback({
              type: "success",
              message: "Donacion enviada exitosamente",
            });
          } else {
            // Online but request failed — queue it
            const result = await addToQueue(data);
            setFeedback({
              type: result.success ? "offline" : "queue-full",
              message: result.message,
            });
            await refreshQueue();
          }
        } catch {
          // Network error during submit — queue it
          const result = await addToQueue(data);
          setFeedback({
            type: result.success ? "offline" : "queue-full",
            message: result.message,
          });
          await refreshQueue();
        }
      } else {
        // Offline — queue it
        const result = await addToQueue(data);
        setFeedback({
          type: result.success ? "offline" : "queue-full",
          message: result.message,
        });
        await refreshQueue();
      }
    },
    [isOnline, onSubmitOnline, refreshQueue]
  );

  const handleDeleteQueued = useCallback(
    async (id: number) => {
      await removeFromQueue(id);
      await refreshQueue();
    },
    [refreshQueue]
  );

  return (
    <div>
      <ConnectionToast isOnline={isOnline} wasOffline={wasOffline} />

      {feedback && (
        <div className="mb-4">
          <FeedbackBanner
            type={feedback.type}
            message={feedback.message}
            onDismiss={() => setFeedback(null)}
          />
        </div>
      )}

      {children({ handleSubmit, isProcessing, isOnline })}

      <QueuedDonationsList
        donations={queuedDonations}
        onDelete={handleDeleteQueued}
        isProcessing={isProcessing}
      />
    </div>
  );
}
