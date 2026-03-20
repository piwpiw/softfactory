const FALLBACK_TEAMS = [
  {
    id: "team-core",
    name: "Core Platform",
    status: "stable",
    department: "Platform",
    uptime_ratio: 99.8
  },
  {
    id: "team-sns",
    name: "SNS Auto",
    status: "stable",
    department: "Growth",
    uptime_ratio: 99.6
  },
  {
    id: "team-review",
    name: "Review Automation",
    status: "warning",
    department: "Operations",
    uptime_ratio: 98.9
  }
];

const FALLBACK_HOURLY = Array.from({ length: 24 }, (_, index) => ({
  hour: String(index).padStart(2, "0"),
  throughput: 25 + ((index * 7) % 45),
  success_rate: 94 + (index % 6)
}));

const FALLBACK_CYCLES = [
  { id: 1, name: "Daily Sync", status: "completed", started_at: "2026-03-04T00:00:00Z", finished_at: "2026-03-04T00:12:00Z", duration_ms: 720000 },
  { id: 2, name: "Campaign Boost", status: "running", started_at: "2026-03-04T01:00:00Z", progress: 64 },
  { id: 3, name: "Inventory Check", status: "completed", started_at: "2026-03-03T22:00:00Z", finished_at: "2026-03-03T22:09:00Z", duration_ms: 540000 }
];

const toJson = (res, body, statusCode = 200, headers = {}) => {
  const payload = JSON.stringify(body);
  res.statusCode = statusCode;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  Object.entries(headers).forEach(([key, value]) => {
    res.setHeader(key, value);
  });
  res.end(payload);
};

const toText = (res, body, statusCode = 200, headers = {}) => {
  res.statusCode = statusCode;
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  Object.entries(headers).forEach(([key, value]) => {
    res.setHeader(key, value);
  });
  res.end(body || "");
};

const parseApiPath = (req) => {
  const url = new URL(req.url, "http://localhost");
  const path = (url.searchParams.get("path") || "").toString().replace(/^\/+/, "");
  const forwardedQuery = new URLSearchParams(url.searchParams);
  forwardedQuery.delete("path");

  const queryString = forwardedQuery.toString();
  return {
    path: path ? `/${path}` : "/",
    queryString,
    search: queryString ? `?${queryString}` : "",
    query: Object.fromEntries(forwardedQuery.entries())
  };
};

const STRICT_REAL_PREFIXES = [
  "/auth/",
  "/platform/",
  "/coocook/",
  "/sns/",
  "/ai-automation/",
  "/instagram-cardnews/",
  "/review/",
  "/videos/",
  "/files/",
  "/search/",
  "/notifications",
];

const requiresStrictRealApi = (path) => STRICT_REAL_PREFIXES.some((prefix) => path.startsWith(prefix));

const readRequestBody = async (req) => {
  if (req.body) {
    if (typeof req.body === "string" || Buffer.isBuffer(req.body)) return req.body;
    return JSON.stringify(req.body);
  }

  if (req.method === "GET" || req.method === "HEAD") {
    return null;
  }

  return await new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)));
    req.on("end", () => {
      if (chunks.length === 0) {
        resolve(null);
        return;
      }
      resolve(Buffer.concat(chunks));
    });
    req.on("error", reject);
  });
};

