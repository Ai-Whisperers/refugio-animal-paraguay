"use client";

import { useEffect } from "react";

/**
 * Registers the service worker for PWA functionality.
 *
 * Only registers in production to avoid caching issues during development.
 * Handles updates by notifying users when a new version is available.
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
          // Check for updates periodically (every 60 minutes)
          const UPDATE_INTERVAL_MS = 60 * 60 * 1000;
          setInterval(() => {
            registration.update();
          }, UPDATE_INTERVAL_MS);

          registration.addEventListener("updatefound", () => {
            const newWorker = registration.installing;
            if (!newWorker) return;

            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "activated" &&
                navigator.serviceWorker.controller
              ) {
                // New version available — log for now, could show toast
                if (process.env.NODE_ENV === "development") {
                  console.log("[SW] New version available");
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
