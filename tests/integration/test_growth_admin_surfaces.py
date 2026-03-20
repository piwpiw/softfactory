import os


def test_growth_admin_contact_upsert_and_summary(client, auth_headers):
    create = client.post(
        "/api/v1/growth/contacts/upsert",
        headers=auth_headers,
        json={
            "email": "growth-admin@example.com",
            "phone": "+821012341234",
            "status": "active",
            "lifecycle_stage": "lead",
            "locale": "ko-KR",
            "timezone": "Asia/Seoul",
            "consents": [
                {
                    "channel": "email",
                    "policy_version": "v2026.03",
                    "opt_in": True,
                    "source": "growth-admin-smoke",
                }
            ],
        },
    )
    assert create.status_code == 200
    create_body = create.get_json()
    assert create_body["status"] == "created"
    assert create_body["contact_id"]

    contacts = client.get("/api/v1/growth/contacts?q=growth-admin", headers=auth_headers)
    assert contacts.status_code == 200
    contact_body = contacts.get_json()
    assert contact_body["total"] == 1
    assert contact_body["items"][0]["email"] == "growth-admin@example.com"
    assert contact_body["items"][0]["lifecycle_stage"] == "lead"

    summary = client.get("/api/v1/growth/dashboard/summary", headers=auth_headers)
    assert summary.status_code == 200
    summary_body = summary.get_json()
    assert summary_body["contacts"]["total"] == 1
    assert summary_body["contacts"]["lifecycle_counts"]["lead"] == 1


def test_growth_admin_replay_recovers_failed_event_and_dlq(client, auth_headers):
    os.environ["GROWTH_QUEUE_TOKEN"] = "queue-token"
    try:
        ingest = client.post(
            "/api/v1/events",
            json={
                "event_id": "evt-growth-admin-replay",
                "event_name": "payment_failed",
                "identity": {"email": "growth-replay@example.com"},
            },
        )
        assert ingest.status_code in (200, 201)

        fail = client.post(
            "/api/v1/growth/queue/fail",
            headers={"X-Queue-Token": "queue-token"},
            json={
                "event_id": "evt-growth-admin-replay",
                "workflow_name": "Growth Recovery",
                "step": "send_message",
                "error": "provider timeout",
                "workflow_run_id": "run-growth-admin-replay",
            },
        )
        assert fail.status_code == 200
        dlq_id = fail.get_json()["dlq_id"]

        dlq_before = client.get("/api/v1/growth/dlq?status=open", headers=auth_headers)
        assert dlq_before.status_code == 200
        before_items = dlq_before.get_json()["items"]
        assert any(item["id"] == dlq_id for item in before_items)

        replay = client.post(
            f"/api/v1/growth/dlq/{dlq_id}/replay",
            headers=auth_headers,
            json={"reason": "admin smoke replay"},
        )
        assert replay.status_code == 200
        replay_body = replay.get_json()
        assert replay_body["replayed"] is True
        assert replay_body["status"] == "resolved"

        events = client.get("/api/v1/growth/events?event_name=payment_failed", headers=auth_headers)
        assert events.status_code == 200
        event_items = events.get_json()["items"]
        matched_event = next(item for item in event_items if item["event_id"] == "evt-growth-admin-replay")
        assert matched_event["processing_status"] == "pending"

        dlq_after = client.get("/api/v1/growth/dlq", headers=auth_headers)
        assert dlq_after.status_code == 200
        after_items = dlq_after.get_json()["items"]
        matched_dlq = next(item for item in after_items if item["id"] == dlq_id)
        assert matched_dlq["status"] == "resolved"
        assert matched_dlq["resolved_reason"] == "admin smoke replay"
    finally:
        os.environ.pop("GROWTH_QUEUE_TOKEN", None)


def test_growth_admin_endpoints_require_auth(client):
    protected_endpoints = [
        "/api/v1/growth/dashboard/summary",
        "/api/v1/growth/contacts",
        "/api/v1/growth/events",
        "/api/v1/growth/journeys",
        "/api/v1/growth/dlq",
    ]

    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
