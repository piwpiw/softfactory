(function () {
  const DEFAULT_TIMEOUT_MS = 8000;
  const RETRY_COUNT = 2;
  const RETRY_BASE_DELAY_MS = 500;
  const GET_CACHE_TTL_MS = 30 * 1000;
  const GET_CACHE_PREFIX = "sf_runtime_cache:";

  const FALLBACK_CHAR = "\"";
  const inflightRequests = new Map();
  const prefetchedPages = new Set();
  const pendingButtons = new Set();
  let activeRequests = 0;

  const canUseStorage = () => typeof window !== "undefined" && !!window.localStorage;
  const canPrefetch = () => {
    const connection = typeof navigator !== "undefined" ? navigator.connection || navigator.mozConnection || navigator.webkitConnection : null;
    if (!connection) return !document.hidden;
    if (connection.saveData) return false;
    if (typeof connection.effectiveType === "string" && /(^slow-2g$|^2g$)/i.test(connection.effectiveType)) return false;
    return !document.hidden;
  };

  const makeCacheKey = (url) => `${GET_CACHE_PREFIX}${url}`;

  const getProgressBar = () => {
    if (!document || !document.body) return null;
    let bar = document.getElementById("sf-global-progress");
    if (bar) return bar;
    bar = document.createElement("div");
    bar.id = "sf-global-progress";
    bar.setAttribute("aria-hidden", "true");
    bar.style.cssText = [
      "position:fixed",
      "top:0",
      "left:0",
      "height:3px",
      "width:0%",
      "z-index:10001",
      "pointer-events:none",
      "background:linear-gradient(90deg,#38bdf8,#60a5fa,#f59e0b)",
      "box-shadow:0 0 18px rgba(96,165,250,0.45)",
      "opacity:0",
      "transition:width 0.22s ease, opacity 0.18s ease"
    ].join(";");
    document.body.appendChild(bar);
    return bar;
  };

  const beginProgress = () => {
    activeRequests += 1;
    const bar = getProgressBar();
    if (!bar) return;
    bar.style.opacity = "1";
    bar.style.width = activeRequests > 1 ? "72%" : "38%";
  };

  const endProgress = () => {
    activeRequests = Math.max(0, activeRequests - 1);
    const bar = getProgressBar();
    if (!bar) return;
    if (activeRequests > 0) {
      bar.style.width = "82%";
      return;
    }
    bar.style.width = "100%";
    setTimeout(() => {
      bar.style.opacity = "0";
      bar.style.width = "0%";
    }, 160);
    if (activeRequests === 0) {
      pendingButtons.forEach((button) => {
        if (!button || !button.isConnected) return;
        button.disabled = false;
        button.style.opacity = "";
        button.style.cursor = "";
        if (button.dataset.sfOriginalLabel) {
          button.innerHTML = button.dataset.sfOriginalLabel;
        }
        delete button.dataset.sfOriginalLabel;
        delete button.dataset.sfPending;
      });
      pendingButtons.clear();
    }
  };

  const readCache = (url) => {
    if (!canUseStorage()) return null;
    try {
      const raw = window.localStorage.getItem(makeCacheKey(url));
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.body || (Date.now() - parsed.savedAt) > GET_CACHE_TTL_MS) return null;
      return new Response(parsed.body, {
        status: parsed.status || 200,
        headers: parsed.headers || { "Content-Type": "application/json" }
      });
    } catch (_) {
      return null;
    }
  };

  const writeCache = async (url, response) => {
    if (!canUseStorage() || !(response instanceof Response) || !response.ok) return response;
    const contentType = response.headers.get("content-type") || "";
    if (!/application\/json|text\//i.test(contentType)) return response;
    try {
      const clone = response.clone();
      const body = await clone.text();
      window.localStorage.setItem(makeCacheKey(url), JSON.stringify({
        savedAt: Date.now(),
        status: response.status,
        headers: { "Content-Type": contentType || "application/json" },
        body
      }));
    } catch (_) {}
    return response;
  };

  const normalizePrefetchHref = (href) => {
    if (!href || href.startsWith("#") || href.startsWith("javascript:")) return null;
    try {
      const target = new URL(href, window.location.href);
      if (target.origin !== window.location.origin) return null;
      if (!/\.html($|\?)/i.test(target.pathname) && !/^\/(analytics|audit|automation-dashboard|chat|dashboard|operations|reports|sprints|teams)/i.test(target.pathname)) {
        return null;
      }
      return target.href;
    } catch (_) {
      return null;
    }
  };

  const prefetchPage = (href) => {
    if (!canPrefetch()) return;
    const normalized = normalizePrefetchHref(href);
    if (!normalized || prefetchedPages.has(normalized)) return;
    prefetchedPages.add(normalized);
    try {
      const link = document.createElement("link");
      link.rel = "prefetch";
      link.as = "document";
      link.href = normalized;
      document.head.appendChild(link);
    } catch (_) {}
    window.fetch.bind(window)(normalized, { method: "GET", credentials: "same-origin" }).catch(() => null);
  };

  const bindNavigationPrefetch = () => {
    if (!document || !document.body || document.body.dataset.sfPrefetchBound === "true") return;
    document.body.dataset.sfPrefetchBound = "true";
    const trigger = (event) => {
      const link = event.target && event.target.closest ? event.target.closest("a[href]") : null;
      if (!link) return;
      prefetchPage(link.getAttribute("href"));
    };
    document.addEventListener("mouseover", trigger, { passive: true });
    document.addEventListener("focusin", trigger);
  };

  const bindPendingForms = () => {
    if (!document || !document.body || document.body.dataset.sfPendingFormBound === "true") return;
    document.body.dataset.sfPendingFormBound = "true";
    document.addEventListener("submit", (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;
      const submitter = event.submitter || form.querySelector('button[type="submit"],input[type="submit"]');
      if (!submitter || submitter.dataset.sfPending === "true") return;
      submitter.dataset.sfPending = "true";
      submitter.dataset.sfOriginalLabel = submitter.innerHTML;
      submitter.disabled = true;
      submitter.style.opacity = "0.72";
      submitter.style.cursor = "wait";
      submitter.innerHTML = '<span style="display:inline-flex;align-items:center;gap:8px;"><span style="width:12px;height:12px;border:2px solid rgba(255,255,255,0.35);border-top-color:currentColor;border-radius:999px;display:inline-block;animation:sf-runtime-spin 0.9s linear infinite;"></span><span>Loading...</span></span>';
      pendingButtons.add(submitter);
      setTimeout(() => {
        if (activeRequests === 0 && pendingButtons.has(submitter)) {
          submitter.disabled = false;
          submitter.style.opacity = "";
          submitter.style.cursor = "";
          if (submitter.dataset.sfOriginalLabel) {
            submitter.innerHTML = submitter.dataset.sfOriginalLabel;
          }
          delete submitter.dataset.sfOriginalLabel;
          delete submitter.dataset.sfPending;
          pendingButtons.delete(submitter);
        }
      }, 12000);
    }, true);
    window.addEventListener("pageshow", () => {
      pendingButtons.clear();
    });
    if (!document.getElementById("sf-runtime-spin-style")) {
      const style = document.createElement("style");
      style.id = "sf-runtime-spin-style";
      style.textContent = "@keyframes sf-runtime-spin{to{transform:rotate(360deg)}}";
      document.head.appendChild(style);
    }
  };

  const runtime = {
    nowText: () => new Date().toLocaleString("ko-KR", { hour12: false }),
    safeText: (value) => String(value ?? ""),

    escapeCSV: (value) => {
      const text = String(value ?? "");
      return `"${text.replaceAll(FALLBACK_CHAR, `${FALLBACK_CHAR}${FALLBACK_CHAR}`)}"`;
    },

    toCSV: (rows, header = null) => {
      const normalized = Array.isArray(rows) ? rows : [];
      const withHeader = header ? [header, ...normalized] : normalized;
      return withHeader
        .map((row) => {
          if (!Array.isArray(row)) return "";
          return row.map(runtime.escapeCSV).join(",");
        })
        .filter(Boolean)
        .join("\n");
    },

    downloadText: (filename, text, type = "text/plain;charset=utf-8;") => {
      const blob = new Blob([text || ""], { type });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(url);
    },

    normalizePath: (path) => {
      if (!path) return "";
      if (path.startsWith("http://") || path.startsWith("https://")) return path;
      if (path.startsWith("/")) return path;
      if (path.startsWith("api/")) return `/${path}`;
      return `/api/v1/${path}`;
    },

    delay: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),

    request: async (path, options = {}, retries = RETRY_COUNT, baseDelay = RETRY_BASE_DELAY_MS) => {
      const url = runtime.normalizePath(path);
      const method = String(options.method || "GET").toUpperCase();
      const shouldUseCache = method === "GET" && options.cache !== "no-store" && options.disableCache !== true;
      const init = {
        ...options,
        headers: {
          Accept: "application/json",
          ...options.headers
        }
      };
      const inflightKey = shouldUseCache ? `${method}:${url}:${JSON.stringify(init.headers || {})}` : null;

      if (shouldUseCache) {
        const cached = readCache(url);
        if (cached) {
          if (!options.silentRefresh) {
            const refreshTask = runtime.request(path, { ...options, disableCache: true, silentRefresh: true }, retries, baseDelay).catch(() => null);
            if (refreshTask && typeof refreshTask.then === "function") {
              refreshTask.then(() => null);
            }
          }
          return cached;
        }
      }

      if (inflightKey && inflightRequests.has(inflightKey)) {
        return inflightRequests.get(inflightKey).then((response) => response.clone());
      }

      let latestError = null;
      const task = (async () => {
        beginProgress();
        for (let attempt = 0; attempt <= retries; attempt++) {
          try {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
            const response = await window.fetch.bind(window)(url, {
              ...init,
              signal: controller.signal
            });
            clearTimeout(timer);
            if (response.status >= 500 && attempt < retries) {
              throw new Error(`server error ${response.status}`);
            }
            if (shouldUseCache) {
              await writeCache(url, response.clone());
            }
            return response;
          } catch (error) {
            latestError = error;
            if (attempt < retries && navigator.onLine !== false) {
              const wait = baseDelay * Math.pow(2, attempt) + Math.random() * 220;
              await runtime.delay(Math.round(wait));
              continue;
            }
            break;
          }
        }
        throw latestError || new Error("network request failed");
      })();

      if (inflightKey) {
        inflightRequests.set(inflightKey, task);
      }

      try {
        const response = await task;
        return response;
      } finally {
        if (inflightKey) inflightRequests.delete(inflightKey);
        endProgress();
      }
    },

    apiFetch: async (path, options = {}, retryOptions = {}) => {
      const response = await runtime.request(
        path,
        options,
        retryOptions.retries ?? RETRY_COUNT,
        retryOptions.baseDelayMs ?? RETRY_BASE_DELAY_MS
      );
      if (!response) {
        throw new Error("empty response");
      }
      return response;
    },

    fetchJson: async (path, options = {}, retryOptions = {}) => {
      const response = await runtime.apiFetch(path, options, retryOptions);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    },

    appendStatus: (el, value) => {
      const target = typeof el === "string" ? document.getElementById(el) : el;
      if (!target) return;
      target.textContent = value == null ? "" : String(value);
    },
    prefetchPage,
  };

  window.sfRuntime = window.sfRuntime ? { ...window.sfRuntime, ...runtime } : runtime;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      bindNavigationPrefetch();
      bindPendingForms();
    });
  } else {
    bindNavigationPrefetch();
    bindPendingForms();
  }
})();
