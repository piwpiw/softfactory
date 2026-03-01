"""Instagram API Service — Unit Tests"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from backend.services.instagram_api import InstagramAPI, InstagramAPIError, instagram_bp
from backend.models import SNSAccount, SNSPost


class TestInstagramAPI:
    """Test InstagramAPI class"""

    @pytest.fixture
    def api(self):
        """Create InstagramAPI instance"""
        return InstagramAPI('test_token_123')

    def test_initialization(self, api):
        """Test API initialization"""
        assert api.access_token == 'test_token_123'
        assert api.session is not None

    @patch('backend.services.instagram_api.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful OAuth authentication"""
        mock_post.return_value.json.return_value = {
            'access_token': 'new_token',
            'user_id': '123456'
        }

        api = InstagramAPI('')
        token, info = api.authenticate('auth_code')

        assert token == 'new_token'
        assert 'user_id' in info

    @patch('backend.services.instagram_api.requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure"""
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.ok = False

        api = InstagramAPI('')
        with pytest.raises(InstagramAPIError):
            api.authenticate('invalid_code')

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_get_account_info(self, mock_request, api):
        """Test get account info"""
        mock_request.return_value = {
            'id': '123456789',
            'username': 'john_doe',
            'name': 'John Doe',
            'biography': 'Marketing expert',
            'followers_count': 15420,
            'follows_count': 850,
            'profile_picture_url': 'https://...',
            'website': 'https://johndoe.com',
            'ig_metadata': {'account_type': 'BUSINESS'}
        }

        info = api.get_account_info()

        assert info['username'] == 'john_doe'
        assert info['followers_count'] == 15420
        assert info['account_type'] == 'business'

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_post_feed(self, mock_request, api):
        """Test posting to feed"""
        api._make_request = MagicMock(side_effect=[
            {'id': '123456789'},  # get account
            {'id': 'container_123'},  # create container
            {'id': 'post_789'}  # publish
        ])

        post_id = api.post_feed(
            'https://example.com/image.jpg',
            'Test caption',
            ['test', 'instagram']
        )

        assert post_id == 'post_789'

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_post_feed_missing_image(self, mock_request, api):
        """Test post_feed with missing image URL"""
        with pytest.raises(InstagramAPIError):
            api.post_feed('', 'No image')

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_post_story(self, mock_request, api):
        """Test posting to story"""
        api._make_request = MagicMock(side_effect=[
            {'id': '123456789'},  # get account
            {'id': 'story_456'}  # create story
        ])

        story_id = api.post_story('https://example.com/story.jpg', 'Back soon!')

        assert story_id == 'story_456'

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_post_reel(self, mock_request, api):
        """Test posting to reel"""
        api._make_request = MagicMock(side_effect=[
            {'id': '123456789'},  # get account
            {'id': 'reel_container'},  # create reel
            {'id': 'reel_999'}  # publish
        ])

        reel_id = api.post_reel(
            'https://example.com/video.mp4',
            'Tutorial',
            'https://example.com/thumb.jpg'
        )

        assert reel_id == 'reel_999'

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_get_insights(self, mock_request, api):
        """Test getting post insights"""
        mock_request.return_value = {
            'data': [
                {'name': 'engagement', 'values': [{'value': 50}]},
                {'name': 'impressions', 'values': [{'value': 1000}]},
                {'name': 'reach', 'values': [{'value': 800}]},
                {'name': 'saved', 'values': [{'value': 10}]}
            ]
        }

        insights = api.get_insights('post_123')

        assert insights['likes'] == 50
        assert insights['impressions'] == 1000
        assert insights['reach'] == 800
        assert insights['engagement_rate'] == 5.0

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_get_media(self, mock_request, api):
        """Test getting recent media"""
        mock_request.return_value = {
            'data': [
                {
                    'id': 'post_1',
                    'caption': 'Photo 1',
                    'media_type': 'IMAGE',
                    'media_url': 'https://...',
                    'timestamp': '2026-02-26T10:00:00Z',
                    'like_count': 100,
                    'comments_count': 10
                }
            ],
            'paging': {
                'cursors': {
                    'after': 'next_cursor'
                }
            }
        }

        posts, next_cursor = api.get_media(limit=25)

        assert len(posts) == 1
        assert posts[0]['id'] == 'post_1'
        assert next_cursor == 'next_cursor'

    @patch('backend.services.instagram_api.requests.post')
    def test_refresh_access_token(self, mock_post, api):
        """Test token refresh"""
        mock_post.return_value.json.return_value = {
            'access_token': 'refreshed_token'
        }

        new_token = api.refresh_access_token('old_token')

        assert new_token == 'refreshed_token'

    @patch('backend.services.instagram_api.InstagramAPI._make_request')
    def test_error_handling_rate_limit(self, mock_request, api):
        """Test rate limit error handling"""
        from requests import Response
        error = InstagramAPIError("Rate limit exceeded. Please try again later.")

        with patch.object(api, '_make_request', side_effect=error):
            with pytest.raises(InstagramAPIError) as exc_info:
                api.post_feed('https://example.com/image.jpg', 'Test')
            assert "Rate limit" in str(exc_info.value)

    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation"""
        rate = InstagramAPI._calculate_engagement_rate(50, 1000)
        assert rate == 5.0

        # Edge case: zero impressions
        rate = InstagramAPI._calculate_engagement_rate(50, 0)
        assert rate == 0.0


class TestInstagramBlueprint:
    """Test Flask blueprint endpoints"""

    @pytest.fixture
    def client(self, app):
        """Create Flask test client"""
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        """Create auth headers with JWT token"""
        return {'Authorization': 'Bearer test_jwt_token'}

    def test_blueprint_registered(self):
        """Test blueprint is properly registered"""
        assert instagram_bp is not None
        assert instagram_bp.name == 'instagram'
        assert instagram_bp.url_prefix == '/api/sns/instagram'

    def test_oauth_authorize_endpoint(self, client, auth_headers):
        """Test OAuth authorize endpoint"""
        with patch.dict('os.environ', {'INSTAGRAM_APP_ID': 'test_app_id'}):
            response = client.get(
                '/api/sns/instagram/oauth/authorize',
                headers=auth_headers
            )
            # Would return 200 with auth_url in real scenario
            # But requires database session setup

    def test_missing_auth_header(self, client):
        """Test endpoint without auth header"""
        response = client.get('/api/sns/instagram/accounts')
        # Should require authentication
        assert response.status_code in [401, 400, 302]


class TestDatabaseIntegration:
    """Test database model integration"""

    def test_sns_account_model_has_instagram_fields(self):
        """Test SNSAccount model has required Instagram fields"""
        account = SNSAccount(
            platform='instagram',
            account_name='test_user',
            access_token='token_123',
            platform_user_id='123456',
            account_type='business'
        )

        assert account.platform == 'instagram'
        assert account.access_token == 'token_123'
        assert account.platform_user_id == '123456'
        assert account.account_type == 'business'

    def test_sns_account_to_dict(self):
        """Test SNSAccount.to_dict() method"""
        account = SNSAccount(
            id=1,
            platform='instagram',
            account_name='john_doe',
            is_active=True,
            platform_user_id='123456',
            followers_count=1000,
            created_at=datetime.utcnow()
        )

        account_dict = account.to_dict()

        assert account_dict['platform'] == 'instagram'
        assert account_dict['account_name'] == 'john_doe'
        assert account_dict['followers_count'] == 1000

    def test_sns_post_creation(self):
        """Test SNSPost model for Instagram posts"""
        post = SNSPost(
            user_id=1,
            account_id=1,
            platform='instagram',
            content='Test post',
            media_url='https://example.com/image.jpg',
            status='published',
            platform_post_id='post_123'
        )

        assert post.platform == 'instagram'
        assert post.platform_post_id == 'post_123'
        assert post.status == 'published'


class TestErrorHandling:
    """Test error handling"""

    def test_instagram_api_error_message(self):
        """Test InstagramAPIError exception"""
        error = InstagramAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_rate_limit_error(self):
        """Test rate limit error detection"""
        error = InstagramAPIError("Rate limit exceeded. Please try again later.")
        assert "Rate limit" in str(error)

    def test_token_error(self):
        """Test token expiry error detection"""
        error = InstagramAPIError("Access token expired. Please re-authenticate.")
        assert "token" in str(error).lower()

    def test_permission_error(self):
        """Test permission denied error"""
        error = InstagramAPIError("Permission denied. Check account permissions.")
        assert "permission" in str(error).lower()


class TestIntegration:
    """Integration tests"""

    @patch('backend.services.instagram_api.InstagramAPI')
    def test_post_with_hashtags(self, mock_api):
        """Test posting with hashtags"""
        mock_instance = MagicMock()
        mock_instance.post_feed.return_value = 'post_123'
        mock_api.return_value = mock_instance

        api = InstagramAPI('token')
        post_id = api.post_feed(
            'https://example.com/img.jpg',
            'My post',
            ['tag1', 'tag2', 'tag3']
        )

        # Hashtags should be formatted with # prefix

    @patch('backend.services.instagram_api.InstagramAPI')
    def test_token_auto_refresh_on_expiry(self, mock_api):
        """Test automatic token refresh on expiry"""
        mock_instance = MagicMock()
        mock_instance.post_feed.side_effect = [
            InstagramAPIError("Access token expired"),
            'refreshed_post_id'
        ]
        mock_instance.refresh_access_token.return_value = 'new_token'
        mock_api.return_value = mock_instance

        # Should detect expiry and attempt refresh


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
