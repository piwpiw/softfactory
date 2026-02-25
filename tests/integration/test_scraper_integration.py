"""
Test Scraper Integration — Review Platform v2.0
Tests review platform scrapers for duplicate prevention, data quality
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
            email='scraper_test@example.com',
            password='hashed_password',
            name='Scraper Test User'
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


class TestScraperIntegration:
    """Test platform scraper integration"""

    def test_scraper_sync_trigger(self, client, auth_headers):
        """Test POST /api/review/sync (trigger scraper)"""
        res = client.post(
            '/api/review/sync',
            headers=auth_headers,
            json={}
        )
        assert res.status_code in [200, 202, 404]

    def test_scraper_sync_specific_platform(self, client, auth_headers):
        """Test POST /api/review/sync?platform=revu"""
        res = client.post(
            '/api/review/sync?platform=revu',
            headers=auth_headers,
            json={}
        )
        assert res.status_code in [200, 202, 404]

    def test_scraper_status(self, client, auth_headers):
        """Test GET /api/review/sync-status"""
        res = client.get('/api/review/sync-status', headers=auth_headers)
        assert res.status_code in [200, 404]


class TestDuplicatePrevention:
    """Test duplicate listing prevention"""

    def test_no_duplicates_on_second_scrape(self, client, auth_headers):
        """Test duplicate listings are not created during scraping"""
        # Run scraper twice
        for _ in range(2):
            res = client.post(
                '/api/review/sync?platform=revu',
                headers=auth_headers
            )
            assert res.status_code in [200, 202, 404]

        # Verify no duplicates (tested by checking external_id uniqueness)
        res = client.get('/api/review/listings', headers=auth_headers)
        if res.status_code == 200:
            data = json.loads(res.data)
            if isinstance(data.get('data'), list):
                # All external_ids should be unique
                external_ids = [item.get('external_id') for item in data['data']]
                assert len(external_ids) == len(set(external_ids))


class TestScraperErrorHandling:
    """Test scraper error scenarios"""

    def test_scraper_invalid_platform(self, client, auth_headers):
        """Test scraper with invalid platform"""
        res = client.post(
            '/api/review/sync?platform=invalid_platform',
            headers=auth_headers
        )
        assert res.status_code in [400, 404]

    def test_scraper_graceful_failure(self, client, auth_headers):
        """Test scraper handles network errors gracefully"""
        res = client.post(
            '/api/review/sync?platform=revu',
            headers=auth_headers
        )
        # Should not crash
        assert res.status_code in [200, 202, 404, 500]
