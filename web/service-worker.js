/**
 * SoftFactory Service Worker v1.0
 * Provides offline support, caching strategy, and background sync
 *
 * CACHE STRATEGY:
 * - Cache-First: Static assets (CSS, JS, fonts)
 * - Network-First: API calls (with fallback to cache)
 * - Stale-While-Revalidate: HTML pages
 *
 * @version 1.0
 * @since 2026-02-26
 */

const CACHE_VERSION = 'v1';
const CACHE_PREFIX = 'softfactory';
const CACHE_NAMES = {
  static: `${CACHE_PREFIX}-static-${CACHE_VERSION}`,
  dynamic: `${CACHE_PREFIX}-dynamic-${CACHE_VERSION}`,
  api: `${CACHE_PREFIX}-api-${CACHE_VERSION}`,
  images: `${CACHE_PREFIX}-images-${CACHE_VERSION}`
};

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/web/platform/index.html',
  '/web/platform/api.js',
  '/web/platform/login.html',
  '/web/platform/register.html',
  '/web/dashboard.html',
  '/web/analytics.html',
  '/web/operations.html',
  '/web/offline.html',
  '/web/manifest.json',
  'https://cdn.tailwindcss.com',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/apexcharts/3.45.0/apexcharts.min.js',
  'https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js'
];

// Routes that should use Cache-First strategy
const CACHE_FIRST_ROUTES = [
  /\.js$/,
  /\.css$/,
  /\.woff2?$/,
  /\.ttf$/,
  /\.eot$/,
  /\.svg$/,
  /icons\/.*\.png$/
];

// Routes that should use Network-First strategy (API calls)
const NETWORK_FIRST_ROUTES = [
  /\/api\//,
  /\/health/
];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', event => {
  console.log('[SW] Installing Service Worker...');

  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAMES.static);
        console.log('[SW] Caching static assets...');
        await cache.addAll(STATIC_ASSETS);
        console.log('[SW] Static assets cached');
        self.skipWaiting(); // Activate immediately
      } catch (error) {
        console.error('[SW] Install error:', error);
      }
    })()
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', event => {
  console.log('[SW] Activating Service Worker...');

  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      const validCaches = Object.values(CACHE_NAMES);

      await Promise.all(
        cacheNames
          .filter(name => name.startsWith(CACHE_PREFIX) && !validCaches.includes(name))
          .map(name => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );

      self.clients.claim(); // Take control immediately
      console.log('[SW] Service Worker activated');
    })()
  );
});

/**
 * Fetch event - implement caching strategies
 */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome extensions and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Determine caching strategy
  if (isNetworkFirstRoute(url.pathname)) {
    event.respondWith(networkFirstStrategy(request));
  } else if (isCacheFirstRoute(url.pathname)) {
    event.respondWith(cacheFirstStrategy(request));
  } else if (url.pathname.endsWith('.html')) {
    event.respondWith(staleWhileRevalidateStrategy(request));
  } else {
    event.respondWith(networkFirstStrategy(request));
  }
});

/**
 * Network-First Strategy: Try network, fallback to cache
 * Best for API calls that may change frequently
 */
async function networkFirstStrategy(request) {
  const cacheName = request.url.includes('/api/') ? CACHE_NAMES.api : CACHE_NAMES.dynamic;

  try {
    const networkResponse = await fetchWithTimeout(request, 5000);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network request failed, trying cache:', request.url);

    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page for HTML requests
    if (request.destination === 'document' || request.url.endsWith('.html')) {
      return caches.match('/web/offline.html');
    }

    // Return appropriate error responses
    return new Response('Offline - Resource not available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

/**
 * Cache-First Strategy: Try cache, fallback to network
 * Best for static assets that don't change often
 */
async function cacheFirstStrategy(request) {
  const cacheName = request.url.includes('/icons/') ? CACHE_NAMES.images : CACHE_NAMES.static;

  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetchWithTimeout(request, 5000);

    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Cache-First strategy failed:', request.url);

    // For images, return a placeholder
    if (request.destination === 'image') {
      return new Response(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="#e5e7eb" width="100" height="100"/></svg>',
        { headers: { 'Content-Type': 'image/svg+xml' } }
      );
    }

    return new Response('Resource not available', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

/**
 * Stale-While-Revalidate Strategy: Return cache immediately, update in background
 * Best for HTML pages and content that can be slightly stale
 */
async function staleWhileRevalidateStrategy(request) {
  const cacheName = CACHE_NAMES.dynamic;

  try {
    const cachedResponse = await caches.match(request);

    // Return cache immediately if available
    if (cachedResponse) {
      // Fetch fresh copy in background
      fetchWithTimeout(request, 5000)
        .then(networkResponse => {
          if (networkResponse.ok) {
            caches.open(cacheName).then(cache => {
              cache.put(request, networkResponse);
            });
          }
        })
        .catch(() => {
          // Silently fail background refresh
        });

      return cachedResponse;
    }

    // No cache, try network
    const networkResponse = await fetchWithTimeout(request, 5000);

    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Stale-While-Revalidate failed:', request.url);
    return caches.match(request) || caches.match('/web/offline.html');
  }
}

/**
 * Fetch with timeout
 */
function fetchWithTimeout(request, timeout = 5000) {
  return Promise.race([
    fetch(request),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Fetch timeout')), timeout)
    )
  ]);
}

/**
 * Check if route should use Network-First strategy
 */
function isNetworkFirstRoute(pathname) {
  return NETWORK_FIRST_ROUTES.some(pattern => pattern.test(pathname));
}

/**
 * Check if route should use Cache-First strategy
 */
function isCacheFirstRoute(pathname) {
  return CACHE_FIRST_ROUTES.some(pattern => pattern.test(pathname));
}

/**
 * Background Sync - Sync form submissions when back online
 */
self.addEventListener('sync', event => {
  console.log('[SW] Background sync event:', event.tag);

  if (event.tag === 'sync-form-submissions') {
    event.waitUntil(syncFormSubmissions());
  }
});

/**
 * Sync pending form submissions
 */
async function syncFormSubmissions() {
  try {
    const db = await openIndexedDB();
    const pendingForms = await getPendingForms(db);

    for (const form of pendingForms) {
      try {
        const response = await fetch(form.url, {
          method: form.method,
          headers: form.headers,
          body: form.body
        });

        if (response.ok) {
          await deletePendingForm(db, form.id);
          console.log('[SW] Form synced successfully:', form.id);
        }
      } catch (error) {
        console.error('[SW] Form sync failed:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync error:', error);
    throw error;
  }
}

/**
 * IndexedDB helpers for pending forms
 */
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('SoftFactoryDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-forms')) {
        db.createObjectStore('pending-forms', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

function getPendingForms(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pending-forms'], 'readonly');
    const store = transaction.objectStore('pending-forms');
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function deletePendingForm(db, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['pending-forms'], 'readwrite');
    const store = transaction.objectStore('pending-forms');
    const request = store.delete(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

/**
 * Push notification event
 */
self.addEventListener('push', event => {
  console.log('[SW] Push notification received');

  const options = {
    badge: '/web/icons/icon-192x192.png',
    icon: '/web/icons/icon-192x192.png',
    body: event.data ? event.data.text() : 'SoftFactory Notification',
    vibrate: [200, 100, 200],
    tag: 'softfactory-notification',
    requireInteraction: false
  };

  event.waitUntil(
    self.registration.showNotification('SoftFactory', options)
  );
});

/**
 * Notification click event
 */
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification clicked');
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(clientList => {
      // Focus existing window if available
      for (const client of clientList) {
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});

console.log('[SW] Service Worker script loaded');
