#!/usr/bin/env python3
"""Fast browser audit for UI-first delivery cycles."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_BASE_URL = "https://softfactory-platform.vercel.app"
DEFAULT_DEMO_PASSKEY = "demo2026"
OUTPUT_ROOT = Path(".workspace") / "reports" / "playwright"

PUBLIC_PAGES = (
    ("home", "/"),
    ("coocook-home", "/coocook/"),
    ("coocook-explore", "/coocook/explore.html"),
    ("coocook-recipes", "/coocook/recipes.html"),
    ("coocook-feed", "/coocook/feed.html"),
    ("coocook-shopping-list", "/coocook/shopping-list.html"),
)

PROTECTED_PAGES = (
    ("platform-dashboard", "/platform/dashboard.html"),
    ("sns-auto-create", "/sns-auto/create.html"),
    ("ai-automation", "/ai-automation/index.html"),
    ("instagram-cardnews", "/instagram-cardnews/index.html"),
)


@dataclass
class PageAudit:
    name: str
    path: str
    visibility: str
    requested_url: str
    final_url: str = ""
    title: str = ""
    status: str = "pending"
    http_status: int | None = None
    duration_ms: int = 0
    screenshot: str = ""
    console_errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def normalize_base(base_url: str) -> str:
    return base_url.rstrip("/")


def build_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"ui-sprint-audit-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def attach_console_capture(page, bucket: list[str]) -> None:
    page.on(
        "console",
        lambda msg: bucket.append(f"{msg.type}: {msg.text}") if msg.type in {"error", "warning"} else None,
    )
    page.on("pageerror", lambda exc: bucket.append(f"pageerror: {exc}"))


def screenshot_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-._" else "-" for ch in name) or "page"


def same_path(actual: str, expected: str) -> bool:
    return actual.rstrip("/") == expected.rstrip("/")


def login_demo(page, base_url: str, passkey: str, timeout_ms: int) -> tuple[bool, list[str]]:
    notes: list[str] = []
    response = page.goto(f"{base_url}/platform/login.html", wait_until="domcontentloaded", timeout=timeout_ms)
    if response is not None:
        notes.append(f"login-http:{response.status}")
    page.wait_for_load_state("networkidle", timeout=timeout_ms)
    page.locator("#tab-demo").click(timeout=timeout_ms)
    page.locator("#passkey").fill(passkey, timeout=timeout_ms)
    page.locator("#demoForm").evaluate("(form) => form.requestSubmit()")
    page.wait_for_url("**/platform/**", timeout=timeout_ms)
    return "/platform/" in page.url, notes


def audit_page(page, *, base_url: str, name: str, path: str, visibility: str, output_dir: Path, timeout_ms: int) -> PageAudit:
    requested_url = f"{base_url}{path}"
    audit = PageAudit(name=name, path=path, visibility=visibility, requested_url=requested_url)
    started = datetime.now(timezone.utc)
    console_errors: list[str] = []
    attach_console_capture(page, console_errors)

    try:
        response = page.goto(requested_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
        audit.final_url = page.url
        audit.http_status = response.status if response is not None else None
        audit.title = page.title()
        final_path = "/" + page.url.split(base_url, 1)[-1].lstrip("/") if page.url.startswith(base_url) else page.url

        if audit.http_status and audit.http_status >= 400:
            audit.status = "http-error"
            audit.notes.append(f"http:{audit.http_status}")
        elif visibility == "public" and not same_path(final_path, path):
            audit.status = "route-drift"
            audit.notes.append(f"final-path:{final_path}")
        elif "/platform/login.html" in page.url and visibility == "protected":
            audit.status = "auth-redirect"
            audit.notes.append("redirected-to-login")
        else:
            audit.status = "ok"
    except PlaywrightTimeoutError as exc:
        audit.status = "timeout"
        audit.final_url = page.url
        audit.notes.append(f"timeout:{exc}")
    except PlaywrightError as exc:
        audit.status = "fail"
        audit.final_url = page.url
        audit.notes.append(str(exc))
    finally:
        audit.console_errors.extend(console_errors)
        screenshot_path = output_dir / f"{screenshot_name(name)}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            audit.screenshot = str(screenshot_path).replace("\\", "/")
        except PlaywrightError as exc:
            audit.notes.append(f"screenshot-failed:{exc}")
        audit.duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return audit


def run(base_url: str, passkey: str, headless: bool, timeout_ms: int) -> int:
    base_url = normalize_base(base_url)
    output_dir = build_output_dir()
    report: dict[str, object] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "output_dir": str(output_dir).replace("\\", "/"),
        "policy": "ui-first",
        "pages": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page_results: list[PageAudit] = []

        for name, path in PUBLIC_PAGES:
            page = context.new_page()
            page_results.append(
                audit_page(page, base_url=base_url, name=name, path=path, visibility="public", output_dir=output_dir, timeout_ms=timeout_ms)
            )
            page.close()

        protected_page = context.new_page()
        login_ok, login_notes = login_demo(protected_page, base_url, passkey, timeout_ms)
        report["login"] = {"status": "ok" if login_ok else "fail", "notes": login_notes, "final_url": protected_page.url}

        if login_ok:
            for name, path in PROTECTED_PAGES:
                page = context.new_page()
                page_results.append(
                    audit_page(page, base_url=base_url, name=name, path=path, visibility="protected", output_dir=output_dir, timeout_ms=timeout_ms)
                )
                page.close()
        else:
            for name, path in PROTECTED_PAGES:
                page_results.append(
                    PageAudit(
                        name=name,
                        path=path,
                        visibility="protected",
                        requested_url=f"{base_url}{path}",
                        status="login-failed",
                        notes=["protected-pages-skipped"],
                    )
                )

        protected_page.close()
        browser.close()

    failures = [item for item in page_results if item.status != "ok"]
    report["pages"] = [asdict(item) for item in page_results]
    report["summary"] = {
        "total_pages": len(page_results),
        "failed_pages": len(failures),
        "ok_pages": len(page_results) - len(failures),
        "public_pages": len(PUBLIC_PAGES),
        "protected_pages": len(PROTECTED_PAGES),
    }
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "ok" if not failures else "partial"
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"UI_SCREEN_SPRINT_AUDIT status={report['status']} failed={len(failures)} report={report_path}")
    return 0 if not failures else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fast UI-first browser audit against key public and protected pages.")
    parser.add_argument("--base", default=DEFAULT_BASE_URL, help="Base URL to audit.")
    parser.add_argument("--passkey", default=DEFAULT_DEMO_PASSKEY, help="Demo passkey for protected pages.")
    parser.add_argument("--headless", default="true", choices=("true", "false"), help="Run Chromium headless.")
    parser.add_argument("--timeout", type=int, default=20000, help="Per-page timeout in milliseconds.")
    args = parser.parse_args()

    raise SystemExit(
        run(
            base_url=args.base,
            passkey=args.passkey,
            headless=args.headless.lower() == "true",
            timeout_ms=args.timeout,
        )
    )


if __name__ == "__main__":
    main()
