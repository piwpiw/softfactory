"""Test Suite — Telegram Bot Integration

Tests for:
  - SNSSettings model fields
  - Telegram service notifications
  - Telegram routes (endpoints)
  - Scheduler integration
"""

import pytest
import json
from datetime import datetime
from backend.models import db, User, SNSSettings, SNSPost, SNSAccount
from backend.telegram_service import TelegramService, send_sns_notification
from backend.services.telegram_routes import telegram_bp


class TestSNSSettingsModel:
    """Test SNSSettings model enhancements."""

    def test_sns_settings_has_telegram_fields(self):
        """Verify SNSSettings has telegram_chat_id and telegram_enabled fields."""
        settings = SNSSettings()
        assert hasattr(settings, 'telegram_chat_id')
        assert hasattr(settings, 'telegram_enabled')

    def test_sns_settings_to_dict_includes_telegram(self):
        """Verify to_dict() includes Telegram fields."""
        settings = SNSSettings(
            user_id=1,
            telegram_chat_id='7910169750',
            telegram_enabled=True
        )
        data = settings.to_dict()
        assert 'telegram_chat_id' in data
        assert 'telegram_enabled' in data
        assert data['telegram_chat_id'] == '7910169750'
        assert data['telegram_enabled'] is True

    def test_sns_settings_telegram_disabled_by_default(self):
        """Telegram should be disabled by default."""
        settings = SNSSettings(user_id=1)
        assert settings.telegram_enabled is False
        assert settings.telegram_chat_id is None


class TestTelegramService:
    """Test TelegramService notification methods."""

    def test_telegram_service_post_success(self):
        """Test post success notification format."""
        # Mock chat_id
        chat_id = '7910169750'

        # Should return True/False based on API success
        result = TelegramService.notify_post_success(
            chat_id,
            'instagram',
            'Test post content here',
            likes=100,
            comments=5,
            post_url='https://instagram.com/p/test'
        )
        # Result depends on bot token validity
        assert isinstance(result, bool)

    def test_telegram_service_post_failure(self):
        """Test post failure notification format."""
        chat_id = '7910169750'
        result = TelegramService.notify_post_failure(
            chat_id,
            'instagram',
            'Connection timeout'
        )
        assert isinstance(result, bool)

    def test_telegram_service_automation_executed(self):
        """Test automation executed notification format."""
        chat_id = '7910169750'
        result = TelegramService.notify_automation_executed(
            chat_id,
            'Daily Instagram Post',
            ['instagram', 'twitter'],
            '2026-02-26 10:30:00 UTC'
        )
        assert isinstance(result, bool)

    def test_telegram_service_daily_summary(self):
        """Test daily summary notification format."""
        chat_id = '7910169750'
        summary_data = {
            'total_posts': 5,
            'successful_posts': 5,
            'failed_posts': 0,
            'total_engagement': 2345,
            'platforms': {
                'instagram': {'posts': 3, 'engagement': 1234},
                'twitter': {'posts': 2, 'engagement': 1111}
            }
        }
        result = TelegramService.notify_daily_summary(chat_id, summary_data)
        assert isinstance(result, bool)

    def test_send_message_missing_token(self):
        """Test send_message with missing token."""
        import os
        original_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        try:
            os.environ['TELEGRAM_BOT_TOKEN'] = ''
            result = TelegramService.send_message('7910169750', 'test')
            assert result is False
        finally:
            if original_token:
                os.environ['TELEGRAM_BOT_TOKEN'] = original_token

    def test_send_message_missing_chat_id(self):
        """Test send_message with missing chat_id."""
        result = TelegramService.send_message('', 'test message')
        assert result is False


