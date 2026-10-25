// オフラインでも起動できるように、アプリ一式をキャッシュする Service Worker。
// ファイルを更新したら CACHE の番号を上げると、古いキャッシュが入れ替わる。
const CACHE = 'docchi-boy-v1';
const APP_FILES = [
  './',
  './index.html',
  './docchi-boy.html',
  './manifest.webmanifest',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(APP_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // ページ本体：ネットに繋がっていれば最新版、繋がっていなければキャッシュ
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(cache => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match('./docchi-boy.html')))
    );
    return;
  }

  // それ以外（アイコン・Google Fonts など）：キャッシュを先に使い、裏で更新する
  if (url.origin === location.origin || url.hostname.endsWith('fonts.googleapis.com') || url.hostname.endsWith('fonts.gstatic.com')) {
    event.respondWith(
      caches.open(CACHE).then(cache => cache.match(req).then(hit => {
        const update = fetch(req)
          .then(res => { if (res.ok || res.type === 'opaque') cache.put(req, res.clone()); return res; })
          .catch(() => hit);
        return hit || update;
      }))
    );
  }
});
