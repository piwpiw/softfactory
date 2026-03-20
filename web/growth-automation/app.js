(function () {
  const page = document.body.dataset.page;
  const bootstrapPath = "/api/v1/growth/public/bootstrap";
  const stageLabels = {
    lead: "Lead",
    signed_up: "Signed Up",
    active: "Active",
    trial: "Trial",
    inactive: "Inactive",
    at_risk: "At Risk",
    lead_captured: "Lead Captured",
    signup_completed: "Signup Completed",
    activated: "Activated",
    key_action_completed: "Key Action Completed",
    payment_failed: "Payment Failed",
    reengagement: "Reengagement",
  };
  const uiCopy = {
    initError: "화면 초기화 실패",
    eventError: "이벤트 실행 실패",
  };
  const state = {
    bootstrap: null,
    contacts: [],
    journeys: [],
    events: [],
    dlq: [],
    summary: null,
    ui: {
      contactPreset: "all",
      journeyPreset: "all",
      opsPreset: "all",
    },
    baseline: null,
    trendSeries: null,
  };

  function qs(id) {
    return document.getElementById(id);
  }

  function safe(value, fallback = "-") {
    if (value === null || value === undefined || value === "") return fallback;
    return String(value);
  }

  function labelize(value) {
    const key = safe(value, "").trim();
    return stageLabels[key] || key.replaceAll("_", " ");
  }

  function timeText(raw) {
    if (!raw) return "-";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return safe(raw);
    return d.toLocaleString("ko-KR");
  }

  function setText(id, text) {
    const el = qs(id);
    if (el) el.textContent = text;
  }

  function escapeHtml(value) {
    return safe(value, "").replace(/[&<>"']/g, (match) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[match]));
  }

  function renderDetailGrid(targetId, items) {
    const target = qs(targetId);
    if (!target) return;
    target.innerHTML = (items || [])
      .map((item) => `<div class="detail-item"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.value)}</span></div>`)
      .join("");
  }

  function renderFilterChips(targetId, items, activeValue, onSelect) {
    const target = qs(targetId);
    if (!target) return;
    target.innerHTML = items
      .map((item) => `<button type="button" class="filter-chip ${item.value === activeValue ? "is-active" : ""}" data-filter-value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</button>`)
      .join("");
    target.querySelectorAll("[data-filter-value]").forEach((button) => {
      button.addEventListener("click", () => onSelect(button.dataset.filterValue));
    });
  }

  function renderCompareGrid(targetId, items) {
    const target = qs(targetId);
    if (!target) return;
    target.innerHTML = (items || [])
      .map((item) => `<article class="compare-card"><div class="compare-head"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.value)}</span></div><div class="compare-trend ${escapeHtml(item.trendClass || "")}">${escapeHtml(item.delta || "")}</div><div class="compare-bar"><div class="compare-fill" style="width:${escapeHtml(item.percent)}%"></div></div><p>${escapeHtml(item.hint)}</p></article>`)
      .join("");
  }

  function renderTrendStrip(targetId, items) {
    const target = qs(targetId);
    if (!target) return;
    const maxMetric = Math.max(...(items || []).map((item) => Number(item.metricValue || 0)), 1);
    target.innerHTML = (items || [])
      .map((item) => {
        const height = Math.max(18, Math.round(((Number(item.metricValue || 0)) / maxMetric) * 56));
        return `<article class="trend-card"><div class="trend-label">${escapeHtml(item.label)}</div><div class="trend-spark"><span class="trend-bar ${escapeHtml(item.trendClass || "")}" style="height:${height}px"></span></div><div class="trend-value">${escapeHtml(item.value)}</div><div class="trend-meta ${escapeHtml(item.trendClass || "")}">${escapeHtml(item.meta || "")}</div></article>`;
      })
      .join("");
  }

  function isoDaysAgo(days) {
    const date = new Date();
    date.setUTCDate(date.getUTCDate() - days);
    return date.toISOString();
  }

  async function getSummaryWindow(fromIso, toIso) {
    const query = `/api/v1/growth/dashboard/summary?from=${encodeURIComponent(fromIso)}&to=${encodeURIComponent(toIso)}`;
    return getJson(query);
  }

  async function getHistoricalBaseline() {
    if (state.baseline) return state.baseline;
    try {
      const currentFrom = isoDaysAgo(7);
      const currentTo = new Date().toISOString();
      const priorFrom = isoDaysAgo(14);
      const priorTo = isoDaysAgo(7);
      const [current, prior] = await Promise.all([
        getSummaryWindow(currentFrom, currentTo),
        getSummaryWindow(priorFrom, priorTo),
      ]);
      state.baseline = {
        label: "Last 7d vs prior 7d",
        current,
        prior,
      };
      return state.baseline;
    } catch (_error) {
      state.baseline = {
        label: "Heuristic baseline",
        current: null,
        prior: null,
      };
      return state.baseline;
    }
  }

  async function getTrendSeries() {
    if (state.trendSeries) return state.trendSeries;
    try {
      const windows = [
        { label: "Current 7d", from: isoDaysAgo(7), to: new Date().toISOString() },
        { label: "Prior 7d", from: isoDaysAgo(14), to: isoDaysAgo(7) },
        { label: "Prior 14-21d", from: isoDaysAgo(21), to: isoDaysAgo(14) },
      ];
      const summaries = await Promise.all(windows.map((window) => getSummaryWindow(window.from, window.to)));
      state.trendSeries = windows.map((window, index) => ({
        label: window.label,
        summary: summaries[index],
      }));
      return state.trendSeries;
    } catch (_error) {
      state.trendSeries = [];
      return state.trendSeries;
    }
  }

  function buildDelta(current, prior, options = {}) {
    const { preferLower = false, suffix = "" } = options;
    if (prior === null || prior === undefined) {
      return {
        text: suffix ? `baseline unavailable ${suffix}` : "baseline unavailable",
        trendClass: "",
      };
    }
    const diff = current - prior;
    const directionGood = preferLower ? diff <= 0 : diff >= 0;
    const prefix = diff === 0 ? "flat" : diff > 0 ? `+${diff}` : `${diff}`;
    return {
      text: suffix ? `${prefix} ${suffix}` : prefix,
      trendClass: directionGood ? "trend-up" : "trend-down",
    };
  }

  function bindSelectableRows(container, rows, onSelect) {
    if (!container) return;
    container.querySelectorAll("tr[data-row-index]").forEach((rowEl) => {
      rowEl.addEventListener("click", () => {
        const index = Number(rowEl.dataset.rowIndex || "-1");
        const selected = rows[index];
        container.querySelectorAll("tr").forEach((item) => item.classList.remove("is-selected"));
        rowEl.classList.add("is-selected");
        if (selected) onSelect(selected);
      });
    });
  }

  function severityLevelForEvent(row) {
    if (!row) return "low";
    if (row.processing_status === "failed" || row.error_code) return "high";
    if (row.processing_status === "pending") return "medium";
    return "low";
  }

  function severityLevelForDlq(row) {
    if (!row) return "low";
    if (row.status === "open") return "high";
    if ((row.retry_count || 0) > 0) return "medium";
    return "low";
  }

  function renderSeverityBadge(level) {
    return `<span class="severity-badge severity-${escapeHtml(level)}">${escapeHtml(level)}</span>`;
  }

  async function apiFetch(path, options = {}) {
    const response = await sfRuntime.apiFetch(path, options);
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return response;
  }

  async function getJson(path) {
    const response = await apiFetch(path);
    return response.json();
  }

  async function getBootstrap(force = false) {
    if (!force && state.bootstrap) return state.bootstrap;
    state.bootstrap = await getJson(bootstrapPath);
    return state.bootstrap;
  }

  async function withBootstrapFallback(loader, fallbackKey) {
    try {
      return await loader();
    } catch (error) {
      const bootstrap = await getBootstrap();
      if (fallbackKey && bootstrap[fallbackKey] !== undefined) {
        return bootstrap[fallbackKey];
      }
      throw error;
    }
  }

  function aggregateCounts(rows, field) {
    return (rows || []).reduce((acc, row) => {
      const key = safe(row?.[field], "unknown");
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
  }

  function buildSummaryCards(summary) {
    if (!summary) return [];
    return [
      { label: "Contacts", value: summary.contacts?.total ?? 0, hint: "Tracked contacts", tone: "neutral" },
      { label: "Events", value: summary.events?.total ?? 0, hint: "Ingested events", tone: "neutral" },
      { label: "Failed Events", value: summary.events?.failed ?? 0, hint: "Processing failures", tone: (summary.events?.failed ?? 0) > 0 ? "danger" : "ok" },
      { label: "Open DLQ", value: summary.errors?.dlq_open ?? 0, hint: "Recovery queue", tone: (summary.errors?.dlq_open ?? 0) > 0 ? "warning" : "ok" },
      { label: "Journey States", value: Object.keys(summary.journey_counts || {}).length, hint: "Active states", tone: "accent" },
    ];
  }

  function renderSummaryCards(targetId, summary) {
    const target = qs(targetId);
    if (!target) return;
    target.innerHTML = buildSummaryCards(summary)
      .map((card) => `<article class="stat stat-${escapeHtml(card.tone || "neutral")}"><div class="k">${escapeHtml(card.label)}</div><div class="v">${escapeHtml(card.value)}</div><div class="k">${escapeHtml(card.hint)}</div></article>`)
      .join("");
  }

  function deriveTodayFocus(summary) {
    if (!summary) return "데이터를 불러오는 중입니다.";
    const failed = summary.events?.failed ?? 0;
    const dlqOpen = summary.errors?.dlq_open ?? 0;
    const pending = summary.queue?.pending ?? 0;
    const contactTotal = summary.contacts?.total ?? 0;
    if (dlqOpen > 0) return `지금은 DLQ ${dlqOpen}건을 먼저 복구해야 합니다. Ops에서 replay 이후 상태를 다시 확인하세요.`;
    if (failed > 0) return `처리 실패 이벤트가 ${failed}건 있습니다. 최근 실패 원인을 먼저 확인하세요.`;
    if (pending > 0) return `대기 중인 이벤트가 ${pending}건 있습니다. queue 소비 상태를 점검해야 합니다.`;
    if (contactTotal === 0) return "리드가 아직 없습니다. Hub 또는 Contacts에서 lead_captured 시나리오를 먼저 실행하세요.";
    return "현재 기본 흐름은 비교적 안정적입니다. signup과 key action 시나리오를 계속 실행해 전환 흐름을 검증하세요.";
  }

  function deriveRecommendations(summary) {
    if (!summary) return [];
    const recs = [];
    const contactTotal = summary.contacts?.total ?? 0;
    const activeTotal = summary.journey_counts?.active ?? 0;
    const failed = summary.events?.failed ?? 0;
    const dlqOpen = summary.errors?.dlq_open ?? 0;
    const pending = summary.queue?.pending ?? 0;

    if (contactTotal === 0) {
      recs.push({
        title: "Lead 유입부터 시작",
        description: "현재 contact가 없습니다. lead_captured를 먼저 생성해 유입부터 contact 생성까지 연결하세요.",
        action: "Contacts 또는 Hub에서 lead 생성",
      });
    }
    if (contactTotal > 0 && activeTotal === 0) {
      recs.push({
        title: "활성화 전환 확인",
        description: "가입은 생겼지만 active 상태가 없습니다. signup_completed 다음 key_action_completed를 바로 실행해보세요.",
        action: "Journeys에서 전환 시나리오 실행",
      });
    }
    if (failed > 0) {
      recs.push({
        title: "실패 이벤트 우선 점검",
        description: `현재 실패 이벤트가 ${failed}건 있습니다. 상태 전이 실패인지 queue 처리 실패인지 먼저 구분해야 합니다.`,
        action: "Ops에서 실패 이벤트 확인",
      });
    }
    if (dlqOpen > 0) {
      recs.push({
        title: "DLQ 복구 진행",
        description: `Open DLQ ${dlqOpen}건이 남아 있습니다. replay 이후 status와 pending queue를 같이 확인하세요.`,
        action: "Ops에서 replay 실행",
      });
    }
    if (pending > 0) {
      recs.push({
        title: "대기 큐 확인",
        description: `pending ${pending}건이 남아 있습니다. 워크플로 소비가 지연되는지 점검이 필요합니다.`,
        action: "Ops에서 queue 상태 확인",
      });
    }
    if (!recs.length) {
      recs.push({
        title: "전환 품질 점검",
        description: "기본 흐름은 정상입니다. lead -> signup -> active -> risk 시나리오를 반복 실행해 품질을 점검하세요.",
        action: "Hub 또는 Journeys에서 시나리오 실행",
      });
    }
    return recs.slice(0, 4);
  }

  function renderRecommendations(targetId, recommendations) {
    const target = qs(targetId);
    if (!target) return;
    target.innerHTML = (recommendations || [])
      .map((rec, index) => `<article class="rec"><div class="rec-meta"><span class="rec-index">P${index + 1}</span><span class="rec-action">${escapeHtml(rec.action || "Review")}</span></div><h3>${escapeHtml(rec.title)}</h3><p>${escapeHtml(rec.description)}</p></article>`)
      .join("");
  }

  async function seedEvent(eventName, identity = {}) {
    const payload = {
      event_name: eventName,
      event_id: `ui-${eventName}-${Date.now()}`,
      ts: new Date().toISOString(),
      identity: {
        email: identity.email || undefined,
        phone: identity.phone || undefined,
        anonymous_id: `web-${Date.now()}`,
      },
      context: { source: "growth-automation-ui" },
      props: { page },
    };
    const response = await apiFetch("/api/v1/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.json();
  }

  function bindSeedButtons() {
    const buttons = Array.from(document.querySelectorAll("[data-seed-event]"));
    if (!buttons.length) return;
    buttons.forEach((button) => {
      button.addEventListener("click", async () => {
        const eventName = button.dataset.seedEvent;
        const email = qs("hubEmail")?.value?.trim() || qs("journeyEmail")?.value?.trim() || qs("leadEmail")?.value?.trim() || "";
        const phone = qs("hubPhone")?.value?.trim() || qs("journeyPhone")?.value?.trim() || qs("leadPhone")?.value?.trim() || "";
        const original = button.textContent;
        button.disabled = true;
        button.textContent = "Running...";
        try {
          await seedEvent(eventName, { email, phone });
          if (page === "hub") {
            await renderHub();
            setText("todayFocus", `${labelize(eventName)} 이벤트를 실행했습니다. 아래 요약과 최근 신호에서 반영 여부를 확인하세요.`);
          }
          if (page === "journeys") {
            await renderJourneys();
            setText("journeyActionHint", `${labelize(eventName)} 실행이 완료되었습니다. 상태 카드와 최근 이벤트 표에서 결과를 확인하세요.`);
          }
          if (page === "contacts") {
            await renderContacts();
            setText("contactsFeedback", `${labelize(eventName)} 이벤트를 실행했습니다. 목록 상단과 segment를 확인하세요.`);
          }
        } catch (error) {
          if (page === "hub") setText("todayFocus", `이벤트 실행 실패: ${error.message}`);
          if (page === "journeys") setText("journeyActionHint", `이벤트 실행 실패: ${error.message}`);
          if (page === "contacts") setText("contactsFeedback", `이벤트 실행 실패: ${error.message}`);
        } finally {
          button.disabled = false;
          button.textContent = original;
        }
      });
    });
  }

  async function createLeadFromContacts() {
    const email = qs("leadEmail")?.value?.trim() || "";
    const phone = qs("leadPhone")?.value?.trim() || "";
    if (!email && !phone) {
      setText("contactsFeedback", "이메일 또는 전화번호를 입력하세요.");
      return;
    }

    const button = qs("leadCreateBtn");
    const original = button?.textContent || "Create";
    if (button) {
      button.disabled = true;
      button.textContent = "Saving...";
    }
    try {
      try {
        await apiFetch("/api/v1/growth/contacts/upsert", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: email || undefined,
            phone: phone || undefined,
            lifecycle_stage: "lead",
          }),
        });
      } catch (error) {
        if (![401, 403].includes(error.status)) throw error;
      }
      await seedEvent("lead_captured", { email, phone });
      await renderContacts();
      setText("contactsFeedback", "Lead를 생성했습니다. 리스트와 segment 분포에서 반영 결과를 확인하세요.");
    } catch (error) {
      setText("contactsFeedback", `Lead 생성 실패: ${error.message}`);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = original;
      }
    }
  }

  async function renderHub() {
    const bootstrap = await getBootstrap(true);
    const summary = await withBootstrapFallback(() => getJson("/api/v1/growth/dashboard/summary"), "summary");
    const eventsPayload = await withBootstrapFallback(() => getJson("/api/v1/growth/events?per_page=10&page=1"), "events");
    const journeyRows = bootstrap.journeys || [];
    const events = Array.isArray(eventsPayload.items) ? eventsPayload.items : (eventsPayload || []);

    state.summary = summary;
    renderSummaryCards("summaryCards", summary);
    renderRecommendations("recommendationList", deriveRecommendations(summary));
    setText("todayFocus", deriveTodayFocus(summary));

    const eventRows = qs("eventRows");
    if (eventRows) {
      eventRows.innerHTML = events.slice(0, 10)
        .map((row) => `<tr><td>${timeText(row.event_ts)}</td><td>${escapeHtml(labelize(row.event_name))}</td><td>${escapeHtml(row.processing_status)}</td><td>${escapeHtml(row.idempotency_key)}</td></tr>`)
        .join("");
    }

    const hubJourneyRows = qs("hubJourneyRows");
    if (hubJourneyRows) {
      hubJourneyRows.innerHTML = journeyRows.slice(0, 8)
        .map((row) => `<tr><td>${escapeHtml(row.journey_id)}</td><td>${escapeHtml(labelize(row.state))}</td><td>${timeText(row.entered_at)}</td></tr>`)
        .join("");
    }
  }

  async function renderContacts() {
    const keyword = encodeURIComponent((qs("contactKeyword")?.value || "").trim());
    const payload = await withBootstrapFallback(
      () => getJson(`/api/v1/growth/contacts?page=1&per_page=50${keyword ? `&q=${keyword}` : ""}`),
      "contacts"
    );
    const summary = await withBootstrapFallback(() => getJson("/api/v1/growth/dashboard/summary"), "summary");
    const allRows = Array.isArray(payload.items) ? payload.items : (payload || []);
    const lifecycleCounts = summary?.contacts?.lifecycle_counts || aggregateCounts(allRows, "lifecycle_stage");
    const baseline = await getHistoricalBaseline();
    const trendSeries = await getTrendSeries();
    const priorLifecycle = baseline.prior?.contacts?.lifecycle_counts || {};
    const preset = state.ui.contactPreset;
    const rows = allRows.filter((row) => {
      if (preset === "lead") return row.lifecycle_stage === "lead";
      if (preset === "active") return row.lifecycle_stage === "active";
      if (preset === "at_risk") return row.lifecycle_stage === "at_risk";
      return true;
    });

    const cardsTarget = qs("contactSummaryCards");
    if (cardsTarget) {
      const summaryCards = [
        { label: "Total Contacts", value: rows.length || summary?.contacts?.total || 0, hint: "Current list scope", tone: "neutral" },
        { label: "Lead", value: lifecycleCounts.lead || 0, hint: "Initial stage", tone: "accent" },
        { label: "Active", value: lifecycleCounts.active || 0, hint: "Activated users", tone: "ok" },
        { label: "At Risk", value: lifecycleCounts.at_risk || 0, hint: "Recovery target", tone: (lifecycleCounts.at_risk || 0) > 0 ? "warning" : "ok" },
      ];
      cardsTarget.innerHTML = summaryCards
        .map((card) => `<article class="stat stat-${escapeHtml(card.tone || "neutral")}"><div class="k">${escapeHtml(card.label)}</div><div class="v">${escapeHtml(card.value)}</div><div class="k">${escapeHtml(card.hint)}</div></article>`)
        .join("");
    }

    const segmentTarget = qs("contactSegments");
    if (segmentTarget) {
      segmentTarget.innerHTML = Object.entries(lifecycleCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([key, value]) => `<span class="segment-chip">${escapeHtml(labelize(key))}: ${escapeHtml(value)}</span>`)
        .join("");
    }

    renderFilterChips("contactSavedFilters", [
      { value: "all", label: "All Contacts" },
      { value: "lead", label: "Lead Only" },
      { value: "active", label: "Active Only" },
      { value: "at_risk", label: "At Risk" },
    ], preset, async (value) => {
      state.ui.contactPreset = value;
      await renderContacts();
    });

    const total = Math.max(Object.values(lifecycleCounts).reduce((acc, value) => acc + value, 0), 1);
    renderCompareGrid("contactCompareGrid", [
      {
        label: "Lead Mix",
        value: `${lifecycleCounts.lead || 0}`,
        percent: Math.round(((lifecycleCounts.lead || 0) / total) * 100),
        delta: buildDelta(lifecycleCounts.lead || 0, priorLifecycle.lead, { suffix: "vs prior 7d" }).text,
        trendClass: buildDelta(lifecycleCounts.lead || 0, priorLifecycle.lead, { suffix: "vs prior 7d" }).trendClass,
        hint: `Top-of-funnel share in the current contact base (${baseline.label})`,
      },
      {
        label: "Active Mix",
        value: `${lifecycleCounts.active || 0}`,
        percent: Math.round(((lifecycleCounts.active || 0) / total) * 100),
        delta: buildDelta(lifecycleCounts.active || 0, priorLifecycle.active, { suffix: "vs prior 7d" }).text,
        trendClass: buildDelta(lifecycleCounts.active || 0, priorLifecycle.active, { suffix: "vs prior 7d" }).trendClass,
        hint: `Users already activated (${baseline.label})`,
      },
      {
        label: "Risk Mix",
        value: `${lifecycleCounts.at_risk || 0}`,
        percent: Math.round(((lifecycleCounts.at_risk || 0) / total) * 100),
        delta: buildDelta(lifecycleCounts.at_risk || 0, priorLifecycle.at_risk, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(lifecycleCounts.at_risk || 0, priorLifecycle.at_risk, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Recovery candidates inside the current base (${baseline.label})`,
      },
    ]);

    renderTrendStrip("contactTrendStrip", trendSeries.map((entry, index, series) => {
      const totalContacts = entry.summary?.contacts?.total ?? 0;
      const next = series[index + 1]?.summary?.contacts?.total;
      const delta = next === undefined ? "baseline" : `${totalContacts - next >= 0 ? "+" : ""}${totalContacts - next} vs prev`;
      return {
        label: entry.label,
        value: `${totalContacts} contacts`,
        metricValue: totalContacts,
        meta: delta,
        trendClass: next === undefined ? "" : (totalContacts >= next ? "trend-up" : "trend-down"),
      };
    }));

    const contactRows = qs("contactRows");
    if (contactRows) {
      contactRows.innerHTML = rows
        .map((row, index) => `<tr data-row-index="${index}"><td>${escapeHtml(row.contact_uid)}</td><td>${escapeHtml(row.email)}</td><td>${escapeHtml(row.phone)}</td><td>${escapeHtml(row.status)}</td><td>${escapeHtml(labelize(row.lifecycle_stage))}</td><td>${timeText(row.created_at)}</td></tr>`)
        .join("");

      bindSelectableRows(contactRows, rows, (selected) => {
        renderDetailGrid("contactDetailGrid", [
          { label: "Contact UID", value: selected.contact_uid },
          { label: "Email", value: selected.email || "-" },
          { label: "Phone", value: selected.phone || "-" },
          { label: "Status", value: selected.status || "-" },
          { label: "Lifecycle", value: labelize(selected.lifecycle_stage) },
          { label: "Created", value: timeText(selected.created_at) },
        ]);
      });

      if (rows[0]) {
        const firstRow = contactRows.querySelector('tr[data-row-index="0"]');
        if (firstRow) firstRow.classList.add("is-selected");
        renderDetailGrid("contactDetailGrid", [
          { label: "Contact UID", value: rows[0].contact_uid },
          { label: "Email", value: rows[0].email || "-" },
          { label: "Phone", value: rows[0].phone || "-" },
          { label: "Status", value: rows[0].status || "-" },
          { label: "Lifecycle", value: labelize(rows[0].lifecycle_stage) },
          { label: "Created", value: timeText(rows[0].created_at) },
        ]);
      }
    }
  }

  async function renderJourneys() {
    const stateFilter = qs("journeyStateFilter")?.value || "";
    const payload = await withBootstrapFallback(
      () => getJson(`/api/v1/growth/journeys?page=1&per_page=100${stateFilter ? `&state=${encodeURIComponent(stateFilter)}` : ""}`),
      "journeys"
    );
    const eventsPayload = await withBootstrapFallback(() => getJson("/api/v1/growth/events?page=1&per_page=20"), "events");
    const summary = await withBootstrapFallback(() => getJson("/api/v1/growth/dashboard/summary"), "summary");

    const rows = Array.isArray(payload.items) ? payload.items : (payload || []);
    const events = Array.isArray(eventsPayload.items) ? eventsPayload.items : (eventsPayload || []);
    const journeyCounts = summary?.journey_counts || aggregateCounts(rows, "state");
    const baseline = await getHistoricalBaseline();
    const trendSeries = await getTrendSeries();
    const priorJourneyCounts = baseline.prior?.journey_counts || {};

    const stageTarget = qs("journeyStageCards");
    if (stageTarget) {
      stageTarget.innerHTML = Object.entries(journeyCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([key, value]) => `<article class="stat-card stage-${escapeHtml(key)}"><div class="label">${escapeHtml(labelize(key))}</div><div class="value">${escapeHtml(value)}</div></article>`)
        .join("");
    }

    renderFilterChips("journeySavedFilters", [
      { value: "all", label: "All States" },
      { value: "lead", label: "Lead Queue" },
      { value: "active", label: "Active Focus" },
      { value: "at_risk", label: "Risk Focus" },
    ], state.ui.journeyPreset, async (value) => {
      state.ui.journeyPreset = value;
      const select = qs("journeyStateFilter");
      if (select) select.value = value === "all" ? "" : value;
      await renderJourneys();
    });

    const journeyTotal = Math.max(Object.values(journeyCounts).reduce((acc, value) => acc + value, 0), 1);
    renderCompareGrid("journeyCompareGrid", [
      {
        label: "Lead Share",
        value: `${journeyCounts.lead || 0}`,
        percent: Math.round(((journeyCounts.lead || 0) / journeyTotal) * 100),
        delta: buildDelta(journeyCounts.lead || 0, priorJourneyCounts.lead, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(journeyCounts.lead || 0, priorJourneyCounts.lead, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Contacts waiting for the next conversion step (${baseline.label})`,
      },
      {
        label: "Active Share",
        value: `${journeyCounts.active || 0}`,
        percent: Math.round(((journeyCounts.active || 0) / journeyTotal) * 100),
        delta: buildDelta(journeyCounts.active || 0, priorJourneyCounts.active, { suffix: "vs prior 7d" }).text,
        trendClass: buildDelta(journeyCounts.active || 0, priorJourneyCounts.active, { suffix: "vs prior 7d" }).trendClass,
        hint: `Contacts that have reached activation (${baseline.label})`,
      },
      {
        label: "Risk Share",
        value: `${journeyCounts.at_risk || 0}`,
        percent: Math.round(((journeyCounts.at_risk || 0) / journeyTotal) * 100),
        delta: buildDelta(journeyCounts.at_risk || 0, priorJourneyCounts.at_risk, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(journeyCounts.at_risk || 0, priorJourneyCounts.at_risk, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Contacts needing recovery treatment (${baseline.label})`,
      },
    ]);

    renderTrendStrip("journeyTrendStrip", trendSeries.map((entry, index, series) => {
      const activeCount = entry.summary?.journey_counts?.active ?? 0;
      const next = series[index + 1]?.summary?.journey_counts?.active;
      const delta = next === undefined ? "baseline" : `${activeCount - next >= 0 ? "+" : ""}${activeCount - next} vs prev`;
      return {
        label: entry.label,
        value: `${activeCount} active`,
        metricValue: activeCount,
        meta: delta,
        trendClass: next === undefined ? "" : (activeCount >= next ? "trend-up" : "trend-down"),
      };
    }));

    const actionList = qs("journeyActionList");
    if (actionList) {
      const stalled = (journeyCounts.lead || 0) > (journeyCounts.active || 0);
      const items = [
        { title: "전환 경로 확인", text: "lead -> signup -> active 흐름이 실제로 이어지는지 확인하세요." },
        { title: stalled ? "lead 병목 점검 필요" : "active 전환 안정화", text: stalled ? "signup_completed와 key_action_completed를 연속 실행해 병목을 찾으세요." : "payment_failed를 추가해 리스크 흐름도 함께 점검하세요." },
        { title: "Cooldown 확인", text: "cooldown_until 값이 있으면 메시지가 막히는 이유를 설명할 수 있습니다." },
      ];
      actionList.innerHTML = items
        .map((item) => `<article class="list-item"><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.text)}</span></article>`)
        .join("");
    }

    const journeyRows = qs("journeyRows");
    if (journeyRows) {
      journeyRows.innerHTML = rows
        .map((row, index) => `<tr data-row-index="${index}"><td>${escapeHtml(row.contact_id)}</td><td>${escapeHtml(row.journey_id)}</td><td>${escapeHtml(labelize(row.state))}</td><td>${timeText(row.entered_at)}</td><td>${timeText(row.last_action_at)}</td><td>${timeText(row.cooldown_until)}</td></tr>`)
        .join("");

      bindSelectableRows(journeyRows, rows, (selected) => {
        renderDetailGrid("journeyDetailGrid", [
          { label: "Contact", value: selected.contact_id },
          { label: "Journey", value: selected.journey_id },
          { label: "State", value: labelize(selected.state) },
          { label: "Entered", value: timeText(selected.entered_at) },
          { label: "Last Action", value: timeText(selected.last_action_at) },
          { label: "Cooldown", value: timeText(selected.cooldown_until) },
        ]);
      });

      if (rows[0]) {
        const firstRow = journeyRows.querySelector('tr[data-row-index="0"]');
        if (firstRow) firstRow.classList.add("is-selected");
        renderDetailGrid("journeyDetailGrid", [
          { label: "Contact", value: rows[0].contact_id },
          { label: "Journey", value: rows[0].journey_id },
          { label: "State", value: labelize(rows[0].state) },
          { label: "Entered", value: timeText(rows[0].entered_at) },
          { label: "Last Action", value: timeText(rows[0].last_action_at) },
          { label: "Cooldown", value: timeText(rows[0].cooldown_until) },
        ]);
      }
    }

    const journeyEventRows = qs("journeyEventRows");
    if (journeyEventRows) {
      journeyEventRows.innerHTML = events.slice(0, 12)
        .map((row) => `<tr><td>${escapeHtml(labelize(row.event_name))}</td><td>${escapeHtml(row.processing_status)}</td><td>${escapeHtml(row.contact_id)}</td><td>${timeText(row.event_ts)}</td></tr>`)
        .join("");
    }
  }

  async function replayDlq(id, button) {
    const original = button?.textContent || "Replay";
    if (button) {
      button.disabled = true;
      button.textContent = "Replaying...";
    }
    try {
      await apiFetch(`/api/v1/growth/dlq/${id}/replay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "ops replay" }),
      });
      setText("opsFeedback", `DLQ ${id} replay를 요청했습니다. 상태 변화를 아래 표에서 다시 확인하세요.`);
      await renderOps();
    } catch (error) {
      setText("opsFeedback", `Replay 실패: ${error.message}`);
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = original;
      }
    }
  }

  async function renderOps() {
    const eventsPayload = await withBootstrapFallback(() => getJson("/api/v1/growth/events?page=1&per_page=20"), "events");
    const dlqPayload = await withBootstrapFallback(() => getJson("/api/v1/growth/dlq?page=1&per_page=20"), "dlq");
    const allEvents = Array.isArray(eventsPayload.items) ? eventsPayload.items : (eventsPayload || []);
    const allDlq = Array.isArray(dlqPayload.items) ? dlqPayload.items : (dlqPayload || []);
    const baseline = await getHistoricalBaseline();
    const trendSeries = await getTrendSeries();
    const priorEventsFailed = baseline.prior?.events?.failed;
    const priorPending = baseline.prior?.queue?.pending;
    const priorDlq = baseline.prior?.errors?.dlq_open;
    const preset = state.ui.opsPreset;
    const events = allEvents.filter((row) => {
      if (preset === "failed") return row.processing_status === "failed" || !!row.error_code;
      if (preset === "pending") return row.processing_status === "pending";
      return true;
    });
    const dlq = allDlq.filter((row) => {
      if (preset === "open_dlq") return row.status === "open";
      return true;
    });

    renderFilterChips("opsSavedFilters", [
      { value: "all", label: "All Signals" },
      { value: "failed", label: "Failed Events" },
      { value: "pending", label: "Pending Events" },
      { value: "open_dlq", label: "Open DLQ" },
    ], preset, async (value) => {
      state.ui.opsPreset = value;
      await renderOps();
    });

    renderCompareGrid("opsCompareGrid", [
      {
        label: "Failed Events",
        value: `${allEvents.filter((row) => row.processing_status === "failed" || row.error_code).length}`,
        percent: Math.round((allEvents.filter((row) => row.processing_status === "failed" || row.error_code).length / Math.max(allEvents.length, 1)) * 100),
        delta: buildDelta(allEvents.filter((row) => row.processing_status === "failed" || row.error_code).length, priorEventsFailed, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(allEvents.filter((row) => row.processing_status === "failed" || row.error_code).length, priorEventsFailed, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Signals that need operator review (${baseline.label})`,
      },
      {
        label: "Pending Events",
        value: `${allEvents.filter((row) => row.processing_status === "pending").length}`,
        percent: Math.round((allEvents.filter((row) => row.processing_status === "pending").length / Math.max(allEvents.length, 1)) * 100),
        delta: buildDelta(allEvents.filter((row) => row.processing_status === "pending").length, priorPending, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(allEvents.filter((row) => row.processing_status === "pending").length, priorPending, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Items waiting in the processing queue (${baseline.label})`,
      },
      {
        label: "Open DLQ",
        value: `${allDlq.filter((row) => row.status === "open").length}`,
        percent: Math.round((allDlq.filter((row) => row.status === "open").length / Math.max(allDlq.length, 1)) * 100),
        delta: buildDelta(allDlq.filter((row) => row.status === "open").length, priorDlq, { suffix: "vs prior 7d", preferLower: true }).text,
        trendClass: buildDelta(allDlq.filter((row) => row.status === "open").length, priorDlq, { suffix: "vs prior 7d", preferLower: true }).trendClass,
        hint: `Recovery queue still requiring replay or intervention (${baseline.label})`,
      },
    ]);

    renderTrendStrip("opsTrendStrip", trendSeries.map((entry, index, series) => {
      const failedCount = entry.summary?.events?.failed ?? 0;
      const next = series[index + 1]?.summary?.events?.failed;
      const delta = next === undefined ? "baseline" : `${failedCount - next >= 0 ? "+" : ""}${failedCount - next} vs prev`;
      return {
        label: entry.label,
        value: `${failedCount} failed`,
        metricValue: failedCount,
        meta: delta,
        trendClass: next === undefined ? "" : (failedCount <= next ? "trend-up" : "trend-down"),
      };
    }));

    const opsEventRows = qs("opsEventRows");
    if (opsEventRows) {
      opsEventRows.innerHTML = events
        .map((row, index) => `<tr data-row-index="${index}"><td>${escapeHtml(labelize(row.event_name))}</td><td>${renderSeverityBadge(severityLevelForEvent(row))} ${escapeHtml(row.processing_status)}</td><td>${escapeHtml(row.error_code)}</td><td>${timeText(row.event_ts)}</td></tr>`)
        .join("");

      bindSelectableRows(opsEventRows, events, (selected) => {
        renderDetailGrid("opsEventDetailGrid", [
          { label: "Event", value: labelize(selected.event_name) },
          { label: "Status", value: selected.processing_status || "-" },
          { label: "Severity", value: severityLevelForEvent(selected) },
          { label: "Error Code", value: selected.error_code || "-" },
          { label: "Contact", value: selected.contact_id || "-" },
          { label: "Timestamp", value: timeText(selected.event_ts) },
        ]);
      });

      if (events[0]) {
        const firstRow = opsEventRows.querySelector('tr[data-row-index="0"]');
        if (firstRow) firstRow.classList.add("is-selected");
        renderDetailGrid("opsEventDetailGrid", [
          { label: "Event", value: labelize(events[0].event_name) },
          { label: "Status", value: events[0].processing_status || "-" },
          { label: "Severity", value: severityLevelForEvent(events[0]) },
          { label: "Error Code", value: events[0].error_code || "-" },
          { label: "Contact", value: events[0].contact_id || "-" },
          { label: "Timestamp", value: timeText(events[0].event_ts) },
        ]);
      }
    }

    const dlqRows = qs("dlqRows");
    if (dlqRows) {
      dlqRows.innerHTML = dlq
        .map((row, index) => `<tr data-row-index="${index}"><td>${escapeHtml(row.id)}</td><td>${escapeHtml(row.workflow_name)}</td><td>${escapeHtml(row.step_name)}</td><td>${escapeHtml(row.error_summary)}</td><td>${escapeHtml(row.retry_count)}</td><td>${renderSeverityBadge(severityLevelForDlq(row))} ${escapeHtml(row.status)}</td><td><button data-replay-id="${row.id}" ${row.status !== "open" ? "disabled" : ""}>Replay</button></td></tr>`)
        .join("");

      dlqRows.querySelectorAll("button[data-replay-id]").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          replayDlq(button.dataset.replayId, button);
        });
      });

      bindSelectableRows(dlqRows, dlq, (selected) => {
        renderDetailGrid("dlqDetailGrid", [
          { label: "DLQ ID", value: selected.id },
          { label: "Workflow", value: selected.workflow_name || "-" },
          { label: "Step", value: selected.step_name || "-" },
          { label: "Severity", value: severityLevelForDlq(selected) },
          { label: "Retry Count", value: selected.retry_count || 0 },
          { label: "Status", value: selected.status || "-" },
          { label: "Error Summary", value: selected.error_summary || "-" },
          { label: "Resolved At", value: timeText(selected.resolved_at) },
          { label: "Resolved Reason", value: selected.resolved_reason || "-" },
        ]);
      });

      if (dlq[0]) {
        const firstRow = dlqRows.querySelector('tr[data-row-index="0"]');
        if (firstRow) firstRow.classList.add("is-selected");
        renderDetailGrid("dlqDetailGrid", [
          { label: "DLQ ID", value: dlq[0].id },
          { label: "Workflow", value: dlq[0].workflow_name || "-" },
          { label: "Step", value: dlq[0].step_name || "-" },
          { label: "Severity", value: severityLevelForDlq(dlq[0]) },
          { label: "Retry Count", value: dlq[0].retry_count || 0 },
          { label: "Status", value: dlq[0].status || "-" },
          { label: "Error Summary", value: dlq[0].error_summary || "-" },
          { label: "Resolved At", value: timeText(dlq[0].resolved_at) },
          { label: "Resolved Reason", value: dlq[0].resolved_reason || "-" },
        ]);
      }
    }

    setText("opsFeedback", dlq.some((row) => row.status === "open")
      ? "Open DLQ가 남아 있습니다. error summary와 retry count를 기준으로 우선순위를 판단하세요."
      : "현재 open DLQ는 없습니다. 최근 실패 이벤트만 모니터링하면 됩니다.");
  }

  function bindPageActions() {
    document.querySelectorAll("[data-progress-event]").forEach((button) => {
      button.dataset.seedEvent = button.dataset.progressEvent;
    });

    bindSeedButtons();

    const contactSearchBtn = qs("contactSearchBtn");
    if (contactSearchBtn) contactSearchBtn.addEventListener("click", renderContacts);

    const leadCreateBtn = qs("leadCreateBtn");
    if (leadCreateBtn) leadCreateBtn.addEventListener("click", createLeadFromContacts);

    const journeyRefreshBtn = qs("journeyRefreshBtn");
    if (journeyRefreshBtn) journeyRefreshBtn.addEventListener("click", renderJourneys);

    const journeyStateFilter = qs("journeyStateFilter");
    if (journeyStateFilter) journeyStateFilter.addEventListener("change", renderJourneys);
  }

  async function start() {
    bindPageActions();
    try {
      if (page === "hub") await renderHub();
      if (page === "contacts") await renderContacts();
      if (page === "journeys") await renderJourneys();
      if (page === "ops") await renderOps();
    } catch (error) {
      console.error(error);
      if (page === "hub") setText("todayFocus", `화면 초기화 실패: ${error.message}`);
      if (page === "contacts") setText("contactsFeedback", `화면 초기화 실패: ${error.message}`);
      if (page === "journeys") setText("journeyActionHint", `화면 초기화 실패: ${error.message}`);
      if (page === "ops") setText("opsFeedback", `화면 초기화 실패: ${error.message}`);
    }
  }

  start();
})();
