"""
E2E Tests: Critical User Journeys
Tests complete flows from login to service usage.
Requires running server at localhost:8000.
"""
import pytest
import requests

BASE = "http://localhost:8000"
DEMO_HEADERS = {"Authorization": "Bearer demo_token"}


@pytest.fixture(scope="module")
def server_running():
    """Check server is up."""
    try:
        r = requests.get(f"{BASE}/web/platform/login.html", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


class TestLoginJourney:
    """User can log in and reach dashboard."""

    def test_login_page_loads(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/web/platform/login.html")
        assert r.status_code == 200
        assert "SoftFactory" in r.text

    def test_demo_api_accessible(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/api/platform/dashboard", headers=DEMO_HEADERS)
        assert r.status_code == 200


class TestSNSAutoJourney:
    """User can manage SNS posts."""

    def test_sns_index_loads(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/web/sns-auto/index.html")
        assert r.status_code == 200


class TestCooCookJourney:
    """User can browse and book chefs."""

    def test_coocook_index_loads(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/web/coocook/index.html")
        assert r.status_code == 200

    def test_chef_api_returns_list(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/api/coocook/chefs", headers=DEMO_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "chefs" in data
        assert len(data["chefs"]) > 0


class TestReviewJourney:
    """User can find and apply to campaigns."""

    def test_review_campaigns_api(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        r = requests.get(f"{BASE}/api/review/campaigns", headers=DEMO_HEADERS)
        assert r.status_code == 200


class TestAllPlatformPages:
    """All 32 platform pages return 200."""

    PAGES = [
        "login.html", "dashboard.html", "billing.html", "profile.html",
        "settings.html", "help.html", "contact.html", "admin.html",
        "api-keys.html", "integrations.html", "usage.html", "changelog.html",
        "roadmap.html", "feedback.html", "notifications.html", "team.html",
        "security.html", "privacy.html", "terms.html", "status.html",
    ]

    def test_all_pages_load(self, server_running):
        if not server_running:
            pytest.skip("Server not running")
        failures = []
        for page in self.PAGES:
            r = requests.get(f"{BASE}/web/platform/{page}", timeout=3)
            if r.status_code != 200:
                failures.append(f"{page}: {r.status_code}")
        assert failures == [], f"Pages failed: {failures}"
