const CACHE = 'ledger-v3';
const FILES = ['./', 'index.html', 'manifest.json', 'icon.svg'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// 網路優先，離線時退回快取，這樣更新程式後不會卡在舊版
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // 只快取自己的檔案與 Firebase 程式庫，Firestore／登入的連線不經過這裡
  if (e.request.method !== 'GET' ||
      !(url.origin === location.origin || url.href.startsWith('https://www.gstatic.com/firebasejs/'))) return;
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request))
  );
});
