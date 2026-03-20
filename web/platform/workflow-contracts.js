(function () {
  function buildAutomationContract({
    topic,
    purpose,
    frequency,
    platforms,
    webhookUrl,
    engine,
    payloadVersion
  }) {
    const cleanTopic = String(topic || "").trim();
    const cleanPurpose = String(purpose || "engagement").trim();
    const cleanFrequency = String(frequency || "daily").trim();
    const cleanPlatforms = Array.isArray(platforms) ? platforms.filter(Boolean).map((item) => String(item).trim()).filter(Boolean) : [];
    const cleanWebhookUrl = String(webhookUrl || "").trim();
    const cleanEngine = String(engine || "direct").trim();

    return {
      name: `${cleanTopic || "Untitled"} · ${cleanPurpose} · ${cleanFrequency}`,
      topic: cleanTopic,
      purpose: cleanPurpose,
      frequency: cleanFrequency,
      platforms: cleanPlatforms,
      engine: cleanEngine,
      webhook_url: cleanWebhookUrl || null,
      delivery_mode: cleanWebhookUrl ? "webhook" : cleanEngine === "internal-queue" ? "queue" : "direct",
      payload_version: payloadVersion || "2026-03-10",
      requested_at: new Date().toISOString(),
    };
  }

  function buildApprovalQueueEntry({
    id,
    service,
    title,
    status,
    owner,
    approvalMode,
    approverRole,
    channels,
    accountIds,
    scheduledAt,
    sourceUrl,
    summary,
    contract,
    metadata
  }) {
    return {
      id: id || `${service}:${Date.now()}`,
      service: service || "unknown",
      title: title || "Untitled item",
      status: status || "queued",
      owner: owner || "system",
      approvalMode: approvalMode || "approve-before-publish",
      approverRole: approverRole || "admin",
      channels: Array.isArray(channels) ? channels : [],
      accountIds: Array.isArray(accountIds) ? accountIds : [],
      scheduledAt: scheduledAt || null,
      sourceUrl: sourceUrl || "",
      summary: summary || "",
      contract: contract || null,
      metadata: metadata || {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }

  window.SoftFactoryWorkflowContracts = {
    buildAutomationContract,
    buildApprovalQueueEntry
  };
})();
