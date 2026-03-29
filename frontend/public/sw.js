// Service Worker for Refugio Animal Paraguay PWA
// Version: 2.0.0 — Added push notification support

const CACHE_NAME = "refugio-animal-v1";
const OFFLINE_URL = "/offline";

// Default notification icon (relative to SW scope)
const DEFAULT_ICON = "/images/icon-192.png";
const DEFAULT_BADGE = "/images/badge-72.png";

// Assets to precache on install
const PRECACHE_ASSETS = [
  "/",
  "/offline",
  "/manifest.json",
];

// Install: precache critical assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  // Activate immediately without waiting for old SW to finish
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  // Take control of all clients immediately
  self.clients.claim();
});

// Fetch: network-first strategy with cache fallback
self.addEventListener("fetch", (event) => {
  // Skip non-GET requests
  if (event.request.method !== "GET") return;

  // Skip API calls and external requests
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful responses
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Try cache, then offline page
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // For navigation requests, show offline page
          if (event.request.mode === "navigate") {
            return caches.match(OFFLINE_URL);
          }
          return new Response("Offline", { status: 503, statusText: "Offline" });
        });
      })
  );
});

// Push: receive push messages from the server and show browser notifications
self.addEventListener("push", (event) => {
  // Parse push payload — fall back to sensible defaults if missing/malformed
  let payload = {
    title: "Refugio Animal Paraguay",
    body: "Tienes una nueva notificacion.",
    url: "/",
    icon: DEFAULT_ICON,
    badge: DEFAULT_BADGE,
    tag: "refugio-notification",
    data: {},
  };

  if (event.data) {
    try {
      const parsed = event.data.json();
      payload = {
        title: parsed.title || payload.title,
        body: parsed.body || payload.body,
        url: parsed.url || payload.url,
        icon: parsed.icon || payload.icon,
        badge: parsed.badge || payload.badge,
        tag: parsed.tag || payload.tag,
        data: parsed.data || {},
      };
    } catch {
      // If JSON parse fails, try plain text as body
      const text = event.data.text();
      if (text) {
        payload.body = text;
      }
    }
  }

  const notificationOptions = {
    body: payload.body,
    icon: payload.icon,
    badge: payload.badge,
    tag: payload.tag,
    renotify: true,
    data: {
      url: payload.url,
      ...payload.data,
    },
    actions: [
      { action: "open", title: "Ver" },
      { action: "dismiss", title: "Cerrar" },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(payload.title, notificationOptions)
  );
});

// NotificationClick: handle user interaction with the shown notification
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "dismiss") {
    return;
  }

  // Determine target URL from notification data
  const targetUrl = (event.notification.data && event.notification.data.url)
    ? event.notification.data.url
    : "/";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      // Focus an existing window on the target URL if one exists
      for (const client of windowClients) {
        if (client.url === targetUrl && "focus" in client) {
          return client.focus();
        }
      }
      // Otherwise open a new window
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// NotificationClose: track dismissed notifications (optional analytics hook)
self.addEventListener("notificationclose", (event) => {
  // Payload data available for analytics if needed
  const _data = event.notification.data;
});