const sendFallback = (res, req, parsedPath) => {
  const method = req.method?.toUpperCase() || "GET";
  const path = parsedPath.path;
  const query = parsedPath.query;
  const params = new URLSearchParams(query);

  if (path === "/v1/status") {
    return toJson(res, {
      status: "ok",
      uptime: true,
      error_rate: 0.12,
      latency_ms: 45,
      updated_at: new Date().toISOString(),
      services: {
        platform: "stable",
        database: "stable",
        cache: "stable"
      }
    });
  }

  if (path === "/v1/teams") {
    return toJson(res, FALLBACK_TEAMS);
  }

  if (path === "/v1/automation/status") {
    return toJson(res, {
      status: "running",
      environment: "vercel-stub",
      cycle_count: FALLBACK_CYCLES.length,
      active_cycle_id: FALLBACK_CYCLES[1].id,
      progress: 64,
      updated_at: new Date().toISOString()
    });
  }

  if (path === "/v1/automation/hourly") {
    return toJson(res, FALLBACK_HOURLY);
  }

  if (path === "/v1/automation/cycles") {
    if (method === "POST") {
      return toJson(res, {
        status: "created",
        id: Date.now(),
        name: "new_cycle",
        created_at: new Date().toISOString()
      }, 201);
    }
    const limit = parseInt(params.get("limit"), 10);
    if (Number.isFinite(limit)) {
      return toJson(res, {
        items: FALLBACK_CYCLES.slice(0, limit),
        limit,
        total: FALLBACK_CYCLES.length
      });
    }
    return toJson(res, FALLBACK_CYCLES);
  }

  if (path === "/v1/chat/messages") {
    if (method === "POST") {
      return toJson(res, {
        id: Date.now(),
        created_at: new Date().toISOString(),
        role: "user",
        message: "요청이 접수되었습니다."
      }, 201);
    }
    return toJson(res, {
      items: [
        {
          id: 1,
          role: "system",
          message: "운영 전용 더미 채팅 데이터입니다.",
          created_at: new Date().toISOString()
        }
      ],
      page: 1,
      per_page: 20
    });
  }

  if (path.startsWith("/auth/")) {
    if (path.includes("/login")) {
      return toJson(res, {
        success: true,
        token: "dummy-admin-token",
        access_token: "dummy-admin-token",
        refresh_token: "dummy-admin-refresh-token",
        user: {
          id: "admin-001",
          name: "SoftFactory 관리자",
          email: "admin@softfactory.local",
          role: "admin"
        }
      }, 200);
    }
    if (path.includes("/me") || path.includes("/verify")) {
      return toJson(res, {
        id: "admin-001",
        name: "SoftFactory 관리자",
        email: "admin@softfactory.local",
        role: "admin",
        department: "Platform"
      });
    }
    return toJson(res, { success: true, status: "mock-auth-ok" });
  }

  if (path.startsWith("/review/") || path.startsWith("/sns/") || path.startsWith("/coocook/") || path.startsWith("/recipe/") || path.startsWith("/experience/") || path.startsWith("/metrics/") || path.startsWith("/platform/") || path.startsWith("/usage/") || path.startsWith("/errors/")) {
    return toJson(res, { items: [], total: 0, page: 1, success: true });
  }

  if (path.startsWith("/videos/")) {
    if (path.includes("/stream/")) {
      return toText(res, "", 404);
    }
    return toJson(res, { items: [], success: true });
  }

  if (path === "/_health") {
    return toJson(res, { status: "ok", scope: "proxy-fallback" });
  }

  return toJson(res, { ok: true, status: "mock", path, method });
};

const passToBackend = async (req, parsedPath) => {
  const backend =
    process.env.API_UPSTREAM_URL ||
    process.env.VERCEL_API_UPSTREAM_URL ||
    process.env.SOFTFACTORY_API_UPSTREAM_URL;
  if (!backend) return null;

  const normalizedBackend = String(backend).replace(/\\r\\n/g, "").trim().replace(/\/$/, "");
  if (!normalizedBackend) return null;

  const target = `${normalizedBackend}${parsedPath.path}${parsedPath.search}`;
  const body = await readRequestBody(req);
  const fetchOptions = {
    method: req.method,
    headers: {
      "Accept": req.headers["accept"] || "application/json",
      "User-Agent": req.headers["user-agent"] || "softfactory-vercel-proxy",
      "X-Forwarded-Host": req.headers["host"] || "",
      "X-Forwarded-Proto": "https",
    }
  };

  if (req.headers["content-type"]) {
    fetchOptions.headers["Content-Type"] = req.headers["content-type"];
  }
  if (req.headers["authorization"]) {
    fetchOptions.headers["Authorization"] = req.headers["authorization"];
  }
  if (req.headers["cookie"]) {
    fetchOptions.headers["Cookie"] = req.headers["cookie"];
  }
  if (req.headers["x-requested-with"]) {
    fetchOptions.headers["X-Requested-With"] = req.headers["x-requested-with"];
  }

  if (body && !["GET", "HEAD"].includes((req.method || "GET").toUpperCase())) {
    fetchOptions.body = body;
  }

  const response = await fetch(target, fetchOptions);
  return response;
};

module.exports = async (req, res) => {
  try {
    const parsedPath = parseApiPath(req);
    if (!parsedPath.path || parsedPath.path === "/") {
      return toJson(res, { message: "softfactory-platform api proxy" });
    }

    const response = await passToBackend(req, parsedPath).catch(() => null);
    if (response) {
      const body = await response.text();
      res.statusCode = response.status;
      response.headers.forEach((value, key) => {
        if (["transfer-encoding", "content-encoding", "content-length", "connection"].includes(key.toLowerCase())) {
          return;
        }
        res.setHeader(key, value);
      });
      res.end(body);
      return;
    }

    if (requiresStrictRealApi(parsedPath.path)) {
      return toJson(res, {
        ok: false,
        status: "upstream-required",
        path: parsedPath.path,
        message: "Real backend upstream is not configured for this deployment.",
      }, 503);
    }

    return sendFallback(res, req, parsedPath);
  } catch (error) {
    const parsedPath = parseApiPath(req);
    if (requiresStrictRealApi(parsedPath.path)) {
      return toJson(res, {
        ok: false,
        status: "upstream-error",
        path: parsedPath.path,
        message: error?.message || "proxy failed",
      }, 502);
    }
    return toJson(res, {
      ok: false,
      status: "mock-fallback",
      message: error?.message || "proxy failed"
    }, 200);
  }
};
