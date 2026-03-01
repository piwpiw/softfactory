#!/usr/bin/env python3
"""SoftFactory Integration Verification Script

Starts the Flask application, tests every API endpoint with demo credentials,
and generates a pass/fail report.

Usage:
    python scripts/verify_integration.py [--port 8000] [--report-file report.json]
"""

import sys
import os
import json
import time
import signal
import argparse
import subprocess
import threading
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PORT = 8000
DEMO_TOKEN = "demo_token"
BASE_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEMO_TOKEN}",
}
NO_AUTH_HEADERS = {"Content-Type": "application/json"}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method, url, headers=None, body=None, expected_codes=None):
    """Execute an HTTP request and return (status_code, body_dict, error_msg)."""
    if expected_codes is None:
        expected_codes = [200, 201]
    if headers is None:
        headers = BASE_HEADERS

    req = Request(url, method=method, headers=headers)
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")

    try:
        resp = urlopen(req, timeout=10)
        status = resp.status
        raw = resp.read().decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"_raw": raw}
        passed = status in expected_codes
        return status, data, None if passed else f"Unexpected status {status}"
    except HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            data = json.loads(raw)
        except Exception:
            data = {"_raw": raw}
        passed = e.code in expected_codes
        return e.code, data, None if passed else f"HTTP {e.code}: {raw[:200]}"
    except URLError as e:
        return 0, {}, f"Connection error: {e.reason}"
    except Exception as e:
        return 0, {}, f"Error: {str(e)}"

def get(url, headers=None, expected=None):
    return _request("GET", url, headers, expected_codes=expected)

def post(url, body=None, headers=None, expected=None):
    return _request("POST", url, headers, body, expected_codes=expected)

def put(url, body=None, headers=None, expected=None):
    return _request("PUT", url, headers, body, expected_codes=expected)

def delete(url, headers=None, expected=None):
    return _request("DELETE", url, headers, expected_codes=expected)

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, name, method, url, status, passed, error=None):
        self.name = name
        self.method = method
        self.url = url
        self.status = status
        self.passed = passed
        self.error = error

    def to_dict(self):
        return {
            "name": self.name,
            "method": self.method,
            "url": self.url,
            "status": self.status,
            "passed": self.passed,
            "error": self.error,
        }


