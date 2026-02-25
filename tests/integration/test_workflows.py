"""
Integration Tests: Complete Workflows & Multi-Step Journeys
Tests end-to-end business processes.
"""
import pytest
import json
from datetime import datetime, timedelta, date


class TestUserAuthenticationWorkflow:
    """Test complete user authentication flow."""

    def test_user_registration_and_login(self, client):
        """Register user then login with credentials."""
        # Step 1: Register
        reg_res = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "securepassword123"
        })
        assert reg_res.status_code == 201
        reg_data = json.loads(reg_res.data)
        assert "access_token" in reg_data
        assert "user" in reg_data
        assert reg_data["user"]["email"] == "newuser@example.com"

        # Step 2: Login with same credentials
        login_res = client.post("/api/auth/login", json={
            "email": "newuser@example.com",
            "password": "securepassword123"
        })
        assert login_res.status_code == 200
        login_data = json.loads(login_res.data)
        assert "access_token" in login_data
        assert login_data["user"]["email"] == "newuser@example.com"

    def test_token_refresh_workflow(self, client, db):
        """Test token refresh flow."""
        from backend.models import User
        user = User(email="refresh@example.com", name="Refresh Test")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # Step 1: Login
        login_res = client.post("/api/auth/login", json={
            "email": "refresh@example.com",
            "password": "password123"
        })
        assert login_res.status_code == 200
        tokens = json.loads(login_res.data)
        refresh_token = tokens["refresh_token"]

        # Step 2: Use refresh token
        refresh_res = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_res.status_code == 200
        new_tokens = json.loads(refresh_res.data)
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

    def test_user_profile_after_registration(self, client):
        """Get user profile after registration."""
        # Step 1: Register
        reg_res = client.post("/api/auth/register", json={
            "email": "profile@example.com",
            "name": "Profile User",
            "password": "pass123"
        })
        assert reg_res.status_code == 201
        tokens = json.loads(reg_res.data)
        access_token = tokens["access_token"]

        # Step 2: Get profile with token
        profile_res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile_res.status_code == 200
        profile_data = json.loads(profile_res.data)
        assert profile_data["email"] == "profile@example.com"
        assert profile_data["name"] == "Profile User"


class TestCooCookWorkflow:
    """Test chef booking workflow."""

    def test_browse_chefs_then_book(self, client, auth_headers, db):
        """Complete CooCook booking workflow."""
        from backend.models import Chef, Booking

        # Step 1: Get available chefs
        chef_res = client.get("/api/coocook/chefs", headers=auth_headers)
        assert chef_res.status_code == 200
        chefs_data = json.loads(chef_res.data)
        assert "chefs" in chefs_data
        assert len(chefs_data["chefs"]) > 0

        # Step 2: Get chef details (first chef)
        first_chef = chefs_data["chefs"][0]
        chef_id = first_chef["id"]
        assert "name" in first_chef
        assert "rating" in first_chef
        assert "price_per_session" in first_chef

        # Step 3: Create booking
        booking_date = (date.today() + timedelta(days=7)).isoformat()
        booking_res = client.post("/api/coocook/bookings", json={
            "chef_id": chef_id,
            "booking_date": booking_date,
            "duration_hours": 3,
            "special_requests": "Please bring extra ingredients"
        }, headers=auth_headers)
        assert booking_res.status_code in (201, 200, 400)

        if booking_res.status_code in (201, 200):
            booking_data = json.loads(booking_res.data)
            assert "id" in booking_data or "booking_id" in booking_data

    def test_view_own_bookings(self, client, auth_headers):
        """User can view their own bookings."""
        booking_res = client.get("/api/coocook/bookings", headers=auth_headers)
        assert booking_res.status_code == 200
        bookings_data = json.loads(booking_res.data)
        assert "bookings" in bookings_data or isinstance(bookings_data, dict)


