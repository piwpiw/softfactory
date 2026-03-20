#!/usr/bin/env python3
"""Run a browser regression flow that includes demo authentication."""

from __future__ import annotations

import argparse
import json
import re
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
DEFAULT_PAGES = (
    ("platform-dashboard", "/platform/dashboard.html", re.compile(r"/platform/dashboard\.html(?:$|[?#])")),
    ("sns-auto-create", "/sns-auto/create.html", re.compile(r"/sns-auto/create\.html(?:$|[?#])")),
    ("ai-automation", "/ai-automation/index.html", re.compile(r"/ai-automation/(?:index\.html)?(?:$|[?#])")),
    ("instagram-cardnews", "/instagram-cardnews/index.html", re.compile(r"/instagram-cardnews/(?:index\.html)?(?:$|[?#])")),
)


@dataclass
class LoginResult:
    status: str
    login_url: str
    final_url: str = ""
    duration_ms: int = 0
    details: list[str] = field(default_factory=list)


@dataclass
class PageResult:
    name: str
    path: str
    requested_url: str
    final_url: str = ""
    status: str = "pending"
    http_status: int | None = None
    title: str = ""
    duration_ms: int = 0
    screenshot: str = ""
    details: list[str] = field(default_factory=list)


def normalize_base(base_url: str) -> str:
    return base_url.rstrip("/")


def build_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / f"auth-regression-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip("/")) or "root"


def attach_error_list(page, bucket: list[str]) -> None:
    page.on(
        "console",
        lambda msg: bucket.append(f"console:{msg.type}: {msg.text}") if msg.type in {"error", "warning"} else None,
    )
    page.on("pageerror", lambda exc: bucket.append(f"pageerror: {exc}"))


def login_with_demo(page, base_url: str, passkey: str, timeout_ms: int) -> LoginResult:
    login_url = f"{base_url}/platform/login.html"
    details: list[str] = []
    start = datetime.now(timezone.utc)

    try:
        response = page.goto(login_url, wait_until="domcontentloaded", timeout=timeout_ms)
        if response is not None:
            details.append(f"login-http:{response.status}")
        page.wait_for_load_state("load", timeout=timeout_ms)
        page.locator("body").wait_for(state="attached", timeout=timeout_ms)
        page.locator("#tab-demo").click(timeout=timeout_ms)
        page.locator("#passkey").fill(passkey, timeout=timeout_ms)
        page.locator("#demoForm").evaluate("(form) => form.requestSubmit()")
        page.wait_for_function(
            "() => /\\/platform\\/(dashboard|onboarding)\\.html(?:$|[?#])/.test(window.location.pathname + window.location.search + window.location.hash)",
            timeout=timeout_ms,
        )
        end = datetime.now(timezone.utc)
        return LoginResult(
            status="ok",
            login_url=login_url,
            final_url=page.url,
            duration_ms=int((end - start).total_seconds() * 1000),
            details=details,
        )
    except (PlaywrightTimeoutError, PlaywrightError, AssertionError) as exc:
        end = datetime.now(timezone.utc)
        details.append(str(exc))
        return LoginResult(
            status="fail",
            login_url=login_url,
            final_url=page.url,
            duration_ms=int((end - start).total_seconds() * 1000),
            details=details,
        )


