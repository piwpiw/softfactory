"""SNS Automation API Endpoints — Comprehensive Test Suite"""
import pytest
import json
from datetime import datetime, timedelta
from backend.app import create_app
from backend.models import db, User, SNSLinkInBio, SNSAutomate, SNSCompetitor, SNSAnalytics, SNSAccount


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
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
    return {'Authorization': 'Bearer demo_token', 'Content-Type': 'application/json'}


class TestLinkInBioEndpoints:
    """Test Link-in-Bio CRUD operations"""

    def test_create_link_in_bio(self, client, auth_headers):
        """POST /api/sns/linkinbio — Create link in bio"""
        response = client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'test-landing',
            'title': 'My Links',
            'links': [
                {'url': 'https://example.com', 'label': 'Website', 'icon': 'globe'},
                {'url': 'https://youtube.com/@user', 'label': 'YouTube', 'icon': 'youtube'}
            ],
            'theme': 'dark'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['data']['slug'] == 'test-landing'

    def test_get_link_in_bios(self, client, auth_headers):
        """GET /api/sns/linkinbio — List link in bios"""
        # Create first
        client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'landing1',
            'title': 'Links 1'
        })

        response = client.get('/api/sns/linkinbio', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1

    def test_update_link_in_bio(self, client, auth_headers):
        """PUT /api/sns/linkinbio/<id> — Update link in bio"""
        # Create first
        create_response = client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'landing1',
            'title': 'Original Title'
        })
        lib_id = create_response.get_json()['id']

        # Update
        response = client.put(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers, json={
            'title': 'Updated Title'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['title'] == 'Updated Title'

    def test_delete_link_in_bio(self, client, auth_headers):
        """DELETE /api/sns/linkinbio/<id> — Delete link in bio"""
        # Create first
        create_response = client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'landing1',
            'title': 'Temp'
        })
        lib_id = create_response.get_json()['id']

        # Delete
        response = client.delete(f'/api/sns/linkinbio/{lib_id}', headers=auth_headers)
        assert response.status_code == 200

    def test_get_link_in_bio_stats(self, client, auth_headers):
        """GET /api/sns/linkinbio/stats — Get click statistics"""
        response = client.get('/api/sns/linkinbio/stats', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_click_count' in data
        assert 'link_in_bios' in data


class TestAutomationEndpoints:
    """Test Automation Rules CRUD operations"""

    def test_create_automate(self, client, auth_headers):
        """POST /api/sns/automate — Create automation rule"""
        response = client.post('/api/sns/automate', headers=auth_headers, json={
            'name': 'Daily AI News',
            'topic': 'AI and Technology',
            'purpose': '홍보',
            'platforms': ['instagram', 'twitter', 'tiktok'],
            'frequency': 'daily'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['data']['name'] == 'Daily AI News'

    def test_get_automates(self, client, auth_headers):
        """GET /api/sns/automate — List automation rules"""
        # Create first
        client.post('/api/sns/automate', headers=auth_headers, json={
            'name': 'Rule 1',
            'topic': 'Tech',
            'purpose': '홍보',
            'platforms': ['instagram'],
            'frequency': 'daily'
        })

        response = client.get('/api/sns/automate', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1

    def test_update_automate(self, client, auth_headers):
        """PUT /api/sns/automate/<id> — Update automation rule"""
        # Create first
        create_response = client.post('/api/sns/automate', headers=auth_headers, json={
            'name': 'Original',
            'topic': 'Tech',
            'purpose': '홍보',
            'platforms': ['instagram'],
            'frequency': 'daily'
        })
        automate_id = create_response.get_json()['id']

        # Update
        response = client.put(f'/api/sns/automate/{automate_id}', headers=auth_headers, json={
            'name': 'Updated'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['name'] == 'Updated'

    def test_delete_automate(self, client, auth_headers):
        """DELETE /api/sns/automate/<id> — Delete automation rule"""
        # Create first
        create_response = client.post('/api/sns/automate', headers=auth_headers, json={
            'name': 'Temp Rule',
            'topic': 'Tech',
            'purpose': '홍보',
            'platforms': ['instagram'],
            'frequency': 'daily'
        })
        automate_id = create_response.get_json()['id']

        # Delete
        response = client.delete(f'/api/sns/automate/{automate_id}', headers=auth_headers)
        assert response.status_code == 200


class TestTrendingEndpoints:
    """Test Trending data endpoints"""

    def test_get_trending_all_platforms(self, client, auth_headers):
        """GET /api/sns/trending — Get trending for all platforms"""
        response = client.get('/api/sns/trending', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'platforms' in data
        assert 'instagram' in data['platforms']

    def test_get_trending_by_platform(self, client, auth_headers):
        """GET /api/sns/trending?platform=instagram — Get trending by platform"""
        response = client.get('/api/sns/trending?platform=instagram', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['platform'] == 'instagram'
        assert 'hashtags' in data['data']


class TestCompetitorEndpoints:
    """Test Competitor tracking CRUD operations"""

    def test_add_competitor(self, client, auth_headers):
        """POST /api/sns/competitor — Add competitor"""
        response = client.post('/api/sns/competitor', headers=auth_headers, json={
            'platform': 'instagram',
            'username': 'competitor_account',
            'followers_count': 50000,
            'engagement_rate': 3.5
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data

    def test_get_competitors(self, client, auth_headers):
        """GET /api/sns/competitor — List competitors"""
        # Add first
        client.post('/api/sns/competitor', headers=auth_headers, json={
            'platform': 'instagram',
            'username': 'user1'
        })

        response = client.get('/api/sns/competitor', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'competitors' in data

    def test_get_competitor_by_platform(self, client, auth_headers):
        """GET /api/sns/competitor?platform=twitter — Filter by platform"""
        client.post('/api/sns/competitor', headers=auth_headers, json={
            'platform': 'twitter',
            'username': 'competitor_tw'
        })

        response = client.get('/api/sns/competitor?platform=twitter', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['competitors'][0]['platform'] == 'twitter'

    def test_update_competitor(self, client, auth_headers):
        """PUT /api/sns/competitor/<id> — Update competitor data"""
        # Add first
        add_response = client.post('/api/sns/competitor', headers=auth_headers, json={
            'platform': 'instagram',
            'username': 'user1',
            'followers_count': 10000
        })
        competitor_id = add_response.get_json()['id']

        # Update
        response = client.put(f'/api/sns/competitor/{competitor_id}', headers=auth_headers, json={
            'followers_count': 15000,
            'engagement_rate': 2.5
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['followers_count'] == 15000

    def test_delete_competitor(self, client, auth_headers):
        """DELETE /api/sns/competitor/<id> — Stop tracking competitor"""
        # Add first
        add_response = client.post('/api/sns/competitor', headers=auth_headers, json={
            'platform': 'instagram',
            'username': 'temp_user'
        })
        competitor_id = add_response.get_json()['id']

        # Delete
        response = client.delete(f'/api/sns/competitor/{competitor_id}', headers=auth_headers)
        assert response.status_code == 200


class TestRepurposingEndpoints:
    """Test AI content repurposing"""

    def test_repurpose_content(self, client, auth_headers):
        """POST /api/sns/ai/repurpose — Repurpose content across platforms"""
        response = client.post('/api/sns/ai/repurpose', headers=auth_headers, json={
            'content': 'Just launched our new AI product! Check it out.',
            'source_platform': 'linkedin',
            'target_platforms': ['instagram', 'twitter', 'tiktok']
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'repurposed_content' in data
        assert 'instagram' in data['repurposed_content']
        assert 'twitter' in data['repurposed_content']


class TestROIMetricsEndpoints:
    """Test ROI calculation endpoints"""

    def test_get_roi_metrics(self, client, auth_headers):
        """GET /api/sns/roi — Get ROI metrics"""
        response = client.get('/api/sns/roi', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data
        assert 'financial' in data
        assert 'roi_percentage' in data['financial']

    def test_get_roi_metrics_by_platform(self, client, auth_headers):
        """GET /api/sns/roi?platform=instagram — Get ROI by platform"""
        response = client.get('/api/sns/roi?platform=instagram', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data

    def test_get_roi_metrics_by_date_range(self, client, auth_headers):
        """GET /api/sns/roi?date_from=...&date_to=... — Get ROI by date range"""
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)

        response = client.get(
            f'/api/sns/roi?date_from={week_ago.isoformat()}&date_to={today.isoformat()}',
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'metrics' in data


class TestErrorHandling:
    """Test error handling and validation"""

    def test_missing_auth_header(self, client):
        """Missing auth header should return 401"""
        response = client.get('/api/sns/linkinbio')
        assert response.status_code == 401

    def test_missing_required_fields(self, client, auth_headers):
        """Missing required fields should return 400"""
        response = client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'test'
            # Missing 'title'
        })
        assert response.status_code == 400

    def test_not_found(self, client, auth_headers):
        """Non-existent resource should return 404"""
        response = client.get('/api/sns/linkinbio/9999', headers=auth_headers)
        assert response.status_code == 404

    def test_duplicate_slug(self, client, auth_headers):
        """Duplicate slug should return 400"""
        client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'test-landing',
            'title': 'Links'
        })

        response = client.post('/api/sns/linkinbio', headers=auth_headers, json={
            'slug': 'test-landing',
            'title': 'Different Links'
        })
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