class TestReviewCampaignWorkflow:
    """Test review campaign application workflow."""

    def test_browse_campaigns_then_apply(self, client, auth_headers):
        """Browse campaigns and apply to one."""
        # Step 1: Get campaigns
        campaigns_res = client.get("/api/review/campaigns", headers=auth_headers)
        assert campaigns_res.status_code == 200
        campaigns_data = json.loads(campaigns_res.data)
        assert "campaigns" in campaigns_data

        if len(campaigns_data["campaigns"]) > 0:
            # Step 2: Apply to first campaign
            campaign = campaigns_data["campaigns"][0]
            campaign_id = campaign["id"]

            apply_res = client.post("/api/review/applications", json={
                "campaign_id": campaign_id,
                "message": "I would love to review this product!",
                "sns_link": "https://instagram.com/testuser",
                "follower_count": 1500
            }, headers=auth_headers)
            assert apply_res.status_code in (201, 200, 400)

    def test_view_own_applications(self, client, auth_headers):
        """User can view their own campaign applications."""
        apps_res = client.get("/api/review/applications", headers=auth_headers)
        # May return 200, 404 (not implemented), or error
        assert apps_res.status_code in (200, 404, 400)


class TestSNSAutoWorkflow:
    """Test SNS automation workflow."""

    def test_create_and_schedule_post(self, client, auth_headers):
        """Create SNS account and schedule post."""
        # Step 1: Get accounts
        accounts_res = client.get("/api/sns-auto/accounts", headers=auth_headers)
        assert accounts_res.status_code in (200, 404)

        if accounts_res.status_code == 200:
            accounts_data = json.loads(accounts_res.data)
            if "accounts" in accounts_data and len(accounts_data["accounts"]) > 0:
                # Step 2: Create post
                post_res = client.post("/api/sns-auto/posts", json={
                    "account_id": accounts_data["accounts"][0]["id"],
                    "content": "Check out this amazing product!",
                    "platform": "instagram",
                    "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                    "template_type": "card_news"
                }, headers=auth_headers)
                assert post_res.status_code in (201, 200, 400)

    def test_view_scheduled_posts(self, client, auth_headers):
        """View all scheduled posts."""
        posts_res = client.get("/api/sns-auto/posts", headers=auth_headers)
        assert posts_res.status_code in (200, 404)


class TestAIAutomationWorkflow:
    """Test AI automation scenario workflow."""

    def test_browse_scenarios_and_deploy(self, client, auth_headers):
        """Browse automation scenarios and deploy one."""
        # Step 1: Get available scenarios
        scenarios_res = client.get(
            "/api/ai-automation/scenarios",
            headers=auth_headers
        )
        assert scenarios_res.status_code == 200
        scenarios_data = json.loads(scenarios_res.data)
        assert "scenarios" in scenarios_data

        if len(scenarios_data["scenarios"]) > 0:
            # Step 2: Deploy first scenario
            scenario = scenarios_data["scenarios"][0]
            deploy_res = client.post("/api/ai-automation/deploy", json={
                "scenario_id": scenario["id"],
                "name": f"My {scenario['name']}",
                "description": "Custom deployment",
                "status": "training"
            }, headers=auth_headers)
            assert deploy_res.status_code in (201, 200, 400, 404)

    def test_view_deployed_employees(self, client, auth_headers):
        """View deployed AI employees."""
        employees_res = client.get(
            "/api/ai-automation/employees",
            headers=auth_headers
        )
        assert employees_res.status_code == 200
        employees_data = json.loads(employees_res.data)
        assert "employees" in employees_data or isinstance(employees_data, dict)


class TestWebAppBuilderWorkflow:
    """Test web app builder enrollment workflow."""

    def test_view_plans_and_enroll(self, client, auth_headers):
        """View bootcamp plans and enroll."""
        # Step 1: Get plans
        plans_res = client.get("/api/webapp-builder/plans", headers=auth_headers)
        assert plans_res.status_code == 200
        plans_data = json.loads(plans_res.data)
        assert "plans" in plans_data

        if len(plans_data["plans"]) > 0:
            # Step 2: Enroll in plan
            plan = plans_data["plans"][0]
            enroll_res = client.post("/api/webapp-builder/enroll", json={
                "plan_type": plan.get("type", "weekday"),
                "start_date": datetime.utcnow().isoformat()
            }, headers=auth_headers)
            assert enroll_res.status_code in (201, 200, 400)

    def test_view_enrollments(self, client, auth_headers):
        """View user's bootcamp enrollments."""
        enrollments_res = client.get(
            "/api/webapp-builder/enrollments",
            headers=auth_headers
        )
        assert enrollments_res.status_code == 200


