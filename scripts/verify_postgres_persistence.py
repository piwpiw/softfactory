#!/usr/bin/env python3
"""Verify persistent API-backed data survives a fresh session."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, timedelta


def _request(base_url: str, path: str, *, method: str = "GET", token: str | None = None, payload: dict | None = None):
    url = base_url.rstrip("/") + path
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        parsed = None
        if body:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body}
        return exc.code, parsed


def _assert(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def _login(base_url: str, email: str, password: str) -> str:
    status, payload = _request(
        base_url,
        "/api/auth/login",
        method="POST",
        payload={"email": email, "password": password},
    )
    _assert(status == 200, f"login failed: {status} {payload}")
    token = (payload or {}).get("access_token")
    _assert(bool(token), "login succeeded without access_token")
    return token


def _load_health(base_url: str):
    for path in ("/health", "/api/health", "/api/metrics/health"):
        status, payload = _request(base_url, path)
        if status == 200:
            return path, payload
    raise AssertionError("health endpoint unavailable at /health, /api/health, and /api/metrics/health")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify PostgreSQL-backed persistence across core services.")
    parser.add_argument("--base-url", default="http://localhost:9000")
    parser.add_argument("--email", default="demo@softfactory.com")
    parser.add_argument("--password", default="demo123")
    parser.add_argument("--require-postgres", action="store_true")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    run_id = uuid.uuid4().hex[:10]

    health_path, health_payload = _load_health(base_url)
    database_backend = (health_payload or {}).get("database_backend")
    if args.require_postgres:
        _assert(database_backend == "postgresql", f"expected PostgreSQL backend, got {database_backend!r}")

    token = _login(base_url, args.email, args.password)

    cardnews_name = f"PG Verify Template {run_id}"
    status, payload = _request(
        base_url,
        "/api/instagram-cardnews/templates",
        method="POST",
        token=token,
        payload={
            "name": cardnews_name,
            "tone": "balanced",
            "description": "PostgreSQL persistence verification template",
            "slides": 6,
            "structure": ["Hook", "Problem", "Insight", "Proof", "CTA", "Wrap"],
            "tags": ["verification", run_id],
        },
    )
    _assert(status == 201, f"cardnews template create failed: {status} {payload}")
    cardnews_template_id = payload["id"]

    sns_account_name = f"verify_{run_id}"
    status, payload = _request(
        base_url,
        "/api/sns/accounts",
        method="POST",
        token=token,
        payload={"platform": "instagram", "account_name": sns_account_name},
    )
    _assert(status == 201, f"sns account create failed: {status} {payload}")
    sns_account_id = payload["id"]

    status, payload = _request(
        base_url,
        "/api/ai-automation/employees",
        method="POST",
        token=token,
        payload={
            "name": f"Verifier {run_id}",
            "scenario_type": "social",
            "description": "Persistence verification employee",
        },
    )
    _assert(status == 201, f"ai employee create failed: {status} {payload}")
    ai_employee_id = payload["employee"]["id"]

    status, payload = _request(base_url, "/api/coocook/chefs", token=token)
    _assert(status == 200, f"coocook chef list failed: {status} {payload}")
    chefs = (payload or {}).get("chefs", [])
    _assert(bool(chefs), "no public coocook chefs available for persistence verification")
    chef_id = chefs[0]["id"]

    queue_key = f"verify-approval-{run_id}"
    status, payload = _request(
        base_url,
        "/api/platform/approval-queue",
        method="POST",
        token=token,
        payload={
            "id": queue_key,
            "service": "instagram-cardnews",
            "title": f"Persistence approval {run_id}",
            "status": "queued",
            "summary": "Approval queue persistence verification",
            "channels": ["instagram"],
            "accountIds": [sns_account_id],
            "metadata": {"runId": run_id},
        },
    )
    _assert(status == 200, f"approval queue upsert failed: {status} {payload}")

    second_token = _login(base_url, args.email, args.password)

    status, payload = _request(base_url, "/api/instagram-cardnews/templates", token=second_token)
    _assert(status == 200, f"cardnews template list failed: {status} {payload}")
    _assert(any(item.get("id") == cardnews_template_id for item in payload), "cardnews template missing after re-login")

    status, payload = _request(base_url, "/api/sns/accounts", token=second_token)
    _assert(status == 200, f"sns accounts list failed: {status} {payload}")
    _assert(any(item.get("id") == sns_account_id for item in payload), "sns account missing after re-login")

    status, payload = _request(base_url, "/api/ai-automation/employees", token=second_token)
    _assert(status == 200, f"ai employees list failed: {status} {payload}")
    _assert(any(item.get("id") == ai_employee_id for item in payload), "ai employee missing after re-login")

    status, payload = _request(base_url, "/api/platform/approval-queue", token=second_token)
    _assert(status == 200, f"approval queue list failed: {status} {payload}")
    items = (payload or {}).get("items", [])
    _assert(any(item.get("id") == queue_key for item in items), "approval queue item missing after re-login")

    booking_date = (date.today() + timedelta(days=7)).isoformat()
    status, payload = _request(
        base_url,
        "/api/coocook/bookings",
        method="POST",
        token=second_token,
        payload={
            "chef_id": chef_id,
            "booking_date": booking_date,
            "duration_hours": 2,
            "special_requests": f"verification-{run_id}",
        },
    )
    _assert(status == 201, f"coocook booking create failed: {status} {payload}")
    booking_id = payload["id"]

    status, payload = _request(base_url, f"/api/coocook/bookings/{booking_id}", token=second_token)
    _assert(status == 200, f"coocook booking detail failed: {status} {payload}")

    status, payload = _request(base_url, "/api/coocook/bookings", token=second_token)
    _assert(status == 200, f"coocook bookings list failed: {status} {payload}")
    _assert(any(item.get("id") == booking_id for item in payload), "coocook booking missing after re-login")

    summary = {
        "base_url": base_url,
        "health_path": health_path,
        "database_backend": database_backend,
        "verified": {
            "instagram_cardnews_template_id": cardnews_template_id,
            "sns_account_id": sns_account_id,
            "ai_employee_id": ai_employee_id,
            "coocook_chef_id": chef_id,
            "coocook_booking_id": booking_id,
            "approval_queue_key": queue_key,
        },
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
