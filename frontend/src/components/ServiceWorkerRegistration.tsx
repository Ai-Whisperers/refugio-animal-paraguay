"use client";

import { useEffect } from "react";

const SW_UPDATE_INTERVAL_MS = 60 * 60 * 1000; // 60 minutes

/**
 * Convert a Base64URL-encoded VAPID public key to a Uint8Array.
 * Required by PushManager.subscribe() applicationServerKey.
 */
export function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i++) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Subscribe the current browser to push notifications via the registered SW.
 * Returns the PushSubscription object or null if push is unsupported/denied.
 */
export async function subscribeToPush(vapidPublicKey: string): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const existing = await registration.pushManager.getSubscription();
    if (existing) return existing;

    return await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });
  } catch {
    return null;
  }
}

/**
 * Unsubscribe the current browser from push notifications.
 */
export async function unsubscribeFromPush(): Promise<void> {
  if (!("serviceWorker" in navigator)) return;

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  if (subscription) {
    await subscription.unsubscribe();
  }
}

/**
 * Registers the service worker for PWA functionality and push notifications.
 *
 * Handles SW updates by logging when a new version is activated.
 * Push subscription is managed separately via the PushNotificationSubscription component.
 */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;

    // Register SW after page load to avoid competing with critical resources
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          // Periodically check for SW updates
          setInterval(() => {
            registration.update();
          }, SW_UPDATE_INTERVAL_MS);

          registration.addEventListener("updatefound", () => {
            const newWorker = registration.installing;
            if (!newWorker) return;

            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "activated" &&
                navigator.serviceWorker.controller
              ) {
                if (process.env.NODE_ENV === "development") {
                  console.log("[SW] New version available — reload to update");
                }
              }
            });
          });
        })
        .catch((error) => {
          if (process.env.NODE_ENV === "development") {
            console.error("[SW] Registration failed:", error);
          }
        });
    });
  }, []);

  return null;
}
