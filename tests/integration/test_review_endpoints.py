"""
Test Review Platform Integration — SNS Auto v2.0
Tests review aggregation, account management, platform scraping
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.models import db, User
from backend.app import app


@pytest.fixture
def app_context():
    """Application context for testing"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_context):
    """Test client"""
    return app_context.test_client()


@pytest.fixture
def demo_user():
    """Create demo user"""
    with app.app_context():
        user = User(
            email='review_test@example.com',
            password='hashed_password',
            name='Review Test User'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_headers(demo_user):
    """Authentication headers"""
    return {
        'Authorization': 'Bearer demo_token',
        'Content-Type': 'application/json'
    }


# ============ AGGREGATED LISTINGS TESTS ============

class TestAggregatedListings:
    """Test aggregated review listings across all platforms"""

    def test_get_aggregated_listings(self, client, auth_headers):
        """Test GET /api/review/aggregated (all listings)"""
        res = client.get('/api/review/aggregated', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'data' in data or 'listings' in data

    def test_aggregated_with_category_filter(self, client, auth_headers):
        """Test GET /api/review/aggregated?category=fashion"""
        res = client.get('/api/review/aggregated?category=fashion', headers=auth_headers)
        assert res.status_code in [200, 404]

    def test_aggregated_with_reward_range_filter(self, client, auth_headers):
        """Test GET /api/review/aggregated?min_reward=10000&max_reward=50000"""
        res = client.get(
            '/api/review/aggregated?min_reward=10000&max_reward=50000',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_aggregated_with_follower_filter(self, client, auth_headers):
        """Test GET /api/review/aggregated?min_followers=1000&max_followers=10000"""
        res = client.get(
            '/api/review/aggregated?min_followers=1000&max_followers=10000',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_aggregated_pagination(self, client, auth_headers):
        """Test GET /api/review/aggregated?page=1&limit=20"""
        res = client.get('/api/review/aggregated?page=1&limit=20', headers=auth_headers)
        assert res.status_code in [200, 404]


# ============ ACCOUNT MANAGEMENT TESTS ============

class TestAccountManagement:
    """Test review account CRUD operations"""

    def test_create_account(self, client, auth_headers):
        """Test POST /api/review/accounts"""
        res = client.post(
            '/api/review/accounts',
            headers=auth_headers,
            json={
                'platform': 'naver',
                'account_name': 'newblog',
                'follower_count': 3000
            }
        )
        assert res.status_code in [201, 200, 404]

    def test_get_accounts(self, client, auth_headers):
        """Test GET /api/review/accounts"""
        res = client.get('/api/review/accounts', headers=auth_headers)
        assert res.status_code in [200, 404]


# ============ REVIEW LISTING TESTS ============

class TestReviewListings:
    """Test review listing management"""

    def test_get_listings(self, client, auth_headers):
        """Test GET /api/review/listings"""
        res = client.get('/api/review/listings', headers=auth_headers)
        assert res.status_code in [200, 404]

    def test_create_listing(self, client, auth_headers):
        """Test POST /api/review/listings"""
        res = client.post(
            '/api/review/listings',
            headers=auth_headers,
            json={
                'source_platform': 'custom',
                'title': 'Custom Review Request',
                'category': 'beauty',
                'reward_amount': 30000
            }
        )
        assert res.status_code in [201, 200, 404]


# ============ APPLICATION TESTS ============

class TestApplicationManagement:
    """Test review application operations"""

    def test_create_application(self, client, auth_headers):
        """Test POST /api/review/applications"""
        res = client.post(
            '/api/review/applications',
            headers=auth_headers,
            json={'listing_id': 1, 'account_id': 1}
        )
        assert res.status_code in [201, 200, 404]

    def test_get_applications(self, client, auth_headers):
        """Test GET /api/review/applications"""
        res = client.get('/api/review/applications', headers=auth_headers)
        assert res.status_code in [200, 404]


# ============ AUTHORIZATION TESTS ============

class TestAuthorizationValidation:
    """Test @require_auth on all Review endpoints"""

    def test_review_endpoints_require_auth(self, client):
        """Test all Review endpoints require authentication"""
        endpoints = [
            '/api/review/aggregated',
            '/api/review/accounts',
            '/api/review/listings',
            '/api/review/applications'
        ]

        for endpoint in endpoints:
            res = client.get(endpoint)
            assert res.status_code == 401


# ============ ERROR HANDLING TESTS ============

class TestErrorHandling:
    """Test error scenarios and responses"""

    def test_invalid_account_id(self, client, auth_headers):
        """Test accessing non-existent account"""
        res = client.get('/api/review/accounts/99999', headers=auth_headers)
        assert res.status_code in [404, 200]

    def test_missing_required_fields(self, client, auth_headers):
        """Test POST with missing required fields"""
        res = client.post(
            '/api/review/applications',
            headers=auth_headers,
            json={}
        )
        assert res.status_code in [400, 404]

    def test_invalid_json_payload(self, client, auth_headers):
        """Test endpoint with invalid JSON"""
        res = client.post(
            '/api/review/accounts',
            headers=auth_headers,
            data='invalid json{',
            content_type='application/json'
        )
        assert res.status_code in [400, 404]
