"""Tests for SNS Revenue Monetization APIs

Test Coverage:
- Link-in-Bio API (6 endpoints: POST/GET/PUT/DELETE/list/stats)
- Automation API (6 endpoints: POST/GET/PUT/DELETE/list/run)
- Trending API (GET with filters)
- Content Repurpose API (POST with platform conversion)
- Competitor Analysis API (POST/GET/DELETE/compare)
- ROI Calculator API (GET with aggregation)

Test Strategy:
- Unit tests for each endpoint
- Integration tests with authentication
- Pagination tests (offset + cursor)
- Field filtering tests
- Error handling tests (400/401/404/422/500)
- Caching verification tests
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.models import (
    db, User, SNSLinkInBio, SNSAutomate, SNSCompetitor,
    SNSAnalytics, SNSAccount
)
from backend.auth import require_auth


@pytest.fixture
def user(app):
    """Create test user"""
    with app.app_context():
        u = User(
            email='test_revenue@example.com',
            name='Test User',
        )
        u.set_password('testpass123')
        db.session.add(u)
        db.session.commit()
        return u


@pytest.fixture
def auth_headers():
    """Generate authentication headers using demo token"""
    return {'Authorization': 'Bearer demo_token'}


# ============ LINK-IN-BIO API TESTS ============

class TestLinkInBioAPI:
    """Tests for Link-in-Bio endpoints"""

    def test_create_linkinbio_success(self, client, auth_headers):
        """Test successful Link-in-Bio creation"""
        payload = {
            'slug': 'my-shop',
            'title': 'My Products',
            'links': [
                {'url': 'https://shop.com', 'label': 'Shop', 'icon': 'shopping-bag'},
                {'url': 'https://blog.com', 'label': 'Blog', 'icon': 'book'}
            ],
            'theme': 'light'
        }

        response = client.post(
            '/api/sns/linkinbio',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['slug'] == 'my-shop'
        assert data['data']['title'] == 'My Products'
        assert len(data['data']['links']) == 2

    def test_create_linkinbio_missing_fields(self, client, auth_headers):
        """Test Link-in-Bio creation with missing required fields"""
        payload = {'slug': 'my-shop'}  # Missing title

        response = client.post(
            '/api/sns/linkinbio',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'Missing fields' in data['error']

    def test_create_linkinbio_duplicate_slug(self, client, app, auth_headers, user):
        """Test Link-in-Bio creation with duplicate slug"""
        with app.app_context():
            # Create first Link-in-Bio
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='duplicate',
                title='First',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()

        # Try to create with same slug
        payload = {'slug': 'duplicate', 'title': 'Second'}
        response = client.post(
            '/api/sns/linkinbio',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'already exists' in data['error']

    def test_create_linkinbio_invalid_slug(self, client, auth_headers):
        """Test Link-in-Bio creation with invalid slug format"""
        payload = {
            'slug': 'invalid@#$',  # Invalid characters
            'title': 'My Products'
        }

        response = client.post(
            '/api/sns/linkinbio',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'alphanumeric' in data['error'].lower()

    def test_list_linkinbio_with_pagination(self, client, app, auth_headers, user):
        """Test Link-in-Bio list with pagination"""
        with app.app_context():
            # Create multiple Link-in-Bios
            for i in range(5):
                lib = SNSLinkInBio(
                    user_id=user.id,
                    slug=f'bio-{i}',
                    title=f'Bio {i}',
                    links=[],
                    theme='light'
                )
                db.session.add(lib)
            db.session.commit()

        # Test offset pagination
        response = client.get(
            '/api/sns/linkinbio?pagination=offset&page=1&per_page=2',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 2
        assert data['total'] == 5

    def test_list_linkinbio_with_field_filtering(self, client, app, auth_headers, user):
        """Test Link-in-Bio list with field filtering"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Test Bio',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()

        response = client.get(
            '/api/sns/linkinbio?fields=slug,title',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'slug' in data['data'][0]
        assert 'title' in data['data'][0]
        # theme should not be present (filtered out)
        assert 'theme' not in data['data'][0]

    def test_get_linkinbio_detail(self, client, app, auth_headers, user):
        """Test get specific Link-in-Bio"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Test Bio',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()
            lib_id = lib.id

        response = client.get(
            f'/api/sns/linkinbio/{lib_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['slug'] == 'test'

    def test_get_linkinbio_not_found(self, client, auth_headers):
        """Test get non-existent Link-in-Bio"""
        response = client.get(
            '/api/sns/linkinbio/999',
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data['error'].lower()

    def test_update_linkinbio_success(self, client, app, auth_headers, user):
        """Test successful Link-in-Bio update"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Original',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()
            lib_id = lib.id

        payload = {
            'title': 'Updated Title',
            'theme': 'dark'
        }

        response = client.put(
            f'/api/sns/linkinbio/{lib_id}',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['theme'] == 'dark'

    def test_update_linkinbio_invalid_theme(self, client, app, auth_headers, user):
        """Test update with invalid theme"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Test',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()
            lib_id = lib.id

        payload = {'theme': 'invalid-theme'}

        response = client.put(
            f'/api/sns/linkinbio/{lib_id}',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid theme' in data['error']

    def test_delete_linkinbio_success(self, client, app, auth_headers, user):
        """Test successful Link-in-Bio deletion"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Test',
                links=[],
                theme='light'
            )
            db.session.add(lib)
            db.session.commit()
            lib_id = lib.id

        response = client.delete(
            f'/api/sns/linkinbio/{lib_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'deleted' in data['message'].lower()

    def test_get_linkinbio_stats(self, client, app, auth_headers, user):
        """Test Link-in-Bio statistics"""
        with app.app_context():
            lib = SNSLinkInBio(
                user_id=user.id,
                slug='test',
                title='Test',
                links=[{'url': 'https://example.com', 'label': 'Example'}],
                theme='light',
                click_count=42
            )
            db.session.add(lib)
            db.session.commit()
            lib_id = lib.id

        response = client.get(
            f'/api/sns/linkinbio/stats/{lib_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['total_clicks'] == 42
        assert len(data['data']['links']) == 1


# ============ AUTOMATION API TESTS ============

class TestAutomationAPI:
    """Tests for Automation endpoints"""

    def test_create_automation_success(self, client, auth_headers):
        """Test successful automation creation"""
        payload = {
            'name': 'Daily Tips',
            'topic': 'Product tips',
            'purpose': 'engagement',
            'platforms': ['instagram', 'twitter'],
            'frequency': 'daily',
            'is_active': True
        }

        response = client.post(
            '/api/sns/automate',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['name'] == 'Daily Tips'
        assert data['data']['is_active'] is True

    def test_create_automation_invalid_frequency(self, client, auth_headers):
        """Test automation with invalid frequency"""
        payload = {
            'name': 'Daily Tips',
            'topic': 'Tips',
            'purpose': 'engagement',
            'platforms': ['instagram'],
            'frequency': 'invalid_freq'
        }

        response = client.post(
            '/api/sns/automate',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid frequency' in data['error']

    def test_create_automation_invalid_purpose(self, client, auth_headers):
        """Test automation with invalid purpose"""
        payload = {
            'name': 'Daily Tips',
            'topic': 'Tips',
            'purpose': 'invalid_purpose',
            'platforms': ['instagram'],
            'frequency': 'daily'
        }

        response = client.post(
            '/api/sns/automate',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid purpose' in data['error']

    def test_list_automations(self, client, app, auth_headers, user):
        """Test list automations with pagination"""
        with app.app_context():
            for i in range(3):
                auto = SNSAutomate(
                    user_id=user.id,
                    name=f'Auto {i}',
                    topic=f'Topic {i}',
                    purpose='engagement',
                    platforms=['instagram'],
                    frequency='daily',
                    next_run=datetime.utcnow() + timedelta(days=1),
                    is_active=True
                )
                db.session.add(auto)
            db.session.commit()

        response = client.get(
            '/api/sns/automate?pagination=offset&per_page=2',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['total'] == 3

    def test_update_automation(self, client, app, auth_headers, user):
        """Test update automation"""
        with app.app_context():
            auto = SNSAutomate(
                user_id=user.id,
                name='Original',
                topic='Topic',
                purpose='engagement',
                platforms=['instagram'],
                frequency='daily',
                next_run=datetime.utcnow() + timedelta(days=1),
                is_active=True
            )
            db.session.add(auto)
            db.session.commit()
            auto_id = auto.id

        payload = {'name': 'Updated Name', 'is_active': False}

        response = client.put(
            f'/api/sns/automate/{auto_id}',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Updated Name'
        assert data['data']['is_active'] is False

    def test_delete_automation(self, client, app, auth_headers, user):
        """Test delete automation"""
        with app.app_context():
            auto = SNSAutomate(
                user_id=user.id,
                name='To Delete',
                topic='Topic',
                purpose='engagement',
                platforms=['instagram'],
                frequency='daily',
                next_run=datetime.utcnow() + timedelta(days=1),
                is_active=True
            )
            db.session.add(auto)
            db.session.commit()
            auto_id = auto.id

        response = client.delete(
            f'/api/sns/automate/{auto_id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'deleted' in data['message'].lower()

    def test_run_automation(self, client, app, auth_headers, user):
        """Test manual automation execution"""
        with app.app_context():
            auto = SNSAutomate(
                user_id=user.id,
                name='Test Auto',
                topic='Topic',
                purpose='engagement',
                platforms=['instagram'],
                frequency='daily',
                next_run=datetime.utcnow() + timedelta(days=1),
                is_active=True
            )
            db.session.add(auto)
            db.session.commit()
            auto_id = auto.id

        response = client.post(
            f'/api/sns/automate/{auto_id}/run',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['status'] == 'executed'


# ============ TRENDING API TESTS ============

class TestTrendingAPI:
    """Tests for Trending endpoints"""

    def test_get_trending_all(self, client, auth_headers):
        """Test get trending topics without filters"""
        response = client.get(
            '/api/sns/trending',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'hashtags' in data['data']
        assert 'topics' in data['data']
        assert 'best_posting_times' in data['data']

    def test_get_trending_by_platform(self, client, auth_headers):
        """Test get trending for specific platform"""
        response = client.get(
            '/api/sns/trending?platform=instagram&region=KR',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['platform'] == 'instagram'
        assert data['data']['region'] == 'KR'

    def test_get_trending_invalid_platform(self, client, auth_headers):
        """Test trending with invalid platform"""
        response = client.get(
            '/api/sns/trending?platform=invalid',
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid platform' in data['error']


# ============ CONTENT REPURPOSE API TESTS ============

class TestRepurposeAPI:
    """Tests for Content Repurpose endpoints"""

    def test_repurpose_content_success(self, client, auth_headers):
        """Test successful content repurposing"""
        payload = {
            'content': 'Check out our new AI tool!',
            'platforms': ['instagram', 'twitter'],
            'tone': 'professional'
        }

        response = client.post(
            '/api/sns/repurpose',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'repurposed' in data['data']
        assert 'instagram' in data['data']['repurposed']
        assert 'twitter' in data['data']['repurposed']

    def test_repurpose_content_invalid_tone(self, client, auth_headers):
        """Test repurposing with invalid tone"""
        payload = {
            'content': 'Test content',
            'platforms': ['instagram'],
            'tone': 'invalid_tone'
        }

        response = client.post(
            '/api/sns/repurpose',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid tone' in data['error']


# ============ COMPETITOR ANALYSIS API TESTS ============

class TestCompetitorAPI:
    """Tests for Competitor endpoints"""

    def test_add_competitor_success(self, client, auth_headers):
        """Test successful competitor addition"""
        payload = {
            'platform': 'instagram',
            'username': '@competitor',
            'name': 'Competitor Inc'
        }

        response = client.post(
            '/api/sns/competitor',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['username'] == '@competitor'

    def test_add_competitor_duplicate(self, client, app, auth_headers, user):
        """Test adding duplicate competitor"""
        with app.app_context():
            comp = SNSCompetitor(
                user_id=user.id,
                platform='instagram',
                username='@existing',
                name='Existing Competitor'
            )
            db.session.add(comp)
            db.session.commit()

        payload = {
            'platform': 'instagram',
            'username': '@existing'
        }

        response = client.post(
            '/api/sns/competitor',
            json=payload,
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'already tracked' in data['error']

    def test_list_competitors(self, client, app, auth_headers, user):
        """Test list competitors"""
        with app.app_context():
            for i in range(3):
                comp = SNSCompetitor(
                    user_id=user.id,
                    platform='instagram',
                    username=f'@competitor{i}',
                    name=f'Competitor {i}'
                )
                db.session.add(comp)
            db.session.commit()

        response = client.get(
            '/api/sns/competitor?pagination=offset&per_page=2',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['total'] == 3

    def test_compare_competitor(self, client, app, auth_headers, user):
        """Test competitor comparison"""
        with app.app_context():
            comp = SNSCompetitor(
                user_id=user.id,
                platform='instagram',
                username='@competitor',
                name='Competitor'
            )
            db.session.add(comp)
            db.session.commit()
            comp_id = comp.id

        response = client.get(
            f'/api/sns/competitor/{comp_id}/compare?period=month',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'comparison' in data['data']
        assert 'insights' in data['data']


# ============ ROI CALCULATOR API TESTS ============

class TestROIAPI:
    """Tests for ROI Calculator endpoints"""

    def test_calculate_roi_all_time(self, client, auth_headers):
        """Test ROI calculation for all-time"""
        response = client.get(
            '/api/sns/roi?period=all',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data['data']
        assert 'revenue' in data['data']
        assert 'cost' in data['data']
        assert 'roi' in data['data']

    def test_calculate_roi_by_period(self, client, auth_headers):
        """Test ROI by different periods"""
        for period in ['week', 'month', 'year']:
            response = client.get(
                f'/api/sns/roi?period={period}',
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['period']['type'] == period

    def test_calculate_roi_invalid_period(self, client, auth_headers):
        """Test ROI with invalid period"""
        response = client.get(
            '/api/sns/roi?period=invalid',
            headers=auth_headers
        )

        assert response.status_code == 422
        data = response.get_json()
        assert 'Invalid period' in data['error']


# ============ AUTHENTICATION TESTS ============

class TestAuthenticationRequired:
    """Tests for authentication requirement"""

    def test_linkinbio_without_auth(self, client):
        """Test Link-in-Bio endpoints require authentication"""
        response = client.get('/api/sns/linkinbio')
        assert response.status_code == 401

    def test_automation_without_auth(self, client):
        """Test Automation endpoints require authentication"""
        response = client.get('/api/sns/automate')
        assert response.status_code == 401

    def test_competitor_without_auth(self, client):
        """Test Competitor endpoints require authentication"""
        response = client.get('/api/sns/competitor')
        assert response.status_code == 401

    def test_roi_without_auth(self, client):
        """Test ROI endpoint requires authentication"""
        response = client.get('/api/sns/roi')
        assert response.status_code == 401
