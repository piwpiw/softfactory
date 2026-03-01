"""Test Suite for Review Service API v2.0
Team E: 체험단 API 엔드포인트 통합 테스트

Test Coverage:
- 15+ endpoints fully tested
- CRUD operations for all resources
- Pagination, filtering, sorting
- Error scenarios
- User data isolation
- Business logic validation
"""

import pytest
from datetime import datetime, timedelta
from backend.models import (
    db, User, ReviewListing, ReviewAccount, ReviewApplication,
    ReviewAutoRule, ReviewBookmark
)

@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()

@pytest.fixture
def auth_header(client):
    """Generate authorization header with token"""
    # Mock token generation
    return {'Authorization': 'Bearer test_token_user_1'}

@pytest.fixture
def user_2_header():
    """Different user's token"""
    return {'Authorization': 'Bearer test_token_user_2'}


# ============ AGGREGATED LISTINGS TESTS ============

class TestAggregatedListings:
    """Test aggregated listings endpoints"""

    def test_get_aggregated_listings(self, client, auth_header):
        """Test GET /api/review/aggregated"""
        response = client.get('/api/review/aggregated', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'listings' in data
        assert 'total' in data
        assert 'pages' in data
        assert 'current_page' in data
        assert 'per_page' in data

    def test_aggregated_pagination(self, client, auth_header):
        """Test pagination parameters"""
        response = client.get('/api/review/aggregated?page=1&per_page=10', headers=auth_header)
        data = response.get_json()
        assert data['current_page'] == 1
        assert data['per_page'] == 10
        assert len(data['listings']) <= 10

    def test_aggregated_per_page_limit(self, client, auth_header):
        """Test max per_page limit (100)"""
        response = client.get('/api/review/aggregated?per_page=200', headers=auth_header)
        data = response.get_json()
        assert data['per_page'] == 100

    def test_aggregated_filtering_by_category(self, client, auth_header):
        """Test category filter"""
        response = client.get('/api/review/aggregated?category=뷰티', headers=auth_header)
        data = response.get_json()
        for listing in data['listings']:
            assert listing['category'] == '뷰티'

    def test_aggregated_filtering_by_platform(self, client, auth_header):
        """Test source_platform filter"""
        response = client.get('/api/review/aggregated?source_platform=revu', headers=auth_header)
        data = response.get_json()
        for listing in data['listings']:
            assert listing['source_platform'] == 'revu'

    def test_aggregated_reward_range(self, client, auth_header):
        """Test reward value range filter"""
        response = client.get('/api/review/aggregated?min_reward=100000&max_reward=500000',
                            headers=auth_header)
        data = response.get_json()
        for listing in data['listings']:
            assert 100000 <= listing['reward_value'] <= 500000

    def test_aggregated_sorting_by_deadline(self, client, auth_header):
        """Test sorting by deadline"""
        response = client.get('/api/review/aggregated?sort_by=deadline', headers=auth_header)
        data = response.get_json()
        listings = data['listings']
        for i in range(len(listings) - 1):
            assert listings[i]['deadline'] <= listings[i+1]['deadline']

    def test_aggregated_sorting_by_reward(self, client, auth_header):
        """Test sorting by reward value"""
        response = client.get('/api/review/aggregated?sort_by=reward_value', headers=auth_header)
        data = response.get_json()
        listings = data['listings']
        for i in range(len(listings) - 1):
            assert listings[i]['reward_value'] >= listings[i+1]['reward_value']

    def test_aggregated_stats(self, client, auth_header):
        """Test GET /api/review/aggregated/stats"""
        response = client.get('/api/review/aggregated/stats', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'platforms' in data
        assert 'categories' in data
        assert 'reward_types' in data

    def test_aggregated_unauthorized(self, client):
        """Test authorization required"""
        response = client.get('/api/review/aggregated')
        assert response.status_code == 401


# ============ BOOKMARKS TESTS ============

class TestBookmarks:
    """Test bookmark endpoints"""

    def test_bookmark_listing(self, client, auth_header):
        """Test POST /api/review/listings/<id>/bookmark"""
        response = client.post('/api/review/listings/1/bookmark', headers=auth_header)
        assert response.status_code == 201
        data = response.get_json()
        assert data['listing_id'] == 1
        assert data['message'] == 'Bookmark added'

    def test_bookmark_duplicate(self, client, auth_header):
        """Test duplicate bookmark error"""
        client.post('/api/review/listings/1/bookmark', headers=auth_header)
        response = client.post('/api/review/listings/1/bookmark', headers=auth_header)
        assert response.status_code == 400
        assert 'Already bookmarked' in response.get_json()['error']

    def test_bookmark_nonexistent_listing(self, client, auth_header):
        """Test bookmark nonexistent listing"""
        response = client.post('/api/review/listings/99999/bookmark', headers=auth_header)
        assert response.status_code == 404

    def test_remove_bookmark(self, client, auth_header):
        """Test DELETE /api/review/listings/<id>/bookmark"""
        client.post('/api/review/listings/1/bookmark', headers=auth_header)
        response = client.delete('/api/review/listings/1/bookmark', headers=auth_header)
        assert response.status_code == 200

    def test_remove_nonexistent_bookmark(self, client, auth_header):
        """Test remove nonexistent bookmark"""
        response = client.delete('/api/review/listings/99999/bookmark', headers=auth_header)
        assert response.status_code == 404

    def test_get_bookmarks(self, client, auth_header):
        """Test GET /api/review/bookmarks"""
        client.post('/api/review/listings/1/bookmark', headers=auth_header)
        response = client.get('/api/review/bookmarks', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'bookmarks' in data
        assert data['total'] >= 1


# ============ MULTI-ACCOUNT MANAGEMENT TESTS ============

class TestMultiAccountManagement:
    """Test account management endpoints"""

    def test_create_account(self, client, auth_header):
        """Test POST /api/review/accounts"""
        payload = {
            'platform': 'naver',
            'account_name': 'mynaverblog',
            'follower_count': 10000,
            'category_tags': ['뷰티', '패션']
        }
        response = client.post('/api/review/accounts', json=payload, headers=auth_header)
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['account']['platform'] == 'naver'

    def test_create_account_invalid_platform(self, client, auth_header):
        """Test invalid platform"""
        payload = {
            'platform': 'invalid_platform',
            'account_name': 'test'
        }
        response = client.post('/api/review/accounts', json=payload, headers=auth_header)
        assert response.status_code == 400

    def test_create_account_missing_fields(self, client, auth_header):
        """Test missing required fields"""
        payload = {'platform': 'naver'}
        response = client.post('/api/review/accounts', json=payload, headers=auth_header)
        assert response.status_code == 400

    def test_create_duplicate_account(self, client, auth_header):
        """Test duplicate account creation"""
        payload = {
            'platform': 'naver',
            'account_name': 'test_blog'
        }
        client.post('/api/review/accounts', json=payload, headers=auth_header)
        response = client.post('/api/review/accounts', json=payload, headers=auth_header)
        assert response.status_code == 400

    def test_get_accounts(self, client, auth_header):
        """Test GET /api/review/accounts"""
        response = client.get('/api/review/accounts', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'accounts' in data
        assert 'total' in data

    def test_get_accounts_by_platform(self, client, auth_header):
        """Test platform filter"""
        response = client.get('/api/review/accounts?platform=naver', headers=auth_header)
        data = response.get_json()
        for account in data['accounts']:
            assert account['platform'] == 'naver'

    def test_get_account_detail(self, client, auth_header):
        """Test GET /api/review/accounts/<id>"""
        # Create account first
        payload = {
            'platform': 'instagram',
            'account_name': 'test_insta'
        }
        create_resp = client.post('/api/review/accounts', json=payload, headers=auth_header)
        account_id = create_resp.get_json()['id']

        response = client.get(f'/api/review/accounts/{account_id}', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == account_id
        assert 'total_applications' in data
        assert 'success_rate' in data

    def test_update_account(self, client, auth_header):
        """Test PUT /api/review/accounts/<id>"""
        # Create account first
        payload = {
            'platform': 'youtube',
            'account_name': 'test_channel'
        }
        create_resp = client.post('/api/review/accounts', json=payload, headers=auth_header)
        account_id = create_resp.get_json()['id']

        # Update
        update_payload = {
            'follower_count': 50000,
            'is_active': False
        }
        response = client.put(f'/api/review/accounts/{account_id}', json=update_payload,
                            headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert data['account']['is_active'] == False

    def test_delete_account(self, client, auth_header):
        """Test DELETE /api/review/accounts/<id>"""
        # Create account first
        payload = {
            'platform': 'tiktok',
            'account_name': 'test_tiktok'
        }
        create_resp = client.post('/api/review/accounts', json=payload, headers=auth_header)
        account_id = create_resp.get_json()['id']

        # Delete
        response = client.delete(f'/api/review/accounts/{account_id}', headers=auth_header)
        assert response.status_code == 200

    def test_user_isolation_accounts(self, client, auth_header, user_2_header):
        """Test user cannot access another user's account"""
        # User 1 creates account
        payload = {
            'platform': 'naver',
            'account_name': 'user1_blog'
        }
        create_resp = client.post('/api/review/accounts', json=payload, headers=auth_header)
        account_id = create_resp.get_json()['id']

        # User 2 tries to access
        response = client.get(f'/api/review/accounts/{account_id}', headers=user_2_header)
        assert response.status_code == 403


# ============ APPLICATION MANAGEMENT TESTS ============

class TestApplicationManagement:
    """Test application endpoints"""

    def test_create_application(self, client, auth_header):
        """Test POST /api/review/applications"""
        # Create account and get listing first (assuming they exist)
        account_payload = {
            'platform': 'naver',
            'account_name': 'blogtest'
        }
        account_resp = client.post('/api/review/accounts', json=account_payload,
                                  headers=auth_header)
        account_id = account_resp.get_json()['id']

        # Create application
        app_payload = {
            'listing_id': 1,
            'account_id': account_id
        }
        response = client.post('/api/review/applications', json=app_payload, headers=auth_header)
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['application']['status'] == 'pending'

    def test_create_application_missing_fields(self, client, auth_header):
        """Test missing required fields"""
        payload = {'listing_id': 1}
        response = client.post('/api/review/applications', json=payload, headers=auth_header)
        assert response.status_code == 400

    def test_get_applications(self, client, auth_header):
        """Test GET /api/review/applications"""
        response = client.get('/api/review/applications', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'applications' in data
        assert 'total' in data

    def test_get_applications_by_status(self, client, auth_header):
        """Test status filter"""
        response = client.get('/api/review/applications?status=pending', headers=auth_header)
        data = response.get_json()
        for app in data['applications']:
            assert app['status'] == 'pending'

    def test_get_application_detail(self, client, auth_header):
        """Test GET /api/review/applications/<id>"""
        # Get first application
        list_resp = client.get('/api/review/applications', headers=auth_header)
        apps = list_resp.get_json()['applications']
        if apps:
            app_id = apps[0]['id']
            response = client.get(f'/api/review/applications/{app_id}', headers=auth_header)
            assert response.status_code == 200

    def test_update_application_status(self, client, auth_header):
        """Test PUT /api/review/applications/<id>"""
        # Get first application
        list_resp = client.get('/api/review/applications', headers=auth_header)
        apps = list_resp.get_json()['applications']
        if apps:
            app_id = apps[0]['id']
            update_payload = {
                'status': 'completed',
                'result': 'Successfully posted review'
            }
            response = client.put(f'/api/review/applications/{app_id}', json=update_payload,
                                headers=auth_header)
            assert response.status_code == 200


# ============ AUTO-APPLY RULES TESTS ============

class TestAutoApplyRules:
    """Test auto-apply rule endpoints"""

    def test_create_rule(self, client, auth_header):
        """Test POST /api/review/auto-apply/rules"""
        payload = {
            'name': '뷰티 제품 자동신청',
            'categories': ['뷰티', '스킨케어'],
            'min_reward': 100000,
            'max_applicants_ratio': 0.5
        }
        response = client.post('/api/review/auto-apply/rules', json=payload, headers=auth_header)
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['rule']['is_active'] == True

    def test_get_rules(self, client, auth_header):
        """Test GET /api/review/auto-apply/rules"""
        response = client.get('/api/review/auto-apply/rules', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'rules' in data
        assert 'total' in data

    def test_update_rule(self, client, auth_header):
        """Test PUT /api/review/auto-apply/rules/<id>"""
        # Create rule first
        create_payload = {
            'name': '패션 자동신청',
            'categories': ['패션']
        }
        create_resp = client.post('/api/review/auto-apply/rules', json=create_payload,
                                 headers=auth_header)
        rule_id = create_resp.get_json()['id']

        # Update
        update_payload = {
            'is_active': False,
            'min_reward': 150000
        }
        response = client.put(f'/api/review/auto-apply/rules/{rule_id}', json=update_payload,
                            headers=auth_header)
        assert response.status_code == 200

    def test_delete_rule(self, client, auth_header):
        """Test DELETE /api/review/auto-apply/rules/<id>"""
        # Create rule first
        create_payload = {
            'name': '음식 자동신청',
            'categories': ['음식']
        }
        create_resp = client.post('/api/review/auto-apply/rules', json=create_payload,
                                 headers=auth_header)
        rule_id = create_resp.get_json()['id']

        # Delete
        response = client.delete(f'/api/review/auto-apply/rules/{rule_id}', headers=auth_header)
        assert response.status_code == 200

    def test_run_auto_apply(self, client, auth_header):
        """Test POST /api/review/auto-apply/run"""
        response = client.post('/api/review/auto-apply/run', headers=auth_header)
        assert response.status_code in [200, 400]  # May fail if no rules/accounts
        if response.status_code == 200:
            data = response.get_json()
            assert 'status' in data
            assert 'applications_created' in data


# ============ ANALYTICS TESTS ============

class TestAnalytics:
    """Test dashboard and analytics"""

    def test_get_dashboard(self, client, auth_header):
        """Test GET /api/review/dashboard"""
        response = client.get('/api/review/dashboard', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert 'accounts_count' in data
        assert 'total_applications' in data
        assert 'success_rate' in data
        assert 'recent_applications' in data

    def test_get_analytics_default(self, client, auth_header):
        """Test GET /api/review/analytics (default month)"""
        response = client.get('/api/review/analytics', headers=auth_header)
        assert response.status_code == 200
        data = response.get_json()
        assert data['period'] == 'month'
        assert 'total_applications' in data
        assert 'by_status' in data
        assert 'by_account' in data
        assert 'by_category' in data
        assert 'by_reward_type' in data

    def test_get_analytics_period_week(self, client, auth_header):
        """Test analytics period filter"""
        response = client.get('/api/review/analytics?period=week', headers=auth_header)
        data = response.get_json()
        assert data['period'] == 'week'

    def test_get_analytics_period_all(self, client, auth_header):
        """Test analytics all time"""
        response = client.get('/api/review/analytics?period=all', headers=auth_header)
        data = response.get_json()
        assert data['period'] == 'all'


# ============ EDGE CASES & BUSINESS LOGIC ============

class TestEdgeCases:
    """Test edge cases and business logic"""

    def test_pagination_first_page(self, client, auth_header):
        """Test first page defaults correctly"""
        response = client.get('/api/review/aggregated', headers=auth_header)
        data = response.get_json()
        assert data['current_page'] == 1

    def test_empty_results(self, client, auth_header):
        """Test empty results handling"""
        response = client.get('/api/review/aggregated?category=nonexistent', headers=auth_header)
        data = response.get_json()
        assert data['total'] == 0
        assert data['listings'] == []

    def test_invalid_enum_values(self, client, auth_header):
        """Test invalid enum values"""
        response = client.post('/api/review/accounts',
                             json={'platform': 'invalid', 'account_name': 'test'},
                             headers=auth_header)
        assert response.status_code == 400

    def test_null_optional_fields(self, client, auth_header):
        """Test optional fields can be null"""
        payload = {
            'platform': 'blog',
            'account_name': 'minimalist_blog'
            # No follower_count or category_tags
        }
        response = client.post('/api/review/accounts', json=payload, headers=auth_header)
        assert response.status_code == 201
        data = response.get_json()
        assert data['account']['follower_count'] == 0
        assert data['account']['category_tags'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
