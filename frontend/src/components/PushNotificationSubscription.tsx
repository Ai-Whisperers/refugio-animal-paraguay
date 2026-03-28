"use client";

import { useEffect, useState, useCallback } from "react";
import { Bell, BellOff, BellRing } from "lucide-react";

/**
 * Push notification subscription manager.
 *
 * Handles browser push notification permission requests,
 * subscription management, and server registration.
 * Falls back gracefully when Push API is not supported.
 */

type PermissionState = "default" | "granted" | "denied" | "unsupported";

const LABEL_ENABLE = "Activar notificaciones";
const LABEL_DISABLE = "Desactivar notificaciones";
const LABEL_DENIED = "Notificaciones bloqueadas";
const LABEL_UNSUPPORTED = "Notificaciones no soportadas";
const LABEL_SUBSCRIBING = "Activando...";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || "";

/**
 * Convert a base64 URL-encoded string to a Uint8Array.
 * Required for applicationServerKey in PushManager.subscribe().
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default function PushNotificationSubscription() {
  const [permission, setPermission] = useState<PermissionState>("default");
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check Push API support
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setPermission("unsupported");
      return;
    }

    // Check current permission and subscription state
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
        console.warn("[Push] VAPID_PUBLIC_KEY not configured");
      }
      return;
    }

    setIsLoading(true);
    try {
      const result = await Notification.requestPermission();
      setPermission(result as PermissionState);

      if (result !== "granted") {
        setIsLoading(false);
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      });

      // Send subscription to server
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
        // Notify server before unsubscribing
        await fetch(`${API_BASE}/api/push-subscriptions`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });

        await subscription.unsubscribe();
      }

      setIsSubscribed(false);
    } catch (error) {
      if (process.env.NODE_ENV === "development") {
        console.error("[Push] Unsubscribe failed:", error);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Don't render anything if push is not supported
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
