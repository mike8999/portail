// Portail hors ligne : pages et données toujours redemandées au réseau d'abord,
// images et bibliothèques servies depuis le cache puis rafraîchies en arrière-plan.
const CACHE = "portail-v1";
const BASE = ["./", "index.html", "apps.json", "reglages.json", "donnees/auto.json", "manifest.webmanifest", "icones/icone-192.png"];

self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE)).catch(() => {})); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== "GET" || u.hostname === "api.github.com" || u.pathname.includes("/.netlify/functions/")) return;
  const page = u.origin === location.origin && (r.mode === "navigate" || /\.(html|json|js|webmanifest)$/.test(u.pathname) || u.pathname.endsWith("/"));
  if (page){
    e.respondWith(fetch(r).then(rep => { const c = rep.clone(); caches.open(CACHE).then(k => k.put(r, c)); return rep; })
      .catch(() => caches.match(r, {ignoreSearch: true}).then(m => m || caches.match("index.html"))));
  } else {
    e.respondWith(caches.match(r).then(m => {
      const net = fetch(r).then(rep => { if (rep.ok || rep.type === "opaque") { const c = rep.clone(); caches.open(CACHE).then(k => k.put(r, c)); } return rep; }).catch(() => m);
      return m || net;
    }));
  }
});
