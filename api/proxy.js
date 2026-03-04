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
  const backend = process.env.API_UPSTREAM_URL || process.env.VERCEL_API_UPSTREAM_URL;
  if (!backend) return null;

  const target = `${backend.replace(/\/$/, "")}${parsedPath.path}${parsedPath.search}`;
  const fetchOptions = {
    method: req.method,
    headers: { "Accept": "application/json" }
  };

  if (req.headers["content-type"]) {
    fetchOptions.headers["Content-Type"] = req.headers["content-type"];
  }

  if (req.body && (req.method === "POST" || req.method === "PUT" || req.method === "PATCH")) {
    fetchOptions.body = req.body;
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
    if (response && response.ok) {
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

    return sendFallback(res, req, parsedPath);
  } catch (error) {
    return toJson(res, {
      ok: false,
      status: "mock-fallback",
      message: error?.message || "proxy failed"
    }, 200);
  }
};
