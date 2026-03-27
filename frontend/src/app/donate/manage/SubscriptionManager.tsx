"use client";

/**
 * SubscriptionManager
 *
 * Allows a donor to look up their subscription by ID, view its status,
 * and perform management actions: pause, resume, cancel, or update amount.
 *
 * Flow:
 *   1. Enter subscription ID -> GET /subscriptions/{id}
 *   2. Display subscription details with action buttons
 *   3. Actions call respective API endpoints and refresh state
 */

import { useState, useCallback } from "react";
import {
  getSubscription,
  pauseSubscription,
  resumeSubscription,
  cancelSubscription,
  updateSubscription,
} from "@/lib/public-api";
import { SUBSCRIPTION_MANAGE } from "@/lib/strings";
import { formatDate } from "@/lib/strings";
import type { SubscriptionDetailResponse } from "@/types/api";
import {
  Search,
  Pause,
  Play,
  XCircle,
  Edit3,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    active: {
      label: SUBSCRIPTION_MANAGE.statusActive,
      className: "bg-green-100 text-green-700",
    },
    paused: {
      label: SUBSCRIPTION_MANAGE.statusPaused,
      className: "bg-yellow-100 text-yellow-700",
    },
    canceled: {
      label: SUBSCRIPTION_MANAGE.statusCanceled,
      className: "bg-red-100 text-red-700",
    },
    past_due: {
      label: SUBSCRIPTION_MANAGE.statusPastDue,
      className: "bg-orange-100 text-orange-700",
    },
    incomplete: {
      label: SUBSCRIPTION_MANAGE.statusIncomplete,
      className: "bg-gray-100 text-gray-700",
    },
  };

  const { label, className } = config[status] ?? {
    label: status,
    className: "bg-gray-100 text-gray-700",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}
    >
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Cancel confirmation dialog
// ---------------------------------------------------------------------------

interface CancelDialogProps {
  onConfirm: (reason: string) => void;
  onDismiss: () => void;
  isLoading: boolean;
}

