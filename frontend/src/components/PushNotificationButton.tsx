"use client";

import { useEffect, useState, useCallback } from "react";
import { Bell, BellOff, BellRing, Loader2 } from "lucide-react";
import dynamic from "next/dynamic";
import { subscribeToPush, unsubscribeFromPush } from "@/components/ServiceWorkerRegistration";

/**
 * PushNotificationButton — full opt-in flow with value-proposition modal.
 *
 * Renders a button that:
 *   - Shows a value-prop modal BEFORE requesting browser permission
 *   - Subscribes/unsubscribes with full server synchronization
 *   - Handles all permission states gracefully
 *
 * Use this instead of PushNotificationSubscription wherever a richer
 * opt-in experience is needed (settings pages, onboarding).
 */

// Lazy-load the modal to keep the initial bundle small
const PushOptInModal = dynamic(() => import("@/components/PushOptInModal"), {
  ssr: false,
});

type BrowserPermission = "default" | "granted" | "denied" | "unsupported";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || "";

const LABELS: Record<string, string> = {
  loading: "Comprobando...",
  subscribing: "Activando...",
  unsubscribing: "Desactivando...",
  subscribed: "Notificaciones activas",
  unsubscribed: "Activar notificaciones",
  denied: "Notificaciones bloqueadas",
  unsupported: "No disponible en este navegador",
};

export default function PushNotificationButton() {
  const [permission, setPermission] = useState<BrowserPermission>("default");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [action, setAction] = useState<"idle" | "subscribing" | "unsubscribing">("idle");
  const [showModal, setShowModal] = useState(false);

  // Detect support and current subscription state
  useEffect(() => {
    if (typeof window === "undefined") {
      setPermission("unsupported");
      setIsLoading(false);
      return;
    }
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setPermission("unsupported");
      setIsLoading(false);
      return;
    }

    setPermission(Notification.permission as BrowserPermission);

    navigator.serviceWorker.ready
      .then((reg) => reg.pushManager.getSubscription())
      .then((sub) => setIsSubscribed(sub !== null))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handleConfirmOptIn = useCallback(async () => {
    setShowModal(false);

    if (!VAPID_PUBLIC_KEY) {
      if (process.env.NODE_ENV === "development") {
        console.warn("[Push] NEXT_PUBLIC_VAPID_PUBLIC_KEY not configured");
      }
      return;
    }

    setAction("subscribing");
    try {
      const permResult = await Notification.requestPermission();
      setPermission(permResult as BrowserPermission);
      if (permResult !== "granted") return;

      const subscription = await subscribeToPush(VAPID_PUBLIC_KEY);
      if (!subscription) return;

      await fetch(`${API_BASE}/api/push-subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(subscription.toJSON()),
      });

      setIsSubscribed(true);
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Push] Subscribe failed:", error);
      }
    } finally {
      setAction("idle");
    }
  }, []);

  const handleUnsubscribe = useCallback(async () => {
    setAction("unsubscribing");
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await fetch(`${API_BASE}/api/push-subscriptions`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: sub.endpoint }),
        });
      }
      await unsubscribeFromPush();
      setIsSubscribed(false);
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Push] Unsubscribe failed:", error);
      }
    } finally {
      setAction("idle");
    }
  }, []);

  const handleClick = useCallback(() => {
    if (isSubscribed) {
      handleUnsubscribe();
    } else {
      // Show the value-prop modal before requesting permission
      setShowModal(true);
    }
  }, [isSubscribed, handleUnsubscribe]);

  if (permission === "unsupported") return null;

  const isBusy = isLoading || action !== "idle";

  const label = isLoading
    ? LABELS.loading
    : action === "subscribing"
      ? LABELS.subscribing
      : action === "unsubscribing"
        ? LABELS.unsubscribing
        : permission === "denied"
          ? LABELS.denied
          : isSubscribed
            ? LABELS.subscribed
            : LABELS.unsubscribed;

  const Icon = isBusy
    ? Loader2
    : permission === "denied"
      ? BellOff
      : isSubscribed
        ? BellRing
        : Bell;

  const isDisabled = isBusy || permission === "denied";

  return (
    <>
      {showModal && (
        <PushOptInModal
          onConfirm={handleConfirmOptIn}
          onDismiss={() => setShowModal(false)}
        />
      )}

      <button
        type="button"
        onClick={handleClick}
        disabled={isDisabled}
        aria-label={label}
        className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
          isSubscribed && !isBusy
            ? "bg-primary-50 text-primary-700 hover:bg-primary-100"
            : isDisabled
              ? "cursor-not-allowed bg-gray-100 text-gray-400"
              : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
        }`}
      >
        <Icon className={`h-4 w-4 ${isBusy ? "animate-spin" : ""}`} aria-hidden="true" />
        <span>{label}</span>
      </button>
    </>
  );
}
