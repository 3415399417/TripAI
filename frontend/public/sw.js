/* TripAI service worker: cache app shell for offline / fast reloads. */
const CACHE_NAME = "tripai-shell-v4";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    (async () => {
      // Navigations: network-first so users always get the newest page.
      if (request.mode === "navigate") {
        try {
          const response = await fetch(request);
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return response;
        } catch {
          const cached = await caches.match(request);
          return cached || caches.match("/");
        }
      }

      // Static assets: cache-first.
      const cached = await caches.match(request);
      if (cached) return cached;

      const response = await fetch(request);
      const copy = response.clone();
      if (
        response.ok &&
        (request.destination === "script" ||
          request.destination === "style" ||
          request.destination === "image" ||
          request.destination === "font")
      ) {
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
      return response;
    })()
  );
});
