/**
 * SoftFactory PWA Installer Module v1.0
 * Handles Service Worker registration, install prompts, and PWA features
 *
 * FEATURES:
 * - Service Worker registration & lifecycle management
 * - Install prompt handling (deferred prompt)
 * - Offline detection & status
 * - Cache management (clear old caches)
 * - Update notification system
 * - Install button management
 *
 * @module pwa-installer
 * @version 1.0
 * @since 2026-02-26
 */

class PWAInstaller {
  constructor() {
    this.deferredPrompt = null;
    this.installBtn = null;
    this.swRegistration = null;
    this.isOnline = navigator.onLine;
    this.cacheSize = 0;

    this.init();
  }

  /**
   * Initialize PWA installer
   */
  async init() {
    console.log('[PWA] Initializing PWA Installer...');

    // Register Service Worker
    if ('serviceWorker' in navigator) {
      this.registerServiceWorker();
    }

    // Setup install prompt handlers
    this.setupInstallPrompt();

    // Listen for online/offline events
    this.setupConnectivityListeners();

    // Setup visibility change listener
    document.addEventListener('visibilitychange', () => this.onVisibilityChange());

    // Load cache size
    await this.calculateCacheSize();

    console.log('[PWA] PWA Installer initialized');
  }

  /**
   * Register Service Worker
   */
  async registerServiceWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/web/service-worker.js', {
        scope: '/',
        updateViaCache: 'none'
      });

      this.swRegistration = registration;
      console.log('[PWA] Service Worker registered:', registration);

      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        console.log('[PWA] Service Worker update found');

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New Service Worker is ready
            this.promptForUpdate();
          }
        });
      });

      // Check for updates periodically
      setInterval(() => {
        registration.update().catch(err => {
          console.log('[PWA] Update check failed:', err);
        });
      }, 60000); // Check every 60 seconds

      return registration;
    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
      return null;
    }
  }

  /**
   * Setup install prompt handler
   */
  setupInstallPrompt() {
    // Capture beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', event => {
      console.log('[PWA] beforeinstallprompt event captured');
      event.preventDefault();
      this.deferredPrompt = event;

      // Show install button
      this.showInstallButton();
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] PWA installed');
      this.deferredPrompt = null;
      this.hideInstallButton();

      // Send event to analytics
      if (window.gtag) {
        gtag('event', 'pwa_installed');
      }

      // Show success message
      this.showNotification('SoftFactory가 설치되었습니다!', 'success');
    });
  }

  /**
   * Show install button
   */
  showInstallButton() {
    if (this.installBtn) {
      this.installBtn.style.display = 'flex';
      this.installBtn.classList.add('animate-pulse');
    }
  }

  /**
   * Hide install button
   */
  hideInstallButton() {
    if (this.installBtn) {
      this.installBtn.style.display = 'none';
      this.installBtn.classList.remove('animate-pulse');
    }
  }

  /**
   * Trigger install prompt
   */
  async triggerInstallPrompt() {
    if (!this.deferredPrompt) {
      console.log('[PWA] No deferred prompt available');
      return false;
    }

    try {
      this.deferredPrompt.prompt();
      const { outcome } = await this.deferredPrompt.userChoice;

      console.log(`[PWA] User ${outcome} the install prompt`);

      this.deferredPrompt = null;
      return outcome === 'accepted';
    } catch (error) {
      console.error('[PWA] Install prompt error:', error);
      return false;
    }
  }

  /**
   * Prompt user for Service Worker update
   */
  promptForUpdate() {
    const message = document.createElement('div');
    message.className = 'fixed bottom-6 right-6 max-w-sm bg-blue-600 text-white rounded-lg shadow-lg p-4 flex gap-4 items-center z-50 animate-slide-up';
    message.innerHTML = `
      <div class="flex-1">
        <p class="font-semibold text-sm">업데이트 이용 가능</p>
        <p class="text-xs text-blue-100">새로운 버전이 준비되었습니다.</p>
      </div>
      <button id="updateBtn" class="px-4 py-2 bg-white text-blue-600 font-medium rounded text-sm hover:bg-blue-50 transition-colors">
        지금 업데이트
      </button>
    `;

    document.body.appendChild(message);

    document.getElementById('updateBtn').addEventListener('click', () => {
      if (this.swRegistration?.waiting) {
        this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      }
      message.remove();
    });

    // Auto remove after 10 seconds
    setTimeout(() => {
      message.remove();
    }, 10000);
  }

  /**
   * Setup connectivity listeners
   */
  setupConnectivityListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      console.log('[PWA] Online');
      this.onConnectivityChange();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      console.log('[PWA] Offline');
      this.onConnectivityChange();
    });
  }

  /**
   * Handle connectivity change
   */
  onConnectivityChange() {
    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('softfactory-connectivity-change', {
      detail: { isOnline: this.isOnline }
    }));

    // Update UI
    this.updateConnectivityIndicator();

    // Log to console
    console.log('[PWA] Connectivity changed:', this.isOnline ? 'online' : 'offline');
  }

  /**
   * Update connectivity indicator in UI
   */
  updateConnectivityIndicator() {
    const indicator = document.getElementById('connectivity-indicator');
    if (!indicator) return;

    if (this.isOnline) {
      indicator.classList.remove('offline');
      indicator.classList.add('online');
      indicator.textContent = '🟢 オンライン';
    } else {
      indicator.classList.remove('online');
      indicator.classList.add('offline');
      indicator.textContent = '🔴 オフライン';
    }
  }

  /**
   * Handle visibility change
   */
  onVisibilityChange() {
    if (document.hidden) {
      console.log('[PWA] App hidden');
    } else {
      console.log('[PWA] App visible');
      // Check for SW updates when app becomes visible
      if (this.swRegistration) {
        this.swRegistration.update().catch(() => {});
      }
    }
  }

  /**
   * Calculate total cache size
   */
  async calculateCacheSize() {
    try {
      const cacheNames = await caches.keys();
      let total = 0;

      for (const name of cacheNames) {
        if (name.startsWith('softfactory')) {
          const cache = await caches.open(name);
          const keys = await cache.keys();

          for (const request of keys) {
            const response = await cache.match(request);
            if (response) {
              total += parseInt(response.headers.get('content-length') || 0);
            }
          }
        }
      }

      this.cacheSize = total;
      console.log('[PWA] Cache size:', this.formatBytes(total));
    } catch (error) {
      console.error('[PWA] Cache size calculation failed:', error);
    }
  }

  /**
   * Clear old caches (except current version)
   */
  async clearOldCaches() {
    try {
      const cacheNames = await caches.keys();
      const validNames = [
        'softfactory-static-v1',
        'softfactory-dynamic-v1',
        'softfactory-api-v1',
        'softfactory-images-v1'
      ];

      const toDelete = cacheNames.filter(
        name => name.startsWith('softfactory') && !validNames.includes(name)
      );

      await Promise.all(toDelete.map(name => caches.delete(name)));

      console.log(`[PWA] Cleared ${toDelete.length} old cache(s)`);
      return toDelete.length;
    } catch (error) {
      console.error('[PWA] Cache clearing failed:', error);
      return 0;
    }
  }

  /**
   * Preload additional pages for offline use
   */
  async preloadPages(urls = []) {
    try {
      const cache = await caches.open('softfactory-dynamic-v1');
      await cache.addAll(urls);
      console.log('[PWA] Preloaded pages:', urls);
    } catch (error) {
      console.error('[PWA] Preload failed:', error);
    }
  }

  /**
   * Get cache size in human-readable format
   */
  getCacheSizeFormatted() {
    return this.formatBytes(this.cacheSize);
  }

  /**
   * Get online status
   */
  isConnected() {
    return this.isOnline;
  }

  /**
   * Check if PWA is installed
   */
  async isInstalled() {
    if (!('getInstalledRelatedApps' in navigator)) {
      return false;
    }

    const apps = await navigator.getInstalledRelatedApps();
    return apps.length > 0;
  }

  /**
   * Show notification
   */
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const colors = {
      success: 'bg-green-600',
      error: 'bg-red-600',
      warning: 'bg-yellow-600',
      info: 'bg-blue-600'
    };

    notification.className = `fixed bottom-6 right-6 ${colors[type] || colors.info} text-white rounded-lg shadow-lg px-6 py-3 z-50 animate-slide-up`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  /**
   * Format bytes to human-readable format
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Log PWA diagnostics
   */
  async logDiagnostics() {
    const diagnostics = {
      serviceWorkerRegistered: !!this.swRegistration,
      serviceWorkerActive: this.swRegistration?.active ? true : false,
      isOnline: this.isOnline,
      installed: await this.isInstalled(),
      cacheSize: this.getCacheSizeFormatted(),
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };

    console.log('[PWA] Diagnostics:', diagnostics);
    return diagnostics;
  }
}

// Initialize PWA Installer on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.PWA = new PWAInstaller();
  });
} else {
  window.PWA = new PWAInstaller();
}

console.log('[PWA] pwa-installer.js loaded');