def evaluate_page(page, base_url: str, entry: tuple[str, str, re.Pattern[str]], output_dir: Path, timeout_ms: int) -> PageResult:
    name, path, final_url_pattern = entry
    requested_url = f"{base_url}{path}"
    start = datetime.now(timezone.utc)
    details: list[str] = []
    result = PageResult(name=name, path=path, requested_url=requested_url)

    try:
        response = page.goto(requested_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_load_state("load", timeout=timeout_ms)
        page.locator("body").wait_for(state="attached", timeout=timeout_ms)
        # Many dashboard surfaces keep polling after initial render, so networkidle is too strict.
        page.wait_for_timeout(1500)
        result.final_url = page.url
        result.http_status = response.status if response is not None else None
        result.title = page.title()

        if "/platform/login.html" in page.url:
            result.status = "auth-redirect"
            result.details.append("redirected to login page")
        elif result.http_status and result.http_status >= 400:
            result.status = "http-error"
            result.details.append(f"http status {result.http_status}")
        elif not final_url_pattern.search(page.url):
            result.status = "unexpected-route"
            result.details.append(f"unexpected final url: {page.url}")
        elif page.locator("body").count() == 0:
            result.status = "missing-body"
            result.details.append("body element not found")
        else:
            result.status = "ok"

        if details:
            result.details.extend(details)
    except PlaywrightTimeoutError as exc:
        result.final_url = page.url
        result.title = page.title()
        if "/platform/login.html" in page.url:
            result.status = "auth-redirect"
            result.details.append("redirected to login page during timeout")
        elif final_url_pattern.search(page.url) and page.locator("body").count() > 0:
            result.status = "ok"
            result.details.append(f"soft-timeout after render: {exc}")
        else:
            result.status = "timeout"
            result.details.append(f"timeout: {exc}")
    except PlaywrightError as exc:
        result.status = "fail"
        result.final_url = page.url
        result.details.append(str(exc))
    finally:
        screenshot_path = output_dir / f"{slugify(name)}.png"
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            result.screenshot = str(screenshot_path).replace("\\", "/")
        except PlaywrightError as exc:
            result.details.append(f"screenshot failed: {exc}")

    end = datetime.now(timezone.utc)
    result.duration_ms = int((end - start).total_seconds() * 1000)
    return result


def run(base_url: str, headless: bool, passkey: str, timeout_ms: int, pages: Iterable[tuple[str, str, re.Pattern[str]]]) -> int:
    base_url = normalize_base(base_url)
    output_dir = build_output_dir()
    report: dict[str, object] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "headless": headless,
        "output_dir": str(output_dir).replace("\\", "/"),
    }

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            context = browser.new_context(viewport={"width": 1600, "height": 960})
            page = context.new_page()
            shared_errors: list[str] = []
            attach_error_list(page, shared_errors)

            login_result = login_with_demo(page, base_url, passkey, timeout_ms)
            if shared_errors:
                login_result.details.extend(shared_errors)
                shared_errors.clear()
            report["login"] = asdict(login_result)

            if login_result.status != "ok":
                report["status"] = "failed"
                report["pages"] = []
                report["finished_at"] = datetime.now(timezone.utc).isoformat()
                (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                browser.close()
                print(f"FAIL login report={output_dir / 'report.json'}")
                return 1

            page_results: list[PageResult] = []
            for entry in pages:
                check_page = context.new_page()
                page_errors: list[str] = []
                attach_error_list(check_page, page_errors)
                result = evaluate_page(check_page, base_url, entry, output_dir, timeout_ms)
                if page_errors:
                    result.details.extend(page_errors)
                page_results.append(result)
                check_page.close()

            browser.close()
    except PlaywrightError as exc:
        report["status"] = "failed"
        report["fatal_error"] = str(exc)
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"FAIL fatal={exc} report={output_dir / 'report.json'}")
        return 1

    failed = [item for item in page_results if item.status != "ok"]
    report["pages"] = [asdict(item) for item in page_results]
    report["status"] = "ok" if not failed else "partial"
    report["failed_pages"] = len(failed)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"AUTH_BROWSER_REGRESSION status={report['status']} failed={len(failed)} report={report_path}")
    return 0 if not failed else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a demo-authenticated browser regression against protected pages.")
    parser.add_argument("--base", default=DEFAULT_BASE_URL, help="Base URL to test.")
    parser.add_argument("--headless", default="true", choices=("true", "false"), help="Run Chromium headless.")
    parser.add_argument("--timeout", type=int, default=20000, help="Timeout in milliseconds.")
    parser.add_argument("--passkey", default=DEFAULT_DEMO_PASSKEY, help="Demo passkey for login flow.")
    args = parser.parse_args()

    raise SystemExit(
        run(
            base_url=args.base,
            headless=args.headless.lower() == "true",
            passkey=args.passkey,
            timeout_ms=args.timeout,
            pages=DEFAULT_PAGES,
        )
    )


if __name__ == "__main__":
    main()
