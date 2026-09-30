// Trailpost HK service worker: keeps the app working with no signal on the hills.
// build.py fills in the version numbers and the file list, and writes the result to dist/sw.js.
// - The page: fresh copy if the network answers within 3 s, otherwise the saved copy.
// - conditions.json (live weather, when it exists): network first, saved copy when offline.
// - Everything else on this site (libraries, font, icons, 3D files): saved copy first; saved the first time it is loaded.
const CORE = 'tp-core-__CORE__';   // changes whenever the app itself changes
const DATA = 'tp-data-__DATA__';   // changes only when the 3D files change, so they are not downloaded again for app updates
const PRECACHE = __PRECACHE__;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CORE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('tp-') && k !== CORE && k !== DATA).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== location.origin) return; // Observatory photos and links: straight to the network
  if (r.mode === 'navigate' || u.pathname.endsWith('/index.html')) return e.respondWith(page(r));
  if (u.pathname.endsWith('/conditions.json')) return e.respondWith(networkFirst(r));
  e.respondWith(savedFirst(r, u));
});

async function page(r) {
  const c = await caches.open(CORE);
  const net = fetch(r).then(res => { if (res.ok) c.put('./', res.clone()); return res; });
  net.catch(() => {});
  const saved = new Promise(ok => setTimeout(ok, 3000)).then(() => c.match('./'));
  try {
    const first = await Promise.race([net, saved]);
    return first || await net;
  } catch (err) {
    return (await c.match('./')) || Response.error();
  }
}

async function networkFirst(r) {
  const c = await caches.open(CORE);
  try {
    const res = await fetch(r);
    if (res.ok) c.put(r, res.clone());
    return res;
  } catch (err) {
    return (await c.match(r)) || Response.error();
  }
}

async function savedFirst(r, u) {
  const hit = await caches.match(r);
  if (hit) return hit;
  const res = await fetch(r);
  if (res.status === 200) (await caches.open(u.pathname.includes('/l3/') ? DATA : CORE)).put(r, res.clone());
  return res;
}
