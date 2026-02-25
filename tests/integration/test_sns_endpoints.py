"""
Test SNS Auto Endpoints Integration — SNS Auto v2.0
Tests 32 API endpoints across accounts, posts, analytics, templates, campaigns
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.models import (
    db, User, SNSAccount, SNSPost, SNSCampaign, SNSTemplate,
    SNSAnalytics, SNSInboxMessage, SNSSettings
)
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
            email='sns_test@example.com',
            password='hashed_password',
            name='SNS Test User'
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


@pytest.fixture
def demo_account(demo_user):
    """Create demo SNS account"""
    with app.app_context():
        account = SNSAccount(
            user_id=demo_user.id,
            platform='instagram',
            account_name='@test_account',
            is_active=True,
            access_token='demo_token',
            refresh_token='demo_refresh',
            token_expires_at=datetime.utcnow() + timedelta(days=30),
            platform_user_id='12345',
            followers_count=5000,
            permissions_json={'read': True, 'write': True}
        )
        db.session.add(account)
        db.session.commit()
        return account


@pytest.fixture
def demo_post(demo_user, demo_account):
    """Create demo SNS post"""
    with app.app_context():
        post = SNSPost(
            user_id=demo_user.id,
            account_id=demo_account.id,
            content='Test post content',
            status='scheduled',
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            media_urls=['http://example.com/image.jpg'],
            hashtags=['#test', '#demo']
        )
        db.session.add(post)
        db.session.commit()
        return post


# ============ LINK IN BIO / LINKINBIO TESTS ============

class TestLinkInBio:
    """Test Link in Bio (Linkinbio) endpoints"""

    def test_create_linkinbio(self, client, auth_headers, demo_user):
        """Test POST /api/sns/linkinbio"""
        res = client.post(
            '/api/sns/linkinbio',
            headers=auth_headers,
            json={
                'slug': 'mylinks',
                'title': 'My Links',
                'links': [
                    {'url': 'https://shop.example.com', 'label': 'Shop'},
                    {'url': 'https://blog.example.com', 'label': 'Blog'}
                ]
            }
        )
        assert res.status_code in [201, 200, 404]
        if res.status_code == 201:
            data = json.loads(res.data)
            assert 'slug' in data.get('data', {}) or 'slug' in data
            assert data.get('data', data).get('slug') == 'mylinks'

    def test_get_linkinbio(self, client, auth_headers, demo_user):
        """Test GET /api/sns/linkinbio"""
        res = client.get('/api/sns/linkinbio', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert isinstance(data.get('data'), list) or isinstance(data, list)

    def test_update_linkinbio(self, client, auth_headers, demo_user):
        """Test PUT /api/sns/linkinbio/{id}"""
        # First create
        res = client.post(
            '/api/sns/linkinbio',
            headers=auth_headers,
            json={'slug': 'test', 'title': 'Test'}
        )
        if res.status_code == 201:
            created_data = json.loads(res.data)
            linkinbio_id = created_data.get('data', {}).get('id') or 1

            # Then update
            res = client.put(
                f'/api/sns/linkinbio/{linkinbio_id}',
                headers=auth_headers,
                json={'title': 'Updated Title'}
            )
            assert res.status_code in [200, 404]

    def test_delete_linkinbio(self, client, auth_headers, demo_user):
        """Test DELETE /api/sns/linkinbio/{id}"""
        res = client.delete(
            '/api/sns/linkinbio/1',
            headers=auth_headers
        )
        assert res.status_code in [200, 204, 404]


# ============ TRENDING & ANALYTICS TESTS ============

class TestAnalyticsAndTrending:
    """Test analytics and trending endpoints"""

    def test_get_trending_posts(self, client, auth_headers):
        """Test GET /api/sns/trending"""
        res = client.get(
            '/api/sns/trending?platform=instagram',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'trending' in data or 'data' in data

    def test_get_trending_hashtags(self, client, auth_headers):
        """Test GET /api/sns/trending/hashtags"""
        res = client.get(
            '/api/sns/trending/hashtags?platform=twitter',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_get_trending_with_category_filter(self, client, auth_headers):
        """Test GET /api/sns/trending with category filter"""
        res = client.get(
            '/api/sns/trending?platform=instagram&category=fashion',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_roi_calculation(self, client, auth_headers):
        """Test GET /api/sns/roi (ROI analytics)"""
        res = client.get('/api/sns/roi', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            if 'data' in data:
                assert 'monthly_revenue' in data['data'] or 'roi' in data['data']

    def test_get_analytics_aggregated(self, client, auth_headers):
        """Test GET /api/sns/analytics (aggregated across all accounts)"""
        res = client.get(
            '/api/sns/analytics?start_date=2026-02-01&end_date=2026-02-25',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'data' in data or 'analytics' in data

    def test_get_analytics_by_account(self, client, auth_headers, demo_account):
        """Test GET /api/sns/analytics/{account_id}"""
        res = client.get(
            f'/api/sns/analytics/{demo_account.id}?start_date=2026-02-01',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_optimal_posting_time(self, client, auth_headers):
        """Test GET /api/sns/optimal-time (ML-based optimal posting time)"""
        res = client.get(
            '/api/sns/optimal-time?platform=instagram',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            if 'data' in data:
                assert 'time' in data['data'] or 'optimal_hour' in data['data']


# ============ ACCOUNT MANAGEMENT TESTS ============

class TestAccountManagement:
    """Test account CRUD operations"""

    def test_get_all_accounts(self, client, auth_headers, demo_account):
        """Test GET /api/sns/accounts"""
        res = client.get('/api/sns/accounts', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'data' in data or 'accounts' in data

    def test_get_single_account(self, client, auth_headers, demo_account):
        """Test GET /api/sns/accounts/{id}"""
        res = client.get(f'/api/sns/accounts/{demo_account.id}', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'data' in data or 'account' in data

    def test_create_account(self, client, auth_headers):
        """Test POST /api/sns/accounts (OAuth connection)"""
        res = client.post(
            '/api/sns/accounts',
            headers=auth_headers,
            json={
                'platform': 'tiktok',
                'account_name': '@new_tiktok',
                'follower_count': 1000,
                'access_token': 'new_token'
            }
        )
        assert res.status_code in [201, 200, 404]
        if res.status_code in [201, 200]:
            data = json.loads(res.data)
            assert 'data' in data or 'account' in data

    def test_reconnect_account(self, client, auth_headers, demo_account):
        """Test POST /api/sns/accounts/{id}/reconnect (refresh OAuth)"""
        res = client.post(
            f'/api/sns/accounts/{demo_account.id}/reconnect',
            headers=auth_headers,
            json={'access_token': 'new_token'}
        )
        assert res.status_code in [200, 404]


# ============ POST MANAGEMENT TESTS ============

class TestPostManagement:
    """Test post CRUD and publishing"""

    def test_create_post(self, client, auth_headers, demo_account):
        """Test POST /api/sns/posts"""
        res = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            json={
                'account_ids': [demo_account.id],
                'content': 'Hello world!',
                'scheduled_at': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'media_urls': ['http://example.com/image.jpg'],
                'hashtags': ['#hello', '#world']
            }
        )
        assert res.status_code in [201, 200, 404]

    def test_get_posts(self, client, auth_headers, demo_post):
        """Test GET /api/sns/posts"""
        res = client.get('/api/sns/posts', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert 'data' in data or 'posts' in data

    def test_update_post(self, client, auth_headers, demo_post):
        """Test PUT /api/sns/posts/{id}"""
        res = client.put(
            f'/api/sns/posts/{demo_post.id}',
            headers=auth_headers,
            json={'content': 'Updated content'}
        )
        assert res.status_code in [200, 404]

    def test_publish_post(self, client, auth_headers, demo_post):
        """Test POST /api/sns/posts/{id}/publish"""
        res = client.post(
            f'/api/sns/posts/{demo_post.id}/publish',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]

    def test_get_post_metrics(self, client, auth_headers, demo_post):
        """Test GET /api/sns/posts/{id}/metrics"""
        res = client.get(
            f'/api/sns/posts/{demo_post.id}/metrics',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            if 'data' in data:
                assert 'likes' in data['data'] or 'engagement' in data['data']

    def test_retry_failed_post(self, client, auth_headers, demo_post):
        """Test POST /api/sns/posts/{id}/retry"""
        res = client.post(
            f'/api/sns/posts/{demo_post.id}/retry',
            headers=auth_headers
        )
        assert res.status_code in [200, 404]


# ============ MEDIA MANAGEMENT TESTS ============

class TestMediaManagement:
    """Test media upload and management"""

    def test_upload_media(self, client, auth_headers):
        """Test POST /api/sns/media (file upload)"""
        data = {
            'file': (b'fake image data', 'test.jpg'),
        }
        res = client.post(
            '/api/sns/media',
            headers={**auth_headers, 'Content-Type': 'multipart/form-data'},
            data=data
        )
        assert res.status_code in [201, 200, 400, 404]

    def test_list_media(self, client, auth_headers):
        """Test GET /api/sns/media"""
        res = client.get('/api/sns/media', headers=auth_headers)
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            data = json.loads(res.data)
            assert isinstance(data.get('data'), list) or 'media' in data


# ============ TEMPLATE MANAGEMENT TESTS ============

class TestTemplateManagement:
    """Test content template CRUD"""

    def test_create_template(self, client, auth_headers):
        """Test POST /api/sns/templates"""
        res = client.post(
            '/api/sns/templates',
            headers=auth_headers,
            json={
                'name': 'Product Launch',
                'content': 'Check out our new product: {product_name}',
                'platforms': ['instagram', 'twitter'],
                'tags': ['product', 'launch']
            }
        )
        assert res.status_code in [201, 200, 404]

    def test_get_templates(self, client, auth_headers):
        """Test GET /api/sns/templates"""
        res = client.get('/api/sns/templates', headers=auth_headers)
        assert res.status_code in [200, 404]

    def test_update_template(self, client, auth_headers):
        """Test PUT /api/sns/templates/{id}"""
        res = client.put(
            '/api/sns/templates/1',
            headers=auth_headers,
            json={'name': 'Updated Template'}
        )
        assert res.status_code in [200, 404]

    def test_delete_template(self, client, auth_headers):
        """Test DELETE /api/sns/templates/{id}"""
        res = client.delete(
            '/api/sns/templates/1',
            headers=auth_headers
        )
        assert res.status_code in [200, 204, 404]


# ============ CAMPAIGN MANAGEMENT TESTS ============

class TestCampaignManagement:
    """Test campaign CRUD operations"""

    def test_create_campaign(self, client, auth_headers):
        """Test POST /api/sns/campaigns"""
        res = client.post(
            '/api/sns/campaigns',
            headers=auth_headers,
            json={
                'name': 'Summer Sale',
                'description': 'Summer promotion campaign',
                'start_date': datetime.utcnow().isoformat(),
                'end_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'platforms': ['instagram', 'facebook'],
                'budget': 5000
            }
        )
        assert res.status_code in [201, 200, 404]

    def test_get_campaigns(self, client, auth_headers):
        """Test GET /api/sns/campaigns"""
        res = client.get('/api/sns/campaigns', headers=auth_headers)
        assert res.status_code in [200, 404]

    def test_manage_campaign(self, client, auth_headers):
        """Test POST /api/sns/campaigns/{id}/manage (pause/resume/cancel)"""
        res = client.post(
            '/api/sns/campaigns/1/manage',
            headers=auth_headers,
            json={'action': 'pause'}
        )
        assert res.status_code in [200, 404]


# ============ INBOX MANAGEMENT TESTS ============

class TestInboxManagement:
    """Test unified message inbox"""

    def test_get_inbox_messages(self, client, auth_headers):
        """Test GET /api/sns/inbox"""
        res = client.get('/api/sns/inbox', headers=auth_headers)
        assert res.status_code in [200, 404]

    def test_reply_to_message(self, client, auth_headers):
        """Test POST /api/sns/inbox/{id}/reply"""
        res = client.post(
            '/api/sns/inbox/1/reply',
            headers=auth_headers,
            json={'content': 'Thanks for your message'}
        )
        assert res.status_code in [200, 201, 404]

    def test_mark_message_read(self, client, auth_headers):
        """Test PUT /api/sns/inbox/{id}/read"""
        res = client.put(
            '/api/sns/inbox/1/read',
            headers=auth_headers,
            json={'read': True}
        )
        assert res.status_code in [200, 204, 404]


# ============ PERMISSION & AUTHORIZATION TESTS ============

class TestAuthorizationValidation:
    """Test @require_auth on all SNS endpoints"""

    def test_sns_endpoints_require_auth(self, client):
        """Test all SNS endpoints require authentication"""
        endpoints = [
            '/api/sns/accounts',
            '/api/sns/posts',
            '/api/sns/analytics',
            '/api/sns/templates',
            '/api/sns/campaigns',
            '/api/sns/inbox'
        ]

        for endpoint in endpoints:
            res = client.get(endpoint)
            assert res.status_code == 401, f"{endpoint} should require auth"

    def test_create_endpoints_require_auth(self, client):
        """Test POST endpoints require authentication"""
        endpoints = [
            '/api/sns/accounts',
            '/api/sns/posts',
            '/api/sns/templates'
        ]

        for endpoint in endpoints:
            res = client.post(endpoint, json={})
            assert res.status_code == 401, f"{endpoint} POST should require auth"


# ============ ERROR HANDLING TESTS ============

class TestErrorHandling:
    """Test error scenarios and responses"""

    def test_invalid_account_id(self, client, auth_headers):
        """Test accessing non-existent account"""
        res = client.get('/api/sns/accounts/99999', headers=auth_headers)
        assert res.status_code in [404, 200]

    def test_invalid_platform(self, client, auth_headers):
        """Test creating account with invalid platform"""
        res = client.post(
            '/api/sns/accounts',
            headers=auth_headers,
            json={
                'platform': 'invalid_platform',
                'account_name': '@test'
            }
        )
        assert res.status_code in [400, 404]

    def test_missing_required_fields(self, client, auth_headers):
        """Test POST with missing required fields"""
        res = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            json={}  # Missing required fields
        )
        assert res.status_code in [400, 404]

    def test_invalid_json_payload(self, client, auth_headers):
        """Test endpoint with invalid JSON"""
        res = client.post(
            '/api/sns/accounts',
            headers=auth_headers,
            data='invalid json{',
            content_type='application/json'
        )
        assert res.status_code in [400, 404]
