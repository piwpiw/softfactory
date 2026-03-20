import os


def test_event_ingest_accepts_and_deduplicates(client):
    payload = {
        "event_id": "evt-growth-1",
        "event_name": "signup_completed",
        "ts": "2026-03-06T10:00:00Z",
        "identity": {"email": "growth-user@example.com", "anonymous_id": "aid-1"},
        "context": {"utm": {"source": "ad"}},
        "props": {"plan": "free"},
    }

    first = client.post("/api/v1/events", json=payload)
    assert first.status_code in (200, 201)
    body = first.get_json()
    assert body["accepted"] is True
    assert body["duplicate"] is False

    second = client.post("/api/v1/events", json=payload)
    assert second.status_code == 200
    body2 = second.get_json()
    assert body2["accepted"] is True
    assert body2["duplicate"] is True


def test_event_ingest_rejects_missing_event_name(client):
    res = client.post("/api/v1/events", json={"event_id": "evt-growth-2"})
    assert res.status_code == 400


def test_event_ingest_token_optional_auth(client):
    os.environ["EVENT_INGEST_TOKEN"] = "evt-token"
    try:
        denied = client.post("/api/v1/events", json={"event_name": "lead_captured"})
        assert denied.status_code == 401

        ok = client.post(
            "/api/v1/events",
            headers={"X-Event-Token": "evt-token"},
            json={"event_name": "lead_captured", "event_id": "evt-growth-3"},
        )
        assert ok.status_code in (200, 201)
    finally:
        os.environ.pop("EVENT_INGEST_TOKEN", None)
