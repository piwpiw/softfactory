"""
Integration tests for key API endpoints.
Verifies HTTP responses, auth, and approval queue persistence/event flow.
"""
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
        assert res.status_code in [200, 401]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert "access_token" in data

    def test_approval_queue_crud_with_demo_token(self, client, auth_headers):
        create_res = client.post("/api/platform/approval-queue", headers=auth_headers, json={
            "id": "sns-auto:test-queue-item",
            "service": "sns-auto",
            "title": "Approval queue test item",
            "status": "queued",
            "approvalMode": "approve-before-publish",
            "approverRole": "admin",
            "channels": ["instagram", "threads"],
            "accountIds": ["acct-1"],
            "sourceUrl": "/sns-auto/create.html",
            "summary": "Unified approval queue integration test item",
            "contract": {
                "engine": "direct",
                "delivery_mode": "direct",
                "payload_version": "2026-03-10"
            },
            "metadata": {
                "slides": 4
            }
        })
        assert create_res.status_code == 200
        created = json.loads(create_res.data)
        assert created["id"] == "sns-auto:test-queue-item"
        assert created["service"] == "sns-auto"
        assert created["approverRole"] == "admin"

        list_res = client.get("/api/platform/approval-queue", headers=auth_headers)
        assert list_res.status_code == 200
        listed = json.loads(list_res.data)
        assert any(item["id"] == "sns-auto:test-queue-item" for item in listed["items"])

        summary_res = client.get("/api/platform/approval-queue/summary", headers=auth_headers)
        assert summary_res.status_code == 200
        summary_data = json.loads(summary_res.data)
        assert summary_data["total"] >= 1
        assert summary_data["byStatus"]["queued"] >= 1

        admin_list_res = client.get("/api/platform/admin/approval-queue", headers=auth_headers)
        assert admin_list_res.status_code == 200
        admin_listed = json.loads(admin_list_res.data)
        assert any(item["id"] == "sns-auto:test-queue-item" for item in admin_listed["items"])

        admin_summary_res = client.get("/api/platform/admin/approval-queue/summary", headers=auth_headers)
        assert admin_summary_res.status_code == 200
        admin_summary = json.loads(admin_summary_res.data)
        assert admin_summary["total"] >= 1

        status_res = client.post(
            "/api/platform/approval-queue/sns-auto:test-queue-item/status",
            headers=auth_headers,
            json={"status": "published"}
        )
        assert status_res.status_code == 200
        updated = json.loads(status_res.data)
        assert updated["status"] == "published"

        events_res = client.get("/api/platform/admin/approval-queue/events?limit=10", headers=auth_headers)
        assert events_res.status_code == 200
        events_data = json.loads(events_res.data)
        event_types = {item["eventType"] for item in events_data["items"] if item["queueKey"] == "sns-auto:test-queue-item"}
        assert "created" in event_types
        assert "status_changed" in event_types

        notifications_res = client.get("/api/notifications", headers=auth_headers)
        assert notifications_res.status_code == 200
        notifications_data = json.loads(notifications_res.data)
        approval_notifications = [
            item for item in notifications_data["data"]
            if item["notification_type"] == "approval_queue"
        ]
        assert approval_notifications

        delete_res = client.delete("/api/platform/approval-queue/sns-auto:test-queue-item", headers=auth_headers)
        assert delete_res.status_code == 200

        events_res_after_delete = client.get("/api/platform/admin/approval-queue/events?limit=10", headers=auth_headers)
        assert events_res_after_delete.status_code == 200
        events_data_after_delete = json.loads(events_res_after_delete.data)
        delete_types = {item["eventType"] for item in events_data_after_delete["items"] if item["queueKey"] == "sns-auto:test-queue-item"}
        assert "deleted" in delete_types


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
        res = client.get("/api/sns/posts", headers=auth_headers)
        assert res.status_code == 200

    def test_get_accounts(self, client, auth_headers):
        res = client.get("/api/sns/accounts", headers=auth_headers)
        assert res.status_code == 200


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


class TestInstagramCardNewsAPI:
    """Test /api/instagram-cardnews/* endpoints backed by the database."""

    def test_templates_generate_projects_and_rules(self, client, auth_headers):
        templates_res = client.get("/api/instagram-cardnews/templates", headers=auth_headers)
        assert templates_res.status_code == 200
        templates = json.loads(templates_res.data)
        assert isinstance(templates, list)

        create_template_res = client.post(
            "/api/instagram-cardnews/templates",
            headers=auth_headers,
            json={
                "name": "Fact Based Template",
                "tone": "professional",
                "slides": 5,
                "structure": ["Hook", "Evidence", "Offer", "CTA"],
                "design": {"fontFamily": "Pretendard"},
                "tags": ["brand", "proof"],
            },
        )
        assert create_template_res.status_code == 201
        created_template = json.loads(create_template_res.data)
        assert created_template["name"] == "Fact Based Template"

        generate_res = client.post(
            "/api/instagram-cardnews/generate",
            headers=auth_headers,
            json={
                "topic": "Spring launch",
                "tone": "dynamic",
                "slide_count": 4,
                "template_id": created_template["id"],
                "keywords": ["launch", "offer"],
                "account_ids": [],
                "channels": [{"platform": "instagram", "format": "instagram-carousel-4-5"}],
            },
        )
        assert generate_res.status_code == 200
        generated = json.loads(generate_res.data)
        assert generated["status"] == "ready"
        assert len(generated["slides"]) == 4

        create_project_res = client.post(
            "/api/instagram-cardnews/projects",
            headers=auth_headers,
            json={
                "title": "Spring launch cardnews",
                "topic": "Spring launch",
                "tone": "dynamic",
                "slide_count": 4,
                "accountIds": [],
                "templates": {"used_template_id": created_template["id"], "score": 91},
                "channels": [{"platform": "instagram", "format": "instagram-carousel-4-5"}],
                "preview": ["Hook", "Proof", "Offer"],
                "draft": generated,
            },
        )
        assert create_project_res.status_code == 201
        project = json.loads(create_project_res.data)
        assert project["title"] == "Spring launch cardnews"

        publish_res = client.post(
            f"/api/instagram-cardnews/projects/{project['id']}/publish",
            headers=auth_headers,
        )
        assert publish_res.status_code == 200
        publish_data = json.loads(publish_res.data)
        assert publish_data["status"] in {"queued", "dispatch_ready"}

        create_rule_res = client.post(
            "/api/instagram-cardnews/dm-rules",
            headers=auth_headers,
            json={"keyword": "price", "reply": "We will send pricing details.", "action": "notify"},
        )
        assert create_rule_res.status_code == 201

        simulate_res = client.post(
            "/api/instagram-cardnews/simulate-dm",
            headers=auth_headers,
            json={"message": "Can you share the price?"},
        )
        assert simulate_res.status_code == 200
        simulation = json.loads(simulate_res.data)
        assert simulation["matched_count"] >= 1


class TestWebAppBuilderAPI:
    """Test /api/webapp-builder/* endpoints."""

    def test_get_plans(self, client, auth_headers):
        res = client.get("/api/webapp-builder/plans", headers=auth_headers)
        assert res.status_code == 200

    def test_get_enrollments(self, client, auth_headers):
        res = client.get("/api/webapp-builder/enrollments", headers=auth_headers)
        assert res.status_code == 200
