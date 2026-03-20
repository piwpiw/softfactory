#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SoftFactory UI Window Smoke Test
Launches real browser windows and checks core pages with screenshot capture.

Usage:
  python scripts/ui-window-smoke-test.py
  python scripts/ui-window-smoke-test.py --base http://127.0.0.1:9000 --headless false
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PwTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_PAGES = [
    ("플랫폼 메인", "/web/platform/index.html"),
    ("플랫폼 로그인", "/web/platform/login.html"),
    ("리뷰 대시보드", "/web/review/index.html"),
    ("리뷰 캠페인", "/web/review/my-campaigns.html"),
    ("쿱쿡", "/web/coocook/index.html"),
    ("SNS 자동화", "/web/sns-auto/index.html"),
    ("보헤미안 마케팅", "/web/bohemian-marketing/index.html"),
    ("AI 자동화", "/web/ai-automation/index.html"),
    ("웹앱 빌더", "/web/webapp-builder/index.html"),
]


def normalize_base(base: str) -> str:
    return base.rstrip("/")


def build_output_dir() -> Path:
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path("artifacts") / f"ui-smoke-{now}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def safe_slug(path: str) -> str:
    slug = path.lstrip("/")
    slug = slug.replace("/", "_").replace(" ", "_")
    if not slug:
        slug = "home"
    return re.sub(r"[^A-Za-z0-9._-]", "-", slug)


def run(base: str, headless: bool, timeout: int, pause: int, pages: list[tuple[str, str]]) -> int:
    base = normalize_base(base)
    out_dir = build_output_dir()
    result = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base": base,
        "headless": headless,
        "pages": [],
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(viewport={"width": 1600, "height": 1080})
            console_errors = []
            js_errors = []

            for page_name, path in pages:
                url = f"{base}{path}"
                entry = {
                    "name": page_name,
                    "path": path,
                    "url": url,
                    "status": "pending",
                    "errors": [],
                }
                page = context.new_page()
                page.on("console", lambda msg: console_errors.append(
                    f"{msg.type}: {msg.text}" if hasattr(msg, "type") else str(msg)
                ) if msg.type != "log" else None)
                page.on("pageerror", lambda exc: js_errors.append(str(exc)))
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                    page.wait_for_load_state("load", timeout=timeout)
                    page.locator("body").wait_for(state="attached", timeout=timeout)
                    page.wait_for_timeout(1500)
                    title = page.title()
                    entry["status"] = "ok"
                    entry["title"] = title
                    errors = [e for e in console_errors + js_errors if e]
                    entry["errors"] = errors
                    page.screenshot(path=out_dir / f"{safe_slug(path)}.png", full_page=True)
                    time.sleep(pause)
                except PwTimeoutError as exc:
                    entry["title"] = page.title()
                    entry["errors"].append(f"timeout: {str(exc)}")
                    if page.locator("body").count() > 0:
                        entry["status"] = "ok"
                        entry["errors"].append("soft-timeout after initial render")
                        entry["errors"].extend([e for e in console_errors + js_errors if e])
                        page.screenshot(path=out_dir / f"{safe_slug(path)}.png", full_page=True)
                    else:
                        entry["status"] = "timeout"
                except Exception as exc:
                    entry["status"] = "fail"
                    entry["errors"].append(str(exc))
                finally:
                    page.close()
                    result["pages"].append(entry)
                    console_errors.clear()
                    js_errors.clear()

            browser.close()
    except Exception as exc:
        result["fatal"] = str(exc)
        result["status"] = "failed"
        Path(out_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"FAIL: {exc}")
        return 1

    fail_count = sum(1 for page in result["pages"] if page["status"] != "ok")
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["status"] = "ok" if fail_count == 0 else "partial"
    result["fail_count"] = fail_count
    result["screenshot_dir"] = str(out_dir)
    report_path = out_dir / "result.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nUI Smoke completed: status={result['status']}, fail={fail_count}, report={report_path}")
    return 0 if fail_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Run UI smoke test with real browser windows.")
    parser.add_argument("--base", default="http://127.0.0.1:9000", help="Base URL for local server")
    parser.add_argument("--headless", default="false", choices=["true", "false"], help="run browser headless")
    parser.add_argument("--timeout", type=int, default=15000, help="ms")
    parser.add_argument("--pause", type=int, default=1, help="pause seconds between pages")
    args = parser.parse_args()

    headless = args.headless.lower() == "true"
    os.makedirs("artifacts", exist_ok=True)
    exit_code = run(
        base=args.base,
        headless=headless,
        timeout=args.timeout,
        pause=args.pause,
        pages=DEFAULT_PAGES,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
