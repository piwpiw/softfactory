(function () {
  const STORAGE_KEY = "sf_unified_approval_queue";
  const API_PATH = "/api/platform/approval-queue";
  const ADMIN_API_PATH = "/api/platform/admin/approval-queue";
  const EVENTS_API_PATH = "/api/platform/admin/approval-queue/events";

  function safeParse(raw, fallback) {
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function loadQueue() {
    return safeParse(localStorage.getItem(STORAGE_KEY), []);
  }

  function saveQueue(queue) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    return queue;
  }

  function getAuthToken() {
    try {
      return localStorage.getItem("access_token") || "";
    } catch (_) {
      return "";
    }
  }

  function canUseApi() {
    return typeof fetch === "function" && !!getAuthToken();
  }

  async function apiFetch(path, options = {}) {
    const token = getAuthToken();
    if (!token) {
      throw new Error("missing access token");
    }

    const response = await fetch(path, {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      credentials: "same-origin",
    });

    if (!response.ok) {
      throw new Error(`approval queue api failed: ${response.status}`);
    }
    return response.json();
  }

  function enqueue(item) {
    const queue = loadQueue().filter((entry) => entry.id !== item.id);
    queue.unshift(item);
    saveQueue(queue);
    return item;
  }

  function updateStatus(id, status) {
    const queue = loadQueue().map((entry) => {
      if (entry.id !== id) return entry;
      return Object.assign({}, entry, {
        status,
        updated_at: new Date().toISOString()
      });
    });
    saveQueue(queue);
    return queue.find((entry) => entry.id === id) || null;
  }

  function remove(id) {
    const queue = loadQueue().filter((entry) => entry.id !== id);
    saveQueue(queue);
    return queue;
  }

  function summarize(queue) {
    const source = Array.isArray(queue) ? queue : loadQueue();
    return source.reduce((acc, entry) => {
      acc.total += 1;
      acc.byStatus[entry.status] = (acc.byStatus[entry.status] || 0) + 1;
      acc.byService[entry.service] = (acc.byService[entry.service] || 0) + 1;
      return acc;
    }, { total: 0, byStatus: {}, byService: {} });
  }

  async function fetchSummary(options = {}) {
    const isAdmin = !!options.admin;
    const path = isAdmin ? `${ADMIN_API_PATH}/summary` : `${API_PATH}/summary`;
    if (!canUseApi()) {
      return summarize(loadQueue());
    }
    try {
      return await apiFetch(path);
    } catch (_) {
      return summarize(loadQueue());
    }
  }

  async function fetchRecentEvents(limit = 20) {
    if (!canUseApi()) {
      return [];
    }
    try {
      const data = await apiFetch(`${EVENTS_API_PATH}?limit=${encodeURIComponent(limit)}`);
      return Array.isArray(data.items) ? data.items : [];
    } catch (_) {
      return [];
    }
  }

  function normalizeEntry(input) {
    return {
      ...input,
      id: input.id || `${input.service}:${Date.now()}`,
      service: input.service || "unknown",
      title: input.title || "Untitled item",
      status: input.status || "queued",
      owner: input.owner || "system",
      approvalMode: input.approvalMode || "approve-before-publish",
      channels: Array.isArray(input.channels) ? input.channels : [],
      accountIds: Array.isArray(input.accountIds) ? input.accountIds : [],
      scheduledAt: input.scheduledAt || null,
      sourceUrl: input.sourceUrl || "",
      summary: input.summary || "",
      created_at: input.created_at || new Date().toISOString(),
      updated_at: input.updated_at || new Date().toISOString()
    };
  }

  window.SoftFactoryApprovalQueue = {
    STORAGE_KEY,
    loadQueue,
    saveQueue,
    enqueue(item) {
      return enqueue(normalizeEntry(item));
    },
    async syncRemote() {
      if (!canUseApi()) return loadQueue();
      try {
        const data = await apiFetch(API_PATH);
        const items = Array.isArray(data.items) ? data.items : [];
        saveQueue(items);
        return items;
      } catch (_) {
        return loadQueue();
      }
    },
    async syncRemoteAdmin() {
      if (!canUseApi()) return loadQueue();
      try {
        const data = await apiFetch(ADMIN_API_PATH);
        const items = Array.isArray(data.items) ? data.items : [];
        saveQueue(items);
        return items;
      } catch (_) {
        return loadQueue();
      }
    },
    async enqueuePersist(item) {
      const normalized = normalizeEntry(item);
      enqueue(normalized);
      if (canUseApi()) {
        try {
          await apiFetch(API_PATH, { method: "POST", body: normalized });
        } catch (_) {
          return normalized;
        }
      }
      return normalized;
    },
    updateStatus,
    async updateStatusPersist(id, status) {
      const updated = updateStatus(id, status);
      if (canUseApi()) {
        try {
          await apiFetch(`${API_PATH}/${encodeURIComponent(id)}/status`, {
            method: "POST",
            body: { status }
          });
        } catch (_) {
          return updated;
        }
      }
      return updated;
    },
    remove,
    fetchSummary,
    fetchRecentEvents,
    async removePersist(id) {
      const queue = remove(id);
      if (canUseApi()) {
        try {
          await apiFetch(`${API_PATH}/${encodeURIComponent(id)}`, {
            method: "DELETE"
          });
        } catch (_) {
          return queue;
        }
      }
      return queue;
    },
    summarize
  };
})();