def run_tests(base_url):
    """Run all integration tests and return a list of TestResult."""
    results = []

    def record(name, method, path, status, passed, error=None):
        results.append(TestResult(name, method, path, status, passed, error))

    # ====================== HEALTH ======================
    s, d, e = get(f"{base_url}/health")
    record("Health Check", "GET", "/health", s, e is None, e)

    # ====================== AUTH ======================
    # Register (may fail if user exists — accept 400 as non-critical)
    s, d, e = post(f"{base_url}/api/auth/register",
                    {"email": "integration_test@example.com", "password": "test123456", "name": "Integration Test"},
                    headers=NO_AUTH_HEADERS, expected=[201, 400])
    record("Auth: Register", "POST", "/api/auth/register", s, e is None, e)

    # Login
    s, d, e = post(f"{base_url}/api/auth/login",
                    {"email": "admin@softfactory.com", "password": "admin123"},
                    headers=NO_AUTH_HEADERS, expected=[200, 401])
    record("Auth: Login", "POST", "/api/auth/login", s, e is None, e)

    # Me (demo token)
    s, d, e = get(f"{base_url}/api/auth/me")
    record("Auth: Get Me", "GET", "/api/auth/me", s, e is None, e)

    # Refresh (intentionally invalid — expect 400/401)
    s, d, e = post(f"{base_url}/api/auth/refresh",
                    {"refresh_token": "invalid"},
                    headers=NO_AUTH_HEADERS, expected=[400, 401])
    record("Auth: Refresh (invalid)", "POST", "/api/auth/refresh", s, e is None, e)

    # OAuth URL
    s, d, e = get(f"{base_url}/api/auth/oauth/google/url", headers=NO_AUTH_HEADERS)
    record("Auth: OAuth URL (Google)", "GET", "/api/auth/oauth/google/url", s, e is None, e)

    # ====================== PLATFORM ======================
    s, d, e = get(f"{base_url}/api/platform/products", headers=NO_AUTH_HEADERS)
    record("Platform: Products", "GET", "/api/platform/products", s, e is None, e)

    s, d, e = get(f"{base_url}/api/platform/dashboard")
    record("Platform: Dashboard", "GET", "/api/platform/dashboard", s, e is None, e)

    # ====================== PAYMENT ======================
    s, d, e = get(f"{base_url}/api/payment/plans", headers=NO_AUTH_HEADERS)
    record("Payment: Plans", "GET", "/api/payment/plans", s, e is None, e)

    s, d, e = get(f"{base_url}/api/payment/subscriptions")
    record("Payment: Subscriptions", "GET", "/api/payment/subscriptions", s, e is None, e)

    # Checkout (expect 400 in dev mode — Stripe not enabled)
    s, d, e = post(f"{base_url}/api/payment/checkout",
                    {"product_id": 1, "plan_type": "monthly"},
                    expected=[200, 400])
    record("Payment: Checkout (dev)", "POST", "/api/payment/checkout", s, e is None, e)

    # ====================== SNS AUTO ======================
    s, d, e = get(f"{base_url}/api/sns/templates")
    record("SNS: Templates", "GET", "/api/sns/templates", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/accounts")
    record("SNS: Accounts", "GET", "/api/sns/accounts", s, e is None, e)

    # Create account
    s, d, e = post(f"{base_url}/api/sns/accounts",
                    {"platform": "instagram", "account_name": "@integration_test"},
                    expected=[201, 400])
    record("SNS: Create Account", "POST", "/api/sns/accounts", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/posts")
    record("SNS: Posts", "GET", "/api/sns/posts", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/trending")
    record("SNS: Trending", "GET", "/api/sns/trending", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/linkinbio")
    record("SNS: Link-in-Bio List", "GET", "/api/sns/linkinbio", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/automate")
    record("SNS: Automation List", "GET", "/api/sns/automate", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/competitor")
    record("SNS: Competitors", "GET", "/api/sns/competitor", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/roi")
    record("SNS: ROI", "GET", "/api/sns/roi", s, e is None, e)

    s, d, e = get(f"{base_url}/api/sns/linkinbio/stats")
    record("SNS: Link-in-Bio Stats", "GET", "/api/sns/linkinbio/stats", s, e is None, e)

    # AI Generate
    s, d, e = post(f"{base_url}/api/sns/ai/generate",
                    {"topic": "test", "tone": "professional", "language": "en", "platform": "instagram"})
    record("SNS: AI Generate", "POST", "/api/sns/ai/generate", s, e is None, e)

    # AI Repurpose
    s, d, e = post(f"{base_url}/api/sns/ai/repurpose",
                    {"content": "Test content", "source_platform": "blog", "target_platforms": ["twitter"]})
    record("SNS: AI Repurpose", "POST", "/api/sns/ai/repurpose", s, e is None, e)

    # ====================== REVIEW ======================
    s, d, e = get(f"{base_url}/api/review/campaigns", headers=NO_AUTH_HEADERS)
    record("Review: Campaigns", "GET", "/api/review/campaigns", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/my-campaigns")
    record("Review: My Campaigns", "GET", "/api/review/my-campaigns", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/my-applications")
    record("Review: My Applications", "GET", "/api/review/my-applications", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/listings")
    record("Review: Listings", "GET", "/api/review/listings", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/bookmarks")
    record("Review: Bookmarks", "GET", "/api/review/bookmarks", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/accounts")
    record("Review: Accounts", "GET", "/api/review/accounts", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/applications")
    record("Review: Applications", "GET", "/api/review/applications", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/auto-rules")
    record("Review: Auto Rules", "GET", "/api/review/auto-rules", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/scraper/status")
    record("Review: Scraper Status", "GET", "/api/review/scraper/status", s, e is None, e)

    s, d, e = get(f"{base_url}/api/review/listings/search?q=test")
    record("Review: Search", "GET", "/api/review/listings/search?q=test", s, e is None, e)

    # ====================== COOCOOK ======================
    s, d, e = get(f"{base_url}/api/coocook/chefs", headers=NO_AUTH_HEADERS)
    record("CooCook: Chefs", "GET", "/api/coocook/chefs", s, e is None, e)

    s, d, e = get(f"{base_url}/api/coocook/bookings")
    record("CooCook: Bookings", "GET", "/api/coocook/bookings", s, e is None, e)

    # ====================== AI AUTOMATION ======================
    s, d, e = get(f"{base_url}/api/ai-automation/plans", headers=NO_AUTH_HEADERS)
    record("AI Automation: Plans", "GET", "/api/ai-automation/plans", s, e is None, e)

    s, d, e = get(f"{base_url}/api/ai-automation/scenarios", headers=NO_AUTH_HEADERS)
    record("AI Automation: Scenarios", "GET", "/api/ai-automation/scenarios", s, e is None, e)

    s, d, e = get(f"{base_url}/api/ai-automation/employees")
    record("AI Automation: Employees", "GET", "/api/ai-automation/employees", s, e is None, e)

    s, d, e = get(f"{base_url}/api/ai-automation/dashboard")
    record("AI Automation: Dashboard", "GET", "/api/ai-automation/dashboard", s, e is None, e)

    # ====================== WEBAPP BUILDER ======================
    s, d, e = get(f"{base_url}/api/webapp-builder/plans", headers=NO_AUTH_HEADERS)
    record("WebApp Builder: Plans", "GET", "/api/webapp-builder/plans", s, e is None, e)

    s, d, e = get(f"{base_url}/api/webapp-builder/courses", headers=NO_AUTH_HEADERS)
    record("WebApp Builder: Courses", "GET", "/api/webapp-builder/courses", s, e is None, e)

    s, d, e = get(f"{base_url}/api/webapp-builder/enrollments")
    record("WebApp Builder: Enrollments", "GET", "/api/webapp-builder/enrollments", s, e is None, e)

    s, d, e = get(f"{base_url}/api/webapp-builder/webapps")
    record("WebApp Builder: Webapps", "GET", "/api/webapp-builder/webapps", s, e is None, e)

    s, d, e = get(f"{base_url}/api/webapp-builder/dashboard")
    record("WebApp Builder: Dashboard", "GET", "/api/webapp-builder/dashboard", s, e is None, e)

    # ====================== DASHBOARD ======================
    s, d, e = get(f"{base_url}/api/dashboard/kpis")
    record("Dashboard: KPIs", "GET", "/api/dashboard/kpis", s, e is None, e)

    s, d, e = get(f"{base_url}/api/dashboard/charts")
    record("Dashboard: Charts", "GET", "/api/dashboard/charts", s, e is None, e)

    s, d, e = get(f"{base_url}/api/dashboard/summary")
    record("Dashboard: Summary", "GET", "/api/dashboard/summary", s, e is None, e)

    # ====================== ANALYTICS ======================
    s, d, e = get(f"{base_url}/api/analytics/advanced")
    record("Analytics: Advanced", "GET", "/api/analytics/advanced", s, e is None, e)

    s, d, e = get(f"{base_url}/api/analytics/cohort")
    record("Analytics: Cohort", "GET", "/api/analytics/cohort", s, e is None, e)

    s, d, e = get(f"{base_url}/api/analytics/funnel")
    record("Analytics: Funnel", "GET", "/api/analytics/funnel", s, e is None, e)

    s, d, e = get(f"{base_url}/api/analytics/service-metrics")
    record("Analytics: Service Metrics", "GET", "/api/analytics/service-metrics", s, e is None, e)

    s, d, e = get(f"{base_url}/api/analytics/trends")
    record("Analytics: Trends", "GET", "/api/analytics/trends", s, e is None, e)

    # ====================== PERFORMANCE ======================
    s, d, e = get(f"{base_url}/api/performance/roi")
    record("Performance: ROI", "GET", "/api/performance/roi", s, e is None, e)

    s, d, e = get(f"{base_url}/api/performance/product-roi")
    record("Performance: Product ROI", "GET", "/api/performance/product-roi", s, e is None, e)

    s, d, e = get(f"{base_url}/api/performance/efficiency")
    record("Performance: Efficiency", "GET", "/api/performance/efficiency", s, e is None, e)

    s, d, e = get(f"{base_url}/api/performance/forecast")
    record("Performance: Forecast", "GET", "/api/performance/forecast", s, e is None, e)

    s, d, e = get(f"{base_url}/api/performance/benchmarks")
    record("Performance: Benchmarks", "GET", "/api/performance/benchmarks", s, e is None, e)

    # ====================== SETTINGS ======================
    s, d, e = get(f"{base_url}/api/settings/organization")
    record("Settings: Organization", "GET", "/api/settings/organization", s, e is None, e)

    s, d, e = put(f"{base_url}/api/settings/organization",
                   {"timezone": "UTC"})
    record("Settings: Update Org", "PUT", "/api/settings/organization", s, e is None, e)

    s, d, e = get(f"{base_url}/api/settings/integrations")
    record("Settings: Integrations", "GET", "/api/settings/integrations", s, e is None, e)

    s, d, e = get(f"{base_url}/api/settings/api-keys")
    record("Settings: API Keys", "GET", "/api/settings/api-keys", s, e is None, e)

    s, d, e = get(f"{base_url}/api/settings/webhook-endpoints")
    record("Settings: Webhooks", "GET", "/api/settings/webhook-endpoints", s, e is None, e)

    s, d, e = get(f"{base_url}/api/settings/notifications")
    record("Settings: Notifications", "GET", "/api/settings/notifications", s, e is None, e)

    s, d, e = get(f"{base_url}/api/settings/billing")
    record("Settings: Billing", "GET", "/api/settings/billing", s, e is None, e)

    # ====================== CACHE STATS ======================
    s, d, e = get(f"{base_url}/api/perf/cache-stats", headers=NO_AUTH_HEADERS)
    record("Perf: Cache Stats", "GET", "/api/perf/cache-stats", s, e is None, e)

    return results


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def wait_for_server(base_url, timeout=30):
    """Wait until the server responds or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urlopen(f"{base_url}/health", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def start_server(port):
    """Start the Flask app in a subprocess."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root

    proc = subprocess.Popen(
        [sys.executable, "-c",
         f"from backend.app import create_app; app = create_app(); app.run(port={port}, debug=False, use_reloader=False)"],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def print_report(results, elapsed):
    """Print a human-readable test report to stdout."""
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    print("\n" + "=" * 72)
    print("  SoftFactory Integration Verification Report")
    print(f"  Date: {datetime.now().isoformat()}")
    print(f"  Duration: {elapsed:.1f}s")
    print("=" * 72)

    # Group by service
    current_group = ""
    for r in results:
        group = r.name.split(":")[0].strip()
        if group != current_group:
            current_group = group
            print(f"\n  [{current_group}]")

        icon = "PASS" if r.passed else "FAIL"
        status_str = f"[{icon}]"
        line = f"    {status_str:8s} {r.method:6s} {r.url:50s} -> {r.status}"
        if r.error:
            line += f"  ({r.error[:60]})"
        print(line)

    print("\n" + "-" * 72)
    print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
    rate = (passed / total * 100) if total > 0 else 0
    print(f"  Pass Rate: {rate:.1f}%")

    if failed == 0:
        print("\n  STATUS: ALL TESTS PASSED")
    else:
        print(f"\n  STATUS: {failed} TEST(S) FAILED")

    print("=" * 72 + "\n")


def save_report(results, elapsed, filepath):
    """Save JSON report to file."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "duration_seconds": round(elapsed, 2),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "pass_rate": round(sum(1 for r in results if r.passed) / max(len(results), 1) * 100, 1),
        },
        "tests": [r.to_dict() for r in results],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  Report saved to: {filepath}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SoftFactory Integration Verification")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run/connect on")
    parser.add_argument("--report-file", type=str, default=None, help="Path to save JSON report")
    parser.add_argument("--no-start", action="store_true", help="Skip starting server (assume already running)")
    args = parser.parse_args()

    base_url = f"http://localhost:{args.port}"
    proc = None

    try:
        if not args.no_start:
            print(f"Starting SoftFactory server on port {args.port}...")
            proc = start_server(args.port)
            if not wait_for_server(base_url, timeout=30):
                print("ERROR: Server did not start within 30 seconds.")
                if proc:
                    proc.terminate()
                sys.exit(1)
            print("Server started successfully.\n")
        else:
            print(f"Connecting to existing server at {base_url}...")
            if not wait_for_server(base_url, timeout=5):
                print(f"ERROR: No server found at {base_url}")
                sys.exit(1)

        print("Running integration tests...\n")
        start_time = time.time()
        results = run_tests(base_url)
        elapsed = time.time() - start_time

        print_report(results, elapsed)

        if args.report_file:
            save_report(results, elapsed, args.report_file)

        # Exit code: 0 if all passed, 1 if any failed
        failed_count = sum(1 for r in results if not r.passed)
        sys.exit(0 if failed_count == 0 else 1)

    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
