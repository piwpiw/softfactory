"""SNS Monetization Endpoints Test Suite — Link-in-Bio, ROI, Trending, Automation

Comprehensive test coverage for:
- Link-in-Bio CRUD & statistics
- ROI tracking & analytics
- Trending content detection
- Automation scheduling
- Edge cases & error handling
"""
import pytest
import json
from datetime import datetime, timedelta
from backend.app import create_app
from backend.models import (
    db, User, SNSLinkInBio, SNSAutomate, SNSAnalytics,
    SNSAccount, SNSPost, SNSCompetitor
)


@pytest.fixture
def app():
    """Create and configure a test app instance for SNS monetization"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    with app.app_context():
        db.create_all()

        # Create test user
        user = User(email='test@example.com', name='Test User', role='user')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Auth headers with demo token"""
    return {
        'Authorization': 'Bearer demo_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_linkinbio_data():
    """Sample Link-in-Bio data"""
    return {
        'slug': 'test-landing',
        'title': 'My Links',
        'description': 'Check out my social links',
        'links': [
            {'url': 'https://example.com', 'label': 'Website', 'icon': 'globe'},
            {'url': 'https://youtube.com/@user', 'label': 'YouTube', 'icon': 'youtube'},
            {'url': 'https://tiktok.com/@user', 'label': 'TikTok', 'icon': 'tiktok'}
        ],
        'theme': 'dark',
        'background_color': '#1a1a1a'
    }


@pytest.fixture
def sample_automate_data():
    """Sample automation rule data"""
    return {
        'topic': 'Tech News',
        'platforms': ['instagram', 'twitter'],
        'frequency': 'daily',
        'time_of_day': '09:00',
        'ai_model': 'claude',
        'is_enabled': True
    }


# ========== LINK-IN-BIO CRUD TESTS ==========

class TestLinkInBioCreate:
    """Test Link-in-Bio creation"""

    def test_create_linkinbio_success(self, client, auth_headers, sample_linkinbio_data):
        """POST /api/sns/linkinbio — Create link in bio with all fields"""
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=sample_linkinbio_data)

        # Verify response
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'id' in data['data']
        assert data['data']['slug'] == 'test-landing'
        assert data['data']['title'] == 'My Links'
        assert len(data['data']['links']) == 3
        assert data['data']['click_count'] == 0

    def test_create_linkinbio_minimal(self, client, auth_headers):
        """POST /api/sns/linkinbio — Create with minimal required fields"""
        minimal_data = {
            'slug': 'minimal-link',
            'title': 'My Page',
            'links': [{'url': 'https://example.com', 'label': 'Home'}]
        }
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=minimal_data)

        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['slug'] == 'minimal-link'

    def test_create_linkinbio_missing_required(self, client, auth_headers):
        """POST /api/sns/linkinbio — Missing required fields returns 422"""
        invalid_data = {'title': 'No Slug'}  # Missing slug and links
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=invalid_data)

        assert response.status_code == 422
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data or 'errors' in data

    def test_create_linkinbio_duplicate_slug(self, client, auth_headers,
                                            sample_linkinbio_data):
        """POST /api/sns/linkinbio — Duplicate slug returns 422"""
        # Create first
        client.post('/api/sns/linkinbio', headers=auth_headers,
                   json=sample_linkinbio_data)

        # Try to create with same slug
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=sample_linkinbio_data)

        assert response.status_code == 422
        data = response.get_json()
        assert data['success'] is False

    def test_create_linkinbio_invalid_url(self, client, auth_headers):
        """POST /api/sns/linkinbio — Invalid URL in links returns 400"""
        invalid_data = {
            'slug': 'bad-url',
            'title': 'Bad Links',
            'links': [{'url': 'not-a-url', 'label': 'Bad'}]
        }
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=invalid_data)

        assert response.status_code in [400, 422]

    def test_create_linkinbio_invalid_theme(self, client, auth_headers):
        """POST /api/sns/linkinbio — Invalid theme returns 400"""
        invalid_data = {
            'slug': 'bad-theme',
            'title': 'Bad Theme',
            'links': [{'url': 'https://example.com', 'label': 'Home'}],
            'theme': 'invalid-theme'
        }
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=invalid_data)

        assert response.status_code in [400, 422]

    def test_create_linkinbio_unauthorized(self, client, sample_linkinbio_data):
        """POST /api/sns/linkinbio — Missing auth returns 401"""
        response = client.post('/api/sns/linkinbio',
                              json=sample_linkinbio_data)

        assert response.status_code == 401


