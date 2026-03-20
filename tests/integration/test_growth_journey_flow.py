import os


def test_growth_queue_pending_ack_and_fail(client):
    os.environ["GROWTH_QUEUE_TOKEN"] = "queue-token"

    seed = client.post(
        "/api/v1/events",
        json={
            "event_id": "evt-queue-1",
            "event_name": "key_action_completed",
            "identity": {"email": "queue-user@example.com"},
        },
    )
    assert seed.status_code in (200, 201)

    pending = client.get("/api/v1/growth/queue/pending?limit=10", headers={"X-Queue-Token": "queue-token"})
    assert pending.status_code == 200
    payload = pending.get_json()
    assert "events" in payload
    assert any(e["event_id"] == "evt-queue-1" for e in payload["events"])

    ack = client.post(
        "/api/v1/growth/queue/ack",
        headers={"X-Queue-Token": "queue-token"},
        json={"event_id": "evt-queue-1", "workflow_run_id": "run-1"},
    )
    assert ack.status_code == 200

    seed2 = client.post(
        "/api/v1/events",
        json={
            "event_id": "evt-queue-2",
            "event_name": "payment_failed",
            "identity": {"email": "queue-user2@example.com"},
        },
    )
    assert seed2.status_code in (200, 201)

    fail = client.post(
        "/api/v1/growth/queue/fail",
        headers={"X-Queue-Token": "queue-token"},
        json={
            "event_id": "evt-queue-2",
            "workflow_name": "Growth 06 Churn Risk",
            "step": "send_message",
            "error": "provider timeout",
            "workflow_run_id": "run-2",
        },
    )
    assert fail.status_code == 200
    assert fail.get_json()["ok"] is True


def test_growth_queue_token_denied(client):
    os.environ["GROWTH_QUEUE_TOKEN"] = "queue-token"
    denied = client.get("/api/v1/growth/queue/pending?limit=1")
    assert denied.status_code == 401
