"use client";

import { useEffect, useState, useCallback } from "react";
import { Bell, BellOff, BellRing } from "lucide-react";
import { subscribeToPush, unsubscribeFromPush } from "@/components/ServiceWorkerRegistration";

/**
 * Push notification subscription manager.
 *
 * Handles browser push notification permission requests,
 * subscription management, and server registration.
 * Falls back gracefully when Push API is not supported.
 *
 * Delegates SW interaction to ServiceWorkerRegistration helpers
 * to avoid duplicating the urlBase64ToUint8Array conversion.
 */

type PermissionState = "default" | "granted" | "denied" | "unsupported";

const LABEL_ENABLE = "Activar notificaciones";
const LABEL_DISABLE = "Desactivar notificaciones";
const LABEL_DENIED = "Notificaciones bloqueadas";
const LABEL_UNSUPPORTED = "Notificaciones no soportadas";
const LABEL_SUBSCRIBING = "Activando...";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || "";

export default function PushNotificationSubscription() {
  const [permission, setPermission] = useState<PermissionState>("default");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setPermission("unsupported");
      return;
    }

    setPermission(Notification.permission as PermissionState);

    navigator.serviceWorker.ready.then((registration) => {
      registration.pushManager.getSubscription().then((subscription) => {
        setIsSubscribed(subscription !== null);
      });
    });
  }, []);

  const subscribe = useCallback(async () => {
    if (!VAPID_PUBLIC_KEY) {
      if (process.env.NODE_ENV === "development") {
        console.warn("[Push] NEXT_PUBLIC_VAPID_PUBLIC_KEY not configured");
      }
      return;
    }

    setIsLoading(true);
    try {
      const permResult = await Notification.requestPermission();
      setPermission(permResult as PermissionState);

      if (permResult !== "granted") return;

      const subscription = await subscribeToPush(VAPID_PUBLIC_KEY);
      if (!subscription) return;

      // Register subscription with backend
      await fetch(`${API_BASE}/api/push-subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(subscription.toJSON()),
      });

      setIsSubscribed(true);
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Push] Subscription failed:", error);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const unsubscribe = useCallback(async () => {
    setIsLoading(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Deregister from backend before unsubscribing locally
        await fetch(`${API_BASE}/api/push-subscriptions`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
      }

      await unsubscribeFromPush();
      setIsSubscribed(false);
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Push] Unsubscribe failed:", error);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  if (permission === "unsupported") return null;

  const Icon = permission === "denied" ? BellOff : isSubscribed ? BellRing : Bell;
  const label =
    permission === "denied"
      ? LABEL_DENIED
      : isLoading
        ? LABEL_SUBSCRIBING
        : isSubscribed
          ? LABEL_DISABLE
          : LABEL_ENABLE;

  const isDisabled = permission === "denied" || isLoading;

  return (
    <button
      onClick={isSubscribed ? unsubscribe : subscribe}
      disabled={isDisabled}
      className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
        isSubscribed
          ? "bg-primary-50 text-primary-700 hover:bg-primary-100"
          : isDisabled
            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
            : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50"
      }`}
      aria-label={label}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );
}