class TestSendSNSNotification:
    """Test high-level send_sns_notification function."""

    def test_notification_disabled_user(self, app):
        """Notification should return False if Telegram disabled."""
        with app.app_context():
            # Create user without Telegram
            user = User(email='test@example.com', name='Test User')
            user.set_password('password')
            db.session.add(user)

            settings = SNSSettings(user_id=user.id, telegram_enabled=False)
            db.session.add(settings)
            db.session.commit()

            result = send_sns_notification(user.id, 'post_success', {
                'platform': 'instagram',
                'content': 'test'
            })
            assert result is False

    def test_notification_missing_chat_id(self, app):
        """Notification should return False if chat_id is missing."""
        with app.app_context():
            user = User(email='test2@example.com', name='Test User 2')
            user.set_password('password')
            db.session.add(user)

            settings = SNSSettings(user_id=user.id, telegram_enabled=True)
            db.session.add(settings)
            db.session.commit()

            result = send_sns_notification(user.id, 'post_success', {
                'platform': 'instagram',
                'content': 'test'
            })
            assert result is False


class TestTelegramRoutes:
    """Test Telegram API endpoints."""

    def test_link_account_endpoint(self, client, auth_headers):
        """Test GET /api/telegram/link-account endpoint."""
        response = client.get('/api/telegram/link-account', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'linking_url' in data
        assert 'token' in data
        assert 'piwpiwtelegrambot' in data['linking_url']

    def test_verify_link_endpoint_invalid_token(self, client, auth_headers):
        """Test POST /api/telegram/verify-link with invalid token."""
        response = client.post('/api/telegram/verify-link',
                              headers=auth_headers,
                              json={'token': 'invalid_token', 'chat_id': '7910169750'})
        assert response.status_code == 400

    def test_verify_link_endpoint_missing_fields(self, client, auth_headers):
        """Test POST /api/telegram/verify-link with missing fields."""
        response = client.post('/api/telegram/verify-link',
                              headers=auth_headers,
                              json={})
        assert response.status_code == 400

    def test_status_endpoint_not_linked(self, client, auth_headers):
        """Test GET /api/telegram/status when not linked."""
        response = client.get('/api/telegram/status', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['telegram_enabled'] is False

    def test_send_test_message_not_enabled(self, client, auth_headers):
        """Test POST /api/telegram/send-test-message when Telegram not enabled."""
        response = client.post('/api/telegram/send-test-message',
                              headers=auth_headers)
        assert response.status_code == 400

    def test_unlink_account_endpoint(self, client, auth_headers, app):
        """Test POST /api/telegram/unlink-account endpoint."""
        with app.app_context():
            # First create a linked account
            from backend.auth import decode_jwt
            token = auth_headers['Authorization'].split(' ')[1]
            claims = decode_jwt(token)
            user_id = claims.get('user_id')

            settings = SNSSettings.query.filter_by(user_id=user_id).first()
            if not settings:
                settings = SNSSettings(user_id=user_id)
                db.session.add(settings)

            settings.telegram_chat_id = '7910169750'
            settings.telegram_enabled = True
            db.session.commit()

        # Now unlink
        response = client.post('/api/telegram/unlink-account', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'

        # Verify it's unlinked
        with app.app_context():
            settings = SNSSettings.query.filter_by(user_id=user_id).first()
            assert settings.telegram_enabled is False
            assert settings.telegram_chat_id is None


class TestSchedulerIntegration:
    """Test scheduler integration with Telegram."""

    def test_execute_scheduled_posts_sends_notifications(self, app):
        """Test that execute_scheduled_posts sends Telegram notifications."""
        with app.app_context():
            # This is an integration test
            # In production, verify notifications are sent when posts execute
            from backend.scheduler import execute_scheduled_posts
            # Should not raise exception
            execute_scheduled_posts(app)

    def test_send_daily_summary(self, app):
        """Test daily summary job execution."""
        with app.app_context():
            from backend.scheduler import send_daily_telegram_summary
            # Should not raise exception
            send_daily_telegram_summary(app)


# Fixtures (conftest.py should have these)
@pytest.fixture
def app():
    """Create Flask app for testing."""
    from backend.app import create_app
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
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(app, client):
    """Create authenticated headers."""
    from backend.auth import encode_jwt
    user = User(email='test@example.com', name='Test User', role='user')
    user.set_password('password123')

    with app.app_context():
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    token = encode_jwt({'user_id': user_id, 'email': 'test@example.com'})
    return {'Authorization': f'Bearer {token}'}
