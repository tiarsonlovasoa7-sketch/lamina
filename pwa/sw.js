/* Service worker minimal : met l'icone et le manifest en cache pour un affichage hors-ligne basique. */
const CACHE = "lamina-v1";
const ASSETS = [
  "/static/icone-192.png",
  "/static/icone-512.png",
  "/static/manifest.webmanifest"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((cles) => Promise.all(cles.filter((c) => c !== CACHE).map((c) => caches.delete(c))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const requete = event.request;
  if (requete.method !== "GET") return;
  event.respondWith(
    caches.match(requete).then((enCache) => {
      if (enCache) return enCache;
      const reponse = fetch(requete).then((rep) => {
        const copie = rep.clone();
        if (rep.ok && rep.headers.get("content-type") && rep.headers.get("content-type").includes("image")) {
          caches.open(CACHE).then((cache) => cache.put(requete, copie));
        }
        return rep;
      });
      return reponse;
    })
  );
});