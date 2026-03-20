#!/usr/bin/env python3
"""Verify the Instagram Cardnews page against the real local backend."""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


OUTPUT_ROOT = Path(".workspace") / "reports" / "playwright"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def build_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"cardnews-real-flow-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ensure_demo_account(base_url: str) -> dict:
    headers = {"Authorization": "Bearer demo_token"}
    payload = {"platform": "instagram", "account_name": "softfactory_live"}
    response = requests.post(f"{base_url}/api/sns/accounts", json=payload, headers=headers, timeout=10)
    if response.status_code not in (201, 400):
        raise RuntimeError(f"SNS account setup failed: {response.status_code} {response.text}")
    accounts = requests.get(f"{base_url}/api/instagram-cardnews/accounts", headers=headers, timeout=10)
    accounts.raise_for_status()
    data = accounts.json()
    if not data:
        raise RuntimeError("No Instagram cardnews accounts available after SNS account setup.")
    return {"account_count": len(data), "first_account": data[0]}


class LocalServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        os.environ.setdefault("TESTING", "true")
        db_path = (OUTPUT_ROOT / "cardnews-real-flow.db").resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")
        os.environ.setdefault("JWT_SECRET", "test-secret-key")

        from backend.app import create_app
        from backend.models import init_db

        self.host = host
        self.port = port
        self.app = create_app()
        with self.app.app_context():
            init_db(self.app)
        self.server = make_server(host, port, self.app, threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)


def run(base_url: str, headless: bool) -> int:
    output_dir = build_output_dir()
    setup = ensure_demo_account(base_url)
    report: dict[str, object] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "setup": setup,
        "steps": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        context.add_init_script(
            """
            window.localStorage.setItem('access_token', 'demo_token');
            window.localStorage.setItem('refresh_token', 'demo_token');
            window.localStorage.setItem('user', JSON.stringify({
              id: 1,
              email: 'demo@softfactory.com',
              name: 'Demo User',
              role: 'user'
            }));
            """
        )
        page = context.new_page()

        def step(name: str, details: str) -> None:
            report["steps"].append({"name": name, "details": details, "at": datetime.now(timezone.utc).isoformat()})

        page.goto(f"{base_url}/web/instagram-cardnews/index.html", wait_until="networkidle", timeout=20000)
        page.wait_for_function(
            "() => document.querySelectorAll('.account-check').length > 0",
            timeout=20000,
        )
        step("open_page", page.url)

        page.locator('[data-workspace-stage=\"publish\"]').click()
        page.locator("#templateNewBtn").click()
        page.locator("#templateName").fill("Real Flow Template")
        page.locator("#templateDesc").fill("Template created in a real browser flow.")
        page.locator("#templateSaveBtn").click()
        page.wait_for_function(
            "() => document.querySelector('#headerStatus')?.textContent?.includes('템플릿')",
            timeout=10000,
        )
        step("save_template", page.locator("#headerStatus").text_content() or "")

        page.locator("#topicInput").fill("Real launch flow")
        page.locator("#keywordsInput").fill("launch, proof, offer")
        page.locator("#slideCountInput").fill("4")
        page.locator("#generateBtn").click()
        page.wait_for_function(
            "() => document.querySelector('#statusText')?.textContent?.includes('생성 완료')",
            timeout=10000,
        )
        step("generate", page.locator("#statusText").text_content() or "")

        page.locator("#publishBtn").click()
        page.wait_for_function(
            "() => document.querySelector('#projectsWrap')?.textContent?.includes('Real launch flow')",
            timeout=10000,
        )
        header_status = page.locator("#headerStatus").text_content() or ""
        status_text = page.locator("#statusText").text_content() or ""
        projects_text = page.locator("#projectsWrap").text_content() or ""
        step("publish", header_status)

        screenshot_path = output_dir / "cardnews-real-flow.png"
        page.screenshot(path=str(screenshot_path), full_page=True)

        report.update({
            "status": "ok",
            "header_status": header_status,
            "status_text": status_text,
            "projects_contains_topic": "Real launch flow" in projects_text,
            "screenshot": str(screenshot_path).replace("\\", "/"),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        browser.close()

    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CARDNEWS_REAL_FLOW status=ok report={report_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Instagram Cardnews against the real backend.")
    parser.add_argument("--base", default="")
    parser.add_argument("--headless", default="true", choices=("true", "false"))
    args = parser.parse_args()
    if args.base:
        raise SystemExit(run(args.base.rstrip("/"), args.headless.lower() == "true"))

    server = LocalServer()
    server.start()
    try:
        raise SystemExit(run(server.base_url, args.headless.lower() == "true"))
    finally:
        server.stop()


if __name__ == "__main__":
    main()