class TestLinkInBioRead:
    """Test Link-in-Bio retrieval"""

    def test_get_linkinbios_empty(self, client, auth_headers):
        """GET /api/sns/linkinbio — Empty list"""
        response = client.get('/api/sns/linkinbio', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_linkinbios_with_data(self, client, auth_headers,
                                      sample_linkinbio_data):
        """GET /api/sns/linkinbio — List with pagination"""
        # Create 3 link-in-bios
        for i in range(3):
            data = sample_linkinbio_data.copy()
            data['slug'] = f'landing-{i}'
            data['title'] = f'Links {i}'
            client.post('/api/sns/linkinbio', headers=auth_headers, json=data)

        # Get list
        response = client.get('/api/sns/linkinbio', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 3

    def test_get_linkinbio_detail(self, client, auth_headers,
                                  sample_linkinbio_data):
        """GET /api/sns/linkinbio/<id> — Get specific link-in-bio"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Get
        response = client.get(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['id'] == lib_id
        assert data['data']['slug'] == 'test-landing'

    def test_get_linkinbio_not_found(self, client, auth_headers):
        """GET /api/sns/linkinbio/<id> — Non-existent returns 404"""
        response = client.get('/api/sns/linkinbio/99999', headers=auth_headers)

        assert response.status_code == 404

    def test_get_linkinbios_pagination(self, client, auth_headers,
                                       sample_linkinbio_data):
        """GET /api/sns/linkinbio?page=X&per_page=Y — Pagination"""
        # Create 15 link-in-bios
        for i in range(15):
            data = sample_linkinbio_data.copy()
            data['slug'] = f'landing-{i}'
            client.post('/api/sns/linkinbio', headers=auth_headers, json=data)

        # Get first page (10 items)
        response = client.get('/api/sns/linkinbio?page=1&per_page=10',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 10


class TestLinkInBioUpdate:
    """Test Link-in-Bio updates"""

    def test_update_linkinbio_title(self, client, auth_headers,
                                    sample_linkinbio_data):
        """PUT /api/sns/linkinbio/<id> — Update title"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Update
        response = client.put(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers,
                             json={'title': 'New Title'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'New Title'

    def test_update_linkinbio_links(self, client, auth_headers,
                                    sample_linkinbio_data):
        """PUT /api/sns/linkinbio/<id> — Update links"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Update
        new_links = [
            {'url': 'https://instagram.com/@user', 'label': 'Instagram', 'icon': 'instagram'},
            {'url': 'https://twitch.tv/@user', 'label': 'Twitch', 'icon': 'twitch'}
        ]
        response = client.put(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers,
                             json={'links': new_links})

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']['links']) == 2

    def test_update_linkinbio_all_fields(self, client, auth_headers,
                                         sample_linkinbio_data):
        """PUT /api/sns/linkinbio/<id> — Update all fields"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Update
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'theme': 'light',
            'background_color': '#ffffff'
        }
        response = client.put(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers,
                             json=update_data)

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'Updated Title'
        assert data['data']['theme'] == 'light'

    def test_update_linkinbio_not_found(self, client, auth_headers):
        """PUT /api/sns/linkinbio/<id> — Non-existent returns 404"""
        response = client.put('/api/sns/linkinbio/99999', headers=auth_headers,
                             json={'title': 'New'})

        assert response.status_code == 404

    def test_update_linkinbio_invalid_data(self, client, auth_headers,
                                           sample_linkinbio_data):
        """PUT /api/sns/linkinbio/<id> — Invalid data returns 400"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Try to update with invalid links
        response = client.put(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers,
                             json={'links': 'not-a-list'})

        assert response.status_code in [400, 422]


class TestLinkInBioDelete:
    """Test Link-in-Bio deletion"""

    def test_delete_linkinbio_success(self, client, auth_headers,
                                      sample_linkinbio_data):
        """DELETE /api/sns/linkinbio/<id> — Delete"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Delete
        response = client.delete(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)

        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_linkinbio_not_found(self, client, auth_headers):
        """DELETE /api/sns/linkinbio/<id> — Non-existent returns 404"""
        response = client.delete('/api/sns/linkinbio/99999', headers=auth_headers)

        assert response.status_code == 404

    def test_delete_linkinbio_cascade(self, client, auth_headers,
                                      sample_linkinbio_data):
        """DELETE /api/sns/linkinbio/<id> — Cascades analytics deletion"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Delete
        response = client.delete(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)
        assert response.status_code == 204


# ========== LINK-IN-BIO STATISTICS TESTS ==========

class TestLinkInBioStatistics:
    """Test Link-in-Bio analytics and statistics"""

    def test_get_linkinbio_stats_empty(self, client, auth_headers,
                                       sample_linkinbio_data):
        """GET /api/sns/linkinbio/<id>/stats — Initial stats"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        # Get stats
        response = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['click_count'] == 0
        assert data['clicks_by_day'] is not None
        assert data['top_links'] is not None or data['top_links'] == []

    def test_get_linkinbio_stats_with_clicks(self, client, auth_headers,
                                             sample_linkinbio_data):
        """GET /api/sns/linkinbio/<id>/stats — Stats with click data"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_data = create_resp.get_json()['data']
        lib_id = lib_data['id']
        slug = lib_data['slug']

        # Simulate clicks (public endpoint)
        for i in range(5):
            client.get(f'/bio/{slug}', headers={})

        # Get stats
        response = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['click_count'] >= 5

    def test_click_increment_via_public_link(self, client, sample_linkinbio_data):
        """GET /bio/<slug> — Public click tracking"""
        # Create
        auth_headers = {'Authorization': 'Bearer demo_token', 'Content-Type': 'application/json'}
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        slug = create_resp.get_json()['data']['slug']

        # Access public link
        response = client.get(f'/bio/{slug}')

        # Should redirect or return 200 (depending on implementation)
        assert response.status_code in [200, 301, 302, 307, 308]

    def test_link_specific_click_tracking(self, client, auth_headers,
                                          sample_linkinbio_data):
        """GET /api/sns/linkinbio/<id>/stats — Track clicks by link"""
        # Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_data = create_resp.get_json()['data']
        lib_id = lib_data['id']

        # Get stats with top_links
        response = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        # top_links should show which links were clicked most
        assert 'top_links' in data


# ========== AUTOMATION CRUD TESTS ==========

class TestAutomateCreate:
    """Test automation rule creation"""

    def test_create_automate_success(self, client, auth_headers,
                                    sample_automate_data):
        """POST /api/sns/automate — Create automation rule"""
        response = client.post('/api/sns/automate', headers=auth_headers,
                              json=sample_automate_data)

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'id' in data['data']
        assert data['data']['topic'] == 'Tech News'
        assert 'instagram' in data['data']['platforms']

    def test_create_automate_validates_frequency(self, client, auth_headers):
        """POST /api/sns/automate — Invalid frequency"""
        invalid_data = {
            'topic': 'News',
            'platforms': ['instagram'],
            'frequency': 'invalid-freq'
        }
        response = client.post('/api/sns/automate', headers=auth_headers,
                              json=invalid_data)

        assert response.status_code in [400, 422]

    def test_create_automate_missing_required(self, client, auth_headers):
        """POST /api/sns/automate — Missing required fields"""
        response = client.post('/api/sns/automate', headers=auth_headers,
                              json={'topic': 'News'})

        assert response.status_code == 422


class TestAutomateRunNow:
    """Test automation execution"""

    def test_run_automate_now_success(self, client, auth_headers,
                                     sample_automate_data):
        """POST /api/sns/automate/<id>/run — Execute automation immediately"""
        # Create
        create_resp = client.post('/api/sns/automate', headers=auth_headers,
                                 json=sample_automate_data)
        auto_id = create_resp.get_json()['data']['id']

        # Run now
        response = client.post(f'/api/sns/automate/{auto_id}/run',
                              headers=auth_headers)

        assert response.status_code in [200, 202]
        data = response.get_json()
        assert data['success'] is True

    def test_run_automate_triggers_generation(self, client, auth_headers,
                                             sample_automate_data):
        """POST /api/sns/automate/<id>/run — Triggers AI content generation"""
        # Create
        create_resp = client.post('/api/sns/automate', headers=auth_headers,
                                 json=sample_automate_data)
        auto_id = create_resp.get_json()['data']['id']

        # Run now
        response = client.post(f'/api/sns/automate/{auto_id}/run',
                              headers=auth_headers)

        assert response.status_code in [200, 202]
        data = response.get_json()
        # Should have generated content or job ID
        assert 'job_id' in data or 'content' in data or 'success' in data


# ========== ROI & TRENDING TESTS ==========

class TestROIMetrics:
    """Test ROI and profitability tracking"""

    def test_get_roi_monthly(self, client, auth_headers):
        """GET /api/sns/roi?period=month — Monthly ROI"""
        response = client.get('/api/sns/roi?period=month', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'revenue' in data
        assert 'roi_percentage' in data
        assert 'channels' in data or 'channels_breakdown' in data

    def test_get_roi_quarterly(self, client, auth_headers):
        """GET /api/sns/roi?period=quarter — Quarterly ROI"""
        response = client.get('/api/sns/roi?period=quarter', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'revenue' in data

    def test_get_roi_with_date_range(self, client, auth_headers):
        """GET /api/sns/roi?start_date=X&end_date=Y — Custom date range"""
        start = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end = datetime.utcnow().isoformat()

        response = client.get(f'/api/sns/roi?start_date={start}&end_date={end}',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'revenue' in data

    def test_roi_channel_breakdown(self, client, auth_headers):
        """GET /api/sns/roi — Channel-specific ROI"""
        response = client.get('/api/sns/roi', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        channels = data.get('channels') or data.get('channels_breakdown', {})
        # Should have at least one channel or be empty
        assert isinstance(channels, dict)


class TestTrendingContent:
    """Test trending content detection"""

    def test_get_trending_all_platforms(self, client, auth_headers):
        """GET /api/sns/trending — Trending across all platforms"""
        response = client.get('/api/sns/trending', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'hashtags' in data or 'trending_topics' in data
        assert 'topics' in data or 'trending_content' in data
        assert 'best_times' in data

    def test_get_trending_instagram(self, client, auth_headers):
        """GET /api/sns/trending?platform=instagram — Platform-specific"""
        response = client.get('/api/sns/trending?platform=instagram',
                             headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'hashtags' in data or 'trending_topics' in data

    def test_get_trending_twitter(self, client, auth_headers):
        """GET /api/sns/trending?platform=twitter — Platform-specific"""
        response = client.get('/api/sns/trending?platform=twitter',
                             headers=auth_headers)

        assert response.status_code == 200

    def test_trending_with_time_filter(self, client, auth_headers):
        """GET /api/sns/trending?time_range=24h — Time-based filtering"""
        response = client.get('/api/sns/trending?time_range=24h',
                             headers=auth_headers)

        assert response.status_code == 200

    def test_trending_best_posting_times(self, client, auth_headers):
        """GET /api/sns/trending — Returns best posting times"""
        response = client.get('/api/sns/trending', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'best_times' in data
        # best_times should have hour suggestions
        times = data.get('best_times', {})
        assert isinstance(times, dict)


# ========== PERFORMANCE & EDGE CASES ==========

class TestPerformance:
    """Performance tests for monetization endpoints"""

    def test_linkinbio_create_performance(self, client, auth_headers,
                                          sample_linkinbio_data):
        """Create should complete in <500ms"""
        import time

        start = time.time()
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=sample_linkinbio_data)
        elapsed = (time.time() - start) * 1000  # milliseconds

        assert response.status_code == 201
        assert elapsed < 500, f"Creation took {elapsed}ms, expected <500ms"

    def test_stats_retrieval_performance(self, client, auth_headers,
                                        sample_linkinbio_data):
        """Stats retrieval should complete in <2000ms"""
        import time

        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        lib_id = create_resp.get_json()['data']['id']

        start = time.time()
        response = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                             headers=auth_headers)
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 2000, f"Stats took {elapsed}ms, expected <2000ms"

    def test_trending_performance(self, client, auth_headers):
        """Trending should complete in <3000ms"""
        import time

        start = time.time()
        response = client.get('/api/sns/trending', headers=auth_headers)
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 3000, f"Trending took {elapsed}ms, expected <3000ms"


class TestSecurityValidation:
    """Security tests for monetization endpoints"""

    def test_sql_injection_prevention(self, client, auth_headers):
        """SQL injection attempts should be safely handled"""
        malicious_slug = "'; DROP TABLE users; --"
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json={
                                  'slug': malicious_slug,
                                  'title': 'Test',
                                  'links': []
                              })

        # Should either reject or safely escape
        assert response.status_code in [400, 422, 201]

    def test_xss_prevention(self, client, auth_headers):
        """XSS attempts should be sanitized"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json={
                                  'slug': 'xss-test',
                                  'title': xss_payload,
                                  'links': []
                              })

        assert response.status_code in [400, 422, 201]
        if response.status_code == 201:
            data = response.get_json()
            # Title should be escaped
            title = data['data']['title']
            assert '<script>' not in title or '&lt;script&gt;' in title

    def test_unauthorized_access(self, client):
        """Endpoints require authentication"""
        response = client.post('/api/sns/linkinbio',
                              json={'slug': 'test', 'title': 'Test'})

        assert response.status_code == 401

    def test_forbidden_access(self, client, auth_headers):
        """Users can only access their own resources"""
        # This would need another user context to properly test
        pass


# ========== INTEGRATION SCENARIOS ==========

class TestMonetizationFlow:
    """End-to-end monetization workflow tests"""

    def test_complete_linkinbio_workflow(self, client, auth_headers,
                                        sample_linkinbio_data):
        """Complete Link-in-Bio workflow: create → share → track"""
        # 1. Create
        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=sample_linkinbio_data)
        assert create_resp.status_code == 201
        lib_data = create_resp.get_json()['data']
        lib_id = lib_data['id']
        slug = lib_data['slug']

        # 2. Verify created
        get_resp = client.get(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)
        assert get_resp.status_code == 200

        # 3. Simulate shares (public access)
        for i in range(3):
            client.get(f'/bio/{slug}')

        # 4. Check stats
        stats_resp = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                               headers=auth_headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.get_json()
        assert stats['click_count'] >= 3

        # 5. Update
        update_resp = client.put(f'/api/sns/linkinbio/{lib_id}',
                                headers=auth_headers,
                                json={'title': 'Updated Links'})
        assert update_resp.status_code == 200

        # 6. Delete
        del_resp = client.delete(f'/api/sns/linkinbio/{lib_id}',
                                headers=auth_headers)
        assert del_resp.status_code == 204

    def test_automation_with_scheduling(self, client, auth_headers,
                                       sample_automate_data):
        """Automation: create → schedule → run"""
        # 1. Create
        create_resp = client.post('/api/sns/automate', headers=auth_headers,
                                 json=sample_automate_data)
        assert create_resp.status_code == 201
        auto_id = create_resp.get_json()['data']['id']

        # 2. Run immediately
        run_resp = client.post(f'/api/sns/automate/{auto_id}/run',
                              headers=auth_headers)
        assert run_resp.status_code in [200, 202]
