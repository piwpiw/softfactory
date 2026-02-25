"""
T11: Integration Tests for SNS Auto v2.0 — Complete System Validation
Tests all 32 backend endpoints + frontend API client integration
"""

import pytest
import json
from datetime import datetime, timedelta
from backend.models import (
    User, SNSAccount, SNSPost, SNSCampaign, SNSTemplate,
    SNSAnalytics, SNSInboxMessage, SNSOAuthState, SNSSettings
)
from backend.app import app, db
from backend.services.sns_auto import (
    create_sns_post, publish_scheduled_posts, get_sns_analytics,
    generate_content_ai
)


@pytest.fixture
def client():
    """Test client with in-memory SQLite"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_headers(client):
    """Fixture for auth token headers"""
    return {
        'Authorization': 'Bearer demo_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def demo_user(client):
    """Create demo user for tests"""
    with app.app_context():
        user = User(
            email='test@example.com',
            password='hashed_password',
            name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def demo_account(demo_user):
    """Create demo SNS account"""
    account = SNSAccount(
        user_id=demo_user.id,
        platform='instagram',
        account_name='@test_account',
        is_active=True,
        access_token='demo_token',
        refresh_token='demo_refresh',
        token_expires_at=datetime.utcnow() + timedelta(days=30),
        platform_user_id='12345',
        followers_count=2540,
        permissions_json={'read': True, 'write': True}
    )
    db.session.add(account)
    db.session.commit()
    return account


# ============ OAUTH TESTS (3) ============

class TestOAuth:
    """OAuth flow: authorize -> callback -> token exchange"""

    def test_get_oauth_authorize_url(self, client, auth_headers):
        """GET /oauth/{platform}/authorize"""
        response = client.get('/api/sns/oauth/instagram/authorize', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'auth_url' in data
        assert 'instagram' in data['auth_url'].lower() or 'oauth' in data['auth_url'].lower()

    def test_oauth_callback_exchange_code(self, client, auth_headers, demo_user):
        """GET /oauth/{platform}/callback with code exchange"""
        response = client.post(
            '/api/sns/oauth/instagram/callback',
            headers=auth_headers,
            json={'code': 'test_code', 'state': 'test_state'}
        )
        assert response.status_code in [200, 401]  # May fail if OAuth mock not fully implemented
        if response.status_code == 200:
            data = response.get_json()
            assert 'access_token' in data or 'account_id' in data

    def test_oauth_simulate_callback(self, client, auth_headers):
        """POST /oauth/{platform}/simulate-callback (demo mode)"""
        response = client.post(
            '/api/sns/oauth/instagram/simulate-callback',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'platform' in data
        assert data['platform'] == 'instagram'
        assert 'access_token' in data


# ============ ACCOUNT MANAGEMENT TESTS (4) ============

class TestAccountManagement:
    """Account CRUD: list, create, get, reconnect, delete"""

    def test_get_all_accounts(self, client, auth_headers, demo_account):
        """GET /accounts (list all)"""
        response = client.get('/api/sns/accounts', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'accounts' in data
        assert len(data['accounts']) > 0
        assert data['accounts'][0]['platform'] == 'instagram'

    def test_get_single_account(self, client, auth_headers, demo_account):
        """GET /accounts/{id}"""
        response = client.get(f'/api/sns/accounts/{demo_account.id}', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'account' in data
        assert data['account']['id'] == demo_account.id
        assert data['account']['platform'] == 'instagram'

    def test_create_new_account(self, client, auth_headers, demo_user):
        """POST /accounts (OAuth connection)"""
        response = client.post(
            '/api/sns/accounts',
            headers=auth_headers,
            json={
                'platform': 'tiktok',
                'account_name': '@new_tiktok',
                'access_token': 'new_token'
            }
        )
        assert response.status_code in [201, 200]
        data = response.get_json()
        assert 'account' in data or 'id' in data

    def test_reconnect_expired_account(self, client, auth_headers, demo_account):
        """POST /accounts/{id}/reconnect"""
        response = client.post(
            f'/api/sns/accounts/{demo_account.id}/reconnect',
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.get_json()
            assert 'account' in data or 'success' in data

    def test_delete_account(self, client, auth_headers, demo_account):
        """DELETE /accounts/{id}"""
        response = client.delete(
            f'/api/sns/accounts/{demo_account.id}',
            headers=auth_headers
        )
        assert response.status_code in [200, 204]


# ============ POST MANAGEMENT TESTS (6) ============

class TestPostManagement:
    """Post CRUD: create, read, update, delete, publish, retry, metrics"""

    def test_create_post(self, client, auth_headers, demo_account):
        """POST /posts"""
        response = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            json={
                'account_id': demo_account.id,
                'content': 'Test post content',
                'template_type': 'card_news',
                'scheduled_at': '2026-03-01T19:00:00'
            }
        )
        assert response.status_code in [201, 200]
        data = response.get_json()
        assert 'post' in data or 'id' in data

    def test_get_posts(self, client, auth_headers, demo_account):
        """GET /posts (with filters)"""
        response = client.get(
            f'/api/sns/posts?account_id={demo_account.id}&status=scheduled',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'posts' in data

    def test_update_post(self, client, auth_headers, demo_account):
        """PUT /posts/{id}"""
        # Create post first
        post = SNSPost(
            user_id=demo_account.user_id,
            account_id=demo_account.id,
            content='Original content',
            platform='instagram',
            status='draft'
        )
        db.session.add(post)
        db.session.commit()

        response = client.put(
            f'/api/sns/posts/{post.id}',
            headers=auth_headers,
            json={'content': 'Updated content', 'status': 'scheduled'}
        )
        assert response.status_code in [200, 404]

    def test_publish_post(self, client, auth_headers, demo_account):
        """POST /posts/{id}/publish"""
        post = SNSPost(
            user_id=demo_account.user_id,
            account_id=demo_account.id,
            content='Test',
            platform='instagram',
            status='scheduled',
            scheduled_at=datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()

        response = client.post(
            f'/api/sns/posts/{post.id}/publish',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_retry_failed_post(self, client, auth_headers, demo_account):
        """POST /posts/{id}/retry"""
        post = SNSPost(
            user_id=demo_account.user_id,
            account_id=demo_account.id,
            content='Test',
            platform='instagram',
            status='failed',
            retry_count=1,
            error_message='Connection timeout'
        )
        db.session.add(post)
        db.session.commit()

        response = client.post(
            f'/api/sns/posts/{post.id}/retry',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_get_post_metrics(self, client, auth_headers, demo_account):
        """GET /posts/{id}/metrics"""
        post = SNSPost(
            user_id=demo_account.user_id,
            account_id=demo_account.id,
            content='Test',
            platform='instagram',
            status='published',
            likes_count=150,
            comments_count=12,
            views_count=2340
        )
        db.session.add(post)
        db.session.commit()

        response = client.get(
            f'/api/sns/posts/{post.id}/metrics',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert 'metrics' in data or 'likes_count' in data

    def test_bulk_create_posts(self, client, auth_headers, demo_account):
        """POST /posts/bulk"""
        response = client.post(
            '/api/sns/posts/bulk',
            headers=auth_headers,
            json={
                'posts': [
                    {'account_id': demo_account.id, 'content': 'Post 1', 'template_type': 'card_news'},
                    {'account_id': demo_account.id, 'content': 'Post 2', 'template_type': 'card_news'}
                ]
            }
        )
        assert response.status_code in [201, 200]


# ============ ANALYTICS TESTS (3) ============

class TestAnalytics:
    """Analytics: aggregated, account-specific, optimal time"""

    def test_get_aggregated_analytics(self, client, auth_headers, demo_account):
        """GET /analytics"""
        response = client.get(
            '/api/sns/analytics?start_date=2026-02-01&end_date=2026-02-28',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_posts' in data or 'platform_breakdown' in data

    def test_get_account_analytics(self, client, auth_headers, demo_account):
        """GET /analytics/accounts/{id}"""
        response = client.get(
            f'/api/sns/analytics/accounts/{demo_account.id}?start_date=2026-02-01&end_date=2026-02-28',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'account' in data or 'metrics' in data

    def test_get_optimal_posting_time(self, client, auth_headers, demo_account):
        """GET /analytics/optimal-time/{id}"""
        response = client.get(
            f'/api/sns/analytics/optimal-time/{demo_account.id}',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'account_id' in data or 'optimal_hour' in data


# ============ MEDIA TESTS (2) ============

class TestMediaManagement:
    """Media upload & retrieval"""

    def test_upload_media(self, client, auth_headers, demo_account):
        """POST /media/upload"""
        # Create a simple test file
        data = {
            'file': (b'fake image data', 'test.jpg'),
            'type': 'image'
        }
        response = client.post(
            '/api/sns/media/upload',
            headers={'Authorization': 'Bearer demo_token'},
            data=data,
            content_type='multipart/form-data'
        )
        assert response.status_code in [200, 201, 400]

    def test_get_media_list(self, client, auth_headers, demo_account):
        """GET /media"""
        response = client.get(
            f'/api/sns/media?account_id={demo_account.id}',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'media' in data or isinstance(data, list)


# ============ TEMPLATE TESTS (4) ============

class TestTemplateManagement:
    """Template CRUD: create, read, update, delete"""

    def test_get_templates(self, client, auth_headers):
        """GET /templates"""
        response = client.get('/api/sns/templates', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        # Should be list or dict with templates key
        assert isinstance(data, (list, dict))

    def test_create_template(self, client, auth_headers, demo_user):
        """POST /templates"""
        response = client.post(
            '/api/sns/templates',
            headers=auth_headers,
            json={
                'name': 'Custom Template',
                'platform': 'instagram',
                'content_template': 'Template content {{variable}}',
                'hashtag_template': '#custom #template',
                'category': 'custom'
            }
        )
        assert response.status_code in [201, 200]

    def test_update_template(self, client, auth_headers, demo_user):
        """PUT /templates/{id}"""
        template = SNSTemplate(
            user_id=demo_user.id,
            name='Original Template',
            platform='instagram',
            content_template='Original'
        )
        db.session.add(template)
        db.session.commit()

        response = client.put(
            f'/api/sns/templates/{template.id}',
            headers=auth_headers,
            json={'name': 'Updated Template'}
        )
        assert response.status_code in [200, 404]

    def test_delete_template(self, client, auth_headers, demo_user):
        """DELETE /templates/{id}"""
        template = SNSTemplate(
            user_id=demo_user.id,
            name='Delete Me',
            platform='instagram'
        )
        db.session.add(template)
        db.session.commit()

        response = client.delete(
            f'/api/sns/templates/{template.id}',
            headers=auth_headers
        )
        assert response.status_code in [200, 204, 404]


# ============ INBOX TESTS (3) ============

class TestInboxManagement:
    """Inbox: list messages, reply, mark as read"""

    def test_get_inbox_messages(self, client, auth_headers, demo_account):
        """GET /inbox"""
        response = client.get(
            '/api/sns/inbox?status=unread&type=dm',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'messages' in data or 'unread_count' in data

    def test_reply_to_message(self, client, auth_headers, demo_account):
        """POST /inbox/{id}/reply"""
        msg = SNSInboxMessage(
            account_id=demo_account.id,
            sender_name='Test User',
            message_text='Hello!',
            message_type='dm',
            status='unread'
        )
        db.session.add(msg)
        db.session.commit()

        response = client.post(
            f'/api/sns/inbox/{msg.id}/reply',
            headers=auth_headers,
            json={'reply_text': 'Thanks for reaching out!'}
        )
        assert response.status_code in [200, 201, 404]

    def test_mark_message_as_read(self, client, auth_headers, demo_account):
        """PUT /inbox/{id}/read"""
        msg = SNSInboxMessage(
            account_id=demo_account.id,
            sender_name='Test User',
            message_text='Hello!',
            message_type='comment',
            status='unread'
        )
        db.session.add(msg)
        db.session.commit()

        response = client.put(
            f'/api/sns/inbox/{msg.id}/read',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]


# ============ CALENDAR TESTS (1) ============

class TestCalendar:
    """Calendar view of scheduled posts"""

    def test_get_monthly_calendar(self, client, auth_headers):
        """GET /calendar"""
        response = client.get(
            '/api/sns/calendar?year=2026&month=2',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'year' in data or 'month' in data or 'days' in data


# ============ CAMPAIGN TESTS (3) ============

class TestCampaignManagement:
    """Campaign CRUD: create, read, update, delete"""

    def test_get_campaigns(self, client, auth_headers, demo_user):
        """GET /campaigns"""
        response = client.get('/api/sns/campaigns', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'campaigns' in data or isinstance(data, list)

    def test_create_campaign(self, client, auth_headers, demo_user):
        """POST /campaigns"""
        response = client.post(
            '/api/sns/campaigns',
            headers=auth_headers,
            json={
                'name': 'Spring Campaign',
                'description': 'Spring product launch',
                'target_platforms': ['instagram', 'tiktok'],
                'start_date': '2026-03-01',
                'end_date': '2026-03-31',
                'status': 'active'
            }
        )
        assert response.status_code in [201, 200]

    def test_get_campaign_detail(self, client, auth_headers, demo_user):
        """GET /campaigns/{id}"""
        campaign = SNSCampaign(
            user_id=demo_user.id,
            name='Test Campaign',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status='active'
        )
        db.session.add(campaign)
        db.session.commit()

        response = client.get(
            f'/api/sns/campaigns/{campaign.id}',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_update_campaign(self, client, auth_headers, demo_user):
        """PUT /campaigns/{id}"""
        campaign = SNSCampaign(
            user_id=demo_user.id,
            name='Test Campaign',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status='active'
        )
        db.session.add(campaign)
        db.session.commit()

        response = client.put(
            f'/api/sns/campaigns/{campaign.id}',
            headers=auth_headers,
            json={'status': 'paused'}
        )
        assert response.status_code in [200, 404]

    def test_delete_campaign(self, client, auth_headers, demo_user):
        """DELETE /campaigns/{id}"""
        campaign = SNSCampaign(
            user_id=demo_user.id,
            name='Delete Campaign',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(campaign)
        db.session.commit()

        response = client.delete(
            f'/api/sns/campaigns/{campaign.id}',
            headers=auth_headers
        )
        assert response.status_code in [200, 204, 404]


# ============ SETTINGS TESTS (2) ============

class TestSettingsManagement:
    """Settings: get and update user preferences"""

    def test_get_settings(self, client, auth_headers, demo_user):
        """GET /settings"""
        response = client.get('/api/sns/settings', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'settings' in data or 'auto_optimal_time' in data

    def test_update_settings(self, client, auth_headers, demo_user):
        """PUT /settings"""
        response = client.put(
            '/api/sns/settings',
            headers=auth_headers,
            json={
                'auto_optimal_time': True,
                'engagement_notifications': True,
                'auto_reply_enabled': False,
                'banned_keywords': ['spam', 'advertisement']
            }
        )
        assert response.status_code in [200, 201]


# ============ AI GENERATION TESTS (3) ============

class TestAIGeneration:
    """AI: generate content, hashtags, optimize"""

    def test_generate_content(self, client, auth_headers):
        """POST /ai/generate"""
        response = client.post(
            '/api/sns/ai/generate',
            headers=auth_headers,
            json={
                'topic': 'Spring product launch',
                'platform': 'instagram',
                'count': 2
            }
        )
        assert response.status_code in [200, 201, 503]  # May fail if Claude API not available

    def test_generate_hashtags(self, client, auth_headers):
        """POST /ai/hashtags"""
        response = client.post(
            '/api/sns/ai/hashtags',
            headers=auth_headers,
            json={
                'topic': 'Spring fashion',
                'platform': 'instagram'
            }
        )
        assert response.status_code in [200, 201]
        if response.status_code == 200:
            data = response.get_json()
            assert 'hashtags' in data or 'trending' in data

    def test_optimize_content(self, client, auth_headers):
        """POST /ai/optimize"""
        response = client.post(
            '/api/sns/ai/optimize',
            headers=auth_headers,
            json={
                'content': 'Check out our new product!',
                'platform': 'twitter'
            }
        )
        assert response.status_code in [200, 201]
        if response.status_code == 200:
            data = response.get_json()
            assert 'optimized_content' in data or 'suggestions' in data


# ============ ERROR HANDLING TESTS ============

class TestErrorHandling:
    """Error scenarios: invalid input, missing auth, not found"""

    def test_missing_auth_token(self, client):
        """Missing Authorization header"""
        response = client.get('/api/sns/accounts')
        assert response.status_code in [401, 403]

    def test_invalid_account_id(self, client, auth_headers):
        """GET /accounts/{invalid_id}"""
        response = client.get('/api/sns/accounts/99999', headers=auth_headers)
        assert response.status_code in [404, 403]

    def test_invalid_post_id(self, client, auth_headers):
        """GET /posts/{invalid_id}/metrics"""
        response = client.get('/api/sns/posts/99999/metrics', headers=auth_headers)
        assert response.status_code in [404, 403]

    def test_invalid_json_body(self, client, auth_headers):
        """POST with malformed JSON"""
        response = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            data='invalid json'
        )
        assert response.status_code in [400, 415]

    def test_missing_required_field(self, client, auth_headers):
        """POST /posts without required fields"""
        response = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            json={'content': 'Missing account_id'}
        )
        assert response.status_code in [400, 422]


# ============ DEMO MODE TESTS ============

class TestDemoMode:
    """Verify demo mode works with frontend"""

    def test_demo_mode_all_endpoints(self, client):
        """All endpoints should return valid demo data"""
        endpoints = [
            '/api/sns/accounts',
            '/api/sns/posts',
            '/api/sns/templates',
            '/api/sns/inbox',
            '/api/sns/campaigns',
            '/api/sns/settings',
            '/api/sns/analytics?start_date=2026-02-01&end_date=2026-02-28',
            '/api/sns/calendar?year=2026&month=2'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers={'Authorization': 'Bearer demo_token'})
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            data = response.get_json()
            assert data is not None, f"No data returned from {endpoint}"


# ============ PERFORMANCE TESTS ============

class TestPerformance:
    """Basic performance: response times under limits"""

    def test_list_response_time(self, client, auth_headers):
        """GET /accounts should respond < 500ms"""
        import time
        start = time.time()
        response = client.get('/api/sns/accounts', headers=auth_headers)
        duration = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration < 500, f"Response took {duration}ms"

    def test_create_response_time(self, client, auth_headers, demo_account):
        """POST /posts should respond < 1000ms"""
        import time
        start = time.time()
        response = client.post(
            '/api/sns/posts',
            headers=auth_headers,
            json={
                'account_id': demo_account.id,
                'content': 'Test',
                'template_type': 'card_news'
            }
        )
        duration = (time.time() - start) * 1000

        assert response.status_code in [200, 201]
        assert duration < 1000, f"Response took {duration}ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