function CancelDialog({ onConfirm, onDismiss, isLoading }: CancelDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
      <h4 className="text-sm font-semibold text-red-800 mb-2">
        {SUBSCRIPTION_MANAGE.cancelConfirmTitle}
      </h4>
      <p className="text-xs text-red-600 mb-3">
        {SUBSCRIPTION_MANAGE.cancelConfirmMessage}
      </p>
      <div className="mb-3">
        <label className="block text-xs text-red-700 mb-1">
          {SUBSCRIPTION_MANAGE.cancelReasonLabel}
        </label>
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          maxLength={500}
          className="w-full px-3 py-2 border border-red-200 rounded-lg text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onConfirm(reason)}
          disabled={isLoading}
          className="flex-1 py-2 px-3 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
        >
          {isLoading && <Loader2 className="h-3 w-3 animate-spin" />}
          {SUBSCRIPTION_MANAGE.cancelConfirmButton}
        </button>
        <button
          type="button"
          onClick={onDismiss}
          disabled={isLoading}
          className="flex-1 py-2 px-3 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {SUBSCRIPTION_MANAGE.cancelDismissButton}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Update amount dialog
// ---------------------------------------------------------------------------

interface UpdateAmountDialogProps {
  currentCents: number;
  currency: string;
  onSave: (newCents: number) => void;
  onDismiss: () => void;
  isLoading: boolean;
}

function UpdateAmountDialog({
  currentCents,
  currency,
  onSave,
  onDismiss,
  isLoading,
}: UpdateAmountDialogProps) {
  const isPYG = currency === "PYG";
  const divisor = isPYG ? 1 : 100;
  const symbol = isPYG ? "Gs." : "\u20AC";
  const [amount, setAmount] = useState(String(currentCents / divisor));

  function handleSave() {
    const parsed = parseFloat(amount);
    if (!isNaN(parsed) && parsed > 0) {
      onSave(Math.round(parsed * divisor));
    }
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
      <h4 className="text-sm font-semibold text-blue-800 mb-2">
        {SUBSCRIPTION_MANAGE.updateAmountLabel}
      </h4>
      <div className="relative mb-3">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
          {symbol}
        </span>
        <input
          type="number"
          min="1"
          step={isPYG ? "1000" : "0.01"}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-blue-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={isLoading}
          className="flex-1 py-2 px-3 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
        >
          {isLoading && <Loader2 className="h-3 w-3 animate-spin" />}
          {SUBSCRIPTION_MANAGE.saveButton}
        </button>
        <button
          type="button"
          onClick={onDismiss}
          disabled={isLoading}
          className="flex-1 py-2 px-3 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {SUBSCRIPTION_MANAGE.cancelDismissButton}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function SubscriptionManager() {
  const [subscriptionId, setSubscriptionId] = useState("");
  const [subscription, setSubscription] =
    useState<SubscriptionDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showAmountDialog, setShowAmountDialog] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const clearMessages = useCallback(() => {
    setError("");
    setSuccessMessage("");
  }, []);

  async function handleLookup() {
    if (!subscriptionId.trim()) return;
    setIsLoading(true);
    setNotFound(false);
    clearMessages();

    try {
      const sub = await getSubscription(subscriptionId.trim());
      setSubscription(sub);
    } catch {
      setSubscription(null);
      setNotFound(true);
    } finally {
      setIsLoading(false);
    }
  }

  async function handlePause() {
    if (!subscription) return;
    setActionLoading(true);
    clearMessages();
    try {
      const updated = await pauseSubscription(subscription.id);
      setSubscription(updated);
      setSuccessMessage(SUBSCRIPTION_MANAGE.actionSuccess);
    } catch {
      setError(SUBSCRIPTION_MANAGE.actionError);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleResume() {
    if (!subscription) return;
    setActionLoading(true);
    clearMessages();
    try {
      const updated = await resumeSubscription(subscription.id);
      setSubscription(updated);
      setSuccessMessage(SUBSCRIPTION_MANAGE.actionSuccess);
    } catch {
      setError(SUBSCRIPTION_MANAGE.actionError);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCancel(reason: string) {
    if (!subscription) return;
    setActionLoading(true);
    clearMessages();
    try {
      const updated = await cancelSubscription(subscription.id, false, reason);
      setSubscription(updated);
      setSuccessMessage(SUBSCRIPTION_MANAGE.actionSuccess);
      setShowCancelDialog(false);
    } catch {
      setError(SUBSCRIPTION_MANAGE.actionError);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleUpdateAmount(newCents: number) {
    if (!subscription) return;
    setActionLoading(true);
    clearMessages();
    try {
      const updated = await updateSubscription(subscription.id, {
        amount_cents: newCents,
      });
      setSubscription(updated);
      setSuccessMessage(SUBSCRIPTION_MANAGE.actionSuccess);
      setShowAmountDialog(false);
    } catch {
      setError(SUBSCRIPTION_MANAGE.actionError);
    } finally {
      setActionLoading(false);
    }
  }

  // --- Lookup form ---
  if (!subscription && !notFound) {
    return (
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {SUBSCRIPTION_MANAGE.lookupTitle}
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {SUBSCRIPTION_MANAGE.subscriptionIdLabel}
            </label>
            <input
              type="text"
              value={subscriptionId}
              onChange={(e) => setSubscriptionId(e.target.value)}
              placeholder="sub_..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              onKeyDown={(e) => e.key === "Enter" && handleLookup()}
            />
          </div>
          <button
            type="button"
            onClick={handleLookup}
            disabled={isLoading || !subscriptionId.trim()}
            className="w-full py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {SUBSCRIPTION_MANAGE.searchButton}
          </button>
        </div>
      </div>
    );
  }

  // --- Not found ---
  if (notFound) {
    return (
      <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 text-center">
        <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-3" />
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          {SUBSCRIPTION_MANAGE.notFoundTitle}
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          {SUBSCRIPTION_MANAGE.notFoundMessage}
        </p>
        <button
          type="button"
          onClick={() => {
            setNotFound(false);
            setSubscriptionId("");
          }}
          className="text-primary-600 hover:text-primary-700 font-medium text-sm"
        >
          {SUBSCRIPTION_MANAGE.searchButton}
        </button>
      </div>
    );
  }

  // --- Subscription detail ---
  const sub = subscription!;
  const isPYG = sub.currency === "PYG";
  const divisor = isPYG ? 1 : 100;
  const symbol = isPYG ? "Gs." : "\u20AC";
  const displayAmount = (sub.amount_cents / divisor).toLocaleString("es-PY");
  const intervalLabel =
    sub.interval === "month"
      ? SUBSCRIPTION_MANAGE.monthly
      : SUBSCRIPTION_MANAGE.yearly;

  const canPause = sub.status === "active";
  const canResume = sub.status === "paused";
  const canCancel = sub.status === "active" || sub.status === "paused";
  const canUpdate = sub.status === "active";

  return (
    <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {SUBSCRIPTION_MANAGE.title}
        </h2>
        <StatusBadge status={sub.status} />
      </div>

      {/* Details */}
      <dl className="space-y-3 mb-6">
        <div className="flex justify-between text-sm">
          <dt className="text-gray-500">{SUBSCRIPTION_MANAGE.amountLabel}</dt>
          <dd className="font-medium text-gray-900">
            {symbol} {displayAmount}
          </dd>
        </div>
        <div className="flex justify-between text-sm">
          <dt className="text-gray-500">{SUBSCRIPTION_MANAGE.intervalLabel}</dt>
          <dd className="font-medium text-gray-900">{intervalLabel}</dd>
        </div>
        {sub.current_period_end && (
          <div className="flex justify-between text-sm">
            <dt className="text-gray-500">
              {SUBSCRIPTION_MANAGE.nextPaymentLabel}
            </dt>
            <dd className="font-medium text-gray-900">
              {formatDate(sub.current_period_end)}
            </dd>
          </div>
        )}
        <div className="flex justify-between text-sm">
          <dt className="text-gray-500">{SUBSCRIPTION_MANAGE.createdLabel}</dt>
          <dd className="font-medium text-gray-900">
            {formatDate(sub.created_at)}
          </dd>
        </div>
        {sub.cancel_at_period_end && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-700">
            Se cancelara al final del periodo actual.
          </div>
        )}
        {sub.last_payment_error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">
            Ultimo error: {sub.last_payment_error}
          </div>
        )}
      </dl>

      {/* Feedback messages */}
      {successMessage && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
          <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
          <span className="text-sm text-green-700">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Action buttons */}
      <div className="space-y-2">
        {canPause && (
          <button
            type="button"
            onClick={handlePause}
            disabled={actionLoading}
            className="w-full py-2.5 px-4 border border-yellow-300 text-yellow-700 rounded-lg text-sm font-medium hover:bg-yellow-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Pause className="h-4 w-4" />
            {SUBSCRIPTION_MANAGE.pauseButton}
          </button>
        )}
        {canResume && (
          <button
            type="button"
            onClick={handleResume}
            disabled={actionLoading}
            className="w-full py-2.5 px-4 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Play className="h-4 w-4" />
            {SUBSCRIPTION_MANAGE.resumeButton}
          </button>
        )}
        {canUpdate && !showAmountDialog && (
          <button
            type="button"
            onClick={() => {
              setShowAmountDialog(true);
              setShowCancelDialog(false);
              clearMessages();
            }}
            disabled={actionLoading}
            className="w-full py-2.5 px-4 border border-blue-300 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Edit3 className="h-4 w-4" />
            {SUBSCRIPTION_MANAGE.updateAmountButton}
          </button>
        )}
        {canCancel && !showCancelDialog && (
          <button
            type="button"
            onClick={() => {
              setShowCancelDialog(true);
              setShowAmountDialog(false);
              clearMessages();
            }}
            disabled={actionLoading}
            className="w-full py-2.5 px-4 border border-red-300 text-red-700 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <XCircle className="h-4 w-4" />
            {SUBSCRIPTION_MANAGE.cancelButton}
          </button>
        )}
      </div>

      {/* Dialogs */}
      {showCancelDialog && (
        <CancelDialog
          onConfirm={handleCancel}
          onDismiss={() => setShowCancelDialog(false)}
          isLoading={actionLoading}
        />
      )}
      {showAmountDialog && (
        <UpdateAmountDialog
          currentCents={sub.amount_cents}
          currency={sub.currency}
          onSave={handleUpdateAmount}
          onDismiss={() => setShowAmountDialog(false)}
          isLoading={actionLoading}
        />
      )}

      {/* Search again */}
      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={() => {
            setSubscription(null);
            setSubscriptionId("");
            clearMessages();
            setShowCancelDialog(false);
            setShowAmountDialog(false);
          }}
          className="text-primary-600 hover:text-primary-700 font-medium text-sm"
        >
          Buscar otra suscripcion
        </button>
      </div>
    </div>
  );
}