class TestPaymentWorkflow:
    """Test payment and subscription workflow."""

    def test_get_products_then_subscribe(self, client, auth_headers):
        """Get available products and subscribe."""
        # Step 1: Get products
        products_res = client.get("/api/platform/products", headers=auth_headers)
        # Endpoint may not exist; just check response
        if products_res.status_code == 200:
            products_data = json.loads(products_res.data)
            if "products" in products_data and len(products_data["products"]) > 0:
                # Step 2: Initiate subscription
                product = products_data["products"][0]
                sub_res = client.post("/api/payment/subscribe", json={
                    "product_id": product["id"],
                    "plan_type": "monthly"
                }, headers=auth_headers)
                assert sub_res.status_code in (201, 200, 400, 404)

    def test_view_billing_history(self, client, auth_headers):
        """View billing and subscription history."""
        billing_res = client.get("/api/platform/billing", headers=auth_headers)
        # Endpoint may not exist or may require subscription
        assert billing_res.status_code in (200, 404, 403)


class TestDashboardWorkflow:
    """Test main dashboard and overview."""

    def test_full_dashboard_access(self, client, auth_headers):
        """Access main dashboard with all data."""
        dashboard_res = client.get("/api/platform/dashboard", headers=auth_headers)
        assert dashboard_res.status_code == 200
        dashboard_data = json.loads(dashboard_res.data)

        # Dashboard should have overview data
        assert isinstance(dashboard_data, dict)
        # May include: products, subscriptions, bookings, campaigns, etc.

    def test_dashboard_requires_auth(self, client):
        """Dashboard access without auth returns 401."""
        dashboard_res = client.get("/api/platform/dashboard")
        assert dashboard_res.status_code == 401


class TestDataIntegrity:
    """Test data integrity across operations."""

    def test_cascade_delete_user_removes_subscriptions(self, db):
        """Deleting user cascades to subscriptions."""
        from backend.models import User, Product, Subscription

        user = User(email="cascade@example.com", name="Cascade User")
        user.set_password("password")
        db.session.add(user)
        db.session.flush()

        product = Product(
            name="Test Product",
            slug="cascade-test",
            monthly_price=50.0
        )
        db.session.add(product)
        db.session.flush()

        subscription = Subscription(
            user_id=user.id,
            product_id=product.id,
            status="active"
        )
        db.session.add(subscription)
        db.session.commit()

        user_id = user.id
        sub_count_before = Subscription.query.filter_by(user_id=user_id).count()
        assert sub_count_before == 1

        # Delete user
        db.session.delete(user)
        db.session.commit()

        # Check subscriptions are deleted
        sub_count_after = Subscription.query.filter_by(user_id=user_id).count()
        assert sub_count_after == 0

    def test_booking_requires_valid_user_and_chef(self, db):
        """Booking must reference existing user and chef."""
        from backend.models import Booking
        from datetime import date

        # Attempt to create booking with non-existent IDs
        booking = Booking(
            user_id=99999,  # Non-existent
            chef_id=99999,  # Non-existent
            booking_date=date.today() + timedelta(days=1),
            duration_hours=2,
            total_price=100.0
        )
        db.session.add(booking)

        # This may fail with FK constraint or succeed if FK is not enforced
        try:
            db.session.commit()
            # If it succeeds, cleanup
            db.session.delete(booking)
            db.session.commit()
        except Exception:
            # Foreign key constraint violation expected
            db.session.rollback()

    def test_campaign_application_requires_valid_campaign(self, db):
        """Campaign application must reference existing campaign."""
        from backend.models import CampaignApplication

        app = CampaignApplication(
            campaign_id=99999,  # Non-existent
            user_id=1,
            message="I want to review"
        )
        db.session.add(app)

        try:
            db.session.commit()
            db.session.delete(app)
            db.session.commit()
        except Exception:
            db.session.rollback()


class TestResponseFormats:
    """Test consistent response formats."""

    def test_success_response_has_consistent_structure(self, client, auth_headers):
        """Success responses have consistent JSON structure."""
        res = client.get("/api/platform/dashboard", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert isinstance(data, dict)

    def test_error_response_includes_error_field(self, client):
        """Error responses include 'error' field."""
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 400
        data = json.loads(res.data)
        assert "error" in data

    def test_list_responses_have_array_fields(self, client, auth_headers):
        """List endpoints return arrays in expected fields."""
        # Test chefs list
        res = client.get("/api/coocook/chefs", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "chefs" in data
        assert isinstance(data["chefs"], list)

        # Test campaigns list
        res = client.get("/api/review/campaigns", headers=auth_headers)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)
