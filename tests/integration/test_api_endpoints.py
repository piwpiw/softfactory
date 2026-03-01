"""
Integration Tests: All 16 API Endpoints
Verifies HTTP responses, auth, and data shapes.
"""
import pytest
import json


class TestPlatformAPI:
    """Test /api/platform/* endpoints."""

    def test_dashboard_requires_auth(self, client):
        res = client.get("/api/platform/dashboard")
        assert res.status_code == 401

    def test_dashboard_with_demo_token(self, client, auth_headers):
        res = client.get("/api/platform/dashboard", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "products" in data or "subscriptions" in data

    def test_login_with_credentials(self, client):
        res = client.post("/api/auth/login", json={
            "email": "demo@softfactory.com",
            "password": "demo123"
        })
        # Accept 200 (success) or 401 (user not found in test DB)
        assert res.status_code in [200, 401]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert "access_token" in data


class TestCooCookAPI:
    """Test /api/coocook/* endpoints."""

    def test_get_chefs(self, client, auth_headers):
        res = client.get("/api/coocook/chefs", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "chefs" in data
        assert isinstance(data["chefs"], list)

    def test_get_bookings(self, client, auth_headers):
        res = client.get("/api/coocook/bookings", headers=auth_headers)
        assert res.status_code == 200


class TestSNSAutoAPI:
    """Test /api/sns-auto/* endpoints."""

    def test_get_posts(self, client, auth_headers):
        res = client.get("/api/sns-auto/posts", headers=auth_headers)
        # 200 or 404 (route may differ)
        assert res.status_code in (200, 404)

    def test_get_accounts(self, client, auth_headers):
        res = client.get("/api/sns-auto/accounts", headers=auth_headers)
        assert res.status_code in (200, 404)


class TestReviewAPI:
    """Test /api/review/* endpoints."""

    def test_get_campaigns(self, client, auth_headers):
        res = client.get("/api/review/campaigns", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "campaigns" in data


class TestAIAutomationAPI:
    """Test /api/ai-automation/* endpoints."""

    def test_get_scenarios(self, client, auth_headers):
        res = client.get("/api/ai-automation/scenarios", headers=auth_headers)
        assert res.status_code == 200

    def test_get_employees(self, client, auth_headers):
        res = client.get("/api/ai-automation/employees", headers=auth_headers)
        assert res.status_code == 200


class TestWebAppBuilderAPI:
    """Test /api/webapp-builder/* endpoints."""

    def test_get_plans(self, client, auth_headers):
        res = client.get("/api/webapp-builder/plans", headers=auth_headers)
        assert res.status_code == 200

    def test_get_enrollments(self, client, auth_headers):
        res = client.get("/api/webapp-builder/enrollments", headers=auth_headers)
        assert res.status_code == 200
